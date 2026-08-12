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
OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"
XAI_RESPONSES_URL = "https://api.x.ai/v1/responses"
OPUS_5_MODEL = "claude-opus-5"
OPUS_5_INPUT_PER_M = 5.0
OPUS_5_OUTPUT_PER_M = 25.0
QWEN38_OPENROUTER_MODEL = "qwen/qwen3.8-max"
QWEN38_OPENROUTER_PROVIDER = "Alibaba"
DEEPSEEK_V4_FLASH_OPENROUTER_MODEL = "deepseek/deepseek-v4-flash-0731"
DEEPSEEK_V4_FLASH_OPENROUTER_PROVIDER = "Phala"
GROK_46_MODEL = "grok-4.6"
OPENROUTER_MODEL_CONFIGS = {
    QWEN38_OPENROUTER_MODEL: {
        "provider": QWEN38_OPENROUTER_PROVIDER,
        "max_tokens": 131_072,
        "zdr": False,
    },
    DEEPSEEK_V4_FLASH_OPENROUTER_MODEL: {
        "provider": DEEPSEEK_V4_FLASH_OPENROUTER_PROVIDER,
        "max_tokens": 393_216,
        "zdr": True,
    },
}


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
        if model in OPENROUTER_MODEL_CONFIGS:
            provider, bare_model = "openrouter", model
        else:
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
        if bare_model == GROK_46_MODEL:
            output, metadata = _call_xai_responses_strict(
                prompt=call_options["prompt"],
                max_tokens=max_tokens,
                timeout_seconds=call_options["request_timeout_seconds"],
                reasoning_effort=str(config.get("reasoning_effort") or "low"),
            )
        elif bare_model in OPENROUTER_MODEL_CONFIGS:
            openrouter_config = OPENROUTER_MODEL_CONFIGS[bare_model]
            output, metadata = _call_openrouter_strict(
                prompt=call_options["prompt"],
                model=bare_model,
                upstream_provider=str(openrouter_config["provider"]),
                max_tokens=min(max_tokens, int(openrouter_config["max_tokens"])),
                timeout_seconds=call_options["request_timeout_seconds"],
                reasoning_effort=str(config.get("reasoning_effort") or "low"),
                zdr=bool(openrouter_config["zdr"]),
            )
        elif bare_model == OPUS_5_MODEL:
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
    reasoning_tokens = int(metadata.get("reasoning_output_tokens") or 0)
    visible_completion_tokens = int(
        metadata.get("visible_output_tokens") or completion_tokens
    )
    cost = float(
        metadata.get("reported_cost_usd")
        if metadata.get("reported_cost_usd") is not None
        else metadata.get("estimated_cost_usd") or 0.0
    )
    raw_usage = metadata.get("raw_usage")
    if not isinstance(raw_usage, dict):
        raw_usage = {
            "input_tokens": prompt_tokens,
            "output_tokens": completion_tokens,
        }
    return {
        "output": output.model_dump_json(),
        "tokenUsage": {
            "total": prompt_tokens + completion_tokens,
            "prompt": prompt_tokens,
            "completion": visible_completion_tokens,
            **(
                {"completionDetails": {"reasoning": reasoning_tokens}}
                if reasoning_tokens
                else {}
            ),
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
            "cost_estimated": bool(metadata.get("cost_estimated", True)),
            "runtime_prompt": "script_bible_v1.EXTRACTION_PROMPT",
            "runtime_schema": "cine_forge.schemas.ScriptBible",
            "upstream_provider": metadata.get("upstream_provider"),
            "reasoning_effort": metadata.get("reasoning_effort"),
            "allow_fallbacks": metadata.get("allow_fallbacks"),
            "data_collection": metadata.get("data_collection"),
            "zdr": metadata.get("zdr"),
            "store": metadata.get("store"),
            "x_zero_data_retention": metadata.get("x_zero_data_retention"),
        },
        "raw": {
            "id": identity.request_id,
            "model": identity.returned_model,
            "provider": metadata.get("upstream_provider"),
            "usage": raw_usage,
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


def _call_openrouter_strict(
    *,
    prompt: str,
    model: str,
    upstream_provider: str,
    max_tokens: int,
    timeout_seconds: float,
    reasoning_effort: str,
    zdr: bool,
) -> tuple[ScriptBible, dict[str, Any]]:
    """Call one pinned OpenRouter model/provider pair with strict JSON."""
    provider_preferences: dict[str, Any] = {
        "order": [upstream_provider],
        "allow_fallbacks": False,
        "require_parameters": True,
    }
    if zdr:
        provider_preferences.update(
            {
                "data_collection": "deny",
                "zdr": True,
            }
        )
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "reasoning": {"effort": reasoning_effort, "exclude": True},
        "provider": provider_preferences,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "script_bible",
                "strict": True,
                "schema": _to_openai_strict_schema(ScriptBible.model_json_schema()),
            },
        },
    }
    started = time.perf_counter()
    raw = _request_openrouter_json(payload, timeout_seconds=timeout_seconds)
    latency_seconds = time.perf_counter() - started
    identity = validate_provider_response_identity(
        provider="openrouter",
        requested_model=model,
        returned_model=raw.get("model"),
        request_id=raw.get("id"),
        require_returned=True,
    )
    returned_provider = raw.get("provider")
    if returned_provider != upstream_provider:
        raise RuntimeError(
            "OpenRouter response provider does not match pinned provider: "
            f"expected {upstream_provider}, received {returned_provider!r}"
        )
    choices = raw.get("choices")
    if not isinstance(choices, list) or len(choices) != 1:
        raise RuntimeError("OpenRouter response must contain exactly one choice")
    choice = choices[0]
    if not isinstance(choice, dict):
        raise RuntimeError("OpenRouter response choice must be a mapping")
    finish_reason = choice.get("finish_reason")
    if finish_reason != "stop":
        raise RuntimeError(f"OpenRouter response did not complete: {finish_reason!r}")
    message = choice.get("message")
    if not isinstance(message, dict):
        raise RuntimeError("OpenRouter response message must be a mapping")
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("OpenRouter transport returned no output text")
    output = ScriptBible.model_validate_json(content)

    usage = raw.get("usage")
    if not isinstance(usage, dict):
        raise RuntimeError("OpenRouter response usage must be a mapping")
    prompt_tokens = _token_count(usage.get("prompt_tokens"), "prompt_tokens")
    completion_tokens = _token_count(
        usage.get("completion_tokens"), "completion_tokens"
    )
    total_tokens = _token_count(usage.get("total_tokens"), "total_tokens")
    if total_tokens != prompt_tokens + completion_tokens:
        raise RuntimeError("OpenRouter total_tokens does not reconcile")
    reported_cost = usage.get("cost")
    if (
        isinstance(reported_cost, bool)
        or not isinstance(reported_cost, (int, float))
        or reported_cost < 0
    ):
        raise RuntimeError("OpenRouter usage.cost must be a nonnegative number")
    return output, {
        "requested_model": identity.requested_model,
        "returned_model": identity.returned_model,
        "request_id": identity.request_id,
        "finish_reason": finish_reason,
        "input_tokens": prompt_tokens,
        "output_tokens": completion_tokens,
        "reported_cost_usd": float(reported_cost),
        "cost_estimated": False,
        "latency_seconds": latency_seconds,
        "upstream_provider": returned_provider,
        "reasoning_effort": reasoning_effort,
        "allow_fallbacks": False,
        "data_collection": "deny" if zdr else None,
        "zdr": zdr,
        "raw_usage": usage,
    }


