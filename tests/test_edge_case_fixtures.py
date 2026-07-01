import json
from pathlib import Path

from recharness import AgentHarnessRouter, AssistRequest, VerifyRequest

FIXTURE_PATHS = [
    Path("examples/headphones/edge_cases.jsonl"),
    Path("examples/backpacks/dogfooding_tasks.jsonl"),
]


def _load_rows(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_edge_case_fixture_rows_are_valid_and_existing_domain_scoped():
    for path in FIXTURE_PATHS:
        rows = _load_rows(path)

        assert rows
        for row in rows:
            assert row["case_id"]
            assert row["domain"] in {"backpacks", "headphones"}
            assert row["user_query"]
            assert row["agent_answer"]
            assert row["expected_verify_status"] in {"pass", "warning", "fail"}
            assert isinstance(row["expected_violation_fields"], list)
            assert isinstance(row["expected_claim_types"], list)


def test_edge_case_fixtures_match_current_verification_behavior():
    router = AgentHarnessRouter.from_config_file("examples/mcp/catalogs.json")

    for path in FIXTURE_PATHS:
        for row in _load_rows(path):
            verify = router.verify(
                VerifyRequest(
                    user_query=row["user_query"],
                    domain=row["domain"],
                    agent_answer=row["agent_answer"],
                )
            )

            assert verify.status == row["expected_verify_status"], row["case_id"]
            assert verify.report is not None
            assert {
                violation.constraint.field for violation in verify.report.violations
            } == set(row["expected_violation_fields"])
            assert {issue.claim_type for issue in verify.report.claim_issues} == set(
                row["expected_claim_types"]
            )


def test_headphones_edge_case_fixture_covers_no_safe_assist_candidate():
    router = AgentHarnessRouter.from_config_file("examples/mcp/catalogs.json")
    row = next(
        row
        for row in _load_rows(Path("examples/headphones/edge_cases.jsonl"))
        if row["case_id"] == "hp_edge_no_product_satisfies_budget"
    )

    assist = router.assist(
        AssistRequest(user_query=row["user_query"], domain=row["domain"], top_k=3)
    )

    assert assist.bundle is not None
    assert len(assist.bundle.recommended) == row["expected_assist_recommended_count"]
