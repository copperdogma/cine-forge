"""Custom promptfoo provider for storyboard-sequence quality analysis."""

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
ANTHROPIC_MESSAGES_URL = "https://api.anthropic.com/v1/messages"
GEMINI_MODELS_URL = "https://generativelanguage.googleapis.com/v1beta/models"


def call_api(prompt: str, options: dict, context: dict) -> dict:
    """Promptfoo entry point for storyboard-sequence packet analysis."""
    started = time.perf_counter()
    config = options.get("config", {})
    base_path = Path(config.get("basePath", Path.cwd()))
    prompt_version = config.get("prompt_version", "storyboard-understanding-v1")

    try:
        sequence_dir = _resolve_sequence_dir(
            base_path=base_path,
            config=config,
            vars_data=context.get("vars", {}),
        )
        packet = _load_storyboard_packet(
            sequence_dir=sequence_dir,
            max_frames=int(config.get("max_frames", 6)),
            max_references=int(config.get("max_references", 4)),
        )
        user_text = _build_user_text(prompt, packet["meta"], prompt_version=prompt_version)
        model = str(config.get("model", "")).strip()
        provider = str(config.get("provider", "")).strip()
        temperature = float(config.get("temperature", 0.0))
        max_tokens = int(config.get("max_tokens", 1400))

        if not model or not provider:
            raise RuntimeError("provider config must include both 'provider' and 'model'")

        images = packet["frames"] + packet["references"]
        if provider == "openai":
            response = _call_openai(
                model=model,
                user_text=user_text,
                images=images,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        elif provider == "anthropic":
            response = _call_anthropic(
                model=model,
                user_text=user_text,
                images=images,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        elif provider == "google":
            response = _call_gemini(
                model=model,
                user_text=user_text,
                images=images,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        else:
            raise RuntimeError(f"Unsupported provider: {provider}")
    except Exception as exc:
        latency_ms = round((time.perf_counter() - started) * 1000)
        return {"output": "", "error": str(exc), "latencyMs": latency_ms}

    latency_ms = round((time.perf_counter() - started) * 1000)
    token_usage = response.get("token_usage", {})
    cost = None
    if token_usage.get("prompt") is not None and token_usage.get("completion") is not None:
        cost = estimate_cost_usd(
            model,
            int(token_usage.get("prompt", 0)),
            int(token_usage.get("completion", 0)),
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
            "storyboard_id": packet["meta"]["storyboard_id"],
            "candidate_variant": packet["meta"].get("candidate_variant"),
            "prompt_version": prompt_version,
            "model": model,
            "provider": provider,
        },
    }


def _resolve_sequence_dir(
    *,
    base_path: Path,
    config: dict[str, Any],
    vars_data: dict[str, Any],
) -> Path:
    sequence_root = str(config.get("sequence_root", "")).strip()
    candidate_variant = str(config.get("candidate_variant", "")).strip()
    storyboard_id = str(vars_data.get("storyboard_id", "")).strip()
    if sequence_root and candidate_variant and storyboard_id:
        return (
            _resolve_relative(base_path, sequence_root)
            / candidate_variant
            / storyboard_id
        ).resolve()
    return _resolve_relative(base_path, str(vars_data.get("sequence_dir", "")))


def _resolve_relative(base_path: Path, value: str) -> Path:
    if not value:
        raise RuntimeError("sequence_dir test var is required")
    path = Path(value)
    return path if path.is_absolute() else (base_path / path).resolve()


def _load_storyboard_packet(
    *,
    sequence_dir: Path,
    max_frames: int,
    max_references: int,
) -> dict[str, Any]:
    meta_path = sequence_dir / "meta.json"
    if not meta_path.exists():
        raise RuntimeError(f"Missing meta.json in {sequence_dir}")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))

    frame_dir = sequence_dir / "frames"
    frames = sorted(frame_dir.glob("*.jpg"))
    if not frames:
        raise RuntimeError(f"No storyboard frames found in {frame_dir}")

    reference_dir = sequence_dir / "references"
    references = sorted(reference_dir.glob("*.jpg")) if reference_dir.exists() else []
    selected_frames = _select_evenly(frames, max_frames)
    return {
        "meta": meta,
        "frames": [_encode_image(path, kind="storyboard_frame") for path in selected_frames],
        "references": [
            _encode_image(path, kind="reference_image")
            for path in references[:max_references]
        ],
    }


def _select_evenly(paths: list[Path], limit: int) -> list[Path]:
    if limit <= 0:
        return []
    if len(paths) <= limit:
        return list(paths)
    if limit == 1:
        return [paths[0]]
    indexes = {
        round(position * (len(paths) - 1) / (limit - 1))
        for position in range(limit)
    }
    return [paths[index] for index in sorted(indexes)]


def _encode_image(path: Path, *, kind: str) -> dict[str, str]:
    return {
        "path": str(path),
        "label": path.stem,
        "kind": kind,
        "mime_type": "image/jpeg",
        "base64": base64.b64encode(path.read_bytes()).decode("utf-8"),
    }


