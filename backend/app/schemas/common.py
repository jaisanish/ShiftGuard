from typing import Optional
from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str = "ok"
    service: str = "shiftguard-edge"
    database: str = "connected"


class MachineResponse(BaseModel):
    """Machine summary response schema."""
    machine_id: str
    latest_state: Optional[str] = None
    latest_operator_id: Optional[str] = None
    latest_speed_kmh: Optional[float] = None
    latest_fuel_l: Optional[float] = None
    latest_engine_hours: Optional[float] = None
    latest_timestamp: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class OperatorResponse(BaseModel):
    """Operator summary response schema."""
    operator_id: str
    operator_skill: Optional[str] = None
    assigned_machine_id: Optional[str] = None
    latest_task_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
