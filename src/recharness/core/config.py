"""Configuration values for harness construction."""

from __future__ import annotations

from enum import StrEnum


class HarnessVariant(StrEnum):
    """Diagnostic retrieval modes for comparing harness behavior."""

    FULL = "full"
    KEYWORD_ONLY = "keyword_only"
    CONSTRAINT_ONLY = "constraint_only"

    @classmethod
    def parse(cls, value: str) -> HarnessVariant:
        try:
            return cls(value)
        except ValueError as exc:
            valid = ", ".join(variant.value for variant in cls)
            raise ValueError(f"Unknown harness variant '{value}'. Valid variants: {valid}") from exc
