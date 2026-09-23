"""
Database Initialization and Synthetic Data Loader (Phase 1)
============================================================

Provides idempotent table creation and data seeding from synthetic CSV files.
"""

import argparse
import csv
from pathlib import Path
from typing import Optional
from sqlalchemy import func, inspect, select, text
from sqlalchemy.orm import Session

from backend.app.database.connection import Base, engine, SessionLocal
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


def init_tables(target_engine=None):
    """Create all database tables if they do not exist."""
    eng = target_engine or engine
    Base.metadata.create_all(bind=eng)
    _migrate_phase6_anomaly_columns(eng)
    _migrate_phase7_eta_columns(eng)


def _migrate_phase6_anomaly_columns(target_engine) -> None:
    """Add Phase 6 columns to an existing local SQLite database without data loss."""
    if target_engine.dialect.name != "sqlite":
        return
    inspector = inspect(target_engine)
    if "anomalies" not in inspector.get_table_names():
        return
    existing = {column["name"] for column in inspector.get_columns("anomalies")}
    additions = {
        "operator_id": "VARCHAR(64) NOT NULL DEFAULT 'UNKNOWN'",
        "window_start": "VARCHAR(64) NOT NULL DEFAULT ''",
        "window_end": "VARCHAR(64) NOT NULL DEFAULT ''",
        "anomaly_type": "VARCHAR(64) NOT NULL DEFAULT 'UNUSUAL_OPERATION'",
        "current_value": "FLOAT",
        "baseline_value": "FLOAT",
        "evidence": "TEXT NOT NULL DEFAULT '[]'",
        "baseline_source": "VARCHAR(32) NOT NULL DEFAULT 'GLOBAL_FALLBACK'",
        "created_at": "VARCHAR(64) NOT NULL DEFAULT ''",
    }
    with target_engine.begin() as connection:
        for column, definition in additions.items():
            if column not in existing:
                connection.execute(text(f"ALTER TABLE anomalies ADD COLUMN {column} {definition}"))
        connection.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_anomalies_operator_time "
            "ON anomalies (operator_id, window_end)"
        ))
        connection.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_anomalies_machine_type "
            "ON anomalies (machine_id, anomaly_type)"
        ))


