"""Agent B — Control Evaluator.

Responsibility: judge whether collected evidence satisfies a compliance control.

Primary path: an LLM (Gemini Flash) reads the control text + evidence JSON and
returns a structured verdict. Fallback path: a deterministic heuristic that
inspects well-known keys — so evaluation still works with no API key, and the
LLM verdict can be sanity-checked.
"""
from __future__ import annotations

import json
import re
from typing import Any

from app.agents.llm import invoke_json
from app.schemas import CollectedEvidence, Evaluation

_PROMPT = """You are a SOC 2 / HIPAA compliance auditor. Decide whether the \
collected infrastructure evidence satisfies the control.

CONTROL
  Framework code: {code}
  Title: {title}
  Description: {description}

COLLECTED EVIDENCE (JSON)
{evidence}

Respond with ONLY a JSON object, no prose, in exactly this shape:
{{"result": "pass" | "fail" | "warning",
  "status": "compliant" | "non_compliant" | "in_progress",
  "summary": "<one sentence citing the specific evidence that drove the verdict>"}}

Rules:
- "pass"/"compliant" only if the evidence clearly meets the control.
- Any disabled control, weak setting, or non-empty violation list => "fail"/"non_compliant".
- Keep the summary specific and under 200 characters."""


class ControlEvaluatorAgent:
    name = "control-evaluator"

    def evaluate(self, control: dict, evidence: CollectedEvidence) -> Evaluation:
        verdict = self._evaluate_with_llm(control, evidence)
        if verdict is not None:
            return verdict
        return self._evaluate_heuristic(evidence)

    # ---- LLM path ---------------------------------------------------------
    def _evaluate_with_llm(self, control: dict, evidence: CollectedEvidence):
        prompt = _PROMPT.format(
            code=control["code"],
            title=control["title"],
            description=control.get("description") or "",
            evidence=json.dumps(evidence.raw_evidence, indent=2),
        )
        raw = invoke_json(prompt)
        if not raw:
            return None
        data = _extract_json(raw)
        if not data:
            return None
        try:
            return Evaluation(
                result=data["result"],
                status=data["status"],
                summary=str(data["summary"])[:300],
                engine="llm",
            )
        except (KeyError, ValueError):
            return None

    # ---- Heuristic fallback ----------------------------------------------
    def _evaluate_heuristic(self, evidence: CollectedEvidence) -> Evaluation:
        """Deterministic rule engine over known evidence shapes."""
        raw = evidence.raw_evidence
        problems = _detect_problems(raw)
        if problems:
            return Evaluation(
                result="fail",
                status="non_compliant",
                summary="Non-compliant: " + "; ".join(problems[:3]),
                engine="heuristic",
            )
        return Evaluation(
            result="pass",
            status="compliant",
            summary="All checked settings meet the control requirements.",
            engine="heuristic",
        )


def _detect_problems(raw: dict[str, Any]) -> list[str]:
    """Inspect common evidence keys and return human-readable violations."""
    problems: list[str] = []

    # Any boolean flag that is False and reads like a security control.
    negative_flags = {
        "iam_mfa_enabled": "MFA is disabled",
        "root_account_mfa": "root account lacks MFA",
        "elb_tls_enabled": "TLS not enforced on load balancers",
        "s3_default_encryption": "S3 default encryption off",
        "rds_storage_encrypted": "RDS storage not encrypted",
        "kms_key_rotation": "KMS key rotation disabled",
        "cloudtrail_enabled": "CloudTrail disabled",
        "multi_region_trail": "trail is not multi-region",
        "branch_protection_enabled": "branch protection disabled",
        "require_status_checks": "status checks not required",
    }
    for key, msg in negative_flags.items():
        if raw.get(key) is False:
            problems.append(msg)

    # Non-empty "violation list" keys.
    for key in ("users_without_mfa", "insecure_listeners", "unencrypted_buckets", "unprotected_repos"):
        items = raw.get(key)
        if isinstance(items, list) and items:
            problems.append(f"{key.replace('_', ' ')}: {', '.join(map(str, items))}")

    # Threshold checks.
    if raw.get("min_tls_version") in {"TLS1.0", "TLS1.1"}:
        problems.append(f"weak TLS version {raw['min_tls_version']}")
    if isinstance(raw.get("required_pull_request_reviews"), int) and raw["required_pull_request_reviews"] < 1:
        problems.append("no required PR reviews")
    if isinstance(raw.get("log_retention_days"), int) and raw["log_retention_days"] < 90:
        problems.append(f"log retention only {raw['log_retention_days']} days")
    policy = raw.get("password_policy")
    if isinstance(policy, dict) and policy.get("minimum_length", 99) < 12:
        problems.append(f"password min length {policy['minimum_length']}")
    if raw.get("misconfigured") is True:
        problems.append("resource is misconfigured")

    return problems


def _extract_json(text: str) -> dict | None:
    """Pull the first JSON object out of an LLM response (handles code fences)."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
