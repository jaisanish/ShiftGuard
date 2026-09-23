"""
ShiftGuard Safety & Incident Pydantic Schemas
=============================================

Pydantic v2 schemas for alerts, incident context buffers, and real-time edge safety state.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class AlertResponse(BaseModel):
    """Safety alert response model."""
    id: str = Field(..., description="Unique alert identifier UUID")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp")
    machine_id: str = Field(..., description="Machine identifier")
    operator_id: str = Field(..., description="Operator identifier")
    task_id: str = Field("UNKNOWN", description="Task identifier")
    alert_type: str = Field(..., description="Type of alert: SEATBELT, PROXIMITY, THERMAL")
    severity: str = Field(..., description="Severity level: INFO, WARNING, CRITICAL")
    status: str = Field(..., description="Lifecycle status: ACTIVE, ACKNOWLEDGED, RESOLVED")
    source: str = Field("EDGE", description="Authoritative source (strictly EDGE)")
    code: Optional[str] = Field(None, description="Diagnostic trouble code")
    title: str = Field(..., description="Short hazard title")
    message: str = Field(..., description="Detailed operator-facing hazard message")
    evidence: Optional[Dict[str, Any]] = Field(None, description="Physical sensor evidence dictionary")
    created_at: str = Field(..., description="ISO creation timestamp")
    resolved_at: Optional[str] = Field(None, description="ISO resolution timestamp")
    acknowledged: bool = Field(False, description="Whether alert has been acknowledged by operator")
    acknowledged_at: Optional[str] = Field(None, description="ISO acknowledgment timestamp")

    model_config = ConfigDict(from_attributes=True)


class IncidentContextBuffer(BaseModel):
    """Structured pre-event, trigger, and post-event telemetry sequence."""
    pre_event: List[Dict[str, Any]] = Field(default_factory=list, description="30s telemetry buffer before trigger")
    trigger_event: Dict[str, Any] = Field(default_factory=dict, description="Exact telemetry frame triggering incident")
    post_event: List[Dict[str, Any]] = Field(default_factory=list, description="Telemetry frames recorded post-trigger")


class IncidentResponse(BaseModel):
    """Incident summary response model."""
    id: str = Field(..., description="Unique incident identifier UUID")
    machine_id: str = Field(..., description="Machine identifier")
    operator_id: str = Field(..., description="Operator identifier")
    task_id: str = Field(..., description="Task identifier")
    alert_id: Optional[str] = Field(None, description="Triggering alert identifier")
    incident_type: str = Field(..., description="Incident category (PROXIMITY, SEATBELT)")
    severity: str = Field(..., description="Severity level: WARNING, CRITICAL")
    summary: str = Field(..., description="Operator summary description")
    status: str = Field(..., description="Incident status: OPEN, ACKNOWLEDGED, RESOLVED")
    gps_zone: Optional[str] = Field(None, description="Open-pit mining geofence zone")
    started_at: str = Field(..., description="ISO event start timestamp")
    triggered_at: str = Field(..., description="ISO trigger timestamp")
    resolved_at: Optional[str] = Field(None, description="ISO resolution timestamp")
    timestamp: str = Field(..., description="ISO record timestamp")

    model_config = ConfigDict(from_attributes=True)


class IncidentDetailResponse(IncidentResponse):
    """Detailed incident response with full physical context buffer."""
    evidence: Optional[Dict[str, Any]] = Field(None, description="Triggering sensor evidence")
    context_buffer: Optional[IncidentContextBuffer] = Field(None, description="Pre-event, trigger, and post-event frames")


class SafetyStateResponse(BaseModel):
    """Current real-time edge safety state for a machine."""
    machine_id: str = Field(..., description="Machine identifier")
    safety_state: str = Field("NORMAL", description="Overall state: NORMAL, WARNING, CRITICAL")
    seatbelt_status: str = Field("FASTENED", description="Seatbelt status: FASTENED or UNFASTENED")
    proximity_distance_m: float = Field(..., description="Live proximity distance in meters")
    active_alerts: List[AlertResponse] = Field(default_factory=list, description="Active alerts")
    is_critical: bool = Field(False, description="True if any critical alert is active")
    critical_alert: Optional[AlertResponse] = Field(None, description="Primary critical alert requiring acknowledgment")


class AcknowledgeRequest(BaseModel):
    """Request payload to acknowledge an alert or incident."""
    operator_id: Optional[str] = Field("OP-101", description="Acknowledging operator identifier")
    notes: Optional[str] = Field(None, description="Optional acknowledgment note")


class AcknowledgeResponse(BaseModel):
    """Response confirming acknowledgment."""
    status: str = Field("ok", description="Status code")
    id: str = Field(..., description="Acknowledged item identifier")
    acknowledged: bool = Field(True, description="Acknowledgment flag")
    acknowledged_at: str = Field(..., description="ISO timestamp")
