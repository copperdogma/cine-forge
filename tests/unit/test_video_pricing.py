"""Exact supported pricing and fail-before-submission boundaries."""

from __future__ import annotations

from dataclasses import replace
from datetime import date
from pathlib import Path

import pytest

from cine_forge.ai.video import VideoGenerationRequest, VideoReferenceInput, generate_video
from cine_forge.ai.video_pricing import (
    VideoPricingError,
    resolve_video_price,
    validate_video_target,
)
from cine_forge.modules.generation.render_adapter_v1.support import load_engine_pack

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(("resolution", "amount"), [("480p", 0.05), ("720p", 0.07)])
def test_exact_output_rate_has_replayable_source(resolution, amount):
    price = resolve_video_price(provider="xai", model="grok-imagine-video", resolution=resolution)
    assert price.unit_price_usd == amount
    assert price.checked_on == date(2026, 10, 23)
    assert price.source_url == "https://docs.x.ai/developers/models/grok-imagine-video"
    assert price.unit == "USD/second"


@pytest.mark.parametrize(
    ("provider", "model", "reason"),
    [
        ("google", "veo-3.1-generate-preview", "shut down 2026-10-22"),
        ("google", "veo-3.1-fast-generate-preview", "shut down 2026-10-22"),
        ("openai", "sora-2", "shut down 2026-09-24"),
        ("openai", "sora-2-pro", "shut down 2026-09-24"),
        ("xai", "grok-video-unknown", "No qualified current video price"),
        ("new-provider", "new-model", "No qualified current video price"),
    ],
)
def test_unknown_and_retired_target_have_no_runtime_rate(provider, model, reason):
    with pytest.raises(VideoPricingError, match=reason):
        validate_video_target(provider=provider, model=model)


@pytest.mark.parametrize("pack_id", ["google_veo31", "google_veo31_fast", "openai_sora2"])
def test_retired_targets_fail_before_credentials_or_submission(monkeypatch, pack_id):
    def unexpected(**kw):
        pytest.fail("retired target reached credential lookup or network")

    monkeypatch.setattr("cine_forge.ai.video.require_env", unexpected)
    monkeypatch.setattr("cine_forge.ai.video._request_json", unexpected)
    request = VideoGenerationRequest(
        prompt="No paid call",
        duration_seconds=4,
        resolution="720p",
        aspect_ratio="16:9",
    )
    with pytest.raises(VideoPricingError, match="unavailable"):
        generate_video(request=request, engine_pack=load_engine_pack(pack_id))


@pytest.mark.parametrize(
    "change",
    [
        {"first_frame": VideoReferenceInput(Path("unused.png"), "image/png", "input_reference")},
        {"last_frame": VideoReferenceInput(Path("unused.png"), "image/png", "last_frame")},
        {
            "reference_images": [
                VideoReferenceInput(Path("unused.png"), "image/png", "reference_image")
            ]
        },
        {"provider_params": {"duration": 10}},
        {"provider_params": {"resolution": "720p"}},
        {"provider_params": {"image_url": "https://example.invalid/paid-input"}},
        {"resolution": "1080p"},
        {"duration_seconds": 0},
        {"duration_seconds": True},
    ],
)
def test_unpriced_variants_fail_before_credentials_or_submission(monkeypatch, change):
    monkeypatch.setattr(
        "cine_forge.ai.video.require_env", lambda *a: pytest.fail("credential lookup")
    )
    monkeypatch.setattr("cine_forge.ai.video._request_json", lambda **kw: pytest.fail("network"))
    request = VideoGenerationRequest(
        prompt="No paid call",
        duration_seconds=4,
        resolution="480p",
        aspect_ratio="16:9",
    )
    with pytest.raises(VideoPricingError):
        generate_video(
            request=replace(request, **change),
            engine_pack=load_engine_pack("xai_grok_imagine_video"),
        )
