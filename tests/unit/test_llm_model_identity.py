"""Adversarial contracts for live LLM response identity."""

from __future__ import annotations

from typing import Any

import pytest

from cine_forge.ai.errors import LLMCallError
from cine_forge.ai.llm import _reset_circuit_breakers, call_llm
from cine_forge.ai.model_identity import validate_provider_response_identity

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def _clean_breakers() -> None:
    _reset_circuit_breakers()


def _chat_response(*, model: str | None, request_id: str | None = "resp-1") -> dict:
    response: dict[str, Any] = {
        "choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5},
    }
    if model is not None:
        response["model"] = model
    if request_id is not None:
        response["id"] = request_id
    return response


@pytest.mark.parametrize(
    ("provider", "requested", "returned"),
    [
        ("openai", "gpt-5.5-pro", "gpt-5.5-pro-2026-04-23"),
        ("anthropic", "claude-sonnet-4-5", "claude-sonnet-4-5-20250929"),
    ],
)
def test_provider_snapshot_aliases_are_exact_and_auditable(
    provider: str,
    requested: str,
    returned: str,
) -> None:
    identity = validate_provider_response_identity(
        provider=provider,
        requested_model=requested,
        returned_model=returned,
        request_id="response-1",
        require_returned=True,
    )

    assert identity.requested_model == requested
    assert identity.returned_model == returned
    assert identity.billing_model == requested


@pytest.mark.parametrize(
    ("provider", "requested", "returned"),
    [
        ("openai", "gpt-5.5", "gpt-5.5-mini-2026-04-23"),
        ("openai", "gpt-5.5-pro-2026-04-23", "gpt-5.5-pro-2026-05-01"),
        (
            "openai",
            "gpt-5.4-2026-01-01",
            "gpt-5.4-2026-01-01-2026-07-22",
        ),
        ("anthropic", "claude-opus-4-8", "claude-haiku-4-5-20251001"),
        (
            "anthropic",
            "claude-sonnet-4-5-20250929",
            "claude-sonnet-4-5-20250929-20260722",
        ),
        (
            "anthropic",
            "claude-sonnet-4-5",
            "claude-sonnet-4-5-20260722",
        ),
        (
            "anthropic",
            "claude-sonnet-4-6",
            "claude-sonnet-4-6-20260722",
        ),
        (
            "anthropic",
            "claude-opus-4-8",
            "claude-opus-4-8-20260722",
        ),
        ("xai", "grok-4.5", "grok-4.3"),
    ],
)
def test_provider_alias_policy_rejects_variant_or_snapshot_substitution(
    provider: str,
    requested: str,
    returned: str,
) -> None:
    with pytest.raises(LLMCallError, match="does not match requested model"):
        validate_provider_response_identity(
            provider=provider,
            requested_model=requested,
            returned_model=returned,
            request_id="response-1",
            require_returned=True,
        )


@pytest.mark.parametrize("missing", ["model", "id"])
def test_live_openai_requires_model_and_call_identity(
    monkeypatch: pytest.MonkeyPatch,
    missing: str,
) -> None:
    response = _chat_response(
        model=None if missing == "model" else "gpt-5.5",
        request_id=None if missing == "id" else "resp-1",
    )
    monkeypatch.setattr("cine_forge.ai.llm._openai_transport", lambda *_a, **_k: response)

    with pytest.raises(LLMCallError, match="must be a non-empty string"):
        call_llm("prompt", model="gpt-5.5", max_retries=0)


@pytest.mark.parametrize(
    ("model", "transport_name", "returned"),
    [
        ("gpt-5.5-pro", "_openai_transport", "gpt-4o-mini"),
        ("grok-4.5", "_xai_transport", "grok-4.3"),
    ],
)
def test_live_openai_compatible_transports_reject_model_substitution(
    monkeypatch: pytest.MonkeyPatch,
    model: str,
    transport_name: str,
    returned: str,
) -> None:
    monkeypatch.setattr(
        f"cine_forge.ai.llm.{transport_name}",
        lambda *_a, **_k: _chat_response(model=returned),
    )

    with pytest.raises(LLMCallError, match="does not match requested model"):
        call_llm("prompt", model=model, max_retries=0)


def test_live_anthropic_rejects_substitution_after_normalization(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "cine_forge.ai.llm._anthropic_transport",
        lambda *_a, **_k: {
            "id": "msg-1",
            "model": "claude-haiku-4-5-20251001",
            "content": [{"type": "text", "text": "ok"}],
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 10, "output_tokens": 5},
        },
    )

    with pytest.raises(LLMCallError, match="does not match requested model"):
        call_llm("prompt", model="claude-opus-4-8", max_retries=0)


def test_live_openai_preserves_requested_and_returned_snapshot_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "cine_forge.ai.llm._openai_transport",
        lambda *_a, **_k: _chat_response(model="gpt-5.5-2026-04-23"),
    )

    output, metadata = call_llm("prompt", model="gpt-5.5", max_retries=0)

    assert output == "ok"
    assert metadata["model"] == "gpt-5.5"
    assert metadata["requested_model"] == "gpt-5.5"
    assert metadata["returned_model"] == "gpt-5.5-2026-04-23"
    assert metadata["request_id"] == "resp-1"


def test_injected_transport_may_omit_provider_identity() -> None:
    output, metadata = call_llm(
        "prompt",
        model="gpt-5.5",
        max_retries=0,
        transport=lambda _payload: _chat_response(model=None, request_id=None),
    )

    assert output == "ok"
    assert metadata["requested_model"] == "gpt-5.5"
    assert metadata["returned_model"] is None
    assert metadata["request_id"] is None
