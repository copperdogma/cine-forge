"""Provider transports used by the explicit live capability smoke service."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

from cine_forge.ai.image import ImageGenerationError, generate_image
from cine_forge.ai.video import (
    VideoGenerationError,
    VideoGenerationRequest,
    generate_video,
)
from cine_forge.env import resolve_env
from cine_forge.schemas.render import EnginePack

OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"
ANTHROPIC_MESSAGES_URL = "https://api.anthropic.com/v1/messages"
GEMINI_GENERATE_CONTENT_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
)
TEXT_PROMPT = "Reply with exactly OK and nothing else."
IMAGE_PROMPT = (
    "Minimal capability smoke image: a single charcoal cube centered on a plain light-gray "
    "background. No text, logos, or watermarks."
)
VIDEO_PROMPT = (
    "Capability smoke video: a simple cinematic shot of a gray cube on a table with subtle "
    "camera drift. No text, logos, or watermarks."
)


class ProbeSpec(Protocol):
    probe_id: str
    provider: str
    env_name: str
    model: str
    engine_pack_id: str | None


@dataclass(frozen=True)
class HttpJsonResponse:
    headers: dict[str, str]
    payload: Any


class HttpJsonError(RuntimeError):
    def __init__(
        self,
        *,
        status_code: int,
        message: str,
        headers: dict[str, str],
        payload: Any,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        self.headers = headers
        self.payload = payload


class HttpTransportError(RuntimeError):
    pass


def run_live_text_probe(spec: ProbeSpec, timeout_seconds: float) -> dict[str, Any]:
    if spec.provider == "anthropic":
        return _run_anthropic_text_probe(spec, timeout_seconds)
    if spec.provider == "google":
        return _run_google_text_probe(spec, timeout_seconds)
    if spec.provider == "openai":
        return _run_openai_text_probe(spec, timeout_seconds)
    raise RuntimeError(f"Unsupported text probe provider: {spec.provider}")


def _run_anthropic_text_probe(spec: ProbeSpec, timeout_seconds: float) -> dict[str, Any]:
    response = http_request_json(
        url=ANTHROPIC_MESSAGES_URL,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "x-api-key": resolve_env(spec.env_name) or "",
            "anthropic-version": "2023-06-01",
        },
        body={
            "model": spec.model,
            "max_tokens": 8,
            "temperature": 0,
            "messages": [{"role": "user", "content": TEXT_PROMPT}],
        },
        timeout_seconds=timeout_seconds,
    )
    if not anthropic_text_from_payload(response.payload).strip():
        raise RuntimeError("Anthropic live smoke returned an empty response.")
    return {
        "model_used": spec.model,
        "request_id": request_id_from_headers(response.headers),
    }


def _run_google_text_probe(spec: ProbeSpec, timeout_seconds: float) -> dict[str, Any]:
    response = http_request_json(
        url=GEMINI_GENERATE_CONTENT_URL.format(
            model=urllib.parse.quote(spec.model, safe=""),
            api_key=urllib.parse.quote(resolve_env(spec.env_name) or "", safe=""),
        ),
        method="POST",
        headers={"Content-Type": "application/json"},
        body={
            "contents": [{"role": "user", "parts": [{"text": TEXT_PROMPT}]}],
            "generationConfig": {
                "maxOutputTokens": 256,
                "thinkingConfig": {"thinkingLevel": "minimal"},
            },
        },
        timeout_seconds=timeout_seconds,
    )
    response_text = google_text_from_payload(response.payload).strip()
    if response_text != "OK":
        raise RuntimeError(
            "Google callability smoke expected exactly 'OK'; "
            f"received {response_text!r}."
        )
    return {
        "model_used": spec.model,
        "request_id": request_id_from_headers(response.headers),
    }


def _run_openai_text_probe(spec: ProbeSpec, timeout_seconds: float) -> dict[str, Any]:
    response = http_request_json(
        url=OPENAI_CHAT_URL,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {resolve_env(spec.env_name) or ''}",
        },
        body={
            "model": spec.model,
            "messages": [{"role": "user", "content": TEXT_PROMPT}],
            "temperature": 0,
            "max_completion_tokens": 8,
        },
        timeout_seconds=timeout_seconds,
    )
    if not openai_text_from_payload(response.payload).strip():
        raise RuntimeError("OpenAI live smoke returned an empty response.")
    return {
        "model_used": spec.model,
        "request_id": request_id_from_headers(response.headers),
    }


def run_live_image_probe(spec: ProbeSpec) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "prompt": IMAGE_PROMPT,
        "entity_type": "prop",
        "model": spec.model,
    }
    if spec.provider == "openai":
        kwargs["quality"] = "low"
    else:
        kwargs["aspect_ratio"] = "1:1"
    image_bytes, model_used = generate_image(**kwargs)
    if not image_bytes:
        raise ImageGenerationError("Live image smoke returned empty image bytes.")
    return {"model_used": model_used}


def run_live_video_probe(
    spec: ProbeSpec,
    engine_pack_loader: Callable[[str], EnginePack],
) -> dict[str, Any]:
    if spec.engine_pack_id is None:
        raise RuntimeError(f"Video probe '{spec.probe_id}' is missing an engine pack.")
    engine_pack = engine_pack_loader(spec.engine_pack_id)
    request = VideoGenerationRequest(
        prompt=VIDEO_PROMPT,
        duration_seconds=min(engine_pack.limits.supported_durations_seconds),
        resolution=_default_video_resolution(engine_pack),
        aspect_ratio=_default_video_aspect_ratio(engine_pack),
    )
    result = generate_video(request=request, engine_pack=engine_pack)
    if not result.video_bytes:
        raise VideoGenerationError("Live video smoke returned empty video bytes.")
    return {"model_used": result.model_used, "request_id": result.request_id}


def http_request_json(
    *,
    url: str,
    method: str,
    headers: dict[str, str],
    body: dict[str, Any] | None,
    timeout_seconds: float,
) -> HttpJsonResponse:
    request_bytes = json.dumps(body).encode("utf-8") if body is not None else None
    request = urllib.request.Request(url, data=request_bytes, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
            body_text = response.read().decode("utf-8")
            return HttpJsonResponse(
                headers={name.lower(): value for name, value in response.headers.items()},
                payload=json.loads(body_text) if body_text else {},
            )
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        payload = _parse_json_body(body_text)
        raise HttpJsonError(
            status_code=exc.code,
            message=_error_message(exc.code, payload, body_text),
            headers={name.lower(): value for name, value in exc.headers.items()},
            payload=payload,
        ) from exc
    except urllib.error.URLError as exc:
        raise HttpTransportError(f"request failed: {exc.reason}") from exc


def anthropic_text_from_payload(payload: Any) -> str:
    if not isinstance(payload, dict) or not isinstance(payload.get("content"), list):
        return ""
    return "".join(
        str(item.get("text", ""))
        for item in payload["content"]
        if isinstance(item, dict) and item.get("type") == "text"
    )


def google_text_from_payload(payload: Any) -> str:
    if not isinstance(payload, dict):
        return ""
    candidates = payload.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        return ""
    content = candidates[0].get("content") if isinstance(candidates[0], dict) else None
    parts = content.get("parts") if isinstance(content, dict) else None
    if not isinstance(parts, list):
        return ""
    return "".join(str(item.get("text", "")) for item in parts if isinstance(item, dict))


def openai_text_from_payload(payload: Any) -> str:
    if not isinstance(payload, dict):
        return ""
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    content = message.get("content", "") if isinstance(message, dict) else ""
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    return "".join(str(item.get("text", "")) for item in content if isinstance(item, dict))


def request_id_from_headers(headers: dict[str, str]) -> str | None:
    for name in ("request-id", "x-request-id", "anthropic-request-id"):
        if headers.get(name):
            return headers[name]
    return None


def _default_video_resolution(engine_pack: EnginePack) -> str:
    resolution = engine_pack.request_defaults.get("default_resolution")
    if isinstance(resolution, str) and resolution.strip():
        return resolution.strip()
    landscape_size = engine_pack.request_defaults.get("landscape_size")
    if isinstance(landscape_size, str) and landscape_size.strip():
        return landscape_size.strip()
    return engine_pack.limits.supported_resolutions[0]


def _default_video_aspect_ratio(engine_pack: EnginePack) -> str:
    ratio = engine_pack.request_defaults.get("landscape_aspect_ratio")
    if isinstance(ratio, str) and ratio.strip():
        return ratio.strip()
    return engine_pack.limits.supported_aspect_ratios[0]


def _parse_json_body(body_text: str) -> Any:
    if not body_text.strip():
        return {}
    try:
        return json.loads(body_text)
    except json.JSONDecodeError:
        return {"raw_body": body_text.strip()}


def _error_message(status_code: int, payload: Any, body_text: str) -> str:
    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, dict):
            detail = error.get("message") or error.get("details") or error.get("status")
            if detail:
                return str(detail)
        if isinstance(error, str) and error.strip():
            return error.strip()
        for key in ("detail", "message", "raw_body"):
            detail = payload.get(key)
            if isinstance(detail, str) and detail.strip():
                return detail.strip()
    return body_text.strip() or f"HTTP {status_code}"
