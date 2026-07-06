"""Gap analysis endpoint (Phase 4).

Compares company policy documents against the latest collected infrastructure
evidence per control and returns concrete gaps.
"""
from fastapi import APIRouter, HTTPException, Depends

from app.agents.evidence_collector import EvidenceCollectorAgent
from app.agents.gap_analyzer import GapAnalyzerAgent
from app.schemas import GapAnalysisRequest
from app.services import repository
from app.auth import verify_organization_access, get_current_user

router = APIRouter(prefix="/api/v1/gap-analysis", tags=["gap-analysis"])
_collector = EvidenceCollectorAgent()
_analyzer = GapAnalyzerAgent()


@router.post("")
def analyze(request: GapAnalysisRequest, user_id: str = Depends(get_current_user)):
    verify_organization_access(request.organization_id, user_id)
    if not repository.get_organization(request.organization_id):
        raise HTTPException(status_code=404, detail="organization not found")

    frameworks = repository.get_frameworks(request.framework_key)
    if not frameworks:
        raise HTTPException(status_code=400, detail="unknown framework")

    findings = []
    for framework in frameworks:
        for control in repository.get_controls_for_framework(framework["id"]):
            # Re-collect current evidence, then diff against policy.
            evidence = _collector.collect(request.organization_id, control)
            gaps = _analyzer.analyze(control, evidence)
            if gaps:
                findings.append(
                    {
                        "control_id": control["id"],
                        "control_code": control["code"],
                        "control_title": control["title"],
                        "category": control["category"],
                        "gaps": gaps,
                    }
                )

    return {
        "organization_id": request.organization_id,
        "framework_key": request.framework_key,
        "controls_with_gaps": len(findings),
        "findings": findings,
    }
