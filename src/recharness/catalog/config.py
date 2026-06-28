"""Multi-catalog configuration loading."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import Field, ValidationError, model_validator

from recharness.schema import RecHarnessModel


class CatalogConfigError(ValueError):
    """Raised when a multi-catalog config cannot be loaded."""


class CatalogConfig(RecHarnessModel):
    path: str
    category: str | None = None
    description: str | None = None


class MultiCatalogConfig(RecHarnessModel):
    catalogs: dict[str, CatalogConfig] = Field(default_factory=dict)
    default_catalog: str | None = None

    @model_validator(mode="after")
    def validate_default_catalog(self) -> MultiCatalogConfig:
        if self.default_catalog is not None and self.default_catalog not in self.catalogs:
            raise ValueError(
                f"default_catalog '{self.default_catalog}' is not present in catalogs"
            )
        return self


def load_multi_catalog_config(path: str | Path) -> MultiCatalogConfig:
    config_path = Path(path)
    try:
        text = config_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CatalogConfigError(f"Could not read catalog config {config_path}: {exc}") from exc

    try:
        raw = _load_config_text(config_path, text)
        return MultiCatalogConfig.model_validate(raw)
    except CatalogConfigError:
        raise
    except (json.JSONDecodeError, ValidationError, ValueError) as exc:
        raise CatalogConfigError(f"Invalid catalog config {config_path}: {exc}") from exc


def _load_config_text(path: Path, text: str) -> dict[str, Any]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return json.loads(text)
    if suffix in {".yaml", ".yml"}:
        try:
            import yaml
        except ImportError as exc:
            raise CatalogConfigError(
                "PyYAML is required to load YAML catalog configs. "
                "Use JSON or install pyyaml."
            ) from exc
        loaded = yaml.safe_load(text)
        return loaded if isinstance(loaded, dict) else {}
    raise CatalogConfigError(f"Unsupported catalog config extension: {suffix}")
