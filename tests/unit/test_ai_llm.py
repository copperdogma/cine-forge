from __future__ import annotations

from typing import Any

import pytest
from pydantic import BaseModel

from cine_forge.ai.llm import (
    LLMCallError,
    _breaker_state,
    _is_circuit_breaker_open,
    _normalize_gemini_response,
    _parse_provider,
    _record_provider_success,
    _record_provider_transient_failure,
    _reset_circuit_breakers,
    _retry_delay_seconds,
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
def test_call_llm_retries_on_529_overloaded_error() -> None:
    attempts = {"count": 0}

    def flaky_transport(_: dict[str, Any]) -> dict[str, Any]:
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise RuntimeError("Anthropic HTTP error 529: overloaded_error")
        return {
            "id": "req_529",
            "choices": [{"message": {"content": "ok"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 10},
        }

    result, metadata = call_llm(
        prompt="normalize",
        model="claude-sonnet-4-6",
        max_retries=2,
        transport=flaky_transport,
    )

    assert result == "ok"
    assert metadata["request_id"] == "req_529"
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
def test_retry_delay_seconds_uses_exponential_backoff_with_jitter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("cine_forge.ai.llm.random.uniform", lambda _a, b: b)

    assert _retry_delay_seconds(attempt=0, base_delay_seconds=0.5, jitter_ratio=0.25) == 0.625
    assert _retry_delay_seconds(attempt=1, base_delay_seconds=0.5, jitter_ratio=0.25) == 1.25
    assert _retry_delay_seconds(attempt=2, base_delay_seconds=0.5, jitter_ratio=0.25) == 2.5


@pytest.mark.unit
def test_retry_delay_seconds_rejects_negative_inputs() -> None:
    with pytest.raises(ValueError, match="attempt"):
        _retry_delay_seconds(attempt=-1)
    with pytest.raises(ValueError, match="base_delay_seconds"):
        _retry_delay_seconds(attempt=0, base_delay_seconds=-0.1)
    with pytest.raises(ValueError, match="jitter_ratio"):
        _retry_delay_seconds(attempt=0, jitter_ratio=-0.1)


@pytest.mark.unit
def test_circuit_breaker_opens_after_three_transient_failures() -> None:
    _reset_circuit_breakers()
    provider = "anthropic"

    _record_provider_transient_failure(provider, now=100.0)
    _record_provider_transient_failure(provider, now=101.0)
    assert not _is_circuit_breaker_open(provider, now=101.0)

    _record_provider_transient_failure(provider, now=102.0)
    assert _is_circuit_breaker_open(provider, now=102.1)


@pytest.mark.unit
def test_circuit_breaker_closes_after_cooldown_and_resets_on_success() -> None:
    _reset_circuit_breakers()
    provider = "google"

    _record_provider_transient_failure(provider, now=10.0)
    _record_provider_transient_failure(provider, now=11.0)
    _record_provider_transient_failure(provider, now=12.0)
    assert _is_circuit_breaker_open(provider, now=12.1)

    assert not _is_circuit_breaker_open(provider, now=43.0)
    assert _breaker_state(provider).consecutive_failures == 0

    _record_provider_transient_failure(provider, now=50.0)
    _record_provider_success(provider)
    assert _breaker_state(provider).consecutive_failures == 0
    assert not _is_circuit_breaker_open(provider, now=50.1)


@pytest.mark.unit
def test_circuit_breaker_half_open_probe_failure_reopens() -> None:
    _reset_circuit_breakers()
    provider = "anthropic"

    _record_provider_transient_failure(provider, now=10.0)
    _record_provider_transient_failure(provider, now=11.0)
    _record_provider_transient_failure(provider, now=12.0)
    assert _is_circuit_breaker_open(provider, now=12.1)

    # Cooldown expires; next call is half-open probe.
    assert not _is_circuit_breaker_open(provider, now=43.0)
    assert _breaker_state(provider).half_open is True

    # Probe failure should reopen immediately.
    _record_provider_transient_failure(provider, now=43.1)
    assert _is_circuit_breaker_open(provider, now=43.2)


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
