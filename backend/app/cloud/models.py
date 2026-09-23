"""
ShiftGuard Cloud PostgreSQL / SQLite Database Models
====================================================

Cloud schema storing synchronized fleet telemetry, safety alerts, incidents,
and future ML prediction artifacts.

Provides full idempotency enforcement via event_id tracking.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    Column,
    Float,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)

from backend.app.cloud.cloud_db import BaseCloud


def cloud_utc_now_iso() -> str:
    """Return current UTC timestamp in ISO 8601 string format."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# ============================================================================
# 1. Cloud Idempotency Event Log Model
# ============================================================================
class CloudEventLogModel(BaseCloud):
    """
    Immutable ledger of all ingested sync events.
    The primary key `event_id` provides guaranteed idempotency across edge retries.
    """
    __tablename__ = "cloud_event_log"

    event_id = Column(String(64), primary_key=True, index=True)
    event_type = Column(String(64), nullable=False, index=True)  # TELEMETRY, ALERT, INCIDENT, TASK, etc.
    received_at = Column(String(64), nullable=False, default=cloud_utc_now_iso, index=True)
    status = Column(String(32), nullable=False, default="ACCEPTED")  # ACCEPTED, DUPLICATE


# ============================================================================
# 2. Cloud Telemetry Model
# ============================================================================
class CloudTelemetryModel(BaseCloud):
    """
    Centralized historical fleet telemetry time-series.
    Populated exclusively via offline-first batch synchronization from edge nodes.
    """
    __tablename__ = "cloud_telemetry"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(64), nullable=False, unique=True, index=True)
    timestamp = Column(String(64), nullable=False, index=True)
    machine_id = Column(String(64), nullable=False, index=True)
    operator_id = Column(String(64), nullable=False, index=True)
    engine_hours = Column(Float, nullable=False)
    engine_rpm = Column(Float, nullable=False)
    engine_load_pct = Column(Float, nullable=False)
    machine_speed_kmh = Column(Float, nullable=False)
    fuel_used_l = Column(Float, nullable=False)
    idling_time_min = Column(Float, nullable=False)
    load_cycles = Column(Integer, nullable=False)
    operating_state = Column(String(64), nullable=False)
    seatbelt_status = Column(String(32), nullable=False)
    proximity_distance_m = Column(Float, nullable=False)
    gps_zone = Column(String(64), nullable=False)
    working_condition = Column(String(64), nullable=False)
    coolant_temp_c = Column(Float, nullable=False)
    hydraulic_oil_temp_c = Column(Float, nullable=False)
    fault_code = Column(String(64), nullable=False, default="NONE")
    task_id = Column(String(64), nullable=False, index=True)
    synced_at = Column(String(64), nullable=False, default=cloud_utc_now_iso, index=True)

    __table_args__ = (
        Index("ix_cloud_telem_machine_time", "machine_id", "timestamp"),
        Index("ix_cloud_telem_operator_time", "operator_id", "timestamp"),
    )


# ============================================================================
# 3. Cloud Alert Model
# ============================================================================
class CloudAlertModel(BaseCloud):
    """
    Centralized historical alerts log synchronized from edge nodes.
    Includes deterministic rule evaluations and operator acknowledgment audit trails.
    """
    __tablename__ = "cloud_alerts"

    id = Column(String(64), primary_key=True, index=True)
    event_id = Column(String(64), nullable=False, index=True)
    timestamp = Column(String(64), nullable=False, index=True)
    machine_id = Column(String(64), nullable=False, index=True)
    operator_id = Column(String(64), nullable=False, index=True)
    task_id = Column(String(64), nullable=False, default="UNKNOWN", index=True)
    alert_type = Column(String(64), nullable=False, index=True)  # SEATBELT, PROXIMITY, THERMAL
    severity = Column(String(32), nullable=False, index=True)  # WARNING, CRITICAL
    status = Column(String(32), nullable=False, default="ACTIVE", index=True)  # ACTIVE, ACKNOWLEDGED, RESOLVED
    source = Column(String(32), nullable=False, default="EDGE")
    code = Column(String(64), nullable=True)
    title = Column(String(128), nullable=False)
    message = Column(Text, nullable=False)
    evidence = Column(Text, nullable=True)  # JSON-encoded evidence dictionary
    created_at = Column(String(64), nullable=False)
    resolved_at = Column(String(64), nullable=True)
    acknowledged = Column(Boolean, default=False, nullable=False)
    acknowledged_at = Column(String(64), nullable=True)
    synced_at = Column(String(64), nullable=False, default=cloud_utc_now_iso)

    __table_args__ = (
        Index("ix_cloud_alerts_machine_severity", "machine_id", "severity"),
    )


