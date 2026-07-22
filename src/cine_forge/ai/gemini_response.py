"""Fail-closed normalization for Gemini generateContent responses."""

from __future__ import annotations

from typing import Any

from cine_forge.ai.errors import LLMCallError
from cine_forge.ai.token_usage import validate_gemini_token_usage

_FINISH_REASON_MAP = {
    "STOP": "stop",
    "MAX_TOKENS": "length",
    "SAFETY": "content_filter",
    "RECITATION": "content_filter",
    "OTHER": "stop",
}


def normalize_gemini_response(
    raw: dict[str, Any], *, expected_model: str | None = None
) -> dict[str, Any]:
    """Convert a provider response while preserving identity and usage truth."""
    candidates = raw.get("candidates", [])
    if not candidates:
        raise LLMCallError("Gemini response missing candidates")
    response_id = _required_string(raw.get("responseId"), "responseId")
    model_version = _required_string(raw.get("modelVersion"), "modelVersion")
    if expected_model is not None and model_version != expected_model:
        raise LLMCallError(
            "Gemini response modelVersion does not match requested model: "
            f"expected {expected_model}, received {model_version}"
        )

    candidate = candidates[0]
    parts = candidate.get("content", {}).get("parts", [])
    text = "".join(part.get("text", "") for part in parts)
    usage = raw.get("usageMetadata", {})
    if not isinstance(usage, dict):
        raise ValueError("Gemini usageMetadata must be a mapping")
    optional_usage: dict[str, object] = {}
    if "totalTokenCount" in usage:
        optional_usage["total_tokens"] = usage["totalTokenCount"]
    if "thoughtsTokenCount" in usage:
        optional_usage["reasoning_completion_tokens"] = usage["thoughtsTokenCount"]
    token_usage = validate_gemini_token_usage(
        prompt_tokens=usage.get("promptTokenCount"),
        visible_completion_tokens=usage.get("candidatesTokenCount"),
        **optional_usage,
    )
    return {
        "id": response_id,
        "model": model_version,
        "choices": [
            {
                "message": {"content": text},
                "finish_reason": _FINISH_REASON_MAP.get(
                    candidate.get("finishReason", "STOP"), "stop"
                ),
            }
        ],
        "usage": {
            "prompt_tokens": token_usage.prompt,
            "completion_tokens": token_usage.billed_completion,
            "total_tokens": token_usage.total,
            "completion_tokens_details": {
                "visible_tokens": token_usage.visible_completion,
                "reasoning_tokens": token_usage.hidden_completion,
            },
        },
    }


def _required_string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise LLMCallError(f"Gemini response {name} must be a non-empty string")
    return value.strip()
