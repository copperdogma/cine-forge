"""Thin LLM call wrapper with retries and cost metadata."""

from __future__ import annotations

import json
import logging
import random
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from functools import partial
from typing import Any

from pydantic import BaseModel

from cine_forge.ai.errors import LLMCallError
from cine_forge.ai.fixture_responses import fixture_response
from cine_forge.ai.gemini_response import (
    normalize_gemini_response as _normalize_gemini_response,
)
from cine_forge.ai.model_identity import validate_provider_response_identity
from cine_forge.ai.token_usage import (
    aliased_token_count,
    validate_standard_token_usage,
    validate_token_count,
)
from cine_forge.env import require_env

logger = logging.getLogger(__name__)

# Input/output pricing in USD per 1M tokens.
MODEL_PRICING_PER_M_TOKEN: dict[str, tuple[float, float]] = {
    # OpenAI
    "gpt-4o": (5.0, 15.0),
    "gpt-4o-mini": (0.15, 0.6),
    "gpt-4.1": (2.0, 8.0),
    "gpt-4.1-mini": (0.40, 1.60),
    "gpt-5.2": (2.0, 8.0),
    "gpt-5.4": (2.5, 15.0),
    "gpt-5.5": (5.0, 30.0),
    "gpt-5.5-pro": (30.0, 180.0),
    "gpt-5.4-mini": (0.75, 4.5),
    "gpt-5.4-nano": (0.20, 1.25),
    # xAI
    "grok-4.3": (1.25, 2.50),
    "grok-4.5": (2.0, 6.0),
    # Anthropic
    "claude-sonnet-4-5": (3.0, 15.0),
    "claude-sonnet-4-5-20250929": (3.0, 15.0),
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-opus-4-8": (5.0, 25.0),
    "claude-opus-4-6": (15.0, 75.0),
    "claude-haiku-4-5-20251001": (0.80, 4.0),
    # Google
    "gemini-2.5-flash-lite": (0.075, 0.30),
    "gemini-2.5-flash": (0.15, 0.60),
    "gemini-2.5-pro": (1.25, 10.0),
    "gemini-3-flash-preview": (0.15, 0.60),
    "gemini-3.1-flash-lite": (0.10, 0.40),
    "gemini-3.1-pro-preview": (1.50, 10.0),
    "gemini-3.5-flash": (1.50, 9.0),
    "gemini-3.5-flash-lite": (0.30, 2.50),
    "gemini-3.6-flash": (1.50, 7.50),
}

ANTHROPIC_MODELS_WITHOUT_TEMPERATURE = {
    "claude-opus-4-8",
}

OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"
XAI_CHAT_URL = "https://api.x.ai/v1/chat/completions"
ANTHROPIC_MESSAGES_URL = "https://api.anthropic.com/v1/messages"
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

# Provider identifiers used by _parse_provider().
PROVIDER_OPENAI = "openai"
PROVIDER_XAI = "xai"
PROVIDER_ANTHROPIC = "anthropic"
PROVIDER_GOOGLE = "google"

_GEMINI_MODELS_WITHOUT_SAMPLING = {
    "gemini-3.5-flash-lite",
    "gemini-3.6-flash",
}
_GEMINI_MODELS_WITH_THINKING_LEVEL = {
    "gemini-3.5-flash-lite",
    "gemini-3.6-flash",
}
_GEMINI_THINKING_LEVELS = {"minimal", "low", "medium", "high"}
_GEMINI_MAX_OUTPUT_TOKENS = 65_536

_CIRCUIT_BREAKER_FAILURE_THRESHOLD = 3
_CIRCUIT_BREAKER_COOLDOWN_SECONDS = 30.0


@dataclass
class _CircuitBreakerState:
    consecutive_failures: int = 0
    opened_until: float = 0.0
    half_open: bool = False


_CIRCUIT_BREAKERS: dict[str, _CircuitBreakerState] = {}


