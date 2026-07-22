"""Promptfoo provider for Anthropic Messages API models with current API quirks."""

from __future__ import annotations

import importlib
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from cine_forge.ai.model_identity import (  # noqa: E402
    validate_provider_response_identity,
)
from cine_forge.env import load_cine_forge_dotenv  # noqa: E402

load_cine_forge_dotenv(REPO_ROOT)

call_llm = importlib.import_module("cine_forge.ai.llm").call_llm


def call_api(prompt: str, options: dict, context: dict) -> dict:
    """Promptfoo entry point for text-only Anthropic Messages API evals."""
    del context
    config = options.get("config", {})
    started = time.perf_counter()
    model: str | None = None

    try:
        model = _configured_model(config)
        max_tokens = int(config.get("max_tokens") or 4096)
        temperature = float(config.get("temperature") or 0.0)
        max_retries = int(config.get("max_retries") or 1)
        timeout_seconds = _timeout_seconds(config)
        output, metadata = call_llm(
            prompt,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            max_retries=max_retries,
            request_timeout_seconds=timeout_seconds,
        )
        identity = validate_provider_response_identity(
            provider="anthropic",
            requested_model=model,
            returned_model=metadata.get("returned_model"),
            request_id=metadata.get("request_id"),
            require_returned=True,
        )
    except Exception as exc:
        error_metadata = {"provider": "anthropic"}
        if model is not None:
            error_metadata["requested_model"] = model
        return {
            "output": "",
            "error": str(exc),
            "latencyMs": round((time.perf_counter() - started) * 1000),
            "metadata": error_metadata,
        }

    output_text = str(output)
    if not output_text.strip():
        return {
            "output": "",
            "error": "Anthropic transport returned no output text",
            "latencyMs": round((time.perf_counter() - started) * 1000),
            "metadata": {
                "provider": "anthropic",
                "model": identity.returned_model,
                "requested_model": identity.requested_model,
                "returned_model": identity.returned_model,
                "request_id": identity.request_id,
                "finish_reason": metadata.get("finish_reason"),
            },
        }

    prompt_tokens = int(metadata.get("input_tokens") or 0)
    completion_tokens = int(metadata.get("output_tokens") or 0)
    return {
        "output": output_text,
        "tokenUsage": {
            "total": prompt_tokens + completion_tokens,
            "prompt": prompt_tokens,
            "completion": completion_tokens,
        },
        "cost": float(metadata.get("estimated_cost_usd") or 0.0),
        "latencyMs": round(float(metadata.get("latency_seconds") or 0.0) * 1000),
        "cached": False,
        "metadata": {
            "provider": "anthropic",
            "model": identity.returned_model,
            "requested_model": identity.requested_model,
            "returned_model": identity.returned_model,
            "request_id": identity.request_id,
            "finish_reason": metadata.get("finish_reason"),
        },
        "raw": {
            "id": identity.request_id,
            "model": identity.returned_model,
            "usage": {
                "input_tokens": prompt_tokens,
                "output_tokens": completion_tokens,
            },
        },
    }


def _configured_model(config: object) -> str:
    if not isinstance(config, dict):
        raise ValueError("Anthropic Messages provider config must be a mapping")
    model = config.get("model")
    if not isinstance(model, str) or not model.strip():
        raise ValueError("Anthropic Messages provider config.model is required")
    return model.strip()


def _timeout_seconds(config: dict) -> float:
    explicit_seconds = config.get("request_timeout_seconds")
    if explicit_seconds is not None:
        try:
            value = float(explicit_seconds)
        except (TypeError, ValueError):
            return 600.0
        return value if value > 0 else 600.0

    raw_timeout = config.get("timeout")
    if raw_timeout is None:
        return 600.0
    try:
        value = float(raw_timeout)
    except (TypeError, ValueError):
        return 600.0
    return value / 1000.0 if value > 0 else 600.0
