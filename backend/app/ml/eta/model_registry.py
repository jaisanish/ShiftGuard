import json
from pathlib import Path
from typing import Any, Optional
import joblib
from backend.app.config import settings
from backend.app.ml.eta.features import FEATURE_NAMES


class ETAModelRegistry:
    def __init__(self, artifact_path=None, metadata_path=None):
        self.artifact_path = Path(artifact_path or settings.ETA_ARTIFACT_PATH)
        self.metadata_path = Path(metadata_path or settings.ETA_METADATA_PATH)
        self.artifact: Optional[dict[str, Any]] = None
        self.metadata: Optional[dict[str, Any]] = None
        self.error: Optional[str] = None

    def load(self, force=False):
        if self.artifact is not None and not force: return True
        try:
            artifact = joblib.load(self.artifact_path)
            metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))
            if artifact.get("feature_names") != FEATURE_NAMES: raise ValueError("ETA feature schema mismatch")
            if artifact.get("model_version") != metadata.get("model_version"): raise ValueError("ETA artifact version mismatch")
            self.artifact, self.metadata, self.error = artifact, metadata, None
            return True
        except Exception as exc:
            self.artifact, self.metadata, self.error = None, None, str(exc)
            return False

    def health(self):
        loaded = self.load(); meta = self.metadata or {}
        return {"status": "ready" if loaded else "unavailable", "model_loaded": loaded,
                "model_version": meta.get("model_version"), "last_trained": meta.get("trained_at"),
                "dataset_version": meta.get("dataset_version"), "metrics": meta.get("metrics", {}),
                "artifact_path": str(self.artifact_path), "error": self.error}


_registry = ETAModelRegistry()
def get_eta_registry(): return _registry
