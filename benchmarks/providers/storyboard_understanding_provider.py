"""Custom promptfoo provider for storyboard-sequence quality analysis."""

from __future__ import annotations

import importlib
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from cine_forge.ai.token_usage import validate_gemini_token_usage  # noqa: E402
from cine_forge.env import load_cine_forge_dotenv  # noqa: E402

load_cine_forge_dotenv(REPO_ROOT)

estimate_cost_usd = importlib.import_module("cine_forge.ai.llm").estimate_cost_usd

import storyboard_understanding_packet as _packet  # noqa: E402
import storyboard_understanding_transport as _transport  # noqa: E402

_build_user_text = _packet._build_user_text
_encode_image = _packet._encode_image
_image_label_text = _packet._image_label_text
_load_storyboard_packet = _packet._load_storyboard_packet
_resolve_relative = _packet._resolve_relative
_resolve_sequence_dir = _packet._resolve_sequence_dir
_build_anthropic_payload = _transport._build_anthropic_payload
_build_gemini_payload = _transport._build_gemini_payload
_build_openai_payload = _transport._build_openai_payload
_call_anthropic = _transport._call_anthropic
_call_gemini = _transport._call_gemini
_call_openai = _transport._call_openai


def call_api(prompt: str, options: dict, context: dict) -> dict:
    """Promptfoo entry point for storyboard-sequence packet analysis."""
    started = time.perf_counter()
    config = options.get("config", {})
    base_path = Path(config.get("basePath", Path.cwd()))
    prompt_version = config.get("prompt_version", "storyboard-understanding-v1")

    try:
        sequence_dir = _resolve_sequence_dir(
            base_path=base_path,
            config=config,
            vars_data=context.get("vars", {}),
        )
        packet = _load_storyboard_packet(
            sequence_dir=sequence_dir,
            max_frames=int(config.get("max_frames", 32)),
            max_references=int(config.get("max_references", 4)),
        )
        expected_storyboard_id = str(context.get("vars", {}).get("storyboard_id", ""))
        if packet["meta"].get("storyboard_id") != expected_storyboard_id:
            raise RuntimeError("packet storyboard_id does not match the requested opaque case")
        user_text = _build_user_text(prompt, packet["meta"], prompt_version=prompt_version)
        model = str(config.get("model", "")).strip()
        provider = str(config.get("provider", "")).strip()
        temperature = float(config.get("temperature", 0.0))
        max_tokens = int(config.get("max_tokens", 2000))

        if not model or not provider:
            raise RuntimeError("provider config must include both 'provider' and 'model'")

        images = packet["frames"] + packet["references"]
        response = _dispatch_request(
            provider=provider,
            model=model,
            user_text=user_text,
            images=images,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        response["output"] = _attach_packet_contract(
            response["output"],
            storyboard_id=str(packet["meta"]["storyboard_id"]),
            frame_count=len(packet["frames"]),
            reference_count=len(packet["references"]),
        )
    except Exception as exc:
        latency_ms = round((time.perf_counter() - started) * 1000)
        return {"output": "", "error": str(exc), "latencyMs": latency_ms}

    latency_ms = round((time.perf_counter() - started) * 1000)
    token_usage = response.get("token_usage", {})
    cost = None
    if token_usage.get("prompt") is not None and token_usage.get("completion") is not None:
        completion_for_cost = _completion_tokens_for_cost(provider, token_usage)
        cost = estimate_cost_usd(
            model,
            int(token_usage.get("prompt", 0)),
            completion_for_cost,
        )

    promptfoo_usage = {
        "total": int(token_usage.get("total", 0)),
        "prompt": int(token_usage.get("prompt", 0)),
        "completion": int(token_usage.get("completion", 0)),
    }
    if "reasoning_completion" in token_usage:
        promptfoo_usage["completionDetails"] = {
            "reasoning": int(token_usage["reasoning_completion"]),
        }

    promptfoo_response = {
        "output": response["output"],
        "tokenUsage": promptfoo_usage,
        "cost": cost,
        "latencyMs": latency_ms,
        "cached": False,
        "metadata": {
            "storyboard_id": packet["meta"]["storyboard_id"],
            "candidate_variant": packet["meta"].get("candidate_variant"),
            "prompt_version": prompt_version,
            "model": model,
            "requested_model": model,
            "returned_model": _raw_identity(response, "modelVersion", "model"),
            "request_id": _raw_identity(response, "responseId", "id"),
            "provider": provider,
            "dataset_manifest_sha256": packet["dataset_manifest_sha256"],
            "asset_manifest_sha256": packet["asset_manifest_sha256"],
        },
    }
    if "raw" in response:
        promptfoo_response["raw"] = response["raw"]
    return promptfoo_response


def _raw_identity(response: dict, *keys: str) -> str:
    raw = response.get("raw")
    if not isinstance(raw, dict):
        raise ValueError("provider response raw identity evidence is required")
    evidence = [raw[key] for key in keys if key in raw]
    if len(evidence) != 1 or not isinstance(evidence[0], str) or not evidence[0].strip():
        raise ValueError(f"provider response must retain exactly one of {keys}")
    return evidence[0].strip()


def _dispatch_request(
    *,
    provider: str,
    model: str,
    user_text: str,
    images: list[dict[str, str]],
    max_tokens: int,
    temperature: float,
) -> dict:
    kwargs = {
        "model": model,
        "user_text": user_text,
        "images": images,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if provider == "openai":
        return _call_openai(**kwargs)
    if provider == "anthropic":
        return _call_anthropic(**kwargs)
    if provider == "google":
        return _call_gemini(**kwargs)
    raise RuntimeError(f"Unsupported provider: {provider}")


def _completion_tokens_for_cost(provider: str, token_usage: dict) -> int:
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
    return int(token_usage.get("billed_completion", visible_completion) or 0)


def _attach_packet_contract(
    output: str,
    *,
    storyboard_id: str,
    frame_count: int,
    reference_count: int,
) -> str:
    import json

    payload = json.loads(output)
    if not isinstance(payload, dict):
        raise ValueError("storyboard analysis response must be one JSON object")
    if payload.get("storyboard_id") != storyboard_id:
        raise ValueError("storyboard analysis response used the wrong opaque storyboard_id")
    protected = {"packet_frame_count", "packet_reference_count"}
    if protected.intersection(payload):
        raise ValueError("model response must not set provider-owned packet counts")
    payload["packet_frame_count"] = frame_count
    payload["packet_reference_count"] = reference_count
    return json.dumps(payload, separators=(",", ":"), sort_keys=True)
