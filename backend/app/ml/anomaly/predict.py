"""Isolation Forest inference and evidence mapping for advisory analytics."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable

import numpy as np

from backend.app.ml.interfaces import AnomalyPredictor, AnomalyResult
from backend.app.ml.anomaly.baseline import select_baseline
from backend.app.ml.anomaly.features import FEATURE_NAMES
from backend.app.ml.anomaly.model_registry import AnomalyModelRegistry, get_anomaly_registry
from backend.app.ml.anomaly.schemas import AnomalyEvidence, AnomalyInsight


TYPE_PRIORITY = {
    "seatbelt_violation_rate": "REPEATED_SAFETY_PATTERN",
    "safety_alert_rate": "REPEATED_SAFETY_PATTERN",
    "idle_ratio": "EXCESSIVE_IDLE",
    "fuel_per_active_hour": "HIGH_FUEL_USAGE",
    "fuel_per_load_cycle": "HIGH_FUEL_USAGE",
    "load_cycles_per_hour": "LOW_PRODUCTIVITY",
}

FEATURE_LABELS = {
    "idle_ratio": "Idle ratio",
    "fuel_per_load_cycle": "Fuel per load cycle",
    "load_cycles_per_hour": "Load cycles per hour",
    "fuel_per_active_hour": "Fuel per active hour",
    "safety_alert_rate": "Safety-event sample rate",
    "seatbelt_violation_rate": "Seatbelt-violation sample rate",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class IsolationForestAnomalyPredictor(AnomalyPredictor):
    def __init__(self, registry: AnomalyModelRegistry | None = None):
        self.registry = registry or get_anomaly_registry()

    def is_ready(self) -> bool:
        return self.registry.ready

    def get_model_info(self) -> dict[str, Any]:
        return self.registry.health()

    def _require_artifact(self) -> dict[str, Any]:
        if not self.registry.load() or not self.registry.artifact:
            raise RuntimeError(self.registry.error or "Anomaly model is unavailable")
        return self.registry.artifact

    @staticmethod
    def _normalized_score(raw_score: float, calibration: dict[str, float]) -> float:
        low = float(calibration["normalization_low"])
        high = float(calibration["normalization_high"])
        if high <= low:
            return 0.0
        return float(np.clip((raw_score - low) / (high - low), 0.0, 1.0))

    def predict_insight(self, feature_window: dict[str, Any]) -> AnomalyInsight:
        artifact = self._require_artifact()
        vector = np.array([[float(feature_window[name]) for name in FEATURE_NAMES]], dtype=float)
        if not np.isfinite(vector).all():
            raise ValueError("Anomaly inference received non-finite feature values")

        scaled = artifact["scaler"].transform(vector)
        raw_score = float(-artifact["model"].decision_function(scaled)[0])
        calibration = artifact["score_calibration"]
        normalized = self._normalized_score(raw_score, calibration)
        is_anomaly = raw_score >= float(calibration["threshold_raw"])

        operator_id = str(feature_window["operator_id"])
        baseline = select_baseline(artifact["baselines"], operator_id)
        evidence = self._build_evidence(feature_window, baseline)
        primary = evidence[0] if evidence else None
        anomaly_type = TYPE_PRIORITY.get(primary.feature, "UNUSUAL_OPERATION") if is_anomaly and primary else "NORMAL_OPERATION"

        now = utc_now_iso()
        return AnomalyInsight(
            timestamp=str(feature_window["window_end"]),
            machine_id=str(feature_window["machine_id"]),
            operator_id=operator_id,
            window_start=str(feature_window["window_start"]),
            window_end=str(feature_window["window_end"]),
            is_anomaly=is_anomaly,
            anomaly_type=anomaly_type,
            anomaly_score=round(normalized, 6),
            current_value=primary.current_value if primary else None,
            baseline_value=primary.baseline_value if primary else None,
            evidence=evidence[:3],
            baseline_source=baseline["source"],
            model_version=str(artifact["model_version"]),
            created_at=now,
        )

    @staticmethod
    def _build_evidence(feature_window: dict[str, Any], baseline: dict[str, Any]) -> list[AnomalyEvidence]:
        evidence: list[AnomalyEvidence] = []
        for feature in FEATURE_NAMES:
            current = float(feature_window[feature])
            stats = baseline["statistics"][feature]
            center = float(stats["median"])
            std = max(float(stats["std"]), 1e-6)
            signed_sigma = (current - center) / std

            # Low productivity is concerning in the negative direction; all other
            # features are interpreted as concerning when elevated.
            relevant_sigma = -signed_sigma if feature == "load_cycles_per_hour" else signed_sigma
            direction = "BELOW" if signed_sigma < 0 else "ABOVE"
            evidence.append(AnomalyEvidence(
                feature=feature,
                current_value=round(current, 6),
                baseline_value=round(center, 6),
                deviation_sigma=round(relevant_sigma, 4),
                direction=direction,
                message=(
                    f"{FEATURE_LABELS[feature]} is {abs(signed_sigma):.1f} standard deviations "
                    f"{direction.lower()} the {baseline['source'].lower().replace('_', ' ')} median."
                ),
            ))
        evidence.sort(key=lambda item: item.deviation_sigma, reverse=True)
        return evidence

    def predict(self, telemetry_record: dict[str, Any]) -> AnomalyResult:
        insight = self.predict_insight(telemetry_record)
        return AnomalyResult(
            machine_id=insight.machine_id,
            timestamp=insight.timestamp,
            is_anomaly=insight.is_anomaly,
            anomaly_score=insight.anomaly_score,
            affected_sensors=[item.feature for item in insight.evidence if item.deviation_sigma > 1.0],
            sensor_scores={item.feature: max(0.0, min(1.0, item.deviation_sigma / 5.0)) for item in insight.evidence},
            confidence=insight.anomaly_score,
            model_version=insight.model_version,
            metadata={"anomaly_type": insight.anomaly_type, "evidence": [e.model_dump() for e in insight.evidence]},
        )

    def batch_predict(self, telemetry_window: Iterable[dict[str, Any]]) -> list[AnomalyResult]:
        return [self.predict(window) for window in telemetry_window]
