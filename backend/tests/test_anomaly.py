"""Phase 6 anomaly feature, model, persistence and API integration tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd
import pytest
from sqlalchemy import create_engine, inspect, select, text

from backend.app.database.models import AnomalyModel, SyncOutboxModel, TelemetryModel
from backend.app.database.init_db import init_tables
from backend.app.ml.anomaly.baseline import build_baselines, select_baseline
from backend.app.ml.anomaly.features import FEATURE_NAMES, build_feature_window, build_feature_windows
from backend.app.ml.anomaly.model_registry import AnomalyModelRegistry
from backend.app.ml.anomaly.predict import IsolationForestAnomalyPredictor


def _records(count: int = 20, *, idle: bool = False, operator_id: str = "OP-101"):
    start = datetime(2026, 9, 20, 6, 0, tzinfo=timezone.utc)
    rows = []
    for index in range(count):
        rows.append({
            "timestamp": (start + timedelta(seconds=45 * index)).isoformat().replace("+00:00", "Z"),
            "machine_id": "CAT-TEST-ANOMALY",
            "operator_id": operator_id,
            "engine_hours": 1000.0 + index / 80,
            "engine_rpm": 710.0 if idle else 1650.0,
            "engine_load_pct": 12.0 if idle else 65.0,
            "machine_speed_kmh": 0.0 if idle else 28.0,
            "fuel_used_l": 100.0 + index * (0.05 if idle else 0.3),
            "idling_time_min": index * 0.75 if idle else 0.0,
            "load_cycles": 4 if idle else 4 + index // 10,
            "operating_state": "IDLE" if idle else "HAULING_LOADED",
            "seatbelt_status": "FASTENED",
            "proximity_distance_m": 30.0,
            "gps_zone": "STAGING_BAY_4" if idle else "HAUL_ROAD_NORTH",
            "working_condition": "NORMAL",
            "coolant_temp_c": 84.0,
            "hydraulic_oil_temp_c": 70.0,
            "fault_code": "IDL-EXCESS-WARN" if idle else "NONE",
            "task_id": "TSK-ANOMALY",
        })
    return rows


def test_feature_window_contains_stable_causal_schema():
    window = build_feature_window(_records())
    assert set(FEATURE_NAMES).issubset(window)
    assert window["window_start"] == "2026-09-20T06:00:00Z"
    assert window["window_end"] == "2026-09-20T06:14:15Z"
    assert window["idle_ratio"] == 0.0
    assert window["load_cycles_per_hour"] > 0
    assert window["seatbelt_violation_rate"] == 0.0


def test_feature_generation_rejects_missing_values():
    records = _records()
    records[3]["fuel_used_l"] = None
    with pytest.raises(ValueError, match="missing or non-numeric"):
        build_feature_window(records)


def test_feature_windows_never_include_future_bucket_data():
    records = _records(40)
    windows = build_feature_windows(pd.DataFrame(records))
    assert len(windows) == 2
    assert windows.iloc[0]["window_end"] < windows.iloc[1]["window_start"]


def test_operator_baseline_and_global_fallback():
    windows = build_feature_windows(pd.DataFrame(_records(40)))
    baselines = build_baselines(windows, minimum_operator_windows=3)
    known = select_baseline(baselines, "OP-101")
    unknown = select_baseline(baselines, "OP-999")
    assert known["source"] == "GLOBAL_FALLBACK"  # only two windows: insufficient history
    assert unknown["source"] == "GLOBAL_FALLBACK"
    assert known["statistics"]["idle_ratio"]["sample_count"] == 2


def test_model_registry_loads_versioned_artifact():
    registry = AnomalyModelRegistry()
    assert registry.load() is True
    assert registry.health()["model_loaded"] is True
    assert registry.metadata["dataset_version"] == "synthetic-telemetry-v1"


def test_missing_artifact_fails_closed(tmp_path):
    registry = AnomalyModelRegistry(tmp_path / "missing.joblib", tmp_path / "missing.json")
    assert registry.load() is False
    assert registry.health()["status"] == "unavailable"


def test_existing_sqlite_anomaly_table_is_migrated_without_data_loss(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'legacy.db'}")
    with engine.begin() as connection:
        connection.execute(text(
            "CREATE TABLE anomalies ("
            "id VARCHAR(64) PRIMARY KEY, machine_id VARCHAR(64) NOT NULL, "
            "sensor_name VARCHAR(64) NOT NULL, anomaly_score FLOAT NOT NULL, "
            "detected_value FLOAT NOT NULL, expected_range_min FLOAT, "
            "expected_range_max FLOAT, timestamp VARCHAR(64) NOT NULL, model_version VARCHAR(64))"
        ))
        connection.execute(text(
            "INSERT INTO anomalies "
            "(id, machine_id, sensor_name, anomaly_score, detected_value, timestamp, model_version) "
            "VALUES ('legacy-1', 'CAT-LEGACY', 'rpm', 0.8, 2200, '2026-01-01T00:00:00Z', 'legacy')"
        ))
    init_tables(engine)
    columns = {column["name"] for column in inspect(engine).get_columns("anomalies")}
    assert {"operator_id", "window_start", "anomaly_type", "evidence", "created_at"}.issubset(columns)
    with engine.connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM anomalies")).scalar_one() == 1


def test_actual_model_flags_controlled_excessive_idle():
    predictor = IsolationForestAnomalyPredictor()
    result = predictor.predict_insight(build_feature_window(_records(idle=True)))
    assert result.is_anomaly is True
    assert result.anomaly_type == "EXCESSIVE_IDLE"
    assert result.model_version == "anomaly-iforest-v1.0.0"
    assert result.evidence


def test_anomaly_api_health_baseline_inference_and_persistence(client, db_session):
    for row in _records(idle=True):
        db_session.add(TelemetryModel(**row))
    db_session.commit()

    health = client.get("/api/anomalies/model/health")
    assert health.status_code == 200
    assert health.json()["model_loaded"] is True

    baseline = client.get("/api/operators/OP-101/baseline")
    assert baseline.status_code == 200
    assert baseline.json()["statistics"]["idle_ratio"]["sample_count"] > 0

    inference = client.get("/api/anomalies/latest-inference?machine_id=CAT-TEST-ANOMALY")
    assert inference.status_code == 200
    assert inference.json()["is_anomaly"] is True

    analyzed = client.post("/api/anomalies/analyze", json={
        "machine_id": "CAT-TEST-ANOMALY",
        "operator_id": "OP-101",
        "persist_if_anomaly": True,
    })
    assert analyzed.status_code == 200
    anomaly_id = analyzed.json()["id"]
    assert anomaly_id

    stored = db_session.execute(select(AnomalyModel).where(AnomalyModel.id == anomaly_id)).scalar_one()
    assert stored.anomaly_type == "EXCESSIVE_IDLE"
    outbox = db_session.execute(
        select(SyncOutboxModel).where(SyncOutboxModel.event_id == f"anomaly-{anomaly_id}")
    ).scalar_one()
    assert outbox.event_type == "ANOMALY"

    history = client.get("/api/anomalies?operator_id=OP-101")
    assert history.status_code == 200
    assert history.json()[0]["id"] == anomaly_id

    summary = client.get("/api/operators/OP-101/anomaly-summary")
    assert summary.status_code == 200
    assert summary.json()["total_anomalies"] == 1
