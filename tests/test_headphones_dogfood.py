import json
import subprocess
import sys
from pathlib import Path

from examples.integrations.run_headphones_dogfood import (
    DEFAULT_TASK_PATH,
    load_dogfood_tasks,
    run_task,
    summarize_result,
    write_jsonl,
)


def test_headphones_dogfood_tasks_file_is_valid_jsonl():
    tasks = load_dogfood_tasks(DEFAULT_TASK_PATH)

    assert tasks
    for task in tasks:
        assert task["task_id"]
        assert task["user_query"]
        assert task["expected_domain"] == "headphones"


def test_headphones_dogfood_runner_routes_all_tasks_to_expected_domain():
    tasks = load_dogfood_tasks(DEFAULT_TASK_PATH)

    results = [run_task(task) for task in tasks]

    assert all(result["selected_domain"] == result["expected_domain"] for result in results)


def test_headphones_dogfood_runner_returns_grounded_answers():
    tasks = load_dogfood_tasks(DEFAULT_TASK_PATH)

    results = [run_task(task) for task in tasks]

    for result in results:
        assert result["final_answer"]
        assert result["recommended_product_ids"]
        assert result["assist_status"] in {"ok", "warning"}
        assert result["verify_status"] in {"pass", "warning", "fail"}
        assert isinstance(result["warnings"], list)
        assert isinstance(result["claim_issues"], list)
        assert isinstance(result["violations"], list)
        assert result["recommended_titles"]
        assert result["warnings_count"] == len(result["warnings"])
        assert result["claim_issue_count"] == len(result["claim_issues"])
        assert result["violation_count"] == len(result["violations"])


def test_headphones_dogfood_in_stock_task_excludes_out_of_stock_products():
    task = next(
        task
        for task in load_dogfood_tasks(DEFAULT_TASK_PATH)
        if task["task_id"] == "dogfood_hp_009"
    )

    result = run_task(task)

    assert "hp_007" not in result["recommended_product_ids"]


def test_headphones_dogfood_summary_and_jsonl_output(tmp_path: Path):
    task = load_dogfood_tasks(DEFAULT_TASK_PATH)[0]
    result = run_task(task)
    out_path = tmp_path / "results.jsonl"

    summary = summarize_result(result)
    write_jsonl([result], out_path)

    assert "Task: dogfood_hp_001" in summary
    assert "Recommended titles:" in summary
    assert "Issue counts:" in summary
    assert "Final answer:" in summary
    rows = [json.loads(line) for line in out_path.read_text().splitlines()]
    assert rows == [result]


def test_headphones_dogfood_runner_executes_as_direct_script(tmp_path: Path):
    out_path = tmp_path / "results.jsonl"

    completed = subprocess.run(
        [
            sys.executable,
            "examples/integrations/run_headphones_dogfood.py",
            "--out",
            str(out_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Task: dogfood_hp_001" in completed.stdout
    assert out_path.exists()


def test_headphones_dogfooding_notes_are_developer_focused():
    text = Path("examples/headphones/dogfooding_notes.md").read_text(encoding="utf-8")

    assert "How to Run" in text
    assert "Current Observations" in text
    assert "benchmark report" not in text.lower()
