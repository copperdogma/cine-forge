"""On-demand live capability smoke for default shipped AI lanes."""

from __future__ import annotations

import json
import logging
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from cine_forge.ai.image import ImageGenerationError, generate_image
from cine_forge.ai.provider_failures import classify_provider_failure_status
from cine_forge.ai.video import (
    VideoGenerationError,
    VideoGenerationRequest,
    generate_video,
)
from cine_forge.driver.retry_policy import StageRetryPolicy
from cine_forge.env import preferred_env_name, provider_env_names, resolve_env
from cine_forge.modules.generation.render_adapter_v1.support import load_engine_pack
from cine_forge.schemas.provider_health import (
    ProviderCapabilitySmokeCheck,
    ProviderCapabilitySmokeSnapshot,
    ProviderCapabilityTested,
    ProviderDependencyOverallStatus,
    ProviderDependencyStatus,
    ProviderKey,
)
from cine_forge.schemas.render import EnginePack

logger = logging.getLogger(__name__)

OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"
ANTHROPIC_MESSAGES_URL = "https://api.anthropic.com/v1/messages"
GEMINI_GENERATE_CONTENT_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
)

_TEXT_PROMPT = "Reply with exactly OK and nothing else."
_IMAGE_PROMPT = (
    "Minimal capability smoke image: a single charcoal cube centered on a plain light-gray "
    "background. No text, logos, or watermarks."
)
_VIDEO_PROMPT = (
    "Capability smoke video: a simple cinematic shot of a gray cube on a table with subtle "
    "camera drift. No text, logos, or watermarks."
)


@dataclass(frozen=True)
class _ProbeSpec:
    probe_id: str
    label: str
    provider: ProviderKey
    capability_tested: ProviderCapabilityTested
    env_name: str
    model: str
    surface_tested: str
    engine_pack_id: str | None = None


@dataclass(frozen=True)
class _HttpJsonResponse:
    headers: dict[str, str]
    payload: Any


class _HttpJsonError(RuntimeError):
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


class _HttpTransportError(RuntimeError):
    pass


TextProbe = Callable[[_ProbeSpec, float], dict[str, Any]]
ImageProbe = Callable[[_ProbeSpec], dict[str, Any]]
VideoProbe = Callable[[_ProbeSpec, Callable[[str], EnginePack]], dict[str, Any]]


_LIVE_PROBE_SPECS: tuple[_ProbeSpec, ...] = (
    _ProbeSpec(
        probe_id="anthropic_text_default",
        label="Anthropic text generation",
        provider="anthropic",
        capability_tested="text_generation",
        env_name="ANTHROPIC_API_KEY",
        model="claude-sonnet-4-6",
        surface_tested="Default text analysis lane",
    ),
    _ProbeSpec(
        probe_id="google_text_default",
        label="Google text generation",
        provider="google",
        capability_tested="text_generation",
        env_name="GEMINI_API_KEY",
        model="gemini-2.5-flash-lite",
        surface_tested="Default text analysis lane",
    ),
    _ProbeSpec(
        probe_id="openai_text_default",
        label="OpenAI text generation",
        provider="openai",
        capability_tested="text_generation",
        env_name="OPENAI_API_KEY",
        model="gpt-4.1-mini",
        surface_tested="Default text analysis lane",
    ),
    _ProbeSpec(
        probe_id="openai_storyboard_image_default",
        label="OpenAI storyboard image generation",
        provider="openai",
        capability_tested="image_generation",
        env_name="OPENAI_API_KEY",
        model="gpt-image-2",
        surface_tested="Storyboard generation default lane",
    ),
    _ProbeSpec(
        probe_id="google_design_study_image_default",
        label="Google design study image generation",
        provider="google",
        capability_tested="image_generation",
        env_name="GEMINI_API_KEY",
        model="imagen-4.0-generate-001",
        surface_tested="Design Study default image lane",
    ),
    _ProbeSpec(
        probe_id="openai_design_study_image_alt",
        label="OpenAI alternate image generation",
        provider="openai",
        capability_tested="image_generation",
        env_name="OPENAI_API_KEY",
        model="gpt-image-1",
        surface_tested="Design Study alternate image lane",
    ),
    _ProbeSpec(
        probe_id="google_render_video_default",
        label="Google render video generation",
        provider="google",
        capability_tested="video_generation",
        env_name="GEMINI_API_KEY",
        model="veo-3.1-generate-preview",
        surface_tested="Scene render default lane",
        engine_pack_id="google_veo31",
    ),
    _ProbeSpec(
        probe_id="xai_ai_previz_video_default",
        label="xAI AI previz video generation",
        provider="xai",
        capability_tested="video_generation",
        env_name="XAI_API_KEY",
        model="grok-imagine-video",
        surface_tested="AI Previz shipped default lane",
        engine_pack_id="xai_grok_imagine_video",
    ),
)


