from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.database.models import TelemetryModel, TaskModel
from backend.app.schemas.common import MachineResponse

router = APIRouter(prefix="/api/machines", tags=["Machines"])


@router.get("", response_model=List[MachineResponse])
def get_machines(db: Session = Depends(get_db)):
    """
    List all active machines with their latest operational state and metrics.
    """
    # Find distinct machines across telemetry and tasks
    telem_machines = db.execute(select(TelemetryModel.machine_id).distinct()).scalars().all()
    task_machines = db.execute(select(TaskModel.machine_id).distinct()).scalars().all()
    all_machine_ids = sorted(list(set(telem_machines) | set(task_machines)))

    results = []
    for mid in all_machine_ids:
        latest = db.execute(
            select(TelemetryModel)
            .where(TelemetryModel.machine_id == mid)
            .order_by(desc(TelemetryModel.timestamp), desc(TelemetryModel.id))
            .limit(1)
        ).scalar_one_or_none()

        if latest:
            results.append(
                MachineResponse(
                    machine_id=mid,
                    latest_state=latest.operating_state,
                    latest_operator_id=latest.operator_id,
                    latest_speed_kmh=latest.machine_speed_kmh,
                    latest_fuel_l=latest.fuel_used_l,
                    latest_engine_hours=latest.engine_hours,
                    latest_timestamp=latest.timestamp,
                )
            )
        else:
            results.append(
                MachineResponse(
                    machine_id=mid,
                )
            )

    return results