def call_llm(
    prompt: str,
    model: str,
    response_schema: type[BaseModel] | None = None,
    max_retries: int = 2,
    max_tokens: int | None = None,
    temperature: float = 0.0,
    fail_on_truncation: bool = False,
    transport: Any | None = None,
    retry_base_delay_seconds: float = 0.5,
    retry_jitter_ratio: float = 0.25,
    enable_caching: bool = False,
    request_timeout_seconds: float | None = None,
    thinking_level: str | None = None,
) -> tuple[str | BaseModel, dict[str, Any]]:
    """Call an LLM and return text (or parsed schema) with call metadata."""
    if max_retries < 0:
        raise ValueError("max_retries must be >= 0")
    if model == "fixture":
        started = time.perf_counter()
        parsed = fixture_response(prompt=prompt, response_schema=response_schema)
        latency = time.perf_counter() - started
        metadata = {
            "model": model,
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": 0.0,
            "latency_seconds": round(latency, 6),
            "request_id": "fixture-response",
            "finish_reason": "stop",
        }
        return parsed, metadata

    provider, bare_model = _parse_provider(model)
    if transport is not None:
        # Injected transport (testing) — bypass provider dispatch entirely.
        sender = transport
        normalizer = None
    elif provider == PROVIDER_ANTHROPIC:
        sender = partial(
            _anthropic_transport,
            request_timeout_seconds=request_timeout_seconds,
        )
        normalizer = _normalize_anthropic_response
    elif provider == PROVIDER_GOOGLE:
        sender = partial(
            _gemini_transport,
            request_timeout_seconds=request_timeout_seconds,
        )
        normalizer = partial(_normalize_gemini_response, expected_model=bare_model)
    elif provider == PROVIDER_XAI:
        sender = partial(
            _xai_transport,
            request_timeout_seconds=request_timeout_seconds,
        )
        normalizer = None  # xAI Chat Completions is OpenAI-compatible
    else:
        sender = partial(
            _openai_transport,
            request_timeout_seconds=request_timeout_seconds,
        )
        normalizer = None  # OpenAI is the canonical format

    last_error: Exception | None = None
    active_max_tokens = max_tokens
    active_temp = temperature

    if transport is None and _is_circuit_breaker_open(provider):
        raise LLMCallError(f"{provider} circuit breaker open; retry later")

    for attempt in range(max_retries + 1):
        try:
            started = time.perf_counter()
            if provider == PROVIDER_ANTHROPIC and transport is None:
                payload = _build_anthropic_payload(
                    model=bare_model,
                    prompt=prompt,
                    temperature=active_temp,
                    max_tokens=active_max_tokens,
                    response_schema=response_schema,
                    enable_caching=enable_caching,
                )
            elif provider == PROVIDER_GOOGLE and transport is None:
                payload = _build_gemini_payload(
                    model=bare_model,
                    prompt=prompt,
                    temperature=active_temp,
                    max_tokens=active_max_tokens,
                    response_schema=response_schema,
                    thinking_level=thinking_level,
                )
            else:
                payload = {
                    "model": bare_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": active_temp,
                    **({"max_completion_tokens": active_max_tokens} if active_max_tokens else {}),
                    **_response_format_payload(response_schema),
                }
            raw_response = sender(payload)
            if normalizer is not None:
                raw_response = normalizer(raw_response)
            latency = time.perf_counter() - started
            parsed, metadata = _parse_response(
                raw_response=raw_response,
                model=bare_model,
                response_schema=response_schema,
                latency_seconds=latency,
                provider=provider,
                require_provider_identity=transport is None,
            )
            if fail_on_truncation and metadata.get("finish_reason") == "length":
                raise LLMCallError("LLM output truncated due to max token limit")
            if transport is None:
                _record_provider_success(provider)
            return parsed, metadata
        except (LLMCallError, Exception) as exc:
            last_error = exc
            
            # Decide if we should retry
            is_json_error = "valid json" in str(exc).lower()
            exc_msg = str(exc).lower()
            is_truncation = (
                "truncated" in exc_msg
                or "max token limit" in exc_msg
                or "unterminated string" in exc_msg
            )
            
            retryable = is_json_error or is_truncation or _is_transient_error(exc)
            if transport is None and _is_transient_error(exc):
                _record_provider_transient_failure(provider)

            if attempt < max_retries and retryable:
                # Adjust params for retry
                if is_truncation and active_max_tokens:
                    active_max_tokens = int(active_max_tokens * 1.5)
                if is_json_error:
                    # SOTA models sometimes benefit from a tiny bit of heat on a retry
                    active_temp = min(active_temp + 0.1, 0.7)
                
                delay_seconds = _retry_delay_seconds(
                    attempt=attempt,
                    base_delay_seconds=retry_base_delay_seconds,
                    jitter_ratio=retry_jitter_ratio,
                )
                time.sleep(delay_seconds)
                continue
            
            # Terminal failure
            if isinstance(exc, LLMCallError):
                raise
            break

    raise LLMCallError(f"LLM call failed after retries: {last_error}") from last_error


