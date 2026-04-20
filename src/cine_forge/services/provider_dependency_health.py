"""Cached provider dependency health checks for required runtime providers."""

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

from cine_forge.ai.provider_failures import classify_provider_failure_status
from cine_forge.env import preferred_env_name, provider_env_names, resolve_env
from cine_forge.schemas.provider_health import (
    ProviderDependencyCheck,
    ProviderDependencyHealthSnapshot,
    ProviderDependencyOverallStatus,
    ProviderDependencyStatus,
    ProviderKey,
)

logger = logging.getLogger(__name__)

OPENAI_MODEL_URL = "https://api.openai.com/v1/models/{model}"
ANTHROPIC_MODEL_URL = "https://api.anthropic.com/v1/models/{model}"
GEMINI_MODEL_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}?key={api_key}"


@dataclass(frozen=True)
class _ProviderSpec:
    provider: ProviderKey
    env_name: str
    model: str


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


_REQUIRED_PROVIDER_SPECS: tuple[_ProviderSpec, ...] = (
    _ProviderSpec("anthropic", "ANTHROPIC_API_KEY", "claude-sonnet-4-6"),
    _ProviderSpec("google", "GEMINI_API_KEY", "gemini-2.5-flash-lite"),
    _ProviderSpec("openai", "OPENAI_API_KEY", "gpt-4.1-mini"),
)


class ProviderDependencyHealthService:
    """Probe required provider credentials with cheap model-access checks."""

    def __init__(
        self,
        *,
        timeout_seconds: float = 10.0,
        http_get_json: Callable[[str, dict[str, str], float], _HttpJsonResponse] | None = None,
    ) -> None:
        self._timeout_seconds = timeout_seconds
        self._http_get_json = http_get_json or _http_get_json
        self._snapshot_lock = threading.RLock()
        self._refresh_lock = threading.Lock()
        self._startup_thread: threading.Thread | None = None
        self._snapshot = self._build_unchecked_snapshot()

    def get_snapshot(self, *, refresh: bool = False) -> ProviderDependencyHealthSnapshot:
        """Return the current cached snapshot, optionally forcing a refresh."""
        if refresh:
            return self.refresh()
        with self._snapshot_lock:
            return self._snapshot.model_copy(deep=True)

    def refresh(self) -> ProviderDependencyHealthSnapshot:
        """Refresh provider dependency health synchronously."""
        with self._refresh_lock:
            providers: dict[ProviderKey, ProviderDependencyCheck] = {}
            for spec in _REQUIRED_PROVIDER_SPECS:
                providers[spec.provider] = self._probe_provider(spec)
            snapshot = _build_snapshot(providers)
            with self._snapshot_lock:
                self._snapshot = snapshot
                return self._snapshot.model_copy(deep=True)

    def start_background_refresh(self) -> None:
        """Prime the cache on startup without blocking app readiness."""
        with self._snapshot_lock:
            if self._startup_thread is not None and self._startup_thread.is_alive():
                return
            thread = threading.Thread(
                target=self._refresh_in_background,
                name="provider-dependency-health-startup",
                daemon=True,
            )
            self._startup_thread = thread
            thread.start()

    def _refresh_in_background(self) -> None:
        try:
            self.refresh()
        except Exception:  # pragma: no cover - defensive logging path
            logger.exception("Startup provider dependency health refresh failed.")

    def _build_unchecked_snapshot(self) -> ProviderDependencyHealthSnapshot:
        providers: dict[ProviderKey, ProviderDependencyCheck] = {}
        for spec in _REQUIRED_PROVIDER_SPECS:
            providers[spec.provider] = _unchecked_result(spec)
        return _build_snapshot(providers)

    def _probe_provider(self, spec: _ProviderSpec) -> ProviderDependencyCheck:
        preferred_name = preferred_env_name(spec.env_name)
        accepted_names = list(provider_env_names(spec.env_name))
        checked_at = datetime.now(UTC)
        api_key = resolve_env(spec.env_name)
        if not api_key:
            return ProviderDependencyCheck(
                provider=spec.provider,
                configured=False,
                status="missing",
                preferred_env_var=preferred_name,
                accepted_env_vars=accepted_names,
                model_tested=spec.model,
                last_checked_at=checked_at,
                latency_ms=0,
                failure_message=_missing_env_message(spec.env_name),
            )

        url = _provider_probe_url(spec, api_key)
        headers = _provider_probe_headers(spec, api_key)
        started = time.perf_counter()
        try:
            response = self._http_get_json(url, headers, self._timeout_seconds)
            latency_ms = _latency_ms(started)
            return ProviderDependencyCheck(
                provider=spec.provider,
                configured=True,
                status="ok",
                preferred_env_var=preferred_name,
                accepted_env_vars=accepted_names,
                model_tested=spec.model,
                last_checked_at=checked_at,
                latency_ms=latency_ms,
                request_id=_request_id_from_headers(response.headers),
            )
        except _HttpJsonError as exc:
            latency_ms = _latency_ms(started)
            return ProviderDependencyCheck(
                provider=spec.provider,
                configured=True,
                status=_status_from_failure(
                    message=exc.message,
                    error_code=str(exc.status_code),
                ),
                preferred_env_var=preferred_name,
                accepted_env_vars=accepted_names,
                model_tested=spec.model,
                last_checked_at=checked_at,
                latency_ms=latency_ms,
                failure_message=exc.message,
                request_id=_request_id_from_headers(exc.headers),
            )
        except _HttpTransportError as exc:
            latency_ms = _latency_ms(started)
            return ProviderDependencyCheck(
                provider=spec.provider,
                configured=True,
                status=_status_from_failure(message=str(exc), error_code=None),
                preferred_env_var=preferred_name,
                accepted_env_vars=accepted_names,
                model_tested=spec.model,
                last_checked_at=checked_at,
                latency_ms=latency_ms,
                failure_message=str(exc),
            )


