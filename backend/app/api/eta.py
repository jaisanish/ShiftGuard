"""Phase 7 ETA model health, prediction, and history APIs."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.ml.eta.model_registry import get_eta_registry
from backend.app.ml.eta.schemas import ETAModelHealth, ETAPrediction
from backend.app.services.eta_service import eta_service

router = APIRouter(tags=["ETA Prediction"])


@router.get("/api/eta/model/health", response_model=ETAModelHealth)
def eta_model_health():
    return get_eta_registry().health()


@router.get("/api/tasks/{task_id}/eta", response_model=ETAPrediction)
def task_eta(task_id: str, persist: bool = Query(True), db: Session = Depends(get_db)):
    try:
        return eta_service.predict_task(db, task_id, persist=persist)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


@router.get("/api/eta-predictions", response_model=list[ETAPrediction])
def eta_history(task_id: str | None = None, limit: int = Query(100, ge=1, le=1000), db: Session = Depends(get_db)):
    return [ETAPrediction(prediction_id=item.id, **eta_service.record_payload(item)) for item in eta_service.list_predictions(db, task_id, limit)]
