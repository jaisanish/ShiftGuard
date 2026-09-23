"""
ShiftGuard ML Contracts & Interfaces
===================================

Defines stable, decoupled abstract contracts for machine learning models.
ML engineers will implement these interfaces with their trained models
(e.g., PyTorch, scikit-learn, ONNX) without altering backend ingestion.

CRITICAL ARCHITECTURAL INVARIANT:
ML models provide advisory and predictive insights ONLY.
ML models must NEVER make real-time safety decisions, suppress alerts,
or override the deterministic Edge Safety Engine.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ============================================================================
# Anomaly Prediction Contracts
# ============================================================================

class AnomalyResult(BaseModel):
    """Output contract for telemetry sensor anomaly inference."""
    machine_id: str = Field(..., description="Target machinery identifier")
    timestamp: str = Field(..., description="Timestamp of analyzed telemetry")
    is_anomaly: bool = Field(..., description="Binary anomaly indicator")
    anomaly_score: float = Field(..., ge=0.0, le=1.0, description="Normalized score 0.0 (nominal) to 1.0 (extreme)")
    affected_sensors: List[str] = Field(default_factory=list, description="List of sensor names exhibiting deviation")
    sensor_scores: Dict[str, float] = Field(default_factory=dict, description="Per-sensor anomaly attribution scores")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Inference confidence score")
    model_version: str = Field(..., description="Artifact version or identifier")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional debug or feature metadata")


class AnomalyPredictor(ABC):
    """
    Abstract interface for Anomaly Detection ML Models.
    Implemented by Teammate C (Anomaly ML).
    """

    @abstractmethod
    def predict(self, telemetry_record: Dict[str, Any]) -> AnomalyResult:
        """
        Evaluate a single telemetry reading for physical sensor anomalies.
        Must execute with deterministic fallback if model is uninitialized.
        """
        pass

    @abstractmethod
    def batch_predict(self, telemetry_window: List[Dict[str, Any]]) -> List[AnomalyResult]:
        """
        Evaluate a rolling window of time-series telemetry records.
        """
        pass

    @abstractmethod
    def is_ready(self) -> bool:
        """Check if model weights and preprocessing pipelines are loaded and ready."""
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Return model metadata, architecture type, training version, and benchmark metrics."""
        pass


# ============================================================================
# ETA Prediction Contracts
# ============================================================================

class ETAResult(BaseModel):
    """Output contract for haul cycle & work order ETA predictions."""
    task_id: str = Field(..., description="Target task identifier")
    machine_id: str = Field(..., description="Assigned machinery identifier")
    predicted_remaining_min: float = Field(..., ge=0.0, description="Estimated minutes remaining until task completion")
    predicted_total_duration_min: float = Field(..., ge=0.0, description="Predicted total cycle duration in minutes")
    confidence_score: float = Field(default=0.85, ge=0.0, le=1.0, description="Prediction confidence score")
    model_version: str = Field(..., description="Model version or checkpoint identifier")
    feature_contributions: Dict[str, float] = Field(
        default_factory=dict, 
        description="Feature attribution (e.g. weather delay, operator factor, gradient factor)"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Auxiliary inference metadata")


class ETAPredictor(ABC):
    """
    Abstract interface for Haul Cycle / Task ETA Prediction Models.
    Implemented by Teammate C (ETA ML).
    """

    @abstractmethod
    def predict_eta(
        self,
        task_data: Dict[str, Any],
        telemetry_snapshot: Dict[str, Any],
    ) -> ETAResult:
        """
        Predict remaining task duration given active task parameters and current telemetry state.
        """
        pass

    @abstractmethod
    def is_ready(self) -> bool:
        """Check if ETA model weights and scaler artifacts are loaded."""
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Return model name, training epoch, MAE/RMSE benchmark metrics, and artifact path."""
        pass
