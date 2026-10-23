"""Explicit fake transport receipts and prices for mechanical adapter tests only."""

from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest

from cine_forge.ai.video import VideoGenerationResult
from cine_forge.schemas import CostRecord
from cine_forge.schemas.media_cost import CostReceipt, VideoPrice


def fixture_video_result(*, fixture_cost_usd: float = 0.0, **kwargs) -> VideoGenerationResult:
    """Synthetic receipt, never evidence its named provider/model is available or priced."""
    if "cost_receipts" not in kwargs:
        model = kwargs["model_used"]
        kwargs["cost_receipts"] = [
            CostReceipt(
                receipt_id=f"mechanical-fixture:{uuid4()}",
                component="video",
                model=model,
                cost=CostRecord(
                    model=model,
                    input_tokens=0,
                    output_tokens=0,
                    estimated_cost_usd=fixture_cost_usd,
                ),
                provider_job_id=kwargs.get("provider_job_id"),
                reason="Synthetic transport estimate; no claim about live pricing or lifecycle.",
            )
        ]
    return VideoGenerationResult(**kwargs)


@pytest.fixture
def fixture_video_prices(monkeypatch):
    """Retired engine packs are exercised only behind an explicitly fake transport boundary."""

    def fixture_price(*, provider, model, resolution):
        return VideoPrice(
            provider=provider,
            model=model,
            resolution=resolution,
            unit_price_usd=1.0,
            source_url="https://example.invalid/mechanical-test-only",
            checked_on=date(2026, 10, 23),
        )

    monkeypatch.setattr(
        "cine_forge.ai.video_pricing.validate_video_target",
        lambda **kwargs: None,
    )
    monkeypatch.setattr(
        "cine_forge.modules.generation.render_adapter_v1.main.validate_video_target",
        lambda **kwargs: None,
    )
    monkeypatch.setattr(
        "cine_forge.modules.generation.render_adapter_v1.unit_preparation.resolve_video_price",
        fixture_price,
    )
