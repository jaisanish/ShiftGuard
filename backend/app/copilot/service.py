"""Retrieval-augmented in-cab copilot with a deterministic offline fallback."""
from __future__ import annotations
import re
from typing import Any
import httpx
from backend.app.config import settings
from backend.app.copilot.knowledge import DOCUMENTS, KNOWLEDGE_VERSION

def _tokens(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", value.lower()))

class CopilotService:
    def retrieve(self, query: str, limit: int = 3) -> list[dict[str, Any]]:
        wanted = _tokens(query)
        ranked = sorted(((len(wanted & _tokens(f"{d['title']} {d['text']}")), d) for d in DOCUMENTS), reverse=True, key=lambda item: item[0])
        return [{"id": d["id"], "title": d["title"], "excerpt": d["text"], "score": score} for score, d in ranked if score][:limit]

    def local_answer(self, query: str, context: dict[str, Any], sources: list[dict[str, Any]]) -> str:
        normalized, telemetry, eta = query.lower(), context.get("telemetry") or {}, context.get("eta") or {}
        if "next task" in normalized:
            task = context.get("upcoming_task") or {}
            return f"Next queued assignment: {task.get('task_type', 'not available').replace('_', ' ')} ({task.get('task_id', 'unassigned')})."
        if "eta" in normalized or "complete" in normalized or "how long" in normalized:
            return f"ETA advisory: {eta.get('predicted_remaining_minutes')} minutes remaining; total estimate {eta.get('predicted_minutes')} minutes, with a {eta.get('interval_lower')}–{eta.get('interval_upper')} minute uncertainty band." if eta else "The ETA model has not returned a prediction; use the dispatch baseline."
        if "health" in normalized or "machine" in normalized:
            return f"Machine snapshot: state {telemetry.get('operating_state', 'unknown')}, RPM {telemetry.get('engine_rpm', 'unknown')}, coolant {telemetry.get('coolant_temp_c', 'unknown')}°C, hydraulic oil {telemetry.get('hydraulic_oil_temp_c', 'unknown')}°C, fault code {telemetry.get('fault_code', 'unknown')}. Follow any edge alert shown in the cockpit."
        if "proximity" in normalized or "safety" in normalized or "seatbelt" in normalized:
            return "Follow the deterministic edge alert displayed in the cockpit. This copilot cannot acknowledge, clear, or override any safety interlock."
        return sources[0]["excerpt"] if sources else "I can help with task status, ETA, machine health, or safety guidance."

    async def answer(self, query: str, context: dict[str, Any]) -> tuple[str, list[dict[str, Any]], str]:
        sources = self.retrieve(query)
        if settings.COPILOT_PROVIDER.lower() == "openai" and settings.OPENAI_API_KEY:
            prompt = "You are ShiftGuard's advisory in-cab assistant. Never claim control of safety. Answer concisely using sources.\nSources:\n" + "\n".join(s["excerpt"] for s in sources) + f"\nContext: {context}\nQuestion: {query}"
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    response = await client.post("https://api.openai.com/v1/responses", headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}, json={"model": settings.OPENAI_MODEL, "input": prompt})
                    response.raise_for_status()
                    return response.json().get("output_text", ""), sources, "openai"
            except Exception:
                pass
        return self.local_answer(query, context, sources), sources, "local"

    def health(self) -> dict[str, Any]:
        configured = settings.COPILOT_PROVIDER.lower() == "openai" and bool(settings.OPENAI_API_KEY)
        return {"status": "ready", "provider": "openai" if configured else "local", "knowledge_version": KNOWLEDGE_VERSION, "document_count": len(DOCUMENTS), "safety_boundary": "advisory_only"}

copilot_service = CopilotService()
