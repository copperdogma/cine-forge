"""Shared provider-failure taxonomy for transport and operator surfaces."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Literal

ProviderFailureStatus = Literal[
    "auth_failed",
    "network_error",
    "policy_blocked",
    "permission_failed",
    "provider_error",
    "quota_failed",
    "rate_limited",
]

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
    "api key is required",
    "api key expired",
    "api key invalid",
    "api key not valid",
    "api key revoked",
    "auth expired",
    "authentication failed",
    "authentication required",
    "api key is not set",
    "api key not set",
    "api_key is not set",
    "api_key) is not set",
    "expired access token",
    "expired api key",
    "incorrect api key",
    "invalid api key",
    "invalid authentication",
    "invalid x-api-key",
    "key expired",
    "missing api key",
    "token expired",
    "unauthorized",
)
_POLICY_TOKENS = (
    "blocked by safety",
    "content policy",
    "filtered for safety",
    "moderation",
    "policy violation",
    "prompt was rejected",
    "rai",
    "responsible ai",
    "safety policy",
)
_PERMISSION_TOKENS = (
    "access denied",
    "does not have access",
    "forbidden",
    "insufficient permissions",
    "not allowed",
    "permission denied",
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


def classify_provider_failure_status(
    *,
    message: str,
    error_code: str | None,
    is_transient: bool = False,
) -> ProviderFailureStatus | None:
    """Classify a provider failure into a small actionable taxonomy."""
    normalized_message = message.lower()

    if _contains_any(normalized_message, _BILLING_TOKENS) or error_code == "402":
        return "quota_failed"

    if _contains_any(normalized_message, _AUTH_TOKENS):
        return "auth_failed"

    if error_code == "401":
        return "auth_failed"

    if _contains_any(normalized_message, _PERMISSION_TOKENS):
        return "permission_failed"

    if error_code == "403":
        return "permission_failed"

    if _contains_any(normalized_message, _POLICY_TOKENS):
        return "policy_blocked"

    if _contains_any(normalized_message, _RATE_LIMIT_TOKENS) or error_code in {"429", "529"}:
        return "rate_limited"

    if is_transient and error_code is not None:
        return "rate_limited"

    return None


def _contains_any(message: str, tokens: Iterable[str]) -> bool:
    return any(token in message for token in tokens)
