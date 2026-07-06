"""Compliance posture endpoints — scores, control status, evidence (Phase 3)."""
from fastapi import APIRouter, HTTPException

from app.schemas import ComplianceOverview
from app.services import repository, scoring

router = APIRouter(prefix="/api/v1/compliance", tags=["compliance"])


@router.get("/overview", response_model=ComplianceOverview)
def overview(organization_id: str):
    if not repository.get_organization(organization_id):
        raise HTTPException(status_code=404, detail="organization not found")
    return scoring.compute_overview(organization_id)


@router.get("/controls")
def controls_with_status(organization_id: str):
    """Every control joined with its latest evidence status for this org."""
    if not repository.get_organization(organization_id):
        raise HTTPException(status_code=404, detail="organization not found")

    latest = {e["control_id"]: e for e in repository.get_latest_evidence(organization_id)}
    out = []
    for framework in repository.get_frameworks():
        for control in repository.get_controls_for_framework(framework["id"]):
            evidence = latest.get(control["id"])
            out.append(
                {
                    "framework_key": framework["key"],
                    "framework_name": framework["name"],
                    "control_id": control["id"],
                    "code": control["code"],
                    "title": control["title"],
                    "category": control["category"],
                    "status": evidence["status"] if evidence else "not_assessed",
                    "result": evidence["result"] if evidence else None,
                    "summary": evidence["summary"] if evidence else None,
                    "collected_at": evidence["collected_at"] if evidence else None,
                }
            )
    return out


@router.get("/evidence")
def recent_evidence(organization_id: str, limit: int = 50):
    if not repository.get_organization(organization_id):
        raise HTTPException(status_code=404, detail="organization not found")
    return repository.get_recent_evidence(organization_id, limit)
