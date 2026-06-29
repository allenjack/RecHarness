"""Local headphones dogfooding runner for the deterministic agent loop."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from examples.integrations.tool_calling_agent_demo import run_agent_loop
except ModuleNotFoundError:
    from tool_calling_agent_demo import run_agent_loop

DEFAULT_TASK_PATH = Path("examples/headphones/dogfooding_tasks.jsonl")


def load_dogfood_tasks(path: str | Path = DEFAULT_TASK_PATH) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    for line_number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        task = json.loads(line)
        _validate_task(task, line_number)
        tasks.append(task)
    return tasks


def run_task(task: dict[str, Any]) -> dict[str, Any]:
    result = run_agent_loop(str(task["user_query"]))
    return {
        "task_id": task["task_id"],
        "user_query": task["user_query"],
        "expected_domain": task["expected_domain"],
        **result,
    }


def summarize_result(result: dict[str, Any]) -> str:
    issues = _issue_summary(result)
    recommended = ", ".join(result.get("recommended_product_ids", [])) or "(none)"
    return "\n".join(
        [
            f"Task: {result['task_id']}",
            f"Query: {result['user_query']}",
            f"Expected domain: {result['expected_domain']}",
            f"Selected domain: {result['selected_domain']}",
            f"Assist status: {result['assist_status']}",
            f"Verify status: {result['verify_status']}",
            f"Recommended: {recommended}",
            f"Issues: {issues}",
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
        description="Run local headphones dogfooding tasks through RecHarness."
    )
    parser.add_argument("--tasks", default=str(DEFAULT_TASK_PATH), help="JSONL task file")
    parser.add_argument("--out", help="Optional JSONL output path")
    args = parser.parse_args()

    results = [run_task(task) for task in load_dogfood_tasks(args.tasks)]
    for index, result in enumerate(results):
        if index:
            print()
        print(summarize_result(result))
    if args.out:
        write_jsonl(results, args.out)


def _validate_task(task: dict[str, Any], line_number: int) -> None:
    required = {"task_id", "user_query", "expected_domain"}
    missing = sorted(required - set(task))
    if missing:
        raise ValueError(f"Task line {line_number} missing fields: {', '.join(missing)}")


def _issue_summary(result: dict[str, Any]) -> str:
    parts: list[str] = []
    warnings = result.get("warnings", [])
    claim_issues = result.get("claim_issues", [])
    violations = result.get("violations", [])
    if warnings:
        parts.append(f"warnings={len(warnings)}")
    if claim_issues:
        parts.append(f"claim_issues={len(claim_issues)}")
    if violations:
        parts.append(f"violations={len(violations)}")
    return ", ".join(parts) if parts else "none"


if __name__ == "__main__":
    main()
