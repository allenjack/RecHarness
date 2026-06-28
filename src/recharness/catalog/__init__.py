"""Catalog loading and validation primitives."""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from recharness.catalog.config import (
    CatalogConfig as CatalogConfig,
)
from recharness.catalog.config import (
    CatalogConfigError as CatalogConfigError,
)
from recharness.catalog.config import (
    MultiCatalogConfig as MultiCatalogConfig,
)
from recharness.catalog.config import (
    load_multi_catalog_config as load_multi_catalog_config,
)
from recharness.schema import ProductItem

__all__ = [
    "CatalogConfig",
    "CatalogConfigError",
    "CatalogIssue",
    "CatalogLoadError",
    "CatalogStats",
    "CatalogValidationReport",
    "JsonlCatalog",
    "MultiCatalogConfig",
    "load_multi_catalog_config",
]


class CatalogLoadError(ValueError):
    """Raised when a catalog file cannot be parsed into product records."""


class CatalogIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    product_id: str | None = None
    line: int | None = None


class CatalogValidationReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_valid: bool
    product_count: int
    duplicate_product_ids: list[str] = Field(default_factory=list)
    issues: list[CatalogIssue] = Field(default_factory=list)


class CatalogStats(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_count: int
    field_coverage: dict[str, float] = Field(default_factory=dict)


class JsonlCatalog(Sequence[ProductItem]):
    """In-memory JSONL catalog backed by validated ProductItem records."""

    def __init__(self, products: list[ProductItem], path: Path | None = None) -> None:
        self._products = products
        self.path = path

    @classmethod
    def load(cls, path: str | Path) -> JsonlCatalog:
        catalog_path = Path(path)
        products: list[ProductItem] = []

        try:
            lines = catalog_path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            raise CatalogLoadError(f"Could not read catalog {catalog_path}: {exc}") from exc

        for index, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError as exc:
                raise CatalogLoadError(
                    f"Malformed JSON in {catalog_path} at line {index}: {exc.msg}"
                ) from exc

            try:
                products.append(ProductItem.model_validate(raw))
            except ValidationError as exc:
                details = "; ".join(
                    ".".join(str(part) for part in error["loc"])
                    for error in exc.errors()
                )
                raise CatalogLoadError(
                    f"Invalid product in {catalog_path} at line {index}: {details}"
                ) from exc

        return cls(products=products, path=catalog_path)

    def __len__(self) -> int:
        return len(self._products)

    def __iter__(self) -> Iterator[ProductItem]:
        return iter(self._products)

    def __getitem__(self, index: int) -> ProductItem:
        return self._products[index]

    def validate(self) -> CatalogValidationReport:
        counts = Counter(product.product_id for product in self._products)
        duplicate_ids = sorted(product_id for product_id, count in counts.items() if count > 1)
        issues = [
            CatalogIssue(
                code="duplicate_product_id",
                message=f"Duplicate product_id: {product_id}",
                product_id=product_id,
            )
            for product_id in duplicate_ids
        ]

        return CatalogValidationReport(
            is_valid=not issues,
            product_count=len(self._products),
            duplicate_product_ids=duplicate_ids,
            issues=issues,
        )

    def stats(self) -> CatalogStats:
        field_names = sorted(
            {field for product in self._products for field in _present_fields(product)}
        )
        coverage = {
            field: _coverage_for_field(self._products, field)
            for field in field_names
        }
        return CatalogStats(product_count=len(self._products), field_coverage=coverage)


def _present_fields(product: ProductItem) -> set[str]:
    fields: set[str] = set()
    raw = product.model_dump()
    for name, value in raw.items():
        if _has_value(value):
            fields.add(name)
    if product.price is not None:
        fields.add("price.amount")
        fields.add("price.currency")
    for key, value in product.attributes.items():
        if _has_value(value):
            fields.add(f"attributes.{key}")
    return fields


def _coverage_for_field(products: list[ProductItem], field: str) -> float:
    if not products:
        return 0.0
    present_count = sum(1 for product in products if _has_value(_resolve_field(product, field)))
    return present_count / len(products)


def _resolve_field(product: ProductItem, field: str) -> Any:
    value: Any = product.model_dump()
    for part in field.split("."):
        if isinstance(value, dict):
            value = value.get(part)
        else:
            value = getattr(value, part, None)
        if value is None:
            return None
    return value


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if value == "":
        return False
    if isinstance(value, (list, dict, set, tuple)) and len(value) == 0:
        return False
    return True
