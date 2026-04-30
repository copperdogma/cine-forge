from __future__ import annotations

import io
from pathlib import Path

import pytest
from PIL import Image

from cine_forge.ai.video import (
    VideoGenerationError,
    VideoGenerationRequest,
    VideoGenerationResult,
    VideoReferenceInput,
    _generate_video_google,
    _generate_video_xai,
    _prepare_openai_input_reference,
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


@pytest.mark.unit
def test_prepare_openai_input_reference_fits_image_to_requested_resolution(tmp_path: Path) -> None:
    image_path = tmp_path / "operator-ref.png"
    Image.new("RGB", (96, 96), color=(40, 90, 180)).save(image_path, format="PNG")
    reference = VideoReferenceInput(
        path=image_path,
        media_type="image/png",
        usage="input_reference",
    )

    filename, file_bytes, media_type = _prepare_openai_input_reference(reference, "1280x720")

    assert filename == "operator-ref_openai_input.png"
    assert media_type == "image/png"
    with Image.open(io.BytesIO(file_bytes)) as image:
        assert image.size == (1280, 720)


@pytest.mark.unit
def test_prepare_openai_input_reference_keeps_matching_image_bytes(tmp_path: Path) -> None:
    image_path = tmp_path / "matching-ref.png"
    Image.new("RGB", (1280, 720), color=(12, 34, 56)).save(image_path, format="PNG")
    reference = VideoReferenceInput(
        path=image_path,
        media_type="image/png",
        usage="input_reference",
    )

    filename, file_bytes, media_type = _prepare_openai_input_reference(reference, "1280x720")

    assert filename == "matching-ref.png"
    assert media_type == "image/png"
    assert file_bytes == image_path.read_bytes()


@pytest.mark.unit
def test_generate_video_google_sends_numeric_duration(monkeypatch: pytest.MonkeyPatch) -> None:
    pack = load_engine_pack("google_veo31_fast")
    request = VideoGenerationRequest(
        prompt="Render a low-fidelity corridor track.",
        duration_seconds=4,
        resolution="720p",
        aspect_ratio="16:9",
        provider_params={"generateAudio": False},
    )
    payloads: list[dict] = []

    def _fake_request_json(*, url, method, headers, body=None, timeout=60):
        if method == "POST":
            assert body is not None
            payload = __import__("json").loads(body.decode("utf-8"))
            payloads.append(payload)
            return {"name": "operations/test-op", "done": False}
        return {
            "name": "operations/test-op",
            "done": True,
            "response": {
                "generateVideoResponse": {
                    "generatedSamples": [{"video": {"uri": "https://example.com/video.mp4"}}]
                }
            },
        }

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr("cine_forge.ai.video._request_json", _fake_request_json)
    monkeypatch.setattr("cine_forge.ai.video._request_bytes", lambda **_: b"video-bytes")
    monkeypatch.setattr("cine_forge.ai.video.time.sleep", lambda *_: None)

    result = _generate_video_google(request=request, engine_pack=pack)

    assert result.media_type == "video/mp4"
    assert payloads[0]["parameters"]["durationSeconds"] == 4


@pytest.mark.unit
def test_generate_video_google_serializes_images_as_bytes_base64_encoded(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pack = load_engine_pack("google_veo31")
    first_path = tmp_path / "first.png"
    last_path = tmp_path / "last.png"
    ref_path = tmp_path / "ref.png"
    for image_path, color in (
        (first_path, (10, 20, 30)),
        (last_path, (40, 50, 60)),
        (ref_path, (70, 80, 90)),
    ):
        Image.new("RGB", (64, 64), color=color).save(image_path, format="PNG")

    request = VideoGenerationRequest(
        prompt="Render a reference-conditioned lab scene.",
        duration_seconds=8,
        resolution="720p",
        aspect_ratio="16:9",
        first_frame=VideoReferenceInput(
            path=first_path,
            media_type="image/png",
            usage="input_reference",
        ),
        last_frame=VideoReferenceInput(
            path=last_path,
            media_type="image/png",
            usage="last_frame",
        ),
        reference_images=[
            VideoReferenceInput(
                path=ref_path,
                media_type="image/png",
                usage="reference_image",
            )
        ],
    )
    payloads: list[dict] = []

    def _fake_request_json(*, url, method, headers, body=None, timeout=60):
        if method == "POST":
            assert body is not None
            payload = __import__("json").loads(body.decode("utf-8"))
            payloads.append(payload)
            return {"name": "operations/test-op", "done": False}
        return {
            "name": "operations/test-op",
            "done": True,
            "response": {
                "generateVideoResponse": {
                    "generatedSamples": [{"video": {"uri": "https://example.com/video.mp4"}}]
                }
            },
        }

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr("cine_forge.ai.video._request_json", _fake_request_json)
    monkeypatch.setattr("cine_forge.ai.video._request_bytes", lambda **_: b"video-bytes")
    monkeypatch.setattr("cine_forge.ai.video.time.sleep", lambda *_: None)

    result = _generate_video_google(request=request, engine_pack=pack)

    assert result.media_type == "video/mp4"
    image_payload = payloads[0]["instances"][0]["image"]
    assert image_payload["mimeType"] == "image/png"
    assert "bytesBase64Encoded" in image_payload
    assert "inlineData" not in image_payload
    last_frame_payload = payloads[0]["instances"][0]["lastFrame"]
    assert "bytesBase64Encoded" in last_frame_payload
    ref_payload = payloads[0]["instances"][0]["referenceImages"][0]["image"]
    assert ref_payload["mimeType"] == "image/png"
    assert "bytesBase64Encoded" in ref_payload


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

    monkeypatch.setenv("XAI_API_KEY", "test-key")
    monkeypatch.setattr("cine_forge.ai.video._request_json", _fake_request_json)
    monkeypatch.setattr("cine_forge.ai.video._request_bytes", lambda **_: b"xai-video")
    monkeypatch.setattr("cine_forge.ai.video.time.sleep", lambda *_: None)

    result = _generate_video_xai(request=request, engine_pack=pack)

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

    monkeypatch.setenv("XAI_API_KEY", "test-key")
    monkeypatch.setattr("cine_forge.ai.video._request_json", _fake_request_json)
    monkeypatch.setattr("cine_forge.ai.video.time.sleep", lambda *_: None)

    with pytest.raises(VideoGenerationError, match="provider rejected prompt"):
        _generate_video_xai(request=request, engine_pack=pack)


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

    monkeypatch.setenv("XAI_API_KEY", "test-key")
    monkeypatch.setattr("cine_forge.ai.video._request_json", _fake_request_json)
    monkeypatch.setattr("cine_forge.ai.video.time.sleep", lambda *_: None)
    monkeypatch.setattr(
        "cine_forge.ai.video.time.monotonic",
        lambda: next(monotonic_values),
    )

    with pytest.raises(VideoGenerationError, match="timed out after 180s"):
        _generate_video_xai(request=request, engine_pack=pack)


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

    monkeypatch.setenv("XAI_API_KEY", "test-key")
    monkeypatch.setattr("cine_forge.ai.video._request_json", _fake_request_json)
    monkeypatch.setattr("cine_forge.ai.video.time.sleep", lambda *_: None)
    monkeypatch.setattr(
        "cine_forge.ai.video.time.monotonic",
        lambda: next(monotonic_values),
    )

    with pytest.raises(VideoGenerationError, match="timed out after 180s"):
        generate_video(request=request, engine_pack=pack)

    assert post_count == 1
