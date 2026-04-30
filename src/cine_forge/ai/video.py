"""Thin video-generation wrapper for OpenAI, Google, and xAI video APIs.

Provider keys prefer ``CINE_FORGE_*`` env names and fall back to the generic
provider names inside this repo process when needed.
"""

from __future__ import annotations

import base64
import io
import json
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from PIL import Image, ImageOps

from cine_forge.env import require_env
from cine_forge.schemas import EnginePack

OPENAI_BASE_URL = "https://api.openai.com/v1"
GOOGLE_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
XAI_BASE_URL = "https://api.x.ai/v1"


class VideoGenerationError(RuntimeError):
    """Terminal error raised when a video-generation request fails."""

    def __init__(
        self,
        message: str,
        *,
        retryable: bool = False,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.retryable = retryable
        self.status_code = status_code


@dataclass(frozen=True)
class VideoReferenceInput:
    """Local image input passed to the target provider."""

    path: Path
    media_type: str
    usage: Literal["input_reference", "reference_image", "last_frame"]


@dataclass(frozen=True)
class VideoGenerationRequest:
    """Normalized request payload for the provider transport layer."""

    prompt: str
    duration_seconds: int
    resolution: str
    aspect_ratio: str
    first_frame: VideoReferenceInput | None = None
    last_frame: VideoReferenceInput | None = None
    reference_images: list[VideoReferenceInput] = field(default_factory=list)
    provider_params: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class VideoGenerationResult:
    """Normalized response returned by the provider transport layer."""

    video_bytes: bytes
    media_type: str
    model_used: str
    request_id: str | None = None
    provider_job_id: str | None = None


def generate_video(
    *,
    request: VideoGenerationRequest,
    engine_pack: EnginePack,
) -> VideoGenerationResult:
    """Generate a video using the provider described by *engine_pack*."""
    retry_policy = engine_pack.retry_policy
    attempts = retry_policy.max_attempts
    last_error: VideoGenerationError | None = None

    for attempt in range(1, attempts + 1):
        try:
            if engine_pack.provider == "openai":
                return _generate_video_openai(request=request, engine_pack=engine_pack)
            if engine_pack.provider == "google":
                return _generate_video_google(request=request, engine_pack=engine_pack)
            if engine_pack.provider == "xai":
                return _generate_video_xai(request=request, engine_pack=engine_pack)
            raise VideoGenerationError(f"Unsupported video provider: {engine_pack.provider}")
        except VideoGenerationError as exc:
            last_error = exc
            if attempt >= attempts or not _should_retry(exc, engine_pack):
                raise
            time.sleep(retry_policy.poll_interval_seconds)

    raise last_error or VideoGenerationError("Video generation failed")


def _should_retry(error: VideoGenerationError, engine_pack: EnginePack) -> bool:
    if not error.retryable:
        return False
    retry_statuses = set(engine_pack.retry_policy.retryable_http_statuses)
    if error.status_code in retry_statuses:
        return True
    message = str(error).lower()
    return any(
        token.lower() in message for token in engine_pack.retry_policy.retryable_error_substrings
    )


def _generate_video_openai(
    *,
    request: VideoGenerationRequest,
    engine_pack: EnginePack,
) -> VideoGenerationResult:
    try:
        api_key = require_env("OPENAI_API_KEY")
    except RuntimeError as exc:
        raise VideoGenerationError(str(exc)) from exc

    fields: list[tuple[str, str]] = [
        ("prompt", request.prompt),
        ("model", engine_pack.target_model),
        ("size", request.resolution),
        ("seconds", str(request.duration_seconds)),
    ]
    files: list[tuple[str, str, bytes, str]] = []
    if request.first_frame is not None:
        filename, file_bytes, media_type = _prepare_openai_input_reference(
            request.first_frame,
            request.resolution,
        )
        files.append(
            (
                "input_reference",
                filename,
                file_bytes,
                media_type,
            )
        )

    body, content_type = _encode_multipart_form(fields=fields, files=files)
    response = _request_json(
        url=f"{OPENAI_BASE_URL}/videos",
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": content_type,
        },
        body=body,
        timeout=120,
    )
    video_id = _read_string(response, "id")
    if not video_id:
        raise VideoGenerationError(f"OpenAI video response missing id: {response}")

    job = response
    poll_started_at = time.monotonic()
    while job.get("status") in {"queued", "in_progress"}:
        _raise_if_poll_timed_out(
            provider="OpenAI",
            provider_job_id=video_id,
            started_at=poll_started_at,
            engine_pack=engine_pack,
        )
        time.sleep(engine_pack.retry_policy.poll_interval_seconds)
        job = _request_json(
            url=f"{OPENAI_BASE_URL}/videos/{video_id}",
            method="GET",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=60,
        )

    status = _read_string(job, "status")
    if status != "completed":
        error = job.get("error") if isinstance(job.get("error"), dict) else {}
        message = _read_string(error, "message") or f"OpenAI video job ended with status={status}"
        code = _read_string(error, "code")
        raise VideoGenerationError(
            f"{message}{f' ({code})' if code else ''}",
            retryable=False,
        )

    content_url = f"{OPENAI_BASE_URL}/videos/{video_id}/content"
    video_bytes = _request_bytes(
        url=content_url,
        method="GET",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=300,
    )
    return VideoGenerationResult(
        video_bytes=video_bytes,
        media_type="video/mp4",
        model_used=engine_pack.target_model,
        request_id=video_id,
        provider_job_id=video_id,
    )


