"""
ShiftGuard Cloud Historical Analytics Endpoints
===============================================

Provides query endpoints for centralized cloud historical data (telemetry, alerts, incidents).
These endpoints query the Cloud PostgreSQL/SQLite database directly and are reserved for
future fleet-wide reporting and ML feature pipelines (Phase 6).
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from backend.app.cloud.cloud_db import get_cloud_db
from backend.app.cloud.repositories.alert_repo import AlertRepository
from backend.app.cloud.repositories.incident_repo import IncidentRepository
from backend.app.cloud.repositories.telemetry_repo import TelemetryRepository

logger = logging.getLogger("shiftguard.api.cloud_history")

router = APIRouter(prefix="/api/cloud", tags=["Cloud Historical Analytics"])


# ============================================================================
# Response Schemas for Cloud Analytics
# ============================================================================
class CloudTelemetryResponse(BaseModel):
    id: int
    event_id: str
    timestamp: str
    machine_id: str
    operator_id: str
    engine_hours: float
    engine_rpm: float
    engine_load_pct: float
    machine_speed_kmh: float
    fuel_used_l: float
    idling_time_min: float
    load_cycles: int
    operating_state: str
    seatbelt_status: str
    proximity_distance_m: float
    gps_zone: str
    working_condition: str
    coolant_temp_c: float
    hydraulic_oil_temp_c: float
    fault_code: str
    task_id: str
    synced_at: str

    model_config = ConfigDict(from_attributes=True)


class CloudAlertResponse(BaseModel):
    id: str
    event_id: str
    timestamp: str
    machine_id: str
    operator_id: str
    task_id: str
    alert_type: str
    severity: str
    status: str
    source: str
    code: Optional[str] = None
    title: str
    message: str
    evidence: Optional[str] = None
    created_at: str
    resolved_at: Optional[str] = None
    acknowledged: bool
    acknowledged_at: Optional[str] = None
    synced_at: str

    model_config = ConfigDict(from_attributes=True)


class CloudIncidentResponse(BaseModel):
    id: str
    event_id: str
    machine_id: str
    operator_id: str
    task_id: str
    alert_id: Optional[str] = None
    incident_type: str
    severity: str
    summary: str
    evidence: Optional[str] = None
    context_buffer: Optional[str] = None
    started_at: str
    triggered_at: str
    resolved_at: Optional[str] = None
    status: str
    gps_zone: Optional[str] = None
    timestamp: str
    synced_at: str

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# 1. Cloud Telemetry History Query
# ============================================================================
@router.get("/telemetry", response_model=List[CloudTelemetryResponse])
def get_cloud_telemetry(
    machine_id: Optional[str] = Query(None, description="Filter by machinery ID"),
    operator_id: Optional[str] = Query(None, description="Filter by operator ID"),
    task_id: Optional[str] = Query(None, description="Filter by task ID"),
    start_time: Optional[str] = Query(None, description="Filter records on or after ISO timestamp"),
    end_time: Optional[str] = Query(None, description="Filter records on or before ISO timestamp"),
    limit: int = Query(100, ge=1, le=1000, description="Max records to return"),
    offset: int = Query(0, ge=0, description="Records to skip"),
    cloud_db: Session = Depends(get_cloud_db),
):
    """Retrieve historical telemetry records persisted in the Cloud Database."""
    return TelemetryRepository.get_historical_telemetry(
        db=cloud_db,
        machine_id=machine_id,
        operator_id=operator_id,
        task_id=task_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        offset=offset,
    )


# ============================================================================
# 2. Cloud Alerts History Query
# ============================================================================
@router.get("/alerts", response_model=List[CloudAlertResponse])
def get_cloud_alerts(
    machine_id: Optional[str] = Query(None, description="Filter by machinery ID"),
    operator_id: Optional[str] = Query(None, description="Filter by operator ID"),
    severity: Optional[str] = Query(None, description="Filter by severity (WARNING, CRITICAL)"),
    status: Optional[str] = Query(None, description="Filter by status (ACTIVE, ACKNOWLEDGED, RESOLVED)"),
    start_time: Optional[str] = Query(None, description="Filter records on or after ISO timestamp"),
    end_time: Optional[str] = Query(None, description="Filter records on or before ISO timestamp"),
    limit: int = Query(100, ge=1, le=1000, description="Max records to return"),
    offset: int = Query(0, ge=0, description="Records to skip"),
    cloud_db: Session = Depends(get_cloud_db),
):
    """Retrieve historical alert records persisted in the Cloud Database."""
    return AlertRepository.get_historical_alerts(
        db=cloud_db,
        machine_id=machine_id,
        operator_id=operator_id,
        severity=severity,
        status=status,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        offset=offset,
    )


# ============================================================================
# 3. Cloud Incidents History Query
# ============================================================================
@router.get("/incidents", response_model=List[CloudIncidentResponse])
def get_cloud_incidents(
    machine_id: Optional[str] = Query(None, description="Filter by machinery ID"),
    operator_id: Optional[str] = Query(None, description="Filter by operator ID"),
    severity: Optional[str] = Query(None, description="Filter by severity (WARNING, CRITICAL)"),
    incident_type: Optional[str] = Query(None, description="Filter by incident type"),
    status: Optional[str] = Query(None, description="Filter by status (OPEN, ACKNOWLEDGED, RESOLVED)"),
    start_time: Optional[str] = Query(None, description="Filter records on or after ISO timestamp"),
    end_time: Optional[str] = Query(None, description="Filter records on or before ISO timestamp"),
    limit: int = Query(100, ge=1, le=1000, description="Max records to return"),
    offset: int = Query(0, ge=0, description="Records to skip"),
    cloud_db: Session = Depends(get_cloud_db),
):
    """Retrieve historical incident records (including context buffers) from Cloud Database."""
    return IncidentRepository.get_historical_incidents(
        db=cloud_db,
        machine_id=machine_id,
        operator_id=operator_id,
        severity=severity,
        incident_type=incident_type,
        status=status,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        offset=offset,
    )
