"""Provider-specific direct transports for the ordered-frame evaluation.

Functions receive the caller namespace so test-injected HTTP and env boundaries
remain the same as the Promptfoo entrypoint.
"""

from __future__ import annotations

import hashlib
import urllib.parse
from pathlib import Path
from typing import Any

from cine_forge.ai.token_usage import validate_gemini_token_usage


def call_xai_responses_strict(
    scope: dict[str, Any],
    *,
    model: str,
    user_text: str,
    frames: list[dict[str, str]],
    max_tokens: int,
    reasoning_effort: str,
) -> dict[str, Any]:
    """Call an xAI vision model through Responses with strict output schema."""
    _to_openai_strict_schema = scope["_to_openai_strict_schema"]
    VideoAnalysisPrediction = scope["VideoAnalysisPrediction"]
    _request_xai_responses_json = scope["_request_xai_responses_json"]
    validate_provider_response_identity = scope["validate_provider_response_identity"]
    _token_count = scope["_token_count"]
    content: list[dict[str, str]] = [{"type": "input_text", "text": user_text}]
    for index, frame in enumerate(frames):
        content.append({"type": "input_text", "text": f"frame_index: {index}"})
        content.append(
            {
                "type": "input_image",
                "image_url": f"data:{frame['mime_type']};base64,{frame['base64']}",
            }
        )
    payload = {
        "model": model,
        "input": [{"role": "user", "content": content}],
        "reasoning": {"effort": reasoning_effort},
        "store": False,
        "max_output_tokens": max_tokens,
        "text": {
            "format": {
                "type": "json_schema",
                "name": "video_analysis_prediction",
                "strict": True,
                "schema": _to_openai_strict_schema(VideoAnalysisPrediction.model_json_schema()),
            }
        },
    }
    raw, x_zero_data_retention = _request_xai_responses_json(payload)
    identity = validate_provider_response_identity(
        provider="xai",
        requested_model=model,
        returned_model=raw.get("model"),
        request_id=raw.get("id"),
        require_returned=True,
    )
    if raw.get("status") != "completed" or raw.get("incomplete_details") is not None:
        raise RuntimeError(
            "xAI Responses request did not complete: "
            f"status={raw.get('status')!r}, incomplete={raw.get('incomplete_details')!r}"
        )
    output = "".join(
        part.get("text", "")
        for item in raw.get("output", [])
        if isinstance(item, dict)
        for part in item.get("content", [])
        if isinstance(part, dict) and part.get("type") == "output_text"
    )
    if not output.strip():
        raise RuntimeError("xAI Responses transport returned no output text")
    VideoAnalysisPrediction.model_validate_json(output)
    usage = raw.get("usage")
    if not isinstance(usage, dict):
        raise RuntimeError("xAI Responses usage must be a mapping")
    input_tokens = _token_count(usage.get("input_tokens"), "input_tokens")
    output_tokens = _token_count(usage.get("output_tokens"), "output_tokens")
    total_tokens = _token_count(usage.get("total_tokens"), "total_tokens")
    if total_tokens != input_tokens + output_tokens:
        raise RuntimeError("xAI Responses total_tokens does not reconcile")
    output_details = usage.get("output_tokens_details")
    if not isinstance(output_details, dict):
        raise RuntimeError("xAI Responses output_tokens_details must be a mapping")
    reasoning_tokens = _token_count(output_details.get("reasoning_tokens"), "reasoning_tokens")
    if reasoning_tokens > output_tokens:
        raise RuntimeError("xAI Responses reasoning_tokens exceeds output_tokens")
    cost_ticks = _token_count(usage.get("cost_in_usd_ticks"), "cost_in_usd_ticks")
    return {
        "output": output,
        "token_usage": {
            "prompt": input_tokens,
            "completion": output_tokens - reasoning_tokens,
            "total": total_tokens,
            "billed_completion": output_tokens,
            "reasoning_completion": reasoning_tokens,
        },
        "reported_cost_usd": cost_ticks / 10_000_000_000,
        "cost_estimated": False,
        "raw": {
            "id": identity.request_id,
            "model": identity.returned_model,
            "status": raw.get("status"),
            "usage": usage,
            "x_zero_data_retention": x_zero_data_retention,
        },
    }


