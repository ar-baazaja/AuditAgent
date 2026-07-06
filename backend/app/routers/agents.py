"""Multi-agent scan endpoints (Phase 2)."""
from fastapi import APIRouter, HTTPException, Depends

from app.agents.llm import llm_available
from app.agents.orchestrator import ComplianceOrchestrator
from app.schemas import ScanRequest, ScanResponse
from app.services import repository
from app.auth import verify_organization_access, get_current_user

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
def run_scan(request: ScanRequest, user_id: str = Depends(get_current_user)):
    """Run the full multi-agent evidence-collection + evaluation pipeline."""
    verify_organization_access(request.organization_id, user_id)
    if not repository.get_organization(request.organization_id):
        raise HTTPException(status_code=404, detail="organization not found")
    try:
        return _orchestrator.run_scan(request.organization_id, request.framework_key)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
