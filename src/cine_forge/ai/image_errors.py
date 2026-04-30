"""Structured errors for image-provider transport failures."""

from __future__ import annotations

import json
from typing import Any


class ImageGenerationError(Exception):
    """Raised when the image generation API call fails."""

    def __init__(
        self,
        message: str,
        *,
        provider: str | None = None,
        model: str | None = None,
        status_code: int | None = None,
        request_id: str | None = None,
        error_code: str | None = None,
        error_type: str | None = None,
        response_body: str | None = None,
        is_transient: bool = False,
    ) -> None:
        super().__init__(message)
        self.provider = provider
        self.model = model
        self.status_code = status_code
        self.request_id = request_id
        self.error_code = error_code
        self.error_type = error_type
        self.response_body = response_body
        self.is_transient = is_transient


def provider_http_error(
    *,
    provider: str,
    provider_label: str,
    model: str,
    status_code: int,
    headers: Any,
    body: str,
) -> ImageGenerationError:
    parsed = _parse_provider_error_body(body)
    provider_message = parsed["message"] or body.strip() or "Provider returned an error."
    request_id = _header_value(
        headers,
        "x-request-id",
        "x-openai-request-id",
        "x-goog-request-id",
        "x-google-request-id",
    ) or parsed["request_id"]
    return ImageGenerationError(
        f"{provider_label} returned HTTP {status_code}: {provider_message}",
        provider=provider,
        model=model,
        status_code=status_code,
        request_id=request_id,
        error_code=parsed["code"],
        error_type=parsed["type"],
        response_body=body,
        is_transient=status_code >= 500,
    )


def _header_value(headers: Any, *names: str) -> str | None:
    if headers is None or not hasattr(headers, "get"):
        return None
    for name in names:
        value = headers.get(name)
        if value:
            return str(value)
    return None


def _parse_provider_error_body(body: str) -> dict[str, str | None]:
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return {"message": body.strip() or None, "code": None, "type": None, "request_id": None}

    if not isinstance(payload, dict):
        return {"message": str(payload), "code": None, "type": None, "request_id": None}

    error = payload.get("error")
    if isinstance(error, dict):
        return {
            "message": _string_value(error.get("message")),
            "code": _string_value(error.get("code")),
            "type": _string_value(error.get("type")),
            "request_id": _string_value(error.get("request_id") or payload.get("request_id")),
        }

    return {
        "message": _string_value(payload.get("message")) or body.strip() or None,
        "code": _string_value(payload.get("code")),
        "type": _string_value(payload.get("type")),
        "request_id": _string_value(payload.get("request_id")),
    }


def _string_value(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
