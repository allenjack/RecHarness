"""Batch evaluation runner for local RecHarness missions."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from pydantic import Field

from recharness.core import RecHarness
from recharness.schema import RecHarnessModel, VerificationReport


class EvalMission(RecHarnessModel):
    mission_id: str
    user_query: str
    gold_product_ids: list[str] = Field(default_factory=list)


class AgentOutput(RecHarnessModel):
    mission_id: str
    agent_name: str = "agent"
    answer: str


class EvalRecord(RecHarnessModel):
    mission_id: str
    agent_name: str
    status: str
    product_grounded: bool
    hard_constraints_satisfied: bool
    resolved_product_ids: list[str] = Field(default_factory=list)
    unresolved_mentions: list[str] = Field(default_factory=list)
    hard_violations: int
    claim_issues: int
    unsupported_claims: int
    violations: int
    report: VerificationReport


class EvalResult(RecHarnessModel):
    metrics: dict[str, float | int]
    records: list[EvalRecord]

    def write(self, out_dir: str | Path) -> None:
        output_dir = Path(out_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "metrics.json").write_text(
            json.dumps(self.metrics, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        _write_leaderboard(output_dir / "leaderboard.csv", self)
        _write_traces(output_dir / "traces.jsonl", self)


class EvalRunner:
    """Evaluate saved agent answers against recommendation missions."""

    def __init__(self, harness: RecHarness, missions_path: str | Path) -> None:
        self.harness = harness
        self.missions = _load_jsonl_models(missions_path, EvalMission)

    def run_with_agent_outputs(self, outputs_path: str | Path) -> EvalResult:
        outputs = _load_jsonl_models(outputs_path, AgentOutput)
        missions_by_id = {mission.mission_id: mission for mission in self.missions}
        records: list[EvalRecord] = []

        for output in outputs:
            mission = missions_by_id[output.mission_id]
            report = self.harness.verify_agent_recommendation(
                user_query=mission.user_query,
                agent_answer=output.answer,
            )
            hard_violations = sum(
                1 for violation in report.violations if violation.severity == "hard"
            )
            product_grounded = report.product_grounded
            hard_constraints_satisfied = hard_violations == 0
            records.append(
                EvalRecord(
                    mission_id=mission.mission_id,
                    agent_name=output.agent_name,
                    status=report.status,
                    product_grounded=product_grounded,
                    hard_constraints_satisfied=hard_constraints_satisfied,
                    resolved_product_ids=[
                        product.product_id for product in report.resolved_products
                    ],
                    unresolved_mentions=report.unresolved_mentions,
                    hard_violations=hard_violations,
                    claim_issues=len(report.claim_issues),
                    unsupported_claims=len(report.unsupported_claims),
                    violations=len(report.violations),
                    report=report,
                )
            )

        return EvalResult(metrics=_metrics(records), records=records)


def _load_jsonl_models(path: str | Path, model):
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(model.model_validate(json.loads(line)))
    return rows


def _metrics(records: list[EvalRecord]) -> dict[str, float | int]:
    total = len(records)
    if total == 0:
        return {
            "missions_total": 0,
            "product_groundedness_rate": 0.0,
            "hallucinated_product_rate": 0.0,
            "hard_constraint_satisfaction_rate": 0.0,
            "hard_violation_rate": 0.0,
            "claim_accuracy_rate": 0.0,
            "unsupported_claim_rate": 0.0,
            "overstated_claim_rate": 0.0,
            "verification_pass_rate": 0.0,
            "avg_violations_per_answer": 0.0,
            "avg_claim_issues_per_answer": 0.0,
        }
    return {
        "missions_total": total,
        "product_groundedness_rate": _rate(record.product_grounded for record in records),
        "hallucinated_product_rate": _rate(
            (not record.product_grounded) or bool(record.unresolved_mentions)
            for record in records
        ),
        "hard_constraint_satisfaction_rate": _rate(
            record.hard_constraints_satisfied for record in records
        ),
        "hard_violation_rate": _rate(record.hard_violations > 0 for record in records),
        "claim_accuracy_rate": _rate(record.claim_issues == 0 for record in records),
        "unsupported_claim_rate": _rate(record.unsupported_claims > 0 for record in records),
        "overstated_claim_rate": _rate(
            any(issue.issue_type == "overstated" for issue in record.report.claim_issues)
            for record in records
        ),
        "verification_pass_rate": _rate(record.status == "pass" for record in records),
        "avg_violations_per_answer": _average(record.violations for record in records),
        "avg_claim_issues_per_answer": _average(record.claim_issues for record in records),
    }


def _rate(values) -> float:
    values = list(values)
    return sum(1 for value in values if value) / len(values)


def _average(values) -> float:
    values = list(values)
    return sum(values) / len(values)


def _write_leaderboard(path: Path, result: EvalResult) -> None:
    by_agent: dict[str, list[EvalRecord]] = {}
    for record in result.records:
        by_agent.setdefault(record.agent_name, []).append(record)

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "agent_name",
                "missions_total",
                "product_groundedness_rate",
                "hallucinated_product_rate",
                "hard_constraint_satisfaction_rate",
                "hard_violation_rate",
                "claim_accuracy_rate",
                "unsupported_claim_rate",
                "overstated_claim_rate",
                "verification_pass_rate",
                "avg_violations_per_answer",
                "avg_claim_issues_per_answer",
            ],
        )
        writer.writeheader()
        for agent_name, records in sorted(by_agent.items()):
            metrics = _metrics(records)
            writer.writerow({"agent_name": agent_name, **metrics})


def _write_traces(path: Path, result: EvalResult) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in result.records:
            payload: dict[str, Any] = record.model_dump(mode="json")
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
