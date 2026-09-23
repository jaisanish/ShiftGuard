"""
ShiftGuard Edge Sync Outbox Repository
======================================

Transactional management of the SQLite `sync_outbox` table.
Ensures local-first ordering: records are persisted locally in SQLite before being enqueued.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import case, desc, func, select
from sqlalchemy.orm import Session

from backend.app.database.models import SyncOutboxModel, utc_now_iso
from backend.app.sync.retry import calculate_next_retry_iso

logger = logging.getLogger("shiftguard.edge.outbox")


class OutboxService:
    """Manages enqueueing, batching, and state transitions for the sync outbox."""

    @staticmethod
    def enqueue_event(
        db: Session,
        event_type: str,
        payload: Dict[str, Any],
        event_id: Optional[str] = None,
    ) -> SyncOutboxModel:
        """
        Enqueue a sync event into SQLite sync_outbox.
        Enforces local-first ordering: MUST be called after local database write.
        """
        eid = event_id or str(uuid.uuid4())
        payload_str = json.dumps(payload)
        now_str = utc_now_iso()

        record = SyncOutboxModel(
            event_id=eid,
            event_type=event_type.upper().strip(),
            payload=payload_str,
            created_at=now_str,
            status="PENDING",
            retry_count=0,
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        logger.info(f"[SYNC] Enqueued {record.event_type} event {record.event_id} into outbox (local-first)")
        return record

    @staticmethod
    def get_pending_events(db: Session, batch_size: int = 25) -> List[SyncOutboxModel]:
        """
        Retrieve eligible pending events for synchronization.
        Priority: INCIDENT > ALERT > TELEMETRY > other, then created_at ascending.
        Includes FAILED records whose exponential backoff timer has matured.
        """
        now_iso = utc_now_iso()

        # Priority case statement: INCIDENT=1, ALERT=2, everything else=3
        priority_order = case(
            (SyncOutboxModel.event_type.in_(["INCIDENT", "INCIDENT_ACKNOWLEDGED"]), 1),
            (SyncOutboxModel.event_type.in_(["ALERT", "ALERT_ACKNOWLEDGED"]), 2),
            else_=3,
        )

        query = (
            select(SyncOutboxModel)
            .where(
                (SyncOutboxModel.status == "PENDING")
                | (
                    (SyncOutboxModel.status == "FAILED")
                    & (SyncOutboxModel.next_retry_at <= now_iso)
                )
            )
            .order_by(priority_order, SyncOutboxModel.created_at.asc())
            .limit(batch_size)
        )
        return list(db.execute(query).scalars().all())

    @staticmethod
    def mark_syncing(db: Session, event_ids: List[str]) -> None:
        """Atomically transition batch events from PENDING to SYNCING."""
        if not event_ids:
            return
        records = db.execute(
            select(SyncOutboxModel).where(SyncOutboxModel.event_id.in_(event_ids))
        ).scalars().all()
        for r in records:
            r.status = "SYNCING"
        db.commit()

    @staticmethod
    def mark_synced(db: Session, event_ids: List[str]) -> None:
        """Atomically mark successfully synchronized events as SYNCED."""
        if not event_ids:
            return
        now_iso = utc_now_iso()
        records = db.execute(
            select(SyncOutboxModel).where(SyncOutboxModel.event_id.in_(event_ids))
        ).scalars().all()
        for r in records:
            r.status = "SYNCED"
            r.synced_at = now_iso
        db.commit()

    @staticmethod
    def mark_failed(db: Session, event_id: str, error_message: str) -> None:
        """Record synchronization failure with exponential backoff scheduling."""
        record = db.execute(
            select(SyncOutboxModel).where(SyncOutboxModel.event_id == event_id)
        ).scalar_one_or_none()
        if not record:
            return
        record.retry_count += 1
        record.status = "FAILED"
        record.last_error = str(error_message)
        record.next_retry_at = calculate_next_retry_iso(record.retry_count)
        db.commit()

    @staticmethod
    def get_outbox_stats(db: Session) -> Dict[str, Any]:
        """Query real-time summary statistics of the sync outbox."""
        pending_count = db.execute(
            select(func.count(SyncOutboxModel.event_id)).where(SyncOutboxModel.status == "PENDING")
        ).scalar_one() or 0

        syncing_count = db.execute(
            select(func.count(SyncOutboxModel.event_id)).where(SyncOutboxModel.status == "SYNCING")
        ).scalar_one() or 0

        synced_count = db.execute(
            select(func.count(SyncOutboxModel.event_id)).where(SyncOutboxModel.status == "SYNCED")
        ).scalar_one() or 0

        failed_count = db.execute(
            select(func.count(SyncOutboxModel.event_id)).where(SyncOutboxModel.status == "FAILED")
        ).scalar_one() or 0

        last_synced = db.execute(
            select(SyncOutboxModel.synced_at)
            .where(SyncOutboxModel.status == "SYNCED")
            .order_by(desc(SyncOutboxModel.synced_at))
            .limit(1)
        ).scalar_one_or_none()

        return {
            "pending_count": pending_count,
            "syncing_count": syncing_count,
            "synced_count": synced_count,
            "failed_count": failed_count,
            "total_unprocessed": pending_count + syncing_count + failed_count,
            "last_synced_at": last_synced,
        }
