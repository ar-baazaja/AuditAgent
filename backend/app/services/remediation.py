"""Phase 5 — Auto-remediation ticketing.

Generates mock Jira/Linear tickets (persisted in `remediation_tickets`) with a
concrete suggested fix when a control fails. `provider_ref` is a fake ticket key
(e.g. LIN-1042) so the UI looks real; swapping in the real Jira/Linear API later
means replacing `_make_provider_ref` and adding an HTTP call.
"""
from __future__ import annotations

import hashlib

from app.services import repository

# Concrete remediation guidance per control category.
_FIX_LIBRARY = {
    "Access Control": (
        "Enable MFA for all IAM users and the root account. Tighten the IAM "
        "password policy: min length 14, symbols required, 90-day rotation.\n"
        "Terraform:\n"
        "  resource \"aws_iam_account_password_policy\" \"strict\" {\n"
        "    minimum_password_length = 14\n"
        "    require_symbols         = true\n"
        "    max_password_age        = 90\n"
        "  }"
    ),
    "Encryption": (
        "Enforce TLS 1.2+ on all load-balancer listeners and enable default "
        "encryption on S3 buckets and RDS instances with KMS key rotation.\n"
        "AWS CLI:\n"
        "  aws s3api put-bucket-encryption --bucket <name> \\\n"
        "    --server-side-encryption-configuration '{\"Rules\":[{\"ApplyServerSideEncryptionByDefault\":{\"SSEAlgorithm\":\"aws:kms\"}}]}'"
    ),
    "Monitoring": (
        "Enable a multi-region CloudTrail trail and set log retention to >=365 "
        "days. Add CloudWatch alarms for unauthorized API calls.\n"
        "  aws cloudtrail create-trail --name org-trail --is-multi-region-trail"
    ),
    "Change Management": (
        "Enable branch protection on the default branch: require >=2 PR reviews "
        "and passing status checks before merge.\n"
        "GitHub API: PUT /repos/{owner}/{repo}/branches/main/protection"
    ),
}

_SEVERITY_BY_CATEGORY = {
    "Access Control": "critical",
    "Encryption": "high",
    "Monitoring": "medium",
    "Change Management": "medium",
}


def suggested_fix_for(category: str) -> str:
    return _FIX_LIBRARY.get(category, "Review the finding and apply the relevant control.")


def severity_for(category: str) -> str:
    return _SEVERITY_BY_CATEGORY.get(category, "medium")


def _make_provider_ref(provider: str, control_id: str) -> str:
    prefix = "JIRA" if provider == "jira" else "LIN"
    num = int(hashlib.sha256(control_id.encode()).hexdigest()[:5], 16) % 9000 + 1000
    return f"{prefix}-{num}"


def create_ticket(
    organization_id: str,
    control: dict,
    finding_summary: str,
    provider: str = "linear",
) -> dict:
    """Create (or reuse) a remediation ticket for a failed control."""
    existing = repository.find_open_ticket(organization_id, control["id"])
    if existing:
        return existing

    category = control.get("category") or ""
    row = {
        "organization_id": organization_id,
        "control_id": control["id"],
        "provider": provider,
        "provider_ref": _make_provider_ref(provider, control["id"]),
        "title": f"[{control['code']}] {control['title']} — remediation required",
        "description": finding_summary,
        "suggested_fix": suggested_fix_for(category),
        "severity": severity_for(category),
        "status": "open",
    }
    return repository.insert_ticket(row)