class ProviderCapabilitySmokeService:
    """Run tiny real calls against default shipped AI capability lanes."""

    def __init__(
        self,
        *,
        timeout_seconds: float = 30.0,
        text_probe: TextProbe | None = None,
        image_probe: ImageProbe | None = None,
        video_probe: VideoProbe | None = None,
        engine_pack_loader: Callable[[str], EnginePack] | None = None,
    ) -> None:
        self._timeout_seconds = timeout_seconds
        self._text_probe = text_probe or _run_live_text_probe
        self._image_probe = image_probe or _run_live_image_probe
        self._video_probe = video_probe or _run_live_video_probe
        self._engine_pack_loader = engine_pack_loader or load_engine_pack
        self._snapshot_lock = threading.RLock()
        self._refresh_lock = threading.Lock()
        self._snapshot = self._build_unchecked_snapshot()

    def get_snapshot(self, *, refresh: bool = False) -> ProviderCapabilitySmokeSnapshot:
        if refresh:
            return self.refresh()
        with self._snapshot_lock:
            return self._snapshot.model_copy(deep=True)

    def refresh(self) -> ProviderCapabilitySmokeSnapshot:
        with self._refresh_lock:
            checks = [self._probe(spec) for spec in _LIVE_PROBE_SPECS]
            snapshot = _build_snapshot(checks)
            with self._snapshot_lock:
                self._snapshot = snapshot
                return self._snapshot.model_copy(deep=True)

    def _build_unchecked_snapshot(self) -> ProviderCapabilitySmokeSnapshot:
        return _build_snapshot([_unchecked_result(spec) for spec in _LIVE_PROBE_SPECS])

    def _probe(self, spec: _ProbeSpec) -> ProviderCapabilitySmokeCheck:
        preferred_name = preferred_env_name(spec.env_name)
        accepted_names = list(provider_env_names(spec.env_name))
        checked_at = datetime.now(UTC)
        api_key = resolve_env(spec.env_name)
        if not api_key:
            return ProviderCapabilitySmokeCheck(
                probe_id=spec.probe_id,
                label=spec.label,
                provider=spec.provider,
                configured=False,
                status="missing",
                preferred_env_var=preferred_name,
                accepted_env_vars=accepted_names,
                capability_tested=spec.capability_tested,
                model_tested=spec.model,
                engine_pack_id=spec.engine_pack_id,
                surface_tested=spec.surface_tested,
                last_checked_at=checked_at,
                latency_ms=0,
                failure_message=_missing_env_message(spec.env_name),
            )

        started = time.perf_counter()
        try:
            if spec.capability_tested == "text_generation":
                result = self._text_probe(spec, self._timeout_seconds)
            elif spec.capability_tested == "image_generation":
                result = self._image_probe(spec)
            else:
                result = self._video_probe(spec, self._engine_pack_loader)
            return ProviderCapabilitySmokeCheck(
                probe_id=spec.probe_id,
                label=spec.label,
                provider=spec.provider,
                configured=True,
                status="ok",
                preferred_env_var=preferred_name,
                accepted_env_vars=accepted_names,
                capability_tested=spec.capability_tested,
                model_tested=str(result.get("model_used") or spec.model),
                engine_pack_id=spec.engine_pack_id,
                surface_tested=spec.surface_tested,
                last_checked_at=checked_at,
                latency_ms=_latency_ms(started),
                request_id=_optional_string(result.get("request_id")),
            )
        except Exception as exc:  # noqa: BLE001
            message = str(exc)
            error_code = _error_code_from_exception(exc)
            return ProviderCapabilitySmokeCheck(
                probe_id=spec.probe_id,
                label=spec.label,
                provider=spec.provider,
                configured=True,
                status=_status_from_failure(
                    message=message,
                    error_code=error_code,
                    is_transient=bool(getattr(exc, "retryable", False)),
                ),
                preferred_env_var=preferred_name,
                accepted_env_vars=accepted_names,
                capability_tested=spec.capability_tested,
                model_tested=spec.model,
                engine_pack_id=spec.engine_pack_id,
                surface_tested=spec.surface_tested,
                last_checked_at=checked_at,
                latency_ms=_latency_ms(started),
                failure_message=message,
                request_id=_request_id_from_exception(exc),
            )