def _call_xai_responses_strict(
    *,
    prompt: str,
    max_tokens: int,
    timeout_seconds: float,
    reasoning_effort: str,
) -> tuple[ScriptBible, dict[str, Any]]:
    """Call Grok 4.6 through native Responses with strict JSON and no storage."""
    payload = {
        "model": GROK_46_MODEL,
        "input": [
            {
                "role": "user",
                "content": [{"type": "input_text", "text": prompt}],
            }
        ],
        "reasoning": {"effort": reasoning_effort},
        "store": False,
        "max_output_tokens": max_tokens,
        "text": {
            "format": {
                "type": "json_schema",
                "name": "script_bible",
                "strict": True,
                "schema": _to_openai_strict_schema(ScriptBible.model_json_schema()),
            }
        },
    }
    started = time.perf_counter()
    raw, x_zero_data_retention = _request_xai_responses_json(
        payload,
        timeout_seconds=timeout_seconds,
    )
    latency_seconds = time.perf_counter() - started
    identity = validate_provider_response_identity(
        provider="xai",
        requested_model=GROK_46_MODEL,
        returned_model=raw.get("model"),
        request_id=raw.get("id"),
        require_returned=True,
    )
    status = raw.get("status")
    if status != "completed" or raw.get("incomplete_details") is not None:
        raise RuntimeError(
            "xAI response did not complete: "
            f"status={status!r}, incomplete={raw.get('incomplete_details')!r}"
        )
    output = raw.get("output")
    if not isinstance(output, list):
        raise RuntimeError("xAI response output must be a list")
    text = "".join(
        part.get("text", "")
        for item in output
        if isinstance(item, dict)
        for part in item.get("content", [])
        if isinstance(part, dict) and part.get("type") == "output_text"
    )
    if not text.strip():
        raise RuntimeError("xAI Responses transport returned no output text")
    bible = ScriptBible.model_validate_json(text)

    usage = raw.get("usage")
    if not isinstance(usage, dict):
        raise RuntimeError("xAI response usage must be a mapping")
    input_tokens = _token_count(usage.get("input_tokens"), "input_tokens")
    output_tokens = _token_count(usage.get("output_tokens"), "output_tokens")
    total_tokens = _token_count(usage.get("total_tokens"), "total_tokens")
    if total_tokens != input_tokens + output_tokens:
        raise RuntimeError("xAI total_tokens does not reconcile")
    details = usage.get("output_tokens_details")
    if not isinstance(details, dict):
        raise RuntimeError("xAI output_tokens_details must be a mapping")
    reasoning_tokens = _token_count(
        details.get("reasoning_tokens"), "reasoning_tokens"
    )
    if reasoning_tokens > output_tokens:
        raise RuntimeError("xAI reasoning_tokens exceeds output_tokens")
    cost_ticks = _token_count(usage.get("cost_in_usd_ticks"), "cost_in_usd_ticks")
    return bible, {
        "requested_model": identity.requested_model,
        "returned_model": identity.returned_model,
        "request_id": identity.request_id,
        "finish_reason": status,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "visible_output_tokens": output_tokens - reasoning_tokens,
        "reasoning_output_tokens": reasoning_tokens,
        "reported_cost_usd": cost_ticks / 10_000_000_000,
        "cost_estimated": False,
        "latency_seconds": latency_seconds,
        "reasoning_effort": reasoning_effort,
        "store": False,
        "x_zero_data_retention": x_zero_data_retention,
        "zdr": x_zero_data_retention == "true",
        "raw_usage": usage,
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


def _request_openrouter_json(payload: dict, *, timeout_seconds: float) -> dict:
    request = urllib.request.Request(
        OPENROUTER_CHAT_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {require_env('OPENROUTER_API_KEY')}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
            raw = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenRouter HTTP error {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"OpenRouter request failed: {exc.reason}") from exc
    if not isinstance(raw, dict):
        raise RuntimeError("OpenRouter response must be a mapping")
    return raw


def _request_xai_responses_json(
    payload: dict,
    *,
    timeout_seconds: float,
) -> tuple[dict, str | None]:
    request = urllib.request.Request(
        XAI_RESPONSES_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {require_env('XAI_API_KEY')}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
            raw = json.loads(response.read().decode("utf-8"))
            x_zero_data_retention = response.headers.get("x-zero-data-retention")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"xAI HTTP error {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"xAI request failed: {exc.reason}") from exc
    if not isinstance(raw, dict):
        raise RuntimeError("xAI response must be a mapping")
    return raw, x_zero_data_retention


def _token_count(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise RuntimeError(f"Provider {name} must be a nonnegative integer")
    return value
