"""Request preparation and response shaping for the visual benchmark provider."""

from __future__ import annotations

import importlib
import math
from pathlib import Path
from typing import Any

_transport = importlib.import_module("video_understanding_transport")
_subject_contract = importlib.import_module("final_render_provider_floor_subject_contract")


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
