import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from backend.app.database.connection import Base


def utc_now_iso() -> str:
    """Return current UTC timestamp in ISO 8601 string format."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# ============================================================================
# 1. Telemetry Model (Fully Implemented)
# ============================================================================
class TelemetryModel(Base):
    """
    Continuous machinery sensor readings and operational states.
    Matches data/synthetic/telemetry_history.csv schema exactly.
    """
    __tablename__ = "telemetry"

    id = Column(Integer, primary_key=True, autoincrement=True)
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

    __table_args__ = (
        Index("ix_telemetry_machine_timestamp", "machine_id", "timestamp"),
        Index("ix_telemetry_operator_timestamp", "operator_id", "timestamp"),
    )


# ============================================================================
# 2. Task Model (Fully Implemented)
# ============================================================================
class TaskModel(Base):
    """
    Work orders, haul assignments, and shift tasks.
    Matches data/synthetic/task_history.csv schema exactly.
    """
    __tablename__ = "tasks"

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

    __table_args__ = (
        Index("ix_tasks_machine_operator", "machine_id", "operator_id"),
    )


# ============================================================================
# 3. Alerts Model (Phase 3 Edge Safety Engine)
# ============================================================================
class AlertModel(Base):
    """
    In-cab alerts and safety events managed by the Edge Safety Engine.
    Follows deterministic state machine: NORMAL -> DETECTED -> WARNING -> CRITICAL -> ACKNOWLEDGED -> RESOLVED.
    """
    __tablename__ = "alerts"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(String(64), nullable=False, default=utc_now_iso, index=True)
    machine_id = Column(String(64), nullable=False, index=True)
    operator_id = Column(String(64), nullable=False, index=True)
    task_id = Column(String(64), nullable=False, default="UNKNOWN", index=True)
    alert_type = Column(String(64), nullable=False)  # SEATBELT, PROXIMITY, THERMAL
    severity = Column(String(32), nullable=False)  # WARNING, CRITICAL
    status = Column(String(32), nullable=False, default="ACTIVE")  # ACTIVE, ACKNOWLEDGED, RESOLVED
    source = Column(String(32), nullable=False, default="EDGE")  # Strictly EDGE
    code = Column(String(64), nullable=True)  # Fault code if applicable
    title = Column(String(128), nullable=False)
    message = Column(Text, nullable=False)
    evidence = Column(Text, nullable=True)  # JSON-encoded evidence dictionary
    created_at = Column(String(64), nullable=False, default=utc_now_iso)
    resolved_at = Column(String(64), nullable=True)
    acknowledged = Column(Boolean, default=False, nullable=False)
    acknowledged_at = Column(String(64), nullable=True)

    __table_args__ = (
        Index("ix_alerts_machine_severity", "machine_id", "severity"),
        Index("ix_alerts_machine_status", "machine_id", "status"),
    )


# ============================================================================
# 4. Incidents Model (Phase 3 Edge Safety Engine)
# ============================================================================
class IncidentModel(Base):
    """
    Persisted safety incident records containing structured context buffers
    (Pre-event + Trigger + Post-event telemetry).
    """
    __tablename__ = "incidents"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    machine_id = Column(String(64), nullable=False, index=True)
    operator_id = Column(String(64), nullable=False, index=True)
    task_id = Column(String(64), nullable=False, default="UNKNOWN", index=True)
    alert_id = Column(String(64), nullable=True, index=True)
    incident_type = Column(String(64), nullable=False)  # PROXIMITY, SEATBELT
    severity = Column(String(32), nullable=False)  # WARNING, CRITICAL
    summary = Column(Text, nullable=False)
    evidence = Column(Text, nullable=True)  # JSON-encoded trigger evidence
    context_buffer = Column(Text, nullable=True)  # JSON-encoded {pre_event, trigger_event, post_event}
    started_at = Column(String(64), nullable=False)
    triggered_at = Column(String(64), nullable=False, index=True)
    resolved_at = Column(String(64), nullable=True)
    status = Column(String(32), default="OPEN", nullable=False)  # OPEN, ACKNOWLEDGED, RESOLVED
    gps_zone = Column(String(64), nullable=True)
    timestamp = Column(String(64), nullable=False, default=utc_now_iso, index=True)

    __table_args__ = (
        Index("ix_incidents_machine_status", "machine_id", "status"),
    )


# ============================================================================
# 5. Anomalies Model (Phase 6 Advisory Analytics)
# ============================================================================
class AnomalyModel(Base):
    """
    Versioned advisory operating-pattern detections produced by the anomaly model.
    This table has no role in deterministic edge safety decisions.
    """
    __tablename__ = "anomalies"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
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
    # Legacy sensor fields are retained as nullable compatibility columns.
    sensor_name = Column(String(64), nullable=True)
    detected_value = Column(Float, nullable=True)
    expected_range_min = Column(Float, nullable=True)
    expected_range_max = Column(Float, nullable=True)
    timestamp = Column(String(64), nullable=False, default=utc_now_iso, index=True)
    model_version = Column(String(64), nullable=False)
    created_at = Column(String(64), nullable=False, default=utc_now_iso)

    __table_args__ = (
        Index("ix_anomalies_operator_time", "operator_id", "window_end"),
        Index("ix_anomalies_machine_type", "machine_id", "anomaly_type"),
    )


# ============================================================================
# 6. ETA Predictions Model (Structurally Valid for Future Extension)
# ============================================================================
class EtaPredictionModel(Base):
    """
    Machine cycle and task ETA predictions.
    Reserved for future ETA ML Model.
    """
    __tablename__ = "eta_predictions"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String(64), ForeignKey("tasks.task_id"), nullable=False, index=True)
    machine_id = Column(String(64), nullable=False, index=True)
    operator_id = Column(String(64), nullable=False, default="UNKNOWN", index=True)
    predicted_eta_min = Column(Float, nullable=False)
    confidence_score = Column(Float, nullable=False)
    feature_snapshot = Column(Text, nullable=True)  # JSON payload of input features
    prediction_timestamp = Column(String(64), nullable=False, default=utc_now_iso, index=True)
    planned_minutes = Column(Float, nullable=True)
    predicted_minutes = Column(Float, nullable=True)
    predicted_remaining_minutes = Column(Float, nullable=True)
    p50 = Column(Float, nullable=True)
    p90 = Column(Float, nullable=True)
    interval_lower = Column(Float, nullable=True)
    interval_upper = Column(Float, nullable=True)
    uncertainty_minutes = Column(Float, nullable=True)
    delta_vs_plan_minutes = Column(Float, nullable=True)
    why_changed = Column(Text, nullable=False, default="[]")
    features_version = Column(String(64), nullable=True)
    model_version = Column(String(64), nullable=True, index=True)


# ============================================================================
# 7. Training Records Model (Structurally Valid for Future Extension)
# ============================================================================
class TrainingRecordModel(Base):
    """
    ML model training metadata, hyperparameter logs, and benchmark metrics.
    Reserved for future training pipeline.
    """
    __tablename__ = "training_records"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    model_name = Column(String(64), nullable=False, index=True)
    model_type = Column(String(64), nullable=False)  # ANOMALY, ETA, CLASSIFIER
    dataset_version = Column(String(64), nullable=False)
    metrics_json = Column(Text, nullable=False)
    training_start = Column(String(64), nullable=False)
    training_end = Column(String(64), nullable=False)
    status = Column(String(32), nullable=False, default="SUCCESS")  # SUCCESS, FAILED, RUNNING


class TrainingCompletionModel(Base):
    """Operator quiz completion audit trail for closed-loop coaching."""
    __tablename__ = "training_completions"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    lesson_id = Column(String(64), nullable=False, index=True)
    lesson_title = Column(String(256), nullable=False)
    operator_id = Column(String(64), nullable=False, index=True)
    completed_at = Column(String(64), nullable=False, default=utc_now_iso, index=True)
    score_pct = Column(Integer, nullable=False)
    passed = Column(Boolean, nullable=False)

    __table_args__ = (Index("ix_training_completions_operator_lesson", "operator_id", "lesson_id"),)


# ============================================================================
# 8. Sync Outbox Model (Phase 5 Offline-First Synchronization)
# ============================================================================
class SyncOutboxModel(Base):
    """
    Local-first edge outbox queue for cloud synchronization.
    Strictly persists all local safety, telemetry, and incident events in SQLite
    prior to asynchronous batch synchronization to the cloud database.
    """
    __tablename__ = "sync_outbox"

    event_id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type = Column(String(64), nullable=False, index=True)  # TELEMETRY, ALERT, INCIDENT, TASK, TRAINING
    payload = Column(Text, nullable=False)
    created_at = Column(String(64), nullable=False, default=utc_now_iso, index=True)
    synced_at = Column(String(64), nullable=True)
    status = Column(String(32), nullable=False, default="PENDING", index=True)  # PENDING, SYNCING, SYNCED, FAILED
    retry_count = Column(Integer, default=0, nullable=False)
    last_error = Column(Text, nullable=True)
    next_retry_at = Column(String(64), nullable=True)

    __table_args__ = (
        Index("ix_sync_outbox_status_type", "status", "event_type"),
    )
