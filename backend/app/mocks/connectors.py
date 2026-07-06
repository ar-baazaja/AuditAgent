"""Mocked AWS / GitHub connectors.

These simulate pulling live infrastructure configuration WITHOUT touching any
real cloud account — so development costs nothing and is fully offline.

Design goals:
  * Realistic-looking config payloads per control (what a real collector returns).
  * Deterministic: the same (organization, control) always yields the same
    config, so re-scans are stable and demos are reproducible.
  * A realistic *mix* of compliant and non-compliant states, derived by hashing
    (org_id + control_code) — no `random` (keeps results reproducible).

Swapping in a real connector later means implementing the same
`fetch(organization_id, control)` signature against boto3 / the GitHub API.
"""
from __future__ import annotations

import hashlib
from typing import Any


def _seed(organization_id: str, control_code: str) -> int:
    """Stable pseudo-value in [0, 99] for an (org, control) pair."""
    digest = hashlib.sha256(f"{organization_id}:{control_code}".encode()).hexdigest()
    return int(digest[:8], 16) % 100


def _is_violation(organization_id: str, control_code: str) -> bool:
    """~1 in 3 controls simulate a violation, deterministically."""
    return _seed(organization_id, control_code) % 3 == 0


class AWSConnector:
    """Simulates AWS configuration reads (IAM, S3, RDS, CloudTrail, ...)."""

    source = "aws"

    def fetch(self, organization_id: str, control_code: str, category: str) -> dict[str, Any]:
        violation = _is_violation(organization_id, control_code)
        account_id = f"{_seed(organization_id, 'acct'):012d}"

        if category == "Access Control":
            return {
                "account_id": account_id,
                "iam_mfa_enabled": not violation,
                "root_account_mfa": not violation,
                "password_policy": {
                    "minimum_length": 8 if violation else 14,
                    "require_symbols": not violation,
                    "max_age_days": 365 if violation else 90,
                },
                "users_without_mfa": ["svc-legacy"] if violation else [],
            }
        if category == "Encryption":
            transit = "transit" in control_code.lower() or control_code in {"CC6.6", "164.312(e)(1)"}
            if transit:
                return {
                    "account_id": account_id,
                    "elb_tls_enabled": not violation,
                    "min_tls_version": "TLS1.0" if violation else "TLS1.2",
                    "insecure_listeners": ["app-lb:80"] if violation else [],
                }
            return {
                "account_id": account_id,
                "s3_default_encryption": not violation,
                "rds_storage_encrypted": not violation,
                "kms_key_rotation": not violation,
                "unencrypted_buckets": ["legacy-exports"] if violation else [],
            }
        if category == "Monitoring":
            return {
                "account_id": account_id,
                "cloudtrail_enabled": not violation,
                "multi_region_trail": not violation,
                "log_retention_days": 7 if violation else 365,
                "cloudwatch_alarms": 0 if violation else 12,
            }
        # Generic fallback config.
        return {
            "account_id": account_id,
            "resource_scanned": True,
            "misconfigured": violation,
        }


class GitHubConnector:
    """Simulates GitHub org/repo settings (branch protection, reviews, ...)."""

    source = "github"

    def fetch(self, organization_id: str, control_code: str, category: str) -> dict[str, Any]:
        violation = _is_violation(organization_id, control_code)
        return {
            "org": f"acme-{_seed(organization_id, 'gh')}",
            "default_branch": "main",
            "branch_protection_enabled": not violation,
            "required_pull_request_reviews": 0 if violation else 2,
            "require_status_checks": not violation,
            "unprotected_repos": ["internal-scripts"] if violation else [],
        }


# Registry keyed by the control's `check_type` (evidence_source).
_CONNECTORS = {
    "aws": AWSConnector(),
    "github": GitHubConnector(),
}


def get_connector(check_type: str):
    """Return the connector for a control's check_type, defaulting to AWS."""
    return _CONNECTORS.get(check_type, _CONNECTORS["aws"])