def _unchecked_result(spec: _ProbeSpec) -> ProviderCapabilitySmokeCheck:
    configured = resolve_env(spec.env_name) is not None
    preferred_name = preferred_env_name(spec.env_name)
    accepted_names = list(provider_env_names(spec.env_name))
    return ProviderCapabilitySmokeCheck(
        probe_id=spec.probe_id,
        label=spec.label,
        provider=spec.provider,
        configured=configured,
        status="unknown" if configured else "missing",
        preferred_env_var=preferred_name,
        accepted_env_vars=accepted_names,
        capability_tested=spec.capability_tested,
        model_tested=spec.model,
        engine_pack_id=spec.engine_pack_id,
        surface_tested=spec.surface_tested,
        failure_message=None if configured else _missing_env_message(spec.env_name),
    )


def _build_snapshot(checks: list[ProviderCapabilitySmokeCheck]) -> ProviderCapabilitySmokeSnapshot:
    checked_at_values = [
        check.last_checked_at for check in checks if check.last_checked_at is not None
    ]
    checked_at = max(checked_at_values) if checked_at_values else None
    return ProviderCapabilitySmokeSnapshot(
        status=_overall_status(checks),
        checked_at=checked_at,
        checks=checks,
    )


def _overall_status(checks: list[ProviderCapabilitySmokeCheck]) -> ProviderDependencyOverallStatus:
    statuses = [check.status for check in checks]
    if statuses and all(status == "ok" for status in statuses):
        return "ok"
    if any(status != "unknown" for status in statuses):
        return "degraded"
    return "unknown"


def _run_live_text_probe(spec: _ProbeSpec, timeout_seconds: float) -> dict[str, Any]:
    if spec.provider == "anthropic":
        return _run_anthropic_text_probe(spec, timeout_seconds)
    if spec.provider == "google":
        return _run_google_text_probe(spec, timeout_seconds)
    if spec.provider == "openai":
        return _run_openai_text_probe(spec, timeout_seconds)
    raise RuntimeError(f"Unsupported text probe provider: {spec.provider}")


def _run_anthropic_text_probe(spec: _ProbeSpec, timeout_seconds: float) -> dict[str, Any]:
    api_key = resolve_env(spec.env_name) or ""
    response = _http_request_json(
        url=ANTHROPIC_MESSAGES_URL,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        body={
            "model": spec.model,
            "max_tokens": 8,
            "temperature": 0,
            "messages": [{"role": "user", "content": _TEXT_PROMPT}],
        },
        timeout_seconds=timeout_seconds,
    )
    text = _anthropic_text_from_payload(response.payload)
    if not text.strip():
        raise RuntimeError("Anthropic live smoke returned an empty response.")
    return {
        "model_used": spec.model,
        "request_id": _request_id_from_headers(response.headers),
    }


def _run_google_text_probe(spec: _ProbeSpec, timeout_seconds: float) -> dict[str, Any]:
    api_key = resolve_env(spec.env_name) or ""
    response = _http_request_json(
        url=GEMINI_GENERATE_CONTENT_URL.format(
            model=urllib.parse.quote(spec.model, safe=""),
            api_key=urllib.parse.quote(api_key, safe=""),
        ),
        method="POST",
        headers={"Content-Type": "application/json"},
        body={
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": _TEXT_PROMPT}],
                }
            ],
            "generationConfig": {
                "temperature": 0,
                "maxOutputTokens": 8,
            },
        },
        timeout_seconds=timeout_seconds,
    )
    text = _google_text_from_payload(response.payload)
    if not text.strip():
        raise RuntimeError("Google live smoke returned an empty response.")
    return {
        "model_used": spec.model,
        "request_id": _request_id_from_headers(response.headers),
    }


def _run_openai_text_probe(spec: _ProbeSpec, timeout_seconds: float) -> dict[str, Any]:
    api_key = resolve_env(spec.env_name) or ""
    response = _http_request_json(
        url=OPENAI_CHAT_URL,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        body={
            "model": spec.model,
            "messages": [{"role": "user", "content": _TEXT_PROMPT}],
            "temperature": 0,
            "max_completion_tokens": 8,
        },
        timeout_seconds=timeout_seconds,
    )
    text = _openai_text_from_payload(response.payload)
    if not text.strip():
        raise RuntimeError("OpenAI live smoke returned an empty response.")
    return {
        "model_used": spec.model,
        "request_id": _request_id_from_headers(response.headers),
    }


def _run_live_image_probe(spec: _ProbeSpec) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "prompt": _IMAGE_PROMPT,
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