def _migrate_phase7_eta_columns(target_engine) -> None:
    """Non-destructively extend legacy ETA records with Phase 7 explainability."""
    if target_engine.dialect.name != "sqlite":
        return
    inspector = inspect(target_engine)
    if "eta_predictions" not in inspector.get_table_names():
        return
    existing = {column["name"] for column in inspector.get_columns("eta_predictions")}
    additions = {
        "operator_id": "VARCHAR(64) NOT NULL DEFAULT 'UNKNOWN'",
        "planned_minutes": "FLOAT", "predicted_minutes": "FLOAT",
        "predicted_remaining_minutes": "FLOAT", "p50": "FLOAT", "p90": "FLOAT",
        "interval_lower": "FLOAT", "interval_upper": "FLOAT", "uncertainty_minutes": "FLOAT",
        "delta_vs_plan_minutes": "FLOAT", "why_changed": "TEXT NOT NULL DEFAULT '[]'",
        "features_version": "VARCHAR(64)", "model_version": "VARCHAR(64)",
    }
    with target_engine.begin() as connection:
        for column, definition in additions.items():
            if column not in existing:
                connection.execute(text(f"ALTER TABLE eta_predictions ADD COLUMN {column} {definition}"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_eta_predictions_task_model ON eta_predictions (task_id, model_version)"))


def seed_tasks(db: Session, tasks_csv: Path) -> int:
    """
    Import tasks from CSV into the database idempotently.
    Returns the number of newly inserted tasks.
    """
    if not tasks_csv.exists():
        print(f"[WARN] Task CSV not found: {tasks_csv}")
        return 0

    inserted_count = 0
    with open(tasks_csv, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            task_id = row["task_id"]
            existing = db.execute(
                select(TaskModel).where(TaskModel.task_id == task_id)
            ).scalar_one_or_none()

            if existing is None:
                new_task = TaskModel(
                    task_id=task_id,
                    machine_id=row["machine_id"],
                    operator_id=row["operator_id"],
                    task_type=row["task_type"],
                    weather=row["weather"],
                    operator_skill=row["operator_skill"],
                    machine_age_years=float(row["machine_age_years"]),
                    estimated_time_min=float(row["estimated_time_min"]),
                    actual_time_min=float(row["actual_time_min"]),
                    planned_start=row["planned_start"],
                    actual_start=row["actual_start"],
                    working_condition=row["working_condition"],
                )
                db.add(new_task)
                inserted_count += 1

    db.commit()
    return inserted_count


def seed_telemetry(db: Session, telemetry_csv: Path, chunk_size: int = 500) -> int:
    """
    Import telemetry from CSV into the database idempotently.
    If the telemetry table already contains rows, skips to avoid duplicates.
    Returns the number of newly inserted records.
    """
    if not telemetry_csv.exists():
        print(f"[WARN] Telemetry CSV not found: {telemetry_csv}")
        return 0

    existing_count = db.execute(select(func.count(TelemetryModel.id))).scalar()
    if existing_count and existing_count > 0:
        print(f"[INFO] Telemetry table already seeded ({existing_count} records present). Skipping.")
        return 0

    inserted_count = 0
    batch = []

    with open(telemetry_csv, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            record = TelemetryModel(
                timestamp=row["timestamp"],
                machine_id=row["machine_id"],
                operator_id=row["operator_id"],
                engine_hours=float(row["engine_hours"]),
                engine_rpm=float(row["engine_rpm"]),
                engine_load_pct=float(row["engine_load_pct"]),
                machine_speed_kmh=float(row["machine_speed_kmh"]),
                fuel_used_l=float(row["fuel_used_l"]),
                idling_time_min=float(row["idling_time_min"]),
                load_cycles=int(row["load_cycles"]),
                operating_state=row["operating_state"],
                seatbelt_status=row["seatbelt_status"],
                proximity_distance_m=float(row["proximity_distance_m"]),
                gps_zone=row["gps_zone"],
                working_condition=row["working_condition"],
                coolant_temp_c=float(row["coolant_temp_c"]),
                hydraulic_oil_temp_c=float(row["hydraulic_oil_temp_c"]),
                fault_code=row.get("fault_code", "NONE"),
                task_id=row["task_id"],
            )
            batch.append(record)
            if len(batch) >= chunk_size:
                db.bulk_save_objects(batch)
                db.commit()
                inserted_count += len(batch)
                batch = []

        if batch:
            db.bulk_save_objects(batch)
            db.commit()
            inserted_count += len(batch)

    return inserted_count


def load_synthetic_data(db: Session, data_dir: Optional[Path] = None) -> dict:
    """Load both synthetic datasets into SQLite."""
    base_data = data_dir or Path("data/synthetic")
    task_csv = base_data / "task_history.csv"
    telemetry_csv = base_data / "telemetry_history.csv"

    task_count = seed_tasks(db, task_csv)
    telemetry_count = seed_telemetry(db, telemetry_csv)

    return {
        "tasks_inserted": task_count,
        "telemetry_inserted": telemetry_count,
    }


def main():
    parser = argparse.ArgumentParser(description="ShiftGuard Database Initializer")
    parser.add_argument("--data-dir", type=str, default="data/synthetic", help="Path to synthetic datasets")
    args = parser.parse_args()

    print("-" * 65)
    print("ShiftGuard -- Database Setup & Seeding")
    print("-" * 65)

    print("Initializing database tables...")
    init_tables()
    print("Tables initialized successfully.")

    db = SessionLocal()
    try:
        data_path = Path(args.data_dir)
        print(f"Loading synthetic data from: {data_path.resolve()}")
        result = load_synthetic_data(db, data_path)
        print(f"[OK] New tasks inserted: {result['tasks_inserted']}")
        print(f"[OK] New telemetry records inserted: {result['telemetry_inserted']}")
    finally:
        db.close()

    print("-" * 65)
    print("Database initialization complete.")
    print("-" * 65)


if __name__ == "__main__":
    main()
