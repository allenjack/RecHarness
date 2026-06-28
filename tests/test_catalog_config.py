import pytest

from recharness.catalog import CatalogConfigError, load_multi_catalog_config


def test_json_multi_catalog_config_loads():
    config = load_multi_catalog_config("examples/mcp/catalogs.json")

    assert config.default_catalog == "backpacks"
    assert config.catalogs["headphones"].category == "headphones"


def test_invalid_default_catalog_fails(tmp_path):
    config_path = tmp_path / "catalogs.json"
    config_path.write_text(
        '{"default_catalog":"missing","catalogs":{"backpacks":{"path":"x.jsonl"}}}',
        encoding="utf-8",
    )

    with pytest.raises(CatalogConfigError, match="default_catalog"):
        load_multi_catalog_config(config_path)


def test_missing_config_file_returns_clear_error(tmp_path):
    with pytest.raises(CatalogConfigError, match="Could not read catalog config"):
        load_multi_catalog_config(tmp_path / "missing.json")


def test_yaml_config_without_dependency_has_clear_error(tmp_path, monkeypatch):
    config_path = tmp_path / "catalogs.yaml"
    config_path.write_text("catalogs: {}", encoding="utf-8")

    import builtins

    original_import = builtins.__import__

    def blocked_import(name, *args, **kwargs):
        if name == "yaml":
            raise ImportError("blocked")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked_import)

    with pytest.raises(CatalogConfigError, match="PyYAML"):
        load_multi_catalog_config(config_path)
