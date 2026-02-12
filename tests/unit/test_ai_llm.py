from __future__ import annotations

from typing import Any

import pytest
from pydantic import BaseModel

from cine_forge.ai.llm import LLMCallError, call_llm, estimate_cost_usd


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
