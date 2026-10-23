"""Offline regressions for paid asynchronous media execution."""

from __future__ import annotations

import pytest

from cine_forge.ai.video import VideoGenerationError, VideoGenerationRequest, generate_video
from cine_forge.modules.generation.render_adapter_v1.support import load_engine_pack

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def _isolate_video_credentials(monkeypatch):
    # Other suites can load prefixed credentials. Offline tests never resolve them.
    monkeypatch.setattr("cine_forge.ai.video.require_env", lambda _: "offline-video-test-key")


def _request() -> VideoGenerationRequest:
    return VideoGenerationRequest(
        prompt="Offline controlled camera move",
        duration_seconds=4,
        resolution="480p",
        aspect_ratio="16:9",
    )


def test_success_preserves_resolved_request_price_and_job(monkeypatch):
    monkeypatch.setattr("cine_forge.ai.video.time.sleep", lambda *_: None)
    monkeypatch.setattr("cine_forge.ai.video._request_bytes", lambda **_: b"video")
    monkeypatch.setattr(
        "cine_forge.ai.video._request_json",
        lambda **kw: (
            {"request_id": "paid-job"}
            if kw["method"] == "POST"
            else {
                "status": "done",
                "model": "grok-imagine-video",
                "video": {"url": "https://example.invalid/video.mp4"},
            }
        ),
    )
    result = generate_video(
        request=_request(), engine_pack=load_engine_pack("xai_grok_imagine_video")
    )
    receipt = result.cost_receipts[0]
    assert receipt.cost.estimated_cost_usd == pytest.approx(0.20)
    assert receipt.provider_job_id == "paid-job"
    assert receipt.quantity == 4
    assert receipt.price.resolution == "480p"
    assert receipt.status == "estimated"


@pytest.mark.parametrize("failure_point", ["poll", "download"])
def test_accepted_job_failure_never_submits_again(monkeypatch, failure_point):
    post_count = 0
    monkeypatch.setattr("cine_forge.ai.video.time.sleep", lambda *_: None)

    def fail():
        raise VideoGenerationError("HTTP 503: temporary failure", retryable=True, status_code=503)

    def json_call(**kw):
        nonlocal post_count
        if kw["method"] == "POST":
            post_count += 1
            return {"request_id": "accepted-paid-job"}
        if failure_point == "poll":
            fail()
        return {"status": "done", "video": {"url": "https://example.invalid/video.mp4"}}

    monkeypatch.setattr("cine_forge.ai.video._request_json", json_call)
    monkeypatch.setattr("cine_forge.ai.video._request_bytes", lambda **_: fail())
    with pytest.raises(VideoGenerationError) as caught:
        generate_video(request=_request(), engine_pack=load_engine_pack("xai_grok_imagine_video"))
    assert post_count == 1
    receipt = caught.value.cost_receipts[0]
    assert receipt.provider_job_id == "accepted-paid-job"
    assert receipt.status == "uncertain"
    assert receipt.cost is None


@pytest.mark.parametrize("status_code", [None, 408, 500, 503])
def test_uncertain_submission_is_not_repeated_or_invented_as_zero(monkeypatch, status_code):
    posts = []

    def json_call(**kw):
        posts.append(kw)
        raise VideoGenerationError(
            "submission response lost", retryable=True, status_code=status_code
        )

    monkeypatch.setattr("cine_forge.ai.video._request_json", json_call)
    with pytest.raises(VideoGenerationError) as caught:
        generate_video(request=_request(), engine_pack=load_engine_pack("xai_grok_imagine_video"))
    assert len(posts) == 1
    receipt = caught.value.cost_receipts[0]
    assert receipt.status == "uncertain"
    assert receipt.cost is None
    assert receipt.provider_job_id is None
    assert caught.value.submission_uncertain


def test_transient_poll_and_download_failures_retry_same_job(monkeypatch):
    posts = 0
    polls = 0
    downloads = 0
    monkeypatch.setattr("cine_forge.ai.video.time.sleep", lambda *_: None)

    def json_call(**kw):
        nonlocal posts, polls
        if kw["method"] == "POST":
            posts += 1
            return {"request_id": "same-job"}
        polls += 1
        assert kw["url"].endswith("/same-job")
        if polls == 1:
            raise VideoGenerationError("temporarily unavailable", retryable=True, status_code=503)
        return {"status": "done", "video": {"url": "https://example.invalid/same-job.mp4"}}

    def download(**kw):
        nonlocal downloads
        downloads += 1
        assert kw["url"].endswith("/same-job.mp4")
        if downloads == 1:
            raise VideoGenerationError("temporarily unavailable", retryable=True, status_code=503)
        return b"video"

    monkeypatch.setattr("cine_forge.ai.video._request_json", json_call)
    monkeypatch.setattr("cine_forge.ai.video._request_bytes", download)
    result = generate_video(
        request=_request(), engine_pack=load_engine_pack("xai_grok_imagine_video")
    )
    assert (posts, polls, downloads) == (1, 2, 2)
    assert len(result.cost_receipts) == 1
    assert result.cost_receipts[0].cost.estimated_cost_usd == pytest.approx(0.20)


