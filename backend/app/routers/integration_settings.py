"""Per-organization integration settings (GitHub / AWS credentials).

Lets each customer tell AuditAgent which of *their own* AWS role / GitHub App
installation to scan. The connectors (app/connectors/aws.py, github.py)
already read from the `integrations` table — this router is what lets users
populate it themselves instead of it being empty forever.
"""
from fastapi import APIRouter, Depends

from app.auth import get_current_user, verify_organization_access
from app.schemas import IntegrationSettings
from app.services import repository

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])


@router.get("")
def get_settings(organization_id: str = Depends(verify_organization_access)):
    integration = repository.get_integration(organization_id)
    return integration or {
        "organization_id": organization_id,
        "github_installation_id": None,
        "aws_role_arn": None,
        "aws_region": "us-east-1",
    }


@router.put("")
def update_settings(body: IntegrationSettings, user_id: str = Depends(get_current_user)):
    verify_organization_access(body.organization_id, user_id)
    fields = {
        "github_installation_id": body.github_installation_id or None,
        "aws_role_arn": body.aws_role_arn or None,
        "aws_region": body.aws_region or "us-east-1",
    }
    return repository.upsert_integration(body.organization_id, fields)
