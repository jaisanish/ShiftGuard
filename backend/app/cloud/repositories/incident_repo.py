"""
Cloud Incident Repository
========================
"""

import json
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from backend.app.cloud.models import CloudIncidentModel

logger = logging.getLogger("shiftguard.cloud.repo.incident")


class IncidentRepository:
    """Manages cloud persistence and historical queries for synchronized safety incidents."""

    @staticmethod
    def upsert_incident(
        db: Session, event_id: str, payload: Dict[str, Any]
    ) -> CloudIncidentModel:
        """Insert or update a synchronized safety incident in the cloud database."""
        inc_id = payload.get("id") or payload.get("incident_id") or event_id

        evidence = payload.get("evidence")
        if isinstance(evidence, dict):
            evidence_str = json.dumps(evidence)
        else:
            evidence_str = str(evidence) if evidence else None

        context_buf = payload.get("context_buffer")
        if isinstance(context_buf, dict):
            context_buf_str = json.dumps(context_buf)
        else:
            context_buf_str = str(context_buf) if context_buf else None

        existing = db.execute(
            select(CloudIncidentModel).where(CloudIncidentModel.id == inc_id)
        ).scalar_one_or_none()

        if existing:
            existing.status = payload.get("status", existing.status)
            existing.severity = payload.get("severity", existing.severity)
            existing.resolved_at = payload.get("resolved_at", existing.resolved_at)
            if context_buf_str:
                existing.context_buffer = context_buf_str
            return existing

        record = CloudIncidentModel(
            id=inc_id,
            event_id=event_id,
            machine_id=payload.get("machine_id", ""),
            operator_id=payload.get("operator_id", ""),
            task_id=payload.get("task_id", "UNKNOWN"),
            alert_id=payload.get("alert_id"),
            incident_type=payload.get("incident_type", "HAZARD"),
            severity=payload.get("severity", "CRITICAL"),
            summary=payload.get("summary", ""),
            evidence=evidence_str,
            context_buffer=context_buf_str,
            started_at=payload.get("started_at") or payload.get("triggered_at", ""),
            triggered_at=payload.get("triggered_at", ""),
            resolved_at=payload.get("resolved_at"),
            status=payload.get("status", "OPEN"),
            gps_zone=payload.get("gps_zone"),
            timestamp=payload.get("timestamp", ""),
        )
        db.add(record)
        return record

    @staticmethod
    def get_historical_incidents(
        db: Session,
        machine_id: Optional[str] = None,
        operator_id: Optional[str] = None,
        severity: Optional[str] = None,
        incident_type: Optional[str] = None,
        status: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[CloudIncidentModel]:
        """Query synchronized incidents with optional filters."""
        query = select(CloudIncidentModel)
        if machine_id:
            query = query.where(CloudIncidentModel.machine_id == machine_id)
        if operator_id:
            query = query.where(CloudIncidentModel.operator_id == operator_id)
        if severity:
            query = query.where(CloudIncidentModel.severity == severity.upper())
        if incident_type:
            query = query.where(CloudIncidentModel.incident_type == incident_type.upper())
        if status:
            query = query.where(CloudIncidentModel.status == status.upper())
        if start_time:
            query = query.where(CloudIncidentModel.triggered_at >= start_time)
        if end_time:
            query = query.where(CloudIncidentModel.triggered_at <= end_time)

        query = query.order_by(desc(CloudIncidentModel.triggered_at)).limit(limit).offset(offset)
        return list(db.execute(query).scalars().all())

    @staticmethod
    def get_incident_by_id(db: Session, incident_id: str) -> Optional[CloudIncidentModel]:
        """Retrieve a specific synchronized incident by ID."""
        return db.execute(
            select(CloudIncidentModel).where(CloudIncidentModel.id == incident_id)
        ).scalar_one_or_none()
