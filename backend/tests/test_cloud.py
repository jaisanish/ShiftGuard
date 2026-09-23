"""
Automated Tests for Cloud Backend, Repositories, Idempotency, and History APIs
=============================================================================
"""

import json
import uuid
import pytest
from starlette.testclient import TestClient

from backend.app.cloud.cloud_db import CloudSessionLocal, init_cloud_tables
from backend.app.cloud.models import CloudEventLogModel, CloudTelemetryModel, CloudAlertModel, CloudIncidentModel
from backend.app.sync.outbox import OutboxService
from backend.app.sync.sync_worker import sync_worker


@pytest.fixture(autouse=True)
def setup_cloud_test_db():
    """Ensure cloud tables exist before tests."""
    init_cloud_tables()
    yield


def test_cloud_health_endpoint(client):
    """Verify GET /api/cloud/health returns operational status."""
    response = client.get("/api/cloud/health")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "shiftguard-cloud"
    assert data["database"] == "connected"


def test_cloud_batch_ingestion_and_idempotency(client):
    """
    Critical Idempotency Test:
    1. Ingest novel batch of TELEMETRY, ALERT, and INCIDENT.
    2. Verify accepted=3, duplicate=0.
    3. Re-submit the EXACT same batch with identical event_ids.
    4. Verify accepted=0, duplicate=3.
    5. Verify zero duplicate records created in cloud database.
    """
    eid_telem = str(uuid.uuid4())
    eid_alert = str(uuid.uuid4())
    eid_inc = str(uuid.uuid4())

    batch_payload = {
        "events": [
            {
                "event_id": eid_telem,
                "event_type": "TELEMETRY",
                "created_at": "2026-09-24T12:00:00Z",
                "payload": {
                    "timestamp": "2026-09-24T12:00:00Z",
                    "machine_id": "CAT-797F-102",
                    "operator_id": "OP-102",
                    "engine_rpm": 1680.0,
                    "machine_speed_kmh": 28.0,
                    "operating_state": "TRAVELLING",
                    "seatbelt_status": "FASTENED",
                    "proximity_distance_m": 35.0,
                    "task_id": "TSK-TEST-01",
                },
            },
            {
                "event_id": eid_alert,
                "event_type": "ALERT",
                "created_at": "2026-09-24T12:00:01Z",
                "payload": {
                    "id": f"alt-{eid_alert[:8]}",
                    "timestamp": "2026-09-24T12:00:01Z",
                    "machine_id": "CAT-797F-102",
                    "operator_id": "OP-102",
                    "task_id": "TSK-TEST-01",
                    "alert_type": "PROXIMITY",
                    "severity": "CRITICAL",
                    "status": "ACTIVE",
                    "title": "PROXIMITY HAZARD",
                    "message": "Obstacle breach <2m",
                },
            },
            {
                "event_id": eid_inc,
                "event_type": "INCIDENT",
                "created_at": "2026-09-24T12:00:02Z",
                "payload": {
                    "id": f"inc-{eid_inc[:8]}",
                    "machine_id": "CAT-797F-102",
                    "operator_id": "OP-102",
                    "task_id": "TSK-TEST-01",
                    "incident_type": "PROXIMITY",
                    "severity": "CRITICAL",
                    "summary": "Severe proximity violation",
                    "context_buffer": {"pre_event": [], "trigger_event": {}},
                    "started_at": "2026-09-24T12:00:02Z",
                    "triggered_at": "2026-09-24T12:00:02Z",
                    "status": "OPEN",
                },
            },
        ]
    }

    # First Submission: Must be ACCEPTED
    resp1 = client.post("/api/sync/events", json=batch_payload)
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["accepted"] == 3
    assert data1["duplicate"] == 0
    assert data1["failed"] == 0

    # Second Submission (Identical event_ids): Must be recognized as DUPLICATE
    resp2 = client.post("/api/sync/events", json=batch_payload)
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["accepted"] == 0
    assert data2["duplicate"] == 3
    assert data2["failed"] == 0

    # Verify no duplicate entries exist in cloud DB
    cloud_db = CloudSessionLocal()
    try:
        from sqlalchemy import select, func
        telem_count = cloud_db.execute(
            select(func.count(CloudTelemetryModel.id)).where(CloudTelemetryModel.event_id == eid_telem)
        ).scalar_one()
        assert telem_count == 1, "Expected exactly 1 telemetry record for event_id"

        alert_count = cloud_db.execute(
            select(func.count(CloudAlertModel.id)).where(CloudAlertModel.event_id == eid_alert)
        ).scalar_one()
        assert alert_count == 1, "Expected exactly 1 alert record for event_id"

        inc_count = cloud_db.execute(
            select(func.count(CloudIncidentModel.id)).where(CloudIncidentModel.event_id == eid_inc)
        ).scalar_one()
        assert inc_count == 1, "Expected exactly 1 incident record for event_id"
    finally:
        cloud_db.close()


def test_cloud_history_apis(client):
    """Test GET /api/cloud/telemetry, /api/cloud/alerts, /api/cloud/incidents."""
    # Query telemetry
    t_resp = client.get("/api/cloud/telemetry?machine_id=CAT-797F-102&limit=10")
    assert t_resp.status_code == 200
    t_data = t_resp.json()
    assert isinstance(t_data, list)

    # Query alerts
    a_resp = client.get("/api/cloud/alerts?severity=CRITICAL&limit=10")
    assert a_resp.status_code == 200
    a_data = a_resp.json()
    assert isinstance(a_data, list)

    # Query incidents
    i_resp = client.get("/api/cloud/incidents?severity=CRITICAL&limit=10")
    assert i_resp.status_code == 200
    i_data = i_resp.json()
    assert isinstance(i_data, list)


def test_end_to_end_edge_to_cloud_sync(db_session, monkeypatch):
    """
    End-to-End Integration Test:
    Edge event ──► SQLite Outbox (PENDING) ──► sync_worker.sync_once() ──► Cloud DB ──► Outbox (SYNCED)
    """
    import asyncio
    eid = str(uuid.uuid4())
    inc_id = f"inc-e2e-{eid[:8]}"
    payload = {
        "id": inc_id,
        "machine_id": "CAT-797F-102",
        "operator_id": "OP-102",
        "task_id": "TSK-E2E",
        "incident_type": "SEATBELT",
        "severity": "CRITICAL",
        "summary": "E2E Seatbelt test incident",
        "started_at": "2026-09-24T12:30:00Z",
        "triggered_at": "2026-09-24T12:30:00Z",
        "status": "OPEN",
    }

    # 1. Enqueue to edge outbox (Local-First)
    outbox_rec = OutboxService.enqueue_event(db_session, "INCIDENT", payload, event_id=eid)
    assert outbox_rec.status == "PENDING"

    # 2. Execute sync cycle
    result = asyncio.run(sync_worker.sync_once())
    assert result["cloud_connected"] is True
    assert result["synced"] >= 1

    # 3. Verify SQLite outbox record is marked SYNCED
    db_session.refresh(outbox_rec)
    assert outbox_rec.status == "SYNCED"
    assert outbox_rec.synced_at is not None

    # 4. Verify incident exists in Cloud DB
    cloud_db = CloudSessionLocal()
    try:
        from sqlalchemy import select
        cloud_inc = cloud_db.execute(
            select(CloudIncidentModel).where(CloudIncidentModel.id == inc_id)
        ).scalar_one_or_none()
        assert cloud_inc is not None
        assert cloud_inc.machine_id == "CAT-797F-102"
        assert cloud_inc.summary == "E2E Seatbelt test incident"
    finally:
        cloud_db.close()
