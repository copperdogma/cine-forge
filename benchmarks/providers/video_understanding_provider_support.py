"""Request preparation and response shaping for the visual benchmark provider."""

from __future__ import annotations

import importlib
import math
import urllib.parse
from pathlib import Path
from typing import Any

from cine_forge.ai.llm import estimate_cost_usd
from cine_forge.ai.token_usage import validate_gemini_token_usage

_transport = importlib.import_module("video_understanding_transport")
_subject_contract = importlib.import_module("final_render_provider_floor_subject_contract")


def response_cost(request: dict[str, Any], response: dict[str, Any]) -> float | None:
    reported_cost = response.get("reported_cost_usd")
    if isinstance(reported_cost, (int, float)) and not isinstance(reported_cost, bool):
        return float(reported_cost)
    token_usage = response.get("token_usage")
    if not isinstance(token_usage, dict):
        return None
    if token_usage.get("prompt") is None or token_usage.get("completion") is None:
        return None
    return estimate_cost_usd(
        request["model"],
        int(token_usage["prompt"]),
        completion_tokens_for_cost(request["provider"], token_usage),
    )


def completion_tokens_for_cost(provider: str, token_usage: dict[str, Any]) -> int:
    """Return billable output while leaving visible completion telemetry intact."""
    if provider == "google":
        optional_usage: dict[str, object] = {}
        if "total" in token_usage:
            optional_usage["total_tokens"] = token_usage["total"]
        if "billed_completion" in token_usage:
            optional_usage["billed_completion_tokens"] = token_usage[
                "billed_completion"
            ]
        if "reasoning_completion" in token_usage:
            optional_usage["reasoning_completion_tokens"] = token_usage[
                "reasoning_completion"
            ]
        return validate_gemini_token_usage(
            prompt_tokens=token_usage.get("prompt"),
            visible_completion_tokens=token_usage.get("completion"),
            **optional_usage,
        ).billed_completion

    visible_completion = int(token_usage.get("completion", 0) or 0)
    billed_completion = int(
        token_usage.get("billed_completion", visible_completion) or 0
    )
    if provider == "xai":
        prompt_tokens = int(token_usage.get("prompt", 0) or 0)
        total_tokens = int(token_usage.get("total", 0) or 0)
        billed_completion = max(
            billed_completion,
            visible_completion,
            total_tokens - prompt_tokens,
        )
    return billed_completion


def prepare_subject_request(prompt: str, options: object, context: object) -> dict[str, Any]:
    if not isinstance(options, dict) or not isinstance(context, dict):
        raise RuntimeError("provider options and context must be mappings")
    config = options.get("config")
    vars_data = context.get("vars")
    if not isinstance(config, dict) or not isinstance(vars_data, dict):
        raise RuntimeError("provider config and test vars must be mappings")
    base_path = Path(config.get("basePath", Path.cwd()))
    prompt_version = str(
        config.get("prompt_version", "video-understanding-frame-packet-v3")
    )
    if (
        prompt_version == _subject_contract.FINAL_RENDER_PROMPT_VERSION
        and not _subject_contract.runtime_subject_config_is_exact(config)
    ):
        raise RuntimeError("final-render provider config does not match its exact contract")
    frame_policy = str(config.get("frame_policy", "five_evenly_spaced_jpegs_v1"))
    evaluation_id = str(vars_data.get("evaluation_id", "")).strip()
    if not evaluation_id:
        raise RuntimeError("evaluation_id test var is required")
    max_frames = _positive_integer(config.get("max_frames", 5), name="max_frames")
    clip_dir = _transport.resolve_clip_dir(
        base_path=base_path,
        config=config,
        vars_data=vars_data,
    )
    packet = _transport.load_clip_packet(clip_dir, max_frames=max_frames)
    expected_variant = str(config.get("candidate_variant", "")).strip()
    expected_clip_id = str(vars_data.get("clip_id", "")).strip()
    if packet["frame_count"] != max_frames:
        raise RuntimeError("frame packet is incomplete")
    if packet["meta"].get("analysis_frame_policy") != frame_policy:
        raise RuntimeError("frame packet policy does not match provider config")
    if packet["meta"].get("clip_id") != expected_clip_id:
        raise RuntimeError("frame packet clip_id does not match test case")
    if expected_variant and packet["meta"].get("candidate_variant") != expected_variant:
        raise RuntimeError("frame packet candidate does not match provider config")
    model = str(config.get("model", "")).strip()
    provider = str(config.get("provider", "")).strip()
    if not model or not provider:
        raise RuntimeError("provider config must include both 'provider' and 'model'")
    return {
        "config": config,
        "evaluation_id": evaluation_id,
        "frame_policy": frame_policy,
        "max_tokens": _positive_integer(config.get("max_tokens", 1400), name="max_tokens"),
        "model": model,
        "packet": packet,
        "prompt_version": prompt_version,
        "provider": provider,
        "temperature": _temperature(config.get("temperature")),
        "user_text": _transport.build_user_text(
            prompt,
            packet["meta"],
            evaluation_id=evaluation_id,
            prompt_version=prompt_version,
            frame_count=packet["frame_count"],
            sample_times=packet["sample_times_seconds"],
        ),
    }


