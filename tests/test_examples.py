import json
import runpy
from pathlib import Path

from recharness import EvalRunner, JsonlCatalog, RecHarness


def test_open_source_docs_exist_and_use_library_positioning():
    expected_docs = [
        "docs/catalog_schema.md",
        "docs/recommendation_bundle.md",
        "docs/verification.md",
        "docs/evaluation.md",
        "docs/adding_a_new_domain.md",
        "CHANGELOG.md",
        "ROADMAP.md",
    ]
    banned_doc_terms = ["paper-" + "specific", "publication-" + "ready"]

    for doc_path in expected_docs:
        text = Path(doc_path).read_text(encoding="utf-8")
        assert all(term not in text.lower() for term in banned_doc_terms)

    readme = Path("README.md").read_text(encoding="utf-8")
    assert "Run Local Evaluation" in readme
    assert "Run Harness " + "Experiments" not in readme
    assert "paper " + "ablation" not in readme.lower()
    assert "Diagnostic variants help users compare retrieval behavior" in readme


def test_no_paper_specific_artifact_directories_exist():
    for directory in ["reports", "paper", "figures", "latex"]:
        assert not Path(directory).exists()


def test_headphones_example_domain_loads_and_evaluates():
    catalog = JsonlCatalog.load("examples/headphones/catalog.jsonl")
    assert 12 <= len(catalog) <= 20
    assert catalog.validate().is_valid

    harness = RecHarness.from_jsonl_catalog("examples/headphones/catalog.jsonl")
    bundle = harness.assist(
        "Find wireless headphones under 1000 RMB for office calls.",
        top_k=3,
    )
    assert bundle.recommended
    assert all(candidate.product.category == "headphones" for candidate in bundle.recommended)

    result = EvalRunner(
        harness=harness,
        missions_path="examples/headphones/missions.jsonl",
    ).run_assist(top_k=3)
    assert result.metrics["missions_total"] >= 10
    assert result.metrics["recommendation_count_avg"] > 0


def test_headphones_verify_outputs_cover_common_failure_modes():
    harness = RecHarness.from_jsonl_catalog("examples/headphones/catalog.jsonl")
    result = EvalRunner(
        harness=harness,
        missions_path="examples/headphones/missions.jsonl",
    ).run_with_agent_outputs("examples/headphones/agent_outputs.jsonl")

    labels = {label for record in result.records for label in record.failure_labels}
    claim_types = {
        issue.claim_type
        for record in result.records
        for issue in record.report.claim_issues
    }
    assert "product_hallucination" in labels
    assert "hard_constraint_violation" in labels
    assert "incorrect_claim" in labels
    assert "overstated_claim" in labels
    assert {"price", "availability", "noise_cancellation"} <= claim_types


def test_example_scripts_run_and_print_expected_output(capsys):
    for script in [
        "examples/assist_demo.py",
        "examples/verify_demo.py",
        "examples/evaluation_demo.py",
    ]:
        runpy.run_path(script, run_name="__main__")

    captured = capsys.readouterr()
    assert "UrbanLite Commuter Backpack 22L" in captured.out
    assert "warning" in captured.out
    assert "missions_total" in captured.out


def test_headphones_jsonl_rows_are_valid_json_objects():
    for path in [
        Path("examples/headphones/catalog.jsonl"),
        Path("examples/headphones/missions.jsonl"),
        Path("examples/headphones/agent_outputs.jsonl"),
    ]:
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                assert isinstance(json.loads(line), dict)
