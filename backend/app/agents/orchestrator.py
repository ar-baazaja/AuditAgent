"""Multi-agent orchestrator.

Coordinates the agents for a compliance scan:
  1. Agent A (EvidenceCollector) pulls infra config for each control.
  2. Agent B (ControlEvaluator) judges pass/fail via LLM (or heuristic).
  3. Results are persisted to `evidence_logs`.
  4. For any failed control, Phase 5 auto-creates a remediation ticket.

This is the seam where a graph framework (LangGraph) would slot in later; for
the MVP a straightforward sequential loop per control is clearer and cheaper.
"""
from __future__ import annotations

from app.agents.control_evaluator import ControlEvaluatorAgent
from app.agents.evidence_collector import EvidenceCollectorAgent
from app.schemas import ControlScanResult, ScanResponse
from app.services import remediation, repository


class ComplianceOrchestrator:
    def __init__(self) -> None:
        self.collector = EvidenceCollectorAgent()
        self.evaluator = ControlEvaluatorAgent()

    def run_scan(self, organization_id: str, framework_key: str | None = None) -> ScanResponse:
        frameworks = repository.get_frameworks(framework_key)
        if not frameworks:
            raise ValueError(f"No framework found for key={framework_key!r}")

        results: list[ControlScanResult] = []
        scanned_keys: list[str] = []
        passed = failed = 0

        for framework in frameworks:
            scanned_keys.append(framework["key"])
            for control in repository.get_controls_for_framework(framework["id"]):
                # 1 + 2: collect then evaluate.
                evidence = self.collector.collect(organization_id, control)
                verdict = self.evaluator.evaluate(control, evidence)

                # 3: persist evidence.
                repository.insert_evidence(
                    {
                        "organization_id": organization_id,
                        "control_id": control["id"],
                        "source": evidence.source,
                        "result": verdict.result,
                        "status": verdict.status,
                        "summary": verdict.summary,
                        "raw_evidence": evidence.raw_evidence,
                        "collected_by": f"agent:{self.collector.name}",
                    }
                )

                # 4: auto-remediation ticket on failure.
                ticket_id = None
                if verdict.status == "non_compliant":
                    failed += 1
                    ticket = remediation.create_ticket(
                        organization_id, control, verdict.summary
                    )
                    ticket_id = ticket.get("id")
                else:
                    passed += 1

                results.append(
                    ControlScanResult(
                        control_id=control["id"],
                        control_code=control["code"],
                        control_title=control["title"],
                        source=evidence.source,
                        result=verdict.result,
                        status=verdict.status,
                        summary=verdict.summary,
                        engine=verdict.engine,
                        ticket_id=ticket_id,
                    )
                )

        return ScanResponse(
            organization_id=organization_id,
            frameworks_scanned=scanned_keys,
            controls_evaluated=len(results),
            passed=passed,
            failed=failed,
            results=results,
        )
