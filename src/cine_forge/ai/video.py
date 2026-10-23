"""Priced asynchronous video generation with submission-safe failure evidence."""

from __future__ import annotations

import json
import math
import time
import urllib.parse
import uuid
from collections.abc import Callable
from typing import Any

from cine_forge.ai.video_http import _read_string, _request_bytes, _request_json
from cine_forge.ai.video_pricing import VideoPricingError, resolve_video_price
from cine_forge.ai.video_types import (
    VideoGenerationError,
    VideoGenerationRequest,
    VideoGenerationResult,
    VideoReferenceInput,
)
from cine_forge.env import require_env
from cine_forge.schemas import EnginePack
from cine_forge.schemas.media_cost import CostReceipt, VideoPrice
from cine_forge.schemas.models import CostRecord

XAI_BASE_URL = "https://api.x.ai/v1"
# Public transport contracts stay available from this module.
__all__ = [
    "VideoGenerationError",
    "VideoGenerationRequest",
    "VideoGenerationResult",
    "VideoReferenceInput",
    "generate_video",
]


def generate_video(
    *,
    request: VideoGenerationRequest,
    engine_pack: EnginePack,
) -> VideoGenerationResult:
    """Generate only a qualified prompt-only request with an auditable estimate."""
    price = resolve_video_price(
        provider=engine_pack.provider,
        model=engine_pack.target_model,
        resolution=request.resolution,
    )
    _validate_priced_request(request)
    try:
        api_key = require_env("XAI_API_KEY")
    except RuntimeError as exc:
        raise VideoGenerationError(str(exc)) from exc
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    response = _submit_xai(request=request, engine_pack=engine_pack, headers=headers, price=price)
    job_id = _read_string(response, "request_id")
    if not job_id:
        raise _uncertain_failure(
            "xAI video response missing request_id; submission outcome is unknown",
            price=price,
            request=request,
            provider_response={"submission": response},
        )
    evidence = {"submission": response}
    try:
        status = _poll_xai(job_id=job_id, engine_pack=engine_pack, headers=headers)
        evidence["result"] = status
        returned_model = _read_string(status, "model") or engine_pack.target_model
        video = status.get("video")
        video_url = _read_string(video, "url") if isinstance(video, dict) else None
        if not video_url:
            raise VideoGenerationError("xAI video result missing output URL")
        _validate_download_url(video_url)
        video_bytes = _retry_existing_job(
            lambda: _request_bytes(url=video_url, method="GET", headers={}, timeout=300),
            engine_pack,
        )
    except VideoGenerationError as exc:
        evidence.update(exc.provider_response)
        raise _uncertain_failure(
            str(exc),
            price=price,
            request=request,
            provider_job_id=job_id,
            provider_response=evidence,
        ) from exc
    receipt = _output_receipt(price, request.duration_seconds, job_id, status)
    return VideoGenerationResult(
        video_bytes=video_bytes,
        media_type="video/mp4",
        model_used=returned_model,
        request_id=job_id,
        provider_job_id=job_id,
        cost_receipts=[receipt],
        provider_response=evidence,
    )


def _validate_download_url(url: str) -> None:
    try:
        parsed = urllib.parse.urlsplit(url)
        valid = parsed.scheme == "https" and bool(parsed.hostname)
    except ValueError as exc:
        raise VideoGenerationError("xAI video output URL must be a valid HTTPS URL") from exc
    if not valid:
        raise VideoGenerationError("xAI video output URL must use HTTPS")


def _validate_priced_request(request: VideoGenerationRequest) -> None:
    if request.first_frame or request.last_frame or request.reference_images:
        raise VideoPricingError("xAI video input media is not qualified for this prompt-only price")
    variants = sorted(key for key, value in request.provider_params.items() if value is not None)
    if variants:
        raise VideoPricingError(f"Unpriced xAI video provider parameter variants: {variants}")
    if isinstance(request.duration_seconds, bool) or not isinstance(request.duration_seconds, int):
        raise VideoPricingError(
            "Video duration must be an explicit positive integer number of seconds"
        )
    if request.duration_seconds <= 0:
        raise VideoPricingError("Video duration must be positive before submission")


def _submit_xai(
    *,
    request: VideoGenerationRequest,
    engine_pack: EnginePack,
    headers: dict[str, str],
    price: VideoPrice,
) -> dict[str, Any]:
    payload = {
        "model": engine_pack.target_model,
        "prompt": request.prompt,
        "duration": request.duration_seconds,
        "resolution": request.resolution,
    }
    if request.aspect_ratio:
        payload["aspect_ratio"] = request.aspect_ratio
    for attempt in range(engine_pack.retry_policy.max_attempts):
        try:
            return _request_json(
                url=f"{XAI_BASE_URL}/videos/generations",
                method="POST",
                headers=headers,
                body=json.dumps(payload).encode("utf-8"),
                timeout=120,
            )
        except VideoGenerationError as exc:
            # A timeout, broken connection, or server failure cannot prove rejection.
            if exc.status_code is None or exc.status_code == 408 or exc.status_code >= 500:
                raise _uncertain_failure(
                    str(exc),
                    price=price,
                    request=request,
                    provider_response=exc.provider_response,
                ) from exc
            if attempt + 1 >= engine_pack.retry_policy.max_attempts or not _should_retry(
                exc, engine_pack
            ):
                raise
            time.sleep(engine_pack.retry_policy.poll_interval_seconds)
    raise AssertionError("retry policy requires at least one attempt")


