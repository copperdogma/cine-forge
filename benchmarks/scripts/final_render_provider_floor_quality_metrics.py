"""Promptfoo response accounting contract for final-render quality evidence."""

from __future__ import annotations

import math
from typing import Any

from cine_forge.ai.errors import LLMCallError
from cine_forge.ai.llm import estimate_cost_usd
from cine_forge.ai.model_identity import (
    ProviderResponseIdentity,
    validate_provider_response_identity,
)
from cine_forge.evals.token_metrics import reconcile_standard_usage


def validated_response_metrics(
    *,
    entry: dict[str, Any],
    response: dict[str, Any],
    max_completion_tokens: int,
) -> tuple[float, float] | None:
    """Reconcile duplicated timing, cost, usage, and current price evidence."""
    if not _positive_fields(entry, ("latencyMs", "cost")):
        return None
    if not _positive_fields(response, ("latencyMs", "cost")):
        return None
    if not _same_number(response["latencyMs"], entry["latencyMs"]):
        return None
    if not _same_number(response["cost"], entry["cost"]):
        return None
    usage = response.get("tokenUsage")
    if not isinstance(usage, dict):
        return None
    required = {"prompt", "completion", "total"}
    allowed = {*required, "numRequests", "completionDetails"}
    if not required.issubset(usage) or not set(usage).issubset(allowed):
        return None
    if not all(_positive_integer(usage[key]) for key in required):
        return None
    prompt_tokens = int(usage["prompt"])
    completion_tokens = int(usage["completion"])
    if (
        not _positive_integer(max_completion_tokens)
        or completion_tokens > max_completion_tokens
        or int(usage["total"]) != prompt_tokens + completion_tokens
    ):
        return None
    if "numRequests" in usage and usage["numRequests"] != 1:
        return None
    details = usage.get("completionDetails")
    if details is not None and not _valid_completion_details(
        details, completion_tokens=completion_tokens
    ):
        return None
    metadata = response.get("metadata")
    if not isinstance(metadata, dict):
        return None
    identity = _raw_provider_evidence(
        response,
        usage=usage,
        metadata=metadata,
    )
    if identity is None:
        return None
    expected_cost = estimate_cost_usd(
        identity.billing_model,
        prompt_tokens,
        completion_tokens,
    )
    if not _same_number(response["cost"], expected_cost):
        return None
    return float(entry["latencyMs"]), float(entry["cost"])


def _raw_provider_evidence(
    response: dict[str, Any],
    *,
    usage: dict[str, Any],
    metadata: dict[str, Any],
) -> ProviderResponseIdentity | None:
    raw = response.get("raw")
    if not isinstance(raw, dict) or set(raw) != {"id", "model", "usage"}:
        return None
    provider = metadata.get("provider")
    requested_model = metadata.get("requested_model")
    if metadata.get("model") != requested_model:
        return None
    try:
        identity = validate_provider_response_identity(
            provider=provider,
            requested_model=requested_model,
            returned_model=raw.get("model"),
            request_id=raw.get("id"),
            require_returned=True,
        )
    except (LLMCallError, TypeError, ValueError):
        return None
    if (
        metadata.get("returned_model") != identity.returned_model
        or metadata.get("request_id") != identity.request_id
    ):
        return None
    raw_usage = raw.get("usage")
    if not isinstance(raw_usage, dict):
        return None
    try:
        reconcile_standard_usage(
            usage,
            raw_usage=raw_usage,
            allow_total_derived_hidden=False,
        )
    except ValueError:
        return None
    return identity


def _valid_completion_details(value: object, *, completion_tokens: int) -> bool:
    if not isinstance(value, dict) or not value:
        return False
    if not set(value).issubset({"reasoning"}):
        return False
    reasoning = value.get("reasoning")
    return _nonnegative_integer(reasoning) and int(reasoning) <= completion_tokens


def _positive_fields(payload: dict[str, Any], fields: tuple[str, ...]) -> bool:
    return all(_finite_positive(payload.get(field)) for field in fields)


def _finite_nonnegative(value: object) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(float(value))
        and float(value) >= 0.0
    )


def _finite_positive(value: object) -> bool:
    return _finite_nonnegative(value) and float(value) > 0.0


def _nonnegative_integer(value: object) -> bool:
    return not isinstance(value, bool) and isinstance(value, int) and value >= 0


def _positive_integer(value: object) -> bool:
    return _nonnegative_integer(value) and int(value) > 0


def _same_number(actual: object, expected: object) -> bool:
    return _finite_nonnegative(actual) and _finite_nonnegative(expected) and math.isclose(
        float(actual), float(expected), rel_tol=0.0, abs_tol=1e-6
    )
