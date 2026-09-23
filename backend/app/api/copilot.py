"""Advisory-only Phase 8 copilot API."""
from typing import Any
from fastapi import APIRouter
from pydantic import BaseModel, Field
from backend.app.copilot.service import copilot_service
router = APIRouter(prefix="/api/copilot", tags=["In-Cab Copilot"])
class CopilotQuery(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    context: dict[str, Any] = Field(default_factory=dict)
class CopilotResponse(BaseModel):
    answer: str
    provider: str
    sources: list[dict[str, Any]]
    safety_boundary: str = "advisory_only"
@router.get("/health")
def copilot_health(): return copilot_service.health()
@router.post("/query", response_model=CopilotResponse)
async def copilot_query(request: CopilotQuery):
    answer, sources, provider = await copilot_service.answer(request.query, request.context)
    return CopilotResponse(answer=answer, provider=provider, sources=sources)
