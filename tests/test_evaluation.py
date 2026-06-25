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
        ],
    )
    harness = RecHarness.from_jsonl_catalog("examples/backpacks/catalog.jsonl")

    result = EvalRunner(
        harness=harness,
        missions_path="examples/backpacks/missions.jsonl",
    ).run_with_agent_outputs(outputs_path)

    assert result.metrics["missions_total"] == 2
    assert result.metrics["product_groundedness_rate"] == 1.0
    assert result.metrics["hard_constraint_satisfaction_rate"] == 1.0
    assert result.metrics["unsupported_claim_rate"] == 0.5


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
