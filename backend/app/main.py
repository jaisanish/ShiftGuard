from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.config import settings
from backend.app.database.connection import SessionLocal
from backend.app.database.init_db import init_tables, load_synthetic_data
from backend.app.cloud.cloud_db import init_cloud_tables
from backend.app.sync.sync_worker import sync_worker
from backend.app.api.health import router as health_router
from backend.app.api.telemetry import router as telemetry_router
from backend.app.api.tasks import router as tasks_router
from backend.app.api.machines import router as machines_router
from backend.app.api.operators import router as operators_router
from backend.app.api.training import router as training_router
from backend.app.api.safety import router as safety_router
from backend.app.api.sync import router as sync_router
from backend.app.api.cloud_history import router as cloud_history_router
from backend.app.api.simulator import router as simulator_router
from backend.app.api.anomalies import router as anomalies_router
from backend.app.api.eta import router as eta_router
from backend.app.edge.telemetry_ws import router as edge_ws_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown lifecycle manager.
    Initializes edge SQLite and cloud database tables, starts the background sync worker.
    """
    # 1. Initialize edge tables
    init_tables()

    # 2. Initialize cloud database tables
    init_cloud_tables()

    # 3. Check and seed synthetic data if available
    synthetic_dir = Path("data/synthetic")
    if synthetic_dir.exists():
        db = SessionLocal()
        try:
            load_synthetic_data(db, synthetic_dir)
        finally:
            db.close()

    # 4. Start edge-to-cloud synchronization worker
    sync_worker.start()

    yield

    # 5. Clean shutdown of sync worker
    sync_worker.stop()


app = FastAPI(
    title="ShiftGuard Edge API",
    description="Smart Operator Assistant for CAT Machinery — Edge, Cloud and Advisory Analytics",
    version="2.7.0",
    lifespan=lifespan,
)

# Configure CORS
origins = settings.CORS_ORIGINS
if isinstance(origins, str):
    origins = [origins]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(health_router)
app.include_router(telemetry_router)
app.include_router(tasks_router)
app.include_router(machines_router)
app.include_router(operators_router)
app.include_router(training_router)
app.include_router(safety_router)
app.include_router(edge_ws_router)
app.include_router(sync_router)
app.include_router(cloud_history_router)
app.include_router(simulator_router)
app.include_router(anomalies_router)
app.include_router(eta_router)


@app.get("/", tags=["Root"])
def root():
    """Root metadata endpoint."""
    return {
        "service": settings.SERVICE_NAME,
        "version": "2.7.0",
        "phase": 7,
        "status": "operational",
        "docs_url": "/docs",
        "health_url": "/health",
    }