def _build_user_text(prompt: str, meta: dict[str, Any], *, prompt_version: str) -> str:
    scene_ids = ", ".join(meta.get("scene_ids", [])) or "[unknown]"
    recurring_characters = ", ".join(meta.get("recurring_character_names", [])) or "[none]"
    reference_labels = ", ".join(
        item.get("label", "")
        for item in meta.get("reference_images", [])
        if isinstance(item, dict) and item.get("label")
    ) or "[none]"
    return "\n".join(
        [
            prompt.strip(),
            "",
            "Storyboard packet",
            f"- prompt_version: {prompt_version}",
            f"- storyboard_id: {meta['storyboard_id']}",
            f"- title: {meta['title']}",
            f"- scene_ids: {scene_ids}",
            f"- frame_count: {meta['frame_count']}",
            f"- recurring_character_names: {recurring_characters}",
            f"- available_reference_image_count: {meta['available_reference_image_count']}",
            f"- prompt_reference_frame_count: {meta['prompt_reference_frame_count']}",
            f"- direct_reference_input_count: {meta['direct_reference_input_count']}",
            f"- reference_transport_supported: {meta['reference_transport_supported']}",
            f"- reference_labels: {reference_labels}",
            "",
            (
                "Images are provided as labeled frame/reference pairs below. Use those "
                "labels as frame_id values in evidence."
            ),
        ]
    )


def _build_openai_payload(
    *,
    model: str,
    user_text: str,
    images: list[dict[str, str]],
    max_tokens: int,
    temperature: float,
) -> dict[str, Any]:
    content = [{"type": "text", "text": user_text}]
    for image in images:
        content.append({"type": "text", "text": _image_label_text(image)})
        content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{image['mime_type']};base64,{image['base64']}",
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
    images: list[dict[str, str]],
    max_tokens: int,
    temperature: float,
) -> dict[str, Any]:
    content: list[dict[str, Any]] = [{"type": "text", "text": user_text}]
    for image in images:
        content.append({"type": "text", "text": _image_label_text(image)})
        content.append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": image["mime_type"],
                    "data": image["base64"],
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
    images: list[dict[str, str]],
    max_tokens: int,
    temperature: float,
) -> dict[str, Any]:
    parts: list[dict[str, Any]] = [{"text": user_text}]
    for image in images:
        parts.append({"text": _image_label_text(image)})
        parts.append(
            {
                "inlineData": {
                    "mimeType": image["mime_type"],
                    "data": image["base64"],
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


def _image_label_text(image: dict[str, str]) -> str:
    kind = image.get("kind") or "image"
    label = image.get("label") or Path(image.get("path", "image")).stem
    if kind == "storyboard_frame":
        return f"Generated storyboard frame: {label}"
    if kind == "reference_image":
        return f"Reference image: {label}"
    return f"Image: {label}"


def _call_openai(
    *,
    model: str,
    user_text: str,
    images: list[dict[str, str]],
    max_tokens: int,
    temperature: float,
) -> dict[str, Any]:
    api_key = require_env("OPENAI_API_KEY")
    payload = _build_openai_payload(
        model=model,
        user_text=user_text,
        images=images,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    request = urllib.request.Request(
        OPENAI_CHAT_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            raw = json.loads(response.read())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI API returned HTTP {exc.code}: {body}") from exc
    message = raw["choices"][0]["message"]["content"]
    usage = raw.get("usage", {})
    return {
        "output": message,
        "token_usage": {
            "prompt": usage.get("prompt_tokens"),
            "completion": usage.get("completion_tokens"),
            "total": usage.get("total_tokens"),
        },
    }


def _call_anthropic(
    *,
    model: str,
    user_text: str,
    images: list[dict[str, str]],
    max_tokens: int,
    temperature: float,
) -> dict[str, Any]:
    api_key = require_env("ANTHROPIC_API_KEY")
    payload = _build_anthropic_payload(
        model=model,
        user_text=user_text,
        images=images,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    request = urllib.request.Request(
        ANTHROPIC_MESSAGES_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            raw = json.loads(response.read())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Anthropic API returned HTTP {exc.code}: {body}") from exc
    content = raw.get("content", [])
    text = "".join(part.get("text", "") for part in content if part.get("type") == "text")
    usage = raw.get("usage", {})
    return {
        "output": text,
        "token_usage": {
            "prompt": usage.get("input_tokens"),
            "completion": usage.get("output_tokens"),
            "total": (usage.get("input_tokens") or 0) + (usage.get("output_tokens") or 0),
        },
    }


def _call_gemini(
    *,
    model: str,
    user_text: str,
    images: list[dict[str, str]],
    max_tokens: int,
    temperature: float,
) -> dict[str, Any]:
    api_key = require_env("GEMINI_API_KEY")
    payload = _build_gemini_payload(
        user_text=user_text,
        images=images,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    url = f"{GEMINI_MODELS_URL}/{urllib.parse.quote(model)}:generateContent?key={api_key}"
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            raw = json.loads(response.read())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Gemini API returned HTTP {exc.code}: {body}") from exc
    candidate = raw.get("candidates", [{}])[0]
    parts = candidate.get("content", {}).get("parts", [])
    text = "".join(part.get("text", "") for part in parts if part.get("text"))
    usage = raw.get("usageMetadata", {})
    return {
        "output": text,
        "token_usage": {
            "prompt": usage.get("promptTokenCount"),
            "completion": usage.get("candidatesTokenCount"),
            "total": usage.get("totalTokenCount"),
        },
    }
