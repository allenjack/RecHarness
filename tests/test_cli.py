import json

from recharness.cli import main


def test_cli_assist_prints_ranked_recommendations(capsys):
    exit_code = main(
        [
            "assist",
            "--catalog",
            "examples/backpacks/catalog.jsonl",
            "--query",
            "Find a commuting backpack under 1500 RMB that fits a 14-inch laptop "
            "and is not too business",
            "--top-k",
            "2",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Top recommendations" in captured.out
    assert "UrbanLite Commuter Backpack 22L" in captured.out


def test_cli_verify_reports_failure_for_bad_recommendation(capsys):
    exit_code = main(
        [
            "verify",
            "--catalog",
            "examples/backpacks/catalog.jsonl",
            "--query",
            "Find a commuting backpack under 1500 RMB that fits a 14-inch laptop",
            "--answer",
            "I recommend RainGuard Metro Pack 24L. It costs 1599 RMB.",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "FAIL" in captured.out
    assert "price.amount" in captured.out


def test_cli_verify_prints_structured_claim_issues(capsys):
    exit_code = main(
        [
            "verify",
            "--catalog",
            "examples/backpacks/catalog.jsonl",
            "--query",
            "Find a commuting backpack under 1500 RMB",
            "--answer",
            "I recommend NorthPeak Office Pack 28L. It costs 1299 RMB "
            "and is fully waterproof.",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Claim issues:" in captured.out
    assert "water_resistance" in captured.out
    assert "attributes.water_resistance" in captured.out


def test_cli_assist_json_outputs_machine_readable_bundle(capsys):
    exit_code = main(
        [
            "assist",
            "--catalog",
            "examples/backpacks/catalog.jsonl",
            "--query",
            "Find a commuting backpack under 1500 RMB",
            "--top-k",
            "2",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert "recommended" in payload
    assert "rejected" in payload
    assert payload["constraint_report"]["status"] in {"pass", "warning", "fail"}


def test_cli_verify_json_outputs_machine_readable_report(capsys):
    exit_code = main(
        [
            "verify",
            "--catalog",
            "examples/backpacks/catalog.jsonl",
            "--query",
            "Find a commuting backpack under 1500 RMB",
            "--answer",
            "I recommend NorthPeak Office Pack 28L. It costs 1299 RMB and is fully waterproof.",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 1
    assert payload["status"] == "warning"
    assert payload["claim_issues"][0]["claim_type"] == "water_resistance"


def test_cli_assist_and_verify_trace_path_create_trace_files(tmp_path, capsys):
    assist_trace = tmp_path / "assist.jsonl"
    verify_trace = tmp_path / "verify.jsonl"

    assist_code = main(
        [
            "assist",
            "--catalog",
            "examples/backpacks/catalog.jsonl",
            "--query",
            "Find a commuting backpack under 1500 RMB",
            "--trace-path",
            str(assist_trace),
        ]
    )
    verify_code = main(
        [
            "verify",
            "--catalog",
            "examples/backpacks/catalog.jsonl",
            "--query",
            "Find a commuting backpack under 1500 RMB",
            "--answer",
            "I recommend UrbanLite Commuter Backpack 22L. It costs 899 RMB.",
            "--trace-path",
            str(verify_trace),
        ]
    )

    capsys.readouterr()

    assert assist_code == 0
    assert verify_code == 0
    assert assist_trace.exists()
    assert verify_trace.exists()
    assert "verify_agent_answer" in verify_trace.read_text(encoding="utf-8")


def test_cli_verify_no_fail_on_warning(capsys):
    warning_code = main(
        [
            "verify",
            "--catalog",
            "examples/backpacks/catalog.jsonl",
            "--query",
            "Find a commuting backpack under 1500 RMB",
            "--answer",
            "I recommend NorthPeak Office Pack 28L. It costs 1299 RMB and is fully waterproof.",
            "--no-fail-on-warning",
        ]
    )
    fail_code = main(
        [
            "verify",
            "--catalog",
            "examples/backpacks/catalog.jsonl",
            "--query",
            "Find a commuting backpack under 1500 RMB",
            "--answer",
            "I recommend RainGuard Metro Pack 24L. It costs 1599 RMB.",
            "--no-fail-on-warning",
        ]
    )

    capsys.readouterr()

    assert warning_code == 0
    assert fail_code == 1
