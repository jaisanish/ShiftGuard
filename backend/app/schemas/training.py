"""
ShiftGuard Training Hub Schemas
===============================

Pydantic schemas and contracts for:
- Operator coaching recommendations
- Training lessons & curriculum
- Interactive quiz evaluations
- Completion states and operator history
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class QuizQuestion(BaseModel):
    id: int = Field(..., description="Unique question sequence number")
    question: str = Field(..., description="Quiz question text")
    options: List[str] = Field(..., description="Answer choices")
    correct_index: int = Field(..., ge=0, description="0-indexed position of correct answer")
    explanation: Optional[str] = Field(None, description="Technical rationale / manual reference")


class Lesson(BaseModel):
    lesson_id: str = Field(..., description="Unique lesson code (e.g. LES-SOZ-01)")
    title: str = Field(..., description="Lesson title")
    category: str = Field(..., description="Category (e.g. SAFETY, TRACTION, SPEED)")
    duration_min: int = Field(..., description="Estimated duration in minutes")
    description: str = Field(..., description="Overview of coaching content")
    video_url: str = Field(..., description="Path to MP4 lesson video")
    pdf_url: str = Field(..., description="Path to PDF reference guide")
    key_points: List[str] = Field(default_factory=list, description="Bullet point summary of procedures")
    quiz: List[QuizQuestion] = Field(default_factory=list, description="3-question comprehension check")


class TrainingRecommendation(BaseModel):
    lesson_id: str = Field(..., description="Target lesson ID")
    title: str = Field(..., description="Title of recommended training")
    reason: str = Field(..., description="Reason for recommendation based on telemetry")
    operator_id: str = Field(..., description="Target operator ID")
    recommended_at: str = Field(..., description="ISO 8601 timestamp of recommendation")
    priority: str = Field(default="HIGH", description="Priority level: HIGH, MEDIUM, LOW")
    duration_min: int = Field(..., description="Estimated duration in minutes")
    evidence: List[str] = Field(default_factory=list, description="Persisted advisory evidence references")


class TrainingCompletionRequest(BaseModel):
    lesson_id: str = Field(..., description="Completed lesson ID")
    operator_id: str = Field(..., description="Operator ID")
    score_pct: int = Field(..., ge=0, le=100, description="Quiz score percentage")
    passed: bool = Field(..., description="Whether pass mark was attained")


class TrainingHistoryItem(BaseModel):
    id: str = Field(..., description="Record UUID")
    lesson_id: str = Field(..., description="Completed lesson ID")
    lesson_title: str = Field(..., description="Title of lesson")
    operator_id: str = Field(..., description="Operator ID")
    completed_at: str = Field(..., description="ISO 8601 completion timestamp")
    score_pct: int = Field(..., description="Final quiz score")
    passed: bool = Field(..., description="Pass/fail status")
