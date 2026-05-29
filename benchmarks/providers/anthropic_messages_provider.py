"""Promptfoo provider for Anthropic Messages API models with current API quirks."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from cine_forge.env import load_cine_forge_dotenv  # noqa: E402

load_cine_forge_dotenv(REPO_ROOT)

call_llm = importlib.import_module("cine_forge.ai.llm").call_llm


def call_api(prompt: str, options: dict, context: dict) -> dict:
    """Promptfoo entry point for text-only Anthropic Messages API evals."""
    del context
    config = options.get("config", {})
    model = str(config.get("model") or "claude-opus-4-8")
    max_tokens = int(config.get("max_tokens") or 4096)
    temperature = float(config.get("temperature") or 0.0)
    max_retries = int(config.get("max_retries") or 1)
    timeout_seconds = _timeout_seconds(config)

    try:
        output, metadata = call_llm(
            prompt,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            max_retries=max_retries,
            request_timeout_seconds=timeout_seconds,
        )
    except Exception as exc:
        return {"output": "", "error": str(exc)}

    prompt_tokens = int(metadata.get("input_tokens") or 0)
    completion_tokens = int(metadata.get("output_tokens") or 0)
    return {
        "output": str(output),
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
            "model": model,
            "request_id": metadata.get("request_id"),
            "finish_reason": metadata.get("finish_reason"),
        },
    }


def _timeout_seconds(config: dict) -> float:
    raw_timeout = config.get("timeout")
    if raw_timeout is None:
        return 600.0
    try:
        value = float(raw_timeout)
    except (TypeError, ValueError):
        return 600.0
    return value / 1000.0 if value > 1000 else value
