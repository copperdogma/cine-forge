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

from cine_forge.ai.model_identity import (  # noqa: E402
    validate_provider_response_identity,
)
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
    try:
        model = _configured_model(config)
        max_tokens = int(
            config.get("max_output_tokens") or config.get("max_tokens") or 4096
        )
        if model.endswith("-pro"):
            # Pro models spend part of this budget on hidden reasoning tokens.
            max_tokens = max(
                max_tokens,
                int(config.get("pro_min_output_tokens") or 12000),
            )
        timeout_seconds = _timeout_seconds(config)
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
        identity = validate_provider_response_identity(
            provider="openai",
            requested_model=model,
            returned_model=response.get("model"),
            request_id=response.get("id"),
            require_returned=True,
        )
    except Exception as exc:
        latency_ms = round((time.perf_counter() - started) * 1000)
        return {"output": "", "error": str(exc), "latencyMs": latency_ms}

    latency_ms = round((time.perf_counter() - started) * 1000)
    output = _extract_output_text(response)
    usage = response.get("usage") or {}
    input_tokens = int(usage.get("input_tokens") or 0)
    output_tokens = int(usage.get("output_tokens") or 0)
    cost = estimate_cost_usd(identity.billing_model, input_tokens, output_tokens)

    output_details = usage.get("output_tokens_details") or {}
    result = {
        "output": output,
        "tokenUsage": {
            "total": int(usage.get("total_tokens") or input_tokens + output_tokens),
            "prompt": input_tokens,
            "completion": output_tokens,
            "completionDetails": {
                "reasoning": int(output_details.get("reasoning_tokens") or 0),
            },
        },
        "cost": cost,
        "latencyMs": latency_ms,
        "cached": False,
        "metadata": {
            "provider": "openai",
            "model": identity.returned_model,
            "requested_model": identity.requested_model,
            "returned_model": identity.returned_model,
            "endpoint": "responses",
            "request_id": identity.request_id,
            "status": response.get("status"),
        },
        "raw": {
            "id": identity.request_id,
            "model": identity.returned_model,
            "status": response.get("status"),
            "usage": usage,
        },
    }
    status = response.get("status")
    if status not in (None, "completed"):
        result["error"] = (
            f"OpenAI Responses API returned status {status!r}: "
            f"{response.get('incomplete_details') or response.get('error') or 'no details'}"
        )
    elif not output.strip():
        result["error"] = "OpenAI Responses API returned no output_text content"
    return result


def _configured_model(config: object) -> str:
    if not isinstance(config, dict):
        raise ValueError("OpenAI Responses provider config must be a mapping")
    model = config.get("model")
    if not isinstance(model, str) or not model.strip():
        raise ValueError("OpenAI Responses provider config.model is required")
    return model.strip()


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
    direct_output = response.get("output_text")
    if isinstance(direct_output, str) and direct_output.strip():
        return direct_output
    output = response.get("output") or []
    chunks: list[str] = []
    for item in output:
        if not isinstance(item, dict):
            continue
        for content in item.get("content") or []:
            if not isinstance(content, dict):
                continue
            if content.get("type") == "output_text":
                chunks.append(str(content.get("text") or ""))
    return "\n".join(chunk for chunk in chunks if chunk)
