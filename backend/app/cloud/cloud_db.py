"""
ShiftGuard Cloud Database Engine & Session Management
=====================================================

Provides isolated persistence for the ShiftGuard Cloud Backend.
Supports PostgreSQL (production) with automatic SQLite fallback (local development / testing).
"""

import logging
from typing import Generator
from sqlalchemy import create_engine, text
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
        logger.info(f"[CLOUD DB] Initialized cloud tables at {settings.CLOUD_DATABASE_URL}")
    except Exception as e:
        logger.error(f"[CLOUD DB] Failed to initialize cloud database: {e}")


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
