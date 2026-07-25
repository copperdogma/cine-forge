"""Promptfoo provider for the exact production script-bible prompt and schema."""

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
from cine_forge.env import load_cine_forge_dotenv, require_env  # noqa: E402
from cine_forge.modules.ingest.script_bible_v1.main import (  # noqa: E402
    DEFAULT_MAX_TOKENS,
    DEFAULT_THINKING_LEVEL,
    DEFAULT_WORK_MODEL,
    EXTRACTION_PROMPT,
)
from cine_forge.schemas import ScriptBible  # noqa: E402

load_cine_forge_dotenv(REPO_ROOT)

_llm = importlib.import_module("cine_forge.ai.llm")
call_llm = _llm.call_llm
_parse_provider = _llm._parse_provider
_to_openai_strict_schema = _llm._to_openai_strict_schema

ANTHROPIC_MESSAGES_URL = "https://api.anthropic.com/v1/messages"
OPUS_5_MODEL = "claude-opus-5"
OPUS_5_INPUT_PER_M = 5.0
OPUS_5_OUTPUT_PER_M = 25.0


def call_api(prompt: str, options: dict, context: dict) -> dict:
    """Run one screenplay through the exact production prompt/schema boundary."""
    del prompt
    config = options.get("config", {})
    started = time.perf_counter()
    model: str | None = None

    try:
        model = _configured_model(config)
        screenplay = _screenplay(context)
        max_tokens = int(config.get("max_tokens") or DEFAULT_MAX_TOKENS)
        max_retries = int(config.get("max_retries") or 1)
        provider, bare_model = _parse_provider(model)
        call_options = {
            "prompt": EXTRACTION_PROMPT.format(script_text=screenplay),
            "model": model,
            "response_schema": ScriptBible,
            "max_tokens": max_tokens,
            "max_retries": max_retries,
            "fail_on_truncation": True,
            "request_timeout_seconds": _timeout_seconds(config),
        }
        if bare_model == DEFAULT_WORK_MODEL:
            call_options["thinking_level"] = str(
                config.get("thinking_level") or DEFAULT_THINKING_LEVEL
            )
        if bare_model == OPUS_5_MODEL:
            output, metadata = _call_opus_5(
                prompt=call_options["prompt"],
                max_tokens=max_tokens,
                timeout_seconds=call_options["request_timeout_seconds"],
            )
        else:
            output, metadata = call_llm(**call_options)
        if not isinstance(output, ScriptBible):
            raise TypeError("script-bible runtime provider expected ScriptBible output")
        identity = validate_provider_response_identity(
            provider=provider,
            requested_model=bare_model,
            returned_model=metadata.get("returned_model"),
            request_id=metadata.get("request_id"),
            require_returned=True,
        )
    except Exception as exc:
        error_metadata = {"provider": "runtime-script-bible"}
        if model is not None:
            error_metadata["requested_model"] = model
        return {
            "output": "",
            "error": str(exc),
            "latencyMs": round((time.perf_counter() - started) * 1000),
            "metadata": error_metadata,
        }

    prompt_tokens = int(metadata.get("input_tokens") or 0)
    completion_tokens = int(metadata.get("output_tokens") or 0)
    cost = float(metadata.get("estimated_cost_usd") or 0.0)
    return {
        "output": output.model_dump_json(),
        "tokenUsage": {
            "total": prompt_tokens + completion_tokens,
            "prompt": prompt_tokens,
            "completion": completion_tokens,
        },
        "cost": cost,
        "latencyMs": round(float(metadata.get("latency_seconds") or 0.0) * 1000),
        "cached": False,
        "metadata": {
            "provider": identity.provider,
            "model": identity.returned_model,
            "requested_model": identity.requested_model,
            "returned_model": identity.returned_model,
            "request_id": identity.request_id,
            "finish_reason": metadata.get("finish_reason"),
            "cost_estimated": True,
            "runtime_prompt": "script_bible_v1.EXTRACTION_PROMPT",
            "runtime_schema": "cine_forge.schemas.ScriptBible",
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
        raise ValueError("script-bible runtime provider config must be a mapping")
    model = config.get("model")
    if not isinstance(model, str) or not model.strip():
        raise ValueError("script-bible runtime provider config.model is required")
    return model.strip()


def _screenplay(context: object) -> str:
    if not isinstance(context, dict):
        raise ValueError("script-bible runtime provider context must be a mapping")
    variables = context.get("vars")
    if not isinstance(variables, dict):
        raise ValueError("script-bible runtime provider context.vars is required")
    screenplay = variables.get("screenplay")
    if not isinstance(screenplay, str) or not screenplay.strip():
        raise ValueError("script-bible runtime provider screenplay is required")
    return screenplay


def _timeout_seconds(config: dict) -> float:
    raw = config.get("request_timeout_seconds", 600)
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return 600.0
    return value if value > 0 else 600.0


def _call_opus_5(
    *,
    prompt: str,
    max_tokens: int,
    timeout_seconds: float,
) -> tuple[ScriptBible, dict[str, Any]]:
    """Call Opus 5 with its provider-enforced structured-output contract."""
    payload = {
        "model": OPUS_5_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": min(max_tokens, 128_000),
        "output_config": {
            "format": {
                "type": "json_schema",
                "schema": _anthropic_schema(ScriptBible.model_json_schema()),
            }
        },
    }
    started = time.perf_counter()
    raw = _request_json(payload, timeout_seconds=timeout_seconds)
    latency_seconds = time.perf_counter() - started
    identity = validate_provider_response_identity(
        provider="anthropic",
        requested_model=OPUS_5_MODEL,
        returned_model=raw.get("model"),
        request_id=raw.get("id"),
        require_returned=True,
    )
    stop_reason = raw.get("stop_reason")
    if stop_reason != "end_turn":
        raise RuntimeError(f"Anthropic response did not complete: {stop_reason!r}")
    content = raw.get("content")
    if not isinstance(content, list):
        raise RuntimeError("Anthropic response content must be a list")
    text = "".join(
        block.get("text", "")
        for block in content
        if isinstance(block, dict) and block.get("type") == "text"
    )
    if not text.strip():
        raise RuntimeError("Anthropic transport returned no output text")
    output = ScriptBible.model_validate_json(text)
    usage = raw.get("usage")
    if not isinstance(usage, dict):
        raise RuntimeError("Anthropic response usage must be a mapping")
    input_tokens = _token_count(usage.get("input_tokens"), "input_tokens")
    output_tokens = _token_count(usage.get("output_tokens"), "output_tokens")
    estimated_cost = (
        input_tokens * OPUS_5_INPUT_PER_M + output_tokens * OPUS_5_OUTPUT_PER_M
    ) / 1_000_000
    return output, {
        "requested_model": identity.requested_model,
        "returned_model": identity.returned_model,
        "request_id": identity.request_id,
        "finish_reason": stop_reason,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "estimated_cost_usd": estimated_cost,
        "latency_seconds": latency_seconds,
    }


def _anthropic_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Match Anthropic SDK schema simplification while preserving post-validation."""
    normalized = _to_openai_strict_schema(schema)

    def visit(node: object) -> None:
        if isinstance(node, dict):
            notes = []
            for keyword, label in (
                ("minimum", "minimum"),
                ("maximum", "maximum"),
                ("minLength", "minimum length"),
                ("maxLength", "maximum length"),
            ):
                if keyword in node:
                    notes.append(f"{label}: {node.pop(keyword)}")
            if notes:
                description = str(node.get("description") or "").strip()
                suffix = f"Constraints enforced after parsing: {', '.join(notes)}."
                node["description"] = f"{description} {suffix}".strip()
            for value in node.values():
                visit(value)
        elif isinstance(node, list):
            for value in node:
                visit(value)

    visit(normalized)
    return normalized


def _request_json(payload: dict, *, timeout_seconds: float) -> dict:
    request = urllib.request.Request(
        ANTHROPIC_MESSAGES_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "x-api-key": require_env("ANTHROPIC_API_KEY"),
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
            raw = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Anthropic HTTP error {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Anthropic request failed: {exc.reason}") from exc
    if not isinstance(raw, dict):
        raise RuntimeError("Anthropic response must be a mapping")
    return raw


def _token_count(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise RuntimeError(f"Anthropic {name} must be a nonnegative integer")
    return value
