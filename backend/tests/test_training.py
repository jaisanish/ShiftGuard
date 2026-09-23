"""
Tests for ShiftGuard Training Hub API
=====================================

Validates:
- GET /api/training/recommendations
- GET /api/training/lessons
- GET /api/training/lessons/{lesson_id}
- POST /api/training/complete
- GET /api/training/history
"""

import pytest
from backend.app.database.models import AlertModel


def test_get_training_recommendations(client):
    """Test retrieving active coaching recommendations."""
    res = client.get("/api/training/recommendations?operator_id=OP-101")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    rec = data[0]
    assert rec["lesson_id"] == "LES-SOZ-01"
    assert "proximity" in rec["reason"].lower()
    assert rec["duration_min"] > 0
    assert rec["priority"] == "HIGH"


def test_get_training_lessons(client):
    """Test retrieving lesson catalog."""
    res = client.get("/api/training/lessons")
    assert res.status_code == 200
    lessons = res.json()
    assert len(lessons) >= 3
    lesson_ids = [l["lesson_id"] for l in lessons]
    assert "LES-SOZ-01" in lesson_ids
    assert "LES-SBL-02" in lesson_ids
    assert "LES-TRC-03" in lesson_ids


def test_get_single_lesson_with_quiz(client):
    """Test retrieving single lesson and verifying 3-question quiz."""
    res = client.get("/api/training/lessons/LES-SOZ-01")
    assert res.status_code == 200
    lesson = res.json()
    assert lesson["lesson_id"] == "LES-SOZ-01"
    assert len(lesson["key_points"]) >= 3
    assert len(lesson["quiz"]) == 3
    # Check question fields
    q = lesson["quiz"][0]
    assert "question" in q
    assert len(q["options"]) == 4
    assert 0 <= q["correct_index"] < 4


def test_get_lesson_not_found(client):
    """Test 404 for invalid lesson ID."""
    res = client.get("/api/training/lessons/LES-DOES-NOT-EXIST")
    assert res.status_code == 404


def test_record_training_completion_and_history(client):
    """Test recording lesson completion and querying history."""
    payload = {
        "lesson_id": "LES-SOZ-01",
        "operator_id": "OP-101",
        "score_pct": 100,
        "passed": True,
    }
    res = client.post("/api/training/complete", json=payload)
    assert res.status_code == 201
    item = res.json()
    assert item["lesson_id"] == "LES-SOZ-01"
    assert item["score_pct"] == 100
    assert item["passed"] is True

    # Check history
    h_res = client.get("/api/training/history?operator_id=OP-101")
    assert h_res.status_code == 200
    history = h_res.json()
    assert len(history) >= 1
    assert any(h["lesson_id"] == "LES-SOZ-01" for h in history)


def test_recommendation_includes_persisted_safety_evidence(client, db_session):
    db_session.add(AlertModel(
        id="alert-coach-1", timestamp="2026-09-24T12:00:00Z", machine_id="CAT-1",
        operator_id="OP-COACH", task_id="TASK-1", alert_type="PROXIMITY", severity="WARNING",
        status="ACTIVE", source="EDGE", title="Proximity", message="Clearance warning",
    ))
    db_session.commit()
    response = client.get("/api/training/recommendations?operator_id=OP-COACH")
    assert response.status_code == 200
    recommendation = response.json()[0]
    assert recommendation["lesson_id"] == "LES-SOZ-01"
    assert recommendation["evidence"] == ["AlertModel:alert-coach-1"]
