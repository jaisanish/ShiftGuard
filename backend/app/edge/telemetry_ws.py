"""
ShiftGuard Edge WebSocket Ingestion & Streaming
================================================

Handles high-frequency real-time telemetry streaming:
- Ingests CAN Bus / J1939 telemetry frames from Python simulators.
- Validates incoming frames against canonical Pydantic schemas.
- Stores frames in SQLite with duplicate detection.
- Broadcasts real-time updates to all connected in-cab frontend consoles.
"""

import json
import logging
from typing import Optional
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from backend.app.database.connection import SessionLocal
from backend.app.edge.engine import edge_safety_engine
from backend.app.edge.safety_features import to_canonical_operating_state
from backend.app.schemas.telemetry import TelemetryResponse
from backend.app.services.broadcast_service import broadcast_service
from backend.app.services.telemetry_service import TelemetryService

logger = logging.getLogger("shiftguard.edge_ws")

router = APIRouter(tags=["WebSocket"])


def get_session():
    return SessionLocal()


@router.websocket("/ws/telemetry")
async def websocket_telemetry_endpoint(
    websocket: WebSocket,
    role: Optional[str] = Query(None, description="Optional client role: 'simulator' or 'frontend'"),
):
    """
    Bi-directional high-frequency WebSocket endpoint for telemetry:
    - Simulators transmit telemetry JSON frames to ingest.
    - Frontend consoles connect to receive live 1Hz telemetry broadcasts,
      authoritative edge safety states, and realtime incident alerts.
    """
    client_type = role or "frontend"
    await broadcast_service.connect(websocket, client_type=client_type)

    # If it is a frontend cockpit connecting, provide initial latest telemetry & safety snapshot immediately
    if client_type == "frontend":
        try:
            with get_session() as db:
                latest = TelemetryService.get_latest(db, machine_id="CAT-797F-101")
                payload = None
                if latest:
                    payload = TelemetryResponse.model_validate(latest).model_dump()
                    payload["operating_state"] = to_canonical_operating_state(
                        payload.get("operating_state"),
                        payload.get("machine_speed_kmh", 0.0),
                        payload.get("engine_rpm", 0.0),
                    )
                    machine_id = payload.get("machine_id", "CAT-797F-101")
                else:
                    machine_id = "CAT-797F-101"

                safety_snapshot = edge_safety_engine.get_safety_state(db, machine_id)
                await websocket.send_text(json.dumps({
                    "type": "telemetry_initial",
                    "data": payload,
                    "safety": safety_snapshot
                }))
        except Exception as e:
            logger.debug(f"[EDGE INGESTION] Failed to send initial state: {e}")

    try:
        while True:
            raw_text = await websocket.receive_text()

            # 1. Parse JSON
            try:
                msg = json.loads(raw_text)
            except Exception as json_err:
                logger.warning(f"[EDGE INGESTION] Malformed JSON received: {json_err}")
                await websocket.send_text(json.dumps({
                    "status": "error",
                    "code": "MALFORMED_JSON",
                    "detail": "Incoming payload must be valid JSON"
                }))
                continue

            # Support ping/pong keepalive
            if msg.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
                continue

            # Support frontend subscribe commands
            if msg.get("type") == "subscribe":
                await websocket.send_text(json.dumps({
                    "status": "ok",
                    "action": "subscribed",
                    "machine_id": msg.get("machine_id", "all")
                }))
                continue

            # Support WebSocket alert acknowledgment
            if msg.get("type") == "acknowledge_alert":
                alert_id = msg.get("alert_id")
                op_id = msg.get("operator_id", "OP-101")
                if alert_id:
                    with get_session() as db:
                        ack = edge_safety_engine.acknowledge_alert(db, alert_id, op_id)
                        if ack:
                            await broadcast_service.broadcast_event({
                                "type": "alert_acknowledged",
                                "data": ack
                            })
                    await websocket.send_text(json.dumps({
                        "status": "ok",
                        "action": "alert_acknowledged",
                        "alert_id": alert_id
                    }))
                continue

            # Support WebSocket incident acknowledgment
            if msg.get("type") == "acknowledge_incident":
                incident_id = msg.get("incident_id")
                op_id = msg.get("operator_id", "OP-101")
                if incident_id:
                    with get_session() as db:
                        ack = edge_safety_engine.acknowledge_incident(db, incident_id, op_id)
                        if ack:
                            await broadcast_service.broadcast_event({
                                "type": "incident_acknowledged",
                                "data": ack
                            })
                    await websocket.send_text(json.dumps({
                        "status": "ok",
                        "action": "incident_acknowledged",
                        "incident_id": incident_id
                    }))
                continue

            # 2. Extract telemetry frame
            telemetry_data = msg.get("data", msg)
            if not isinstance(telemetry_data, dict) or "machine_id" not in telemetry_data:
                await websocket.send_text(json.dumps({
                    "status": "error",
                    "code": "INVALID_PAYLOAD",
                    "detail": "Payload must contain telemetry fields with 'machine_id'"
                }))
                continue

            machine_id = telemetry_data.get("machine_id")
            logger.info(f"[EDGE INGESTION] Received telemetry frame from simulator for machine {machine_id}")

            # 3. Strict schema validation
            try:
                validated = TelemetryService.validate_telemetry(telemetry_data)
            except Exception as val_err:
                await websocket.send_text(json.dumps({
                    "status": "error",
                    "code": "VALIDATION_ERROR",
                    "detail": str(val_err)
                }))
                continue

            val_dict = validated.model_dump()

            # 4. Storage to SQLite and Edge Safety Engine evaluation
            with get_session() as db:
                record, is_new = TelemetryService.store_telemetry(db, validated)
                if is_new:
                    try:
                        from backend.app.sync.event_serializer import serialize_telemetry_event
                        from backend.app.sync.outbox import OutboxService
                        OutboxService.enqueue_event(
                            db, "TELEMETRY", serialize_telemetry_event(record)
                        )
                    except Exception as outbox_err:
                        logger.warning(f"[OUTBOX] Failed to enqueue telemetry: {outbox_err}")

                safety_result = edge_safety_engine.evaluate_telemetry(db, val_dict)

            # 5. Broadcast telemetry frame to connected frontend clients with canonical operating state
            broadcast_payload = dict(val_dict)
            broadcast_payload["operating_state"] = to_canonical_operating_state(
                val_dict.get("operating_state"),
                val_dict.get("machine_speed_kmh", 0.0),
                val_dict.get("engine_rpm", 0.0),
            )
            broadcast_count = await broadcast_service.broadcast_telemetry(broadcast_payload)

            # 6. Broadcast safety update event to connected frontend clients
            await broadcast_service.broadcast_event({
                "type": "safety_update",
                "data": safety_result
            })

            # 7. If a new incident was declared, broadcast incident_created event immediately
            if safety_result.get("new_incident"):
                await broadcast_service.broadcast_event({
                    "type": "incident_created",
                    "data": safety_result["new_incident"]
                })

            # 8. Return acknowledgement to sender
            await websocket.send_text(json.dumps({
                "status": "ok" if is_new else "duplicate",
                "machine_id": validated.machine_id,
                "timestamp": validated.timestamp,
                "broadcast_count": broadcast_count,
                "is_new": is_new,
                "safety_state": safety_result.get("safety_state", "NORMAL"),
            }))

    except WebSocketDisconnect:
        logger.info(f"[EDGE INGESTION] Disconnected WebSocket connection (role={client_type})")
    except Exception as e:
        logger.error(f"[EDGE INGESTION] Error in telemetry WebSocket loop: {e}")
    finally:
        await broadcast_service.disconnect(websocket)
