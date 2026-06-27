"""Command-line entrypoint for RecHarness."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from recharness.catalog import CatalogLoadError, JsonlCatalog
from recharness.core import RecHarness
from recharness.evaluation import EvalRunner
from recharness.integrations.mcp_server import create_mcp_server


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="recharness")
    subparsers = parser.add_subparsers(dest="command", required=True)

    catalog_parser = subparsers.add_parser("catalog")
    catalog_subparsers = catalog_parser.add_subparsers(dest="catalog_command", required=True)
    validate_parser = catalog_subparsers.add_parser("validate")
    validate_parser.add_argument("catalog_path")

    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--catalog", required=True)
    verify_parser.add_argument("--query", required=True)
    verify_parser.add_argument("--json", action="store_true")
    verify_parser.add_argument("--trace-path")
    verify_parser.add_argument("--no-fail-on-warning", action="store_true")
    answer_group = verify_parser.add_mutually_exclusive_group(required=True)
    answer_group.add_argument("--answer")
    answer_group.add_argument("--answer-file")

    assist_parser = subparsers.add_parser("assist")
    assist_parser.add_argument("--catalog", required=True)
    assist_parser.add_argument("--query", required=True)
    assist_parser.add_argument("--top-k", type=int, default=5)
    assist_parser.add_argument("--json", action="store_true")
    assist_parser.add_argument("--trace-path")

    eval_parser = subparsers.add_parser("eval")
    eval_parser.add_argument("--catalog", required=True)
    eval_parser.add_argument("--missions", required=True)
    eval_parser.add_argument("--agent-outputs", required=True)
    eval_parser.add_argument("--out", required=True)

    mcp_parser = subparsers.add_parser("mcp")
    mcp_subparsers = mcp_parser.add_subparsers(dest="mcp_command", required=True)
    mcp_serve_parser = mcp_subparsers.add_parser("serve")
    mcp_serve_parser.add_argument("--catalog", required=True)

    args = parser.parse_args(argv)

    if args.command == "catalog" and args.catalog_command == "validate":
        return _validate_catalog(args.catalog_path)
    if args.command == "verify":
        return _verify_recommendation(
            args.catalog,
            args.query,
            args.answer,
            args.answer_file,
            json_output=args.json,
            trace_path=args.trace_path,
            no_fail_on_warning=args.no_fail_on_warning,
        )
    if args.command == "assist":
        return _assist(
            args.catalog,
            args.query,
            args.top_k,
            json_output=args.json,
            trace_path=args.trace_path,
        )
    if args.command == "eval":
        return _eval(args.catalog, args.missions, args.agent_outputs, args.out)
    if args.command == "mcp" and args.mcp_command == "serve":
        return _mcp_serve(args.catalog)

    parser.error("Unsupported command")
    return 2


def _validate_catalog(catalog_path: str) -> int:
    try:
        catalog = JsonlCatalog.load(catalog_path)
    except CatalogLoadError as exc:
        print(f"Catalog invalid: {exc}", file=sys.stderr)
        return 1

    report = catalog.validate()
    stats = catalog.stats()

    if report.is_valid:
        print(f"Catalog valid: {report.product_count} products")
    else:
        print(f"Catalog invalid: {report.product_count} products")
        for issue in report.issues:
            print(f"- {issue.message}")

    print("Fields coverage:")
    for field, coverage in sorted(stats.field_coverage.items()):
        print(f"- {field}: {coverage:.0%}")

    return 0 if report.is_valid else 1


def _verify_recommendation(
    catalog_path: str,
    query: str,
    answer: str | None,
    answer_file: str | None,
    json_output: bool = False,
    trace_path: str | None = None,
    no_fail_on_warning: bool = False,
) -> int:
    try:
        harness = RecHarness.from_jsonl_catalog(catalog_path, trace_path=trace_path)
    except CatalogLoadError as exc:
        print(f"Catalog invalid: {exc}", file=sys.stderr)
        return 1

    agent_answer = answer if answer is not None else Path(answer_file).read_text(encoding="utf-8")
    report = harness.verify_agent_recommendation(query, agent_answer)

    if json_output:
        _print_json(report.model_dump(mode="json"))
        return _verify_exit_code(report.status, no_fail_on_warning)

    print(report.status.upper())
    if report.summary:
        print(report.summary)
    if report.violations:
        print("Violations:")
        for violation in report.violations:
            print(f"- {violation.message}")
    if report.claim_issues:
        print("Claim issues:")
        for issue in report.claim_issues:
            print(
                f"- [{issue.severity}] {issue.claim_type} "
                f"{issue.field}: {issue.message}"
            )
    if report.unsupported_claims:
        print("Unsupported claims:")
        for claim in report.unsupported_claims:
            print(f"- {claim}")
    if report.repair_suggestions:
        print("Repair suggestions:")
        for suggestion in report.repair_suggestions:
            print(f"- {suggestion}")

    return _verify_exit_code(report.status, no_fail_on_warning)


def _assist(
    catalog_path: str,
    query: str,
    top_k: int,
    json_output: bool = False,
    trace_path: str | None = None,
) -> int:
    try:
        harness = RecHarness.from_jsonl_catalog(catalog_path, trace_path=trace_path)
    except CatalogLoadError as exc:
        print(f"Catalog invalid: {exc}", file=sys.stderr)
        return 1

    bundle = harness.assist(query, top_k=top_k)

    if json_output:
        _print_json(bundle.model_dump(mode="json"))
        return 0

    print("Parsed need")
    print(f"- category: {bundle.user_need.category or 'unknown'}")
    scenarios = ", ".join(bundle.user_need.scenario) if bundle.user_need.scenario else "none"
    print(f"- scenarios: {scenarios}")
    if bundle.constraint_report is not None:
        print(f"- constraint report: {bundle.constraint_report.status}")

    print("Top recommendations")
    for index, candidate in enumerate(bundle.recommended, start=1):
        score = "n/a" if candidate.final_score is None else f"{candidate.final_score:.3f}"
        price = ""
        if candidate.product.price is not None:
            price = f" - {candidate.product.price.amount:g} {candidate.product.price.currency}"
        print(f"{index}. {candidate.product.title}{price} - score {score}")
        if candidate.violations:
            print(f"   Risks: {len(candidate.violations)} constraint violation(s)")

    if bundle.rejected:
        print("Rejected products")
        for candidate in bundle.rejected:
            print(f"- {candidate.product.title}")
            for violation in candidate.violations:
                print(f"  - {violation.message}")

    if bundle.summary_for_agent:
        print("Summary for agent")
        print(bundle.summary_for_agent)

    return 0


def _verify_exit_code(status: str, no_fail_on_warning: bool) -> int:
    if status == "pass":
        return 0
    if status == "warning" and no_fail_on_warning:
        return 0
    return 1


def _print_json(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False))


def _eval(catalog_path: str, missions_path: str, outputs_path: str, out_dir: str) -> int:
    try:
        harness = RecHarness.from_jsonl_catalog(catalog_path)
    except CatalogLoadError as exc:
        print(f"Catalog invalid: {exc}", file=sys.stderr)
        return 1

    result = EvalRunner(harness=harness, missions_path=missions_path).run_with_agent_outputs(
        outputs_path
    )
    result.write(out_dir)

    print(f"Evaluated {result.metrics['missions_total']} mission outputs")
    print(f"Wrote metrics.json, leaderboard.csv, and traces.jsonl to {out_dir}")
    return 0


def _mcp_serve(catalog_path: str) -> int:
    try:
        server = create_mcp_server(catalog_path)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    server.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
