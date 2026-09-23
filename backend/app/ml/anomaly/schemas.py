"""Pydantic API contracts for Phase 6 anomaly analytics."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class AnomalyEvidence(BaseModel):
    feature: str
    current_value: float
    baseline_value: float
    deviation_sigma: float
    direction: str
    message: str


class AnomalyInsight(BaseModel):
    id: Optional[str] = None
    timestamp: str
    machine_id: str
    operator_id: str
    window_start: str
    window_end: str
    is_anomaly: bool
    anomaly_type: str
    anomaly_score: float = Field(ge=0.0, le=1.0)
    current_value: Optional[float] = None
    baseline_value: Optional[float] = None
    evidence: list[AnomalyEvidence] = Field(default_factory=list)
    baseline_source: str
    model_version: str
    created_at: str


class AnomalyRecordResponse(BaseModel):
    id: str
    timestamp: str
    machine_id: str
    operator_id: str
    window_start: str
    window_end: str
    anomaly_type: str
    anomaly_score: float
    current_value: Optional[float] = None
    baseline_value: Optional[float] = None
    evidence: str
    model_version: str
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class OperatorBaselineResponse(BaseModel):
    operator_id: str
    source: str
    window_count: int
    sufficient_history: bool
    minimum_operator_windows: int
    statistics: dict[str, dict[str, float]]


class AnomalyModelHealth(BaseModel):
    status: str
    model_loaded: bool
    model_version: Optional[str] = None
    last_trained: Optional[str] = None
    dataset_version: Optional[str] = None
    feature_schema: list[str] = Field(default_factory=list)
    artifact_path: str
    error: Optional[str] = None


class AnomalySummary(BaseModel):
    operator_id: str
    total_anomalies: int
    by_type: dict[str, int]
    latest: Optional[AnomalyInsight] = None
    model_health: AnomalyModelHealth


class AnalyzeRequest(BaseModel):
    machine_id: str
    operator_id: Optional[str] = None
    persist_if_anomaly: bool = True


class TrainingMetadata(BaseModel):
    model_version: str
    model_type: str
    trained_at: str
    dataset_version: str
    dataset_sha256: str
    training_rows: int
    feature_window_count: int
    feature_schema: list[str]
    window_minutes: int
    minimum_operator_windows: int
    hyperparameters: dict[str, Any]
    score_calibration: dict[str, float]
    diagnostics: dict[str, Any]
