"""
Automated Tests for Edge Sync Outbox and Worker
==============================================
"""

import json
import pytest
from sqlalchemy import select
from starlette.testclient import TestClient

from backend.app.database.models import SyncOutboxModel, TelemetryModel, AlertModel, IncidentModel
from backend.app.sync.outbox import OutboxService
from backend.app.sync.event_serializer import (
    serialize_telemetry_event,
    serialize_alert_event,
    serialize_incident_event,
)
from backend.app.sync.retry import calculate_next_retry_iso
from backend.app.sync.sync_worker import sync_worker


def test_outbox_insertion(db_session):
    """Test local-first insertion into sync_outbox table."""
    payload = {"machine_id": "CAT-797F-101", "engine_rpm": 1650.0}
    record = OutboxService.enqueue_event(db_session, "TELEMETRY", payload)

    assert record.event_id is not None
    assert record.event_type == "TELEMETRY"
    assert record.status == "PENDING"
    assert record.retry_count == 0

    # Query from DB
    persisted = db_session.execute(
        select(SyncOutboxModel).where(SyncOutboxModel.event_id == record.event_id)
    ).scalar_one()
    assert json.loads(persisted.payload) == payload


def test_event_serialization(db_session):
    """Test telemetry, alert, and incident serializers produce canonical dicts."""
    telem = TelemetryModel(
        timestamp="2026-09-24T10:00:00Z",
        machine_id="CAT-797F-102",
        operator_id="OP-102",
        engine_hours=8420.0,
        engine_rpm=1700.0,
        engine_load_pct=68.0,
        machine_speed_kmh=24.5,
        fuel_used_l=25.0,
        idling_time_min=3.0,
        load_cycles=5,
        operating_state="TRAVELLING",
        seatbelt_status="FASTENED",
        proximity_distance_m=35.0,
        gps_zone="NORTH_PIT",
        working_condition="NORMAL",
        coolant_temp_c=85.0,
        hydraulic_oil_temp_c=70.0,
        fault_code="NONE",
        task_id="TSK-1001",
    )
    t_payload = serialize_telemetry_event(telem)
    assert t_payload["machine_id"] == "CAT-797F-102"
    assert t_payload["engine_rpm"] == 1700.0

    alert = AlertModel(
        id="alt-test-01",
        timestamp="2026-09-24T10:01:00Z",
        machine_id="CAT-797F-102",
        operator_id="OP-102",
        task_id="TSK-1001",
        alert_type="PROXIMITY",
        severity="CRITICAL",
        status="ACTIVE",
        title="PROXIMITY HAZARD",
        message="Obstacle distance 1.5m",
        evidence=json.dumps({"proximity_distance_m": 1.5}),
        created_at="2026-09-24T10:01:00Z",
    )
    a_payload = serialize_alert_event(alert)
    assert a_payload["alert_type"] == "PROXIMITY"
    assert a_payload["severity"] == "CRITICAL"

    inc = IncidentModel(
        id="inc-test-01",
        machine_id="CAT-797F-102",
        operator_id="OP-102",
        task_id="TSK-1001",
        alert_id="alt-test-01",
        incident_type="PROXIMITY",
        severity="CRITICAL",
        summary="Severe proximity breach",
        evidence=json.dumps({"proximity_distance_m": 1.5}),
        context_buffer=json.dumps({"pre_event": [], "trigger_event": {}}),
        started_at="2026-09-24T10:01:00Z",
        triggered_at="2026-09-24T10:01:00Z",
        status="OPEN",
        timestamp="2026-09-24T10:01:00Z",
    )
    i_payload = serialize_incident_event(inc)
    assert i_payload["incident_type"] == "PROXIMITY"
    assert i_payload["severity"] == "CRITICAL"


def test_batch_creation_and_priority(db_session):
    """Test get_pending_events prioritizes INCIDENT and ALERT over TELEMETRY."""
    OutboxService.enqueue_event(db_session, "TELEMETRY", {"speed": 10}, event_id="ev-telem-1")
    OutboxService.enqueue_event(db_session, "TELEMETRY", {"speed": 20}, event_id="ev-telem-2")
    OutboxService.enqueue_event(db_session, "ALERT", {"title": "Warning"}, event_id="ev-alert-1")
    OutboxService.enqueue_event(db_session, "INCIDENT", {"summary": "Crash hazard"}, event_id="ev-inc-1")

    pending = OutboxService.get_pending_events(db_session, batch_size=10)
    assert len(pending) == 4
    # INCIDENT must be first, then ALERT, then TELEMETRY
    assert pending[0].event_type == "INCIDENT"
    assert pending[1].event_type == "ALERT"
    assert pending[2].event_type == "TELEMETRY"
    assert pending[3].event_type == "TELEMETRY"


def test_outbox_state_transitions(db_session):
    """Test transition from PENDING -> SYNCING -> SYNCED, and FAILED with backoff."""
    ev = OutboxService.enqueue_event(db_session, "TELEMETRY", {"speed": 30}, event_id="ev-trans-1")

    # Mark SYNCING
    OutboxService.mark_syncing(db_session, [ev.event_id])
    persisted = db_session.execute(
        select(SyncOutboxModel).where(SyncOutboxModel.event_id == ev.event_id)
    ).scalar_one()
    assert persisted.status == "SYNCING"

    # Mark SYNCED
    OutboxService.mark_synced(db_session, [ev.event_id])
    db_session.refresh(persisted)
    assert persisted.status == "SYNCED"
    assert persisted.synced_at is not None

    # Test failure on another event
    ev2 = OutboxService.enqueue_event(db_session, "ALERT", {"title": "Test"}, event_id="ev-fail-1")
    OutboxService.mark_failed(db_session, ev2.event_id, "Connection refused")
    db_session.refresh(ev2)
    assert ev2.status == "FAILED"
    assert ev2.retry_count == 1
    assert ev2.last_error == "Connection refused"
    assert ev2.next_retry_at is not None


def test_retry_backoff_calculation():
    """Verify exponential backoff timestamps advance monotonically."""
    t0 = calculate_next_retry_iso(0, base_seconds=2.0)
    t1 = calculate_next_retry_iso(1, base_seconds=2.0)
    t2 = calculate_next_retry_iso(2, base_seconds=2.0)
    assert t1 > t0
    assert t2 > t1


def test_sync_status_endpoint(client, db_session):
    """Verify GET /api/sync/status returns accurate outbox metrics."""
    OutboxService.enqueue_event(db_session, "TELEMETRY", {"speed": 15}, event_id="ev-status-1")
    response = client.get("/api/sync/status")
    assert response.status_code == 200
    data = response.json()
    assert "cloud_connected" in data
    assert "pending_count" in data
    assert data["pending_count"] >= 1
    assert "total_unprocessed" in data


def test_toggle_cloud_endpoint(client):
    """Verify POST /api/sync/toggle-cloud sets simulation state."""
    response = client.post("/api/sync/toggle-cloud?connected=false")
    assert response.status_code == 200
    assert response.json()["cloud_connected"] is False
    assert sync_worker.cloud_connected is False

    # Restore
    response = client.post("/api/sync/toggle-cloud?connected=true")
    assert response.status_code == 200
    assert response.json()["cloud_connected"] is True
    assert sync_worker.cloud_connected is True
