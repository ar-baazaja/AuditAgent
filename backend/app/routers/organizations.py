"""Organization endpoints (read-only for the MVP dashboard)."""
from fastapi import APIRouter, HTTPException

from app.services import repository

router = APIRouter(prefix="/api/v1/organizations", tags=["organizations"])


@router.get("")
def list_organizations():
    return repository.list_organizations()


@router.get("/{organization_id}")
def get_organization(organization_id: str):
    org = repository.get_organization(organization_id)
    if not org:
        raise HTTPException(status_code=404, detail="organization not found")
    return org
