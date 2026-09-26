"""Provider-specific direct transports for the ordered-frame evaluation.

Functions receive the caller namespace so test-injected HTTP and env boundaries
remain the same as the Promptfoo entrypoint.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any


def call_anthropic(
    scope: dict[str, Any],
    *,
    model: str,
    user_text: str,
    frames: list[dict[str, str]],
    max_tokens: int,
    temperature: float | None,
    effort: str | None = None,
    raw_output_path: Path | None = None,
) -> dict[str, Any]:
    _require_env = scope["_require_env"]
    _build_anthropic_payload = scope["_build_anthropic_payload"]
    _anthropic_video_schema = scope["_anthropic_video_schema"]
    _request_json = scope["_request_json"]
    ANTHROPIC_MESSAGES_URL = scope["ANTHROPIC_MESSAGES_URL"]
    ProviderHTTPError = scope["ProviderHTTPError"]
    _write_raw_envelope = scope["_write_raw_envelope"]
    api_key = _require_env("ANTHROPIC_API_KEY")
    payload = _build_anthropic_payload(
        model=model,
        user_text=user_text,
        frames=frames,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    if model == "claude-opus-5-5":
        if effort != "medium" or raw_output_path is None:
            raise RuntimeError("Opus 5.5 requires medium effort and durable raw output")
        payload.pop("temperature", None)
        payload["output_config"] = {
            "effort": effort,
            "format": {"type": "json_schema", "schema": _anthropic_video_schema()},
        }
    try:
        response = _request_json(
            ANTHROPIC_MESSAGES_URL,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            body=payload,
        )
    except ProviderHTTPError as exc:
        if raw_output_path is not None:
            _write_raw_envelope(
                raw_output_path,
                {
                    "request": payload,
                    "response_error": {"status": exc.status_code, "body": exc.body},
                },
            )
        raise
    if raw_output_path is not None:
        _write_raw_envelope(raw_output_path, response)
    return _normalize_anthropic_response(scope, response, model, raw_output_path)


def _normalize_anthropic_response(
    scope: dict[str, Any],
    response: dict[str, Any],
    model: str,
    raw_output_path: Path | None,
) -> dict[str, Any]:
    validate_provider_response_identity = scope["validate_provider_response_identity"]
    VideoAnalysisPrediction = scope["VideoAnalysisPrediction"]
    _token_count = scope["_token_count"]
    REPO_ROOT = scope["REPO_ROOT"]
    if model == "claude-opus-5-5" and response.get("stop_reason") != "end_turn":
        raise RuntimeError(f"Anthropic response did not finish: {response.get('stop_reason')!r}")
    blocks = response.get("content", [])
    output = "\n".join(block.get("text", "") for block in blocks if block.get("type") == "text")
    usage = response.get("usage", {})
    identity = validate_provider_response_identity(
        provider="anthropic",
        requested_model=model,
        returned_model=response.get("model"),
        request_id=response.get("id"),
        require_returned=True,
    )
    if model == "claude-opus-5-5":
        VideoAnalysisPrediction.model_validate_json(output)
        input_tokens = _token_count(usage.get("input_tokens"), "input_tokens")
        output_tokens = _token_count(usage.get("output_tokens"), "output_tokens")
        if any(
            usage.get(name, 0)
            for name in ("cache_creation_input_tokens", "cache_read_input_tokens")
        ):
            raise RuntimeError("Unexpected Anthropic cached input usage; billing needs review")
        raw_bytes = raw_output_path.read_bytes()
        reported_cost = (input_tokens * 4 + output_tokens * 20) / 1_000_000
    else:
        reported_cost = None
    return {
        "output": output,
        "token_usage": {
            "prompt": usage.get("input_tokens", 0),
            "completion": usage.get("output_tokens", 0),
            "total": usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
        },
        "raw": {
            "id": identity.request_id,
            "model": identity.returned_model,
            "usage": usage,
            **(
                {
                    "stop_reason": response.get("stop_reason"),
                    "raw_envelope_path": raw_output_path.resolve()
                    .relative_to(REPO_ROOT)
                    .as_posix(),
                    "raw_envelope_sha256": hashlib.sha256(raw_bytes).hexdigest(),
                    "raw_envelope_bytes": len(raw_bytes),
                }
                if model == "claude-opus-5-5"
                else {}
            ),
        },
        **(
            {"reported_cost_usd": reported_cost, "cost_estimated": True}
            if model == "claude-opus-5-5"
            else {}
        ),
    }


def anthropic_video_schema(
    scope: dict[str, Any],
) -> dict[str, Any]:
    """Provider-supported projection of the maintained exact-key prompt shape.

    The prompt requires every field even where the Pydantic model supplies a
    default. Unsupported numeric/string constraints remain in descriptions and
    are enforced by Pydantic after the complete envelope is retained.
    """
    VideoAnalysisPrediction = scope["VideoAnalysisPrediction"]
    original = VideoAnalysisPrediction.model_json_schema()

    def project(node: dict[str, Any]) -> dict[str, Any]:
        if "$ref" in node:
            return project(original["$defs"][node["$ref"].split("/")[-1]])
        supported = {
            "type",
            "enum",
            "properties",
            "items",
            "required",
            "additionalProperties",
            "description",
            "title",
            "default",
            "minimum",
            "maximum",
            "minLength",
            "$ref",
            "$defs",
        }
        unsupported = set(node) - supported
        if unsupported:
            raise RuntimeError(f"Unhandled video schema keys: {sorted(unsupported)}")
        kept = {key: node[key] for key in ("type", "enum", "description") if key in node}
        limits = [
            f"{key}={node[key]}" for key in ("minimum", "maximum", "minLength") if key in node
        ]
        if limits:
            kept["description"] = (
                kept.get("description", "") + " Local validation: " + ", ".join(limits)
            ).strip()
        if "properties" in node:
            kept["properties"] = {key: project(value) for key, value in node["properties"].items()}
            kept["required"] = list(node["properties"])
            kept["additionalProperties"] = False
        if "items" in node:
            kept["items"] = project(node["items"])
        return kept

    return project(original)
