"""Fail-closed token-usage contracts shared by runtime and eval transports."""

from __future__ import annotations

from dataclasses import dataclass

_MISSING = object()


@dataclass(frozen=True)
class GeminiTokenUsage:
    """Validated Gemini usage with visible and billable output kept distinct."""

    prompt: int
    visible_completion: int
    reported_reasoning_completion: int | None
    hidden_completion: int
    total: int
    billed_completion: int


@dataclass(frozen=True)
class StandardTokenUsage:
    """Validated non-Gemini usage with hidden output kept explicit."""

    prompt: int
    visible_completion: int
    reported_reasoning_completion: int | None
    hidden_completion: int
    total: int
    billed_completion: int


def validate_standard_token_usage(
    *,
    prompt_tokens: object,
    completion_tokens: object,
    total_tokens: object = _MISSING,
    reasoning_completion_tokens: object = _MISSING,
    allow_total_derived_hidden: bool = False,
) -> StandardTokenUsage:
    """Validate OpenAI-compatible or Anthropic token counters exactly."""
    prompt = validate_token_count(prompt_tokens, "prompt_tokens")
    visible_completion = validate_token_count(
        completion_tokens,
        "completion_tokens",
    )
    reported_reasoning: int | None = None
    if reasoning_completion_tokens is not _MISSING:
        reported_reasoning = validate_token_count(
            reasoning_completion_tokens,
            "reasoning_completion_tokens",
        )

    minimum_total = prompt + visible_completion
    if total_tokens is _MISSING:
        hidden_completion = (
            (reported_reasoning or 0) if allow_total_derived_hidden else 0
        )
        total = minimum_total + hidden_completion
    else:
        total = validate_token_count(total_tokens, "total_tokens")
        if total < minimum_total:
            raise ValueError("total_tokens must be at least prompt_tokens + completion_tokens")
        hidden_completion = total - minimum_total
        if allow_total_derived_hidden:
            if (
                reported_reasoning is not None
                and reported_reasoning != hidden_completion
            ):
                raise ValueError(
                    "total_tokens does not reconcile with prompt_tokens + "
                    "completion_tokens + reasoning_completion_tokens"
                )
        elif hidden_completion:
            raise ValueError(
                "total_tokens does not reconcile with prompt_tokens + completion_tokens"
            )
    if (
        reported_reasoning is not None
        and not allow_total_derived_hidden
        and reported_reasoning > visible_completion
    ):
        raise ValueError(
            "reasoning_completion_tokens must not exceed completion_tokens"
        )

    return StandardTokenUsage(
        prompt=prompt,
        visible_completion=visible_completion,
        reported_reasoning_completion=reported_reasoning,
        hidden_completion=hidden_completion,
        total=total,
        billed_completion=visible_completion + hidden_completion,
    )


def validate_gemini_token_usage(
    *,
    prompt_tokens: object,
    visible_completion_tokens: object,
    total_tokens: object = _MISSING,
    reasoning_completion_tokens: object = _MISSING,
    billed_completion_tokens: object = _MISSING,
) -> GeminiTokenUsage:
    """Validate Gemini counters and derive hidden-thinking-inclusive output.

    Gemini may report visible candidates, hidden reasoning, and a total. When
    reasoning and total are both present they are redundant evidence and must
    agree exactly. When total is absent, explicit reasoning still contributes
    to billable completion. Legacy responses with neither field retain the
    visible-only behavior.
    """
    prompt = validate_token_count(prompt_tokens, "prompt_tokens")
    visible_completion = validate_token_count(
        visible_completion_tokens,
        "visible_completion_tokens",
    )
    reported_reasoning: int | None = None
    if reasoning_completion_tokens is not _MISSING:
        reported_reasoning = validate_token_count(
            reasoning_completion_tokens,
            "reasoning_completion_tokens",
        )

    minimum_total = prompt + visible_completion
    if total_tokens is _MISSING:
        hidden_completion = reported_reasoning or 0
        total = minimum_total + hidden_completion
    else:
        total = validate_token_count(total_tokens, "total_tokens")
        if total < minimum_total:
            raise ValueError(
                "total_tokens must be at least prompt_tokens + "
                "visible_completion_tokens"
            )
        hidden_completion = total - minimum_total
        if (
            reported_reasoning is not None
            and reported_reasoning != hidden_completion
        ):
            raise ValueError(
                "total_tokens does not reconcile with prompt_tokens + "
                "visible_completion_tokens + reasoning_completion_tokens"
            )

    billed_completion = visible_completion + hidden_completion
    if billed_completion_tokens is not _MISSING:
        supplied_billed = validate_token_count(
            billed_completion_tokens,
            "billed_completion_tokens",
        )
        if supplied_billed != billed_completion:
            raise ValueError(
                "billed_completion_tokens does not match validated Gemini usage"
            )

    return GeminiTokenUsage(
        prompt=prompt,
        visible_completion=visible_completion,
        reported_reasoning_completion=reported_reasoning,
        hidden_completion=hidden_completion,
        total=total,
        billed_completion=billed_completion,
    )


def validate_token_count(value: object, name: str) -> int:
    """Require a real nonnegative integer token counter (never bool/string)."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be a nonnegative integer")
    if value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")
    return value


def aliased_token_count(
    mapping: dict,
    keys: tuple[str, ...],
    *,
    name: str,
) -> int | None:
    """Validate redundant counter aliases and require them to agree exactly."""
    evidence = [
        validate_token_count(mapping[key], f"{name}.{key}")
        for key in keys
        if key in mapping
    ]
    if not evidence:
        return None
    if any(value != evidence[0] for value in evidence[1:]):
        raise ValueError(f"{name} aliases do not match")
    return evidence[0]
