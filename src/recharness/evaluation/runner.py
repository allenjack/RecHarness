"""Batch evaluation runner for local RecHarness missions."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Literal

from pydantic import Field

from recharness.core import RecHarness
from recharness.evaluation.failures import (
    failure_labels_from_bundle,
    failure_labels_from_report,
)
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
    claim_issue_messages: int = 0
    unsupported_claims: int
    overstated_claims: int = 0
    incorrect_claims: int = 0
    violations: int
    failure_labels: list[str] = Field(default_factory=list)
    recommendation_count: int = 0
    rejected_candidates: int = 0
    avg_final_score: float = 0.0
    gold_hit: bool = False
    report: VerificationReport


class EvalResult(RecHarnessModel):
    mode: Literal["answers", "assist"] = "answers"
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
        _write_per_mission_results(output_dir / "per_mission_results.jsonl", self)
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
                    claim_issue_messages=len(report.claim_issue_messages),
                    unsupported_claims=len(report.unsupported_claims),
                    overstated_claims=len(report.overstated_claims),
                    incorrect_claims=len(report.incorrect_claims),
                    violations=len(report.violations),
                    failure_labels=failure_labels_from_report(report),
                    report=report,
                )
            )

        return EvalResult(mode="answers", metrics=_metrics(records), records=records)

    def run_assist(self, top_k: int = 5) -> EvalResult:
        records: list[EvalRecord] = []
        for mission in self.missions:
            bundle = self.harness.assist(mission.user_query, top_k=top_k)
            hard_violations = sum(
                1
                for candidate in bundle.recommended
                for violation in candidate.violations
                if violation.severity == "hard"
            )
            recommended_ids = [
                candidate.product.product_id for candidate in bundle.recommended
            ]
            final_scores = [
                candidate.final_score
                for candidate in bundle.recommended
                if candidate.final_score is not None
            ]
            avg_final_score = _average(final_scores) if final_scores else 0.0
            gold_hit = bool(set(recommended_ids) & set(mission.gold_product_ids))
            hard_constraints_satisfied = hard_violations == 0
            records.append(
                EvalRecord(
                    mission_id=mission.mission_id,
                    agent_name="recharness_assist",
                    status="pass" if hard_constraints_satisfied else "fail",
                    product_grounded=bool(recommended_ids),
                    hard_constraints_satisfied=hard_constraints_satisfied,
                    resolved_product_ids=recommended_ids,
                    unresolved_mentions=[],
                    hard_violations=hard_violations,
                    claim_issues=0,
                    claim_issue_messages=0,
                    unsupported_claims=0,
                    overstated_claims=0,
                    incorrect_claims=0,
                    violations=sum(
                        len(candidate.violations) for candidate in bundle.recommended
                    ),
                    failure_labels=failure_labels_from_bundle(bundle),
                    recommendation_count=len(recommended_ids),
                    rejected_candidates=len(bundle.rejected),
                    avg_final_score=avg_final_score,
                    gold_hit=gold_hit,
                    report=bundle.constraint_report,
                )
            )

        return EvalResult(mode="assist", metrics=_assist_metrics(records), records=records)


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
            "claim_issue_rate": 0.0,
            "unsupported_claim_rate": 0.0,
            "overstated_claim_rate": 0.0,
            "incorrect_claim_rate": 0.0,
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
        "claim_issue_rate": _rate(record.claim_issues > 0 for record in records),
        "unsupported_claim_rate": _rate(record.unsupported_claims > 0 for record in records),
        "overstated_claim_rate": _rate(record.overstated_claims > 0 for record in records),
        "incorrect_claim_rate": _rate(record.incorrect_claims > 0 for record in records),
        "verification_pass_rate": _rate(record.status == "pass" for record in records),
        "avg_violations_per_answer": _average(record.violations for record in records),
        "avg_claim_issues_per_answer": _average(record.claim_issues for record in records),
        **_failure_label_rates(records),
    }


def _assist_metrics(records: list[EvalRecord]) -> dict[str, float | int]:
    total = len(records)
    if total == 0:
        return {
            "missions_total": 0,
            "recommendation_count_avg": 0.0,
            "hard_constraint_satisfaction_rate": 0.0,
            "hard_violation_rate": 0.0,
            "gold_recall_at_k": 0.0,
            "avg_final_score": 0.0,
            "avg_rejected_candidates": 0.0,
        }
    return {
        "missions_total": total,
        "recommendation_count_avg": _average(
            record.recommendation_count for record in records
        ),
        "hard_constraint_satisfaction_rate": _rate(
            record.hard_constraints_satisfied for record in records
        ),
        "hard_violation_rate": _rate(record.hard_violations > 0 for record in records),
        "gold_recall_at_k": _rate(record.gold_hit for record in records),
        "avg_final_score": _average(record.avg_final_score for record in records),
        "avg_rejected_candidates": _average(
            record.rejected_candidates for record in records
        ),
        **_failure_label_rates(records),
    }


def _failure_label_rates(records: list[EvalRecord]) -> dict[str, float]:
    labels = sorted({label for record in records for label in record.failure_labels})
    return {
        f"failure_rate.{label}": _rate(
            label in record.failure_labels for record in records
        )
        for label in labels
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
        metric_keys = sorted(result.metrics)
        writer = csv.DictWriter(
            handle,
            fieldnames=["agent_name", *metric_keys],
        )
        writer.writeheader()
        for agent_name, records in sorted(by_agent.items()):
            metrics = _assist_metrics(records) if result.mode == "assist" else _metrics(records)
            writer.writerow({"agent_name": agent_name, **metrics})


def _write_per_mission_results(path: Path, result: EvalResult) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in result.records:
            payload: dict[str, Any] = record.model_dump(mode="json", exclude={"report"})
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _write_traces(path: Path, result: EvalResult) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in result.records:
            payload: dict[str, Any] = record.model_dump(mode="json")
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
