"""Cloud repository for synchronized Phase 6 anomaly analytics."""

from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from backend.app.cloud.models import CloudAnomalyModel


class AnomalyRepository:
    @staticmethod
    def insert_anomaly(db: Session, event_id: str, payload: dict[str, Any]) -> CloudAnomalyModel:
        record = CloudAnomalyModel(
            id=str(payload.get("id") or event_id),
            event_id=event_id,
            timestamp=str(payload.get("timestamp", "")),
            machine_id=str(payload.get("machine_id", "")),
            operator_id=str(payload.get("operator_id", "")),
            window_start=str(payload.get("window_start", "")),
            window_end=str(payload.get("window_end", "")),
            anomaly_type=str(payload.get("anomaly_type", "UNUSUAL_OPERATION")),
            anomaly_score=float(payload.get("anomaly_score", 0.0)),
            current_value=payload.get("current_value"),
            baseline_value=payload.get("baseline_value"),
            evidence=str(payload.get("evidence", "[]")),
            baseline_source=str(payload.get("baseline_source", "GLOBAL_FALLBACK")),
            model_version=str(payload.get("model_version", "unknown")),
            created_at=str(payload.get("created_at") or payload.get("timestamp", "")),
        )
        db.add(record)
        return record

    @staticmethod
    def get_historical_anomalies(
        db: Session,
        machine_id: Optional[str] = None,
        operator_id: Optional[str] = None,
        anomaly_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[CloudAnomalyModel]:
        query = select(CloudAnomalyModel)
        if machine_id:
            query = query.where(CloudAnomalyModel.machine_id == machine_id)
        if operator_id:
            query = query.where(CloudAnomalyModel.operator_id == operator_id)
        if anomaly_type:
            query = query.where(CloudAnomalyModel.anomaly_type == anomaly_type.upper())
        query = query.order_by(desc(CloudAnomalyModel.window_end)).limit(limit).offset(offset)
        return list(db.execute(query).scalars().all())