def _run_live_video_probe(
    spec: _ProbeSpec,
    engine_pack_loader: Callable[[str], EnginePack],
) -> dict[str, Any]:
    if spec.engine_pack_id is None:
        raise RuntimeError(f"Video probe '{spec.probe_id}' is missing an engine pack.")
    engine_pack = engine_pack_loader(spec.engine_pack_id)
    request = VideoGenerationRequest(
        prompt=_VIDEO_PROMPT,
        duration_seconds=min(engine_pack.limits.supported_durations_seconds),
        resolution=_default_video_resolution(engine_pack),
        aspect_ratio=_default_video_aspect_ratio(engine_pack),
    )
    result = generate_video(request=request, engine_pack=engine_pack)
    if not result.video_bytes:
        raise VideoGenerationError("Live video smoke returned empty video bytes.")
    return {
        "model_used": result.model_used,
        "request_id": result.request_id,
    }


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


def _http_request_json(
    *,
    url: str,
    method: str,
    headers: dict[str, str],
    body: dict[str, Any] | None,
    timeout_seconds: float,
) -> _HttpJsonResponse:
    request_bytes = json.dumps(body).encode("utf-8") if body is not None else None
    request = urllib.request.Request(url, data=request_bytes, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
            body_text = response.read().decode("utf-8")
            payload = json.loads(body_text) if body_text else {}
            return _HttpJsonResponse(
                headers={name.lower(): value for name, value in response.headers.items()},
                payload=payload,
            )
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        payload = _parse_json_body(body_text)
        raise _HttpJsonError(
            status_code=exc.code,
            message=_error_message(exc.code, payload, body_text),
            headers={name.lower(): value for name, value in exc.headers.items()},
            payload=payload,
        ) from exc
    except urllib.error.URLError as exc:
        raise _HttpTransportError(f"request failed: {exc.reason}") from exc


def _anthropic_text_from_payload(payload: Any) -> str:
    if not isinstance(payload, dict):
        return ""
    parts = payload.get("content")
    if not isinstance(parts, list):
        return ""
    return "".join(
        str(item.get("text", ""))
        for item in parts
        if isinstance(item, dict) and item.get("type") == "text"
    )


def _google_text_from_payload(payload: Any) -> str:
    if not isinstance(payload, dict):
        return ""
    candidates = payload.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        return ""
    content = candidates[0].get("content") if isinstance(candidates[0], dict) else None
    if not isinstance(content, dict):
        return ""
    parts = content.get("parts")
    if not isinstance(parts, list):
        return ""
    return "".join(str(item.get("text", "")) for item in parts if isinstance(item, dict))


def _openai_text_from_payload(payload: Any) -> str:
    if not isinstance(payload, dict):
        return ""
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    if not isinstance(message, dict):
        return ""
    content = message.get("content", "")
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    return "".join(str(item.get("text", "")) for item in content if isinstance(item, dict))


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
        detail = payload.get("detail")
        if isinstance(detail, str) and detail.strip():
            return detail.strip()
        message = payload.get("message")
        if isinstance(message, str) and message.strip():
            return message.strip()
        raw_body = payload.get("raw_body")
        if isinstance(raw_body, str) and raw_body.strip():
            return raw_body.strip()
    stripped = body_text.strip()
    if stripped:
        return stripped
    return f"HTTP {status_code}"


def _status_from_failure(
    *,
    message: str,
    error_code: str | None,
    is_transient: bool = False,
) -> ProviderDependencyStatus:
    status = classify_provider_failure_status(
        message=message,
        error_code=error_code,
        is_transient=is_transient,
    )
    if status is None:
        return "unknown"
    return status


def _missing_env_message(env_name: str) -> str:
    accepted = provider_env_names(env_name)
    preferred_name = accepted[0]
    if len(accepted) == 1:
        return f"{preferred_name} is not set"
    return f"{preferred_name} (or legacy {env_name}) is not set"


def _request_id_from_headers(headers: dict[str, str]) -> str | None:
    for name in ("request-id", "x-request-id", "anthropic-request-id"):
        value = headers.get(name)
        if value:
            return value
    return None


def _request_id_from_exception(exc: Exception) -> str | None:
    if isinstance(exc, _HttpJsonError):
        return _request_id_from_headers(exc.headers)
    return StageRetryPolicy.extract_request_id(str(exc))


def _error_code_from_exception(exc: Exception) -> str | None:
    if isinstance(exc, _HttpJsonError):
        return str(exc.status_code)
    status_code = getattr(exc, "status_code", None)
    if status_code is not None:
        return str(status_code)
    return StageRetryPolicy.extract_error_code(str(exc))


def _latency_ms(started: float) -> int:
    return max(0, int(round((time.perf_counter() - started) * 1000)))


def _optional_string(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None
