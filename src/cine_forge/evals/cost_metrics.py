"""Pricing-derived evaluation cost checks."""

from __future__ import annotations

import math

# Pricing from src/cine_forge/ai/llm.py MODEL_PRICING_PER_M_TOKEN.
# Values are (input_per_M, output_per_M) in USD.
PRICING: dict[str, tuple[float, float]] = {
    "gpt-5.4": (2.5, 15.0),
    "gpt-5.5": (5.0, 30.0),
    "gpt-5.5-pro": (30.0, 180.0),
    "gpt-5.4-mini": (0.75, 4.5),
    "gpt-5.4-nano": (0.20, 1.25),
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-sonnet-4-5": (3.0, 15.0),
    "claude-sonnet-4-5-20250929": (3.0, 15.0),
    "claude-opus-4-6": (15.0, 75.0),
    "claude-opus-4-8": (5.0, 25.0),
    "claude-haiku-4-5-20251001": (0.80, 4.0),
    "gemini-3.1-flash-lite": (0.10, 0.40),
    "gemini-3.1-pro-preview": (1.50, 10.0),
    "gemini-3.5-flash": (1.50, 9.0),
    "gemini-3.5-flash-lite": (0.30, 2.50),
    "gemini-3.6-flash": (1.50, 7.50),
    "grok-4.3": (1.25, 2.50),
    "grok-4.5": (2.0, 6.0),
    "kimi-k2.6": (0.95, 4.0),
}

# Providers commonly round reported costs. Accept the larger of one micro-dollar
# or 1% of the derived usage cost; larger differences indicate stale pricing,
# mismatched usage, or a mislabeled provider and must fail closed.
REPORTED_COST_REL_TOLERANCE = 0.01
REPORTED_COST_ABS_TOLERANCE_USD = 0.000001


def estimate_cost(
    provider_id: str,
    prompt_tokens: int,
    completion_tokens: int,
) -> float | None:
    """Estimate cost from token counts when the provider reports no cost."""
    model_id = provider_id.rsplit(":", 1)[-1]
    return estimate_model_cost(model_id, prompt_tokens, completion_tokens)


def estimate_model_cost(
    model_id: str,
    prompt_tokens: int,
    completion_tokens: int,
) -> float | None:
    """Estimate cost for one resolved model slug."""
    pricing = PRICING.get(model_id)
    if not pricing:
        return None
    input_price, output_price = pricing
    return (prompt_tokens * input_price + completion_tokens * output_price) / 1_000_000


def validate_reported_cost(
    *,
    reported_cost: float | int,
    derived_cost: float | None,
    model_slug: str | None,
) -> None:
    """Reject known-model cost evidence outside the rounding tolerance."""
    if derived_cost is None:
        return
    if not math.isclose(
        float(reported_cost),
        derived_cost,
        rel_tol=REPORTED_COST_REL_TOLERANCE,
        abs_tol=REPORTED_COST_ABS_TOLERANCE_USD,
    ):
        raise ValueError(
            f"reported cost for {model_slug} does not match derived usage cost "
            f"within rel={REPORTED_COST_REL_TOLERANCE:g}, "
            f"abs=${REPORTED_COST_ABS_TOLERANCE_USD:g}"
        )
