"""Promptfoo provider for OpenAI models that require the Responses API."""

from __future__ import annotations

import importlib
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from cine_forge.env import load_cine_forge_dotenv  # noqa: E402

load_cine_forge_dotenv(REPO_ROOT)

estimate_cost_usd = importlib.import_module("cine_forge.ai.llm").estimate_cost_usd
require_env = importlib.import_module("cine_forge.env").require_env

OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"


def call_api(prompt: str, options: dict, context: dict) -> dict:
    """Promptfoo entry point for text-only Responses API evals."""
    del context
    started = time.perf_counter()
    config = options.get("config", {})
    model = str(config.get("model") or "gpt-5.5-pro")
    max_tokens = int(config.get("max_output_tokens") or config.get("max_tokens") or 4096)
    if model.endswith("-pro"):
        # Pro models spend part of this budget on hidden reasoning tokens. The
        # legacy promptfoo configs were sized for visible Chat Completions output.
        max_tokens = max(max_tokens, int(config.get("pro_min_output_tokens") or 12000))
    timeout_seconds = _timeout_seconds(config)

    try:
        payload = _build_payload(
            prompt=prompt,
            model=model,
            max_tokens=max_tokens,
            config=config,
            include_temperature=True,
        )
        try:
            response = _request_json(payload, timeout_seconds=timeout_seconds)
        except RuntimeError as exc:
            if "temperature" not in str(exc).lower():
                raise
            payload = _build_payload(
                prompt=prompt,
                model=model,
                max_tokens=max_tokens,
                config=config,
                include_temperature=False,
            )
            response = _request_json(payload, timeout_seconds=timeout_seconds)
    except Exception as exc:
        latency_ms = round((time.perf_counter() - started) * 1000)
        return {"output": "", "error": str(exc), "latencyMs": latency_ms}

    latency_ms = round((time.perf_counter() - started) * 1000)
    output = _extract_output_text(response)
    usage = response.get("usage") or {}
    input_tokens = int(usage.get("input_tokens") or 0)
    output_tokens = int(usage.get("output_tokens") or 0)
    cost = estimate_cost_usd(model, input_tokens, output_tokens)

    input_details = usage.get("input_tokens_details") or {}
    output_details = usage.get("output_tokens_details") or {}
    return {
        "output": output,
        "tokenUsage": {
            "total": int(usage.get("total_tokens") or input_tokens + output_tokens),
            "prompt": input_tokens,
            "completion": output_tokens,
            "completionDetails": {
                "cachedPrompt": int(input_details.get("cached_tokens") or 0),
                "reasoning": int(output_details.get("reasoning_tokens") or 0),
            },
        },
        "cost": cost,
        "latencyMs": latency_ms,
        "cached": False,
        "metadata": {
            "provider": "openai",
            "model": model,
            "endpoint": "responses",
            "response_id": response.get("id"),
            "status": response.get("status"),
        },
    }


def _build_payload(
    *,
    prompt: str,
    model: str,
    max_tokens: int,
    config: dict[str, Any],
    include_temperature: bool,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": model,
        "input": prompt,
        "max_output_tokens": max_tokens,
        "store": False,
    }
    if include_temperature and "temperature" in config:
        payload["temperature"] = float(config.get("temperature", 0.0))

    response_format = config.get("response_format") or {}
    if response_format.get("type") == "json_object":
        payload["text"] = {"format": {"type": "json_object"}}

    reasoning_effort = config.get("reasoning_effort")
    if not reasoning_effort and model.endswith("-pro"):
        reasoning_effort = "medium"
    if reasoning_effort:
        payload["reasoning"] = {"effort": str(reasoning_effort)}
    return payload


def _timeout_seconds(config: dict[str, Any]) -> float:
    raw_timeout = config.get("timeout")
    if raw_timeout is None:
        return 600.0
    try:
        value = float(raw_timeout)
    except (TypeError, ValueError):
        return 600.0
    return value / 1000.0 if value > 1000 else value


def _request_json(payload: dict[str, Any], *, timeout_seconds: float) -> dict[str, Any]:
    api_key = require_env("OPENAI_API_KEY")
    request = urllib.request.Request(
        OPENAI_RESPONSES_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI Responses API returned HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"OpenAI Responses API request failed: {exc.reason}") from exc


def _extract_output_text(response: dict[str, Any]) -> str:
    output = response.get("output") or []
    chunks: list[str] = []
    for item in output:
        for content in item.get("content") or []:
            if content.get("type") == "output_text":
                chunks.append(str(content.get("text") or ""))
    return "\n".join(chunk for chunk in chunks if chunk)
