"""
ShiftGuard Telemetry REST API
=============================

Exposes endpoints for querying latest snapshots and historical timeseries.
All business logic is cleanly delegated to TelemetryService.
"""

from typing import List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.schemas.telemetry import TelemetryResponse
from backend.app.services.telemetry_service import TelemetryService

router = APIRouter(prefix="/api/telemetry", tags=["Telemetry"])


@router.get("/latest", response_model=Union[TelemetryResponse, List[TelemetryResponse]])
def get_latest_telemetry(
    machine_id: Optional[str] = Query(None, description="Optional machine ID filter"),
    db: Session = Depends(get_db),
):
    """
    Retrieve the most recent telemetry snapshot.
    If machine_id is specified, returns the latest record for that machine.
    If omitted, returns the latest record for every distinct machine in the fleet.
    """
    result = TelemetryService.get_latest(db, machine_id=machine_id)
    if machine_id and not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No telemetry found for machine '{machine_id}'",
        )

    from backend.app.edge.safety_features import to_canonical_operating_state

    if isinstance(result, list):
        for r in result:
            r.operating_state = to_canonical_operating_state(
                r.operating_state, r.machine_speed_kmh, r.engine_rpm
            )
    elif result:
        result.operating_state = to_canonical_operating_state(
            result.operating_state, result.machine_speed_kmh, result.engine_rpm
        )

    return result


@router.get("", response_model=List[TelemetryResponse])
@router.get("/history", response_model=List[TelemetryResponse])
def get_telemetry_history(
    machine_id: Optional[str] = Query(None, description="Filter by machinery ID"),
    operator_id: Optional[str] = Query(None, description="Filter by operator ID"),
    task_id: Optional[str] = Query(None, description="Filter by task ID"),
    start_time: Optional[str] = Query(None, description="Filter records on or after ISO timestamp"),
    end_time: Optional[str] = Query(None, description="Filter records on or before ISO timestamp"),
    limit: int = Query(100, ge=1, le=1000, description="Max records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    db: Session = Depends(get_db),
):
    """
    Query historical telemetry timeseries with optional multi-parameter filtering.
    Records are ordered chronologically by timestamp ascending.
    Accessible via both GET /api/telemetry and GET /api/telemetry/history.
    """
    return TelemetryService.get_history(
        db=db,
        machine_id=machine_id,
        operator_id=operator_id,
        task_id=task_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        offset=offset,
    )