# ============================================================================
# 4. Cloud Incident Model
# ============================================================================
class CloudIncidentModel(BaseCloud):
    """
    Centralized high-severity safety incidents synchronized from edge nodes.
    Maintains the full physical context buffer (Pre-event + Trigger + Post-event).
    """
    __tablename__ = "cloud_incidents"

    id = Column(String(64), primary_key=True, index=True)
    event_id = Column(String(64), nullable=False, index=True)
    machine_id = Column(String(64), nullable=False, index=True)
    operator_id = Column(String(64), nullable=False, index=True)
    task_id = Column(String(64), nullable=False, default="UNKNOWN", index=True)
    alert_id = Column(String(64), nullable=True, index=True)
    incident_type = Column(String(64), nullable=False, index=True)  # PROXIMITY, SEATBELT
    severity = Column(String(32), nullable=False, index=True)  # WARNING, CRITICAL
    summary = Column(Text, nullable=False)
    evidence = Column(Text, nullable=True)  # JSON-encoded trigger evidence
    context_buffer = Column(Text, nullable=True)  # JSON-encoded {pre_event, trigger_event, post_event}
    started_at = Column(String(64), nullable=False)
    triggered_at = Column(String(64), nullable=False, index=True)
    resolved_at = Column(String(64), nullable=True)
    status = Column(String(32), default="OPEN", nullable=False, index=True)  # OPEN, ACKNOWLEDGED, RESOLVED
    gps_zone = Column(String(64), nullable=True)
    timestamp = Column(String(64), nullable=False, index=True)
    synced_at = Column(String(64), nullable=False, default=cloud_utc_now_iso)

    __table_args__ = (
        Index("ix_cloud_incidents_machine_severity", "machine_id", "severity"),
    )


# ============================================================================
# 5. Future ML & Analytics Foundation Models (Phase 6+)
# ============================================================================
class CloudTaskModel(BaseCloud):
    """Work orders and haul assignments synchronized to cloud."""
    __tablename__ = "cloud_tasks"

    task_id = Column(String(64), primary_key=True, index=True)
    machine_id = Column(String(64), nullable=False, index=True)
    operator_id = Column(String(64), nullable=False, index=True)
    task_type = Column(String(64), nullable=False)
    weather = Column(String(64), nullable=False)
    operator_skill = Column(String(64), nullable=False)
    machine_age_years = Column(Float, nullable=False)
    estimated_time_min = Column(Float, nullable=False)
    actual_time_min = Column(Float, nullable=False)
    planned_start = Column(String(64), nullable=False)
    actual_start = Column(String(64), nullable=False)
    working_condition = Column(String(64), nullable=False)
    synced_at = Column(String(64), nullable=False, default=cloud_utc_now_iso)


class CloudAnomalyModel(BaseCloud):
    """Synchronized advisory operating-pattern anomaly results (Phase 6)."""
    __tablename__ = "cloud_anomalies"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String(64), nullable=False, unique=True, index=True)
    machine_id = Column(String(64), nullable=False, index=True)
    operator_id = Column(String(64), nullable=False, index=True)
    window_start = Column(String(64), nullable=False, index=True)
    window_end = Column(String(64), nullable=False, index=True)
    anomaly_type = Column(String(64), nullable=False, index=True)
    anomaly_score = Column(Float, nullable=False)
    current_value = Column(Float, nullable=True)
    baseline_value = Column(Float, nullable=True)
    evidence = Column(Text, nullable=False, default="[]")
    baseline_source = Column(String(32), nullable=False, default="GLOBAL_FALLBACK")
    timestamp = Column(String(64), nullable=False, index=True)
    model_version = Column(String(64), nullable=False)
    created_at = Column(String(64), nullable=False)
    synced_at = Column(String(64), nullable=False, default=cloud_utc_now_iso)

    __table_args__ = (
        Index("ix_cloud_anomaly_operator_time", "operator_id", "window_end"),
    )


class CloudEtaPredictionModel(BaseCloud):
    """Synchronized cycle ETA predictions (Phase 6)."""
    __tablename__ = "cloud_eta_predictions"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String(64), nullable=False, index=True)
    machine_id = Column(String(64), nullable=False, index=True)
    predicted_eta_min = Column(Float, nullable=False)
    confidence_score = Column(Float, nullable=False)
    feature_snapshot = Column(Text, nullable=True)
    prediction_timestamp = Column(String(64), nullable=False, index=True)
    synced_at = Column(String(64), nullable=False, default=cloud_utc_now_iso)
