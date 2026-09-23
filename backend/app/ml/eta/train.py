"""Offline Gradient Boosting ETA training with chronological validation."""

from __future__ import annotations

import hashlib, json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from backend.app.ml.eta.features import CATEGORICAL_FEATURES, FEATURE_NAMES, NUMERIC_FEATURES, build_training_frame

MODEL_VERSION = "eta-gbr-v1.0.0"
FEATURES_VERSION = "eta-features-v1"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def train_eta_model(tasks_csv: Path, telemetry_csv: Path, artifact_path: Path, metadata_path: Path) -> dict[str, Any]:
    tasks = pd.read_csv(tasks_csv).sort_values("planned_start").reset_index(drop=True)
    telemetry = pd.read_csv(telemetry_csv)
    X, y = build_training_frame(tasks, telemetry)
    split = max(int(len(X) * 0.8), 1)
    X_train, X_valid = X.iloc[:split], X.iloc[split:]
    y_train, y_valid = y.iloc[:split], y.iloc[split:]

    preprocess = ColumnTransformer([
        ("categorical", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_FEATURES),
        ("numeric", StandardScaler(), NUMERIC_FEATURES),
    ])
    pipeline = Pipeline([
        ("preprocess", preprocess),
        ("regressor", GradientBoostingRegressor(n_estimators=180, learning_rate=0.04, max_depth=3, random_state=42, loss="huber")),
    ])
    pipeline.fit(X_train, y_train)
    predictions = pipeline.predict(X_valid)
    residuals = np.abs(y_valid.to_numpy() - predictions)
    q90 = float(np.quantile(residuals, 0.90))
    metrics = {
        "mae": float(mean_absolute_error(y_valid, predictions)),
        "rmse": float(mean_squared_error(y_valid, predictions) ** 0.5),
        "r2": float(r2_score(y_valid, predictions)),
        "planned_baseline_mae": float(mean_absolute_error(y_valid, X_valid["estimated_time_min"])),
    }
    trained_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    artifact = {
        "model_version": MODEL_VERSION,
        "features_version": FEATURES_VERSION,
        "feature_names": FEATURE_NAMES,
        "pipeline": pipeline,
        "residual_q90": q90,
        "metrics": metrics,
    }
    metadata = {
        "model_version": MODEL_VERSION,
        "model_type": "GradientBoostingRegressor",
        "features_version": FEATURES_VERSION,
        "feature_schema": FEATURE_NAMES,
        "trained_at": trained_at,
        "dataset_version": "synthetic-tasks-v1",
        "task_dataset_sha256": _sha(tasks_csv),
        "telemetry_dataset_sha256": _sha(telemetry_csv),
        "training_rows": int(len(X_train)),
        "validation_rows": int(len(X_valid)),
        "split": "chronological 80/20 by planned_start",
        "metrics": metrics,
        "uncertainty": {"method": "90th percentile absolute validation residual", "residual_q90_minutes": q90},
        "limitations": ["Training data and validation labels are synthetic.", "Metrics do not establish real-world accuracy."],
    }
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, artifact_path, compress=3)
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata
