from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.database.models import TaskModel
from backend.app.schemas.task import TaskResponse

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])


@router.get("", response_model=List[TaskResponse])
def get_tasks(
    machine_id: Optional[str] = Query(None, description="Filter by machinery ID"),
    operator_id: Optional[str] = Query(None, description="Filter by operator ID"),
    task_type: Optional[str] = Query(None, description="Filter by task type"),
    limit: int = Query(100, ge=1, le=1000, description="Max records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    db: Session = Depends(get_db),
):
    """
    List dispatched task assignments with optional filtering by machine, operator, or type.
    """
    stmt = select(TaskModel)

    if machine_id:
        stmt = stmt.where(TaskModel.machine_id == machine_id)
    if operator_id:
        stmt = stmt.where(TaskModel.operator_id == operator_id)
    if task_type:
        stmt = stmt.where(TaskModel.task_type == task_type)

    stmt = stmt.order_by(TaskModel.planned_start.asc()).offset(offset).limit(limit)
    tasks = db.execute(stmt).scalars().all()

    return tasks


@router.get("/{task_id}", response_model=TaskResponse)
def get_task_by_id(task_id: str, db: Session = Depends(get_db)):
    """
    Retrieve single task record by unique task_id.
    """
    task = db.execute(
        select(TaskModel).where(TaskModel.task_id == task_id)
    ).scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task '{task_id}' not found",
        )

    return task