def _prepare_openai_input_reference(
    reference: VideoReferenceInput,
    resolution: str,
) -> tuple[str, bytes, str]:
    target_size = _openai_resolution_size(resolution)
    original_bytes = reference.path.read_bytes()
    if target_size is None:
        return reference.path.name, original_bytes, reference.media_type

    with Image.open(io.BytesIO(original_bytes)) as image:
        if image.size == target_size:
            return reference.path.name, original_bytes, reference.media_type

        fitted = ImageOps.fit(
            image.convert("RGB"),
            target_size,
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5),
        )
        buffer = io.BytesIO()
        fitted.save(buffer, format="PNG")
        return f"{reference.path.stem}_openai_input.png", buffer.getvalue(), "image/png"


def _openai_resolution_size(resolution: str) -> tuple[int, int] | None:
    if "x" not in resolution:
        return None
    width_text, height_text = resolution.lower().split("x", 1)
    try:
        return int(width_text), int(height_text)
    except ValueError:
        return None


def _generate_video_google(
    *,
    request: VideoGenerationRequest,
    engine_pack: EnginePack,
) -> VideoGenerationResult:
    try:
        api_key = require_env("GEMINI_API_KEY")
    except RuntimeError as exc:
        raise VideoGenerationError(str(exc)) from exc

    instance: dict[str, Any] = {"prompt": request.prompt}
    if request.first_frame is not None:
        instance["image"] = _google_image_payload(request.first_frame)
    if request.last_frame is not None:
        instance["lastFrame"] = _google_image_payload(request.last_frame)
    if request.reference_images:
        instance["referenceImages"] = [
            {
                "image": _google_image_payload(item),
                "referenceType": "asset",
            }
            for item in request.reference_images
        ]

    parameters: dict[str, Any] = {}
    if request.resolution:
        parameters["resolution"] = request.resolution
    if request.aspect_ratio:
        parameters["aspectRatio"] = request.aspect_ratio
    if request.duration_seconds:
        parameters["durationSeconds"] = request.duration_seconds
    for key, value in request.provider_params.items():
        if value is not None:
            parameters[key] = value

    payload: dict[str, Any] = {"instances": [instance]}
    if parameters:
        payload["parameters"] = parameters

    response = _request_json(
        url=f"{GOOGLE_BASE_URL}/models/{engine_pack.target_model}:predictLongRunning",
        method="POST",
        headers={
            "x-goog-api-key": api_key,
            "Content-Type": "application/json",
        },
        body=json.dumps(payload).encode("utf-8"),
        timeout=120,
    )
    operation_name = _read_string(response, "name")
    if not operation_name:
        raise VideoGenerationError(f"Google video response missing operation name: {response}")

    status = response
    poll_started_at = time.monotonic()
    while status.get("done") is not True:
        _raise_if_poll_timed_out(
            provider="Google",
            provider_job_id=operation_name,
            started_at=poll_started_at,
            engine_pack=engine_pack,
        )
        time.sleep(engine_pack.retry_policy.poll_interval_seconds)
        status = _request_json(
            url=f"{GOOGLE_BASE_URL}/{urllib.parse.quote(operation_name, safe='/')}",
            method="GET",
            headers={"x-goog-api-key": api_key},
            timeout=60,
        )

    error = status.get("error")
    if isinstance(error, dict):
        message = _read_string(error, "message") or "Google video generation failed"
        code = _read_string(error, "status")
        raise VideoGenerationError(
            f"{message}{f' ({code})' if code else ''}",
            retryable=False,
        )

    video_uri = _google_video_uri(status)
    if not video_uri:
        raise VideoGenerationError(f"Google video operation missing output URI: {status}")

    video_bytes = _request_bytes(
        url=video_uri,
        method="GET",
        headers={"x-goog-api-key": api_key},
        timeout=300,
    )
    return VideoGenerationResult(
        video_bytes=video_bytes,
        media_type="video/mp4",
        model_used=engine_pack.target_model,
        request_id=operation_name,
        provider_job_id=operation_name,
    )


