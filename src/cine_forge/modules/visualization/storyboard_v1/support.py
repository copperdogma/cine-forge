"""Shared helpers for storyboard generation."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from cine_forge.artifacts import ArtifactStore
from cine_forge.schemas import ArtifactRef, ShotPlan, TrackEntry

DEFAULT_IMAGE_MODEL = "imagen-4.0-generate-001"
DEFAULT_STYLE = "sketch"
STYLE_PROMPTS: dict[str, str] = {
    "sketch": (
        "Render as a rough black-and-white production storyboard sketch with fast pencil energy,"
        " readable silhouettes, clear staging, and low-detail backgrounds."
    ),
    "clean_line": (
        "Render as clean storyboard line art with crisp outlines, restrained shading, and"
        " strong composition clarity."
    ),
    "animation_style": (
        "Render as simplified animation storyboard art with expressive posing, readable"
        " silhouettes, and stylized but production-useful clarity."
    ),
    "abstract_color_coded": (
        "Render as abstract color-coded storyboard art using simple shapes and controlled"
        " color blocks to clarify blocking and frame balance."
    ),
    "photoreal": (
        "Render as a cinematic photoreal concept frame while preserving storyboard-style"
        " composition discipline and shot readability."
    ),
}
OPENAI_QUALITY_BY_STYLE = {
    "sketch": "low",
    "clean_line": "low",
    "animation_style": "low",
    "abstract_color_coded": "low",
    "photoreal": "high",
}
ALLOWED_STYLES = set(STYLE_PROMPTS)
_SLUG_RE = re.compile(r"[^a-z0-9]+")


def openai_quality_for_style(style: str) -> str:
    return OPENAI_QUALITY_BY_STYLE.get(style, "low")


def scene_map(payload: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(payload, list):
        return {}
    mapped: dict[str, dict[str, Any]] = {}
    for item in payload:
        if not isinstance(item, dict):
            continue
        scene_id = item.get("scene_id")
        if isinstance(scene_id, str) and scene_id:
            mapped[scene_id] = item
    return mapped


def entity_map(payload: Any, *, key: str, fallback_key: str) -> dict[str, dict[str, Any]]:
    if not isinstance(payload, list):
        return {}
    mapped: dict[str, dict[str, Any]] = {}
    for item in payload:
        if not isinstance(item, dict):
            continue
        primary = item.get(key)
        if isinstance(primary, str) and primary.strip():
            mapped[slugify(primary)] = item
        fallback = item.get(fallback_key)
        if isinstance(fallback, str) and fallback.strip():
            mapped.setdefault(slugify(fallback), item)
    return mapped


def resolve_character_bible(
    character_bibles: dict[str, dict[str, Any]],
    character_id: str,
) -> dict[str, Any] | None:
    return character_bibles.get(slugify(character_id))


def resolve_location_bible(
    location_bibles: dict[str, dict[str, Any]],
    location_name: str,
) -> dict[str, Any] | None:
    return location_bibles.get(slugify(location_name))


def normalize_aspect_ratio(raw_value: Any) -> str | None:
    if not isinstance(raw_value, str) or not raw_value.strip():
        return None
    text = raw_value.strip()
    if ":" in text:
        left, _, right = text.partition(":")
        try:
            width = float(left)
            height = float(right)
        except ValueError:
            return None
    else:
        try:
            width, height = (float(item) for item in text.split("/", 1))
        except ValueError:
            return None
        except Exception:
            return None
    if height <= 0:
        return None
    ratio = width / height
    if ratio >= 1.2:
        return "16:9"
    if ratio <= 0.8:
        return "9:16"
    return "1:1"


def string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if isinstance(item, str) and item.strip()]


def clean_prompt_lines(lines: list[str]) -> list[str]:
    cleaned: list[str] = []
    for line in lines:
        text = str(line or "").strip()
        if not text:
            continue
        if not text.endswith((".", "!", "?")):
            text = f"{text}."
        cleaned.append(text)
    return cleaned


def anticipated_storyboard_ref(store: ArtifactStore, scene_id: str) -> ArtifactRef:
    versions = store.list_versions("storyboard", scene_id)
    next_version = versions[-1].version + 1 if versions else 1
    return ArtifactRef(
        artifact_type="storyboard",
        entity_id=scene_id,
        version=next_version,
        path=f"artifacts/storyboard/{scene_id}/v{next_version}.json",
    )


def latest_project_ref(store: ArtifactStore, artifact_type: str) -> ArtifactRef | None:
    refs = store.list_versions(artifact_type=artifact_type, entity_id="project")
    return refs[-1] if refs else None


def latest_entity_ref(store: ArtifactStore, artifact_type: str, entity_id: str) -> ArtifactRef:
    refs = store.list_versions(artifact_type=artifact_type, entity_id=entity_id)
    if not refs:
        raise ValueError(f"storyboard_v1 missing '{artifact_type}' artifact for '{entity_id}'")
    return refs[-1]


def maybe_latest_ref(
    store: ArtifactStore,
    artifact_type: str,
    entity_id: str,
) -> ArtifactRef | None:
    refs = store.list_versions(artifact_type=artifact_type, entity_id=entity_id)
    return refs[-1] if refs else None


def track_counts(entries: list[TrackEntry]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in entries:
        counts[entry.track_type] = counts.get(entry.track_type, 0) + 1
    return counts


def storyboard_confidence(plan: ShotPlan) -> float:
    values = [plan.coverage_strategy.audit.confidence]
    values.extend(shot.audit.confidence for shot in plan.shots)
    return sum(values) / len(values) if values else 0.0


def empty_cost(model: str) -> dict[str, Any]:
    return {
        "model": model,
        "input_tokens": 0,
        "output_tokens": 0,
        "estimated_cost_usd": 0.0,
    }


def merge_cost(total: dict[str, Any], call_cost: dict[str, Any]) -> None:
    total["input_tokens"] += int(call_cost.get("input_tokens", 0) or 0)
    total["output_tokens"] += int(call_cost.get("output_tokens", 0) or 0)
    total["estimated_cost_usd"] = round(
        float(total["estimated_cost_usd"]) + float(call_cost.get("estimated_cost_usd", 0.0) or 0.0),
        8,
    )
    models = {item for item in str(total.get("model", "")).split("+") if item}
    models.update(item for item in str(call_cost.get("model", "")).split("+") if item)
    total["model"] = "+".join(sorted(models)) if models else "code"


def dedupe_refs(refs: list[ArtifactRef]) -> list[ArtifactRef]:
    seen: set[tuple[str, str | None, int, str]] = set()
    deduped: list[ArtifactRef] = []
    for ref in refs:
        key = (ref.artifact_type, ref.entity_id, ref.version, ref.path)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(ref)
    return deduped


def storyboard_frame_dir(project_dir: Path, scene_id: str, version: int) -> Path:
    return project_dir / "artifacts" / "storyboard_frames" / scene_id / f"v{version}"


def image_format_for_model(model: str) -> tuple[str, str]:
    if model == "mock":
        return ".svg", "image/svg+xml"
    return ".jpg", "image/jpeg"


def slugify(value: str) -> str:
    text = value.strip().lower()
    text = _SLUG_RE.sub("_", text)
    return text.strip("_")


def average_values(values: Any) -> float:
    numbers = [float(value) for value in values]
    return sum(numbers) / len(numbers) if numbers else 0.0
