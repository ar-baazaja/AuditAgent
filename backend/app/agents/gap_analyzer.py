"""Phase 4 — Gap Analysis Agent.

Reads a company policy document (Markdown) and compares its stated requirements
against the actual (mocked) infrastructure settings for a control, producing a
plain-language list of gaps. LLM-powered with a heuristic fallback.
"""
from __future__ import annotations

import json
import re

from app.agents.llm import invoke_json
from app.mocks.policy_store import get_policy_for_category
from app.schemas import CollectedEvidence

_PROMPT = """You are a compliance analyst performing a gap analysis.

COMPANY POLICY (Markdown)
{policy}

ACTUAL INFRASTRUCTURE SETTINGS (JSON) for control {code} - {title}
{evidence}

List every gap where the actual settings fail to meet a policy requirement.
Respond with ONLY a JSON array (no prose). Each item:
{{"requirement": "<the policy requirement>",
  "actual": "<what the settings show>",
  "gap": "<why it fails>",
  "severity": "low" | "medium" | "high" | "critical"}}
Return [] if there are no gaps."""


class GapAnalyzerAgent:
    name = "gap-analyzer"

    def analyze(self, control: dict, evidence: CollectedEvidence) -> list[dict]:
        policy = get_policy_for_category(control.get("category") or "")
        if not policy:
            return []

        raw = invoke_json(
            _PROMPT.format(
                policy=policy,
                code=control["code"],
                title=control["title"],
                evidence=json.dumps(evidence.raw_evidence, indent=2),
            )
        )
        gaps = _extract_json_array(raw) if raw else None
        if gaps is not None:
            return gaps
        return self._heuristic_gaps(control, evidence)

    def _heuristic_gaps(self, control: dict, evidence: CollectedEvidence) -> list[dict]:
        """Fallback: reuse the evaluator's problem detector as gaps."""
        from app.agents.control_evaluator import _detect_problems

        problems = _detect_problems(evidence.raw_evidence)
        return [
            {
                "requirement": f"{control['category']} policy compliance",
                "actual": problem,
                "gap": problem,
                "severity": "high",
            }
            for problem in problems
        ]


def _extract_json_array(text: str) -> list | None:
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if not match:
        return None
    try:
        parsed = json.loads(match.group(0))
        return parsed if isinstance(parsed, list) else None
    except json.JSONDecodeError:
        return None
