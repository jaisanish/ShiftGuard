"""
ShiftGuard Event Serializers for Sync Outbox
============================================

Transforms SQLite edge database models into standardized JSON-serializable
event dictionaries for the sync_outbox queue.
"""

from typing import Any, Dict
from backend.app.database.models import AlertModel, IncidentModel, TelemetryModel


def serialize_telemetry_event(telemetry: TelemetryModel) -> Dict[str, Any]:
    """Serialize TelemetryModel into canonical telemetry event payload."""
    return {
        "timestamp": telemetry.timestamp,
        "machine_id": telemetry.machine_id,
        "operator_id": telemetry.operator_id,
        "engine_hours": telemetry.engine_hours,
        "engine_rpm": telemetry.engine_rpm,
        "engine_load_pct": telemetry.engine_load_pct,
        "machine_speed_kmh": telemetry.machine_speed_kmh,
        "fuel_used_l": telemetry.fuel_used_l,
        "idling_time_min": telemetry.idling_time_min,
        "load_cycles": telemetry.load_cycles,
        "operating_state": telemetry.operating_state,
        "seatbelt_status": telemetry.seatbelt_status,
        "proximity_distance_m": telemetry.proximity_distance_m,
        "gps_zone": telemetry.gps_zone,
        "working_condition": telemetry.working_condition,
        "coolant_temp_c": telemetry.coolant_temp_c,
        "hydraulic_oil_temp_c": telemetry.hydraulic_oil_temp_c,
        "fault_code": telemetry.fault_code,
        "task_id": telemetry.task_id,
    }


def serialize_alert_event(alert: AlertModel) -> Dict[str, Any]:
    """Serialize AlertModel into canonical alert event payload."""
    return {
        "id": alert.id,
        "timestamp": alert.timestamp,
        "machine_id": alert.machine_id,
        "operator_id": alert.operator_id,
        "task_id": alert.task_id,
        "alert_type": alert.alert_type,
        "severity": alert.severity,
        "status": alert.status,
        "source": alert.source,
        "code": alert.code,
        "title": alert.title,
        "message": alert.message,
        "evidence": alert.evidence,
        "created_at": alert.created_at,
        "resolved_at": alert.resolved_at,
        "acknowledged": alert.acknowledged,
        "acknowledged_at": alert.acknowledged_at,
    }


def serialize_incident_event(incident: IncidentModel) -> Dict[str, Any]:
    """Serialize IncidentModel into canonical incident event payload."""
    return {
        "id": incident.id,
        "machine_id": incident.machine_id,
        "operator_id": incident.operator_id,
        "task_id": incident.task_id,
        "alert_id": incident.alert_id,
        "incident_type": incident.incident_type,
        "severity": incident.severity,
        "summary": incident.summary,
        "evidence": incident.evidence,
        "context_buffer": incident.context_buffer,
        "started_at": incident.started_at,
        "triggered_at": incident.triggered_at,
        "resolved_at": incident.resolved_at,
        "status": incident.status,
        "gps_zone": incident.gps_zone,
        "timestamp": incident.timestamp,
    }
