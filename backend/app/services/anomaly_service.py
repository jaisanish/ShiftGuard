"""Application service joining telemetry history, ML inference, persistence and sync."""

from __future__ import annotations

import json
from typing import Any, Optional

import pandas as pd
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database.models import AnomalyModel, TelemetryModel
from backend.app.ml.anomaly.baseline import select_baseline
from backend.app.ml.anomaly.features import build_feature_windows
from backend.app.ml.anomaly.model_registry import get_anomaly_registry
from backend.app.ml.anomaly.predict import IsolationForestAnomalyPredictor
from backend.app.ml.anomaly.schemas import AnomalyInsight
from backend.app.sync.event_serializer import serialize_anomaly_event
from backend.app.sync.outbox import OutboxService


TELEMETRY_FEATURE_COLUMNS = [
    "timestamp", "machine_id", "operator_id", "fuel_used_l", "idling_time_min",
    "load_cycles", "operating_state", "seatbelt_status", "machine_speed_kmh",
    "proximity_distance_m", "fault_code",
]


class AnomalyService:
    def __init__(self, predictor: IsolationForestAnomalyPredictor | None = None):
        self.predictor = predictor or IsolationForestAnomalyPredictor()

    @staticmethod
    def _telemetry_dict(record: TelemetryModel) -> dict[str, Any]:
        return {column: getattr(record, column) for column in TELEMETRY_FEATURE_COLUMNS}

    def latest_feature_window(
        self, db: Session, machine_id: str, operator_id: Optional[str] = None
    ) -> dict[str, Any]:
        query = select(TelemetryModel).where(TelemetryModel.machine_id == machine_id)
        if operator_id:
            query = query.where(TelemetryModel.operator_id == operator_id)
        records = list(
            db.execute(query.order_by(TelemetryModel.timestamp.desc()).limit(1000)).scalars().all()
        )
        if not records:
            raise LookupError(f"No telemetry found for machine '{machine_id}'")
        records.reverse()
        windows = build_feature_windows(pd.DataFrame([self._telemetry_dict(record) for record in records]))
        if windows.empty:
            raise ValueError("Insufficient telemetry for a 15-minute anomaly feature window")
        return windows.iloc[-1].to_dict()

    def infer_latest(
        self, db: Session, machine_id: str, operator_id: Optional[str] = None
    ) -> AnomalyInsight:
        window = self.latest_feature_window(db, machine_id, operator_id)
        return self.predictor.predict_insight(window)

    @staticmethod
    def persist(db: Session, insight: AnomalyInsight) -> tuple[AnomalyModel, bool]:
        existing = db.execute(
            select(AnomalyModel).where(
                AnomalyModel.machine_id == insight.machine_id,
                AnomalyModel.operator_id == insight.operator_id,
                AnomalyModel.window_end == insight.window_end,
                AnomalyModel.model_version == insight.model_version,
            )
        ).scalar_one_or_none()
        if existing:
            return existing, False

        primary_feature = insight.evidence[0].feature if insight.evidence else None
        record = AnomalyModel(
            machine_id=insight.machine_id,
            operator_id=insight.operator_id,
            window_start=insight.window_start,
            window_end=insight.window_end,
            anomaly_type=insight.anomaly_type,
            anomaly_score=insight.anomaly_score,
            current_value=insight.current_value,
            baseline_value=insight.baseline_value,
            evidence=json.dumps([item.model_dump() for item in insight.evidence]),
            baseline_source=insight.baseline_source,
            sensor_name=primary_feature,
            detected_value=insight.current_value,
            timestamp=insight.timestamp,
            model_version=insight.model_version,
            created_at=insight.created_at,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record, True

    def analyze(
        self,
        db: Session,
        machine_id: str,
        operator_id: Optional[str] = None,
        persist_if_anomaly: bool = True,
    ) -> AnomalyInsight:
        insight = self.infer_latest(db, machine_id, operator_id)
        if insight.is_anomaly and persist_if_anomaly:
            record, is_new = self.persist(db, insight)
            insight.id = record.id
            if is_new:
                OutboxService.enqueue_event(
                    db,
                    "ANOMALY",
                    serialize_anomaly_event(record),
                    event_id=f"anomaly-{record.id}",
                )
        return insight

    @staticmethod
    def list_anomalies(
        db: Session,
        machine_id: Optional[str] = None,
        operator_id: Optional[str] = None,
        anomaly_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AnomalyModel]:
        query = select(AnomalyModel)
        if machine_id:
            query = query.where(AnomalyModel.machine_id == machine_id)
        if operator_id:
            query = query.where(AnomalyModel.operator_id == operator_id)
        if anomaly_type:
            query = query.where(AnomalyModel.anomaly_type == anomaly_type.upper())
        query = query.order_by(desc(AnomalyModel.window_end)).limit(limit).offset(offset)
        return list(db.execute(query).scalars().all())

    @staticmethod
    def get_anomaly(db: Session, anomaly_id: str) -> Optional[AnomalyModel]:
        return db.execute(select(AnomalyModel).where(AnomalyModel.id == anomaly_id)).scalar_one_or_none()

    @staticmethod
    def get_baseline(operator_id: str) -> dict[str, Any]:
        registry = get_anomaly_registry()
        if not registry.load() or not registry.artifact:
            raise RuntimeError(registry.error or "Anomaly model is unavailable")
        profile = select_baseline(registry.artifact["baselines"], operator_id)
        return {
            **profile,
            "minimum_operator_windows": int(
                registry.artifact["baselines"].get(
                    "minimum_operator_windows", settings.ANOMALY_MIN_OPERATOR_WINDOWS
                )
            ),
        }

    @staticmethod
    def summary(db: Session, operator_id: str) -> dict[str, Any]:
        grouped = db.execute(
            select(AnomalyModel.anomaly_type, func.count(AnomalyModel.id))
            .where(AnomalyModel.operator_id == operator_id)
            .group_by(AnomalyModel.anomaly_type)
        ).all()
        records = AnomalyService.list_anomalies(db, operator_id=operator_id, limit=1)
        latest = records[0] if records else None
        latest_insight = None
        if latest:
            latest_insight = AnomalyInsight(
                id=latest.id,
                timestamp=latest.timestamp,
                machine_id=latest.machine_id,
                operator_id=latest.operator_id,
                window_start=latest.window_start,
                window_end=latest.window_end,
                is_anomaly=True,
                anomaly_type=latest.anomaly_type,
                anomaly_score=latest.anomaly_score,
                current_value=latest.current_value,
                baseline_value=latest.baseline_value,
                evidence=json.loads(latest.evidence or "[]"),
                baseline_source=latest.baseline_source,
                model_version=latest.model_version,
                created_at=latest.created_at,
            )
        return {
            "operator_id": operator_id,
            "total_anomalies": int(sum(count for _, count in grouped)),
            "by_type": {kind: int(count) for kind, count in grouped},
            "latest": latest_insight,
            "model_health": get_anomaly_registry().health(),
        }


anomaly_service = AnomalyService()
