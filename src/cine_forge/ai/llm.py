"""Thin LLM call wrapper with retries and cost metadata."""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from pydantic import BaseModel

# Input/output pricing in USD per 1M tokens.
MODEL_PRICING_PER_M_TOKEN: dict[str, tuple[float, float]] = {
    # OpenAI
    "gpt-4o": (5.0, 15.0),
    "gpt-4o-mini": (0.15, 0.6),
    "gpt-4.1": (2.0, 8.0),
    "gpt-4.1-mini": (0.40, 1.60),
    "gpt-5.2": (2.0, 8.0),
    # Anthropic
    "claude-sonnet-4-5": (3.0, 15.0),
    "claude-sonnet-4-5-20250929": (3.0, 15.0),
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-opus-4-6": (15.0, 75.0),
    "claude-haiku-4-5-20251001": (0.80, 4.0),
    # Google
    "gemini-2.5-flash-lite": (0.0, 0.0),  # Free tier
    "gemini-2.5-flash": (0.15, 0.60),
    "gemini-2.5-pro": (1.25, 10.0),
    "gemini-3-flash-preview": (0.15, 0.60),
}

OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"
ANTHROPIC_MESSAGES_URL = "https://api.anthropic.com/v1/messages"
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

# Provider identifiers used by _parse_provider().
PROVIDER_OPENAI = "openai"
PROVIDER_ANTHROPIC = "anthropic"
PROVIDER_GOOGLE = "google"


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
    if model == "fixture":
        started = time.perf_counter()
        parsed = _fixture_response(prompt=prompt, response_schema=response_schema)
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
        sender = _anthropic_transport
        normalizer = _normalize_anthropic_response
    elif provider == PROVIDER_GOOGLE:
        sender = _gemini_transport
        normalizer = _normalize_gemini_response
    else:
        sender = _openai_transport
        normalizer = None  # OpenAI is the canonical format

    last_error: Exception | None = None
    active_max_tokens = max_tokens
    active_temp = temperature

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
                )
            elif provider == PROVIDER_GOOGLE and transport is None:
                payload = _build_gemini_payload(
                    model=bare_model,
                    prompt=prompt,
                    temperature=active_temp,
                    max_tokens=active_max_tokens,
                    response_schema=response_schema,
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
            )
            if fail_on_truncation and metadata.get("finish_reason") == "length":
                raise LLMCallError("LLM output truncated due to max token limit")
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
            if attempt < max_retries and retryable:
                # Adjust params for retry
                if is_truncation and active_max_tokens:
                    active_max_tokens = int(active_max_tokens * 1.5)
                if is_json_error:
                    # SOTA models sometimes benefit from a tiny bit of heat on a retry
                    active_temp = min(active_temp + 0.1, 0.7)
                
                time.sleep(0.5 * (attempt + 1))
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

    # Fail early on truncated structured output — retries can bump max_tokens.
    if finish_reason == "length":
        raise LLMCallError(
            "LLM output truncated due to max token limit"
        )

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
        with urllib.request.urlopen(request, timeout=300) as response:  # noqa: S310
            body = response.read().decode("utf-8")
            return json.loads(body)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise LLMCallError(f"OpenAI HTTP error {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise LLMCallError(f"OpenAI request failed: {exc.reason}") from exc


def _parse_provider(model: str) -> tuple[str, str]:
    """Parse provider prefix from model string, falling back to auto-detection.

    Accepted formats:
        "anthropic:claude-sonnet-4-6"  -> ("anthropic", "claude-sonnet-4-6")
        "google:gemini-2.5-pro"        -> ("google", "gemini-2.5-pro")
        "openai:gpt-4.1"              -> ("openai", "gpt-4.1")
        "claude-sonnet-4-6"           -> ("anthropic", "claude-sonnet-4-6")
        "gemini-2.5-pro"              -> ("google", "gemini-2.5-pro")
        "gpt-4.1"                     -> ("openai", "gpt-4.1")
    """
    if ":" in model:
        provider, bare_model = model.split(":", 1)
        provider = provider.lower()
        if provider in (PROVIDER_OPENAI, PROVIDER_ANTHROPIC, PROVIDER_GOOGLE):
            return provider, bare_model
    # Auto-detect from model name
    if model.startswith("claude-"):
        return PROVIDER_ANTHROPIC, model
    if model.startswith("gemini-"):
        return PROVIDER_GOOGLE, model
    return PROVIDER_OPENAI, model


def _build_anthropic_payload(
    model: str,
    prompt: str,
    temperature: float,
    max_tokens: int | None,
    response_schema: type[BaseModel] | None,
) -> dict[str, Any]:
    """Build an Anthropic Messages API request payload."""
    payload: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens or 16384,
    }
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
    return {
        "id": raw.get("id", ""),
        "choices": [{
            "message": {"content": text},
            "finish_reason": finish_reason_map.get(stop_reason, stop_reason),
        }],
        "usage": {
            "prompt_tokens": usage.get("input_tokens", 0),
            "completion_tokens": usage.get("output_tokens", 0),
        },
    }


