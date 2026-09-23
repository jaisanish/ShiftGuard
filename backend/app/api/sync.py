"""
ShiftGuard Cloud Sync & Outbox Monitoring Endpoints
===================================================

Provides endpoints for:
- POST /api/sync/events: Cloud batch ingestion with idempotency guarantees.
- GET /api/sync/status: Edge-to-cloud outbox status and connectivity metrics.
- POST /api/sync/trigger: Manual outbox flush cycle.
- POST /api/sync/toggle-cloud: Simulation toggle for offline demonstrations.
- GET /api/cloud/health: Health check for cloud backend database.
"""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.cloud.cloud_db import get_cloud_db
from backend.app.cloud.cloud_health import get_cloud_health
from backend.app.cloud.sync_service import CloudSyncService
from backend.app.database.connection import get_db
from backend.app.sync.outbox import OutboxService
from backend.app.sync.sync_worker import sync_worker

logger = logging.getLogger("shiftguard.api.sync")

router = APIRouter(tags=["Cloud Synchronization"])


# ============================================================================
# Request / Response Schemas
# ============================================================================
class SyncEventItem(BaseModel):
    event_id: str = Field(..., description="Unique event identifier (Idempotency Key)")
    event_type: str = Field(..., description="TELEMETRY, ALERT, INCIDENT, etc.")
    created_at: Optional[str] = Field(None, description="ISO UTC timestamp")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Structured event payload")


class SyncBatchRequest(BaseModel):
    events: List[SyncEventItem] = Field(..., description="Batch of events to ingest")


class SyncStatusResponse(BaseModel):
    cloud_connected: bool
    is_syncing: bool
    pending_count: int
    syncing_count: int
    synced_count: int
    failed_count: int
    total_unprocessed: int
    last_synced_at: Optional[str] = None
    last_sync_duration_ms: float = 0.0


# ============================================================================
# 1. Cloud Batch Ingestion (Cloud Endpoint)
# ============================================================================
@router.post("/api/sync/events", status_code=status.HTTP_200_OK)
def ingest_sync_events(
    batch: SyncBatchRequest,
    cloud_db: Session = Depends(get_cloud_db),
):
    """
    Ingest a batch of synchronization events into the Cloud Database.
    Guarantees strict idempotency via event_id verification: duplicate submissions
    are acknowledged without creating duplicate records in the cloud database.
    """
    events_raw = [item.model_dump() for item in batch.events]
    result = CloudSyncService.ingest_batch(cloud_db, events_raw)
    return result


# ============================================================================
# 2. Edge Outbox & Cloud Status (Edge Monitoring Endpoint)
# ============================================================================
@router.get("/api/sync/status", response_model=SyncStatusResponse)
def get_sync_status(edge_db: Session = Depends(get_db)):
    """
    Retrieve real-time edge sync outbox queue statistics and cloud connection state.
    Used by the operator cockpit to display live sync indicators.
    """
    stats = OutboxService.get_outbox_stats(edge_db)
    return SyncStatusResponse(
        cloud_connected=sync_worker.cloud_connected,
        is_syncing=sync_worker.is_syncing,
        pending_count=stats["pending_count"],
        syncing_count=stats["syncing_count"],
        synced_count=stats["synced_count"],
        failed_count=stats["failed_count"],
        total_unprocessed=stats["total_unprocessed"],
        last_synced_at=stats["last_synced_at"] or sync_worker.last_sync_time,
        last_sync_duration_ms=sync_worker.last_sync_duration_ms,
    )


# ============================================================================
# 3. Manual Sync Trigger (Testing & Operator Action)
# ============================================================================
@router.post("/api/sync/trigger")
async def trigger_sync():
    """Immediately execute an outbox batch synchronization cycle."""
    result = await sync_worker.sync_once()
    return {
        "status": "triggered",
        "result": result,
    }


# ============================================================================
# 4. Cloud Disconnect / Reconnect Simulation Toggle (Judging & Demo Support)
# ============================================================================
@router.post("/api/sync/toggle-cloud")
def toggle_cloud_connection(
    connected: bool = Query(..., description="Set True for cloud connected, False for disconnected")
):
    """
    Simulate cloud network disconnection or restoration without restarting servers.
    Essential for live demonstrations of offline-first operation.
    """
    sync_worker.cloud_override_enabled = connected
    sync_worker.cloud_connected = connected
    logger.info(f"[SYNC] Cloud connectivity toggle set to: connected={connected}")
    return {
        "cloud_connected": connected,
        "message": f"Cloud connectivity simulation is now {'CONNECTED' if connected else 'DISCONNECTED'}",
    }


# ============================================================================
# 5. Cloud Service Health
# ============================================================================
@router.get("/api/cloud/health")
def cloud_health():
    """Check connectivity and operational health of the cloud database."""
    return get_cloud_health()
