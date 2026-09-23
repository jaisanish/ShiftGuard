"""
ShiftGuard Training Hub REST API
================================

Exposes endpoints for operator coaching recommendations,
lesson catalogs, quiz completions, and training histories.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.schemas.training import (
    Lesson,
    TrainingCompletionRequest,
    TrainingHistoryItem,
    TrainingRecommendation,
)
from backend.app.training.service import training_service
from backend.app.database.connection import get_db

router = APIRouter(prefix="/api/training", tags=["Training & Coach"])


@router.get("/recommendations", response_model=List[TrainingRecommendation])
def get_recommendations(
    operator_id: Optional[str] = Query(None, description="Target operator ID"),
    db: Session = Depends(get_db),
):
    """
    Retrieve active training recommendations for an operator.
    Later behavior analysis engine populates lesson_id, reason, operator_id, and recommended_at.
    """
    return training_service.get_recommendations(db, operator_id=operator_id)


@router.get("/lessons", response_model=List[Lesson])
def get_lessons():
    """
    Retrieve all available operator training curriculum lessons.
    """
    return training_service.get_lessons()


@router.get("/lessons/{lesson_id}", response_model=Lesson)
def get_lesson(lesson_id: str):
    """
    Retrieve a specific training module by ID with key points and quiz questions.
    """
    lesson = training_service.get_lesson_by_id(lesson_id)
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lesson '{lesson_id}' not found in curriculum catalog",
        )
    return lesson


@router.get("/history", response_model=List[TrainingHistoryItem])
def get_training_history(
    operator_id: Optional[str] = Query(None, description="Optional operator filter"),
    db: Session = Depends(get_db),
):
    """
    Retrieve history of completed operator coaching sessions and quiz scores.
    """
    return training_service.get_history(db, operator_id=operator_id)


@router.post("/complete", response_model=TrainingHistoryItem, status_code=status.HTTP_201_CREATED)
def record_completion(request: TrainingCompletionRequest, db: Session = Depends(get_db)):
    """
    Submit completed lesson and quiz results for permanent record keeping.
    """
    return training_service.record_completion(db, request)
