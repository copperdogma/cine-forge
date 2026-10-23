from __future__ import annotations

import pytest

from cine_forge.ai.video import (
    VideoGenerationError,
    VideoGenerationRequest,
    generate_video,
)
from cine_forge.modules.generation.render_adapter_v1.support import load_engine_pack


@pytest.fixture(autouse=True)
def _isolate_video_credentials(monkeypatch):
    # Other suites can load prefixed credentials. Offline tests never resolve them.
    monkeypatch.setattr("cine_forge.ai.video.require_env", lambda _: "offline-video-test-key")


@pytest.mark.unit
def test_generate_video_retries_definite_rate_limit_rejection(monkeypatch):
    pack = load_engine_pack("xai_grok_imagine_video")
    request = VideoGenerationRequest(
        prompt="Render a controlled push into the lab.",
        duration_seconds=4,
        resolution="480p",
        aspect_ratio="16:9",
    )
    posts = []

    def json_call(**kw):
        if kw["method"] == "POST":
            posts.append(kw)
            if len(posts) == 1:
                raise VideoGenerationError("rate limit", retryable=True, status_code=429)
            return {"request_id": "accepted-after-rejection"}
        return {"status": "done", "video": {"url": "https://example.invalid/clip"}}

    monkeypatch.setattr("cine_forge.ai.video._request_json", json_call)
    monkeypatch.setattr("cine_forge.ai.video._request_bytes", lambda **_: b"video")
    monkeypatch.setattr("cine_forge.ai.video.time.sleep", lambda *_: None)
    result = generate_video(request=request, engine_pack=pack)
    assert result.provider_job_id == "accepted-after-rejection"
    assert len(posts) == 2


@pytest.mark.unit
def test_generate_video_stops_on_nonretryable_rejection(monkeypatch):
    posts = []

    def json_call(**kw):
        posts.append(kw)
        raise VideoGenerationError("bad request", status_code=400)

    monkeypatch.setattr("cine_forge.ai.video._request_json", json_call)
    request = VideoGenerationRequest(
        prompt="Rejected prompt",
        duration_seconds=4,
        resolution="480p",
        aspect_ratio="16:9",
    )
    with pytest.raises(VideoGenerationError, match="bad request") as caught:
        generate_video(request=request, engine_pack=load_engine_pack("xai_grok_imagine_video"))
    assert len(posts) == 1
    assert caught.value.cost_receipts == []


@pytest.mark.unit
def test_generate_video_xai_polls_until_done_and_downloads_bytes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pack = load_engine_pack("xai_grok_imagine_video")
    request = VideoGenerationRequest(
        prompt="Render a rough handheld hallway approach.",
        duration_seconds=4,
        resolution="480p",
        aspect_ratio="16:9",
    )
    calls: list[tuple[str, str, dict | None]] = []

    def _fake_request_json(*, url, method, headers, body=None, timeout=60):
        payload = None
        if body is not None:
            payload = __import__("json").loads(body.decode("utf-8"))
        calls.append((method, url, payload))
        if method == "POST":
            return {"request_id": "req-123"}
        if len(calls) == 2:
            return {"status": "pending", "progress": 42}
        return {
            "status": "done",
            "model": "grok-imagine-video",
            "video": {
                "url": "https://vidgen.x.ai/test/video.mp4",
                "duration": 4,
                "respect_moderation": True,
            },
        }

    monkeypatch.setattr("cine_forge.ai.video._request_json", _fake_request_json)
    monkeypatch.setattr("cine_forge.ai.video._request_bytes", lambda **_: b"xai-video")
    monkeypatch.setattr("cine_forge.ai.video.time.sleep", lambda *_: None)

    result = generate_video(request=request, engine_pack=pack)

    assert result.media_type == "video/mp4"
    assert result.request_id == "req-123"
    assert calls[0][2] == {
        "model": "grok-imagine-video",
        "prompt": "Render a rough handheld hallway approach.",
        "duration": 4,
        "aspect_ratio": "16:9",
        "resolution": "480p",
    }


@pytest.mark.unit
def test_generate_video_xai_raises_on_failed_status(monkeypatch: pytest.MonkeyPatch) -> None:
    pack = load_engine_pack("xai_grok_imagine_video")
    request = VideoGenerationRequest(
        prompt="Render a blocked stairwell argument.",
        duration_seconds=4,
        resolution="480p",
        aspect_ratio="16:9",
    )

    def _fake_request_json(*, url, method, headers, body=None, timeout=60):
        if method == "POST":
            return {"request_id": "req-456"}
        return {
            "status": "failed",
            "error": {"message": "provider rejected prompt", "code": "safety_rejected"},
        }

    monkeypatch.setattr("cine_forge.ai.video._request_json", _fake_request_json)
    monkeypatch.setattr("cine_forge.ai.video.time.sleep", lambda *_: None)

    with pytest.raises(VideoGenerationError, match="provider rejected prompt"):
        generate_video(request=request, engine_pack=pack)


@pytest.mark.unit
def test_generate_video_xai_times_out_pending_jobs(monkeypatch: pytest.MonkeyPatch) -> None:
    pack = load_engine_pack("xai_grok_imagine_video")
    request = VideoGenerationRequest(
        prompt="Render a stuck provider job.",
        duration_seconds=4,
        resolution="480p",
        aspect_ratio="16:9",
    )

    def _fake_request_json(*, url, method, headers, body=None, timeout=60):
        if method == "POST":
            return {"request_id": "req-timeout"}
        return {"status": "pending", "progress": 5}

    monotonic_values = iter([0.0, pack.retry_policy.max_poll_seconds + 0.1])

    monkeypatch.setattr("cine_forge.ai.video._request_json", _fake_request_json)
    monkeypatch.setattr("cine_forge.ai.video.time.sleep", lambda *_: None)
    monkeypatch.setattr(
        "cine_forge.ai.video.time.monotonic",
        lambda: next(monotonic_values),
    )

    with pytest.raises(VideoGenerationError, match="timed out after 180s"):
        generate_video(request=request, engine_pack=pack)


@pytest.mark.unit
def test_generate_video_does_not_retry_poll_timeouts(monkeypatch: pytest.MonkeyPatch) -> None:
    pack = load_engine_pack("xai_grok_imagine_video")
    request = VideoGenerationRequest(
        prompt="Render a stuck provider job.",
        duration_seconds=4,
        resolution="480p",
        aspect_ratio="16:9",
    )
    post_count = 0

    def _fake_request_json(*, url, method, headers, body=None, timeout=60):
        nonlocal post_count
        if method == "POST":
            post_count += 1
            return {"request_id": f"req-timeout-{post_count}"}
        return {"status": "pending", "progress": 5}

    monotonic_values = iter([0.0, pack.retry_policy.max_poll_seconds + 0.1])

    monkeypatch.setattr("cine_forge.ai.video._request_json", _fake_request_json)
    monkeypatch.setattr("cine_forge.ai.video.time.sleep", lambda *_: None)
    monkeypatch.setattr(
        "cine_forge.ai.video.time.monotonic",
        lambda: next(monotonic_values),
    )

    with pytest.raises(VideoGenerationError, match="timed out after 180s"):
        generate_video(request=request, engine_pack=pack)

    assert post_count == 1
