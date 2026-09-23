from pydantic import BaseModel, ConfigDict, Field


class TaskResponse(BaseModel):
    """
    Task record response model matching task_history.csv exactly.
    """
    task_id: str = Field(..., description="Unique task identifier")
    machine_id: str = Field(..., description="Assigned machinery ID")
    operator_id: str = Field(..., description="Assigned operator ID")
    task_type: str = Field(..., description="Type of earthmoving work order")
    weather: str = Field(..., description="Weather condition during task")
    operator_skill: str = Field(..., description="Operator experience level")
    machine_age_years: float = Field(..., description="Age of machine in years")
    estimated_time_min: float = Field(..., description="Estimated task duration in minutes")
    actual_time_min: float = Field(..., description="Actual recorded duration in minutes")
    planned_start: str = Field(..., description="Scheduled start ISO timestamp")
    actual_start: str = Field(..., description="Actual start ISO timestamp")
    working_condition: str = Field(..., description="Ground/terrain working condition")

    model_config = ConfigDict(from_attributes=True)
