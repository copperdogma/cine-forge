"""Track manifest builder and always-playable resolver helpers."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from cine_forge.artifacts import ArtifactStore
from cine_forge.schemas import ArtifactRef, Timeline, TrackEntry, TrackManifest

DEFAULT_FALLBACK_ORDER = [
    "generated_video",
    "animatics",
    "storyboards",
    "script",
]

DEFAULT_TRACK_REGISTRY: dict[str, dict[str, Any]] = {
    "script": {"priority": 400},
    "dialogue_audio": {"priority": 350},
    "shots": {"priority": 300},
    "storyboards": {"priority": 200},
    "animatics": {"priority": 150},
    "keyframes": {"priority": 175},
    "generated_video": {"priority": 100},
    "continuity_events": {"priority": 500},
    "music_sfx": {"priority": 450},
}

_SCENE_ID_RE = re.compile(r"(scene_[0-9]+)$")


def run_module(
    inputs: dict[str, Any], params: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    """Build a project-level track manifest from timeline and available artifacts."""
    timeline_payload = _find_timeline(inputs)
    if timeline_payload is None:
        raise ValueError("track_system_v1 requires timeline input")

    project_dir = context.get("project_dir")
    if not isinstance(project_dir, str) or not project_dir:
        raise ValueError("track_system_v1 requires context.project_dir")

    store = ArtifactStore(project_dir=Path(project_dir))
    timeline_ref = _latest_project_ref(store=store, artifact_type="timeline")
    if timeline_ref is None:
        raise ValueError("track_system_v1 could not resolve latest project timeline artifact")
    timeline = Timeline.model_validate(timeline_payload)

    fallback_order = params.get("fallback_order")
    if fallback_order is not None and not isinstance(fallback_order, list):
        raise ValueError("track_system_v1 params.fallback_order must be a list")

    registry_overrides = params.get("track_registry")
    if registry_overrides is not None and not isinstance(registry_overrides, dict):
        raise ValueError("track_system_v1 params.track_registry must be an object")

    continuity_index = _find_continuity_index(inputs)
    manifest = build_track_manifest(
        timeline=timeline,
        timeline_ref=timeline_ref,
        store=store,
        continuity_index=continuity_index,
        fallback_order=fallback_order,
        track_registry=build_track_registry(registry_overrides),
    )

    lineage = [timeline_ref, *[entry.artifact_ref for entry in manifest.entries]]
    if continuity_index is not None:
        continuity_ref = _latest_project_ref(store=store, artifact_type="continuity_index")
        if continuity_ref is not None:
            lineage.append(continuity_ref)

    deduped_lineage = _dedupe_refs(lineage)

    return {
        "artifacts": [
            {
                "artifact_type": "track_manifest",
                "entity_id": "project",
                "data": manifest.model_dump(mode="json"),
                "metadata": {
                    "lineage": [ref.model_dump(mode="json") for ref in deduped_lineage],
                    "intent": "Canonical project track state and always-playable fallback order.",
                    "rationale": (
                        "Track manifest is derived from the latest timeline plus available "
                        "representation artifacts and deterministic fallback priorities."
                    ),
                    "confidence": _coverage_confidence(manifest=manifest, timeline=timeline),
                    "source": "hybrid",
                },
            }
        ],
        "cost": {
            "model": "code",
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": 0.0,
        },
    }


def build_track_registry(overrides: dict[str, Any] | None = None) -> dict[str, dict[str, Any]]:
    """Build an extensible track-type registry with optional caller overrides."""
    registry = {name: dict(config) for name, config in DEFAULT_TRACK_REGISTRY.items()}
    if not overrides:
        return registry

    for track_type, raw_config in overrides.items():
        if not isinstance(raw_config, dict):
            raise ValueError(f"track registry override for '{track_type}' must be an object")
        existing = dict(registry.get(track_type, {}))
        existing.update(raw_config)
        registry[track_type] = existing
    return registry


def build_track_manifest(
    timeline: Timeline,
    timeline_ref: ArtifactRef,
    store: ArtifactStore,
    continuity_index: dict[str, Any] | None = None,
    fallback_order: list[str] | None = None,
    track_registry: dict[str, dict[str, Any]] | None = None,
) -> TrackManifest:
    """Build baseline track manifest from timeline scene refs and optional continuity."""
    registry = track_registry or build_track_registry()
    entries: list[TrackEntry] = []

    time_windows = _timeline_scene_windows(timeline)
    for timeline_entry in timeline.entries:
        start_time, end_time = time_windows[timeline_entry.scene_id]
        entries.append(
            TrackEntry(
                track_type="script",
                scene_id=timeline_entry.scene_id,
                artifact_ref=timeline_entry.scene_ref,
                start_time_seconds=start_time,
                end_time_seconds=end_time,
                priority=_track_priority("script", registry),
                status="available",
                notes="Auto-populated from timeline scene_ref.",
            )
        )

    if continuity_index is not None:
        entries.extend(
            _build_continuity_entries(
                continuity_index=continuity_index,
                store=store,
                track_registry=registry,
            )
        )

    order = _fallback_order(fallback_order)
    manifest = TrackManifest(
        timeline_ref=timeline_ref,
        entries=entries,
        fallback_order=order,
        track_fill_counts=_track_counts(entries),
    )
    return manifest


def add_track_entry(manifest: TrackManifest, entry: TrackEntry) -> TrackManifest:
    """Return a new manifest with one entry appended."""
    entries = list(manifest.entries)
    entries.append(entry)
    return manifest.model_copy(
        update={"entries": entries, "track_fill_counts": _track_counts(entries)}
    )


def update_track_entry(
    manifest: TrackManifest,
    *,
    track_type: str,
    scene_id: str,
    shot_id: str | None = None,
    updates: dict[str, Any],
) -> TrackManifest:
    """Return a new manifest with the first matching entry updated."""
    if not updates:
        return manifest

    entries = list(manifest.entries)
    target_idx = None
    for idx, entry in enumerate(entries):
        if (
            entry.track_type == track_type
            and entry.scene_id == scene_id
            and entry.shot_id == shot_id
        ):
            target_idx = idx
            break
    if target_idx is None:
        raise ValueError("No track entry found for provided track_type/scene_id/shot_id")

    updated_entry = entries[target_idx].model_copy(update=updates)
    entries[target_idx] = TrackEntry.model_validate(updated_entry)
    return manifest.model_copy(
        update={"entries": entries, "track_fill_counts": _track_counts(entries)}
    )


def remove_track_entries(
    manifest: TrackManifest,
    *,
    track_type: str | None = None,
    scene_id: str | None = None,
    shot_id: str | None = None,
) -> TrackManifest:
    """Return a new manifest with entries matching the filter removed."""
    if track_type is None and scene_id is None and shot_id is None:
        raise ValueError("At least one filter is required to remove track entries")

    kept: list[TrackEntry] = []
    removed = 0
    for entry in manifest.entries:
        matches = (
            (track_type is None or entry.track_type == track_type)
            and (scene_id is None or entry.scene_id == scene_id)
            and (shot_id is None or entry.shot_id == shot_id)
        )
        if matches:
            removed += 1
            continue
        kept.append(entry)

    if removed == 0:
        raise ValueError("No track entries matched remove filter")

    return manifest.model_copy(update={"entries": kept, "track_fill_counts": _track_counts(kept)})


def best_for_scene(
    manifest: TrackManifest,
    *,
    scene_id: str,
    shot_id: str | None = None,
    fallback_order: list[str] | None = None,
    include_unavailable: bool = False,
) -> dict[str, Any]:
    """Resolve the best available representation for a scene (and optional shot)."""
    order = _fallback_order(fallback_order or manifest.fallback_order)
    scene_entries = [entry for entry in manifest.entries if entry.scene_id == scene_id]

    considered = [
        {
            "track_type": entry.track_type,
            "status": entry.status,
            "priority": entry.priority,
            "shot_id": entry.shot_id,
            "artifact_ref": entry.artifact_ref.model_dump(mode="json"),
        }
        for entry in scene_entries
    ]

    for layer in order:
        candidates = [entry for entry in scene_entries if entry.track_type == layer]
        if not include_unavailable:
            candidates = [entry for entry in candidates if entry.status == "available"]
        if not candidates:
            continue

        if shot_id is not None:
            shot_matches = [entry for entry in candidates if entry.shot_id == shot_id]
            scene_matches = [entry for entry in candidates if entry.shot_id is None]
            if shot_matches:
                candidates = shot_matches
            elif scene_matches:
                candidates = scene_matches

        winner = sorted(candidates, key=_entry_sort_key)[0]
        return {
            "resolved": True,
            "scene_id": scene_id,
            "shot_id": shot_id,
            "selected_track_type": winner.track_type,
            "entry": winner.model_dump(mode="json"),
            "rationale": {
                "fallback_order": order,
                "selected_reason": (
                    f"Selected '{winner.track_type}' as highest fallback layer "
                    "with eligible entries."
                ),
                "considered": considered,
            },
        }

    return {
        "resolved": False,
        "scene_id": scene_id,
        "shot_id": shot_id,
        "selected_track_type": None,
        "entry": None,
        "rationale": {
            "fallback_order": order,
            "selected_reason": "No eligible track entry found for requested scene/shot.",
            "considered": considered,
        },
    }


def best_for_time_range(
    manifest: TrackManifest,
    timeline: Timeline,
    *,
    start_time_seconds: float,
    end_time_seconds: float,
    fallback_order: list[str] | None = None,
) -> dict[str, Any]:
    """Resolve best representation for each overlapping timeline scene in a time window."""
    if end_time_seconds < start_time_seconds:
        raise ValueError("end_time_seconds must be >= start_time_seconds")

    windows = _timeline_scene_windows(timeline)
    overlaps: list[dict[str, Any]] = []
    for scene_id, (scene_start, scene_end) in windows.items():
        if scene_end <= start_time_seconds or scene_start >= end_time_seconds:
            continue
        overlaps.append(
            {
                "scene_id": scene_id,
                "window": {
                    "start_time_seconds": scene_start,
                    "end_time_seconds": scene_end,
                },
                "best": best_for_scene(
                    manifest,
                    scene_id=scene_id,
                    fallback_order=fallback_order,
                ),
            }
        )

    return {
        "start_time_seconds": start_time_seconds,
        "end_time_seconds": end_time_seconds,
        "overlapping_scenes": overlaps,
    }


def track_fill_summary(
    manifest: TrackManifest,
    *,
    timeline: Timeline | None = None,
) -> dict[str, Any]:
    """Summarize per-track entry count and per-scene coverage."""
    counts = _track_counts(manifest.entries)
    expected_scene_ids = {entry.scene_id for entry in timeline.entries} if timeline else set()

    coverage: dict[str, int] = {}
    for track_type in sorted(counts):
        covered = {
            entry.scene_id
            for entry in manifest.entries
            if entry.track_type == track_type and entry.status == "available"
        }
        coverage[track_type] = len(covered)

    return {
        "track_counts": counts,
        "scene_coverage": coverage,
        "expected_scene_count": len(expected_scene_ids),
    }


def unresolved_gaps_by_fallback_layer(
    manifest: TrackManifest,
    *,
    timeline: Timeline,
    fallback_order: list[str] | None = None,
) -> dict[str, Any]:
    """Report scene gaps per fallback layer and unresolved scenes."""
    order = _fallback_order(fallback_order or manifest.fallback_order)
    scene_ids = [entry.scene_id for entry in timeline.entries]

    gaps_by_layer: dict[str, list[str]] = {}
    for track_type in order:
        missing = []
        for scene_id in scene_ids:
            has_available = any(
                entry.scene_id == scene_id
                and entry.track_type == track_type
                and entry.status == "available"
                for entry in manifest.entries
            )
            if not has_available:
                missing.append(scene_id)
        gaps_by_layer[track_type] = missing

    unresolved = [
        scene_id
        for scene_id in scene_ids
        if not best_for_scene(manifest, scene_id=scene_id, fallback_order=order)["resolved"]
    ]

    return {
        "fallback_order": order,
        "gaps_by_layer": gaps_by_layer,
        "unresolved_scenes": unresolved,
    }


def _track_priority(track_type: str, registry: dict[str, dict[str, Any]]) -> int:
    default_priority = 1000
    config = registry.get(track_type, {})
    raw_priority = config.get("priority", default_priority)
    try:
        return max(0, int(raw_priority))
    except (TypeError, ValueError):
        return default_priority


def _build_continuity_entries(
    continuity_index: dict[str, Any],
    store: ArtifactStore,
    track_registry: dict[str, dict[str, Any]],
) -> list[TrackEntry]:
    entries: list[TrackEntry] = []
    timelines = continuity_index.get("timelines", {})
    if not isinstance(timelines, dict):
        return entries

    for entity_timeline in timelines.values():
        if not isinstance(entity_timeline, dict):
            continue
        states = entity_timeline.get("states", [])
        if not isinstance(states, list):
            continue
        for state_id in states:
            if not isinstance(state_id, str):
                continue
            scene_id = _scene_id_from_state_id(state_id)
            if not scene_id:
                continue
            versions = store.list_versions("continuity_state", state_id)
            if not versions:
                continue
            entries.append(
                TrackEntry(
                    track_type="continuity_events",
                    scene_id=scene_id,
                    artifact_ref=versions[-1],
                    priority=_track_priority("continuity_events", track_registry),
                    status="available",
                    notes="Auto-populated from continuity_index timelines.",
                )
            )
    return entries


def _scene_id_from_state_id(state_id: str) -> str | None:
    match = _SCENE_ID_RE.search(state_id)
    return match.group(1) if match else None


def _find_timeline(inputs: dict[str, Any]) -> dict[str, Any] | None:
    for value in inputs.values():
        if isinstance(value, dict) and "entries" in value and "total_scenes" in value:
            return value
    return None


def _find_continuity_index(inputs: dict[str, Any]) -> dict[str, Any] | None:
    for value in inputs.values():
        if isinstance(value, dict) and "timelines" in value and "overall_continuity_score" in value:
            return value
    return None


def _latest_project_ref(store: ArtifactStore, artifact_type: str) -> ArtifactRef | None:
    refs = store.list_versions(artifact_type=artifact_type, entity_id="project")
    return refs[-1] if refs else None


def _timeline_scene_windows(timeline: Timeline) -> dict[str, tuple[float, float]]:
    edit_sorted = sorted(timeline.entries, key=lambda entry: entry.edit_position)
    windows: dict[str, tuple[float, float]] = {}
    current_time = 0.0
    for entry in edit_sorted:
        start = current_time
        duration = max(float(entry.estimated_duration_seconds), 0.0)
        current_time = start + duration
        windows[entry.scene_id] = (start, current_time)
    return windows


def _entry_sort_key(entry: TrackEntry) -> tuple[int, int]:
    shot_weight = 0 if entry.shot_id else 1
    return (entry.priority, shot_weight)


def _fallback_order(order: list[str] | None) -> list[str]:
    if not order:
        return list(DEFAULT_FALLBACK_ORDER)
    seen = set()
    normalized = []
    for item in order:
        if not isinstance(item, str):
            continue
        if item in seen:
            continue
        normalized.append(item)
        seen.add(item)
    return normalized or list(DEFAULT_FALLBACK_ORDER)


def _track_counts(entries: list[TrackEntry]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in entries:
        counts[entry.track_type] = counts.get(entry.track_type, 0) + 1
    return counts


def _coverage_confidence(manifest: TrackManifest, timeline: Timeline) -> float:
    if timeline.total_scenes <= 0:
        return 1.0
    resolved = sum(
        1
        for scene in timeline.entries
        if best_for_scene(manifest, scene_id=scene.scene_id).get("resolved", False)
    )
    return resolved / float(timeline.total_scenes)


def _dedupe_refs(refs: list[ArtifactRef | None]) -> list[ArtifactRef]:
    deduped: list[ArtifactRef] = []
    seen: set[tuple[str, str | None, int, str]] = set()
    for ref in refs:
        if ref is None:
            continue
        key = (ref.artifact_type, ref.entity_id, ref.version, ref.path)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(ref)
    return deduped
