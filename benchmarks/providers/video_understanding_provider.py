"""Custom promptfoo provider for the Story 030 video-understanding benchmark."""

from __future__ import annotations

import base64
import importlib
import json
import sys
import time
import urllib.error
import urllib.parse
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


OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"
XAI_CHAT_URL = "https://api.x.ai/v1/chat/completions"
ANTHROPIC_MESSAGES_URL = "https://api.anthropic.com/v1/messages"
GEMINI_MODELS_URL = "https://generativelanguage.googleapis.com/v1beta/models"


def call_api(prompt: str, options: dict, context: dict) -> dict:
    """Promptfoo entry point for multimodal clip-packet analysis."""
    started = time.perf_counter()
    config = options.get("config", {})
    base_path = Path(config.get("basePath", Path.cwd()))
    prompt_version = config.get("prompt_version", "video-understanding-v1")
    frame_policy = config.get("frame_policy", "five_evenly_spaced_jpegs_v1")

    try:
        clip_dir = _resolve_clip_dir(
            base_path=base_path,
            config=config,
            vars_data=context.get("vars", {}),
        )
        packet = _load_clip_packet(clip_dir, max_frames=int(config.get("max_frames", 5)))
        user_text = _build_user_text(prompt, packet["meta"], prompt_version=prompt_version)
        model = str(config.get("model", "")).strip()
        provider = str(config.get("provider", "")).strip()
        temperature = float(config.get("temperature", 0.0))
        max_tokens = int(config.get("max_tokens", 1400))

        if not model or not provider:
            raise RuntimeError("provider config must include both 'provider' and 'model'")

        if provider == "openai":
            response = _call_openai(
                model=model,
                user_text=user_text,
                frames=packet["frames"],
                max_tokens=max_tokens,
                temperature=temperature,
            )
        elif provider == "xai":
            response = _call_xai(
                model=model,
                user_text=user_text,
                frames=packet["frames"],
                max_tokens=max_tokens,
                temperature=temperature,
            )
        elif provider == "anthropic":
            response = _call_anthropic(
                model=model,
                user_text=user_text,
                frames=packet["frames"],
                max_tokens=max_tokens,
                temperature=temperature,
            )
        elif provider == "google":
            response = _call_gemini(
                model=model,
                user_text=user_text,
                frames=packet["frames"],
                max_tokens=max_tokens,
                temperature=temperature,
            )
        else:
            raise RuntimeError(f"Unsupported provider: {provider}")
    except Exception as exc:
        latency_ms = round((time.perf_counter() - started) * 1000)
        return {
            "output": "",
            "error": str(exc),
            "latencyMs": latency_ms,
        }

    latency_ms = round((time.perf_counter() - started) * 1000)
    token_usage = response.get("token_usage", {})
    cost = None
    if token_usage.get("prompt") is not None and token_usage.get("completion") is not None:
        completion_for_cost = int(token_usage.get("completion", 0))
        if str(config.get("provider", "")).strip() == "xai":
            total_tokens = int(token_usage.get("total", 0))
            prompt_tokens = int(token_usage.get("prompt", 0))
            completion_for_cost = max(completion_for_cost, total_tokens - prompt_tokens)
        cost = estimate_cost_usd(
            model,
            int(token_usage.get("prompt", 0)),
            completion_for_cost,
        )

    return {
        "output": response["output"],
        "tokenUsage": {
            "total": int(token_usage.get("total", 0)),
            "prompt": int(token_usage.get("prompt", 0)),
            "completion": int(token_usage.get("completion", 0)),
        },
        "cost": cost,
        "latencyMs": latency_ms,
        "cached": False,
        "metadata": {
            "clip_id": packet["meta"]["clip_id"],
            "candidate_variant": packet["meta"].get("candidate_variant"),
            "prompt_version": prompt_version,
            "frame_policy": frame_policy,
            "model": model,
            "provider": provider,
        },
    }


def _resolve_clip_dir(
    *,
    base_path: Path,
    config: dict[str, Any],
    vars_data: dict[str, Any],
) -> Path:
    clip_dir_value = str(config.get("clip_dir", "")).strip()
    if clip_dir_value:
        return _resolve_relative(base_path, clip_dir_value)

    root_value = str(config.get("clip_root", "")).strip()
    variant = str(config.get("candidate_variant", "")).strip()
    clip_id = str(vars_data.get("clip_id", "")).strip()
    if root_value and variant and clip_id:
        return (_resolve_relative(base_path, root_value) / variant / clip_id).resolve()

    return _resolve_relative(base_path, str(vars_data.get("clip_dir", "")))


def _resolve_relative(base_path: Path, value: str) -> Path:
    if not value:
        raise RuntimeError("clip_dir test var is required")
    path = Path(value)
    return path if path.is_absolute() else (base_path / path).resolve()


def _load_clip_packet(clip_dir: Path, *, max_frames: int) -> dict[str, Any]:
    meta_path = clip_dir / "meta.json"
    if not meta_path.exists():
        raise RuntimeError(f"Missing meta.json in {clip_dir}")
    meta = json.loads(meta_path.read_text())

    frame_dir = clip_dir / "frames"
    frames = sorted(frame_dir.glob("*.jpg"))
    if not frames:
        raise RuntimeError(f"No analysis frames found in {frame_dir}")

    packet_frames = frames[:max_frames]
    return {
        "meta": meta,
        "frames": [
            {
                "path": path,
                "mime_type": "image/jpeg",
                "base64": base64.b64encode(path.read_bytes()).decode("utf-8"),
            }
            for path in packet_frames
        ],
    }


