# Contributing to RecHarness

Thanks for helping improve RecHarness.

## Development Setup

```bash
uv sync --extra dev
uv run pytest
uv run ruff check .
```

If `uv` is unavailable:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m pytest
.venv/bin/ruff check .
```

## Scope

RecHarness is a recommendation reliability harness, not a full shopping agent or ecommerce platform. Prefer deterministic, offline behavior for core features. Put optional model or runtime integrations behind adapters.

## Pull Requests

- Keep PRs focused on one milestone or behavior.
- Add tests for parser, verifier, retrieval, ranking, CLI, or evaluation changes.
- Update README or docs when public APIs or commands change.
- Run tests and lint before requesting review.