def _unchecked_result(spec: _ProviderSpec) -> ProviderDependencyCheck:
    configured = resolve_env(spec.env_name) is not None
    preferred_name = preferred_env_name(spec.env_name)
    accepted_names = list(provider_env_names(spec.env_name))
    return ProviderDependencyCheck(
        provider=spec.provider,
        configured=configured,
        status="unknown" if configured else "missing",
        preferred_env_var=preferred_name,
        accepted_env_vars=accepted_names,
        model_tested=spec.model,
        failure_message=None if configured else _missing_env_message(spec.env_name),
    )


def _build_snapshot(
    providers: dict[ProviderKey, ProviderDependencyCheck],
) -> ProviderDependencyHealthSnapshot:
    checked_at_values = [
        check.last_checked_at
        for check in providers.values()
        if check.last_checked_at is not None
    ]
    checked_at = max(checked_at_values) if checked_at_values else None
    return ProviderDependencyHealthSnapshot(
        status=_overall_status(list(providers.values())),
        checked_at=checked_at,
        providers=providers,
    )


def _overall_status(
    checks: list[ProviderDependencyCheck],
) -> ProviderDependencyOverallStatus:
    statuses = [check.status for check in checks]
    if statuses and all(status == "ok" for status in statuses):
        return "ok"
    if any(status != "unknown" for status in statuses):
        return "degraded"
    return "unknown"


def _provider_probe_url(spec: _ProviderSpec, api_key: str) -> str:
    quoted_model = urllib.parse.quote(spec.model, safe="")
    if spec.provider == "anthropic":
        return ANTHROPIC_MODEL_URL.format(model=quoted_model)
    if spec.provider == "google":
        return GEMINI_MODEL_URL.format(
            model=quoted_model,
            api_key=urllib.parse.quote(api_key, safe=""),
        )
    return OPENAI_MODEL_URL.format(model=quoted_model)


def _provider_probe_headers(spec: _ProviderSpec, api_key: str) -> dict[str, str]:
    if spec.provider == "anthropic":
        return {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        }
    if spec.provider == "openai":
        return {
            "Authorization": f"Bearer {api_key}",
        }
    return {}


def _status_from_failure(message: str, error_code: str | None) -> ProviderDependencyStatus:
    status = classify_provider_failure_status(message=message, error_code=error_code)
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


def _latency_ms(started: float) -> int:
    return max(0, int(round((time.perf_counter() - started) * 1000)))


def _http_get_json(
    url: str,
    headers: dict[str, str],
    timeout_seconds: float,
) -> _HttpJsonResponse:
    request = urllib.request.Request(url, headers=headers, method="GET")
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
