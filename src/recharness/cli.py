"""Command-line entrypoint for RecHarness."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from recharness.catalog import CatalogLoadError, JsonlCatalog
from recharness.core import RecHarness


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
    answer_group = verify_parser.add_mutually_exclusive_group(required=True)
    answer_group.add_argument("--answer")
    answer_group.add_argument("--answer-file")

    args = parser.parse_args(argv)

    if args.command == "catalog" and args.catalog_command == "validate":
        return _validate_catalog(args.catalog_path)
    if args.command == "verify":
        return _verify_recommendation(args.catalog, args.query, args.answer, args.answer_file)

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
) -> int:
    try:
        harness = RecHarness.from_jsonl_catalog(catalog_path)
    except CatalogLoadError as exc:
        print(f"Catalog invalid: {exc}", file=sys.stderr)
        return 1

    agent_answer = answer if answer is not None else Path(answer_file).read_text(encoding="utf-8")
    report = harness.verify_agent_recommendation(query, agent_answer)

    print(report.status.upper())
    if report.summary:
        print(report.summary)
    if report.violations:
        print("Violations:")
        for violation in report.violations:
            print(f"- {violation.message}")
    if report.unsupported_claims:
        print("Unsupported claims:")
        for claim in report.unsupported_claims:
            print(f"- {claim}")
    if report.repair_suggestions:
        print("Repair suggestions:")
        for suggestion in report.repair_suggestions:
            print(f"- {suggestion}")

    return 0 if report.status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
