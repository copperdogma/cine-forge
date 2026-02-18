from __future__ import annotations

from typing import Any

import pytest
from pydantic import BaseModel

from cine_forge.ai.llm import (
    LLMCallError,
    _normalize_gemini_response,
    _parse_provider,
    _to_gemini_schema,
    call_llm,
    estimate_cost_usd,
)


class DemoSchema(BaseModel):
    value: str


@pytest.mark.unit
def test_call_llm_returns_parsed_schema_and_metadata() -> None:
    def fake_transport(_: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": "req_123",
            "choices": [{"message": {"content": '{"value":"ok"}'}}],
            "usage": {"prompt_tokens": 200, "completion_tokens": 40},
        }

    result, metadata = call_llm(
        prompt="hello",
        model="gpt-4o-mini",
        response_schema=DemoSchema,
        transport=fake_transport,
    )

    assert isinstance(result, DemoSchema)
    assert result.value == "ok"
    assert metadata["input_tokens"] == 200
    assert metadata["output_tokens"] == 40
    assert metadata["request_id"] == "req_123"
    assert metadata["estimated_cost_usd"] > 0


@pytest.mark.unit
def test_call_llm_retries_on_transient_error() -> None:
    attempts = {"count": 0}

    def flaky_transport(_: dict[str, Any]) -> dict[str, Any]:
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise RuntimeError("rate limit exceeded")
        return {
            "id": "req_456",
            "choices": [{"message": {"content": "script text"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 20},
        }

    result, metadata = call_llm(
        prompt="normalize",
        model="gpt-4o-mini",
        max_retries=2,
        transport=flaky_transport,
    )

    assert result == "script text"
    assert metadata["request_id"] == "req_456"
    assert attempts["count"] == 2


@pytest.mark.unit
def test_call_llm_fails_after_max_retries() -> None:
    def always_fail(_: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError("timeout while waiting")

    with pytest.raises(LLMCallError, match="failed after retries"):
        call_llm(
            prompt="x",
            model="gpt-4o",
            max_retries=1,
            transport=always_fail,
        )


@pytest.mark.unit
def test_estimate_cost_usd_uses_known_model_pricing() -> None:
    cost = estimate_cost_usd(model="gpt-4o-mini", input_tokens=1_000_000, output_tokens=1_000_000)
    assert cost == pytest.approx(0.75)


@pytest.mark.unit
def test_call_llm_detects_truncation_when_fail_on_truncation() -> None:
    def truncated_transport(_: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": "req_789",
            "choices": [{"message": {"content": "partial"}, "finish_reason": "length"}],
            "usage": {"prompt_tokens": 20, "completion_tokens": 20},
        }

    with pytest.raises(LLMCallError, match="truncated"):
        call_llm(
            prompt="normalize",
            model="gpt-4o-mini",
            fail_on_truncation=True,
            transport=truncated_transport,
        )


# --- Provider Parsing ---


@pytest.mark.unit
def test_parse_provider_prefixed() -> None:
    assert _parse_provider("anthropic:claude-sonnet-4-6") == ("anthropic", "claude-sonnet-4-6")
    assert _parse_provider("google:gemini-2.5-pro") == ("google", "gemini-2.5-pro")
    assert _parse_provider("openai:gpt-4.1") == ("openai", "gpt-4.1")


@pytest.mark.unit
def test_parse_provider_autodetect() -> None:
    assert _parse_provider("claude-sonnet-4-6") == ("anthropic", "claude-sonnet-4-6")
    assert _parse_provider("claude-haiku-4-5-20251001") == (
        "anthropic", "claude-haiku-4-5-20251001"
    )
    assert _parse_provider("gemini-2.5-pro") == ("google", "gemini-2.5-pro")
    assert _parse_provider("gemini-2.5-flash") == ("google", "gemini-2.5-flash")
    assert _parse_provider("gpt-4.1") == ("openai", "gpt-4.1")
    assert _parse_provider("gpt-4o-mini") == ("openai", "gpt-4o-mini")


@pytest.mark.unit
def test_parse_provider_unknown_prefix_falls_through() -> None:
    # Unknown prefix treated as part of model name, auto-detects to openai
    assert _parse_provider("unknown:some-model") == ("openai", "unknown:some-model")


# --- Gemini Response Normalization ---


@pytest.mark.unit
def test_normalize_gemini_response_basic() -> None:
    raw = {
        "candidates": [{
            "content": {"parts": [{"text": "hello world"}]},
            "finishReason": "STOP",
        }],
        "usageMetadata": {
            "promptTokenCount": 100,
            "candidatesTokenCount": 50,
        },
    }
    normalized = _normalize_gemini_response(raw)
    assert normalized["choices"][0]["message"]["content"] == "hello world"
    assert normalized["choices"][0]["finish_reason"] == "stop"
    assert normalized["usage"]["prompt_tokens"] == 100
    assert normalized["usage"]["completion_tokens"] == 50


@pytest.mark.unit
def test_normalize_gemini_response_truncation() -> None:
    raw = {
        "candidates": [{
            "content": {"parts": [{"text": "partial"}]},
            "finishReason": "MAX_TOKENS",
        }],
        "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 10},
    }
    normalized = _normalize_gemini_response(raw)
    assert normalized["choices"][0]["finish_reason"] == "length"


@pytest.mark.unit
def test_normalize_gemini_response_missing_candidates() -> None:
    with pytest.raises(LLMCallError, match="missing candidates"):
        _normalize_gemini_response({"candidates": []})


# --- Gemini Schema Conversion ---


@pytest.mark.unit
def test_to_gemini_schema_simple() -> None:
    schema = DemoSchema.model_json_schema()
    result = _to_gemini_schema(schema)
    assert result["type"] == "OBJECT"
    assert result["properties"]["value"]["type"] == "STRING"
    assert "title" not in result
    assert "additionalProperties" not in result


@pytest.mark.unit
def test_to_gemini_schema_with_optional_field() -> None:
    class WithOptional(BaseModel):
        name: str
        nickname: str | None = None

    schema = WithOptional.model_json_schema()
    result = _to_gemini_schema(schema)
    assert result["properties"]["name"]["type"] == "STRING"
    # Optional resolves to the non-null variant
    assert result["properties"]["nickname"]["type"] == "STRING"


@pytest.mark.unit
def test_to_gemini_schema_nested_model() -> None:
    class Inner(BaseModel):
        score: float

    class Outer(BaseModel):
        name: str
        detail: Inner

    schema = Outer.model_json_schema()
    result = _to_gemini_schema(schema)
    assert result["properties"]["name"]["type"] == "STRING"
    detail = result["properties"]["detail"]
    assert detail["type"] == "OBJECT"
    assert detail["properties"]["score"]["type"] == "NUMBER"


# --- Gemini end-to-end via call_llm with injected transport ---


@pytest.mark.unit
def test_call_llm_with_gemini_model_uses_transport() -> None:
    """Verify gemini-* auto-detects to google and works with injected transport."""

    def fake_gemini_transport(_: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": "",
            "choices": [{"message": {"content": '{"value":"gemini_ok"}'}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 50, "completion_tokens": 20},
        }

    result, metadata = call_llm(
        prompt="test",
        model="gemini-2.5-pro",
        response_schema=DemoSchema,
        transport=fake_gemini_transport,
    )
    assert isinstance(result, DemoSchema)
    assert result.value == "gemini_ok"


@pytest.mark.unit
def test_call_llm_with_prefixed_model_string() -> None:
    """Verify provider-prefixed model strings work through call_llm."""

    def fake_transport(_: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": "req_prefix",
            "choices": [{"message": {"content": "prefixed"}}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 5},
        }

    result, metadata = call_llm(
        prompt="test",
        model="anthropic:claude-sonnet-4-6",
        transport=fake_transport,
    )
    assert result == "prefixed"
    # bare_model is used for cost estimation
    assert metadata["model"] == "claude-sonnet-4-6"
