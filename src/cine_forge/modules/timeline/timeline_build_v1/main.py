"""Build timeline artifact from scene index and optional continuity data."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from cine_forge.artifacts import ArtifactStore
from cine_forge.schemas import ArtifactRef, Timeline, TimelineEntry

_SCENE_ID_RE = re.compile(r"(scene_[0-9]+)$")


def run_module(
    inputs: dict[str, Any], params: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    """Build and emit a project-level timeline artifact."""
    scene_index = _find_scene_index(inputs)
    if scene_index is None:
        raise ValueError("timeline_build_v1 requires scene_index input")

    continuity_index = _find_continuity_index(inputs)
    project_dir = context.get("project_dir")
    if not isinstance(project_dir, str) or not project_dir:
        raise ValueError("timeline_build_v1 requires context.project_dir")

    store = ArtifactStore(project_dir=Path(project_dir))
    default_scene_duration = float(params.get("default_scene_duration_seconds", 60.0))
    timeline = build_initial_timeline(
        scene_index=scene_index,
        continuity_index=continuity_index,
        store=store,
        default_scene_duration_seconds=default_scene_duration,
    )
    lineage_refs = [entry.scene_ref for entry in timeline.entries]
    if continuity_index is not None:
        continuity_refs = store.list_versions(artifact_type="continuity_index", entity_id="project")
        if continuity_refs:
            lineage_refs.append(continuity_refs[-1])

    return {
        "artifacts": [
            {
                "artifact_type": "timeline",
                "entity_id": "project",
                "data": timeline.model_dump(mode="json"),
                "metadata": {
                    "lineage": [ref.model_dump(mode="json") for ref in lineage_refs],
                    "intent": "Canonical project timeline with script/edit/story ordering.",
                    "rationale": (
                        "Built from scene index and optional continuity evidence with "
                        "explicit chronology confidence."
                    ),
                    "confidence": _aggregate_confidence(timeline),
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


def build_initial_timeline(
    scene_index: dict[str, Any],
    continuity_index: dict[str, Any] | None,
    store: ArtifactStore,
    default_scene_duration_seconds: float = 60.0,
) -> Timeline:
    """Construct initial timeline from the latest scene index and optional continuity index."""
    entries_payload = scene_index.get("entries", [])
    if not isinstance(entries_payload, list):
        raise ValueError("scene_index.entries must be a list")
    total_scenes = max(len(entries_payload), 0)

    runtime_minutes = float(scene_index.get("estimated_runtime_minutes", 0.0) or 0.0)
    total_runtime_seconds = max(runtime_minutes * 60.0, 0.0)
    per_scene_duration = (
        total_runtime_seconds / total_scenes
        if total_scenes > 0 and total_runtime_seconds > 0
        else max(default_scene_duration_seconds, 0.0)
    )

    story_positions, story_confidences, story_rationales, chronology_source = _derive_story_order(
        scene_index_entries=entries_payload,
        continuity_index=continuity_index,
    )

    timeline_entries: list[TimelineEntry] = []
    for idx, entry in enumerate(entries_payload, start=1):
        scene_id = str(entry.get("scene_id") or "")
        if not scene_id:
            raise ValueError("scene_index entry missing scene_id")
        scene_ref = _latest_scene_ref(store=store, scene_id=scene_id)
        timeline_entries.append(
            TimelineEntry(
                scene_id=scene_id,
                scene_ref=scene_ref,
                script_position=idx,
                edit_position=idx,
                story_position=story_positions.get(scene_id, idx),
                estimated_duration_seconds=per_scene_duration,
                shot_count=0,
                shot_ids=[],
                story_order_confidence=story_confidences.get(scene_id, "low"),
                story_order_rationale=story_rationales.get(scene_id, "Defaulted to edit order."),
            )
        )

    return Timeline(
        entries=timeline_entries,
        total_scenes=total_scenes,
        estimated_runtime_seconds=per_scene_duration * total_scenes,
        edit_order_locked=False,
        story_order_locked=False,
        chronology_source=chronology_source,
    )


def reorder_edit_positions(timeline: Timeline, ordered_scene_ids: list[str]) -> Timeline:
    """Return a new timeline with reordered edit positions."""
    mapping = _position_map(ordered_scene_ids)
    _validate_reorder_payload(timeline, ordered_scene_ids, order_label="edit")
    updated = []
    for entry in timeline.entries:
        if entry.scene_id not in mapping:
            raise ValueError(f"Scene '{entry.scene_id}' missing in edit reordering payload")
        updated.append(entry.model_copy(update={"edit_position": mapping[entry.scene_id]}))
    return _normalize_timeline(timeline, updated)


def reorder_story_positions(timeline: Timeline, ordered_scene_ids: list[str]) -> Timeline:
    """Return a new timeline with reordered story positions."""
    mapping = _position_map(ordered_scene_ids)
    _validate_reorder_payload(timeline, ordered_scene_ids, order_label="story")
    updated = []
    for entry in timeline.entries:
        if entry.scene_id not in mapping:
            raise ValueError(f"Scene '{entry.scene_id}' missing in story reordering payload")
        updated.append(
            entry.model_copy(
                update={
                    "story_position": mapping[entry.scene_id],
                    "story_order_confidence": "high",
                    "story_order_rationale": "Explicitly reordered by operator/director.",
                }
            )
        )
    return _normalize_timeline(timeline, updated)


def add_scene_entry(
    timeline: Timeline,
    entry: TimelineEntry,
    edit_position: int | None = None,
    story_position: int | None = None,
) -> Timeline:
    """Return a new timeline with an additional scene entry."""
    if any(item.scene_id == entry.scene_id for item in timeline.entries):
        raise ValueError(f"Scene '{entry.scene_id}' already exists in timeline")
    entries = list(timeline.entries)
    edit_pos = max(1, edit_position or (len(entries) + 1))
    story_pos = max(1, story_position or (len(entries) + 1))
    for existing in entries:
        if existing.edit_position >= edit_pos:
            existing.edit_position += 1
        if existing.story_position >= story_pos:
            existing.story_position += 1
    entries.append(
        entry.model_copy(
            update={
                "script_position": len(entries) + 1,
                "edit_position": edit_pos,
                "story_position": story_pos,
            }
        )
    )
    _renumber_positions(entries, key="edit_position")
    _renumber_positions(entries, key="story_position")
    return _normalize_timeline(timeline, entries)


def remove_scene_entry(timeline: Timeline, scene_id: str) -> Timeline:
    """Return a new timeline with one scene removed."""
    entries = [entry for entry in timeline.entries if entry.scene_id != scene_id]
    if len(entries) == len(timeline.entries):
        raise ValueError(f"Scene '{scene_id}' not found in timeline")
    _renumber_positions(entries, key="script_position")
    _renumber_positions(entries, key="edit_position")
    _renumber_positions(entries, key="story_position")
    return _normalize_timeline(timeline, entries)


def scene_at_edit_position(timeline: Timeline, position: int) -> TimelineEntry | None:
    """Lookup helper: scene at edit position N."""
    for entry in timeline.entries:
        if entry.edit_position == position:
            return entry
    return None


def scene_at_story_position(timeline: Timeline, position: int) -> TimelineEntry | None:
    """Lookup helper: scene at story position N."""
    for entry in timeline.entries:
        if entry.story_position == position:
            return entry
    return None


def positions_for_scene(timeline: Timeline, scene_id: str) -> dict[str, int] | None:
    """Lookup helper: script/edit/story positions for a scene."""
    for entry in timeline.entries:
        if entry.scene_id == scene_id:
            return {
                "script_position": entry.script_position,
                "edit_position": entry.edit_position,
                "story_position": entry.story_position,
            }
    return None


def _latest_scene_ref(store: ArtifactStore, scene_id: str) -> ArtifactRef:
    refs = store.list_versions(artifact_type="scene", entity_id=scene_id)
    if not refs:
        raise ValueError(f"timeline_build_v1 could not resolve scene artifact for '{scene_id}'")
    return refs[-1]


def _find_scene_index(inputs: dict[str, Any]) -> dict[str, Any] | None:
    for value in inputs.values():
        if isinstance(value, dict) and "entries" in value and "total_scenes" in value:
            return value
    return None


def _find_continuity_index(inputs: dict[str, Any]) -> dict[str, Any] | None:
    for value in inputs.values():
        if isinstance(value, dict) and "timelines" in value and "overall_continuity_score" in value:
            return value
    return None


def _derive_story_order(
    scene_index_entries: list[dict[str, Any]],
    continuity_index: dict[str, Any] | None,
) -> tuple[dict[str, int], dict[str, str], dict[str, str], str]:
    scene_ids = [str(entry.get("scene_id") or "") for entry in scene_index_entries]
    valid_scene_ids = [scene_id for scene_id in scene_ids if scene_id]
    fallback_positions = {scene_id: idx for idx, scene_id in enumerate(valid_scene_ids, start=1)}

    if not continuity_index:
        return (
            fallback_positions,
            {scene_id: "low" for scene_id in valid_scene_ids},
            {
                scene_id: "No continuity_index provided; defaulted to edit order."
                for scene_id in valid_scene_ids
            },
            "scene_index_fallback",
        )

    timelines = continuity_index.get("timelines", {})
    if not isinstance(timelines, dict):
        return (
            fallback_positions,
            {scene_id: "low" for scene_id in valid_scene_ids},
            {
                scene_id: "Invalid continuity_index.timelines; defaulted to edit order."
                for scene_id in valid_scene_ids
            },
            "scene_index_fallback",
        )

    seen_order: list[str] = []
    for timeline in timelines.values():
        if not isinstance(timeline, dict):
            continue
        states = timeline.get("states", [])
        if not isinstance(states, list):
            continue
        for state_id in states:
            if not isinstance(state_id, str):
                continue
            match = _SCENE_ID_RE.search(state_id)
            if not match:
                continue
            scene_id = match.group(1)
            if scene_id in valid_scene_ids and scene_id not in seen_order:
                seen_order.append(scene_id)

    if not seen_order:
        return (
            fallback_positions,
            {scene_id: "low" for scene_id in valid_scene_ids},
            {
                scene_id: "Continuity states lacked scene references; defaulted to edit order."
                for scene_id in valid_scene_ids
            },
            "scene_index_fallback",
        )

    ordered = list(seen_order)
    for scene_id in valid_scene_ids:
        if scene_id not in ordered:
            ordered.append(scene_id)

    positions = {scene_id: idx for idx, scene_id in enumerate(ordered, start=1)}
    confidences: dict[str, str] = {}
    rationales: dict[str, str] = {}
    for scene_id in valid_scene_ids:
        if scene_id in seen_order:
            confidences[scene_id] = "medium"
            rationales[scene_id] = "Derived from continuity timeline state ordering."
        else:
            confidences[scene_id] = "low"
            rationales[scene_id] = "No continuity evidence for scene; defaulted to edit order."
    return positions, confidences, rationales, "continuity_index"


def _position_map(ordered_scene_ids: list[str]) -> dict[str, int]:
    if len(set(ordered_scene_ids)) != len(ordered_scene_ids):
        raise ValueError("Scene IDs for reordering must be unique")
    return {scene_id: idx for idx, scene_id in enumerate(ordered_scene_ids, start=1)}


def _validate_reorder_payload(
    timeline: Timeline,
    ordered_scene_ids: list[str],
    order_label: str,
) -> None:
    expected_scene_ids = {entry.scene_id for entry in timeline.entries}
    provided_scene_ids = set(ordered_scene_ids)
    if expected_scene_ids != provided_scene_ids:
        missing = sorted(expected_scene_ids - provided_scene_ids)
        extra = sorted(provided_scene_ids - expected_scene_ids)
        raise ValueError(
            f"{order_label}_reorder payload must include exactly timeline scene IDs "
            f"(missing={missing}, extra={extra})"
        )


def _normalize_timeline(timeline: Timeline, entries: list[TimelineEntry]) -> Timeline:
    return timeline.model_copy(
        update={
            "entries": entries,
            "total_scenes": len(entries),
            "estimated_runtime_seconds": sum(entry.estimated_duration_seconds for entry in entries),
        }
    )


def _renumber_positions(entries: list[TimelineEntry], key: str) -> None:
    sorted_entries = sorted(entries, key=lambda item: getattr(item, key))
    for idx, entry in enumerate(sorted_entries, start=1):
        setattr(entry, key, idx)


def _aggregate_confidence(timeline: Timeline) -> float:
    if not timeline.entries:
        return 1.0
    weight = {"high": 1.0, "medium": 0.75, "low": 0.5}
    total = sum(weight.get(entry.story_order_confidence, 0.5) for entry in timeline.entries)
    return round(total / len(timeline.entries), 4)