def estimate_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate call cost from token counts and static pricing table."""
    input_price, output_price = MODEL_PRICING_PER_M_TOKEN.get(model, (0.0, 0.0))
    input_cost = (max(input_tokens, 0) / 1_000_000) * input_price
    output_cost = (max(output_tokens, 0) / 1_000_000) * output_price
    return round(input_cost + output_cost, 8)


def _response_format_payload(response_schema: type[BaseModel] | None) -> dict[str, Any]:
    if not response_schema:
        return {}
    schema = _to_openai_strict_schema(response_schema.model_json_schema())
    return {
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": response_schema.__name__,
                "strict": True,
                "schema": schema,
            },
        }
    }


def _to_openai_strict_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Ensure JSON schema is compatible with OpenAI strict mode."""

    def walk(node: Any) -> Any:
        if isinstance(node, dict):
            updated = {key: walk(value) for key, value in node.items()}
            if updated.get("type") == "object":
                updated.setdefault("additionalProperties", False)
                properties = updated.get("properties")
                if isinstance(properties, dict):
                    updated["required"] = list(properties.keys())
            return updated
        if isinstance(node, list):
            return [walk(item) for item in node]
        return node

    return walk(schema)


def _parse_response(
    raw_response: dict[str, Any],
    model: str,
    response_schema: type[BaseModel] | None,
    latency_seconds: float,
    provider: str | None = None,
    require_provider_identity: bool = False,
) -> tuple[str | BaseModel, dict[str, Any]]:
    choices = raw_response.get("choices", [])
    if not choices:
        raise LLMCallError("LLM response missing choices")

    message = choices[0].get("message", {})
    text = message.get("content", "")
    if isinstance(text, list):
        text = "".join(part.get("text", "") for part in text if isinstance(part, dict))
    if not isinstance(text, str):
        raise LLMCallError("LLM message content is not text")

    metadata, finish_reason = _response_metadata(
        raw_response=raw_response,
        first_choice=choices[0],
        model=model,
        latency_seconds=latency_seconds,
        provider=provider or _parse_provider(model)[0],
        require_provider_identity=require_provider_identity,
    )

    if not response_schema:
        return text, metadata

    # Fail early on truncated structured output — retries can bump max_tokens.
    if finish_reason == "length":
        raise LLMCallError("LLM output truncated due to max token limit")

    # 1. Try to find a JSON code block with regex
    # This handles cases where the model puts the JSON inside ```json ... ```
    # but also includes other conversational text.
    cleaned_text = text.strip()
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned_text)
    if json_match:
        cleaned_text = json_match.group(1).strip()
    else:
        # Fallback: simple stripping of markdown markers if regex failed
        if cleaned_text.startswith("```"):
            cleaned_text = re.sub(r"^```[a-zA-Z]*\n", "", cleaned_text)
            cleaned_text = re.sub(r"\n```$", "", cleaned_text)
            cleaned_text = cleaned_text.strip()

    try:
        payload = json.loads(cleaned_text)
    except json.JSONDecodeError as exc:
        # For autonomous debugging: log the actual malformed text
        print(
            f"\n[DEBUG] Structured response was not valid JSON. "
            f"First 500 chars:\n{cleaned_text[:500]}..."
        )
        print(f"[DEBUG] Raw response was (first 500 chars):\n{text[:500]}...")
        raise LLMCallError(f"Structured response was not valid JSON: {exc}") from exc
    return response_schema.model_validate(payload), metadata