def call_gemini(
    scope: dict[str, Any],
    *,
    model: str,
    user_text: str,
    frames: list[dict[str, str]],
    max_tokens: int,
    temperature: float | None = None,
) -> dict[str, Any]:
    _require_env = scope["_require_env"]
    _build_gemini_payload = scope["_build_gemini_payload"]
    _VIDEO_ANALYSIS_RESPONSE_SCHEMA = scope["_VIDEO_ANALYSIS_RESPONSE_SCHEMA"]
    GEMINI_MODELS_URL = scope["GEMINI_MODELS_URL"]
    _request_json = scope["_request_json"]
    validate_provider_response_identity = scope["validate_provider_response_identity"]
    _token_count = scope["_token_count"]
    api_key = _require_env("GEMINI_API_KEY")
    payload = _build_gemini_payload(
        user_text=user_text,
        frames=frames,
        max_tokens=max_tokens,
        temperature=temperature,
        response_schema=_VIDEO_ANALYSIS_RESPONSE_SCHEMA,
    )
    url = f"{GEMINI_MODELS_URL}/{urllib.parse.quote(model, safe='')}:generateContent?key={api_key}"
    response = _request_json(
        url,
        headers={"Content-Type": "application/json"},
        body=payload,
    )
    candidates = response.get("candidates", [])
    parts = candidates[0].get("content", {}).get("parts", []) if candidates else []
    output = "\n".join(part.get("text", "") for part in parts if "text" in part)
    usage = response.get("usageMetadata", {})
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
    normalized_usage = {
        "prompt": token_usage.prompt,
        "completion": token_usage.visible_completion,
        "total": token_usage.total,
        "billed_completion": token_usage.billed_completion,
    }
    if token_usage.reported_reasoning_completion is not None:
        normalized_usage["reasoning_completion"] = token_usage.reported_reasoning_completion
    identity = validate_provider_response_identity(
        provider="google",
        requested_model=model,
        returned_model=response.get("modelVersion"),
        request_id=response.get("responseId"),
        require_returned=True,
    )
    raw_evidence = {
        "responseId": identity.request_id,
        "modelVersion": identity.returned_model,
        "usageMetadata": usage,
    }
    return {
        "output": output,
        "token_usage": normalized_usage,
        "raw": raw_evidence,
    }


def call_openrouter_strict(
    scope: dict[str, Any],
    *,
    model: str,
    user_text: str,
    frames: list[dict[str, str]],
    max_tokens: int,
    upstream_provider: str,
    raw_output_path: Path,
    timeout_seconds: float,
) -> dict[str, Any]:
    """Call an exact OpenRouter provider with strict JSON and no fallback."""
    OPENROUTER_CHAT_URL = scope["OPENROUTER_CHAT_URL"]
    _require_env = scope["_require_env"]
    _request_json = scope["_request_json"]
    ProviderHTTPError = scope["ProviderHTTPError"]
    _write_raw_envelope = scope["_write_raw_envelope"]
    VideoAnalysisPrediction = scope["VideoAnalysisPrediction"]
    if not upstream_provider:
        raise RuntimeError("OpenRouter video evaluation requires upstream_provider")
    _build_openai_payload = scope["_build_openai_payload"]
    _to_openai_strict_schema = scope["_to_openai_strict_schema"]
    payload = _build_openai_payload(
        model=model,
        user_text=user_text,
        frames=frames,
        max_tokens=max_tokens,
    )
    payload["provider"] = {
        "order": [upstream_provider],
        "allow_fallbacks": False,
        "require_parameters": True,
    }
    payload["response_format"] = {
        "type": "json_schema",
        "json_schema": {
            "name": "video_analysis_prediction",
            "strict": True,
            "schema": _to_openai_strict_schema(VideoAnalysisPrediction.model_json_schema()),
        },
    }
    try:
        response = _request_json(
            OPENROUTER_CHAT_URL,
            headers={
                "Authorization": f"Bearer {_require_env('OPENROUTER_API_KEY')}",
                "Content-Type": "application/json",
            },
            body=payload,
            timeout_seconds=timeout_seconds,
        )
    except ProviderHTTPError as exc:
        _write_raw_envelope(
            raw_output_path,
            {"request": payload, "response_error": {"status": exc.status_code, "body": exc.body}},
        )
        raise
    # Persist the complete safe/synthetic envelope before reading semantic text.
    _write_raw_envelope(raw_output_path, response)
    raw_bytes = raw_output_path.read_bytes()
    return _normalize_openrouter_response(
        scope,
        response=response,
        upstream_provider=upstream_provider,
        raw_output_path=raw_output_path,
        raw_bytes=raw_bytes,
        model=model,
    )


