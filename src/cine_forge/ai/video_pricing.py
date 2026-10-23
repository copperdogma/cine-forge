"""Checked prices for qualified video transports; absence never means free."""

from __future__ import annotations

from datetime import date

from cine_forge.schemas.media_cost import VideoPrice

XAI_VIDEO_PRICE_SOURCE = "https://docs.x.ai/developers/models/grok-imagine-video"
VIDEO_PRICE_CHECKED_ON = date(2026, 10, 23)


class VideoPricingError(ValueError):
    """The requested transport has no qualified, current execution price."""


def validate_video_target(*, provider: str, model: str) -> None:
    """Reject retired and unqualified targets before any paid prerequisite."""
    if provider == "openai" and model.startswith("sora-2"):
        raise VideoPricingError(
            f"OpenAI {model} is unavailable: Sora 2 Videos API shut down 2026-09-24"
        )
    if provider == "google" and model.startswith("veo-3.1-") and "preview" in model:
        raise VideoPricingError(
            f"Google {model} is unavailable: Veo 3.1 preview shut down 2026-10-22"
        )
    if (provider, model) != ("xai", "grok-imagine-video"):
        raise VideoPricingError(f"No qualified current video price for {provider}/{model}")


def resolve_video_price(*, provider: str, model: str, resolution: str) -> VideoPrice:
    """Resolve the exact prompt-only output rate, never a benchmark rate."""
    validate_video_target(provider=provider, model=model)
    rates = {"480p": 0.05, "720p": 0.07}
    if resolution not in rates:
        raise VideoPricingError(
            f"No qualified current video price for {provider}/{model} at {resolution}"
        )
    return VideoPrice(
        provider=provider,
        model=model,
        resolution=resolution,
        unit_price_usd=rates[resolution],
        source_url=XAI_VIDEO_PRICE_SOURCE,
        checked_on=VIDEO_PRICE_CHECKED_ON,
    )
