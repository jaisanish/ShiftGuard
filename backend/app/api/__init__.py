"""
API Routers Package for ShiftGuard.
"""
from backend.app.api.health import router as health_router
from backend.app.api.telemetry import router as telemetry_router
from backend.app.api.tasks import router as tasks_router
from backend.app.api.machines import router as machines_router
from backend.app.api.operators import router as operators_router

__all__ = [
    "health_router",
    "telemetry_router",
    "tasks_router",
    "machines_router",
    "operators_router",
]
