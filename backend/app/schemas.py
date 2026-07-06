"""Pydantic request/response models shared across routers and agents."""
from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

EvidenceResult = Literal["pass", "fail", "warning", "info"]
ControlStatus = Literal["not_assessed", "compliant", "non_compliant", "in_progress"]
EvidenceSource = Literal["aws", "github", "manual", "policy_doc"]


# ---- Agent I/O ------------------------------------------------------------
class CollectedEvidence(BaseModel):
    """Output of Agent A (evidence collector)."""

    control_id: str
    control_code: str
    source: EvidenceSource
    raw_evidence: dict[str, Any]


class Evaluation(BaseModel):
    """Output of Agent B (control evaluator)."""

    result: EvidenceResult
    status: ControlStatus
    summary: str
    # Which engine produced this — 'llm' or 'heuristic'. Useful for transparency.
    engine: str = "llm"


# ---- API requests ---------------------------------------------------------
class ScanRequest(BaseModel):
    organization_id: str
    # Optional: restrict to one framework ('soc2' | 'hipaa'). None = all.
    framework_key: Optional[str] = None


class GapAnalysisRequest(BaseModel):
    organization_id: str
    framework_key: str = Field(..., description="'soc2' or 'hipaa'")


class TicketCreateRequest(BaseModel):
    organization_id: str
    control_id: str
    title: str
    description: str
    severity: Literal["low", "medium", "high", "critical"] = "medium"
    suggested_fix: Optional[str] = None
    provider: Literal["jira", "linear"] = "linear"


# ---- API responses --------------------------------------------------------
class ControlScanResult(BaseModel):
    control_id: str
    control_code: str
    control_title: str
    source: EvidenceSource
    result: EvidenceResult
    status: ControlStatus
    summary: str
    engine: str
    ticket_id: Optional[str] = None


class ScanResponse(BaseModel):
    organization_id: str
    frameworks_scanned: list[str]
    controls_evaluated: int
    passed: int
    failed: int
    results: list[ControlScanResult]


class FrameworkScore(BaseModel):
    framework_key: str
    framework_name: str
    total_controls: int
    assessed: int
    compliant: int
    non_compliant: int
    score: int  # 0-100, percent of assessed controls that are compliant


class ComplianceOverview(BaseModel):
    organization_id: str
    overall_score: int
    frameworks: list[FrameworkScore]
