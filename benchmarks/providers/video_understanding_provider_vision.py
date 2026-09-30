"""Provider-specific direct transports for the ordered-frame evaluation.

Functions receive the caller namespace so test-injected HTTP and env boundaries
remain the same as the Promptfoo entrypoint.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from video_understanding_provider_support import (
    call_gemini as call_gemini,
)
from video_understanding_provider_support import (
    openai_frame_content,
    openai_usage_and_cost,
)


def call_openai_responses_strict(
    scope: dict[str, Any],
    *,
    model: str,
    user_text: str,
    frames: list[dict[str, str]],
    max_tokens: int,
    reasoning_effort: str,
    raw_output_path: Path,
) -> dict[str, Any]:
    """Direct foreground Responses, with raw retention before validation."""
    if model not in {"gpt-6-sol", "gpt-6.1-sol", "gpt-6-luna"} or reasoning_effort != "low":
        raise RuntimeError("This bounded lane requires GPT-6 Sol/6.1 Sol/Luna at low effort")
    if len(frames) != 5:
        raise RuntimeError("Five ordered JPEGs are required")
    content = openai_frame_content(user_text, frames)
    payload = {
        "model": model,
        "input": [{"role": "user", "content": content}],
        "reasoning": {"effort": reasoning_effort},
        "store": False,
        "service_tier": "default",
        "max_output_tokens": max_tokens,
        "text": {"format": {
            "type": "json_schema", "name": "video_analysis_prediction", "strict": True,
            "schema": scope["_anthropic_video_schema"](),
        }},
    }
    try:
        response = scope["_request_json"](
            scope["OPENAI_RESPONSES_URL"],
            headers={
                "Authorization": f"Bearer {scope['_require_env']('OPENAI_API_KEY')}",
                "Content-Type": "application/json",
            },
            body=payload,
            raw_output_path=raw_output_path,
        )
    except scope["ProviderHTTPError"] as exc:
        scope["_write_raw_envelope"](raw_output_path, {
            "request": payload,
            "response_error": {"status": exc.status_code, "body": exc.body},
        })
        raise
    scope["_write_raw_envelope"](raw_output_path, response)
    raw_bytes = raw_output_path.read_bytes()
    identity = scope["validate_provider_response_identity"](
        provider="openai", requested_model=model, returned_model=response.get("model"),
        request_id=response.get("id"), require_returned=True,
    )
    if (response.get("status") != "completed" or response.get("incomplete_details") is not None
            or response.get("error") is not None):
        raise RuntimeError(
            f"OpenAI Responses did not complete: {response.get('status')!r}, "
            f"{response.get('incomplete_details')!r}, error={response.get('error')!r}"
        )
    if response.get("service_tier") != "default":
        raise RuntimeError("OpenAI Responses did not report Standard/default tier")
    output_items = response.get("output")
    if not isinstance(output_items, list):
        raise RuntimeError("OpenAI Responses output must be a list")
    messages = [item for item in output_items if isinstance(item, dict)
                and item.get("type") == "message"]
    if len(messages) != 1 or messages[0].get("status") != "completed":
        raise RuntimeError("OpenAI Responses requires one completed assistant message")
    texts = [
        part.get("text")
        for item in output_items if isinstance(item, dict)
        for part in item.get("content", []) if isinstance(part, dict)
        and part.get("type") == "output_text"
    ]
    if len(texts) != 1 or not isinstance(texts[0], str) or not texts[0].strip():
        raise RuntimeError("OpenAI Responses requires one complete output_text")
    output = texts[0]
    scope["VideoAnalysisPrediction"].model_validate_json(output)
    (
        usage, input_tokens, output_tokens, total_tokens,
        reasoning_tokens, written_tokens, estimated_cost,
    ) = openai_usage_and_cost(scope, response, model)
    repo_root = scope["REPO_ROOT"]
    return {
        "output": output,
        "token_usage": {
            "prompt": input_tokens, "completion": output_tokens - reasoning_tokens,
            "total": total_tokens, "billed_completion": output_tokens,
            "reasoning_completion": reasoning_tokens,
        },
        "reported_cost_usd": estimated_cost,
        "cost_estimated": True,
        "raw": {
            "id": identity.request_id, "model": identity.returned_model,
            "status": response["status"], "service_tier": response["service_tier"],
            "usage": usage,
            "cache_write_count_known": written_tokens is not None,
            "raw_envelope_path": raw_output_path.relative_to(repo_root).as_posix(),
            "raw_envelope_sha256": hashlib.sha256(raw_bytes).hexdigest(),
            "raw_envelope_bytes": len(raw_bytes),
        },
    }


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
