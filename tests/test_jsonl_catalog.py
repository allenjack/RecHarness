import json

import pytest

from recharness import JsonlCatalog, ProductItem
from recharness.catalog import CatalogLoadError


def write_jsonl(path, rows):
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def test_loads_valid_jsonl_catalog(tmp_path):
    catalog_path = tmp_path / "catalog.jsonl"
    write_jsonl(
        catalog_path,
        [
            {
                "product_id": "bag_001",
                "title": "UrbanLite Commuter Backpack 22L",
                "category": "backpack",
                "price": {"amount": 899, "currency": "CNY"},
                "attributes": {"laptop_size_inches": 14, "weight_kg": 0.85},
            }
        ],
    )

    catalog = JsonlCatalog.load(catalog_path)

    assert len(catalog) == 1
    assert isinstance(catalog[0], ProductItem)
    assert catalog[0].product_id == "bag_001"


def test_validate_reports_duplicate_product_ids(tmp_path):
    catalog_path = tmp_path / "catalog.jsonl"
    write_jsonl(
        catalog_path,
        [
            {"product_id": "bag_001", "title": "Bag One", "category": "backpack"},
            {"product_id": "bag_001", "title": "Bag Duplicate", "category": "backpack"},
        ],
    )

    report = JsonlCatalog.load(catalog_path).validate()

    assert report.is_valid is False
    assert report.product_count == 2
    assert report.duplicate_product_ids == ["bag_001"]
    assert any("Duplicate product_id" in issue.message for issue in report.issues)


def test_malformed_jsonl_raises_load_error_with_line_number(tmp_path):
    catalog_path = tmp_path / "catalog.jsonl"
    catalog_path.write_text('{"product_id": "bag_001"\n', encoding="utf-8")

    with pytest.raises(CatalogLoadError) as exc:
        JsonlCatalog.load(catalog_path)

    assert "line 1" in str(exc.value)


def test_missing_required_product_field_raises_load_error(tmp_path):
    catalog_path = tmp_path / "catalog.jsonl"
    write_jsonl(catalog_path, [{"product_id": "bag_001", "category": "backpack"}])

    with pytest.raises(CatalogLoadError) as exc:
        JsonlCatalog.load(catalog_path)

    assert "line 1" in str(exc.value)
    assert "title" in str(exc.value)


def test_catalog_stats_reports_field_coverage(tmp_path):
    catalog_path = tmp_path / "catalog.jsonl"
    write_jsonl(
        catalog_path,
        [
            {
                "product_id": "bag_001",
                "title": "UrbanLite",
                "category": "backpack",
                "price": {"amount": 899, "currency": "CNY"},
                "attributes": {"laptop_size_inches": 14, "weight_kg": 0.85},
            },
            {
                "product_id": "bag_002",
                "title": "Trail Pack",
                "category": "backpack",
                "attributes": {"laptop_size_inches": 16},
            },
        ],
    )

    stats = JsonlCatalog.load(catalog_path).stats()

    assert stats.product_count == 2
    assert stats.field_coverage["price"] == 0.5
    assert stats.field_coverage["attributes.laptop_size_inches"] == 1.0
    assert stats.field_coverage["attributes.weight_kg"] == 0.5


def test_example_backpack_catalog_loads_and_validates():
    catalog = JsonlCatalog.load("examples/backpacks/catalog.jsonl")

    report = catalog.validate()
    stats = catalog.stats()

    assert report.is_valid is True
    assert report.product_count >= 50
    assert stats.field_coverage["attributes.laptop_size_inches"] == 1.0
