"""Frame-packet loading and provider payload builders for the visual benchmark."""

from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
from typing import Any


def resolve_clip_dir(
    *,
    base_path: Path,
    config: dict[str, Any],
    vars_data: dict[str, Any],
) -> Path:
    """Resolve the configured clip directory without reading candidate answers."""
    clip_dir_value = str(config.get("clip_dir", "")).strip()
    if clip_dir_value:
        return resolve_relative(base_path, clip_dir_value)

    root_value = str(config.get("clip_root", "")).strip()
    variant = str(config.get("candidate_variant", "")).strip()
    clip_id = str(vars_data.get("clip_id", "")).strip()
    if root_value and variant and clip_id:
        return (resolve_relative(base_path, root_value) / variant / clip_id).resolve()

    return resolve_relative(base_path, str(vars_data.get("clip_dir", "")))


def resolve_relative(base_path: Path, value: str) -> Path:
    if not value:
        raise RuntimeError("clip_dir test var is required")
    path = Path(value)
    return path if path.is_absolute() else (base_path / path).resolve()


def load_clip_packet(clip_dir: Path, *, max_frames: int) -> dict[str, Any]:
    """Load only the ordered JPEG samples and neutral transport metadata."""
    if max_frames < 1:
        raise RuntimeError("max_frames must be at least 1")
    meta_path = clip_dir / "meta.json"
    if not meta_path.exists():
        raise RuntimeError(f"Missing meta.json in {clip_dir}")
    meta_bytes = meta_path.read_bytes()
    meta = json.loads(meta_bytes)

    frame_dir = clip_dir / "frames"
    all_frames = sorted(frame_dir.glob("*.jpg"))
    if not all_frames:
        raise RuntimeError(f"No analysis frames found in {frame_dir}")

    packet_paths = all_frames[:max_frames]
    frame_hashes = [hashlib.sha256(path.read_bytes()).hexdigest() for path in packet_paths]
    declared_hashes = meta.get("sampled_frame_sha256")
    if declared_hashes is not None and declared_hashes[: len(frame_hashes)] != frame_hashes:
        raise RuntimeError(f"Frame hashes do not match meta.json in {clip_dir}")
    all_times = sample_times_seconds(meta, frame_count=len(all_frames))
    return {
        "meta": meta,
        "meta_sha256": hashlib.sha256(meta_bytes).hexdigest(),
        "frame_count": len(packet_paths),
        "frame_sha256": frame_hashes,
        "sample_times_seconds": all_times[: len(packet_paths)],
        "frames": [
            {
                "path": path,
                "mime_type": "image/jpeg",
                "base64": base64.b64encode(path.read_bytes()).decode("utf-8"),
            }
            for path in packet_paths
        ],
    }


def sample_times_seconds(meta: dict[str, Any], *, frame_count: int) -> list[float]:
    """Recover the generator's documented evenly-spaced sample timestamps."""
    if frame_count < 1:
        return []
    explicit = meta.get("sample_times_seconds")
    if isinstance(explicit, list) and len(explicit) >= frame_count:
        return [round(float(value), 3) for value in explicit[:frame_count]]
    duration = float(meta["duration_seconds"])
    fps_value = meta.get("fps")
    if fps_value:
        fps = float(fps_value)
        source_count = max(1, round(duration * fps))
        indexes = sorted(
            {0, source_count // 4, source_count // 2, (3 * source_count) // 4, source_count - 1}
        )
        if len(indexes) >= frame_count:
            return [round(index / fps, 3) for index in indexes[:frame_count]]
    if frame_count == 1:
        return [0.0]
    return [round(duration * index / (frame_count - 1), 3) for index in range(frame_count)]


def build_user_text(
    prompt: str,
    meta: dict[str, Any],
    *,
    evaluation_id: str,
    prompt_version: str,
    frame_count: int | None = None,
    sample_times: list[float] | None = None,
) -> str:
    """Build an answer-neutral brief for ordered JPEG frame comprehension."""
    del prompt_version  # Kept in the public signature for existing callers.
    if not evaluation_id.strip():
        raise RuntimeError("evaluation_id is required for an answer-neutral frame packet")
    count = frame_count if frame_count is not None else len(sample_times or [])
    times = sample_times or sample_times_seconds(meta, frame_count=count or 5)
    formatted_times = ", ".join(f"{value:g}" for value in times)
    return "\n".join(
        [
            prompt.strip(),
            "",
            "Ordered frame packet",
            f"- clip_id: {evaluation_id}",
            f"- duration_seconds: {meta['duration_seconds']}",
            f"- resolution: {meta['resolution']}",
            f"- frame_count: {count or len(times)}",
            f"- ordered_frame_indices: {list(range(count or len(times)))}",
            f"- ordered_sample_times_seconds: [{formatted_times}]",
            "- audio_available_to_model: false",
            "",
            (
                "Only the ordered JPEG samples are submitted. The source video's audio, "
                "transcript, and descriptive metadata are unavailable; do not infer them."
            ),
        ]
    )


def build_openai_payload(
    *,
    model: str,
    user_text: str,
    frames: list[dict[str, str]],
    max_tokens: int,
    temperature: float | None = None,
) -> dict[str, Any]:
    content: list[dict[str, Any]] = [{"type": "text", "text": user_text}]
    for index, frame in enumerate(frames):
        content.append({"type": "text", "text": f"frame_index: {index}"})
        content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{frame['mime_type']};base64,{frame['base64']}",
                    "detail": "high",
                },
            }
        )
    payload: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": content}],
        "max_completion_tokens": max_tokens,
        "response_format": {"type": "json_object"},
    }
    if temperature is not None:
        payload["temperature"] = temperature
    return payload


def build_anthropic_payload(
    *,
    model: str,
    user_text: str,
    frames: list[dict[str, str]],
    max_tokens: int,
    temperature: float | None = None,
) -> dict[str, Any]:
    content: list[dict[str, Any]] = [{"type": "text", "text": user_text}]
    for index, frame in enumerate(frames):
        content.append({"type": "text", "text": f"frame_index: {index}"})
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
    payload: dict[str, Any] = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": content}],
    }
    if temperature is not None:
        payload["temperature"] = temperature
    return payload


def build_gemini_payload(
    *,
    user_text: str,
    frames: list[dict[str, str]],
    max_tokens: int,
    temperature: float | None = None,
    response_schema: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build Gemini generateContent input without unsupported sampling controls."""
    del temperature  # Compatibility-only argument; Gemini 3.x requests omit it.
    parts: list[dict[str, Any]] = [{"text": user_text}]
    for index, frame in enumerate(frames):
        parts.append({"text": f"frame_index: {index}"})
        parts.append(
            {
                "inline_data": {
                    "mime_type": frame["mime_type"],
                    "data": frame["base64"],
                }
            }
        )
    generation_config: dict[str, Any] = {
        "maxOutputTokens": max_tokens,
        "responseMimeType": "application/json",
    }
    if response_schema is not None:
        generation_config["responseSchema"] = response_schema
    return {
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": generation_config,
    }
