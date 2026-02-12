"""Thin LLM call wrapper with retries and cost metadata."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any

from pydantic import BaseModel

# Input/output pricing in USD per 1M tokens.
MODEL_PRICING_PER_M_TOKEN: dict[str, tuple[float, float]] = {
    "gpt-4o": (5.0, 15.0),
    "gpt-4o-mini": (0.15, 0.6),
}

OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"


class LLMCallError(RuntimeError):
    """Terminal error for model invocation failures."""


def call_llm(
    prompt: str,
    model: str,
    response_schema: type[BaseModel] | None = None,
    max_retries: int = 2,
    max_tokens: int | None = None,
    temperature: float = 0.0,
    fail_on_truncation: bool = False,
    transport: Any | None = None,
) -> tuple[str | BaseModel, dict[str, Any]]:
    """Call an LLM and return text (or parsed schema) with call metadata."""
    if max_retries < 0:
        raise ValueError("max_retries must be >= 0")

    sender = transport or _openai_transport
    last_error: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            started = time.perf_counter()
            raw_response = sender(
                {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                    **({"max_completion_tokens": max_tokens} if max_tokens else {}),
                    **_response_format_payload(response_schema),
                }
            )
            latency = time.perf_counter() - started
            parsed, metadata = _parse_response(
                raw_response=raw_response,
                model=model,
                response_schema=response_schema,
                latency_seconds=latency,
            )
            if fail_on_truncation and metadata.get("finish_reason") == "length":
                raise LLMCallError("LLM output truncated due to max token limit")
            return parsed, metadata
        except LLMCallError:
            raise
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt >= max_retries or not _is_transient_error(exc):
                break
            # Simple linear backoff keeps retries deterministic for tests.
            time.sleep(0.2 * (attempt + 1))

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

    usage = raw_response.get("usage", {})
    input_tokens = int(usage.get("prompt_tokens", 0) or 0)
    output_tokens = int(usage.get("completion_tokens", 0) or 0)
    request_id = raw_response.get("id")
    finish_reason = choices[0].get("finish_reason")
    metadata = {
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "estimated_cost_usd": estimate_cost_usd(model, input_tokens, output_tokens),
        "latency_seconds": round(latency_seconds, 6),
        "request_id": request_id,
        "finish_reason": finish_reason,
    }

    if not response_schema:
        return text, metadata

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise LLMCallError("Structured response was not valid JSON") from exc
    return response_schema.model_validate(payload), metadata


def _openai_transport(request_payload: dict[str, Any]) -> dict[str, Any]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise LLMCallError("OPENAI_API_KEY is required for OpenAI transport")

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
        with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310
            body = response.read().decode("utf-8")
            return json.loads(body)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise LLMCallError(f"OpenAI HTTP error {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise LLMCallError(f"OpenAI request failed: {exc.reason}") from exc


def _is_transient_error(error: Exception) -> bool:
    message = str(error).lower()
    transient_tokens = ("rate", "timeout", "tempor", "503", "429", "connection reset")
    return any(token in message for token in transient_tokens)
