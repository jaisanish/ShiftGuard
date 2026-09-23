"""
ShiftGuard Training Hub Service
===============================

Provides curriculum catalog, operator coaching recommendations,
quiz evaluations, and training history tracking.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from backend.app.database.models import AlertModel, AnomalyModel, IncidentModel, TrainingCompletionModel

from backend.app.schemas.training import (
    Lesson,
    QuizQuestion,
    TrainingCompletionRequest,
    TrainingHistoryItem,
    TrainingRecommendation,
)


DEMO_LESSONS: List[Lesson] = [
    Lesson(
        lesson_id="LES-SOZ-01",
        title="Safe Operating Zones & Spotting Separation",
        category="SAFETY",
        duration_min=6,
        description=(
            "Standard operating procedures for maintaining required clearance envelopes "
            "around crusher hoppers, dump crests, and active loading equipment."
        ),
        video_url="/training/safe-operating-zones.mp4",
        pdf_url="/training/safe-operating-zones.pdf",
        key_points=[
            "Maintain a minimum 15-meter separation envelope from active hydraulic shovels during swing arcs.",
            "Reduce speed to spotting pace (under 3.0 km/h) when within 12 meters of crusher hoppers.",
            "Never reverse closer than 5.0 meters to an unverified bench crest without spotter guidance.",
            "Sound two short horn blasts before initiating reverse in dump or crusher feed zones.",
            "Immediately halt machine if proximity radar alert elevates to RED (<3m separation).",
        ],
        quiz=[
            QuizQuestion(
                id=1,
                question="What is the minimum safe clearance envelope required when approaching an active hydraulic shovel?",
                options=["5 meters", "10 meters", "15 meters", "25 meters"],
                correct_index=2,
                explanation="CAT Safety Manual Section 4.2 mandates a 15-meter buffer from excavator cab swing radius.",
            ),
            QuizQuestion(
                id=2,
                question="What ground speed must not be exceeded once spotting within 12 meters of a crusher hopper?",
                options=["3 km/h", "8 km/h", "12 km/h", "16 km/h"],
                correct_index=0,
                explanation="Spotting procedures restrict haul trucks to under 3.0 km/h to prevent hopper barrier impact.",
            ),
            QuizQuestion(
                id=3,
                question="What audible signal is required prior to engaging reverse in a staging or dump zone?",
                options=[
                    "Continuous horn blast",
                    "Two short horn blasts",
                    "One long horn blast",
                    "No signal required if radar is active",
                ],
                correct_index=1,
                explanation="Two short horn blasts notify surrounding ground personnel and light vehicles of reverse motion.",
            ),
        ],
    ),
    Lesson(
        lesson_id="LES-SBL-02",
        title="Seatbelt Interlock Protocols & Dynamic Roll Mitigation",
        category="SAFETY",
        duration_min=4,
        description="Comprehensive review of cab restraint compliance, rollover protection systems, and automated motion interlocks.",
        video_url="/training/seatbelt-protocols.mp4",
        pdf_url="/training/seatbelt-protocols.pdf",
        key_points=[
            "Seatbelts must remain latched whenever engine RPM is above idle or transmission is in gear.",
            "Automatic alarms sound if vehicle exceeds 0.5 km/h with an unfastened harness.",
            "Three-point inertia reel belts must be inspected daily for webbing fraying and buckle latch tension.",
        ],
        quiz=[
            QuizQuestion(
                id=1,
                question="When is an operator permitted to unbuckle their three-point restraint?",
                options=[
                    "While waiting in a stationary dump queue in neutral",
                    "Only when machine is fully stopped with parking brake set",
                    "During low-speed spotting under 5 km/h",
                    "Whenever cabin air conditioning is active",
                ],
                correct_index=1,
                explanation="Restraints must remain fastened until parking brake is locked and machine is at a complete stop.",
            ),
            QuizQuestion(
                id=2,
                question="At what ground speed does the ShiftGuard seatbelt warning escalate to a critical safety alert?",
                options=["0.5 km/h", "5.0 km/h", "15.0 km/h", "25.0 km/h"],
                correct_index=0,
                explanation="Any motion detected above 0.5 km/h without a buckled harness triggers immediate safety alarms.",
            ),
            QuizQuestion(
                id=3,
                question="What daily pre-shift inspection is required on the seatbelt assembly?",
                options=[
                    "Lubricating the internal retractor spring",
                    "Testing retractor locking tension and checking webbing for cuts",
                    "Measuring belt buckle weight",
                    "No daily check required",
                ],
                correct_index=1,
                explanation="Inspectors must verify inertial locking and ensure fabric integrity before shift startup.",
            ),
        ],
    ),
    Lesson(
        lesson_id="LES-TRC-03",
        title="Muddy Ramp Traction & Severe Incline Haulage",
        category="TRACTION",
        duration_min=8,
        description="Techniques for maintaining traction on slick ramp inclines, managing retarder brake heat, and preventing wheel slip.",
        video_url="/training/ramp-traction.mp4",
        pdf_url="/training/ramp-traction.pdf",
        key_points=[
            "Select constant low transmission gear before entering a steep gradient.",
            "Avoid high throttle inputs on muddy switches to prevent torque slip and tire spinning.",
            "Monitor hydraulic oil and coolant temperatures during prolonged uphill loaded pulls.",
        ],
        quiz=[
            QuizQuestion(
                id=1,
                question="What gear selection policy is recommended when descending a 10% muddy ramp loaded?",
                options=[
                    "Neutral coasting to save fuel",
                    "Same low gear required to climb the ramp with automatic retarder engaged",
                    "Highest forward gear with intermittent service brakes",
                    "Reverse gear with emergency brake applied",
                ],
                correct_index=1,
                explanation="Rule of thumb: descend in the same low gear used to climb, relying on compression and retarder.",
            ),
            QuizQuestion(
                id=2,
                question="What should an operator do if wheel slip exceeds 25% on a wet ramp incline?",
                options=[
                    "Floor the accelerator pedal to power through",
                    "Modulate throttle gently to match tire speed to ground speed",
                    "Engage diff-lock while spinning at full throttle",
                    "Stop and dismount on the slope",
                ],
                correct_index=1,
                explanation="Easing throttle allows tire lugs to clean out and re-establish tractive adhesion without trenching.",
            ),
            QuizQuestion(
                id=3,
                question="Which telemetry indicator warns of impending powertrain overheating during heavy hauling?",
                options=[
                    "Coolant temperature exceeding 98°C and hydraulic oil exceeding 85°C",
                    "Engine RPM dropping below 1200",
                    "Fuel level dropping by 10 liters",
                    "Load cycle count incrementing",
                ],
                correct_index=0,
                explanation="Elevated thermal readings signal powertrain cooling overload requiring reduced engine load.",
            ),
        ],
    ),
]


class TrainingService:
    """
    In-memory and persistent service for operator coaching.
    """

    def __init__(self):
        self._history: List[TrainingHistoryItem] = [
            TrainingHistoryItem(
                id="rec-demo-01",
                lesson_id="LES-SBL-02",
                lesson_title="Seatbelt Interlock Protocols & Dynamic Roll Mitigation",
                operator_id="OP-101",
                completed_at="2026-09-20T14:22:00Z",
                score_pct=100,
                passed=True,
            )
        ]

    def get_lessons(self) -> List[Lesson]:
        return DEMO_LESSONS

    def get_lesson_by_id(self, lesson_id: str) -> Optional[Lesson]:
        for lesson in DEMO_LESSONS:
            if lesson.lesson_id.upper() == lesson_id.upper():
                return lesson
        return None

    def get_recommendations(self, db: Session, operator_id: Optional[str] = None) -> List[TrainingRecommendation]:
        """Map persisted advisory/safety evidence to human-reviewable lesson suggestions."""
        operator = operator_id or "OP-101"
        recommendations: list[TrainingRecommendation] = []
        proximity = list(db.execute(select(AlertModel).where(AlertModel.operator_id == operator, AlertModel.alert_type == "PROXIMITY").order_by(desc(AlertModel.timestamp)).limit(3)).scalars())
        proximity += list(db.execute(select(IncidentModel).where(IncidentModel.operator_id == operator, IncidentModel.incident_type == "PROXIMITY").order_by(desc(IncidentModel.triggered_at)).limit(3)).scalars())
        seatbelt = list(db.execute(select(AlertModel).where(AlertModel.operator_id == operator, AlertModel.alert_type == "SEATBELT").order_by(desc(AlertModel.timestamp)).limit(3)).scalars())
        anomalies = list(db.execute(select(AnomalyModel).where(AnomalyModel.operator_id == operator).order_by(desc(AnomalyModel.window_end)).limit(3)).scalars())
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        if proximity:
            recommendations.append(TrainingRecommendation(lesson_id="LES-SOZ-01", title="Safe Operating Zones & Spotting Separation", reason=f"Recommended from {len(proximity)} persisted proximity safety event(s).", operator_id=operator, recommended_at=now, priority="HIGH", duration_min=6, evidence=[f"{type(item).__name__}:{item.id}" for item in proximity]))
        if seatbelt:
            recommendations.append(TrainingRecommendation(lesson_id="LES-SBL-02", title="Seatbelt Interlock Protocols & Dynamic Roll Mitigation", reason=f"Recommended from {len(seatbelt)} persisted seatbelt safety alert(s).", operator_id=operator, recommended_at=now, priority="HIGH", duration_min=4, evidence=[f"AlertModel:{item.id}" for item in seatbelt]))
        if anomalies:
            recommendations.append(TrainingRecommendation(lesson_id="LES-TRC-03", title="Muddy Ramp Traction & Severe Incline Haulage", reason=f"Recommended from {len(anomalies)} advisory operating-pattern anomaly result(s); review with a supervisor.", operator_id=operator, recommended_at=now, priority="MEDIUM", duration_min=8, evidence=[f"AnomalyModel:{item.id}" for item in anomalies]))
        if not recommendations:
            recommendations.append(TrainingRecommendation(lesson_id="LES-SOZ-01", title="Safe Operating Zones & Spotting Separation", reason="Baseline proximity safety refresher; no recent persisted coaching trigger was found.", operator_id=operator, recommended_at=now, priority="HIGH", duration_min=6, evidence=[]))
        return recommendations

    def record_completion(self, db: Session, request: TrainingCompletionRequest) -> TrainingHistoryItem:
        lesson = self.get_lesson_by_id(request.lesson_id)
        title = lesson.title if lesson else request.lesson_id

        item = TrainingHistoryItem(
            id=str(uuid.uuid4()),
            lesson_id=request.lesson_id,
            lesson_title=title,
            operator_id=request.operator_id,
            completed_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            score_pct=request.score_pct,
            passed=request.passed,
        )
        db.add(TrainingCompletionModel(**item.model_dump()))
        db.commit()
        return item

    def get_history(self, db: Session, operator_id: Optional[str] = None) -> List[TrainingHistoryItem]:
        statement = select(TrainingCompletionModel).order_by(desc(TrainingCompletionModel.completed_at))
        if operator_id:
            statement = statement.where(TrainingCompletionModel.operator_id == operator_id)
        return [TrainingHistoryItem.model_validate(row, from_attributes=True) for row in db.execute(statement).scalars()]


# Global singleton
training_service = TrainingService()
