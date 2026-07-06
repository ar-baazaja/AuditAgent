"""Loads mock company policy documents (Markdown) from disk.

In a real product these would be uploaded per-organization and embedded into
pgvector. For the MVP they are bundled Markdown files, mapped to control
categories so the gap analyzer can pick the relevant policy.
"""
from __future__ import annotations

from pathlib import Path

_POLICY_DIR = Path(__file__).parent / "policies"

# Map a control category to its governing policy file.
_CATEGORY_TO_POLICY = {
    "Access Control": "access_control_policy.md",
    "Encryption": "encryption_policy.md",
    "Monitoring": "logging_monitoring_policy.md",
    "Change Management": "logging_monitoring_policy.md",
}


def get_policy_for_category(category: str) -> str:
    """Return the Markdown policy text governing a control category."""
    filename = _CATEGORY_TO_POLICY.get(category)
    if not filename:
        return ""
    path = _POLICY_DIR / filename
    return path.read_text(encoding="utf-8") if path.exists() else ""


def list_policies() -> dict[str, str]:
    """Return {filename: text} for every bundled policy document."""
    return {p.name: p.read_text(encoding="utf-8") for p in _POLICY_DIR.glob("*.md")}
