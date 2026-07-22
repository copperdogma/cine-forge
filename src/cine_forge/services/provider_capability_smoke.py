"""On-demand live capability smoke for default shipped AI lanes."""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from cine_forge.ai.provider_failures import classify_provider_failure_status
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
from cine_forge.services.provider_capability_probes import (
    HttpJsonError,
    request_id_from_headers,
    run_live_image_probe,
    run_live_text_probe,
    run_live_video_probe,
)

logger = logging.getLogger(__name__)

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
        probe_id="google_script_bible_text_default",
        label="Google Script Bible model callability",
        provider="google",
        capability_tested="text_generation",
        env_name="GEMINI_API_KEY",
        model="gemini-3.5-flash-lite",
        surface_tested=(
            "Script Bible model ID callability only; structured-output quality is not tested"
        ),
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
        self._text_probe = text_probe or run_live_text_probe
        self._image_probe = image_probe or run_live_image_probe
        self._video_probe = video_probe or run_live_video_probe
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


def _request_id_from_exception(exc: Exception) -> str | None:
    if isinstance(exc, HttpJsonError):
        return request_id_from_headers(exc.headers)
    return StageRetryPolicy.extract_request_id(str(exc))


def _error_code_from_exception(exc: Exception) -> str | None:
    if isinstance(exc, HttpJsonError):
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
