"""Cross-provider payload and HTTP helpers for storyboard packet analysis."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from storyboard_understanding_packet import _image_label_text

from cine_forge.ai.model_identity import validate_provider_response_identity
from cine_forge.ai.token_usage import validate_gemini_token_usage
from cine_forge.env import require_env

OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"
ANTHROPIC_MESSAGES_URL = "https://api.anthropic.com/v1/messages"
GEMINI_MODELS_URL = "https://generativelanguage.googleapis.com/v1beta/models"


def _build_openai_payload(
    *,
    model: str,
    user_text: str,
    images: list[dict[str, str]],
    max_tokens: int,
    temperature: float,
) -> dict[str, Any]:
    content = [{"type": "text", "text": user_text}]
    for image in images:
        content.append({"type": "text", "text": _image_label_text(image)})
        content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{image['mime_type']};base64,{image['base64']}",
                    "detail": "high",
                },
            }
        )
    return {
        "model": model,
        "messages": [{"role": "user", "content": content}],
        "temperature": temperature,
        "max_completion_tokens": max_tokens,
        "response_format": {"type": "json_object"},
    }


def _build_anthropic_payload(
    *,
    model: str,
    user_text: str,
    images: list[dict[str, str]],
    max_tokens: int,
    temperature: float,
) -> dict[str, Any]:
    content: list[dict[str, Any]] = [{"type": "text", "text": user_text}]
    for image in images:
        content.append({"type": "text", "text": _image_label_text(image)})
        content.append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": image["mime_type"],
                    "data": image["base64"],
                },
            }
        )
    return {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [{"role": "user", "content": content}],
    }


def _build_gemini_payload(
    *,
    user_text: str,
    images: list[dict[str, str]],
    max_tokens: int,
) -> dict[str, Any]:
    parts: list[dict[str, Any]] = [{"text": user_text}]
    for image in images:
        parts.append({"text": _image_label_text(image)})
        parts.append(
            {
                "inlineData": {
                    "mimeType": image["mime_type"],
                    "data": image["base64"],
                }
            }
        )
    return {
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {
            "maxOutputTokens": max_tokens,
            "responseMimeType": "application/json",
        },
    }


def _call_openai(
    *,
    model: str,
    user_text: str,
    images: list[dict[str, str]],
    max_tokens: int,
    temperature: float,
) -> dict[str, Any]:
    api_key = require_env("OPENAI_API_KEY")
    payload = _build_openai_payload(
        model=model,
        user_text=user_text,
        images=images,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    request = urllib.request.Request(
        OPENAI_CHAT_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            raw = json.loads(response.read())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI API returned HTTP {exc.code}: {body}") from exc
    message = raw["choices"][0]["message"]["content"]
    usage = raw.get("usage", {})
    identity = validate_provider_response_identity(
        provider="openai",
        requested_model=model,
        returned_model=raw.get("model"),
        request_id=raw.get("id"),
        require_returned=True,
    )
    return {
        "output": message,
        "token_usage": {
            "prompt": usage.get("prompt_tokens"),
            "completion": usage.get("completion_tokens"),
            "total": usage.get("total_tokens"),
        },
        "raw": {
            "id": identity.request_id,
            "model": identity.returned_model,
            "usage": usage,
        },
    }


def _call_anthropic(
    *,
    model: str,
    user_text: str,
    images: list[dict[str, str]],
    max_tokens: int,
    temperature: float,
) -> dict[str, Any]:
    api_key = require_env("ANTHROPIC_API_KEY")
    payload = _build_anthropic_payload(
        model=model,
        user_text=user_text,
        images=images,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    request = urllib.request.Request(
        ANTHROPIC_MESSAGES_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            raw = json.loads(response.read())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Anthropic API returned HTTP {exc.code}: {body}") from exc
    content = raw.get("content", [])
    text = "".join(part.get("text", "") for part in content if part.get("type") == "text")
    usage = raw.get("usage", {})
    identity = validate_provider_response_identity(
        provider="anthropic",
        requested_model=model,
        returned_model=raw.get("model"),
        request_id=raw.get("id"),
        require_returned=True,
    )
    return {
        "output": text,
        "token_usage": {
            "prompt": usage.get("input_tokens"),
            "completion": usage.get("output_tokens"),
            "total": (usage.get("input_tokens") or 0) + (usage.get("output_tokens") or 0),
        },
        "raw": {
            "id": identity.request_id,
            "model": identity.returned_model,
            "usage": usage,
        },
    }


def _call_gemini(
    *,
    model: str,
    user_text: str,
    images: list[dict[str, str]],
    max_tokens: int,
    temperature: float,
) -> dict[str, Any]:
    del temperature
    api_key = require_env("GEMINI_API_KEY")
    payload = _build_gemini_payload(
        user_text=user_text,
        images=images,
        max_tokens=max_tokens,
    )
    url = f"{GEMINI_MODELS_URL}/{urllib.parse.quote(model)}:generateContent?key={api_key}"
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            raw = json.loads(response.read())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Gemini API returned HTTP {exc.code}: {body}") from exc
    candidate = raw.get("candidates", [{}])[0]
    parts = candidate.get("content", {}).get("parts", [])
    text = "".join(part.get("text", "") for part in parts if part.get("text"))
    usage = raw.get("usageMetadata", {})
    if not isinstance(usage, dict):
        raise ValueError("Gemini usageMetadata must be a mapping")
    optional_usage: dict[str, object] = {}
    if "totalTokenCount" in usage:
        optional_usage["total_tokens"] = usage["totalTokenCount"]
    if "thoughtsTokenCount" in usage:
        optional_usage["reasoning_completion_tokens"] = usage[
            "thoughtsTokenCount"
        ]
    token_usage = validate_gemini_token_usage(
        prompt_tokens=usage.get("promptTokenCount"),
        visible_completion_tokens=usage.get("candidatesTokenCount"),
        **optional_usage,
    )
    normalized_usage = {
        "prompt": token_usage.prompt,
        "completion": token_usage.visible_completion,
        "total": token_usage.total,
        "billed_completion": token_usage.billed_completion,
    }
    if token_usage.reported_reasoning_completion is not None:
        normalized_usage["reasoning_completion"] = (
            token_usage.reported_reasoning_completion
        )
    identity = validate_provider_response_identity(
        provider="google",
        requested_model=model,
        returned_model=raw.get("modelVersion"),
        request_id=raw.get("responseId"),
        require_returned=True,
    )
    raw_evidence = {
        "responseId": identity.request_id,
        "modelVersion": identity.returned_model,
        "usageMetadata": usage,
    }
    return {
        "output": text,
        "token_usage": normalized_usage,
        "raw": raw_evidence,
    }
