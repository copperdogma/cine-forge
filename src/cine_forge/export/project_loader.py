"""Shared artifact-loading helpers for project export flows."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cine_forge.ai.fdx import detect_and_convert_fdx
from cine_forge.artifacts import ArtifactStore
from cine_forge.modules.ingest.story_ingest_v1.main import read_source_text_with_diagnostics
from cine_forge.schemas import ArtifactRef, Scene, Timeline, TimelineEntry, TrackManifest


def load_all_artifacts(
    store: ArtifactStore,
) -> tuple[
    list[dict[str, Any]],
    dict[str, dict[str, Any]],
    dict[str, dict[str, Any]],
    dict[str, dict[str, Any]],
]:
    """Load the latest scene and bible artifacts used by export surfaces."""
    scenes: list[dict[str, Any]] = []
    characters: dict[str, dict[str, Any]] = {}
    locations: dict[str, dict[str, Any]] = {}
    props: dict[str, dict[str, Any]] = {}

    for scene_id in store.list_entities("scene"):
        latest = _latest_ref(store, "scene", scene_id)
        if latest is None:
            continue
        data = store.load_artifact(latest).data
        if data:
            scenes.append(data)
    scenes.sort(key=lambda item: item.get("scene_number", 0))

    for character_id in store.list_entities("character_bible"):
        latest = _latest_ref(store, "character_bible", character_id)
        if latest is None:
            continue
        data = store.load_artifact(latest).data
        if data:
            characters[character_id] = data

    for location_id in store.list_entities("location_bible"):
        latest = _latest_ref(store, "location_bible", location_id)
        if latest is None:
            continue
        data = store.load_artifact(latest).data
        if data:
            locations[location_id] = data

    for prop_id in store.list_entities("prop_bible"):
        latest = _latest_ref(store, "prop_bible", prop_id)
        if latest is None:
            continue
        data = store.load_artifact(latest).data
        if data:
            props[prop_id] = data

    return scenes, characters, locations, props


def load_script_content(store: ArtifactStore) -> str:
    """Return the canonical script text when present."""
    latest = _latest_ref(store, "canonical_script", "project")
    if latest is None:
        return ""
    data = store.load_artifact(latest).data
    return data.get("script_text") or data.get("content") or data.get("text") or ""


def load_exportable_script_content(store: ArtifactStore) -> str:
    """Return the best available screenplay text for export surfaces.

    Prefers the canonical normalized script when present, but falls back to the
    latest uploaded input so screenplay export still works before breakdown.
    """
    script_text = load_script_content(store)
    if script_text.strip():
        return script_text

    input_path = _latest_input_path(store)
    if input_path is None:
        raise ValueError("No screenplay input is available for export.")

    try:
        extracted, _diagnostics = read_source_text_with_diagnostics(input_path)
    except Exception as exc:  # noqa: BLE001
        raise ValueError(
            "Screenplay export could not read the latest uploaded input. "
            "Run basic breakdown first to normalize it."
        ) from exc

    if input_path.suffix.lower() == ".fdx":
        converted = detect_and_convert_fdx(extracted)
        if converted.is_fdx:
            extracted = converted.fountain_text or ""

    if not extracted.strip():
        raise ValueError(
            "Screenplay export needs readable script text. "
            "Run basic breakdown first to normalize this input."
        )
    return extracted


def load_pre_scene_text(store: ArtifactStore, first_scene_start_line: int) -> str:
    """Return canonical-script content that appears before the first scene."""
    script_text = load_script_content(store)
    if not script_text or first_scene_start_line <= 1:
        return ""
    lines = script_text.splitlines()
    return "\n".join(lines[: first_scene_start_line - 1])


def load_project_title(store: ArtifactStore, project_id: str) -> str:
    """Resolve the project title from project_config, falling back to the ID."""
    latest = _latest_ref(store, "project_config", "project")
    if latest is None:
        return project_id
    data = store.load_artifact(latest).data
    return str(data.get("title") or project_id)


def load_timeline_artifact(store: ArtifactStore) -> tuple[ArtifactRef, Timeline] | None:
    """Return the latest project timeline artifact when available."""
    latest = _latest_ref(store, "timeline", "project")
    if latest is None:
        return None
    artifact = store.load_artifact(latest)
    return latest, Timeline.model_validate(artifact.data)


def load_track_manifest_artifact(
    store: ArtifactStore,
    *,
    expected_timeline_ref: ArtifactRef | None = None,
) -> tuple[ArtifactRef, TrackManifest] | None:
    """Return the latest project track manifest that matches the timeline, if any."""
    latest = _latest_ref(store, "track_manifest", "project")
    if latest is None:
        return None
    artifact = store.load_artifact(latest)
    manifest = TrackManifest.model_validate(artifact.data)
    if (
        expected_timeline_ref is not None
        and manifest.timeline_ref.key() != expected_timeline_ref.key()
    ):
        return None
    return latest, manifest


def load_timeline_scenes(
    store: ArtifactStore,
    timeline: Timeline,
) -> list[tuple[TimelineEntry, Scene]]:
    """Resolve typed scene artifacts for each timeline slot in edit order."""
    ordered_entries = sorted(timeline.entries, key=lambda entry: entry.edit_position)
    resolved: list[tuple[TimelineEntry, Scene]] = []
    for entry in ordered_entries:
        artifact = store.load_artifact(entry.scene_ref)
        resolved.append((entry, Scene.model_validate(artifact.data)))
    return resolved


def _latest_ref(
    store: ArtifactStore,
    artifact_type: str,
    entity_id: str | None,
) -> ArtifactRef | None:
    refs = store.list_versions(artifact_type, entity_id)
    return refs[-1] if refs else None


def _latest_input_path(store: ArtifactStore) -> Path | None:
    inputs_dir = store.project_dir / "inputs"
    if not inputs_dir.exists():
        return None

    input_files = [entry for entry in inputs_dir.iterdir() if entry.is_file()]
    if not input_files:
        return None
    return max(input_files, key=lambda entry: entry.stat().st_mtime)
