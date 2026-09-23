from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.database.models import TaskModel, TelemetryModel
from backend.app.schemas.common import OperatorResponse

router = APIRouter(prefix="/api/operators", tags=["Operators"])


@router.get("", response_model=List[OperatorResponse])
def get_operators(db: Session = Depends(get_db)):
    """
    List all active operators with their skill level, current machine assignment, and active task.
    """
    op_ids_from_tasks = db.execute(select(TaskModel.operator_id).distinct()).scalars().all()
    op_ids_from_telem = db.execute(select(TelemetryModel.operator_id).distinct()).scalars().all()
    all_op_ids = sorted(list(set(op_ids_from_tasks) | set(op_ids_from_telem)))

    results = []
    for oid in all_op_ids:
        # Find skill from tasks
        task_info = db.execute(
            select(TaskModel)
            .where(TaskModel.operator_id == oid)
            .order_by(desc(TaskModel.actual_start))
            .limit(1)
        ).scalar_one_or_none()

        # Find latest telemetry
        telem_info = db.execute(
            select(TelemetryModel)
            .where(TelemetryModel.operator_id == oid)
            .order_by(desc(TelemetryModel.timestamp))
            .limit(1)
        ).scalar_one_or_none()

        skill = task_info.operator_skill if task_info else "INTERMEDIATE"
        assigned_machine = telem_info.machine_id if telem_info else (task_info.machine_id if task_info else None)
        latest_task = task_info.task_id if task_info else (telem_info.task_id if telem_info else None)

        results.append(
            OperatorResponse(
                operator_id=oid,
                operator_skill=skill,
                assigned_machine_id=assigned_machine,
                latest_task_id=latest_task,
            )
        )

    return results
