from typing import Any, Optional
from pydantic import BaseModel, Field


class ETAPrediction(BaseModel):
    prediction_id: Optional[str] = None
    task_id: str
    machine_id: str
    operator_id: str
    timestamp: str
    planned_minutes: float
    predicted_minutes: float
    predicted_remaining_minutes: float
    p50: float
    p90: float
    interval_lower: float
    interval_upper: float
    uncertainty_minutes: float
    delta_vs_plan_minutes: float
    why_changed: list[str] = Field(default_factory=list)
    features_version: str
    model_version: str
    feature_snapshot: dict[str, Any]


class ETAModelHealth(BaseModel):
    status: str
    model_loaded: bool
    model_version: Optional[str] = None
    last_trained: Optional[str] = None
    dataset_version: Optional[str] = None
    metrics: dict[str, float] = Field(default_factory=dict)
    artifact_path: str
    error: Optional[str] = None
