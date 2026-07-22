"""Non-Gemini eval token evidence must be strict and replayable."""

from __future__ import annotations

import pytest

from cine_forge.evals.token_metrics import completion_tokens_for_cost

pytestmark = pytest.mark.unit


def test_openai_normalized_and_raw_usage_reconcile() -> None:
    result = completion_tokens_for_cost(
        "file://../providers/openai_responses_provider.py",
        {"prompt": 100, "completion": 20, "total": 120},
        model_slug="gpt-5.5-pro",
        raw_usage={"input_tokens": 100, "output_tokens": 20, "total_tokens": 120},
    )

    assert result == 20


def test_openai_normalized_and_raw_reasoning_breakdown_reconcile() -> None:
    result = completion_tokens_for_cost(
        "file://../providers/openai_responses_provider.py",
        {
            "prompt": 100,
            "completion": 20,
            "total": 120,
            "completionDetails": {"reasoning": 8},
        },
        model_slug="gpt-5.5-pro",
        raw_usage={
            "input_tokens": 100,
            "output_tokens": 20,
            "total_tokens": 120,
            "output_tokens_details": {"reasoning_tokens": 8},
        },
    )

    assert result == 20


def test_openai_raw_reasoning_breakdown_mismatch_is_rejected() -> None:
    with pytest.raises(ValueError, match="raw provider usage does not match"):
        completion_tokens_for_cost(
            "openai:gpt-5.5",
            {
                "prompt": 100,
                "completion": 20,
                "total": 120,
                "completionDetails": {"reasoning": 8},
            },
            raw_usage={
                "input_tokens": 100,
                "output_tokens": 20,
                "total_tokens": 120,
                "output_tokens_details": {"reasoning_tokens": 7},
            },
        )


@pytest.mark.parametrize("reasoning", [True, "8", 8.0, -1])
def test_openai_raw_reasoning_breakdown_rejects_non_integer_evidence(
    reasoning: object,
) -> None:
    with pytest.raises(ValueError, match="must be a nonnegative integer"):
        completion_tokens_for_cost(
            "openai:gpt-5.5",
            {"prompt": 100, "completion": 20, "total": 120},
            raw_usage={
                "input_tokens": 100,
                "output_tokens": 20,
                "total_tokens": 120,
                "output_tokens_details": {"reasoning_tokens": reasoning},
            },
        )


def test_openai_reasoning_breakdown_cannot_exceed_output_total() -> None:
    with pytest.raises(ValueError, match="must not exceed completion_tokens"):
        completion_tokens_for_cost(
            "openai:gpt-5.5",
            {
                "prompt": 100,
                "completion": 20,
                "total": 120,
                "completionDetails": {"reasoning": 21},
            },
        )


def test_anthropic_normalized_and_raw_usage_reconcile_without_raw_total() -> None:
    result = completion_tokens_for_cost(
        "file://../providers/anthropic_messages_provider.py",
        {"prompt": 100, "completion": 20, "total": 120},
        model_slug="claude-opus-4-8",
        raw_usage={"input_tokens": 100, "output_tokens": 20},
    )

    assert result == 20


def test_xai_normalized_and_raw_reasoning_usage_reconcile() -> None:
    result = completion_tokens_for_cost(
        "xai:grok-4.5",
        {
            "prompt": 100,
            "completion": 20,
            "total": 1120,
            "completionDetails": {"reasoning": 1000},
        },
        raw_usage={
            "prompt_tokens": 100,
            "completion_tokens": 20,
            "total_tokens": 1120,
            "completion_tokens_details": {"reasoning_tokens": 1000},
        },
    )

    assert result == 1020


def test_custom_provider_grok_slug_uses_xai_reasoning_accounting() -> None:
    result = completion_tokens_for_cost(
        "file://../providers/video_understanding_provider.py",
        {
            "prompt": 100,
            "completion": 20,
            "total": 1120,
            "completionDetails": {"reasoning": 1000},
        },
        model_slug="grok-4.5",
        raw_usage={
            "prompt_tokens": 100,
            "completion_tokens": 20,
            "total_tokens": 1120,
            "completion_tokens_details": {"reasoning_tokens": 1000},
        },
    )

    assert result == 1020


def test_raw_non_gemini_usage_mismatch_is_rejected() -> None:
    with pytest.raises(ValueError, match="raw provider usage does not match"):
        completion_tokens_for_cost(
            "openai:gpt-5.5",
            {"prompt": 100, "completion": 20, "total": 120},
            raw_usage={
                "prompt_tokens": 100,
                "completion_tokens": 19,
                "total_tokens": 119,
            },
        )


@pytest.mark.parametrize(
    "token_usage",
    [
        {"prompt": "100", "completion": 20, "total": 120},
        {"prompt": 100, "completion": -1, "total": 99},
        {"prompt": 100, "completion": 20, "total": 119},
        {"prompt": 100, "completion": True, "total": 101},
    ],
)
def test_non_gemini_eval_usage_rejects_coercion_and_bad_totals(
    token_usage: dict[str, object],
) -> None:
    with pytest.raises(ValueError):
        completion_tokens_for_cost("openai:gpt-5.5", token_usage)
