import pytest
from pydantic import ValidationError
from backend.app.schemas.telemetry import TelemetryResponse
from backend.app.schemas.task import TaskResponse
from backend.app.schemas.common import HealthResponse, MachineResponse, OperatorResponse


def test_valid_telemetry_schema():
    """Verify TelemetryResponse accepts valid 19-field dictionary."""
    data = {
        "timestamp": "2026-09-20T06:00:00Z",
        "machine_id": "CAT-797F-101",
        "operator_id": "OP-101",
        "engine_hours": 8420.5,
        "engine_rpm": 1680.0,
        "engine_load_pct": 65.0,
        "machine_speed_kmh": 28.5,
        "fuel_used_l": 15.4,
        "idling_time_min": 2.5,
        "load_cycles": 3,
        "operating_state": "HAULING_LOADED",
        "seatbelt_status": "FASTENED",
        "proximity_distance_m": 35.0,
        "gps_zone": "HAUL_ROAD_NORTH",
        "working_condition": "NORMAL",
        "coolant_temp_c": 86.2,
        "hydraulic_oil_temp_c": 72.0,
        "fault_code": "NONE",
        "task_id": "TSK-1001",
    }
    model = TelemetryResponse(**data)
    assert model.machine_id == "CAT-797F-101"
    assert model.engine_rpm == 1680.0
    assert model.seatbelt_status == "FASTENED"


def test_telemetry_missing_field_raises_validation_error():
    """Verify missing required fields raise Pydantic ValidationError."""
    incomplete_data = {
        "timestamp": "2026-09-20T06:00:00Z",
        "machine_id": "CAT-797F-101",
        # operator_id missing
        "engine_hours": 8420.5,
    }
    with pytest.raises(ValidationError):
        TelemetryResponse(**incomplete_data)


def test_telemetry_invalid_type_raises_validation_error():
    """Verify invalid numeric type raises Pydantic ValidationError."""
    invalid_data = {
        "timestamp": "2026-09-20T06:00:00Z",
        "machine_id": "CAT-797F-101",
        "operator_id": "OP-101",
        "engine_hours": "NOT_A_FLOAT",
        "engine_rpm": 1680.0,
        "engine_load_pct": 65.0,
        "machine_speed_kmh": 28.5,
        "fuel_used_l": 15.4,
        "idling_time_min": 2.5,
        "load_cycles": 3,
        "operating_state": "HAULING_LOADED",
        "seatbelt_status": "FASTENED",
        "proximity_distance_m": 35.0,
        "gps_zone": "HAUL_ROAD_NORTH",
        "working_condition": "NORMAL",
        "coolant_temp_c": 86.2,
        "hydraulic_oil_temp_c": 72.0,
        "fault_code": "NONE",
        "task_id": "TSK-1001",
    }
    with pytest.raises(ValidationError):
        TelemetryResponse(**invalid_data)


def test_valid_task_schema():
    """Verify TaskResponse accepts valid 12-field dictionary."""
    data = {
        "task_id": "TSK-1001",
        "machine_id": "CAT-797F-101",
        "operator_id": "OP-101",
        "task_type": "OVERBURDEN_REMOVAL",
        "weather": "CLEAR",
        "operator_skill": "EXPERT",
        "machine_age_years": 3.2,
        "estimated_time_min": 57.0,
        "actual_time_min": 52.3,
        "planned_start": "2026-09-20T06:00:00Z",
        "actual_start": "2026-09-20T06:02:00Z",
        "working_condition": "NORMAL",
    }
    model = TaskResponse(**data)
    assert model.task_id == "TSK-1001"
    assert model.operator_skill == "EXPERT"
    assert model.actual_time_min == 52.3


def test_task_missing_field_raises_validation_error():
    """Verify missing required fields in task schema raise ValidationError."""
    incomplete_data = {
        "task_id": "TSK-1001",
        "machine_id": "CAT-797F-101",
    }
    with pytest.raises(ValidationError):
        TaskResponse(**incomplete_data)


def test_health_response_schema():
    """Verify HealthResponse schema structure."""
    res = HealthResponse(status="ok", service="shiftguard-edge", database="connected")
    assert res.status == "ok"
    assert res.service == "shiftguard-edge"
    assert res.database == "connected"