def _response_metadata(
    *,
    raw_response: dict[str, Any],
    first_choice: dict[str, Any],
    model: str,
    latency_seconds: float,
    provider: str,
    require_provider_identity: bool,
) -> tuple[dict[str, Any], object]:
    """Build auditable usage metadata without inflating response parsing."""
    usage = raw_response.get("usage", {})
    if not isinstance(usage, dict):
        raise LLMCallError("LLM response usage must be a mapping")
    usage_contract: dict[str, object] = {}
    if "total_tokens" in usage:
        usage_contract["total_tokens"] = usage["total_tokens"]
    completion_details = (
        usage.get("completion_tokens_details")
        or usage.get("completionDetails")
        or {}
    )
    visible_output_tokens: int | None = None
    if isinstance(completion_details, dict):
        visible_tokens = completion_details.get("visible_tokens")
        if visible_tokens is not None:
            visible_output_tokens = validate_token_count(
                visible_tokens,
                "visible_output_tokens",
            )
    if provider == PROVIDER_XAI and isinstance(completion_details, dict):
        reasoning_evidence = aliased_token_count(
            completion_details,
            ("reasoning_tokens", "reasoning"),
            name="completion token details",
        )
        if reasoning_evidence is not None:
            usage_contract["reasoning_completion_tokens"] = reasoning_evidence
    token_usage = validate_standard_token_usage(
        prompt_tokens=usage.get("prompt_tokens"),
        completion_tokens=usage.get("completion_tokens"),
        allow_total_derived_hidden=provider == PROVIDER_XAI,
        **usage_contract,
    )
    input_tokens = token_usage.prompt
    output_tokens = token_usage.visible_completion
    reasoning_output_tokens = token_usage.hidden_completion
    identity = validate_provider_response_identity(
        provider=provider,
        requested_model=model,
        returned_model=raw_response.get("model"),
        request_id=raw_response.get("id"),
        require_returned=require_provider_identity,
    )
    finish_reason = first_choice.get("finish_reason")
    metadata: dict[str, Any] = {
        "model": model,
        "requested_model": identity.requested_model,
        "returned_model": identity.returned_model,
        "provider": identity.provider,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "estimated_cost_usd": estimate_cost_usd(
            identity.billing_model,
            input_tokens,
            output_tokens,
        ),
        "latency_seconds": round(latency_seconds, 6),
        "request_id": identity.request_id,
        "finish_reason": finish_reason,
    }
    if reasoning_output_tokens > 0:
        metadata["reasoning_output_tokens"] = reasoning_output_tokens
        metadata["estimated_cost_usd"] = estimate_cost_usd(
            identity.billing_model,
            input_tokens,
            token_usage.billed_completion,
        )
    if visible_output_tokens is not None:
        metadata["visible_output_tokens"] = visible_output_tokens
    if model.startswith("gemini-") and isinstance(completion_details, dict):
        metadata["reasoning_output_tokens"] = int(
            completion_details.get("reasoning_tokens") or 0
        )
    cache_read = usage.get("cache_read_input_tokens")
    cache_write = usage.get("cache_creation_input_tokens")
    if cache_read is not None or cache_write is not None:
        metadata["cache_read_input_tokens"] = (
            validate_token_count(cache_read, "cache_read_input_tokens")
            if cache_read is not None
            else 0
        )
        metadata["cache_creation_input_tokens"] = (
            validate_token_count(cache_write, "cache_creation_input_tokens")
            if cache_write is not None
            else 0
        )
        logger.debug(
            "Anthropic cache: read=%d write=%d model=%s",
            metadata["cache_read_input_tokens"],
            metadata["cache_creation_input_tokens"],
            model,
        )
    return metadata, finish_reason


