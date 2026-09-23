"""
ShiftGuard Edge Sync Worker
===========================

Background worker that periodically queries the SQLite sync_outbox,
batches pending events, and synchronizes them to the Cloud Sync API.
Maintains state for real-time frontend monitoring and handles network failures gracefully.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import httpx
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database.connection import SessionLocal
from backend.app.sync.outbox import OutboxService

logger = logging.getLogger("shiftguard.edge.sync_worker")


class SyncWorker:
    """Manages periodic batch transmission and cloud connection state tracking."""

    def __init__(self):
        self.cloud_connected: bool = True
        self.is_syncing: bool = False
        self.last_sync_time: Optional[str] = None
        self.last_sync_duration_ms: float = 0.0
        self.last_sync_count: int = 0
        self.cloud_override_enabled: Optional[bool] = None  # For testing offline demonstration
        self._task: Optional[asyncio.Task] = None
        self._running: bool = False

    def is_cloud_effectively_enabled(self) -> bool:
        """Return whether cloud sync is currently enabled."""
        if self.cloud_override_enabled is not None:
            return self.cloud_override_enabled
        return settings.CLOUD_ENABLED

    async def sync_once(self) -> Dict[str, Any]:
        """
        Execute a single batch synchronization cycle.
        Returns a dictionary summarizing the sync cycle results.
        """
        start_time = time.monotonic()
        db: Session = SessionLocal()
        try:
            # 1. Check if cloud is configured and enabled
            if not self.is_cloud_effectively_enabled():
                self.cloud_connected = False
                logger.info("[SYNC] Cloud unavailable (air-gapped / simulated disconnect). Events remain in outbox.")
                stats = OutboxService.get_outbox_stats(db)
                return {
                    "status": "cloud_disabled",
                    "cloud_connected": False,
                    "pending_count": stats["pending_count"],
                    "synced": 0,
                }

            # 2. Select eligible pending events (prioritizing INCIDENT > ALERT > TELEMETRY)
            batch = OutboxService.get_pending_events(db, batch_size=settings.SYNC_BATCH_SIZE)
            if not batch:
                # Still check cloud health if outbox is empty
                stats = OutboxService.get_outbox_stats(db)
                self.cloud_connected = True
                return {
                    "status": "idle",
                    "cloud_connected": True,
                    "pending_count": stats["pending_count"],
                    "synced": 0,
                }

            event_ids = [item.event_id for item in batch]
            logger.info(f"[SYNC] {len(batch)} pending events found. Batch started: {event_ids}")

            # 3. Mark batch as SYNCING
            OutboxService.mark_syncing(db, event_ids)
            self.is_syncing = True

            # 4. Prepare JSON batch payload
            payload_events = []
            for item in batch:
                try:
                    p = json.loads(item.payload)
                except Exception:
                    p = {"raw": item.payload}
                payload_events.append({
                    "event_id": item.event_id,
                    "event_type": item.event_type,
                    "created_at": item.created_at,
                    "payload": p,
                })

            # 5. Transmit batch to Cloud Sync API
            logger.info(f"[SYNC] Sent {len(payload_events)} events to {settings.CLOUD_SYNC_URL}")
            try:
                async with httpx.AsyncClient(timeout=8.0) as client:
                    resp = await client.post(
                        settings.CLOUD_SYNC_URL,
                        json={"events": payload_events},
                    )

                if resp.status_code == 200:
                    data = resp.json()
                    accepted = data.get("accepted", 0)
                    duplicate = data.get("duplicate", 0)
                    results = data.get("results", [])

                    synced_ids = []
                    failed_map = {}

                    for res in results:
                        eid = res.get("event_id")
                        st = res.get("status")
                        if st in ("ACCEPTED", "DUPLICATE"):
                            synced_ids.append(eid)
                        else:
                            failed_map[eid] = res.get("error", "Unknown error")

                    # Mark successfully synced events
                    if synced_ids:
                        OutboxService.mark_synced(db, synced_ids)
                    # Mark any individual failures with backoff
                    for fid, err in failed_map.items():
                        OutboxService.mark_failed(db, fid, err)

                    duration_ms = round((time.monotonic() - start_time) * 1000, 2)
                    self.cloud_connected = True
                    self.last_sync_time = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                    self.last_sync_duration_ms = duration_ms
                    self.last_sync_count = len(synced_ids)

                    logger.info(f"[SYNC] {len(synced_ids)} events synchronized in {duration_ms}ms (Cloud connection active)")
                    stats = OutboxService.get_outbox_stats(db)
                    return {
                        "status": "success",
                        "cloud_connected": True,
                        "synced": len(synced_ids),
                        "pending_count": stats["pending_count"],
                        "duration_ms": duration_ms,
                    }
                else:
                    # Cloud returned non-200 error
                    err_msg = f"HTTP {resp.status_code}: {resp.text}"
                    logger.warning(f"[SYNC] Cloud sync returned error: {err_msg}")
                    for eid in event_ids:
                        OutboxService.mark_failed(db, eid, err_msg)
                    self.cloud_connected = False
                    return {
                        "status": "cloud_error",
                        "cloud_connected": False,
                        "error": err_msg,
                    }

            except Exception as net_err:
                # Network unreachable, connection refused, or timeout
                err_msg = str(net_err)
                logger.warning(f"[SYNC] Cloud unavailable ({err_msg}). Retaining events in local outbox. Retry scheduled.")
                for eid in event_ids:
                    OutboxService.mark_failed(db, eid, err_msg)
                self.cloud_connected = False
                return {
                    "status": "network_error",
                    "cloud_connected": False,
                    "error": err_msg,
                }
        finally:
            self.is_syncing = False
            db.close()

    async def _run_loop(self):
        """Continuous background synchronization loop."""
        logger.info(f"[SYNC] Starting background sync worker (interval={settings.SYNC_INTERVAL_SECONDS}s)")
        while self._running:
            try:
                await self.sync_once()
            except Exception as e:
                logger.error(f"[SYNC] Unexpected error in sync worker loop: {e}")
            await asyncio.sleep(settings.SYNC_INTERVAL_SECONDS)

    def start(self):
        """Start the background sync worker task."""
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._run_loop())

    def stop(self):
        """Stop the background sync worker task."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()


sync_worker = SyncWorker()
