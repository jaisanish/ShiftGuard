"""
ShiftGuard Simulator & Hazard Injection Endpoints
=================================================

Provides API triggers to inject operational and safety hazard scenarios
directly into the edge ingestion pipeline for live demonstrations and testing.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Query, BackgroundTasks, HTTPException
from pydantic import BaseModel

from simulator.generator import TelemetryGenerator
from simulator.scenarios import SCENARIO_DESCRIPTIONS, SCENARIO_TASK_MAP
from backend.app.sync.sync_worker import sync_worker
from backend.app.services.broadcast_service import broadcast_service
from backend.app.database.connection import SessionLocal
from backend.app.services.telemetry_service import TelemetryService
from backend.app.edge.engine import edge_safety_engine
from backend.app.edge.safety_features import to_canonical_operating_state

logger = logging.getLogger("shiftguard.api.simulator")

router = APIRouter(prefix="/api/simulator", tags=["Simulator & Hazard Injection"])


class HazardInjectResponse(BaseModel):
    status: str
    scenario: str
    frames_injected: int
    message: str


class DemoRunRequest(BaseModel):
    scenario: str
    machine_id: Optional[str] = None
    frame_delay_ms: int = 0


DEMO_SCENARIOS = {
    **{name: {"telemetry_scenario": name, "description": SCENARIO_DESCRIPTIONS[name], "expected": "Deterministic telemetry and edge evaluation."} for name in SCENARIO_TASK_MAP},
    "offline_sync": {"telemetry_scenario": "normal", "description": "Normal edge operation while cloud synchronization is deliberately unavailable.", "expected": "Telemetry remains local and the outbox retains pending events until cloud restoration."},
}
demo_status = {"status": "idle", "run_id": None, "scenario": None, "frames_processed": 0, "cloud_forced_offline": False}


async def _run_hazard_injection(scenario: str, machine_id: Optional[str] = None, frame_delay_seconds: float = 0.5) -> int:
    """Asynchronously generates and feeds frames into the edge pipeline."""
    gen = TelemetryGenerator(
        scenario=scenario,
        machine_id=machine_id,
        loop=False,
        base_step_seconds=1.0,
    )

    frames = list(gen.generate_frames())
    logger.info(f"[SIMULATOR API] Injecting {len(frames)} frames for scenario '{scenario}'")

    for frame in frames:
        db = SessionLocal()
        try:
            val = TelemetryService.validate_telemetry(frame)
            rec, is_new = TelemetryService.store_telemetry(db, val)
            if is_new:
                from backend.app.sync.event_serializer import serialize_telemetry_event
                from backend.app.sync.outbox import OutboxService
                OutboxService.enqueue_event(db, "TELEMETRY", serialize_telemetry_event(rec))

            val_dict = val.model_dump()
            safety_res = edge_safety_engine.evaluate_telemetry(db, val_dict)

            # Broadcast canonical telemetry
            b_payload = dict(val_dict)
            b_payload["operating_state"] = to_canonical_operating_state(
                val_dict.get("operating_state"),
                val_dict.get("machine_speed_kmh", 0.0),
                val_dict.get("engine_rpm", 0.0),
            )
            await broadcast_service.broadcast_telemetry(b_payload)

            # Broadcast safety update
            await broadcast_service.broadcast_event({
                "type": "safety_update",
                "data": safety_res,
            })

            # Broadcast incident created if any
            if safety_res.get("new_incident"):
                await broadcast_service.broadcast_event({
                    "type": "incident_created",
                    "data": safety_res["new_incident"],
                })

        except Exception as e:
            logger.error(f"[SIMULATOR API] Error injecting frame: {e}")
        finally:
            db.close()

        if frame_delay_seconds:
            await asyncio.sleep(frame_delay_seconds)
    return len(frames)


@router.get("/demo/scenarios")
def list_demo_scenarios():
    """List named deterministic demo scripts and their expected outcomes."""
    return [{"id": name, **details} for name, details in DEMO_SCENARIOS.items()]


@router.get("/demo/status")
def get_demo_status():
    """Return the most recent deterministic demo run without mutating telemetry history."""
    return demo_status


@router.post("/demo/run")
async def run_deterministic_demo(request: DemoRunRequest):
    """Run every frame in a named scenario before returning; zero delay is repeatable and presentation-friendly."""
    scenario_id = request.scenario.strip().lower()
    if scenario_id not in DEMO_SCENARIOS:
        raise HTTPException(status_code=400, detail=f"Invalid demo scenario. Valid values: {list(DEMO_SCENARIOS)}")
    run_id = str(uuid.uuid4())
    details = DEMO_SCENARIOS[scenario_id]
    force_offline = scenario_id == "offline_sync"
    if force_offline:
        sync_worker.cloud_override_enabled = False
        sync_worker.cloud_connected = False
    demo_status.update({"status": "running", "run_id": run_id, "scenario": scenario_id, "frames_processed": 0, "cloud_forced_offline": force_offline, "started_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")})
    try:
        count = await _run_hazard_injection(details["telemetry_scenario"], request.machine_id, max(request.frame_delay_ms, 0) / 1000)
        demo_status.update({"status": "completed", "frames_processed": count, "completed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")})
    except Exception as exc:
        demo_status.update({"status": "failed", "error": str(exc)})
        raise HTTPException(status_code=500, detail=f"Demo run failed: {exc}") from exc
    return {**demo_status, "description": details["description"], "expected": details["expected"]}


@router.post("/demo/restore-cloud")
def restore_demo_cloud():
    """End an offline-sync demo and return cloud control to normal configuration."""
    sync_worker.cloud_override_enabled = None
    sync_worker.cloud_connected = True
    demo_status["cloud_forced_offline"] = False
    return {"status": "restored", "cloud_connected": True}


@router.post("/inject-hazard", response_model=HazardInjectResponse)
async def inject_hazard(
    scenario: str = Query(
        "proximity_critical",
        description="Scenario to inject: proximity_critical, seatbelt_violation, proximity_warning, normal"
    ),
    machine_id: Optional[str] = Query(None, description="Optional machine ID override"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    """
    Trigger an immediate simulation hazard scenario (e.g. proximity_critical, seatbelt_violation).
    Frames are processed by the EdgeSafetyEngine in real time, triggering alerts,
    updating the frontend console via WebSocket, and queuing outbox events.
    """
    clean_scenario = scenario.strip().lower()
    if clean_scenario not in SCENARIO_TASK_MAP:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid scenario '{scenario}'. Valid options: {list(SCENARIO_TASK_MAP.keys())}"
        )

    background_tasks.add_task(_run_hazard_injection, clean_scenario, machine_id)
    return HazardInjectResponse(
        status="initiated",
        scenario=clean_scenario,
        frames_injected=len(list(TelemetryGenerator(scenario=clean_scenario).generate_frames())),
        message=f"Scenario '{clean_scenario}' triggered. Streaming frames into Edge Safety Engine.",
    )
