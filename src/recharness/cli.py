"""Command-line entrypoint for RecHarness."""

from __future__ import annotations

import argparse
import sys

from recharness.catalog import CatalogLoadError, JsonlCatalog


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="recharness")
    subparsers = parser.add_subparsers(dest="command", required=True)

    catalog_parser = subparsers.add_parser("catalog")
    catalog_subparsers = catalog_parser.add_subparsers(dest="catalog_command", required=True)
    validate_parser = catalog_subparsers.add_parser("validate")
    validate_parser.add_argument("catalog_path")

    args = parser.parse_args(argv)

    if args.command == "catalog" and args.catalog_command == "validate":
        return _validate_catalog(args.catalog_path)

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


if __name__ == "__main__":
    raise SystemExit(main())
