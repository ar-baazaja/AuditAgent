"""Remediation ticketing endpoints (Phase 5)."""
from fastapi import APIRouter, HTTPException, Depends

from app.schemas import TicketCreateRequest
from app.services import remediation, repository
from app.auth import verify_organization_access, get_current_user

router = APIRouter(prefix="/api/v1/remediation", tags=["remediation"])


@router.get("/tickets")
def list_tickets(organization_id: str = Depends(verify_organization_access)):
    if not repository.get_organization(organization_id):
        raise HTTPException(status_code=404, detail="organization not found")
    return repository.list_tickets(organization_id)


@router.post("/tickets")
def create_ticket(request: TicketCreateRequest, user_id: str = Depends(get_current_user)):
    """Manually create a remediation ticket (auto-creation happens during scans)."""
    verify_organization_access(request.organization_id, user_id)
    control_rows = (
        repository.get_supabase()
        .table("controls")
        .select("*")
        .eq("id", request.control_id)
        .limit(1)
        .execute()
        .data
    )
    if not control_rows:
        raise HTTPException(status_code=404, detail="control not found")

    ticket = remediation.create_ticket(
        organization_id=request.organization_id,
        control=control_rows[0],
        finding_summary=request.description,
        provider=request.provider,
    )
    return ticket
