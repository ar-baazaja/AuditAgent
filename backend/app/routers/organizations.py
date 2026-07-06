"""Organization endpoints (read-only for the MVP dashboard)."""
from fastapi import APIRouter, HTTPException, Depends

from app.services import repository
from app.auth import verify_organization_access, get_current_user

router = APIRouter(prefix="/api/v1/organizations", tags=["organizations"])


@router.get("")
def list_organizations(user_id: str = Depends(get_current_user)):
    """Return only organizations the user is a member of."""
    supabase = repository.get_supabase()
    res = supabase.table("organization_members").select("organization_id").eq("user_id", user_id).execute()
    org_ids = [m["organization_id"] for m in res.data] if res.data else []
    if not org_ids:
        return []
    orgs = supabase.table("organizations").select("*").in_("id", org_ids).execute()
    return orgs.data


@router.get("/{organization_id}")
def get_organization(organization_id: str = Depends(verify_organization_access)):
    org = repository.get_organization(organization_id)
    if not org:
        raise HTTPException(status_code=404, detail="organization not found")
    return org
