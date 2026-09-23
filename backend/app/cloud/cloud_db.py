"""
ShiftGuard Cloud Database Engine & Session Management
=====================================================

Provides isolated persistence for the ShiftGuard Cloud Backend.
Supports PostgreSQL (production) with automatic SQLite fallback (local development / testing).
"""

import logging
from typing import Generator
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from backend.app.config import settings

logger = logging.getLogger("shiftguard.cloud.db")

BaseCloud = declarative_base()

# Determine connect_args based on DB dialect
connect_args = {}
if settings.CLOUD_DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

cloud_engine = create_engine(
    settings.CLOUD_DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)

CloudSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=cloud_engine,
)


def init_cloud_tables() -> None:
    """Initialize all cloud database tables defined on BaseCloud."""
    try:
        # Import models so they register with BaseCloud.metadata
        from backend.app.cloud import models  # noqa: F401
        BaseCloud.metadata.create_all(bind=cloud_engine)
        _migrate_phase6_cloud_anomaly_columns()
        logger.info(f"[CLOUD DB] Initialized cloud tables at {settings.CLOUD_DATABASE_URL}")
    except Exception as e:
        logger.error(f"[CLOUD DB] Failed to initialize cloud database: {e}")


def _migrate_phase6_cloud_anomaly_columns() -> None:
    """Non-destructively upgrade the local SQLite cloud fallback used by the demo."""
    if cloud_engine.dialect.name != "sqlite":
        return
    inspector = inspect(cloud_engine)
    if "cloud_anomalies" not in inspector.get_table_names():
        return
    existing = {column["name"] for column in inspector.get_columns("cloud_anomalies")}
    additions = {
        "event_id": "VARCHAR(64) NOT NULL DEFAULT ''",
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
    with cloud_engine.begin() as connection:
        for column, definition in additions.items():
            if column not in existing:
                connection.execute(text(f"ALTER TABLE cloud_anomalies ADD COLUMN {column} {definition}"))
        connection.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_cloud_anomaly_operator_time "
            "ON cloud_anomalies (operator_id, window_end)"
        ))
        connection.execute(text(
            "CREATE UNIQUE INDEX IF NOT EXISTS ix_cloud_anomalies_event_id "
            "ON cloud_anomalies (event_id)"
        ))


def get_cloud_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a transactional session for the cloud database."""
    db = CloudSessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_cloud_db_health() -> bool:
    """Perform a lightweight SELECT 1 check to verify cloud database connectivity."""
    try:
        with cloud_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.warning(f"[CLOUD DB] Health check failed: {e}")
        return False
