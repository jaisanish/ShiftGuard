"""
Cloud Alert Repository
======================
"""

import json
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from backend.app.cloud.models import CloudAlertModel

logger = logging.getLogger("shiftguard.cloud.repo.alert")


class AlertRepository:
    """Manages cloud persistence and historical queries for synchronized safety alerts."""

    @staticmethod
    def upsert_alert(
        db: Session, event_id: str, payload: Dict[str, Any]
    ) -> CloudAlertModel:
        """Insert or update a synchronized safety alert in the cloud database."""
        alert_id = payload.get("id") or payload.get("alert_id") or event_id

        evidence = payload.get("evidence")
        if isinstance(evidence, dict):
            evidence_str = json.dumps(evidence)
        else:
            evidence_str = str(evidence) if evidence else None

        existing = db.execute(
            select(CloudAlertModel).where(CloudAlertModel.id == alert_id)
        ).scalar_one_or_none()

        if existing:
            existing.status = payload.get("status", existing.status)
            existing.severity = payload.get("severity", existing.severity)
            existing.message = payload.get("message", existing.message)
            existing.acknowledged = bool(payload.get("acknowledged", existing.acknowledged))
            existing.acknowledged_at = payload.get("acknowledged_at", existing.acknowledged_at)
            existing.resolved_at = payload.get("resolved_at", existing.resolved_at)
            if evidence_str:
                existing.evidence = evidence_str
            return existing

        record = CloudAlertModel(
            id=alert_id,
            event_id=event_id,
            timestamp=payload.get("timestamp", ""),
            machine_id=payload.get("machine_id", ""),
            operator_id=payload.get("operator_id", ""),
            task_id=payload.get("task_id", "UNKNOWN"),
            alert_type=payload.get("alert_type", "HAZARD"),
            severity=payload.get("severity", "WARNING"),
            status=payload.get("status", "ACTIVE"),
            source=payload.get("source", "EDGE"),
            code=payload.get("code", "NONE"),
            title=payload.get("title", "EDGE SAFETY ALERT"),
            message=payload.get("message", ""),
            evidence=evidence_str,
            created_at=payload.get("created_at") or payload.get("timestamp", ""),
            resolved_at=payload.get("resolved_at"),
            acknowledged=bool(payload.get("acknowledged", False)),
            acknowledged_at=payload.get("acknowledged_at"),
        )
        db.add(record)
        return record

    @staticmethod
    def get_historical_alerts(
        db: Session,
        machine_id: Optional[str] = None,
        operator_id: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[CloudAlertModel]:
        """Query synchronized alerts with optional filters."""
        query = select(CloudAlertModel)
        if machine_id:
            query = query.where(CloudAlertModel.machine_id == machine_id)
        if operator_id:
            query = query.where(CloudAlertModel.operator_id == operator_id)
        if severity:
            query = query.where(CloudAlertModel.severity == severity.upper())
        if status:
            query = query.where(CloudAlertModel.status == status.upper())
        if start_time:
            query = query.where(CloudAlertModel.timestamp >= start_time)
        if end_time:
            query = query.where(CloudAlertModel.timestamp <= end_time)

        query = query.order_by(desc(CloudAlertModel.timestamp)).limit(limit).offset(offset)
        return list(db.execute(query).scalars().all())