def _generate_video_xai(
    *,
    request: VideoGenerationRequest,
    engine_pack: EnginePack,
) -> VideoGenerationResult:
    try:
        api_key = require_env("XAI_API_KEY")
    except RuntimeError as exc:
        raise VideoGenerationError(str(exc)) from exc

    payload: dict[str, Any] = {
        "model": engine_pack.target_model,
        "prompt": request.prompt,
        "duration": request.duration_seconds,
    }
    if request.aspect_ratio:
        payload["aspect_ratio"] = request.aspect_ratio
    if request.resolution:
        payload["resolution"] = request.resolution
    for key, value in request.provider_params.items():
        if value is not None:
            payload[key] = value

    response = _request_json(
        url=f"{XAI_BASE_URL}/videos/generations",
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        body=json.dumps(payload).encode("utf-8"),
        timeout=120,
    )
    request_id = _read_string(response, "request_id")
    if not request_id:
        raise VideoGenerationError(f"xAI video response missing request_id: {response}")

    status_payload = _request_json(
        url=f"{XAI_BASE_URL}/videos/{urllib.parse.quote(request_id, safe='')}",
        method="GET",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=60,
    )
    status = _read_string(status_payload, "status")
    poll_started_at = time.monotonic()
    while status == "pending":
        _raise_if_poll_timed_out(
            provider="xAI",
            provider_job_id=request_id,
            started_at=poll_started_at,
            engine_pack=engine_pack,
        )
        time.sleep(engine_pack.retry_policy.poll_interval_seconds)
        status_payload = _request_json(
            url=f"{XAI_BASE_URL}/videos/{urllib.parse.quote(request_id, safe='')}",
            method="GET",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=60,
        )
        status = _read_string(status_payload, "status")

    if status != "done":
        error = status_payload.get("error") if isinstance(status_payload.get("error"), dict) else {}
        message = _read_string(error, "message") or (
            f"xAI video job ended with status={status or 'unknown'}"
        )
        code = _read_string(error, "code") or _read_string(error, "type")
        raise VideoGenerationError(
            f"{message}{f' ({code})' if code else ''}",
            retryable=False,
        )

    video_url = _xai_video_url(status_payload)
    if not video_url:
        raise VideoGenerationError(f"xAI video result missing output URL: {status_payload}")

    video_bytes = _request_bytes(
        url=video_url,
        method="GET",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=300,
    )
    return VideoGenerationResult(
        video_bytes=video_bytes,
        media_type="video/mp4",
        model_used=_read_string(status_payload, "model") or engine_pack.target_model,
        request_id=request_id,
        provider_job_id=request_id,
    )


