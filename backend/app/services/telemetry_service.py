"""
ShiftGuard Telemetry Service
============================

Domain service responsible for:
- Validating raw telemetry payloads against canonical Pydantic schemas.
- Storing valid telemetry records into SQLite with duplicate detection.
- Querying latest machine snapshots and historical telemetry timeseries.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union
from pydantic import ValidationError
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from backend.app.database.models import TelemetryModel
from backend.app.edge.safety_features import to_canonical_operating_state
from backend.app.schemas.telemetry import TelemetryResponse

logger = logging.getLogger("shiftguard.telemetry")


class TelemetryService:
    """
    Clean business logic service for telemetry ingestion, validation,
    storage, and historical retrieval.
    """

    @staticmethod
    def validate_telemetry(payload: Union[Dict[str, Any], str]) -> TelemetryResponse:
        """
        Validate incoming telemetry payload using canonical TelemetryResponse schema.
        Raises ValidationError if fields or physical bounds are invalid.
        """
        try:
            if isinstance(payload, str):
                validated = TelemetryResponse.model_validate_json(payload)
            else:
                validated = TelemetryResponse.model_validate(payload)

            logger.info(
                f"[TELEMETRY VALIDATION] Telemetry validated successfully: "
                f"machine={validated.machine_id}, state={validated.operating_state}, ts={validated.timestamp}"
            )
            return validated
        except ValidationError as e:
            logger.warning(f"[TELEMETRY VALIDATION] Validation failed: {e.errors()}")
            raise

    @staticmethod
    def store_telemetry(db: Session, telemetry: TelemetryResponse) -> Tuple[TelemetryModel, bool]:
        """
        Persist a validated telemetry record to SQLite.
        Detects duplicate events (same machine_id and timestamp) and handles idempotently.

        Returns:
            Tuple[TelemetryModel, bool]: (record, is_new)
        """
        # Duplicate detection check
        existing = db.execute(
            select(TelemetryModel).where(
                TelemetryModel.machine_id == telemetry.machine_id,
                TelemetryModel.timestamp == telemetry.timestamp,
            )
        ).scalar_one_or_none()

        if existing:
            logger.info(
                f"[TELEMETRY STORAGE] Duplicate event detected for {telemetry.machine_id} "
                f"at {telemetry.timestamp} - preserved existing record (id={existing.id})"
            )
            return existing, False

        # Create new database record
        telemetry_dict = telemetry.model_dump(exclude={"id"})
        record = TelemetryModel(**telemetry_dict)
        db.add(record)
        db.commit()
        db.refresh(record)

        logger.info(
            f"[TELEMETRY STORAGE] Saved telemetry record id={record.id} "
            f"for machine {record.machine_id} at {record.timestamp}"
        )
        return record, True

    @staticmethod
    def get_latest(
        db: Session, machine_id: Optional[str] = None
    ) -> Union[TelemetryModel, List[TelemetryModel], None]:
        """
        Retrieve latest telemetry record for a specific machine or all distinct machines.
        """
        if machine_id:
            return db.execute(
                select(TelemetryModel)
                .where(TelemetryModel.machine_id == machine_id)
                .order_by(desc(TelemetryModel.timestamp), desc(TelemetryModel.id))
                .limit(1)
            ).scalar_one_or_none()

        machine_ids = db.execute(
            select(TelemetryModel.machine_id).distinct()
        ).scalars().all()

        latest_records = []
        for mid in machine_ids:
            rec = db.execute(
                select(TelemetryModel)
                .where(TelemetryModel.machine_id == mid)
                .order_by(desc(TelemetryModel.timestamp), desc(TelemetryModel.id))
                .limit(1)
            ).scalar_one_or_none()
            if rec:
                latest_records.append(rec)

        return latest_records

    @staticmethod
    def get_history(
        db: Session,
        machine_id: Optional[str] = None,
        operator_id: Optional[str] = None,
        task_id: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[TelemetryModel]:
        """
        Query historical telemetry with multi-parameter filtering and chronological ordering.
        """
        stmt = select(TelemetryModel)

        if machine_id:
            stmt = stmt.where(TelemetryModel.machine_id == machine_id)
        if operator_id:
            stmt = stmt.where(TelemetryModel.operator_id == operator_id)
        if task_id:
            stmt = stmt.where(TelemetryModel.task_id == task_id)
        if start_time:
            stmt = stmt.where(TelemetryModel.timestamp >= start_time)
        if end_time:
            stmt = stmt.where(TelemetryModel.timestamp <= end_time)

        stmt = stmt.order_by(TelemetryModel.timestamp.asc(), TelemetryModel.id.asc()).offset(offset).limit(limit)
        return db.execute(stmt).scalars().all()
