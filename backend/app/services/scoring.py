"""Compliance scoring — always computed from evidence, never stored.

A framework's score is the percentage of its controls that are `compliant`,
based on the latest evidence per control. Controls with no evidence yet are
counted as unassessed and excluded from the denominator so early scans aren't
unfairly penalised (but surfaced separately as `assessed` vs `total`).
"""
from __future__ import annotations

from app.schemas import ComplianceOverview, FrameworkScore
from app.services import repository


def compute_overview(organization_id: str) -> ComplianceOverview:
    latest = repository.get_latest_evidence(organization_id)
    status_by_control = {e["control_id"]: e["status"] for e in latest}

    framework_scores: list[FrameworkScore] = []
    weighted_sum = 0
    weight_total = 0

    for framework in repository.get_frameworks():
        controls = repository.get_controls_for_framework(framework["id"])
        total = len(controls)
        compliant = non_compliant = assessed = 0

        for control in controls:
            status = status_by_control.get(control["id"])
            if status in (None, "not_assessed"):
                continue
            assessed += 1
            if status == "compliant":
                compliant += 1
            elif status == "non_compliant":
                non_compliant += 1

        score = round((compliant / assessed) * 100) if assessed else 0
        framework_scores.append(
            FrameworkScore(
                framework_key=framework["key"],
                framework_name=framework["name"],
                total_controls=total,
                assessed=assessed,
                compliant=compliant,
                non_compliant=non_compliant,
                score=score,
            )
        )
        if assessed:
            weighted_sum += compliant
            weight_total += assessed

    overall = round((weighted_sum / weight_total) * 100) if weight_total else 0
    return ComplianceOverview(
        organization_id=organization_id,
        overall_score=overall,
        frameworks=framework_scores,
    )
