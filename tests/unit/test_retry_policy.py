"""Unit tests for StageRetryPolicy."""

from __future__ import annotations

import pytest

from cine_forge.driver.retry_policy import StageRetryPolicy


@pytest.mark.unit
def test_build_attempt_plan_returns_primary_model() -> None:
    plan = StageRetryPolicy.build_stage_model_attempt_plan(
        stage_id="custom_stage",
        stage_params={"model": "gpt-4.1"},
    )
    assert plan[0] == "gpt-4.1"
    assert len(plan) >= 1


@pytest.mark.unit
def test_build_attempt_plan_includes_fallback_for_known_stage() -> None:
    plan = StageRetryPolicy.build_stage_model_attempt_plan(
        stage_id="normalize",
        stage_params={"model": "claude-haiku-4-5-20251001"},
    )
    # Should include the primary + fallback models from _DEFAULT_STAGE_FALLBACK_MODELS
    assert plan[0] == "claude-haiku-4-5-20251001"
    assert len(plan) > 1


@pytest.mark.unit
def test_build_attempt_plan_respects_max_attempts() -> None:
    plan = StageRetryPolicy.build_stage_model_attempt_plan(
        stage_id="normalize",
        stage_params={"model": "claude-haiku-4-5-20251001"},
        max_attempts=2,
    )
    assert len(plan) <= 2


@pytest.mark.unit
def test_build_attempt_plan_uses_fallback_override() -> None:
    plan = StageRetryPolicy.build_stage_model_attempt_plan(
        stage_id="normalize",
        stage_params={"model": "gpt-4.1"},
        fallback_overrides={"normalize": ["custom-fallback-1", "custom-fallback-2"]},
    )
    assert "custom-fallback-1" in plan
    assert "custom-fallback-2" in plan


@pytest.mark.unit
def test_is_retryable_returns_false_for_value_error() -> None:
    assert StageRetryPolicy.is_retryable_stage_error(ValueError("bad input")) is False


@pytest.mark.unit
def test_next_healthy_index_skips_unhealthy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        StageRetryPolicy,
        "provider_is_healthy",
        staticmethod(lambda provider: provider != "anthropic"),
    )
    plan = ["claude-sonnet-4-6", "gpt-4.1", "gemini-2.5-flash"]
    idx = StageRetryPolicy.next_healthy_attempt_index(plan, 0)
    # Should skip claude (anthropic) and return index of gpt-4.1 (openai)
    assert idx == 1


@pytest.mark.unit
def test_max_attempts_uses_default() -> None:
    result = StageRetryPolicy.max_attempts_for_stage("some_stage", 3)
    assert result == 3


@pytest.mark.unit
def test_max_attempts_uses_override() -> None:
    result = StageRetryPolicy.max_attempts_for_stage(
        "normalize", 3, stage_overrides={"normalize": 5}
    )
    assert result == 5


@pytest.mark.unit
def test_fallback_retry_delay_exponential() -> None:
    d0 = StageRetryPolicy.fallback_retry_delay_seconds(0, 1.0, 0.0)
    d1 = StageRetryPolicy.fallback_retry_delay_seconds(1, 1.0, 0.0)
    d2 = StageRetryPolicy.fallback_retry_delay_seconds(2, 1.0, 0.0)
    assert d0 == 1.0
    assert d1 == 2.0
    assert d2 == 4.0


@pytest.mark.unit
def test_extract_error_code() -> None:
    assert StageRetryPolicy.extract_error_code("HTTP 429 Too Many Requests") == "429"
    assert StageRetryPolicy.extract_error_code("no code here") is None


@pytest.mark.unit
def test_extract_request_id() -> None:
    assert StageRetryPolicy.extract_request_id("Error req_abc123 failed") == "req_abc123"
    assert StageRetryPolicy.extract_request_id("no request id") is None


@pytest.mark.unit
def test_provider_from_model() -> None:
    assert StageRetryPolicy.provider_from_model("claude-sonnet-4-6") == "anthropic"
    assert StageRetryPolicy.provider_from_model("gpt-4.1") == "openai"
    assert StageRetryPolicy.provider_from_model("gemini-2.5-flash") == "google"
    assert StageRetryPolicy.provider_from_model("custom-local") == "code"


@pytest.mark.unit
def test_terminal_reason_non_retryable() -> None:
    state = {"attempts": [{"transient": False}]}
    assert StageRetryPolicy.terminal_reason(state) == "non_retryable_error"


@pytest.mark.unit
def test_terminal_reason_budget_exhausted() -> None:
    state = {"attempts": [{"transient": True}]}
    assert StageRetryPolicy.terminal_reason(state) == "retry_budget_exhausted_or_no_fallback"


@pytest.mark.unit
def test_terminal_reason_no_attempts() -> None:
    assert StageRetryPolicy.terminal_reason({}) == "module_error"
