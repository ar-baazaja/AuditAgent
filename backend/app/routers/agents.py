"""Multi-agent scan endpoints (Phase 2)."""
from fastapi import APIRouter, HTTPException

from app.agents.llm import llm_available
from app.agents.orchestrator import ComplianceOrchestrator
from app.schemas import ScanRequest, ScanResponse
from app.services import repository

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])
_orchestrator = ComplianceOrchestrator()


@router.get("/status")
def agent_status():
    """Report which evaluation engine is active (LLM vs heuristic fallback)."""
    return {
        "evaluation_engine": "llm" if llm_available() else "heuristic",
        "llm_available": llm_available(),
    }


@router.post("/scan", response_model=ScanResponse)
def run_scan(request: ScanRequest):
    """Run the full multi-agent evidence-collection + evaluation pipeline."""
    if not repository.get_organization(request.organization_id):
        raise HTTPException(status_code=404, detail="organization not found")
    try:
        return _orchestrator.run_scan(request.organization_id, request.framework_key)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
