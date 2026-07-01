"""Local repair dogfooding runner for deterministic RecHarness loops."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from recharness import AgentHarnessRouter, AssistRequest, VerifyRequest
from recharness.core.answer_repair import repair_answer_from_verification

try:
    from examples.integrations.tool_calling_agent_demo import (
        choose_domain,
        draft_answer_from_assist_response,
    )
except ModuleNotFoundError:
    from tool_calling_agent_demo import choose_domain, draft_answer_from_assist_response


CATALOG_CONFIG_PATH = "examples/mcp/catalogs.json"
DEFAULT_TASK_PATHS = [
    Path("examples/headphones/dogfooding_tasks.jsonl"),
    Path("examples/headphones/edge_cases.jsonl"),
    Path("examples/backpacks/dogfooding_tasks.jsonl"),
]


def load_repair_tasks(paths: list[str | Path] | None = None) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    for path in paths or DEFAULT_TASK_PATHS:
        for line_number, line in enumerate(
            Path(path).read_text(encoding="utf-8").splitlines(),
            1,
        ):
            if not line.strip():
                continue
            task = _normalize_task(json.loads(line))
            _validate_task(task, path, line_number)
            tasks.append(task)
    return tasks


def run_task(task: dict[str, Any]) -> dict[str, Any]:
    router = AgentHarnessRouter.from_config_file(CATALOG_CONFIG_PATH)
    catalogs = router.list_catalogs()
    query = str(task["user_query"])
    expected_domain = str(task["expected_domain"])
    selected_domain = expected_domain or choose_domain(catalogs, query)

    assist = router.assist(
        AssistRequest(user_query=query, domain=selected_domain, top_k=3)
    )
    draft = str(task.get("agent_answer") or _draft_from_assist(assist))
    verify = router.verify(
        VerifyRequest(
            user_query=query,
            domain=selected_domain,
            agent_answer=draft,
        )
    )
    repair = repair_answer_from_verification(draft, verify, assist_response=assist)

    bundle = assist.bundle
    report = verify.report
    warnings = list(assist.warnings) + list(verify.warnings)
    return {
        "task_id": task["task_id"],
        "query": query,
        "expected_domain": expected_domain,
        "selected_domain": selected_domain,
        "assist_status": assist.status,
        "verify_status": verify.status,
        "repair_status": repair.status,
        "recommended_product_ids": _recommended_product_ids(bundle),
        "recommended_titles": _recommended_titles(bundle),
        "claim_issue_count": len(report.claim_issues) if report else 0,
        "violation_count": len(report.violations) if report else 0,
        "warning_count": len(warnings),
        "final_answer": repair.repaired_answer,
        "repair_changes": repair.changes,
        "repair_warnings": repair.warnings,
    }


def summarize_result(result: dict[str, Any]) -> str:
    recommended_ids = ", ".join(result.get("recommended_product_ids", [])) or "(none)"
    recommended_titles = ", ".join(result.get("recommended_titles", [])) or "(none)"
    changes = "; ".join(result.get("repair_changes", [])) or "none"
    warnings = "; ".join(result.get("repair_warnings", [])) or "none"
    return "\n".join(
        [
            f"Task: {result['task_id']}",
            f"Query: {result['query']}",
            f"Expected domain: {result['expected_domain']}",
            f"Selected domain: {result['selected_domain']}",
            f"Assist status: {result['assist_status']}",
            f"Verify status: {result['verify_status']}",
            f"Repair status: {result['repair_status']}",
            f"Recommended: {recommended_ids}",
            f"Recommended titles: {recommended_titles}",
            (
                "Issue counts: "
                f"warnings={result.get('warning_count', 0)}, "
                f"claim_issues={result.get('claim_issue_count', 0)}, "
                f"violations={result.get('violation_count', 0)}"
            ),
            f"Repair changes: {changes}",
            f"Repair warnings: {warnings}",
            "Final answer:",
            str(result["final_answer"]),
        ]
    )


def write_jsonl(results: list[dict[str, Any]], path: str | Path) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for result in results:
            handle.write(json.dumps(result, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run local repair dogfooding tasks through RecHarness."
    )
    parser.add_argument(
        "--tasks",
        action="append",
        help="JSONL task file. Repeat to include multiple files.",
    )
    parser.add_argument("--out", help="Optional JSONL output path")
    args = parser.parse_args()

    results = [run_task(task) for task in load_repair_tasks(args.tasks)]
    for index, result in enumerate(results):
        if index:
            print()
        print(summarize_result(result))
    if args.out:
        write_jsonl(results, args.out)


def _normalize_task(task: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(task)
    normalized["task_id"] = normalized.get("task_id") or normalized.get("case_id")
    normalized["expected_domain"] = normalized.get("expected_domain") or normalized.get("domain")
    return normalized


def _validate_task(task: dict[str, Any], path: str | Path, line_number: int) -> None:
    required = {"task_id", "user_query", "expected_domain"}
    missing = sorted(required - set(task))
    if missing:
        raise ValueError(
            f"Task {path}:{line_number} missing fields: {', '.join(missing)}"
        )


def _draft_from_assist(assist) -> str:
    return draft_answer_from_assist_response(assist.model_dump(mode="json"))


def _recommended_product_ids(bundle) -> list[str]:
    if bundle is None:
        return []
    return [candidate.product.product_id for candidate in bundle.recommended]


def _recommended_titles(bundle) -> list[str]:
    if bundle is None:
        return []
    return [candidate.product.title for candidate in bundle.recommended]


if __name__ == "__main__":
    main()
