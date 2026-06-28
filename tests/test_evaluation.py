import json

from recharness import EvalRunner, RecHarness


def write_jsonl(path, rows):
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def test_eval_runner_scores_agent_outputs_against_missions(tmp_path):
    outputs_path = tmp_path / "agent_outputs.jsonl"
    write_jsonl(
        outputs_path,
        [
            {
                "mission_id": "backpack_001",
                "agent_name": "test_agent",
                "answer": (
                    "I recommend UrbanLite Commuter Backpack 22L. It costs 899 RMB "
                    "and fits a 14-inch laptop."
                ),
            },
            {
                "mission_id": "backpack_002",
                "agent_name": "test_agent",
                "answer": (
                    "I recommend NorthPeak Office Pack 28L. It costs 1299 RMB "
                    "and is fully waterproof."
                ),
            },
            {
                "mission_id": "backpack_003",
                "agent_name": "test_agent",
                "answer": "I recommend UrbanLite Commuter Backpack 22L. It costs 699 RMB.",
            },
        ],
    )
    harness = RecHarness.from_jsonl_catalog("examples/backpacks/catalog.jsonl")

    result = EvalRunner(
        harness=harness,
        missions_path="examples/backpacks/missions.jsonl",
    ).run_with_agent_outputs(outputs_path)

    assert result.metrics["missions_total"] == 3
    assert result.metrics["product_groundedness_rate"] == 1.0
    assert result.metrics["hallucinated_product_rate"] == 0.0
    assert result.metrics["hard_constraint_satisfaction_rate"] == 1.0
    assert result.metrics["hard_violation_rate"] == 0.0
    assert result.metrics["claim_accuracy_rate"] == 1 / 3
    assert result.metrics["claim_issue_rate"] == 2 / 3
    assert result.metrics["unsupported_claim_rate"] == 0.0
    assert result.metrics["overstated_claim_rate"] == 1 / 3
    assert result.metrics["incorrect_claim_rate"] == 1 / 3
    assert result.metrics["verification_pass_rate"] == 1 / 3
    assert result.metrics["avg_violations_per_answer"] == 0.0
    assert result.metrics["avg_claim_issues_per_answer"] == 2 / 3
    assert result.records[0].resolved_product_ids == ["bag_001"]
    assert result.records[0].unresolved_mentions == []
    assert result.records[0].hard_violations == 0
    assert result.records[1].claim_issues == 1
    assert "overstated_claim" in result.records[1].failure_labels
    assert "incorrect_claim" in result.records[2].failure_labels


def test_cli_eval_writes_metrics_leaderboard_and_traces(tmp_path):
    outputs_path = tmp_path / "agent_outputs.jsonl"
    out_dir = tmp_path / "run"
    write_jsonl(
        outputs_path,
        [
            {
                "mission_id": "backpack_001",
                "agent_name": "test_agent",
                "answer": (
                    "I recommend UrbanLite Commuter Backpack 22L. It costs 899 RMB "
                    "and fits a 14-inch laptop."
                ),
            }
        ],
    )

    from recharness.cli import main

    exit_code = main(
        [
            "eval",
            "--catalog",
            "examples/backpacks/catalog.jsonl",
            "--missions",
            "examples/backpacks/missions.jsonl",
            "--agent-outputs",
            str(outputs_path),
            "--out",
            str(out_dir),
        ]
    )

    assert exit_code == 0
    assert (out_dir / "metrics.json").exists()
    assert (out_dir / "leaderboard.csv").exists()
    assert (out_dir / "traces.jsonl").exists()
    trace_text = (out_dir / "traces.jsonl").read_text(encoding="utf-8")
    assert "claim_issues" in trace_text
    assert "resolved_product_ids" in trace_text
    assert (out_dir / "per_mission_results.jsonl").exists()


def test_eval_runner_run_assist_scores_bundles():
    harness = RecHarness.from_jsonl_catalog("examples/backpacks/catalog.jsonl")

    result = EvalRunner(
        harness=harness,
        missions_path="examples/backpacks/missions.jsonl",
    ).run_assist(top_k=3)

    assert result.metrics["missions_total"] == 50
    assert result.metrics["recommendation_count_avg"] > 0
    assert result.metrics["hard_constraint_satisfaction_rate"] == 1.0
    assert result.metrics["gold_recall_at_k"] >= 0
    assert result.metrics["avg_final_score"] > 0
    assert result.metrics["avg_rejected_candidates"] > 0
    assert result.records[0].agent_name == "recharness_assist"
    assert result.records[0].resolved_product_ids


def test_eval_result_writes_assist_outputs(tmp_path):
    harness = RecHarness.from_jsonl_catalog("examples/backpacks/catalog.jsonl")
    result = EvalRunner(
        harness=harness,
        missions_path="examples/backpacks/missions.jsonl",
    ).run_assist(top_k=2)
    out_dir = tmp_path / "assist_eval"

    result.write(out_dir)

    assert (out_dir / "metrics.json").exists()
    assert (out_dir / "per_mission_results.jsonl").exists()
    assert (out_dir / "leaderboard.csv").exists()
    assert (out_dir / "traces.jsonl").exists()