def build_promptfoo_response(
    *,
    request: dict[str, Any],
    response: dict[str, Any],
    latency_ms: int,
    cost_usd: float | None,
    subject_contract_sha256: str | None,
) -> dict[str, Any]:
    token_usage = response.get("token_usage")
    if not isinstance(token_usage, dict):
        raise RuntimeError("provider response token_usage must be a mapping")
    raw = response.get("raw")
    if not isinstance(raw, dict):
        raise RuntimeError("provider response raw evidence must be a mapping")
    returned_model = raw.get("modelVersion") or raw.get("model")
    request_id = raw.get("responseId") or raw.get("id")
    if not isinstance(returned_model, str) or not returned_model.strip():
        raise RuntimeError("provider response raw model identity is required")
    if not isinstance(request_id, str) or not request_id.strip():
        raise RuntimeError("provider response raw request identity is required")
    promptfoo_usage: dict[str, Any] = {
        "total": _nonnegative_integer(token_usage.get("total"), name="total tokens"),
        "prompt": _nonnegative_integer(token_usage.get("prompt"), name="prompt tokens"),
        "completion": _nonnegative_integer(
            token_usage.get("completion"), name="completion tokens"
        ),
    }
    if "reasoning_completion" in token_usage:
        promptfoo_usage["completionDetails"] = {
            "reasoning": _nonnegative_integer(
                token_usage["reasoning_completion"], name="reasoning tokens"
            ),
        }
    packet = request["packet"]
    metadata = {
        "clip_id": packet["meta"]["clip_id"],
        "evaluation_id": request["evaluation_id"],
        "candidate_variant": packet["meta"].get("candidate_variant"),
        "prompt_version": request["prompt_version"],
        "frame_policy": request["frame_policy"],
        "model": request["model"],
        "requested_model": request["model"],
        "returned_model": returned_model.strip(),
        "request_id": request_id.strip(),
        "provider": request["provider"],
        "cost_estimated": bool(response.get("cost_estimated", cost_usd is not None)),
        "modality": "ordered_jpeg_frame_packet",
        "audio_submitted": False,
        "frame_count": packet["frame_count"],
        "sample_times_seconds": packet["sample_times_seconds"],
        "frame_sha256": packet["frame_sha256"],
        "meta_sha256": packet["meta_sha256"],
    }
    if subject_contract_sha256 is not None:
        metadata["subject_contract_sha256"] = subject_contract_sha256
    promptfoo_response = {
        "output": response["output"],
        "tokenUsage": promptfoo_usage,
        "cost": cost_usd,
        "latencyMs": latency_ms,
        "cached": False,
        "metadata": metadata,
    }
    promptfoo_response["raw"] = raw
    return promptfoo_response


def _temperature(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RuntimeError("temperature must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise RuntimeError("temperature must be a finite number")
    return result


def _positive_integer(value: object, *, name: str) -> int:
    result = _nonnegative_integer(value, name=name)
    if result < 1:
        raise RuntimeError(f"{name} must be positive")
    return result


def _nonnegative_integer(value: object, *, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise RuntimeError(f"{name} must be a nonnegative integer")
    return value

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


def openai_usage_and_cost(
    scope: dict[str, Any], response: dict[str, Any], model: str
) -> tuple[dict[str, Any], int, int, int, int, int | None, float]:
    usage = response.get("usage")
    if not isinstance(usage, dict):
        raise RuntimeError("OpenAI Responses usage must be a mapping")
    count = scope["_token_count"]
    input_tokens = count(usage.get("input_tokens"), "input_tokens")
    output_tokens = count(usage.get("output_tokens"), "output_tokens")
    total_tokens = count(usage.get("total_tokens"), "total_tokens")
    if total_tokens != input_tokens + output_tokens:
        raise RuntimeError("OpenAI Responses token totals do not reconcile")
    input_details = usage.get("input_tokens_details") or {}
    output_details = usage.get("output_tokens_details") or {}
    if not isinstance(input_details, dict) or not isinstance(output_details, dict):
        raise RuntimeError("OpenAI Responses token details must be mappings")
    cached_tokens = count(input_details.get("cached_tokens", 0), "cached_tokens")
    write_count = input_details.get("cache_write_tokens")
    written_tokens = (
        count(write_count, "cache_write_tokens") if write_count is not None else None
    )
    reasoning_tokens = count(output_details.get("reasoning_tokens", 0), "reasoning_tokens")
    if (cached_tokens > input_tokens or reasoning_tokens > output_tokens or
            (written_tokens is not None and cached_tokens + written_tokens > input_tokens)):
        raise RuntimeError("OpenAI Responses token details exceed total tokens")
    input_rate, cached_rate, write_rate, output_rate = {
        "gpt-6-sol": (2.0, 0.2, 2.5, 10.0),
        "gpt-6-luna": (0.1, 0.01, 0.125, 0.5),
    }[model]
    # If write telemetry is absent, charge every non-cached input token at the
    # higher write rate. This is an upper bound, not a billed-cost claim.
    charged_writes = (
        written_tokens if written_tokens is not None else input_tokens - cached_tokens
    )
    ordinary_tokens = input_tokens - cached_tokens - charged_writes
    estimated_cost = (
        ordinary_tokens * input_rate
        + cached_tokens * cached_rate
        + charged_writes * write_rate
        + output_tokens * output_rate
    ) / 1_000_000
    return (
        usage, input_tokens, output_tokens, total_tokens,
        reasoning_tokens, written_tokens, estimated_cost,
    )


def openai_frame_content(
    user_text: str, frames: list[dict[str, str]]
) -> list[dict[str, Any]]:
    content: list[dict[str, Any]] = [{"type": "input_text", "text": user_text}]
    for index, frame in enumerate(frames):
        content.append({"type": "input_text", "text": f"frame_index: {index}"})
        content.append({
            "type": "input_image",
            "image_url": f"data:{frame['mime_type']};base64,{frame['base64']}",
            "detail": "high",
        })
    return content
