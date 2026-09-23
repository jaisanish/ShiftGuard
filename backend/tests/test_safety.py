"""
Automated tests for ShiftGuard Edge Safety Engine, Alerts, and Incidents
========================================================================
"""

import json
import pytest
from backend.app.database.models import AlertModel, IncidentModel
from backend.app.edge.engine import edge_safety_engine


def test_safety_status_endpoint(client, db_session):
    """Verify GET /api/safety/status returns valid safety state."""
    response = client.get("/api/safety/status?machine_id=CAT-797F-102")
    assert response.status_code == 200
    data = response.json()
    assert data["machine_id"] == "CAT-797F-102"
    assert data["safety_state"] in ("NORMAL", "WARNING", "CRITICAL")
    assert "proximity_distance_m" in data
    assert "active_alerts" in data


def test_edge_safety_engine_evaluation_nominal(db_session):
    """Test deterministic evaluation on nominal telemetry."""
    frame = {
        "machine_id": "CAT-797F-102",
        "operator_id": "OP-102",
        "timestamp": "2026-09-24T10:00:00Z",
        "machine_speed_kmh": 25.0,
        "engine_rpm": 1600.0,
        "seatbelt_status": "FASTENED",
        "proximity_distance_m": 35.0,
        "operating_state": "TRAVELLING",
        "task_id": "TSK-DEMO-01",
    }
    res = edge_safety_engine.evaluate_telemetry(db_session, frame)
    assert res["safety_state"] == "NORMAL"
    assert res["is_critical"] is False
    assert res["critical_alert"] is None
    assert res["new_incident"] is None


def test_edge_safety_engine_proximity_critical(db_session):
    """Test critical proximity violation (< 2.0m) creates Alert and Incident with context buffer."""
    frame = {
        "machine_id": "CAT-797F-102",
        "operator_id": "OP-102",
        "timestamp": "2026-09-24T10:05:00Z",
        "machine_speed_kmh": 12.0,
        "engine_rpm": 1400.0,
        "seatbelt_status": "FASTENED",
        "proximity_distance_m": 1.8,  # Critical < 2.0m
        "operating_state": "TRAVELLING",
        "task_id": "TSK-DEMO-04",
        "gps_zone": "CRUSHER_FEED_1",
    }
    res = edge_safety_engine.evaluate_telemetry(db_session, frame)
    assert res["safety_state"] == "CRITICAL"
    assert res["is_critical"] is True
    assert res["critical_alert"] is not None
    assert res["critical_alert"]["alert_type"] == "PROXIMITY"
    assert res["new_incident"] is not None
    assert res["new_incident"]["incident_type"] == "PROXIMITY"

    inc_id = res["new_incident"]["id"]
    # Verify incident saved in database
    inc_record = db_session.query(IncidentModel).filter(IncidentModel.id == inc_id).first()
    assert inc_record is not None
    assert inc_record.severity == "CRITICAL"
    assert inc_record.status == "OPEN"
    # Verify context buffer JSON
    ctx = json.loads(inc_record.context_buffer)
    assert "trigger_event" in ctx
    assert ctx["trigger_event"]["proximity_distance_m"] == 1.8


def test_incidents_rest_endpoints(client, db_session):
    """Test GET /api/incidents and GET /api/incidents/{id} endpoints."""
    # First create an incident via engine
    frame = {
        "machine_id": "CAT-797F-102",
        "operator_id": "OP-102",
        "timestamp": "2026-09-24T10:10:00Z",
        "machine_speed_kmh": 8.0,
        "engine_rpm": 1200.0,
        "seatbelt_status": "FASTENED",
        "proximity_distance_m": 1.5,
        "operating_state": "TRAVELLING",
        "task_id": "TSK-DEMO-04",
    }
    res = edge_safety_engine.evaluate_telemetry(db_session, frame)
    inc_id = res["new_incident"]["id"]

    # Query incident list
    list_res = client.get("/api/incidents?machine_id=CAT-797F-102")
    assert list_res.status_code == 200
    incidents = list_res.json()
    assert len(incidents) >= 1
    target = [i for i in incidents if i["id"] == inc_id][0]
    assert target["incident_type"] == "PROXIMITY"
    assert target["severity"] == "CRITICAL"

    # Query incident detail
    detail_res = client.get(f"/api/incidents/{inc_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["id"] == inc_id
    assert detail["context_buffer"] is not None
    assert "trigger_event" in detail["context_buffer"]
    assert detail["context_buffer"]["trigger_event"]["proximity_distance_m"] == 1.5

    # Acknowledge incident
    ack_res = client.post(f"/api/incidents/{inc_id}/acknowledge", json={"operator_id": "OP-101"})
    assert ack_res.status_code == 200
    ack_data = ack_res.json()
    assert ack_data["acknowledged"] is True

    # Confirm status updated to ACKNOWLEDGED
    updated_res = client.get(f"/api/incidents/{inc_id}")
    assert updated_res.json()["status"] == "ACKNOWLEDGED"


def test_alerts_rest_endpoints(client, db_session):
    """Test GET /api/alerts and POST /api/alerts/{id}/acknowledge."""
    # Create an alert
    frame = {
        "machine_id": "CAT-797F-102",
        "operator_id": "OP-102",
        "timestamp": "2026-09-24T10:15:00Z",
        "machine_speed_kmh": 5.0,
        "engine_rpm": 1100.0,
        "seatbelt_status": "FASTENED",
        "proximity_distance_m": 4.2,  # Warning distance <= 5.0m
        "operating_state": "TRAVELLING",
        "task_id": "TSK-DEMO-03",
    }
    res = edge_safety_engine.evaluate_telemetry(db_session, frame)
    assert len(res["active_alerts"]) > 0
    alert_id = res["active_alerts"][0]["id"]

    # Query alerts
    alerts_res = client.get("/api/alerts?machine_id=CAT-797F-102")
    assert alerts_res.status_code == 200
    alerts = alerts_res.json()
    assert any(a["id"] == alert_id for a in alerts)

    # Acknowledge alert
    ack_res = client.post(f"/api/alerts/{alert_id}/acknowledge")
    assert ack_res.status_code == 200
    assert ack_res.json()["acknowledged"] is True

    # 404 on non-existent alert
    missing_res = client.post("/api/alerts/non-existent-uuid/acknowledge")
    assert missing_res.status_code == 404
