"""Support helpers for render-adapter engine packs and artifact wiring."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from cine_forge.artifacts import ArtifactStore
from cine_forge.schemas import ArtifactRef, EnginePack, TrackEntry

ENGINE_PACK_DIR = Path(__file__).resolve().parent / "engine_packs"
SLUG_RE = re.compile(r"[^a-z0-9]+")
IMAGE_KINDS = {
    "keyframe",
    "scene_injected_image",
    "project_injected_image",
    "character_injected_image",
    "location_injected_image",
    "prop_injected_image",
}
AUDIO_KINDS = {"scene_injected_audio", "project_injected_audio"}


def load_engine_pack(pack_id: str) -> EnginePack:
    """Load and validate one engine-pack YAML file by pack_id."""
    for path in ENGINE_PACK_DIR.glob("*.yaml"):
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            continue
        if payload.get("pack_id") == pack_id:
            return EnginePack.model_validate(payload)
    raise ValueError(f"Unknown render engine pack: {pack_id}")


def anticipated_entity_ref(store: ArtifactStore, artifact_type: str, entity_id: str) -> ArtifactRef:
    versions = store.list_versions(artifact_type, entity_id)
    next_version = versions[-1].version + 1 if versions else 1
    return ArtifactRef(
        artifact_type=artifact_type,
        entity_id=entity_id,
        version=next_version,
        path=f"artifacts/{artifact_type}/{entity_id}/v{next_version}.json",
    )


def latest_entity_ref(
    store: ArtifactStore,
    artifact_type: str,
    entity_id: str,
) -> ArtifactRef | None:
    refs = store.list_versions(artifact_type, entity_id)
    return refs[-1] if refs else None


def latest_project_ref(store: ArtifactStore, artifact_type: str) -> ArtifactRef | None:
    return latest_entity_ref(store, artifact_type, "project")


def track_counts(entries: list[TrackEntry]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in entries:
        counts[entry.track_type] = counts.get(entry.track_type, 0) + 1
    return counts


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


def render_media_dir(
    project_dir: Path,
    scene_id: str,
    version: int,
    *,
    media_root: str = "generated_video_media",
) -> Path:
    return project_dir / "artifacts" / media_root / scene_id / f"v{version}"


def relative_path(project_dir: Path, path: Path) -> str:
    return str(path.relative_to(project_dir))


def media_type_for_image(path: str) -> str:
    suffix = Path(path).suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if suffix == ".png":
        return "image/png"
    if suffix == ".webp":
        return "image/webp"
    return "application/octet-stream"


def normalize_aspect_ratio(
    requested_aspect_ratio: str | None,
    supported_aspect_ratios: list[str],
) -> tuple[str, str | None]:
    """Map a project aspect ratio onto the engine pack's supported set."""
    if not supported_aspect_ratios:
        raise ValueError("supported_aspect_ratios must not be empty")

    if not requested_aspect_ratio:
        return supported_aspect_ratios[0], None
    normalized = requested_aspect_ratio.strip()
    if normalized in supported_aspect_ratios:
        return normalized, None

    ratio_value = _aspect_ratio_value(normalized)
    if ratio_value is None:
        return supported_aspect_ratios[0], (
            f"Aspect ratio '{requested_aspect_ratio}' is invalid; defaulted to "
            f"{supported_aspect_ratios[0]}."
        )

    target = "9:16" if ratio_value < 1.0 else "16:9"
    if target in supported_aspect_ratios:
        return target, (
            f"Aspect ratio '{requested_aspect_ratio}' is not directly supported; "
            f"mapped to {target}."
        )
    return supported_aspect_ratios[0], (
        f"Aspect ratio '{requested_aspect_ratio}' is not directly supported; "
        f"defaulted to {supported_aspect_ratios[0]}."
    )


def normalize_duration_seconds(
    requested_seconds: float,
    supported_durations_seconds: list[int],
) -> tuple[int, str | None]:
    """Round a requested duration up to the nearest supported engine duration."""
    if requested_seconds <= 0:
        raise ValueError("requested_seconds must be positive")
    if not supported_durations_seconds:
        raise ValueError("supported_durations_seconds must not be empty")

    supported = sorted(set(supported_durations_seconds))
    for candidate in supported:
        if requested_seconds <= candidate:
            if abs(requested_seconds - candidate) < 0.01:
                return candidate, None
            return candidate, (
                f"Requested duration {requested_seconds:.1f}s normalized to supported "
                f"duration {candidate}s."
            )
    raise ValueError(
        f"Requested duration {requested_seconds:.1f}s exceeds engine maximum {supported[-1]}s."
    )


def optional_string(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def slugify(value: str) -> str:
    return SLUG_RE.sub("_", value.strip().lower()).strip("_")


def first_or_none(values: list[Any]) -> Any | None:
    return values[0] if values else None


def _aspect_ratio_value(raw: str) -> float | None:
    if ":" not in raw:
        return None
    left, right = raw.split(":", maxsplit=1)
    try:
        numerator = float(left.strip())
        denominator = float(right.strip())
    except ValueError:
        return None
    if denominator == 0:
        return None
    return numerator / denominator
