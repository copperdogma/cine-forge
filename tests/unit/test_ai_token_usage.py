"""Unit contracts for fail-closed Gemini token arithmetic."""

from __future__ import annotations

import pytest

from cine_forge.ai.token_usage import (
    validate_gemini_token_usage,
    validate_standard_token_usage,
)

pytestmark = pytest.mark.unit


def test_redundant_visible_reasoning_and_total_evidence_reconciles() -> None:
    usage = validate_gemini_token_usage(
        prompt_tokens=100,
        visible_completion_tokens=10,
        reasoning_completion_tokens=1000,
        total_tokens=1110,
    )

    assert usage.visible_completion == 10
    assert usage.reported_reasoning_completion == 1000
    assert usage.hidden_completion == 1000
    assert usage.billed_completion == 1010
    assert usage.total == 1110


def test_redundant_reasoning_and_total_mismatch_is_rejected() -> None:
    with pytest.raises(ValueError, match="does not reconcile"):
        validate_gemini_token_usage(
            prompt_tokens=100,
            visible_completion_tokens=10,
            reasoning_completion_tokens=999,
            total_tokens=1110,
        )


def test_reasoning_is_billed_when_total_is_absent() -> None:
    usage = validate_gemini_token_usage(
        prompt_tokens=100,
        visible_completion_tokens=10,
        reasoning_completion_tokens=1000,
    )

    assert usage.total == 1110
    assert usage.hidden_completion == 1000
    assert usage.billed_completion == 1010


def test_total_can_reveal_hidden_output_without_reasoning_breakdown() -> None:
    usage = validate_gemini_token_usage(
        prompt_tokens=100,
        visible_completion_tokens=10,
        total_tokens=1110,
    )

    assert usage.reported_reasoning_completion is None
    assert usage.hidden_completion == 1000
    assert usage.billed_completion == 1010


def test_legacy_visible_only_usage_is_preserved() -> None:
    usage = validate_gemini_token_usage(
        prompt_tokens=100,
        visible_completion_tokens=10,
    )

    assert usage.reported_reasoning_completion is None
    assert usage.hidden_completion == 0
    assert usage.total == 110
    assert usage.billed_completion == 10


@pytest.mark.parametrize(
    ("prompt", "completion", "total", "message"),
    [
        ("100", 10, 110, "prompt_tokens must be a nonnegative integer"),
        (True, 10, 11, "prompt_tokens must be a nonnegative integer"),
        (100, -1, 99, "completion_tokens must be a nonnegative integer"),
        (100, 1.5, 101, "completion_tokens must be a nonnegative integer"),
        (100, 10, "110", "total_tokens must be a nonnegative integer"),
    ],
)
def test_standard_usage_rejects_coerced_or_negative_counters(
    prompt: object,
    completion: object,
    total: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        validate_standard_token_usage(
            prompt_tokens=prompt,
            completion_tokens=completion,
            total_tokens=total,
        )


def test_standard_usage_requires_exact_total_without_hidden_output() -> None:
    with pytest.raises(ValueError, match="does not reconcile"):
        validate_standard_token_usage(
            prompt_tokens=100,
            completion_tokens=10,
            total_tokens=111,
        )


def test_xai_style_standard_usage_reconciles_reasoning_and_total() -> None:
    usage = validate_standard_token_usage(
        prompt_tokens=100,
        completion_tokens=10,
        reasoning_completion_tokens=1000,
        total_tokens=1110,
        allow_total_derived_hidden=True,
    )

    assert usage.hidden_completion == 1000
    assert usage.billed_completion == 1010


def test_xai_style_standard_usage_rejects_reasoning_total_contradiction() -> None:
    with pytest.raises(ValueError, match="does not reconcile"):
        validate_standard_token_usage(
            prompt_tokens=100,
            completion_tokens=10,
            reasoning_completion_tokens=999,
            total_tokens=1110,
            allow_total_derived_hidden=True,
        )
