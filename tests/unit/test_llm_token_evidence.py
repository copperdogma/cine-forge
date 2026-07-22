"""Production LLM metadata must not coerce or misreconcile token evidence."""

from __future__ import annotations

from typing import Any

import pytest

from cine_forge.ai.errors import LLMCallError
from cine_forge.ai.llm import _reset_circuit_breakers, call_llm

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def _clean_breakers() -> None:
    _reset_circuit_breakers()


def _response(usage: dict[str, object]) -> dict[str, Any]:
    return {
        "id": "response-usage-1",
        "model": "gpt-5.5",
        "choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}],
        "usage": usage,
    }


@pytest.mark.parametrize(
    "usage",
    [
        {"prompt_tokens": "10", "completion_tokens": 5},
        {"prompt_tokens": True, "completion_tokens": 5},
        {"prompt_tokens": 10, "completion_tokens": -1},
        {"prompt_tokens": 10, "completion_tokens": 5.5},
        {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 14},
        {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": "15"},
    ],
)
def test_production_metadata_rejects_malformed_standard_usage(
    monkeypatch: pytest.MonkeyPatch,
    usage: dict[str, object],
) -> None:
    monkeypatch.setattr(
        "cine_forge.ai.llm._openai_transport",
        lambda *_a, **_k: _response(usage),
    )

    with pytest.raises((LLMCallError, ValueError)):
        call_llm("prompt", model="gpt-5.5", max_retries=0)


def test_xai_production_usage_reconciles_visible_reasoning_and_total(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = _response(
        {
            "prompt_tokens": 100,
            "completion_tokens": 20,
            "total_tokens": 1120,
            "completion_tokens_details": {"reasoning_tokens": 1000},
        }
    )
    response["model"] = "grok-4.5"
    monkeypatch.setattr(
        "cine_forge.ai.llm._xai_transport",
        lambda *_a, **_k: response,
    )

    output, metadata = call_llm("prompt", model="grok-4.5", max_retries=0)

    assert output == "ok"
    assert metadata["output_tokens"] == 20
    assert metadata["reasoning_output_tokens"] == 1000
    assert metadata["estimated_cost_usd"] == pytest.approx(0.00632)


def test_xai_production_usage_rejects_reasoning_total_contradiction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = _response(
        {
            "prompt_tokens": 100,
            "completion_tokens": 20,
            "total_tokens": 1120,
            "completion_tokens_details": {"reasoning_tokens": 999},
        }
    )
    response["model"] = "grok-4.5"
    monkeypatch.setattr(
        "cine_forge.ai.llm._xai_transport",
        lambda *_a, **_k: response,
    )

    with pytest.raises(LLMCallError, match="does not reconcile"):
        call_llm("prompt", model="grok-4.5", max_retries=0)
