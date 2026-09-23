"""
ShiftGuard Safety & Incidents REST Router
=========================================

Endpoints for querying edge safety status, alerts, and incident context buffers.
"""

import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.database.models import AlertModel, IncidentModel, utc_now_iso
from backend.app.edge.engine import edge_safety_engine
from backend.app.schemas.safety import (
    AcknowledgeRequest,
    AcknowledgeResponse,
    AlertResponse,
    IncidentContextBuffer,
    IncidentDetailResponse,
    IncidentResponse,
    SafetyStateResponse,
)

router = APIRouter(prefix="/api", tags=["Safety & Incidents"])


@router.get("/safety/status", response_model=SafetyStateResponse)
def get_safety_status(
    machine_id: str = Query("CAT-797F-102", description="Target machine ID"),
    db: Session = Depends(get_db),
):
    """Retrieve current real-time safety status snapshot for a machine."""
    state = edge_safety_engine.get_safety_state(db, machine_id)
    return SafetyStateResponse(**state)


@router.get("/alerts", response_model=List[AlertResponse])
def get_alerts(
    machine_id: Optional[str] = Query(None, description="Filter by machine ID"),
    severity: Optional[str] = Query(None, description="Filter by severity (WARNING, CRITICAL)"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (ACTIVE, ACKNOWLEDGED, RESOLVED)"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List edge safety alerts with optional filtering."""
    stmt = select(AlertModel)
    if machine_id:
        stmt = stmt.where(AlertModel.machine_id == machine_id)
    if severity:
        stmt = stmt.where(AlertModel.severity == severity.upper())
    if status_filter:
        stmt = stmt.where(AlertModel.status == status_filter.upper())

    stmt = stmt.order_by(desc(AlertModel.timestamp), desc(AlertModel.id)).offset(offset).limit(limit)
    records = db.execute(stmt).scalars().all()

    results = []
    for r in records:
        ev = None
        if r.evidence:
            try:
                ev = json.loads(r.evidence)
            except Exception:
                ev = None
        results.append(
            AlertResponse(
                id=r.id,
                timestamp=r.timestamp,
                machine_id=r.machine_id,
                operator_id=r.operator_id,
                task_id=r.task_id or "UNKNOWN",
                alert_type=r.alert_type,
                severity=r.severity,
                status=r.status,
                source=r.source or "EDGE",
                code=r.code,
                title=r.title,
                message=r.message,
                evidence=ev,
                created_at=r.created_at,
                resolved_at=r.resolved_at,
                acknowledged=r.acknowledged,
                acknowledged_at=r.acknowledged_at,
            )
        )
    return results


@router.post("/alerts/{alert_id}/acknowledge", response_model=AcknowledgeResponse)
def acknowledge_alert_endpoint(
    alert_id: str,
    payload: Optional[AcknowledgeRequest] = None,
    db: Session = Depends(get_db),
):
    """Acknowledge an active safety alert."""
    op_id = payload.operator_id if payload else "OP-101"
    ack = edge_safety_engine.acknowledge_alert(db, alert_id, operator_id=op_id)
    if not ack:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with ID '{alert_id}' not found",
        )
    return AcknowledgeResponse(
        status="ok",
        id=ack["id"],
        acknowledged=True,
        acknowledged_at=ack["acknowledged_at"],
    )


@router.get("/incidents", response_model=List[IncidentResponse])
def get_incidents(
    machine_id: Optional[str] = Query(None, description="Filter by machine ID"),
    severity: Optional[str] = Query(None, description="Filter by severity (WARNING, CRITICAL)"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (OPEN, ACKNOWLEDGED, RESOLVED)"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List recorded safety incidents."""
    stmt = select(IncidentModel)
    if machine_id:
        stmt = stmt.where(IncidentModel.machine_id == machine_id)
    if severity:
        stmt = stmt.where(IncidentModel.severity == severity.upper())
    if status_filter:
        stmt = stmt.where(IncidentModel.status == status_filter.upper())

    stmt = stmt.order_by(desc(IncidentModel.timestamp), desc(IncidentModel.id)).offset(offset).limit(limit)
    records = db.execute(stmt).scalars().all()

    return [
        IncidentResponse(
            id=r.id,
            machine_id=r.machine_id,
            operator_id=r.operator_id,
            task_id=r.task_id or "UNKNOWN",
            alert_id=r.alert_id,
            incident_type=r.incident_type,
            severity=r.severity,
            summary=r.summary,
            status=r.status,
            gps_zone=r.gps_zone,
            started_at=r.started_at,
            triggered_at=r.triggered_at,
            resolved_at=r.resolved_at,
            timestamp=r.timestamp,
        )
        for r in records
    ]


@router.get("/incidents/{incident_id}", response_model=IncidentDetailResponse)
def get_incident_detail(
    incident_id: str,
    db: Session = Depends(get_db),
):
    """Retrieve full incident details including structured physical context buffer."""
    record = db.execute(
        select(IncidentModel).where(IncidentModel.id == incident_id)
    ).scalar_one_or_none()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident with ID '{incident_id}' not found",
        )

    evidence_dict = None
    if record.evidence:
        try:
            evidence_dict = json.loads(record.evidence)
        except Exception:
            evidence_dict = None

    context_buf = None
    if record.context_buffer:
        try:
            parsed = json.loads(record.context_buffer)
            context_buf = IncidentContextBuffer(
                pre_event=parsed.get("pre_event", []),
                trigger_event=parsed.get("trigger_event", {}),
                post_event=parsed.get("post_event", []),
            )
        except Exception:
            context_buf = None

    return IncidentDetailResponse(
        id=record.id,
        machine_id=record.machine_id,
        operator_id=record.operator_id,
        task_id=record.task_id or "UNKNOWN",
        alert_id=record.alert_id,
        incident_type=record.incident_type,
        severity=record.severity,
        summary=record.summary,
        status=record.status,
        gps_zone=record.gps_zone,
        started_at=record.started_at,
        triggered_at=record.triggered_at,
        resolved_at=record.resolved_at,
        timestamp=record.timestamp,
        evidence=evidence_dict,
        context_buffer=context_buf,
    )


@router.post("/incidents/{incident_id}/acknowledge", response_model=AcknowledgeResponse)
def acknowledge_incident_endpoint(
    incident_id: str,
    payload: Optional[AcknowledgeRequest] = None,
    db: Session = Depends(get_db),
):
    """Acknowledge a recorded safety incident."""
    op_id = payload.operator_id if payload else "OP-101"
    ack = edge_safety_engine.acknowledge_incident(db, incident_id, operator_id=op_id)
    if not ack:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident with ID '{incident_id}' not found",
        )
    return AcknowledgeResponse(
        status="ok",
        id=ack["id"],
        acknowledged=True,
        acknowledged_at=ack["acknowledged_at"],
    )
