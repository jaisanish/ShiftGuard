"""Trusted local artifact registry for the ShiftGuard Isolation Forest model."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional

import joblib

from backend.app.config import settings
from backend.app.ml.anomaly.features import FEATURE_NAMES

logger = logging.getLogger("shiftguard.ml.anomaly.registry")


class AnomalyModelRegistry:
    def __init__(self, artifact_path: str | Path | None = None, metadata_path: str | Path | None = None):
        self.artifact_path = Path(artifact_path or settings.ANOMALY_ARTIFACT_PATH)
        self.metadata_path = Path(metadata_path or settings.ANOMALY_METADATA_PATH)
        self.artifact: Optional[dict[str, Any]] = None
        self.metadata: Optional[dict[str, Any]] = None
        self.error: Optional[str] = None

    def load(self, force: bool = False) -> bool:
        if self.artifact is not None and not force:
            return True
        self.artifact = None
        self.metadata = None
        self.error = None
        try:
            if not self.artifact_path.exists():
                raise FileNotFoundError(f"Model artifact not found: {self.artifact_path}")
            if not self.metadata_path.exists():
                raise FileNotFoundError(f"Model metadata not found: {self.metadata_path}")

            # Security boundary: load only the configured local project artifact.
            artifact = joblib.load(self.artifact_path)
            metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))
            if artifact.get("feature_names") != FEATURE_NAMES:
                raise ValueError("Artifact feature schema does not match application feature schema")
            if artifact.get("model_version") != metadata.get("model_version"):
                raise ValueError("Artifact and metadata versions do not match")
            for required in ("model", "scaler", "baselines", "score_calibration"):
                if required not in artifact:
                    raise ValueError(f"Artifact is missing required field '{required}'")

            self.artifact = artifact
            self.metadata = metadata
            logger.info("[ANOMALY] Loaded model version %s", metadata.get("model_version"))
            return True
        except Exception as exc:
            self.error = str(exc)
            logger.warning("[ANOMALY] Model unavailable: %s", exc)
            return False

    @property
    def ready(self) -> bool:
        return self.load()

    def health(self) -> dict[str, Any]:
        loaded = self.load()
        metadata = self.metadata or {}
        return {
            "status": "ready" if loaded else "unavailable",
            "model_loaded": loaded,
            "model_version": metadata.get("model_version"),
            "last_trained": metadata.get("trained_at"),
            "dataset_version": metadata.get("dataset_version"),
            "feature_schema": metadata.get("feature_schema", []),
            "artifact_path": str(self.artifact_path),
            "error": self.error,
        }


_registry = AnomalyModelRegistry()


def get_anomaly_registry() -> AnomalyModelRegistry:
    return _registry
