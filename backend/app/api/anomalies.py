"""Phase 6 anomaly model health, inference, history and baseline APIs."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.ml.anomaly.model_registry import get_anomaly_registry
from backend.app.ml.anomaly.schemas import (
    AnalyzeRequest,
    AnomalyInsight,
    AnomalyModelHealth,
    AnomalyRecordResponse,
    AnomalySummary,
    OperatorBaselineResponse,
)
from backend.app.services.anomaly_service import anomaly_service

router = APIRouter(tags=["Anomaly Analytics"])


@router.get("/api/anomalies/model/health", response_model=AnomalyModelHealth)
def anomaly_model_health():
    return get_anomaly_registry().health()


@router.get("/api/anomalies/latest-inference", response_model=AnomalyInsight)
def latest_anomaly_inference(
    machine_id: str = Query(...),
    operator_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    try:
        return anomaly_service.infer_latest(db, machine_id, operator_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


@router.post("/api/anomalies/analyze", response_model=AnomalyInsight)
def analyze_anomaly(request: AnalyzeRequest, db: Session = Depends(get_db)):
    try:
        return anomaly_service.analyze(
            db,
            machine_id=request.machine_id,
            operator_id=request.operator_id,
            persist_if_anomaly=request.persist_if_anomaly,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


@router.get("/api/anomalies", response_model=list[AnomalyRecordResponse])
def list_anomalies(
    machine_id: Optional[str] = Query(None),
    operator_id: Optional[str] = Query(None),
    anomaly_type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    return anomaly_service.list_anomalies(
        db, machine_id, operator_id, anomaly_type, limit, offset
    )


@router.get("/api/anomalies/{anomaly_id}", response_model=AnomalyRecordResponse)
def get_anomaly(anomaly_id: str, db: Session = Depends(get_db)):
    result = anomaly_service.get_anomaly(db, anomaly_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Anomaly result not found")
    return result


@router.get("/api/operators/{operator_id}/baseline", response_model=OperatorBaselineResponse)
def get_operator_baseline(operator_id: str):
    try:
        return anomaly_service.get_baseline(operator_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


@router.get("/api/operators/{operator_id}/anomaly-summary", response_model=AnomalySummary)
def get_operator_anomaly_summary(operator_id: str, db: Session = Depends(get_db)):
    return anomaly_service.summary(db, operator_id)
