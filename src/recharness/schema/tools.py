"""Stable agent-facing request and response schemas."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from recharness.schema import (
    RecHarnessModel,
    RecommendationBundle,
    UserNeed,
    VerificationReport,
)


class AssistRequest(RecHarnessModel):
    user_query: str
    domain: str | None = None
    top_k: int = 5
    include_rejected: bool = True
    variant: str = "full"


class AssistResponse(RecHarnessModel):
    status: Literal["ok", "warning", "error"]
    domain: str | None = None
    bundle: RecommendationBundle | None = None
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class VerifyRequest(RecHarnessModel):
    user_query: str
    agent_answer: str
    domain: str | None = None


class VerifyResponse(RecHarnessModel):
    status: Literal["pass", "warning", "fail", "error"]
    domain: str | None = None
    report: VerificationReport | None = None
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ParseRequest(RecHarnessModel):
    user_query: str
    domain: str | None = None


class ParseResponse(RecHarnessModel):
    status: Literal["ok", "error"]
    domain: str | None = None
    user_need: UserNeed | None = None
    errors: list[str] = Field(default_factory=list)