def _normalize_openrouter_response(
    scope: dict[str, Any],
    *,
    response: dict[str, Any],
    upstream_provider: str,
    raw_output_path: Path,
    raw_bytes: bytes,
    model: str,
) -> dict[str, Any]:
    REPO_ROOT = scope["REPO_ROOT"]
    validate_provider_response_identity = scope["validate_provider_response_identity"]
    VideoAnalysisPrediction = scope["VideoAnalysisPrediction"]
    _token_count = scope["_token_count"]
    identity = validate_provider_response_identity(
        provider="openrouter",
        requested_model=model,
        returned_model=response.get("model"),
        request_id=response.get("id"),
        require_returned=True,
    )
    returned_provider = response.get("provider")
    if returned_provider != upstream_provider:
        raise RuntimeError(
            "OpenRouter response provider does not match pinned provider: "
            f"expected {upstream_provider}, received {returned_provider!r}"
        )
    choices = response.get("choices")
    if not isinstance(choices, list) or len(choices) != 1:
        raise RuntimeError("OpenRouter response must contain exactly one choice")
    choice = choices[0]
    if not isinstance(choice, dict) or choice.get("finish_reason") != "stop":
        raise RuntimeError("OpenRouter response did not complete")
    message = choice.get("message")
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("OpenRouter response returned no output text")
    VideoAnalysisPrediction.model_validate_json(content)
    usage = response.get("usage")
    if not isinstance(usage, dict):
        raise RuntimeError("OpenRouter response usage must be a mapping")
    prompt_tokens = _token_count(usage.get("prompt_tokens"), "prompt_tokens")
    completion_tokens = _token_count(usage.get("completion_tokens"), "completion_tokens")
    total_tokens = _token_count(usage.get("total_tokens"), "total_tokens")
    if total_tokens != prompt_tokens + completion_tokens:
        raise RuntimeError("OpenRouter total_tokens does not reconcile")
    reported_cost = usage.get("cost")
    if isinstance(reported_cost, bool) or not isinstance(reported_cost, (int, float)):
        raise RuntimeError("OpenRouter usage.cost must be a number")
    return {
        "output": content,
        "token_usage": {
            "prompt": prompt_tokens,
            "completion": completion_tokens,
            "total": total_tokens,
        },
        "reported_cost_usd": float(reported_cost),
        "cost_estimated": False,
        "raw": {
            "id": identity.request_id,
            "model": identity.returned_model,
            "provider": returned_provider,
            "usage": usage,
            "raw_envelope_path": raw_output_path.relative_to(REPO_ROOT).as_posix(),
            "raw_envelope_sha256": hashlib.sha256(raw_bytes).hexdigest(),
            "raw_envelope_bytes": len(raw_bytes),
        },
    }
