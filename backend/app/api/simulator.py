"""
ShiftGuard Simulator & Hazard Injection Endpoints
=================================================

Provides API triggers to inject operational and safety hazard scenarios
directly into the edge ingestion pipeline for live demonstrations and testing.
"""

import asyncio
import logging
from typing import Optional
from fastapi import APIRouter, Query, BackgroundTasks, HTTPException
from pydantic import BaseModel

from simulator.generator import TelemetryGenerator
from simulator.scenarios import SCENARIO_TASK_MAP
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


async def _run_hazard_injection(scenario: str, machine_id: Optional[str] = None):
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

        await asyncio.sleep(0.5)


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