def test_raw_submit_and_failure_status_identity_remain_available(monkeypatch):
    monkeypatch.setattr(
        "cine_forge.ai.video._request_json",
        lambda **kw: (
            {"request_id": "failed-job", "trace_id": "provider-trace"}
            if kw["method"] == "POST"
            else {
                "status": "failed",
                "error": {"message": "rejected later", "code": "safety"},
            }
        ),
    )
    with pytest.raises(VideoGenerationError) as caught:
        generate_video(request=_request(), engine_pack=load_engine_pack("xai_grok_imagine_video"))
    assert caught.value.provider_job_id == "failed-job"
    assert caught.value.provider_response["submission"]["trace_id"] == "provider-trace"
    assert caught.value.provider_response["result"]["error"]["code"] == "safety"
    assert caught.value.cost_receipts[0].cost is None


def test_missing_submission_job_id_is_uncertain_and_not_repeated(monkeypatch):
    posts = []

    def json_call(**kw):
        posts.append(kw)
        return {"unexpected": "accepted?"}

    monkeypatch.setattr("cine_forge.ai.video._request_json", json_call)
    with pytest.raises(VideoGenerationError, match="missing request_id") as caught:
        generate_video(request=_request(), engine_pack=load_engine_pack("xai_grok_imagine_video"))
    assert len(posts) == 1
    assert caught.value.cost_receipts[0].status == "uncertain"
    assert caught.value.provider_response["submission"] == {"unexpected": "accepted?"}


@pytest.mark.parametrize("failure", [TimeoutError("read timed out"), ConnectionResetError("reset")])
def test_actual_http_transport_uncertainty_keeps_receipt(monkeypatch, failure):
    posts = []

    def urlopen(request, timeout):
        posts.append(request)
        raise failure

    monkeypatch.setattr("cine_forge.ai.video_http.urllib.request.urlopen", urlopen)
    with pytest.raises(VideoGenerationError, match="Network error") as caught:
        generate_video(request=_request(), engine_pack=load_engine_pack("xai_grok_imagine_video"))
    assert len(posts) == 1
    assert caught.value.cost_receipts[0].cost is None
    assert caught.value.cost_receipts[0].status == "uncertain"


def test_success_720p_uses_resolved_duration_and_retains_raw_result(monkeypatch):
    from dataclasses import replace

    monkeypatch.setattr("cine_forge.ai.video._request_bytes", lambda **_: b"video")
    raw_result = {
        "status": "done",
        "model": "grok-imagine-video",
        "provider_trace": "kept",
        "video": {"url": "https://example.invalid/clip"},
    }
    monkeypatch.setattr(
        "cine_forge.ai.video._request_json",
        lambda **kw: {"request_id": "720p-job"} if kw["method"] == "POST" else raw_result,
    )
    result = generate_video(
        request=replace(_request(), resolution="720p", duration_seconds=8),
        engine_pack=load_engine_pack("xai_grok_imagine_video"),
    )
    receipt = result.cost_receipts[0]
    assert receipt.quantity == 8
    assert receipt.price.resolution == "720p"
    assert receipt.cost.estimated_cost_usd == pytest.approx(0.56)
    assert receipt.provider_job_id == "720p-job"
    assert result.provider_response["result"] == raw_result


@pytest.mark.parametrize("reported_seconds", [8, 8.25])
def test_reported_output_duration_sets_estimate_quantity(monkeypatch, reported_seconds):
    monkeypatch.setattr("cine_forge.ai.video._request_bytes", lambda **_: b"video")
    monkeypatch.setattr(
        "cine_forge.ai.video._request_json",
        lambda **kw: (
            {"request_id": "duration-job"}
            if kw["method"] == "POST"
            else {
                "status": "done",
                "model": "grok-imagine-video",
                "video": {"url": "https://example.invalid/clip", "duration": reported_seconds},
            }
        ),
    )
    result = generate_video(
        request=_request(), engine_pack=load_engine_pack("xai_grok_imagine_video")
    )
    receipt = result.cost_receipts[0]
    assert receipt.quantity == reported_seconds
    assert receipt.cost.estimated_cost_usd == pytest.approx(reported_seconds * 0.05)
    assert "provider-reported output duration" in receipt.reason