def _anthropic_transport(request_payload: dict[str, Any]) -> dict[str, Any]:
    """Send request to Anthropic Messages API."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise LLMCallError("ANTHROPIC_API_KEY is required for Anthropic transport")

    encoded = json.dumps(request_payload).encode("utf-8")
    request = urllib.request.Request(
        ANTHROPIC_MESSAGES_URL,
        data=encoded,
        headers={
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=300) as response:  # noqa: S310
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
) -> dict[str, Any]:
    """Build a Gemini generateContent request payload."""
    generation_config: dict[str, Any] = {
        "temperature": temperature,
        "max_output_tokens": max_tokens or 16384,
    }
    if response_schema:
        generation_config["response_mime_type"] = "application/json"
        generation_config["response_schema"] = _to_gemini_schema(
            response_schema.model_json_schema()
        )
    payload: dict[str, Any] = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generation_config": generation_config,
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


def _normalize_gemini_response(raw: dict[str, Any]) -> dict[str, Any]:
    """Convert Gemini generateContent response to OpenAI-compatible format."""
    candidates = raw.get("candidates", [])
    if not candidates:
        raise LLMCallError("Gemini response missing candidates")

    candidate = candidates[0]
    parts = candidate.get("content", {}).get("parts", [])
    text = "".join(part.get("text", "") for part in parts)

    finish_reason_raw = candidate.get("finishReason", "STOP")
    finish_reason_map = {
        "STOP": "stop",
        "MAX_TOKENS": "length",
        "SAFETY": "content_filter",
        "RECITATION": "content_filter",
        "OTHER": "stop",
    }

    usage = raw.get("usageMetadata", {})
    return {
        "id": "",
        "choices": [{
            "message": {"content": text},
            "finish_reason": finish_reason_map.get(finish_reason_raw, "stop"),
        }],
        "usage": {
            "prompt_tokens": usage.get("promptTokenCount", 0),
            "completion_tokens": usage.get("candidatesTokenCount", 0),
        },
    }


def _gemini_transport(request_payload: dict[str, Any]) -> dict[str, Any]:
    """Send request to Gemini generateContent API."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise LLMCallError("GEMINI_API_KEY is required for Google transport")

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
        with urllib.request.urlopen(request, timeout=300) as response:  # noqa: S310
            body = response.read().decode("utf-8")
            return json.loads(body)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise LLMCallError(f"Gemini HTTP error {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise LLMCallError(f"Gemini request failed: {exc.reason}") from exc


def _is_transient_error(error: Exception) -> bool:
    message = str(error).lower()
    transient_tokens = ("rate", "timeout", "tempor", "503", "429", "connection reset")
    return any(token in message for token in transient_tokens)


def _fixture_response(
    prompt: str,
    response_schema: type[BaseModel] | None,
) -> str | BaseModel:
    root_path = os.getenv("CINE_FORGE_MOCK_FIXTURE_DIR")
    if not root_path:
        raise LLMCallError("CINE_FORGE_MOCK_FIXTURE_DIR is required for model='fixture'")
    fixture_root = Path(root_path)
    lowered_prompt = prompt.lower()

    if response_schema is None:
        if "search/replace blocks" in lowered_prompt:
            return ""
        screenplay_fixture = fixture_root / "normalization_screenplay_cleanup.txt"
        prose_fixture = fixture_root / "normalization_prose_conversion.txt"
        source_path = (
            screenplay_fixture
            if "source format: screenplay" in lowered_prompt
            else prose_fixture
        )
        return source_path.read_text(encoding="utf-8")

    schema_name = response_schema.__name__
    if schema_name == "_MetadataEnvelope":
        source_format = "screenplay" if "source format: screenplay" in lowered_prompt else "prose"
        payload = {
            "source_format": source_format,
            "strategy": (
                "passthrough_cleanup"
                if "strategy: passthrough_cleanup" in lowered_prompt
                else "full_conversion"
            ),
            "inventions": [],
            "assumptions": [],
            "overall_confidence": 0.92,
            "rationale": "Fixture-backed metadata response.",
        }
        return response_schema.model_validate(payload)

    if schema_name in {"QAResult", "QARepairPlan"}:
        scene_match = re.search(r"scene_[0-9]{3}", lowered_prompt)
        scene_id = scene_match.group(0) if scene_match else None
        if scene_id:
            qa_source = fixture_root / "qa" / f"{scene_id}_qa.json"
            scene_source = fixture_root / "scenes" / f"{scene_id}.json"
        else:
            qa_source = fixture_root / "normalization_qa.json"
            scene_source = None

        if not qa_source.exists():
            qa_source = fixture_root / "normalization_qa.json"
        qa_payload = json.loads(qa_source.read_text(encoding="utf-8"))
        scene_payload = (
            json.loads(scene_source.read_text(encoding="utf-8"))
            if scene_source and scene_source.exists()
            else {}
        )
        issues = [
            {
                "severity": issue.get("severity", "note"),
                "description": issue.get("description", "fixture note"),
                "location": issue.get("location", "unknown"),
            }
            for issue in qa_payload.get("issues", [])
        ]
        result_payload = {
            "passed": bool(qa_payload.get("passed", True)),
            "confidence": float(qa_payload.get("confidence", 0.95)),
            "issues": issues,
            "summary": str(
                scene_payload.get("note")
                or qa_payload.get("summary")
                or "Fixture QA result"
            ),
        }
        if schema_name == "QAResult":
            return response_schema.model_validate(result_payload)
        return response_schema.model_validate({"qa_result": result_payload, "edits": []})

    if schema_name == "_BoundaryValidation":
        return response_schema.model_validate(
            {
                "is_sensible": True,
                "confidence": 0.8,
                "rationale": "Fixture boundary validation accepted chunk boundary.",
            }
        )

    if schema_name == "_EnrichmentEnvelope":
        return response_schema.model_validate(
            {
                "narrative_beats": [],
                "tone_mood": "neutral",
                "tone_shifts": [],
                "heading": None,
                "location": None,
                "time_of_day": None,
                "int_ext": None,
                "characters_present": None,
            }
        )

    if schema_name == "_DetectedConfigEnvelope":
        config_fixture = fixture_root / "project_config_autodetect.json"
        raw = json.loads(config_fixture.read_text(encoding="utf-8"))
        payload = {
            "title": {"value": raw["title"], "confidence": 0.9, "rationale": "Fixture title"},
            "format": {"value": raw["format"], "confidence": 0.9, "rationale": "Fixture format"},
            "genre": {"value": raw["genre"], "confidence": 0.86, "rationale": "Fixture genre"},
            "tone": {"value": raw["tone"], "confidence": 0.84, "rationale": "Fixture tone"},
            "estimated_duration_minutes": {
                "value": raw["estimated_duration_minutes"],
                "confidence": 0.85,
                "rationale": "Fixture runtime estimate",
            },
            "primary_characters": {
                "value": raw["primary_characters"],
                "confidence": 0.85,
                "rationale": "Fixture primary characters",
            },
            "supporting_characters": {
                "value": raw["supporting_characters"],
                "confidence": 0.8,
                "rationale": "Fixture supporting characters",
            },
            "location_count": {
                "value": raw["location_count"],
                "confidence": 0.9,
                "rationale": "Fixture location count",
            },
            "locations_summary": {
                "value": raw["locations_summary"],
                "confidence": 0.9,
                "rationale": "Fixture locations summary",
            },
            "target_audience": {
                "value": raw["target_audience"],
                "confidence": 0.7,
                "rationale": "Fixture audience",
            },
        }
        return response_schema.model_validate(payload)

    raise LLMCallError(f"Unsupported fixture response schema: {schema_name}")
