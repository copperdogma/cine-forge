"""Translate provider failures into actionable chat notifications."""

from __future__ import annotations

import time
from collections.abc import Iterable
from typing import Any

from cine_forge.driver.retry_policy import StageRetryPolicy

_PROVIDER_LABELS = {
    "anthropic": "Anthropic",
    "google": "Google",
    "openai": "OpenAI",
}

_BILLING_TOKENS = (
    "balance is too low",
    "billing",
    "billing hard limit",
    "credit balance",
    "credits",
    "exceeded your current quota",
    "insufficient balance",
    "insufficient quota",
    "payment required",
    "quota exceeded",
    "top up",
)
_AUTH_TOKENS = (
    "api key expired",
    "api key invalid",
    "api key revoked",
    "auth expired",
    "authentication failed",
    "authentication required",
    "expired access token",
    "expired api key",
    "incorrect api key",
    "invalid api key",
    "invalid authentication",
    "invalid x-api-key",
    "key expired",
    "token expired",
    "unauthorized",
)
_RATE_LIMIT_TOKENS = (
    "capacity",
    "overloaded",
    "rate limit",
    "resource exhausted",
    "temporarily unavailable",
    "too many requests",
    "try again later",
)


def build_provider_failure_chat_message(
    *,
    run_id: str,
    exc: Exception,
    run_state: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Build an actionable chat message for user-fixable provider failures."""
    stage_id, stage_state = _latest_failed_stage(run_state)
    attempt = _latest_failed_attempt(stage_state)
    failure_kind = classify_provider_failure(exc=exc, stage_state=stage_state, attempt=attempt)
    if failure_kind is None:
        return None

    provider = _provider_for_failure(stage_state=stage_state, attempt=attempt)
    provider_label = _provider_label(provider)
    stage_label = _stage_label(stage_id)
    context_line = _context_line(
        provider_label=provider_label,
        stage_label=stage_label,
        run_id=run_id,
        request_id=_request_id(exc=exc, attempt=attempt),
    )

    if failure_kind == "quota":
        content = (
            f"{context_line}\n\n"
            f"{provider_label} billing or quota blocked this run. "
            "Top up credits or raise the provider spending limit, then retry from run details."
        )
    elif failure_kind == "auth":
        content = (
            f"{context_line}\n\n"
            f"{provider_label} rejected the credentials for this run. "
            "Refresh or replace the API key for that provider, then retry from run details."
        )
    else:
        content = (
            f"{context_line}\n\n"
            f"{provider_label} is rate-limiting requests or is temporarily overloaded. "
            "Wait a moment, then retry from run details."
        )

    stage_fragment = stage_id or "run"
    provider_fragment = provider or "provider"
    return {
        "id": f"provider_failure_{run_id}_{stage_fragment}_{failure_kind}_{provider_fragment}",
        "type": "ai_suggestion",
        "content": content,
        "timestamp": time.time(),
        "actions": [
            {
                "id": "view_run_details",
                "label": "View Run Details",
                "variant": "outline",
                "route": f"runs/{run_id}",
            }
        ],
        "needsAction": True,
        "route": f"runs/{run_id}",
    }


def classify_provider_failure(
    *,
    exc: Exception,
    stage_state: dict[str, Any] | None,
    attempt: dict[str, Any] | None,
) -> str | None:
    """Return the actionable provider-failure kind, if this looks user-fixable."""
    message = " ".join(_message_parts(exc=exc, stage_state=stage_state, attempt=attempt))
    error_code = _error_code(exc=exc, attempt=attempt)
    is_transient = bool(attempt.get("transient")) if isinstance(attempt, dict) else False

    if _contains_any(message, _BILLING_TOKENS) or error_code == "402":
        return "quota"

    if _contains_any(message, _AUTH_TOKENS):
        return "auth"

    if error_code == "401":
        return "auth"

    if error_code == "403" and _contains_any(
        message,
        ("auth", "credential", "key", "token"),
    ):
        return "auth"

    if _contains_any(message, _RATE_LIMIT_TOKENS) or error_code in {"429", "529"}:
        return "rate_limit"

    if is_transient and error_code is not None:
        return "rate_limit"

    return None


def _latest_failed_stage(
    run_state: dict[str, Any] | None,
) -> tuple[str | None, dict[str, Any] | None]:
    if not isinstance(run_state, dict):
        return None, None

    stages = run_state.get("stages")
    if not isinstance(stages, dict):
        return None, None

    ordered_ids: list[str] = []
    raw_stage_order = run_state.get("stage_order")
    if isinstance(raw_stage_order, list):
        ordered_ids.extend(str(stage_id) for stage_id in raw_stage_order if str(stage_id) in stages)
    ordered_ids.extend(
        str(stage_id) for stage_id in stages.keys() if str(stage_id) not in ordered_ids
    )

    for stage_id in reversed(ordered_ids):
        raw_stage_state = stages.get(stage_id)
        if not isinstance(raw_stage_state, dict):
            continue
        if raw_stage_state.get("status") == "failed":
            return stage_id, raw_stage_state

    for stage_id in reversed(ordered_ids):
        raw_stage_state = stages.get(stage_id)
        if not isinstance(raw_stage_state, dict):
            continue
        if _latest_failed_attempt(raw_stage_state) is not None:
            return stage_id, raw_stage_state

    return None, None


def _latest_failed_attempt(stage_state: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(stage_state, dict):
        return None
    attempts = stage_state.get("attempts")
    if not isinstance(attempts, list):
        return None
    for raw_attempt in reversed(attempts):
        if not isinstance(raw_attempt, dict):
            continue
        if raw_attempt.get("status") == "failed" or raw_attempt.get("error"):
            return raw_attempt
    return None


def _message_parts(
    *,
    exc: Exception,
    stage_state: dict[str, Any] | None,
    attempt: dict[str, Any] | None,
) -> Iterable[str]:
    yield str(exc).lower()
    if isinstance(attempt, dict) and attempt.get("error"):
        yield str(attempt["error"]).lower()
    if isinstance(stage_state, dict) and stage_state.get("final_error_class"):
        yield str(stage_state["final_error_class"]).lower()


def _error_code(*, exc: Exception, attempt: dict[str, Any] | None) -> str | None:
    if isinstance(attempt, dict) and attempt.get("error_code"):
        return str(attempt["error_code"])
    return StageRetryPolicy.extract_error_code(str(exc))


def _request_id(*, exc: Exception, attempt: dict[str, Any] | None) -> str | None:
    if isinstance(attempt, dict) and attempt.get("request_id"):
        return str(attempt["request_id"])
    return StageRetryPolicy.extract_request_id(str(exc))


def _provider_for_failure(
    *,
    stage_state: dict[str, Any] | None,
    attempt: dict[str, Any] | None,
) -> str | None:
    if isinstance(attempt, dict) and attempt.get("provider"):
        return _normalize_provider(str(attempt["provider"]))
    if isinstance(stage_state, dict) and stage_state.get("model_used"):
        return _normalize_provider(
            StageRetryPolicy.provider_from_model(str(stage_state["model_used"]))
        )
    return None


def _normalize_provider(provider: str) -> str | None:
    lowered = provider.strip().lower()
    if not lowered:
        return None
    if lowered in {"google", "gemini"}:
        return "google"
    if lowered in {"openai", "gpt"}:
        return "openai"
    if lowered in {"anthropic", "claude"}:
        return "anthropic"
    if lowered == "code":
        return None
    return lowered


def _provider_label(provider: str | None) -> str:
    if provider is None:
        return "Your AI provider"
    return _PROVIDER_LABELS.get(provider, provider.title())


def _stage_label(stage_id: str | None) -> str | None:
    if stage_id is None:
        return None
    return stage_id.replace("_", " ")


def _context_line(
    *,
    provider_label: str,
    stage_label: str | None,
    run_id: str,
    request_id: str | None,
) -> str:
    if stage_label:
        context = f"{provider_label} failed during the `{stage_label}` stage in run `{run_id}`."
    else:
        context = f"{provider_label} failed during run `{run_id}`."
    if request_id:
        context += f" Request ID: `{request_id}`."
    return context


def _contains_any(message: str, tokens: Iterable[str]) -> bool:
    return any(token in message for token in tokens)