def _poll_xai(
    *,
    job_id: str,
    engine_pack: EnginePack,
    headers: dict[str, str],
) -> dict[str, Any]:
    started_at = time.monotonic()
    while True:
        status_payload = _retry_existing_job(
            lambda: _request_json(
                url=f"{XAI_BASE_URL}/videos/{urllib.parse.quote(job_id, safe='')}",
                method="GET",
                headers=headers,
                timeout=60,
            ),
            engine_pack,
        )
        status = _read_string(status_payload, "status")
        if status == "done":
            return status_payload
        if status != "pending":
            error = status_payload.get("error")
            detail = _read_string(error, "message") if isinstance(error, dict) else None
            raise VideoGenerationError(
                detail or f"xAI video job ended with status={status or 'unknown'}",
                provider_job_id=job_id,
                provider_response={"result": status_payload},
            )
        if time.monotonic() - started_at > engine_pack.retry_policy.max_poll_seconds:
            raise VideoGenerationError(
                f"xAI video job {job_id} timed out after "
                f"{engine_pack.retry_policy.max_poll_seconds:g}s waiting for completion",
                provider_job_id=job_id,
                provider_response={"result": status_payload},
            )
        time.sleep(engine_pack.retry_policy.poll_interval_seconds)


def _retry_existing_job[T](operation: Callable[[], T], engine_pack: EnginePack) -> T:
    """Only retry GET polling/download work, preserving the accepted job identity."""
    for attempt in range(engine_pack.retry_policy.max_attempts):
        try:
            return operation()
        except VideoGenerationError as exc:
            if attempt + 1 >= engine_pack.retry_policy.max_attempts or not _should_retry(
                exc, engine_pack
            ):
                raise
            time.sleep(engine_pack.retry_policy.poll_interval_seconds)
    raise AssertionError("retry policy requires at least one attempt")


def _should_retry(error: VideoGenerationError, engine_pack: EnginePack) -> bool:
    if not error.retryable:
        return False
    if error.status_code in engine_pack.retry_policy.retryable_http_statuses:
        return True
    return any(
        token.lower() in str(error).lower()
        for token in engine_pack.retry_policy.retryable_error_substrings
    )


def _output_receipt(
    price: VideoPrice,
    requested_seconds: int,
    job_id: str,
    result: dict[str, Any],
) -> CostReceipt:
    model = _read_string(result, "model") or price.model
    video = result.get("video")
    reported = video.get("duration") if isinstance(video, dict) else None
    seconds = reported if reported is not None else requested_seconds
    valid_seconds = (
        isinstance(seconds, (int, float))
        and not isinstance(seconds, bool)
        and math.isfinite(seconds)
        and seconds > 0
    )
    reason = None
    if model != price.model:
        reason = f"Returned video model {model} has no qualified price; requested {price.model}"
    elif not valid_seconds:
        reason = f"Provider returned invalid output duration {reported!r}; billing quantity unknown"
    if reason:
        return CostReceipt(
            receipt_id=f"video:{price.provider}:{job_id}",
            component="video",
            model=model,
            provider=price.provider,
            provider_job_id=job_id,
            status="uncertain",
            price=price if model == price.model else None,
            quantity=seconds if valid_seconds else None,
            reason=reason,
        )
    quantity_basis = (
        "provider-reported output duration"
        if reported is not None
        else "resolved request duration; provider did not return output duration"
    )
    return CostReceipt(
        receipt_id=f"video:{price.provider}:{job_id}",
        component="video",
        model=model,
        provider=price.provider,
        provider_job_id=job_id,
        price=price,
        quantity=seconds,
        cost=CostRecord(
            model=model,
            input_tokens=0,
            output_tokens=0,
            estimated_cost_usd=round(seconds * price.unit_price_usd, 8),
            request_id=job_id,
        ),
        reason=f"List-price estimate using {quantity_basis}; not provider billing",
    )


def _uncertain_failure(
    message: str,
    *,
    price: VideoPrice,
    request: VideoGenerationRequest,
    provider_job_id: str | None = None,
    provider_response: dict[str, Any] | None = None,
) -> VideoGenerationError:
    result = (provider_response or {}).get("result")
    returned_model = _read_string(result, "model") if isinstance(result, dict) else None
    receipt_model = returned_model or price.model
    receipt = CostReceipt(
        receipt_id=f"video:{price.provider}:{provider_job_id or uuid.uuid4().hex}",
        component="video",
        model=receipt_model,
        provider=price.provider,
        status="uncertain",
        provider_job_id=provider_job_id,
        price=price if receipt_model == price.model else None,
        quantity=request.duration_seconds,
        reason=f"Provider charge unknown: {message}",
    )
    return VideoGenerationError(
        message,
        retryable=False,
        cost_receipts=[receipt],
        provider_job_id=provider_job_id,
        provider_response=provider_response,
        submission_uncertain=True,
    )
