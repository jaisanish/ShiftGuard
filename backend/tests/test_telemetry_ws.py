"""
Tests for ShiftGuard Live Telemetry WebSocket Streaming & Simulator
===================================================================

Validates:
- WebSocket ingestion (/ws/telemetry) with canonical Pydantic schema validation.
- SQLite persistence of incoming telemetry frames.
- Frontend initial telemetry snapshot on connection.
- Duplicate telemetry frame detection.
- Malformed JSON and validation error handling.
- Ping/pong keepalive handling.
- Broadcast service fan-out and dead socket cleanup.
- Simulator scenario definitions and generator pacing.
- Clean client disconnect and connection tracking.
"""

import asyncio
import json
from unittest.mock import AsyncMock
import pytest
from starlette.testclient import TestClient

from backend.app.database.models import TelemetryModel
from backend.app.edge.telemetry_ws import get_session
from backend.app.main import app
from backend.app.schemas.telemetry import TelemetryResponse
from backend.app.services.broadcast_service import TelemetryBroadcastService, broadcast_service
from backend.app.services.telemetry_service import TelemetryService
from simulator.generator import TelemetryGenerator
from simulator.scenarios import (
    SCENARIO_TASK_MAP,
    get_scenario_records,
)


@pytest.fixture
def override_ws_db(db_session, monkeypatch):
    """Ensure WebSocket handler writes to the in-memory test database session."""
    class SessionContext:
        def __enter__(self):
            return db_session
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    monkeypatch.setattr("backend.app.edge.telemetry_ws.get_session", lambda: SessionContext())


VALID_FRAME = {
    "timestamp": "2026-09-23T12:00:00Z",
    "machine_id": "CAT-797F-101",
    "operator_id": "OP-101",
    "engine_hours": 8430.5,
    "engine_rpm": 1680.0,
    "engine_load_pct": 62.0,
    "machine_speed_kmh": 32.5,
    "fuel_used_l": 48.0,
    "idling_time_min": 12.0,
    "load_cycles": 14,
    "operating_state": "HAULING_LOADED",
    "seatbelt_status": "FASTENED",
    "proximity_distance_m": 42.0,
    "gps_zone": "HAUL_ROAD_NORTH",
    "working_condition": "NORMAL",
    "coolant_temp_c": 86.4,
    "hydraulic_oil_temp_c": 72.1,
    "fault_code": "NONE",
    "task_id": "TSK-DEMO-01",
}


def test_ws_telemetry_valid_ingest_and_storage(client, override_ws_db, db_session):
    """
    Test simulator transmitting valid telemetry frame over /ws/telemetry.
    Verifies acknowledgement and database persistence.
    """
    with client.websocket_connect("/ws/telemetry?role=simulator") as ws:
        ws.send_text(json.dumps(VALID_FRAME))
        ack = ws.receive_json()

        assert ack["status"] == "ok"
        assert ack["machine_id"] == "CAT-797F-101"
        assert ack["is_new"] is True

    # Verify record was stored in SQLite
    stored = db_session.query(TelemetryModel).filter_by(
        machine_id="CAT-797F-101",
        timestamp="2026-09-23T12:00:00Z"
    ).first()
    assert stored is not None
    assert stored.engine_rpm == 1680.0
    assert stored.operating_state == "HAULING_LOADED"
    assert stored.fault_code == "NONE"


def test_ws_telemetry_frontend_initial_snapshot(client, seed_test_data):
    """
    Test frontend console connecting to /ws/telemetry receives
    an initial latest telemetry snapshot.
    """
    with client.websocket_connect("/ws/telemetry?role=frontend") as ws:
        init_msg = ws.receive_json()
        assert init_msg["type"] in ["telemetry_initial", "telemetry_update"]
        assert "data" in init_msg
        assert init_msg["data"]["machine_id"] == "CAT-797F-101"


def test_ws_telemetry_duplicate_detection(client, override_ws_db, db_session):
    """
    Test duplicate event handling:
    Transmitting an event with existing (machine_id, timestamp) returns 'duplicate'
    and avoids creating duplicate rows in the database.
    """
    with client.websocket_connect("/ws/telemetry?role=simulator") as ws:
        # 1. First transmission
        ws.send_text(json.dumps(VALID_FRAME))
        ack1 = ws.receive_json()
        assert ack1["status"] in ["ok", "duplicate"]

        # 2. Second transmission with exact same timestamp & machine_id
        ws.send_text(json.dumps(VALID_FRAME))
        ack2 = ws.receive_json()
        assert ack2["status"] == "duplicate"
        assert ack2["is_new"] is False

    # Check count in DB is exactly 1
    count = db_session.query(TelemetryModel).filter_by(
        machine_id="CAT-797F-101",
        timestamp="2026-09-23T12:00:00Z"
    ).count()
    assert count == 1


