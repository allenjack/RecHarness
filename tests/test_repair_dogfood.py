import json
import subprocess
import sys
from pathlib import Path

from examples.integrations.run_repair_dogfood import (
    DEFAULT_TASK_PATHS,
    load_repair_tasks,
    run_task,
    summarize_result,
    write_jsonl,
)


def test_repair_dogfood_default_task_loading_uses_existing_fixtures():
    tasks = load_repair_tasks(DEFAULT_TASK_PATHS)

    assert tasks
    assert {task["expected_domain"] for task in tasks} == {"backpacks", "headphones"}
    assert all(task["task_id"] for task in tasks)
    assert all(task["user_query"] for task in tasks)


def test_repair_dogfood_runner_returns_one_result_per_task():
    tasks = load_repair_tasks(DEFAULT_TASK_PATHS)

    results = [run_task(task) for task in tasks]

    assert len(results) == len(tasks)
    for result in results:
        assert result["task_id"]
        assert result["query"]
        assert result["expected_domain"] in {"backpacks", "headphones"}
        assert result["selected_domain"] == result["expected_domain"]
        assert result["assist_status"] in {"ok", "warning", "error"}
        assert result["verify_status"] in {"pass", "warning", "fail", "error"}
        assert result["repair_status"] in {"unchanged", "repaired", "qualified", "failed"}
        assert isinstance(result["recommended_product_ids"], list)
        assert isinstance(result["recommended_titles"], list)
        assert isinstance(result["claim_issue_count"], int)
        assert isinstance(result["violation_count"], int)
        assert isinstance(result["warning_count"], int)
        assert result["final_answer"]
        assert isinstance(result["repair_changes"], list)
        assert isinstance(result["repair_warnings"], list)


def test_repair_dogfood_summary_and_jsonl_output(tmp_path: Path):
    task = load_repair_tasks([Path("examples/headphones/edge_cases.jsonl")])[0]
    result = run_task(task)
    out_path = tmp_path / "repair_results.jsonl"

    summary = summarize_result(result)
    write_jsonl([result], out_path)

    assert "Task:" in summary
    assert "Repair status:" in summary
    assert "Final answer:" in summary
    rows = [json.loads(line) for line in out_path.read_text(encoding="utf-8").splitlines()]
    assert rows == [result]


def test_repair_dogfood_runner_executes_as_direct_script(tmp_path: Path):
    out_path = tmp_path / "results.jsonl"

    completed = subprocess.run(
        [
            sys.executable,
            "examples/integrations/run_repair_dogfood.py",
            "--tasks",
            "examples/headphones/edge_cases.jsonl",
            "--out",
            str(out_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Repair status:" in completed.stdout
    assert out_path.exists()


def test_repair_dogfooding_notes_are_developer_focused():
    text = Path("examples/repair_dogfooding_notes.md").read_text(encoding="utf-8")

    assert "How to Run" in text
    assert "Current Observations" in text
    assert "Follow-up Fixes" in text
    assert "This is not a benchmark report." in text
    assert "leaderboard" not in text.lower()
