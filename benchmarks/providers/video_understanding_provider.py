"""Custom promptfoo provider for the Story 030 video-understanding benchmark."""

from __future__ import annotations

import importlib
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
SCRIPT_ROOT = REPO_ROOT / "benchmarks" / "scripts"
for import_root in (SRC_ROOT, SCRIPT_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from cine_forge.ai.model_identity import (  # noqa: E402
    validate_provider_response_identity,
)
from cine_forge.ai.token_usage import validate_gemini_token_usage  # noqa: E402
from cine_forge.env import load_cine_forge_dotenv  # noqa: E402

load_cine_forge_dotenv(REPO_ROOT)

_llm = importlib.import_module("cine_forge.ai.llm")
estimate_cost_usd = _llm.estimate_cost_usd
_to_gemini_schema = _llm._to_gemini_schema
_to_openai_strict_schema = _llm._to_openai_strict_schema
require_env = importlib.import_module("cine_forge.env").require_env
VideoAnalysisPrediction = importlib.import_module(
    "cine_forge.schemas"
).VideoAnalysisPrediction


def _gemini_response_schema() -> dict[str, Any]:
    schema = VideoAnalysisPrediction.model_json_schema()
    schema["required"] = list(schema.get("properties", {}))
    return _to_gemini_schema(schema)


_VIDEO_ANALYSIS_RESPONSE_SCHEMA = _gemini_response_schema()

_transport = importlib.import_module("video_understanding_transport")
_build_anthropic_payload = _transport.build_anthropic_payload
_build_gemini_payload = _transport.build_gemini_payload
_build_openai_payload = _transport.build_openai_payload
_build_user_text = _transport.build_user_text
_load_clip_packet = _transport.load_clip_packet
_resolve_clip_dir = _transport.resolve_clip_dir
_resolve_relative = _transport.resolve_relative

_provider_support = importlib.import_module("video_understanding_provider_support")
_build_promptfoo_response = _provider_support.build_promptfoo_response
_completion_tokens_for_cost = _provider_support.completion_tokens_for_cost
_prepare_subject_request = _provider_support.prepare_subject_request
_response_cost = _provider_support.response_cost

_subject_contract = importlib.import_module("final_render_provider_floor_subject_contract")
_final_render_prompt_version = _subject_contract.FINAL_RENDER_PROMPT_VERSION
_subject_contract_fingerprint = _subject_contract.subject_contract_fingerprint


OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"
XAI_CHAT_URL = "https://api.x.ai/v1/chat/completions"
XAI_RESPONSES_URL = "https://api.x.ai/v1/responses"
ANTHROPIC_MESSAGES_URL = "https://api.anthropic.com/v1/messages"
GEMINI_MODELS_URL = "https://generativelanguage.googleapis.com/v1beta/models"


def call_api(prompt: str, options: dict, context: dict) -> dict:
    """Promptfoo entry point for multimodal clip-packet analysis."""
    started = time.perf_counter()
    try:
        request = _prepare_subject_request(prompt, options, context)
        subject_contract_sha256 = _current_subject_contract(request)
        response = _dispatch_subject_request(request)
        latency_ms = round((time.perf_counter() - started) * 1000)
        return _build_promptfoo_response(
            request=request,
            response=response,
            latency_ms=latency_ms,
            cost_usd=_response_cost(request, response),
            subject_contract_sha256=subject_contract_sha256,
        )
    except Exception as exc:
        latency_ms = round((time.perf_counter() - started) * 1000)
        return {
            "output": "",
            "error": str(exc),
            "latencyMs": latency_ms,
        }


def _dispatch_subject_request(request: dict[str, Any]) -> dict[str, Any]:
    common = {
        "model": request["model"],
        "user_text": request["user_text"],
        "frames": request["packet"]["frames"],
        "max_tokens": request["max_tokens"],
    }
    provider = request["provider"]
    if provider == "openai":
        return _call_openai(**common, temperature=request["temperature"])
    if provider == "xai":
        if request["config"].get("transport") == "responses_strict":
            return _call_xai_responses_strict(
                model=request["model"],
                user_text=request["user_text"],
                frames=request["packet"]["frames"],
                max_tokens=request["max_tokens"],
                reasoning_effort=str(
                    request["config"].get("reasoning_effort") or "low"
                ),
            )
        return _call_xai(**common, temperature=request["temperature"])
    if provider == "anthropic":
        return _call_anthropic(**common, temperature=request["temperature"])
    if provider == "google":
        return _call_gemini(**common)
    raise RuntimeError(f"Unsupported provider: {provider}")


def _current_subject_contract(request: dict[str, Any]) -> str | None:
    if request["prompt_version"] != _final_render_prompt_version:
        return None
    fingerprint = _subject_contract_fingerprint(
        request["config"],
        repo_root=REPO_ROOT,
    )
    if fingerprint is None:
        raise RuntimeError("final-render subject request contract is incomplete")
    return fingerprint


def _call_openai(
    *,
    model: str,
    user_text: str,
    frames: list[dict[str, str]],
    max_tokens: int,
    temperature: float | None,
) -> dict[str, Any]:
    api_key = _require_env("OPENAI_API_KEY")
    payload = _build_openai_payload(
        model=model,
        user_text=user_text,
        frames=frames,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    response = _request_json(
        OPENAI_CHAT_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        body=payload,
    )
    choice = response["choices"][0]["message"]["content"]
    return _openai_compatible_result(
        response=response,
        output=choice,
        provider="openai",
        requested_model=model,
    )


def _call_xai(
    *,
    model: str,
    user_text: str,
    frames: list[dict[str, str]],
    max_tokens: int,
    temperature: float | None,
) -> dict[str, Any]:
    api_key = _require_env("XAI_API_KEY")
    payload = _build_openai_payload(
        model=model,
        user_text=user_text,
        frames=frames,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    response = _request_json(
        XAI_CHAT_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        body=payload,
    )
    choice = response["choices"][0]["message"]["content"]
    return _openai_compatible_result(
        response=response,
        output=choice,
        provider="xai",
        requested_model=model,
    )


def _call_xai_responses_strict(
    *,
    model: str,
    user_text: str,
    frames: list[dict[str, str]],
    max_tokens: int,
    reasoning_effort: str,
) -> dict[str, Any]:
    """Call an xAI vision model through Responses with strict output schema."""
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
                "schema": _to_openai_strict_schema(
                    VideoAnalysisPrediction.model_json_schema()
                ),
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
    reasoning_tokens = _token_count(
        output_details.get("reasoning_tokens"), "reasoning_tokens"
    )
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


def _call_anthropic(
    *,
    model: str,
    user_text: str,
    frames: list[dict[str, str]],
    max_tokens: int,
    temperature: float | None,
) -> dict[str, Any]:
    api_key = _require_env("ANTHROPIC_API_KEY")
    payload = _build_anthropic_payload(
        model=model,
        user_text=user_text,
        frames=frames,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    response = _request_json(
        ANTHROPIC_MESSAGES_URL,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        body=payload,
    )
    blocks = response.get("content", [])
    output = "\n".join(block.get("text", "") for block in blocks if block.get("type") == "text")
    usage = response.get("usage", {})
    identity = validate_provider_response_identity(
        provider="anthropic",
        requested_model=model,
        returned_model=response.get("model"),
        request_id=response.get("id"),
        require_returned=True,
    )
    return {
        "output": output,
        "token_usage": {
            "prompt": usage.get("input_tokens", 0),
            "completion": usage.get("output_tokens", 0),
            "total": usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
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
    frames: list[dict[str, str]],
    max_tokens: int,
    temperature: float | None = None,
) -> dict[str, Any]:
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


def _openai_compatible_result(
    *,
    response: dict[str, Any],
    output: str,
    provider: str,
    requested_model: str,
) -> dict[str, Any]:
    usage = response.get("usage")
    if not isinstance(usage, dict):
        raise ValueError("provider usage must be a mapping")
    identity = validate_provider_response_identity(
        provider=provider,
        requested_model=requested_model,
        returned_model=response.get("model"),
        request_id=response.get("id"),
        require_returned=True,
    )
    token_usage: dict[str, Any] = {
        "prompt": usage.get("prompt_tokens"),
        "completion": usage.get("completion_tokens"),
        "total": usage.get("total_tokens"),
    }
    details = usage.get("completion_tokens_details")
    if isinstance(details, dict) and "reasoning_tokens" in details:
        token_usage["reasoning_completion"] = details["reasoning_tokens"]
    return {
        "output": output,
        "token_usage": token_usage,
        "raw": {
            "id": identity.request_id,
            "model": identity.returned_model,
            "usage": usage,
        },
    }


def _request_json(url: str, *, headers: dict[str, str], body: dict[str, Any]) -> dict[str, Any]:
    data = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        payload = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{url} returned HTTP {exc.code}: {payload}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"{url} request failed: {exc}") from exc


def _request_xai_responses_json(payload: dict[str, Any]) -> tuple[dict[str, Any], str | None]:
    request = urllib.request.Request(
        XAI_RESPONSES_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {_require_env('XAI_API_KEY')}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:  # noqa: S310
            raw = json.loads(response.read().decode("utf-8"))
            x_zero_data_retention = response.headers.get("x-zero-data-retention")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"xAI Responses HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"xAI Responses request failed: {exc}") from exc
    if not isinstance(raw, dict):
        raise RuntimeError("xAI Responses response must be a mapping")
    return raw, x_zero_data_retention


def _token_count(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise RuntimeError(f"xAI Responses {name} must be a nonnegative integer")
    return value


def _require_env(name: str) -> str:
    return require_env(name)