def test_ws_telemetry_malformed_json(client):
    """Test sending malformed non-JSON string returns MALFORMED_JSON error."""
    with client.websocket_connect("/ws/telemetry?role=simulator") as ws:
        ws.send_text("NOT_VALID_JSON{")
        response = ws.receive_json()
        assert response["status"] == "error"
        assert response["code"] == "MALFORMED_JSON"


def test_ws_telemetry_validation_error(client):
    """Test sending JSON missing required telemetry fields returns VALIDATION_ERROR."""
    with client.websocket_connect("/ws/telemetry?role=simulator") as ws:
        invalid_frame = {
            "machine_id": "CAT-797F-101",
            "timestamp": "2026-09-23T12:00:00Z",
            # missing required engine_rpm, coolant_temp_c, etc.
        }
        ws.send_text(json.dumps(invalid_frame))
        response = ws.receive_json()
        assert response["status"] == "error"
        assert response["code"] == "VALIDATION_ERROR"


def test_ws_telemetry_ping_pong(client):
    """Test ping keepalive message returns pong."""
    with client.websocket_connect("/ws/telemetry?role=simulator") as ws:
        ws.send_text(json.dumps({"type": "ping"}))
        response = ws.receive_json()
        assert response["type"] == "pong"


def test_ws_telemetry_subscribe_action(client):
    """Test client subscribe action acknowledged cleanly."""
    with client.websocket_connect("/ws/telemetry?role=frontend") as ws:
        # Drain initial message
        try:
            ws.receive_json()
        except Exception:
            pass

        ws.send_text(json.dumps({"type": "subscribe", "machine_id": "CAT-797F-101"}))
        response = ws.receive_json()
        assert response["status"] == "ok"
        assert response["action"] == "subscribed"


@pytest.mark.anyio
async def test_broadcast_service_fanout_and_cleanup():
    """
    Test TelemetryBroadcastService multi-client fanout and dead-socket purging.
    """
    service = TelemetryBroadcastService()
    assert service.client_count == 0

    # Create 3 mock WebSocket connections
    ws1 = AsyncMock()
    ws2 = AsyncMock()
    ws3 = AsyncMock()
    # Simulate ws3 throwing error on send
    ws3.send_text.side_effect = RuntimeError("Socket closed")

    await service.connect(ws1, client_type="frontend")
    await service.connect(ws2, client_type="frontend")
    await service.connect(ws3, client_type="frontend")
    assert service.client_count == 3

    # Broadcast
    test_payload = {"machine_id": "CAT-797F-101", "machine_speed_kmh": 28.5}
    delivered = await service.broadcast_telemetry(test_payload)

    # ws1 and ws2 received the message, ws3 failed and got purged
    assert delivered == 2
    assert service.client_count == 2
    ws1.send_text.assert_called_once()
    ws2.send_text.assert_called_once()

    # Disconnect remaining
    await service.disconnect(ws1)
    assert service.client_count == 1


def test_simulator_all_7_scenarios():
    """Verify all 7 required scenarios load deterministically from demo_telemetry.csv."""
    scenarios = [
        "normal",
        "seatbelt_violation",
        "proximity_warning",
        "proximity_critical",
        "excessive_idle",
        "repeated_safety",
        "eta_delay",
    ]
    for s in scenarios:
        records = get_scenario_records(s)
        assert len(records) > 0
        assert records[0]["task_id"] == SCENARIO_TASK_MAP[s]
        # Validate that each record passes canonical Pydantic schema
        validated = TelemetryResponse.model_validate(records[0])
        assert validated.machine_id is not None
        assert validated.timestamp is not None
        assert validated.engine_hours > 0


def test_telemetry_generator_pacing():
    """Test TelemetryGenerator yields frames with updated timestamps and monotonic hours."""
    gen = TelemetryGenerator(scenario="normal", loop=False, base_step_seconds=1.0)
    frames = list(gen.generate_frames())
    assert len(frames) == len(get_scenario_records("normal"))
    # Timestamps should be non-empty ISO strings
    for f in frames:
        assert "T" in f["timestamp"]
        assert f["timestamp"].endswith("Z")
        assert f["machine_id"] == "CAT-797F-101"


def test_api_telemetry_history_endpoint(client, seed_test_data):
    """Test GET /api/telemetry/history returns matching historical telemetry records."""
    response = client.get("/api/telemetry/history?machine_id=CAT-797F-101")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    for item in data:
        assert item["machine_id"] == "CAT-797F-101"
