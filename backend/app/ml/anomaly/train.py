"""Offline training pipeline for the versioned ShiftGuard Isolation Forest artifact."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import RobustScaler

from backend.app.ml.anomaly.baseline import build_baselines
from backend.app.ml.anomaly.features import (
    FEATURE_NAMES,
    WINDOW_MINUTES,
    build_feature_window,
    build_feature_windows,
    feature_matrix,
)


DEFAULT_MODEL_VERSION = "anomaly-iforest-v1.0.0"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _score_vector(artifact: dict[str, Any], window: dict[str, Any]) -> tuple[float, bool]:
    vector = np.array([[float(window[name]) for name in FEATURE_NAMES]], dtype=float)
    scaled = artifact["scaler"].transform(vector)
    raw = float(-artifact["model"].decision_function(scaled)[0])
    cal = artifact["score_calibration"]
    low, high = float(cal["normalization_low"]), float(cal["normalization_high"])
    normalized = float(np.clip((raw - low) / max(high - low, 1e-9), 0.0, 1.0))
    return normalized, raw >= float(cal["threshold_raw"])


def evaluate_demo_scenarios(artifact: dict[str, Any], demo_csv: Path | None) -> dict[str, Any]:
    """Evaluate deterministic synthetic scenarios; labels are demo-only, never real-world validation."""
    if not demo_csv or not demo_csv.exists():
        return {"available": False, "reason": "demo dataset not found"}

    demo = pd.read_csv(demo_csv)
    expectations = {
        "TSK-DEMO-01": ("normal", False),
        "TSK-DEMO-02": ("seatbelt_violation", True),
        "TSK-DEMO-03": ("proximity_warning", True),
        "TSK-DEMO-04": ("proximity_critical", True),
        "TSK-DEMO-05": ("excessive_idle", True),
        "TSK-DEMO-06": ("repeated_safety", True),
        "TSK-DEMO-07": ("high_fuel_usage", True),
    }
    results: list[dict[str, Any]] = []
    for task_id, (name, expected) in expectations.items():
        rows = demo[demo["task_id"] == task_id]
        if len(rows) < 2:
            continue
        window = build_feature_window(rows)
        score, predicted = _score_vector(artifact, window)
        results.append({
            "scenario": name,
            "synthetic_expected_anomaly": expected,
            "predicted_anomaly": predicted,
            "anomaly_score": round(score, 6),
            "correct": predicted == expected,
        })

    positives = [row for row in results if row["synthetic_expected_anomaly"]]
    true_positive = sum(row["predicted_anomaly"] for row in positives)
    predicted_positive = sum(row["predicted_anomaly"] for row in results)
    correct = sum(row["correct"] for row in results)
    return {
        "available": True,
        "label_scope": "Synthetic controlled-scenario evaluation only",
        "scenario_count": len(results),
        "accuracy": correct / len(results) if results else 0.0,
        "recall": true_positive / len(positives) if positives else 0.0,
        "precision": true_positive / predicted_positive if predicted_positive else 0.0,
        "scenarios": results,
    }


def train_anomaly_model(
    telemetry_csv: Path,
    artifact_path: Path,
    metadata_path: Path,
    demo_csv: Path | None = None,
    model_version: str = DEFAULT_MODEL_VERSION,
    minimum_operator_windows: int = 6,
) -> dict[str, Any]:
    telemetry = pd.read_csv(telemetry_csv)
    windows = build_feature_windows(telemetry)
    if len(windows) < 20:
        raise ValueError(f"Anomaly training requires at least 20 windows; found {len(windows)}")

    matrix = feature_matrix(windows)
    scaler = RobustScaler()
    scaled = scaler.fit_transform(matrix)
    model = IsolationForest(
        n_estimators=250,
        contamination=0.08,
        max_samples="auto",
        random_state=42,
        n_jobs=1,
    )
    model.fit(scaled)

    raw_scores = -model.decision_function(scaled)
    calibration = {
        "normalization_low": float(np.quantile(raw_scores, 0.05)),
        "normalization_high": float(np.quantile(raw_scores, 0.99)),
        "threshold_raw": float(np.quantile(raw_scores, 0.92)),
    }
    artifact: dict[str, Any] = {
        "model_version": model_version,
        "feature_names": FEATURE_NAMES,
        "model": model,
        "scaler": scaler,
        "baselines": build_baselines(windows, minimum_operator_windows),
        "score_calibration": calibration,
    }

    diagnostics = evaluate_demo_scenarios(artifact, demo_csv)
    trained_at = utc_now_iso()
    metadata = {
        "model_version": model_version,
        "model_type": "IsolationForest",
        "trained_at": trained_at,
        "dataset_version": "synthetic-telemetry-v1",
        "dataset_sha256": file_sha256(telemetry_csv),
        "training_rows": int(len(telemetry)),
        "feature_window_count": int(len(windows)),
        "feature_schema": FEATURE_NAMES,
        "window_minutes": WINDOW_MINUTES,
        "minimum_operator_windows": minimum_operator_windows,
        "hyperparameters": {
            "n_estimators": 250,
            "contamination": 0.08,
            "random_state": 42,
            "scaler": "RobustScaler",
        },
        "score_calibration": calibration,
        "diagnostics": diagnostics,
        "limitations": [
            "Training and evaluation data are synthetic.",
            "Diagnostics do not establish real-world generalization or safety performance.",
            "The model provides advisory analytics and never controls edge safety decisions.",
        ],
    }

    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, artifact_path, compress=3)
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata
