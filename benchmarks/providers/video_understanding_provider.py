"""Custom promptfoo provider for the Story 030 video-understanding benchmark."""

from __future__ import annotations

import importlib
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import video_understanding_provider_anthropic as _anthropic
import video_understanding_provider_vision as _vision

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
SCRIPT_ROOT = REPO_ROOT / "benchmarks" / "scripts"
for import_root in (SRC_ROOT, SCRIPT_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from cine_forge.ai.model_identity import (  # noqa: E402
    validate_provider_response_identity,
)
from cine_forge.env import load_cine_forge_dotenv  # noqa: E402

load_cine_forge_dotenv(REPO_ROOT)

_llm = importlib.import_module("cine_forge.ai.llm")
estimate_cost_usd = _llm.estimate_cost_usd
_to_gemini_schema = _llm._to_gemini_schema
_to_openai_strict_schema = _llm._to_openai_strict_schema
require_env = importlib.import_module("cine_forge.env").require_env
VideoAnalysisPrediction = importlib.import_module("cine_forge.schemas").VideoAnalysisPrediction


def _gemini_response_schema() -> dict[str, Any]:
    schema = VideoAnalysisPrediction.model_json_schema()
    schema["required"] = list(schema.get("properties", {}))
    return _to_gemini_schema(schema)


_VIDEO_ANALYSIS_RESPONSE_SCHEMA = _gemini_response_schema()

_transport = importlib.import_module("video_understanding_transport")
_build_anthropic_payload = _transport.build_anthropic_payload
_build_gemini_payload = _transport.build_gemini_payload
_build_openai_payload = _transport.build_openai_payload
_build_user_text = _transport.build_user_text
_load_clip_packet = _transport.load_clip_packet
_resolve_clip_dir = _transport.resolve_clip_dir
_resolve_relative = _transport.resolve_relative

_provider_support = importlib.import_module("video_understanding_provider_support")
_build_promptfoo_response = _provider_support.build_promptfoo_response
_completion_tokens_for_cost = _provider_support.completion_tokens_for_cost
_prepare_subject_request = _provider_support.prepare_subject_request
_response_cost = _provider_support.response_cost

_subject_contract = importlib.import_module("final_render_provider_floor_subject_contract")
_final_render_prompt_version = _subject_contract.FINAL_RENDER_PROMPT_VERSION
_subject_contract_fingerprint = _subject_contract.subject_contract_fingerprint


OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"
XAI_CHAT_URL = "https://api.x.ai/v1/chat/completions"
XAI_RESPONSES_URL = "https://api.x.ai/v1/responses"
OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"
ANTHROPIC_MESSAGES_URL = "https://api.anthropic.com/v1/messages"
GEMINI_MODELS_URL = "https://generativelanguage.googleapis.com/v1beta/models"


class ProviderHTTPError(RuntimeError):
    """A provider failure whose safe response body can be durably retained."""

    def __init__(self, *, url: str, status_code: int, body: str) -> None:
        super().__init__(f"{url} returned HTTP {status_code}: {body}")
        self.url = url
        self.status_code = status_code
        self.body = body


def call_api(prompt: str, options: dict, context: dict) -> dict:
    """Promptfoo entry point for multimodal clip-packet analysis."""
    started = time.perf_counter()
    try:
        request = _prepare_subject_request(prompt, options, context)
        subject_contract_sha256 = _current_subject_contract(request)
        response = _dispatch_subject_request(request)
        latency_ms = round((time.perf_counter() - started) * 1000)
        return _build_promptfoo_response(
            request=request,
            response=response,
            latency_ms=latency_ms,
            cost_usd=_response_cost(request, response),
            subject_contract_sha256=subject_contract_sha256,
        )
    except Exception as exc:
        latency_ms = round((time.perf_counter() - started) * 1000)
        return {
            "output": "",
            "error": str(exc),
            "latencyMs": latency_ms,
        }


def _dispatch_subject_request(request: dict[str, Any]) -> dict[str, Any]:
    common = {
        "model": request["model"],
        "user_text": request["user_text"],
        "frames": request["packet"]["frames"],
        "max_tokens": request["max_tokens"],
    }
    provider = request["provider"]
    if provider == "openai":
        return _call_openai(**common, temperature=request["temperature"])
    if provider == "xai":
        if request["config"].get("transport") == "responses_strict":
            return _call_xai_responses_strict(
                model=request["model"],
                user_text=request["user_text"],
                frames=request["packet"]["frames"],
                max_tokens=request["max_tokens"],
                reasoning_effort=str(request["config"].get("reasoning_effort") or "low"),
            )
        return _call_xai(**common, temperature=request["temperature"])
    if provider == "anthropic":
        return _call_anthropic(
            **common,
            temperature=request["temperature"],
            effort=request["config"].get("reasoning_effort"),
            raw_output_path=_anthropic_raw_output_path(request),
        )
    if provider == "google":
        return _call_gemini(**common)
    if provider == "openrouter":
        return _call_openrouter_strict(
            **common,
            upstream_provider=str(request["config"].get("upstream_provider") or ""),
            raw_output_path=_openrouter_raw_output_path(request),
            timeout_seconds=float(request["config"].get("request_timeout_seconds") or 15),
        )
    raise RuntimeError(f"Unsupported provider: {provider}")


def _openrouter_raw_output_path(request: dict[str, Any]) -> Path:
    """Use ignored output storage for complete synthetic raw envelopes."""
    configured_dir = request["config"].get("raw_output_dir")
    if not isinstance(configured_dir, str) or not configured_dir.strip():
        raise RuntimeError("OpenRouter video evaluation requires raw_output_dir")
    target_dir = (REPO_ROOT / configured_dir).resolve()
    output_root = (REPO_ROOT / "output").resolve()
    if output_root not in target_dir.parents and target_dir != output_root:
        raise RuntimeError("OpenRouter raw_output_dir must stay under repo output/")
    return target_dir / f"{request['evaluation_id']}-raw-envelope.json"


def _anthropic_raw_output_path(request: dict[str, Any]) -> Path | None:
    configured_dir = request["config"].get("raw_output_dir")
    if not configured_dir:
        return None
    target_dir = (REPO_ROOT / str(configured_dir)).resolve()
    output_root = (REPO_ROOT / "output").resolve()
    if target_dir != output_root and output_root not in target_dir.parents:
        raise RuntimeError("Anthropic raw_output_dir must stay under repo output/")
    return target_dir / f"{request['evaluation_id']}-raw-envelope.json"


def _current_subject_contract(request: dict[str, Any]) -> str | None:
    if request["prompt_version"] != _final_render_prompt_version:
        return None
    fingerprint = _subject_contract_fingerprint(
        request["config"],
        repo_root=REPO_ROOT,
    )
    if fingerprint is None:
        raise RuntimeError("final-render subject request contract is incomplete")
    return fingerprint


def _call_openai(
    *,
    model: str,
    user_text: str,
    frames: list[dict[str, str]],
    max_tokens: int,
    temperature: float | None,
) -> dict[str, Any]:
    api_key = _require_env("OPENAI_API_KEY")
    payload = _build_openai_payload(
        model=model,
        user_text=user_text,
        frames=frames,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    response = _request_json(
        OPENAI_CHAT_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        body=payload,
    )
    choice = response["choices"][0]["message"]["content"]
    return _openai_compatible_result(
        response=response,
        output=choice,
        provider="openai",
        requested_model=model,
    )


def _call_xai(
    *,
    model: str,
    user_text: str,
    frames: list[dict[str, str]],
    max_tokens: int,
    temperature: float | None,
) -> dict[str, Any]:
    api_key = _require_env("XAI_API_KEY")
    payload = _build_openai_payload(
        model=model,
        user_text=user_text,
        frames=frames,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    response = _request_json(
        XAI_CHAT_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        body=payload,
    )
    choice = response["choices"][0]["message"]["content"]
    return _openai_compatible_result(
        response=response,
        output=choice,
        provider="xai",
        requested_model=model,
    )


def _call_xai_responses_strict(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return _vision.call_xai_responses_strict(globals(), *args, **kwargs)


def _call_anthropic(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return _anthropic.call_anthropic(globals(), *args, **kwargs)


def _anthropic_video_schema(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return _anthropic.anthropic_video_schema(globals(), *args, **kwargs)


def _call_gemini(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return _vision.call_gemini(globals(), *args, **kwargs)


def _call_openrouter_strict(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return _vision.call_openrouter_strict(globals(), *args, **kwargs)


def _write_raw_envelope(path: Path, envelope: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(envelope, indent=2, sort_keys=True), encoding="utf-8")


def _openai_compatible_result(
    *,
    response: dict[str, Any],
    output: str,
    provider: str,
    requested_model: str,
) -> dict[str, Any]:
    usage = response.get("usage")
    if not isinstance(usage, dict):
        raise ValueError("provider usage must be a mapping")
    identity = validate_provider_response_identity(
        provider=provider,
        requested_model=requested_model,
        returned_model=response.get("model"),
        request_id=response.get("id"),
        require_returned=True,
    )
    token_usage: dict[str, Any] = {
        "prompt": usage.get("prompt_tokens"),
        "completion": usage.get("completion_tokens"),
        "total": usage.get("total_tokens"),
    }
    details = usage.get("completion_tokens_details")
    if isinstance(details, dict) and "reasoning_tokens" in details:
        token_usage["reasoning_completion"] = details["reasoning_tokens"]
    return {
        "output": output,
        "token_usage": token_usage,
        "raw": {
            "id": identity.request_id,
            "model": identity.returned_model,
            "usage": usage,
        },
    }


def _request_json(
    url: str,
    *,
    headers: dict[str, str],
    body: dict[str, Any],
    timeout_seconds: float = 180,
) -> dict[str, Any]:
    data = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        payload = exc.read().decode("utf-8", errors="replace")
        raise ProviderHTTPError(url=url, status_code=exc.code, body=payload) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"{url} request failed: {exc}") from exc


def _request_xai_responses_json(payload: dict[str, Any]) -> tuple[dict[str, Any], str | None]:
    request = urllib.request.Request(
        XAI_RESPONSES_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {_require_env('XAI_API_KEY')}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:  # noqa: S310
            raw = json.loads(response.read().decode("utf-8"))
            x_zero_data_retention = response.headers.get("x-zero-data-retention")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"xAI Responses HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"xAI Responses request failed: {exc}") from exc
    if not isinstance(raw, dict):
        raise RuntimeError("xAI Responses response must be a mapping")
    return raw, x_zero_data_retention


def _token_count(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise RuntimeError(f"xAI Responses {name} must be a nonnegative integer")
    return value


def _require_env(name: str) -> str:
    return require_env(name)
