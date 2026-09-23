from sqlalchemy import inspect
from backend.app.database.connection import Base
from backend.app.database.models import (
    TelemetryModel,
    TaskModel,
    AlertModel,
    IncidentModel,
    AnomalyModel,
    EtaPredictionModel,
    TrainingRecordModel,
    SyncOutboxModel,
)


def test_database_tables_exist(db_session):
    """Verify that all 8 required database tables are created."""
    inspector = inspect(db_session.bind)
    table_names = inspector.get_table_names()

    required_tables = [
        "telemetry",
        "tasks",
        "alerts",
        "incidents",
        "anomalies",
        "eta_predictions",
        "training_records",
        "sync_outbox",
    ]

    for table in required_tables:
        assert table in table_names, f"Expected table '{table}' in database"


def test_telemetry_table_columns(db_session):
    """Verify telemetry table has all 19 columns corresponding to telemetry schema."""
    inspector = inspect(db_session.bind)
    cols = {col["name"]: col for col in inspector.get_columns("telemetry")}

    expected_cols = [
        "id",
        "timestamp",
        "machine_id",
        "operator_id",
        "engine_hours",
        "engine_rpm",
        "engine_load_pct",
        "machine_speed_kmh",
        "fuel_used_l",
        "idling_time_min",
        "load_cycles",
        "operating_state",
        "seatbelt_status",
        "proximity_distance_m",
        "gps_zone",
        "working_condition",
        "coolant_temp_c",
        "hydraulic_oil_temp_c",
        "fault_code",
        "task_id",
    ]

    for col in expected_cols:
        assert col in cols, f"Expected column '{col}' in telemetry table"


def test_tasks_table_columns(db_session):
    """Verify tasks table has all 12 columns corresponding to task_history.csv."""
    inspector = inspect(db_session.bind)
    cols = {col["name"]: col for col in inspector.get_columns("tasks")}

    expected_cols = [
        "task_id",
        "machine_id",
        "operator_id",
        "task_type",
        "weather",
        "operator_skill",
        "machine_age_years",
        "estimated_time_min",
        "actual_time_min",
        "planned_start",
        "actual_start",
        "working_condition",
    ]

    for col in expected_cols:
        assert col in cols, f"Expected column '{col}' in tasks table"


def test_future_extension_tables_are_valid(db_session):
    """Verify future extension tables (alerts, anomalies, etc.) are structurally valid."""
    inspector = inspect(db_session.bind)
    for tbl in ["alerts", "incidents", "anomalies", "eta_predictions", "training_records", "sync_outbox"]:
        pk = inspector.get_pk_constraint(tbl)
        assert len(pk["constrained_columns"]) > 0, f"Table '{tbl}' must have a primary key"
