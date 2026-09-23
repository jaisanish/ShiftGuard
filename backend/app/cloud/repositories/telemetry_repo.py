"""
Cloud Telemetry Repository
==========================
"""

import logging
from typing import Any, Dict, List, Optional
from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from backend.app.cloud.models import CloudTelemetryModel

logger = logging.getLogger("shiftguard.cloud.repo.telemetry")


class TelemetryRepository:
    """Manages cloud persistence and historical queries for fleet telemetry."""

    @staticmethod
    def insert_telemetry(
        db: Session, event_id: str, payload: Dict[str, Any]
    ) -> CloudTelemetryModel:
        """Insert a synchronized telemetry record into the cloud database."""
        record = CloudTelemetryModel(
            event_id=event_id,
            timestamp=payload.get("timestamp", ""),
            machine_id=payload.get("machine_id", ""),
            operator_id=payload.get("operator_id", ""),
            engine_hours=float(payload.get("engine_hours", 0.0) or 0.0),
            engine_rpm=float(payload.get("engine_rpm", 0.0) or 0.0),
            engine_load_pct=float(payload.get("engine_load_pct", 0.0) or 0.0),
            machine_speed_kmh=float(payload.get("machine_speed_kmh", 0.0) or 0.0),
            fuel_used_l=float(payload.get("fuel_used_l", 0.0) or 0.0),
            idling_time_min=float(payload.get("idling_time_min", 0.0) or 0.0),
            load_cycles=int(payload.get("load_cycles", 0) or 0),
            operating_state=str(payload.get("operating_state", "STOPPED")),
            seatbelt_status=str(payload.get("seatbelt_status", "FASTENED")),
            proximity_distance_m=float(payload.get("proximity_distance_m", 42.0) or 42.0),
            gps_zone=str(payload.get("gps_zone", "UNKNOWN")),
            working_condition=str(payload.get("working_condition", "NORMAL")),
            coolant_temp_c=float(payload.get("coolant_temp_c", 82.0) or 82.0),
            hydraulic_oil_temp_c=float(payload.get("hydraulic_oil_temp_c", 68.0) or 68.0),
            fault_code=str(payload.get("fault_code", "NONE")),
            task_id=str(payload.get("task_id", "UNKNOWN")),
        )
        db.add(record)
        return record

    @staticmethod
    def get_historical_telemetry(
        db: Session,
        machine_id: Optional[str] = None,
        operator_id: Optional[str] = None,
        task_id: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[CloudTelemetryModel]:
        """Query synchronized telemetry with optional filters."""
        query = select(CloudTelemetryModel)
        if machine_id:
            query = query.where(CloudTelemetryModel.machine_id == machine_id)
        if operator_id:
            query = query.where(CloudTelemetryModel.operator_id == operator_id)
        if task_id:
            query = query.where(CloudTelemetryModel.task_id == task_id)
        if start_time:
            query = query.where(CloudTelemetryModel.timestamp >= start_time)
        if end_time:
            query = query.where(CloudTelemetryModel.timestamp <= end_time)

        query = query.order_by(desc(CloudTelemetryModel.timestamp)).limit(limit).offset(offset)
        return list(db.execute(query).scalars().all())
