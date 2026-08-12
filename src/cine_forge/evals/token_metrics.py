"""Token evidence reconciliation for evaluation cost metrics."""

from __future__ import annotations

from cine_forge.ai.token_usage import (
    GeminiTokenUsage,
    StandardTokenUsage,
    aliased_token_count,
    validate_gemini_token_usage,
    validate_standard_token_usage,
    validate_token_count,
)


def completion_tokens_for_cost(
    provider_id: str,
    token_usage: dict,
    *,
    model_slug: str | None = None,
    raw_usage_metadata: dict | None = None,
    raw_usage: dict | None = None,
) -> int:
    """Return billable output tokens without overwriting visible completion tokens."""
    if is_gemini_provider(provider_id, model_slug=model_slug):
        return reconcile_gemini_usage(
            token_usage,
            raw_usage_metadata=raw_usage_metadata,
        ).billed_completion

    is_xai = is_xai_provider(provider_id, model_slug=model_slug)
    usage = reconcile_standard_usage(
        token_usage,
        raw_usage=raw_usage,
        allow_total_derived_hidden=is_xai,
    )
    return usage.billed_completion if is_xai else usage.visible_completion


def reconcile_standard_usage(
    token_usage: dict,
    *,
    raw_usage: dict | None = None,
    allow_total_derived_hidden: bool,
) -> StandardTokenUsage:
    """Validate normalized non-Gemini usage and optional raw evidence."""
    normalized = _validated_normalized_standard_usage(
        token_usage,
        allow_total_derived_hidden=allow_total_derived_hidden,
    )
    if raw_usage is None:
        return normalized
    raw = _validated_raw_standard_usage(
        raw_usage,
        allow_total_derived_hidden=allow_total_derived_hidden,
    )
    normalized_core = (
        normalized.prompt,
        normalized.visible_completion,
        normalized.hidden_completion,
        normalized.total,
        normalized.billed_completion,
    )
    raw_core = (
        raw.prompt,
        raw.visible_completion,
        raw.hidden_completion,
        raw.total,
        raw.billed_completion,
    )
    reasoning_mismatch = (
        normalized.reported_reasoning_completion is not None
        and raw.reported_reasoning_completion
        != normalized.reported_reasoning_completion
    )
    if raw_core != normalized_core or reasoning_mismatch:
        raise ValueError("raw provider usage does not match normalized tokenUsage")
    # Promptfoo may strip completionDetails from a custom provider's normalized
    # tokenUsage while retaining the provider-owned raw response. In that case
    # the raw reasoning count is strictly stronger replay evidence, provided all
    # billable counters still reconcile exactly.
    return raw


def reconcile_gemini_usage(
    token_usage: dict,
    *,
    raw_usage_metadata: dict | None = None,
) -> GeminiTokenUsage:
    """Validate normalized Gemini usage and reconcile raw provider evidence."""
    normalized = _validated_normalized_gemini_usage(token_usage)
    if raw_usage_metadata is None:
        return normalized
    raw = _validated_raw_gemini_usage(raw_usage_metadata)
    normalized_core = (
        normalized.prompt,
        normalized.visible_completion,
        normalized.total,
        normalized.billed_completion,
    )
    raw_core = (
        raw.prompt,
        raw.visible_completion,
        raw.total,
        raw.billed_completion,
    )
    if normalized_core != raw_core:
        raise ValueError(
            "raw Gemini usageMetadata does not match normalized tokenUsage"
        )
    return normalized


def is_gemini_provider(provider_id: str, *, model_slug: str | None = None) -> bool:
    """Return whether retained identity evidence names a Gemini provider lane."""
    provider_key = provider_id.lower()
    return (
        "google:" in provider_key
        or "gemini" in provider_key
        or (model_slug or "").startswith("gemini-")
    )


def is_xai_provider(provider_id: str, *, model_slug: str | None = None) -> bool:
    """Return whether retained identity evidence names an xAI provider lane."""
    provider_key = provider_id.lower()
    model_key = (model_slug or "").lower()
    return "xai:" in provider_key or "grok" in provider_key or model_key.startswith("grok-")


def raw_gemini_usage_metadata(
    response: dict, *, required: bool = False
) -> dict | None:
    """Return raw Gemini usage metadata when retained by Promptfoo."""
    raw = response.get("raw")
    if not isinstance(raw, dict):
        if required:
            raise ValueError("raw Gemini provider response must be retained as a mapping")
        return None
    if "usageMetadata" not in raw:
        if required:
            raise ValueError("raw Gemini provider response must retain usageMetadata")
        return None
    for key in ("responseId", "modelVersion"):
        value = raw.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"raw Gemini provider response must retain non-empty {key}"
            )
    usage_metadata = raw["usageMetadata"]
    if not isinstance(usage_metadata, dict):
        raise ValueError("raw Gemini usageMetadata must be a mapping")
    return usage_metadata


def raw_standard_usage(response: dict) -> dict | None:
    """Return retained non-Gemini raw usage when the transport exposes it."""
    raw = response.get("raw")
    if not isinstance(raw, dict) or "usage" not in raw:
        return None
    usage = raw["usage"]
    if not isinstance(usage, dict):
        raise ValueError("raw provider usage must be a mapping")
    return usage


