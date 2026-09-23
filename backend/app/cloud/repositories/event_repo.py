"""
Cloud Event Repository (Idempotency Key Ledger)
==============================================
"""

import logging
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.cloud.models import CloudEventLogModel

logger = logging.getLogger("shiftguard.cloud.repo.event")


class EventRepository:
    """Manages cloud event idempotency tracking."""

    @staticmethod
    def is_duplicate(db: Session, event_id: str) -> bool:
        """
        Check if event_id has already been processed and persisted in the cloud database.
        Returns True if duplicate, False if novel.
        """
        existing = db.execute(
            select(CloudEventLogModel).where(CloudEventLogModel.event_id == event_id)
        ).scalar_one_or_none()
        return existing is not None

    @staticmethod
    def record_event(
        db: Session, event_id: str, event_type: str, status: str = "ACCEPTED"
    ) -> CloudEventLogModel:
        """Record event_id in the idempotency ledger."""
        record = CloudEventLogModel(
            event_id=event_id,
            event_type=event_type,
            status=status,
        )
        db.add(record)
        return record
