"""
ShiftGuard Cloud Batch Ingestion & Idempotency Service
======================================================

Processes incoming event batches from edge outbox synchronization.
Enforces absolute idempotency: duplicate event submissions are recognized
and acknowledged without creating duplicate database records.
"""

import logging
from typing import Any, Dict, List
from sqlalchemy.orm import Session

from backend.app.cloud.repositories.event_repo import EventRepository
from backend.app.cloud.repositories.telemetry_repo import TelemetryRepository
from backend.app.cloud.repositories.alert_repo import AlertRepository
from backend.app.cloud.repositories.incident_repo import IncidentRepository
from backend.app.cloud.repositories.anomaly_repo import AnomalyRepository

logger = logging.getLogger("shiftguard.cloud.sync")


class CloudSyncService:
    """Orchestrates cloud event batch ingestion and idempotency."""

    @staticmethod
    def ingest_batch(db: Session, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process a batch of sync events received from an edge node.

        Returns:
            Dict containing counts of accepted, duplicate, and failed events
            along with per-event resolution status.
        """
        accepted_count = 0
        duplicate_count = 0
        failed_count = 0
        results = []

        logger.info(f"[SYNC] Ingesting batch of {len(events)} events from edge")

        for event in events:
            event_id = event.get("event_id")
            event_type = str(event.get("event_type", "UNKNOWN")).upper().strip()
            payload = event.get("payload") or {}

            if not event_id:
                failed_count += 1
                results.append({
                    "event_id": "MISSING",
                    "status": "FAILED",
                    "error": "Missing required 'event_id' idempotency key"
                })
                continue

            # Idempotency check: Has this event already been processed?
            if EventRepository.is_duplicate(db, event_id):
                logger.info(f"[SYNC] Duplicate event {event_id} ({event_type}) ignored (idempotent)")
                duplicate_count += 1
                results.append({
                    "event_id": event_id,
                    "status": "DUPLICATE",
                    "message": "Event already processed and persisted in cloud database"
                })
                continue

            # Process novel event
            try:
                if event_type == "TELEMETRY":
                    TelemetryRepository.insert_telemetry(db, event_id, payload)
                elif event_type in ("ALERT", "ALERT_ACKNOWLEDGED"):
                    AlertRepository.upsert_alert(db, event_id, payload)
                elif event_type in ("INCIDENT", "INCIDENT_ACKNOWLEDGED"):
                    IncidentRepository.upsert_incident(db, event_id, payload)
                elif event_type == "ANOMALY":
                    AnomalyRepository.insert_anomaly(db, event_id, payload)
                else:
                    logger.warning(f"[SYNC] Unknown event type '{event_type}' for event {event_id}. Recorded in log.")

                # Record in idempotency ledger
                EventRepository.record_event(db, event_id, event_type, status="ACCEPTED")
                db.commit()

                accepted_count += 1
                results.append({
                    "event_id": event_id,
                    "status": "ACCEPTED"
                })
            except Exception as e:
                db.rollback()
                logger.error(f"[SYNC] Error processing event {event_id}: {e}")
                failed_count += 1
                results.append({
                    "event_id": event_id,
                    "status": "FAILED",
                    "error": str(e)
                })

        logger.info(
            f"[SYNC] Batch complete: {accepted_count} accepted, "
            f"{duplicate_count} duplicate, {failed_count} failed."
        )

        return {
            "status": "ok",
            "total": len(events),
            "accepted": accepted_count,
            "duplicate": duplicate_count,
            "failed": failed_count,
            "results": results,
        }