def _validated_normalized_gemini_usage(token_usage: dict) -> GeminiTokenUsage:
    optional_usage: dict[str, object] = {}
    if "total" in token_usage:
        optional_usage["total_tokens"] = token_usage["total"]
    if "billed_completion" in token_usage:
        optional_usage["billed_completion_tokens"] = token_usage[
            "billed_completion"
        ]
    reasoning = _reasoning_token_evidence(
        token_usage.get("completionDetails"),
        field_name="completionDetails",
    )
    if reasoning is not None:
        optional_usage["reasoning_completion_tokens"] = reasoning
    return validate_gemini_token_usage(
        prompt_tokens=token_usage.get("prompt"),
        visible_completion_tokens=token_usage.get("completion"),
        **optional_usage,
    )


def _validated_raw_gemini_usage(usage_metadata: dict) -> GeminiTokenUsage:
    optional_usage: dict[str, object] = {}
    if "totalTokenCount" in usage_metadata:
        optional_usage["total_tokens"] = usage_metadata["totalTokenCount"]
    reasoning = _aliased_token_evidence(
        usage_metadata,
        ("thoughtsTokenCount", "reasoningTokenCount"),
        field_name="raw Gemini reasoning tokens",
    )
    if reasoning is not None:
        optional_usage["reasoning_completion_tokens"] = reasoning
    if "total_tokens" not in optional_usage and reasoning is None:
        raise ValueError(
            "raw Gemini usage must retain totalTokenCount or reasoning-token evidence"
        )
    return validate_gemini_token_usage(
        prompt_tokens=usage_metadata.get("promptTokenCount"),
        visible_completion_tokens=usage_metadata.get("candidatesTokenCount"),
        **optional_usage,
    )


def _validated_normalized_standard_usage(
    token_usage: dict,
    *,
    allow_total_derived_hidden: bool,
) -> StandardTokenUsage:
    if not isinstance(token_usage, dict):
        raise ValueError("tokenUsage must be a mapping")
    optional: dict[str, object] = {}
    if "total" in token_usage:
        optional["total_tokens"] = token_usage["total"]
    reasoning = _reasoning_token_evidence(
        token_usage.get("completionDetails"),
        field_name="completionDetails",
    )
    if reasoning is not None:
        optional["reasoning_completion_tokens"] = reasoning
    return validate_standard_token_usage(
        prompt_tokens=token_usage.get("prompt"),
        completion_tokens=token_usage.get("completion"),
        allow_total_derived_hidden=allow_total_derived_hidden,
        **optional,
    )


def _validated_raw_standard_usage(
    raw_usage: dict,
    *,
    allow_total_derived_hidden: bool,
) -> StandardTokenUsage:
    if not isinstance(raw_usage, dict):
        raise ValueError("raw provider usage must be a mapping")
    prompt = aliased_token_count(
        raw_usage,
        ("prompt_tokens", "input_tokens"),
        name="raw prompt tokens",
    )
    completion = aliased_token_count(
        raw_usage,
        ("completion_tokens", "output_tokens"),
        name="raw completion tokens",
    )
    optional: dict[str, object] = {}
    if "total_tokens" in raw_usage:
        optional["total_tokens"] = raw_usage["total_tokens"]
    reasoning = _raw_standard_reasoning_evidence(raw_usage)
    if reasoning is not None:
        optional["reasoning_completion_tokens"] = reasoning
    # xAI Responses reports output_tokens as the billed total inclusive of
    # reasoning, unlike xAI Chat Completions where completion_tokens is visible
    # output and reasoning is additional. Normalize only the unambiguous
    # Responses shape before applying the shared reconciliation contract.
    if (
        allow_total_derived_hidden
        and "output_tokens" in raw_usage
        and "completion_tokens" not in raw_usage
        and reasoning is not None
        and completion is not None
    ):
        completion -= validate_token_count(
            reasoning,
            "raw output_tokens_details.reasoning_tokens",
        )
        if completion < 0:
            raise ValueError("raw xAI reasoning tokens exceed output_tokens")
    return validate_standard_token_usage(
        prompt_tokens=prompt,
        completion_tokens=completion,
        allow_total_derived_hidden=allow_total_derived_hidden,
        **optional,
    )


def _raw_standard_reasoning_evidence(raw_usage: dict) -> object | None:
    evidence: list[object] = []
    for key in ("completion_tokens_details", "output_tokens_details"):
        if key not in raw_usage:
            continue
        reasoning = _reasoning_token_evidence(
            raw_usage[key],
            field_name=f"raw {key}",
        )
        if reasoning is not None:
            evidence.append(reasoning)
    if not evidence:
        return None
    if any(value != evidence[0] for value in evidence[1:]):
        raise ValueError("raw reasoning-token detail aliases do not match")
    return evidence[0]


def _reasoning_token_evidence(value: object, *, field_name: str) -> object | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a mapping")
    return _aliased_token_evidence(
        value,
        ("reasoning", "reasoning_tokens"),
        field_name=f"{field_name} reasoning tokens",
    )


def _aliased_token_evidence(
    mapping: dict,
    keys: tuple[str, ...],
    *,
    field_name: str,
) -> object | None:
    evidence = [mapping[key] for key in keys if key in mapping]
    if not evidence:
        return None
    if any(value != evidence[0] for value in evidence[1:]):
        raise ValueError(f"{field_name} aliases do not match")
    return evidence[0]
