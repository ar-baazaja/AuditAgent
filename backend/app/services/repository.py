"""Data-access layer over Supabase (service_role).

All raw table reads/writes live here so routers and agents stay thin and the
DB schema is touched in exactly one place.
"""
from __future__ import annotations

from typing import Any, Optional

from app.db import get_supabase


# ---- Frameworks & controls ------------------------------------------------
def get_frameworks(framework_key: Optional[str] = None) -> list[dict]:
    q = get_supabase().table("compliance_frameworks").select("*")
    if framework_key:
        q = q.eq("key", framework_key)
    return q.execute().data


def get_controls_for_framework(framework_id: str) -> list[dict]:
    return (
        get_supabase()
        .table("controls")
        .select("*")
        .eq("framework_id", framework_id)
        .execute()
        .data
    )


# ---- Organizations --------------------------------------------------------
def list_organizations() -> list[dict]:
    return get_supabase().table("organizations").select("*").order("created_at").execute().data


def get_organization(organization_id: str) -> Optional[dict]:
    rows = (
        get_supabase()
        .table("organizations")
        .select("*")
        .eq("id", organization_id)
        .limit(1)
        .execute()
        .data
    )
    return rows[0] if rows else None


# ---- Evidence -------------------------------------------------------------
def insert_evidence(row: dict[str, Any]) -> dict:
    return get_supabase().table("evidence_logs").insert(row).execute().data[0]


def get_latest_evidence(organization_id: str) -> list[dict]:
    """Most-recent evidence row per control for an org.

    Supabase/PostgREST has no DISTINCT ON, so we fetch newest-first and dedupe
    in Python (control counts are small in the MVP).
    """
    rows = (
        get_supabase()
        .table("evidence_logs")
        .select("*")
        .eq("organization_id", organization_id)
        .order("collected_at", desc=True)
        .execute()
        .data
    )
    latest: dict[str, dict] = {}
    for row in rows:
        latest.setdefault(row["control_id"], row)
    return list(latest.values())


def get_recent_evidence(organization_id: str, limit: int = 50) -> list[dict]:
    return (
        get_supabase()
        .table("evidence_logs")
        .select("*")
        .eq("organization_id", organization_id)
        .order("collected_at", desc=True)
        .limit(limit)
        .execute()
        .data
    )


# ---- Remediation tickets --------------------------------------------------
def insert_ticket(row: dict[str, Any]) -> dict:
    return get_supabase().table("remediation_tickets").insert(row).execute().data[0]


def list_tickets(organization_id: str) -> list[dict]:
    return (
        get_supabase()
        .table("remediation_tickets")
        .select("*")
        .eq("organization_id", organization_id)
        .order("created_at", desc=True)
        .execute()
        .data
    )


def find_open_ticket(organization_id: str, control_id: str) -> Optional[dict]:
    rows = (
        get_supabase()
        .table("remediation_tickets")
        .select("*")
        .eq("organization_id", organization_id)
        .eq("control_id", control_id)
        .neq("status", "closed")
        .limit(1)
        .execute()
        .data
    )
    return rows[0] if rows else None