def _openai_transport(
    request_payload: dict[str, Any],
    *,
    request_timeout_seconds: float | None = None,
) -> dict[str, Any]:
    try:
        api_key = require_env("OPENAI_API_KEY")
    except RuntimeError as exc:
        raise LLMCallError(f"{exc} for OpenAI transport") from exc

    encoded = json.dumps(request_payload).encode("utf-8")
    request = urllib.request.Request(
        OPENAI_CHAT_URL,
        data=encoded,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(
            request,
            timeout=_resolve_request_timeout(request_timeout_seconds),
        ) as response:  # noqa: S310
            body = response.read().decode("utf-8")
            return json.loads(body)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise LLMCallError(f"OpenAI HTTP error {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise LLMCallError(f"OpenAI request failed: {exc.reason}") from exc


def _xai_transport(
    request_payload: dict[str, Any],
    *,
    request_timeout_seconds: float | None = None,
) -> dict[str, Any]:
    try:
        api_key = require_env("XAI_API_KEY")
    except RuntimeError as exc:
        raise LLMCallError(f"{exc} for xAI transport") from exc

    encoded = json.dumps(request_payload).encode("utf-8")
    request = urllib.request.Request(
        XAI_CHAT_URL,
        data=encoded,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(
            request,
            timeout=_resolve_request_timeout(request_timeout_seconds),
        ) as response:  # noqa: S310
            body = response.read().decode("utf-8")
            return json.loads(body)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise LLMCallError(f"xAI HTTP error {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise LLMCallError(f"xAI request failed: {exc.reason}") from exc


def _parse_provider(model: str) -> tuple[str, str]:
    """Parse provider prefix from model string, falling back to auto-detection.

    Accepted formats:
        "anthropic:claude-sonnet-4-6"  -> ("anthropic", "claude-sonnet-4-6")
        "google:gemini-2.5-pro"        -> ("google", "gemini-2.5-pro")
        "openai:gpt-4.1"              -> ("openai", "gpt-4.1")
        "xai:grok-4.3"                -> ("xai", "grok-4.3")
        "claude-sonnet-4-6"           -> ("anthropic", "claude-sonnet-4-6")
        "gemini-2.5-pro"              -> ("google", "gemini-2.5-pro")
        "grok-4.3"                    -> ("xai", "grok-4.3")
        "gpt-4.1"                     -> ("openai", "gpt-4.1")
    """
    if ":" in model:
        provider, bare_model = model.split(":", 1)
        provider = provider.lower()
        if provider in (
            PROVIDER_OPENAI,
            PROVIDER_XAI,
            PROVIDER_ANTHROPIC,
            PROVIDER_GOOGLE,
        ):
            return provider, bare_model
    # Auto-detect from model name
    if model.startswith("claude-"):
        return PROVIDER_ANTHROPIC, model
    if model.startswith("gemini-"):
        return PROVIDER_GOOGLE, model
    if model.startswith("grok-"):
        return PROVIDER_XAI, model
    return PROVIDER_OPENAI, model


def _build_anthropic_payload(
    model: str,
    prompt: str,
    temperature: float,
    max_tokens: int | None,
    response_schema: type[BaseModel] | None,
    enable_caching: bool = False,
) -> dict[str, Any]:
    """Build an Anthropic Messages API request payload."""
    if enable_caching:
        user_content: Any = [
            {"type": "text", "text": prompt, "cache_control": {"type": "ephemeral"}}
        ]
    else:
        user_content = prompt

    payload: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": user_content}],
        "max_tokens": max_tokens or 16384,
    }
    if model not in ANTHROPIC_MODELS_WITHOUT_TEMPERATURE:
        payload["temperature"] = temperature
    if response_schema:
        schema_json = json.dumps(response_schema.model_json_schema(), indent=2)
        payload["system"] = (
            f"You must respond with valid JSON matching this schema:\n{schema_json}\n\n"
            "Output ONLY the JSON object, no markdown fences, no explanation."
        )
    return payload


def _normalize_anthropic_response(raw: dict[str, Any]) -> dict[str, Any]:
    """Convert Anthropic Messages API response to OpenAI-compatible format."""
    content_blocks = raw.get("content", [])
    text = "".join(
        block.get("text", "")
        for block in content_blocks
        if block.get("type") == "text"
    )
    usage = raw.get("usage", {})
    stop_reason = raw.get("stop_reason", "end_turn")
    finish_reason_map = {
        "end_turn": "stop",
        "max_tokens": "length",
        "stop_sequence": "stop",
    }
    normalized_usage: dict[str, Any] = {
        "prompt_tokens": usage.get("input_tokens"),
        "completion_tokens": usage.get("output_tokens"),
    }
    # Preserve cache token counts if present
    if "cache_read_input_tokens" in usage:
        normalized_usage["cache_read_input_tokens"] = usage["cache_read_input_tokens"]
    if "cache_creation_input_tokens" in usage:
        normalized_usage["cache_creation_input_tokens"] = usage["cache_creation_input_tokens"]
    return {
        "id": raw.get("id", ""),
        "model": raw.get("model"),
        "choices": [{
            "message": {"content": text},
            "finish_reason": finish_reason_map.get(stop_reason, stop_reason),
        }],
        "usage": normalized_usage,
    }


def _anthropic_transport(
    request_payload: dict[str, Any],
    *,
    request_timeout_seconds: float | None = None,
) -> dict[str, Any]:
    """Send request to Anthropic Messages API."""
    try:
        api_key = require_env("ANTHROPIC_API_KEY")
    except RuntimeError as exc:
        raise LLMCallError(f"{exc} for Anthropic transport") from exc

    encoded = json.dumps(request_payload).encode("utf-8")
    request = urllib.request.Request(
        ANTHROPIC_MESSAGES_URL,
        data=encoded,
        headers={
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
            "anthropic-beta": "prompt-caching-2024-07-31",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(
            request,
            timeout=_resolve_request_timeout(request_timeout_seconds),
        ) as response:  # noqa: S310
            body = response.read().decode("utf-8")
            return json.loads(body)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise LLMCallError(f"Anthropic HTTP error {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise LLMCallError(f"Anthropic request failed: {exc.reason}") from exc


def _build_gemini_payload(
    model: str,
    prompt: str,
    temperature: float,
    max_tokens: int | None,
    response_schema: type[BaseModel] | None,
    thinking_level: str | None = None,
) -> dict[str, Any]:
    """Build a Gemini generateContent request payload."""
    output_tokens = max_tokens or 16384
    if model in _GEMINI_MODELS_WITH_THINKING_LEVEL:
        output_tokens = min(output_tokens, _GEMINI_MAX_OUTPUT_TOKENS)
    generation_config: dict[str, Any] = {
        "maxOutputTokens": output_tokens,
    }
    if model not in _GEMINI_MODELS_WITHOUT_SAMPLING:
        generation_config["temperature"] = temperature
    if thinking_level is not None:
        if model not in _GEMINI_MODELS_WITH_THINKING_LEVEL:
            raise ValueError(f"thinking_level is not supported for Gemini model {model}")
        normalized_thinking_level = thinking_level.strip().lower()
        if normalized_thinking_level not in _GEMINI_THINKING_LEVELS:
            allowed = ", ".join(sorted(_GEMINI_THINKING_LEVELS))
            raise ValueError(f"thinking_level must be one of: {allowed}")
        generation_config["thinkingConfig"] = {
            "thinkingLevel": normalized_thinking_level,
        }
    if response_schema:
        generation_config["responseMimeType"] = "application/json"
        generation_config["responseSchema"] = _to_gemini_schema(
            response_schema.model_json_schema()
        )
    payload: dict[str, Any] = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": generation_config,
    }
    # Stash model name for _gemini_transport to build the URL.
    payload["_model"] = model
    return payload


def _to_gemini_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Convert a Pydantic JSON schema to Gemini's responseSchema format.

    Gemini uses a subset of OpenAPI 3.0 schema:
    - Type names are UPPERCASE: STRING, NUMBER, INTEGER, BOOLEAN, ARRAY, OBJECT
    - No $defs/$ref support — must be inlined
    - No title, default, additionalProperties fields
    """
    defs = schema.get("$defs", {})

    type_map = {
        "string": "STRING",
        "number": "NUMBER",
        "integer": "INTEGER",
        "boolean": "BOOLEAN",
        "array": "ARRAY",
        "object": "OBJECT",
        "null": "STRING",  # Gemini lacks null; approximate as STRING
    }

    def resolve(node: Any) -> Any:
        if isinstance(node, dict):
            # Resolve $ref
            ref = node.get("$ref")
            if ref and ref.startswith("#/$defs/"):
                def_name = ref[len("#/$defs/"):]
                if def_name in defs:
                    return resolve(defs[def_name])
                return {}

            # Handle anyOf (Pydantic uses this for Optional fields)
            if "anyOf" in node:
                variants = node["anyOf"]
                non_null = [v for v in variants if v.get("type") != "null"]
                if non_null:
                    return resolve(non_null[0])
                return {"type": "STRING"}

            result: dict[str, Any] = {}
            # Convert type
            if "type" in node:
                raw_type = node["type"]
                result["type"] = type_map.get(raw_type, raw_type.upper())

            # Copy supported fields
            if "description" in node:
                result["description"] = node["description"]
            if "enum" in node:
                result["enum"] = node["enum"]
            if "properties" in node:
                result["properties"] = {
                    k: resolve(v) for k, v in node["properties"].items()
                }
            if "required" in node:
                result["required"] = node["required"]
            if "items" in node:
                result["items"] = resolve(node["items"])

            return result

        if isinstance(node, list):
            return [resolve(item) for item in node]
        return node

    return resolve(schema)


def _gemini_transport(
    request_payload: dict[str, Any],
    *,
    request_timeout_seconds: float | None = None,
) -> dict[str, Any]:
    """Send request to Gemini generateContent API."""
    try:
        api_key = require_env("GEMINI_API_KEY")
    except RuntimeError as exc:
        raise LLMCallError(f"{exc} for Google transport") from exc

    model = request_payload.pop("_model")
    url = f"{GEMINI_BASE_URL}/{model}:generateContent?key={api_key}"
    encoded = json.dumps(request_payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=encoded,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(
            request,
            timeout=_resolve_request_timeout(request_timeout_seconds),
        ) as response:  # noqa: S310
            body = response.read().decode("utf-8")
            return json.loads(body)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise LLMCallError(f"Gemini HTTP error {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise LLMCallError(f"Gemini request failed: {exc.reason}") from exc


def _resolve_request_timeout(request_timeout_seconds: float | None) -> float:
    if request_timeout_seconds is None:
        return 300.0
    if request_timeout_seconds <= 0:
        raise ValueError("request_timeout_seconds must be > 0")
    return request_timeout_seconds


def _retry_delay_seconds(
    attempt: int,
    base_delay_seconds: float = 0.5,
    jitter_ratio: float = 0.25,
) -> float:
    """Exponential backoff with bounded additive jitter."""
    if attempt < 0:
        raise ValueError("attempt must be >= 0")
    if base_delay_seconds < 0:
        raise ValueError("base_delay_seconds must be >= 0")
    if jitter_ratio < 0:
        raise ValueError("jitter_ratio must be >= 0")

    base = base_delay_seconds * (2 ** attempt)
    jitter = random.uniform(0.0, base * jitter_ratio) if base > 0 else 0.0
    return base + jitter


def _breaker_state(provider: str) -> _CircuitBreakerState:
    state = _CIRCUIT_BREAKERS.get(provider)
    if state is None:
        state = _CircuitBreakerState()
        _CIRCUIT_BREAKERS[provider] = state
    return state


def _is_circuit_breaker_open(provider: str, *, now: float | None = None) -> bool:
    state = _breaker_state(provider)
    current_time = time.time() if now is None else now
    if state.opened_until <= current_time:
        if state.opened_until > 0:
            # Cooldown expired. Allow exactly one probe in half-open mode.
            state.opened_until = 0.0
            state.consecutive_failures = 0
            state.half_open = True
        return False
    return True


def _record_provider_transient_failure(provider: str, *, now: float | None = None) -> None:
    state = _breaker_state(provider)
    if state.half_open:
        # Probe failed -> reopen immediately.
        current_time = time.time() if now is None else now
        state.opened_until = current_time + _CIRCUIT_BREAKER_COOLDOWN_SECONDS
        state.consecutive_failures = _CIRCUIT_BREAKER_FAILURE_THRESHOLD
        state.half_open = False
        return
    state.consecutive_failures += 1
    if state.consecutive_failures < _CIRCUIT_BREAKER_FAILURE_THRESHOLD:
        return
    current_time = time.time() if now is None else now
    state.opened_until = current_time + _CIRCUIT_BREAKER_COOLDOWN_SECONDS
    state.half_open = False


def _record_provider_success(provider: str) -> None:
    state = _breaker_state(provider)
    state.consecutive_failures = 0
    state.opened_until = 0.0
    state.half_open = False


def _reset_circuit_breakers() -> None:
    _CIRCUIT_BREAKERS.clear()


def _is_transient_error(error: Exception) -> bool:
    message = str(error).lower()
    transient_tokens = (
        "rate limit",
        "overload",
        "overloaded",
        "overloaded_error",
        "capacity",
        "temporarily unavailable",
        "service unavailable",
        "timeout",
        "timed out",
        "connection reset",
        "connection aborted",
        "connection refused",
        "429",
        "503",
        "529",
    )
    return any(token in message for token in transient_tokens)
