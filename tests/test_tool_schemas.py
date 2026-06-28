import pytest
from pydantic import ValidationError

from recharness import AssistRequest, AssistResponse, ParseRequest, VerifyResponse


def test_tool_request_response_models_are_json_serializable():
    request = AssistRequest(
        user_query="Find headphones",
        domain="headphones",
        top_k=3,
        include_rejected=False,
        variant="keyword_only",
    )
    response = AssistResponse(status="error", domain="headphones", errors=["Unknown domain"])

    assert request.model_dump(mode="json") == {
        "user_query": "Find headphones",
        "domain": "headphones",
        "top_k": 3,
        "include_rejected": False,
        "variant": "keyword_only",
    }
    assert response.model_dump(mode="json")["bundle"] is None
    assert response.errors == ["Unknown domain"]


def test_tool_error_envelopes_do_not_need_exception_objects():
    parse = ParseRequest(user_query="hello")
    verify = VerifyResponse(status="error", errors=["No route could be resolved"])

    assert parse.domain is None
    assert verify.report is None
    assert verify.model_dump(mode="json")["errors"] == ["No route could be resolved"]


def test_assist_request_top_k_bounds():
    assert AssistRequest(user_query="Find headphones").top_k == 5
    assert AssistRequest(user_query="Find headphones", top_k=1).top_k == 1
    assert AssistRequest(user_query="Find headphones", top_k=20).top_k == 20

    with pytest.raises(ValidationError):
        AssistRequest(user_query="Find headphones", top_k=0)
    with pytest.raises(ValidationError):
        AssistRequest(user_query="Find headphones", top_k=21)
