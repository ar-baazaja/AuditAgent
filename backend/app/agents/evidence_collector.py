"""Agent A — Evidence Collector.

Responsibility: given a control, pull the relevant configuration from the
appropriate (mocked) infrastructure connector and return it as structured
evidence. This is intentionally deterministic tooling — the "intelligence"
lives in Agent B (the evaluator).
"""
from __future__ import annotations

from app.connectors import get_connector
from app.schemas import CollectedEvidence


class EvidenceCollectorAgent:
    name = "evidence-collector"

    def collect(self, organization_id: str, control: dict) -> CollectedEvidence:
        """Fetch infra config for a single control row (from the DB catalog)."""
        check_type = control.get("check_type") or "aws"
        connector = get_connector(check_type)
        raw = connector.fetch(
            organization_id=organization_id,
            control_code=control["code"],
            category=control.get("category") or "",
        )
        return CollectedEvidence(
            control_id=control["id"],
            control_code=control["code"],
            source=connector.source,  # type: ignore[arg-type]
            raw_evidence=raw,
        )
