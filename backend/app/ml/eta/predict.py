from datetime import datetime, timezone
from typing import Any
import pandas as pd
from backend.app.ml.eta.features import FEATURE_NAMES
from backend.app.ml.eta.model_registry import get_eta_registry
from backend.app.ml.eta.schemas import ETAPrediction


class GradientBoostingETAPredictor:
    def __init__(self, registry=None): self.registry = registry or get_eta_registry()
    def is_ready(self): return self.registry.load()
    def get_model_info(self): return self.registry.health()

    def predict(self, task: dict[str, Any], features: dict[str, Any]) -> ETAPrediction:
        if not self.registry.load() or not self.registry.artifact: raise RuntimeError(self.registry.error or "ETA model unavailable")
        art = self.registry.artifact
        row = pd.DataFrame([{name: features[name] for name in FEATURE_NAMES}])
        predicted = max(float(art["pipeline"].predict(row)[0]), 1.0)
        uncertainty = float(art["residual_q90"])
        elapsed = float(features["elapsed_minutes"])
        planned = float(task["estimated_time_min"])
        reasons = []
        if float(features["idle_minutes_delta"]) > 2: reasons.append("Idle time increased")
        if str(features["working_condition"]).upper() in {"MUDDY", "SEVERE", "STEEP_INCLINE"}: reasons.append(f"Working condition: {features['working_condition']}")
        if float(features["load_cycles_delta"]) == 0 and elapsed > 5: reasons.append("No completed load cycle in current context")
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        return ETAPrediction(task_id=str(task["task_id"]), machine_id=str(task["machine_id"]), operator_id=str(task["operator_id"]),
            timestamp=now, planned_minutes=round(planned,2), predicted_minutes=round(predicted,2),
            predicted_remaining_minutes=round(max(predicted-elapsed,0),2), p50=round(predicted,2), p90=round(predicted+uncertainty,2),
            interval_lower=round(max(predicted-uncertainty,0),2), interval_upper=round(predicted+uncertainty,2),
            uncertainty_minutes=round(uncertainty,2), delta_vs_plan_minutes=round(predicted-planned,2), why_changed=reasons,
            features_version=art["features_version"], model_version=art["model_version"], feature_snapshot=features)
