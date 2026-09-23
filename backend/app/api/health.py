from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database.connection import get_db
from backend.app.schemas.common import HealthResponse
from backend.app.cloud.cloud_db import check_cloud_db_health
from backend.app.copilot.service import copilot_service
from backend.app.ml.anomaly.model_registry import get_anomaly_registry
from backend.app.ml.eta.model_registry import get_eta_registry

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def get_health(db: Session = Depends(get_db)):
    """
    Service health check endpoint.
    Verifies SQLite database connectivity.
    """
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "disconnected"
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "error",
                "service": settings.SERVICE_NAME,
                "database": db_status,
            },
        )

    return {
        "status": "ok",
        "service": settings.SERVICE_NAME,
        "database": db_status,
    }


@router.get("/health/ready")
def get_readiness(db: Session = Depends(get_db)):
    """Report integrated runtime dependencies, without treating optional cloud sync as required."""
    try:
        db.execute(text("SELECT 1"))
        database = {"status": "ready"}
    except Exception as exc:
        database = {"status": "unavailable", "error": str(exc)}
    anomaly = get_anomaly_registry().health()
    eta = get_eta_registry().health()
    cloud_ok = check_cloud_db_health() if settings.CLOUD_ENABLED else None
    components = {
        "database": database,
        "anomaly_model": anomaly,
        "eta_model": eta,
        "copilot": copilot_service.health(),
        "cloud": {"status": "ready" if cloud_ok else "disabled" if cloud_ok is None else "unavailable", "enabled": settings.CLOUD_ENABLED},
    }
    required_ready = database["status"] == "ready" and anomaly["model_loaded"] and eta["model_loaded"]
    payload = {"status": "ready" if required_ready else "not_ready", "service": settings.SERVICE_NAME, "components": components}
    if not required_ready:
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=payload)
    return payload
