"""Local-first ETA inference, persistence, and sync orchestration."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from backend.app.database.models import EtaPredictionModel, TaskModel, TelemetryModel
from backend.app.ml.eta.features import build_inference_row
from backend.app.ml.eta.predict import GradientBoostingETAPredictor
from backend.app.ml.eta.schemas import ETAPrediction
from backend.app.sync.outbox import OutboxService


class ETAService:
    def __init__(self, predictor: GradientBoostingETAPredictor | None = None):
        self.predictor = predictor or GradientBoostingETAPredictor()

    @staticmethod
    def record_payload(record: EtaPredictionModel) -> dict[str, Any]:
        return {
            "task_id": record.task_id, "machine_id": record.machine_id, "operator_id": record.operator_id,
            "timestamp": record.prediction_timestamp, "planned_minutes": record.planned_minutes,
            "predicted_minutes": record.predicted_minutes, "predicted_remaining_minutes": record.predicted_remaining_minutes,
            "p50": record.p50, "p90": record.p90, "interval_lower": record.interval_lower,
            "interval_upper": record.interval_upper, "uncertainty_minutes": record.uncertainty_minutes,
            "delta_vs_plan_minutes": record.delta_vs_plan_minutes, "why_changed": json.loads(record.why_changed or "[]"),
            "features_version": record.features_version, "model_version": record.model_version,
            "feature_snapshot": json.loads(record.feature_snapshot or "{}"),
        }

    @staticmethod
    def task_payload(task: TaskModel) -> dict[str, Any]:
        return {field: getattr(task, field) for field in (
            "task_id", "machine_id", "operator_id", "task_type", "weather", "operator_skill",
            "machine_age_years", "estimated_time_min", "working_condition",
        )}

    def predict_task(self, db: Session, task_id: str, persist: bool = True) -> ETAPrediction:
        task = db.execute(select(TaskModel).where(TaskModel.task_id == task_id)).scalar_one_or_none()
        if not task:
            raise LookupError(f"Task '{task_id}' not found")
        records = list(db.execute(select(TelemetryModel).where(TelemetryModel.task_id == task_id).order_by(TelemetryModel.timestamp)).scalars())
        telemetry = [{"timestamp": row.timestamp, "load_cycles": row.load_cycles, "idling_time_min": row.idling_time_min, "fuel_used_l": row.fuel_used_l} for row in records]
        task_data = self.task_payload(task)
        features = build_inference_row(task_data, telemetry)
        prediction = self.predictor.predict(task_data, features)
        if not persist:
            return prediction
        snapshot = json.dumps(features, sort_keys=True)
        existing = db.execute(select(EtaPredictionModel).where(
            EtaPredictionModel.task_id == task_id, EtaPredictionModel.model_version == prediction.model_version,
            EtaPredictionModel.feature_snapshot == snapshot,
        ).order_by(desc(EtaPredictionModel.prediction_timestamp))).scalar_one_or_none()
        if existing:
            return ETAPrediction(prediction_id=existing.id, **self.record_payload(existing))
        confidence = max(0.0, min(1.0, 1 - prediction.uncertainty_minutes / max(prediction.predicted_minutes, 1)))
        record = EtaPredictionModel(
            task_id=prediction.task_id, machine_id=prediction.machine_id, operator_id=prediction.operator_id,
            predicted_eta_min=prediction.predicted_minutes, confidence_score=confidence,
            feature_snapshot=snapshot, prediction_timestamp=prediction.timestamp,
            planned_minutes=prediction.planned_minutes, predicted_minutes=prediction.predicted_minutes,
            predicted_remaining_minutes=prediction.predicted_remaining_minutes, p50=prediction.p50, p90=prediction.p90,
            interval_lower=prediction.interval_lower, interval_upper=prediction.interval_upper,
            uncertainty_minutes=prediction.uncertainty_minutes, delta_vs_plan_minutes=prediction.delta_vs_plan_minutes,
            why_changed=json.dumps(prediction.why_changed), features_version=prediction.features_version, model_version=prediction.model_version,
        )
        db.add(record); db.commit(); db.refresh(record)
        OutboxService.enqueue_event(db, "ETA", {"id": record.id, **self.record_payload(record)}, event_id=f"eta-{record.id}")
        return prediction.model_copy(update={"prediction_id": record.id})

    def list_predictions(self, db: Session, task_id: str | None = None, limit: int = 100) -> list[EtaPredictionModel]:
        statement = select(EtaPredictionModel)
        if task_id:
            statement = statement.where(EtaPredictionModel.task_id == task_id)
        return list(db.execute(statement.order_by(desc(EtaPredictionModel.prediction_timestamp)).limit(limit)).scalars())


eta_service = ETAService()