def _raise_if_poll_timed_out(
    *,
    provider: str,
    provider_job_id: str,
    started_at: float,
    engine_pack: EnginePack,
) -> None:
    elapsed_seconds = time.monotonic() - started_at
    max_poll_seconds = float(engine_pack.retry_policy.max_poll_seconds)
    if elapsed_seconds <= max_poll_seconds:
        return
    raise VideoGenerationError(
        f"{provider} video job {provider_job_id} timed out after "
        f"{max_poll_seconds:g}s waiting for completion",
        retryable=False,
    )


def _request_json(
    *,
    url: str,
    method: str,
    headers: dict[str, str],
    body: bytes | None = None,
    timeout: int = 60,
) -> dict[str, Any]:
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise VideoGenerationError(
            f"HTTP {exc.code}: {detail}",
            retryable=exc.code in {408, 429, 500, 502, 503, 504},
            status_code=exc.code,
        ) from exc
    except urllib.error.URLError as exc:
        raise VideoGenerationError(
            f"Network error: {exc.reason}",
            retryable=True,
        ) from exc

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise VideoGenerationError("Video API returned invalid JSON") from exc
    if not isinstance(payload, dict):
        raise VideoGenerationError(f"Expected dict JSON response, got: {type(payload)!r}")
    return payload


def _request_bytes(
    *,
    url: str,
    method: str,
    headers: dict[str, str],
    timeout: int = 120,
) -> bytes:
    req = urllib.request.Request(url, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise VideoGenerationError(
            f"HTTP {exc.code}: {detail}",
            retryable=exc.code in {408, 429, 500, 502, 503, 504},
            status_code=exc.code,
        ) from exc
    except urllib.error.URLError as exc:
        raise VideoGenerationError(
            f"Network error: {exc.reason}",
            retryable=True,
        ) from exc


def _encode_multipart_form(
    *,
    fields: list[tuple[str, str]],
    files: list[tuple[str, str, bytes, str]],
) -> tuple[bytes, str]:
    boundary = f"----cineforge-{uuid.uuid4().hex}"
    chunks: list[bytes] = []

    for name, value in fields:
        chunks.extend(
            [
                f"--{boundary}\r\n".encode(),
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(),
                value.encode("utf-8"),
                b"\r\n",
            ]
        )

    for field_name, filename, content, media_type in files:
        chunks.extend(
            [
                f"--{boundary}\r\n".encode(),
                (
                    f'Content-Disposition: form-data; name="{field_name}"; '
                    f'filename="{filename}"\r\n'
                ).encode(),
                f"Content-Type: {media_type}\r\n\r\n".encode(),
                content,
                b"\r\n",
            ]
        )

    chunks.append(f"--{boundary}--\r\n".encode())
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def _google_image_payload(reference: VideoReferenceInput) -> dict[str, Any]:
    return {
        "bytesBase64Encoded": base64.b64encode(reference.path.read_bytes()).decode("ascii"),
        "mimeType": reference.media_type,
    }


def _google_video_uri(payload: dict[str, Any]) -> str | None:
    response = payload.get("response")
    if not isinstance(response, dict):
        return None

    generated = response.get("generateVideoResponse")
    if isinstance(generated, dict):
        samples = generated.get("generatedSamples")
        if isinstance(samples, list) and samples:
            first = samples[0]
            if isinstance(first, dict):
                video = first.get("video")
                if isinstance(video, dict):
                    return _read_string(video, "uri")

    generated_videos = response.get("generatedVideos")
    if isinstance(generated_videos, list) and generated_videos:
        first = generated_videos[0]
        if isinstance(first, dict):
            video = first.get("video")
            if isinstance(video, dict):
                return _read_string(video, "uri")

    return None


def _xai_video_url(payload: dict[str, Any]) -> str | None:
    video = payload.get("video")
    if not isinstance(video, dict):
        return None
    return _read_string(video, "url")


def _read_string(payload: dict[str, Any], key: str) -> str | None:
    value = payload.get(key)
    if isinstance(value, str) and value.strip():
        return value
    return None
