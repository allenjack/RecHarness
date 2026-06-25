from recharness.cli import main


def test_cli_assist_prints_ranked_recommendations(capsys):
    exit_code = main(
        [
            "assist",
            "--catalog",
            "examples/backpacks/catalog.jsonl",
            "--query",
            "Find a commuting backpack under 1500 RMB that fits a 14-inch laptop and is not too business",
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
