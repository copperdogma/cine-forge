"""Small HTTP boundary shared by video transports."""

from __future__ import annotations

import http.client
import json
import urllib.error
import urllib.request
from typing import Any

from cine_forge.ai.video_types import VideoGenerationError


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
            provider_response={"http_status": exc.code, "body": detail},
        ) from exc
    except (urllib.error.URLError, OSError, http.client.HTTPException) as exc:
        raise VideoGenerationError(
            f"Network error: {getattr(exc, 'reason', str(exc))}",
            retryable=True,
        ) from exc

    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise VideoGenerationError(
            "Video API returned invalid JSON",
            provider_response={"body": raw.decode("utf-8", errors="replace")},
        ) from exc
    if not isinstance(payload, dict):
        raise VideoGenerationError(
            f"Expected dict JSON response, got: {type(payload)!r}",
            provider_response={"body": payload},
        )
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
            provider_response={"http_status": exc.code, "body": detail},
        ) from exc
    except (urllib.error.URLError, OSError, http.client.HTTPException) as exc:
        raise VideoGenerationError(
            f"Network error: {getattr(exc, 'reason', str(exc))}",
            retryable=True,
        ) from exc


def _read_string(payload: dict[str, Any], key: str) -> str | None:
    value = payload.get(key)
    if isinstance(value, str) and value.strip():
        return value
    return None