def _build_user_text(prompt: str, meta: dict[str, Any], *, prompt_version: str) -> str:
    transcript = meta.get("transcript") or "[none]"
    audio_description = meta.get("audio_description") or "[none]"
    tags = ", ".join(meta.get("tags", [])) or "[none]"
    return "\n".join(
        [
            prompt.strip(),
            "",
            "Clip packet",
            f"- prompt_version: {prompt_version}",
            f"- clip_id: {meta['clip_id']}",
            f"- title: {meta['title']}",
            f"- source_type: {meta.get('source_type', 'unknown')}",
            f"- duration_seconds: {meta['duration_seconds']}",
            f"- resolution: {meta['resolution']}",
            f"- has_audio: {meta['has_audio']}",
            f"- tags: {tags}",
            f"- transcript: {transcript}",
            f"- audio_description: {audio_description}",
            "",
            (
                "Use the images plus the clip packet above. "
                "Do not invent details not grounded in them."
            ),
        ]
    )


def _build_openai_payload(
    *,
    model: str,
    user_text: str,
    frames: list[dict[str, str]],
    max_tokens: int,
    temperature: float,
) -> dict[str, Any]:
    content = [{"type": "text", "text": user_text}]
    for frame in frames:
        content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{frame['mime_type']};base64,{frame['base64']}",
                    "detail": "high",
                },
            }
        )
    return {
        "model": model,
        "messages": [{"role": "user", "content": content}],
        "temperature": temperature,
        "max_completion_tokens": max_tokens,
        "response_format": {"type": "json_object"},
    }


def _build_anthropic_payload(
    *,
    model: str,
    user_text: str,
    frames: list[dict[str, str]],
    max_tokens: int,
    temperature: float,
) -> dict[str, Any]:
    content: list[dict[str, Any]] = [{"type": "text", "text": user_text}]
    for frame in frames:
        content.append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": frame["mime_type"],
                    "data": frame["base64"],
                },
            }
        )
    return {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [{"role": "user", "content": content}],
    }


def _build_gemini_payload(
    *,
    user_text: str,
    frames: list[dict[str, str]],
    max_tokens: int,
    temperature: float,
) -> dict[str, Any]:
    parts: list[dict[str, Any]] = [{"text": user_text}]
    for frame in frames:
        parts.append(
            {
                "inline_data": {
                    "mime_type": frame["mime_type"],
                    "data": frame["base64"],
                }
            }
        )
    return {
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
            "responseMimeType": "application/json",
        },
    }


def _call_openai(
    *,
    model: str,
    user_text: str,
    frames: list[dict[str, str]],
    max_tokens: int,
    temperature: float,
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
    usage = response.get("usage", {})
    return {
        "output": choice,
        "token_usage": {
            "prompt": usage.get("prompt_tokens", 0),
            "completion": usage.get("completion_tokens", 0),
            "total": usage.get("total_tokens", 0),
        },
    }


def _call_xai(
    *,
    model: str,
    user_text: str,
    frames: list[dict[str, str]],
    max_tokens: int,
    temperature: float,
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
    usage = response.get("usage", {})
    return {
        "output": choice,
        "token_usage": {
            "prompt": usage.get("prompt_tokens", 0),
            "completion": usage.get("completion_tokens", 0),
            "total": usage.get("total_tokens", 0),
        },
    }


def _call_anthropic(
    *,
    model: str,
    user_text: str,
    frames: list[dict[str, str]],
    max_tokens: int,
    temperature: float,
) -> dict[str, Any]:
    api_key = _require_env("ANTHROPIC_API_KEY")
    payload = _build_anthropic_payload(
        model=model,
        user_text=user_text,
        frames=frames,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    response = _request_json(
        ANTHROPIC_MESSAGES_URL,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        body=payload,
    )
    blocks = response.get("content", [])
    output = "\n".join(block.get("text", "") for block in blocks if block.get("type") == "text")
    usage = response.get("usage", {})
    return {
        "output": output,
        "token_usage": {
            "prompt": usage.get("input_tokens", 0),
            "completion": usage.get("output_tokens", 0),
            "total": usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
        },
    }


def _call_gemini(
    *,
    model: str,
    user_text: str,
    frames: list[dict[str, str]],
    max_tokens: int,
    temperature: float,
) -> dict[str, Any]:
    api_key = _require_env("GEMINI_API_KEY")
    payload = _build_gemini_payload(
        user_text=user_text,
        frames=frames,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    url = f"{GEMINI_MODELS_URL}/{urllib.parse.quote(model, safe='')}:generateContent?key={api_key}"
    response = _request_json(
        url,
        headers={"Content-Type": "application/json"},
        body=payload,
    )
    candidates = response.get("candidates", [])
    parts = candidates[0].get("content", {}).get("parts", []) if candidates else []
    output = "\n".join(part.get("text", "") for part in parts if "text" in part)
    usage = response.get("usageMetadata", {})
    return {
        "output": output,
        "token_usage": {
            "prompt": usage.get("promptTokenCount", 0),
            "completion": usage.get("candidatesTokenCount", 0),
            "total": usage.get("totalTokenCount", 0),
        },
    }


def _request_json(url: str, *, headers: dict[str, str], body: dict[str, Any]) -> dict[str, Any]:
    data = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        payload = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{url} returned HTTP {exc.code}: {payload}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"{url} request failed: {exc}") from exc


def _require_env(name: str) -> str:
    return require_env(name)
