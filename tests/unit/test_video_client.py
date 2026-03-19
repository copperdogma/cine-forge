from __future__ import annotations

import pytest

from cine_forge.ai.video import (
    VideoGenerationError,
    VideoGenerationRequest,
    VideoGenerationResult,
    generate_video,
)
from cine_forge.modules.generation.render_adapter_v1.support import load_engine_pack


@pytest.mark.unit
def test_generate_video_retries_retryable_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    pack = load_engine_pack("openai_sora2")
    request = VideoGenerationRequest(
        prompt="Render a controlled push into the lab.",
        duration_seconds=8,
        resolution="1280x720",
        aspect_ratio="16:9",
    )
    state = {"calls": 0}

    def _fake_openai(*, request, engine_pack):
        state["calls"] += 1
        if state["calls"] == 1:
            raise VideoGenerationError("rate limit", retryable=True, status_code=429)
        return VideoGenerationResult(
            video_bytes=b"video",
            media_type="video/mp4",
            model_used=engine_pack.target_model,
            request_id="video-001",
            provider_job_id="job-001",
        )

    monkeypatch.setattr("cine_forge.ai.video._generate_video_openai", _fake_openai)
    monkeypatch.setattr("cine_forge.ai.video.time.sleep", lambda *_: None)

    result = generate_video(request=request, engine_pack=pack)

    assert result.request_id == "video-001"
    assert state["calls"] == 2


@pytest.mark.unit
def test_generate_video_stops_on_nonretryable_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    pack = load_engine_pack("google_veo31")
    request = VideoGenerationRequest(
        prompt="Render the rooftop reckoning at dawn.",
        duration_seconds=8,
        resolution="720p",
        aspect_ratio="16:9",
    )
    state = {"calls": 0}

    def _fake_google(*, request, engine_pack):
        state["calls"] += 1
        raise VideoGenerationError("bad request", retryable=False, status_code=400)

    monkeypatch.setattr("cine_forge.ai.video._generate_video_google", _fake_google)
    monkeypatch.setattr("cine_forge.ai.video.time.sleep", lambda *_: None)

    with pytest.raises(VideoGenerationError, match="bad request"):
        generate_video(request=request, engine_pack=pack)

    assert state["calls"] == 1