def test_unknown_returned_model_keeps_bytes_and_identity_without_invented_price(monkeypatch):
    monkeypatch.setattr("cine_forge.ai.video._request_bytes", lambda **_: b"retained-video")
    monkeypatch.setattr(
        "cine_forge.ai.video._request_json",
        lambda **kw: (
            {"request_id": "different-model-job"}
            if kw["method"] == "POST"
            else {
                "status": "done",
                "model": "grok-imagine-video-unqualified",
                "video": {"url": "https://example.invalid/clip", "duration": 4},
            }
        ),
    )
    result = generate_video(
        request=_request(), engine_pack=load_engine_pack("xai_grok_imagine_video")
    )
    receipt = result.cost_receipts[0]
    assert result.video_bytes == b"retained-video"
    assert result.model_used == receipt.model == "grok-imagine-video-unqualified"
    assert receipt.provider_job_id == "different-model-job"
    assert receipt.status == "uncertain"
    assert receipt.cost is None
    assert receipt.price is None
    assert result.provider_response["result"]["model"] == receipt.model


@pytest.mark.parametrize("bad_duration", [0, -1, "8", True, float("nan")])
def test_invalid_reported_duration_keeps_bytes_without_amount(monkeypatch, bad_duration):
    monkeypatch.setattr("cine_forge.ai.video._request_bytes", lambda **_: b"video")
    monkeypatch.setattr(
        "cine_forge.ai.video._request_json",
        lambda **kw: (
            {"request_id": "invalid-duration-job"}
            if kw["method"] == "POST"
            else {
                "status": "done",
                "model": "grok-imagine-video",
                "video": {"url": "https://example.invalid/clip", "duration": bad_duration},
            }
        ),
    )
    result = generate_video(
        request=_request(), engine_pack=load_engine_pack("xai_grok_imagine_video")
    )
    assert result.video_bytes == b"video"
    receipt = result.cost_receipts[0]
    assert receipt.status == "uncertain"
    assert receipt.cost is None
    assert receipt.quantity is None
    assert "invalid output duration" in receipt.reason


def test_cdn_download_and_stdlib_redirect_never_receive_api_bearer(monkeypatch):
    import io
    import urllib.request

    poll_headers = []
    download_requests = []

    def json_call(**kw):
        if kw["method"] == "POST":
            return {"request_id": "cdn-job"}
        poll_headers.append(kw["headers"])
        return {
            "status": "done",
            "model": "grok-imagine-video",
            "video": {"url": "https://vidgen.x.ai/temporary/clip.mp4", "duration": 4},
        }

    def offline_urlopen(request, timeout):
        download_requests.append(request)
        redirected = urllib.request.HTTPRedirectHandler().redirect_request(
            request,
            None,
            302,
            "Found",
            {},
            "https://media.example.invalid/redirected.mp4",
        )
        download_requests.append(redirected)
        return io.BytesIO(b"downloaded-video")

    monkeypatch.setattr("cine_forge.ai.video._request_json", json_call)
    monkeypatch.setattr("cine_forge.ai.video_http.urllib.request.urlopen", offline_urlopen)
    result = generate_video(
        request=_request(),
        engine_pack=load_engine_pack("xai_grok_imagine_video"),
    )
    assert result.video_bytes == b"downloaded-video"
    assert poll_headers[0]["Authorization"] == "Bearer offline-video-test-key"
    assert len(download_requests) == 2
    assert download_requests[0].full_url == "https://vidgen.x.ai/temporary/clip.mp4"
    assert download_requests[1].full_url == "https://media.example.invalid/redirected.mp4"
    for request in download_requests:
        assert not any(name.lower() == "authorization" for name, _ in request.header_items())


@pytest.mark.parametrize("output_url", ["http://vidgen.x.ai/clip", "file:///tmp/clip", "https://"])
def test_non_https_or_invalid_output_url_is_rejected_before_download(monkeypatch, output_url):
    monkeypatch.setattr("cine_forge.ai.video._request_bytes", lambda **_: pytest.fail("download"))
    monkeypatch.setattr(
        "cine_forge.ai.video._request_json",
        lambda **kw: (
            {"request_id": "insecure-output-job"}
            if kw["method"] == "POST"
            else {
                "status": "done",
                "model": "grok-imagine-video",
                "video": {"url": output_url},
            }
        ),
    )
    with pytest.raises(VideoGenerationError, match="HTTPS") as caught:
        generate_video(request=_request(), engine_pack=load_engine_pack("xai_grok_imagine_video"))
    assert caught.value.provider_job_id == "insecure-output-job"
    assert caught.value.cost_receipts[0].status == "uncertain"
    assert caught.value.cost_receipts[0].cost is None
