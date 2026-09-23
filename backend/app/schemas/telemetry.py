from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class TelemetryResponse(BaseModel):
    """
    Telemetry record response model matching telemetry_history.csv exactly.
    """
    id: Optional[int] = None
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp")
    machine_id: str = Field(..., description="Unique heavy machinery ID")
    operator_id: str = Field(..., description="Assigned operator ID")
    engine_hours: float = Field(..., description="Cumulative engine operating hours")
    engine_rpm: float = Field(..., description="Engine RPM")
    engine_load_pct: float = Field(..., description="Engine load percentage")
    machine_speed_kmh: float = Field(..., description="Ground speed in km/h")
    fuel_used_l: float = Field(..., description="Cumulative fuel consumed in liters")
    idling_time_min: float = Field(..., description="Cumulative idling minutes")
    load_cycles: int = Field(..., description="Cumulative load cycles completed")
    operating_state: str = Field(..., description="Machine operational state")
    seatbelt_status: str = Field(..., description="Seatbelt status: FASTENED or UNFASTENED")
    proximity_distance_m: float = Field(..., description="Distance to nearest obstacle in meters")
    gps_zone: str = Field(..., description="Designated mine geofence zone")
    working_condition: str = Field(..., description="Ground/operational condition")
    coolant_temp_c: float = Field(..., description="Engine coolant temperature in Celsius")
    hydraulic_oil_temp_c: float = Field(..., description="Hydraulic oil temperature in Celsius")
    fault_code: str = Field(..., description="Active diagnostic fault code or NONE")
    task_id: str = Field(..., description="Associated dispatch task identifier")

    model_config = ConfigDict(from_attributes=True)
