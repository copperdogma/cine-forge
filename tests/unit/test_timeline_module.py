from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from cine_forge.artifacts import ArtifactStore
from cine_forge.modules.timeline.timeline_build_v1.main import (
    add_scene_entry,
    build_initial_timeline,
    positions_for_scene,
    remove_scene_entry,
    reorder_edit_positions,
    reorder_story_positions,
    run_module,
    scene_at_edit_position,
    scene_at_story_position,
)
from cine_forge.schemas import ArtifactMetadata, TimelineEntry


def _seed_scene_artifacts(project_dir: Path, scene_ids: list[str]) -> ArtifactStore:
    store = ArtifactStore(project_dir=project_dir)
    for idx, scene_id in enumerate(scene_ids, start=1):
        store.save_artifact(
            artifact_type="scene",
            entity_id=scene_id,
            data={
                "scene_id": scene_id,
                "scene_number": idx,
                "heading": f"INT. TEST {idx} - DAY",
                "location": f"TEST {idx}",
                "time_of_day": "DAY",
                "int_ext": "INT",
                "characters_present": ["ALPHA"],
                "elements": [],
                "narrative_beats": [],
                "tone_mood": "neutral",
                "tone_shifts": [],
                "source_span": {"start_line": 1, "end_line": 5},
                "inferences": [],
                "provenance": [],
                "confidence": 1.0,
            },
            metadata=ArtifactMetadata(
                lineage=[],
                intent="seed scene",
                rationale="unit test seed",
                confidence=1.0,
                source="code",
            ),
        )
    return store


def _scene_index(scene_ids: list[str]) -> dict[str, Any]:
    entries = []
    for idx, scene_id in enumerate(scene_ids, start=1):
        entries.append(
            {
                "scene_id": scene_id,
                "scene_number": idx,
                "heading": f"INT. TEST {idx} - DAY",
                "location": f"TEST {idx}",
                "time_of_day": "DAY",
                "characters_present": ["ALPHA"],
                "source_span": {"start_line": idx * 10, "end_line": idx * 10 + 9},
                "tone_mood": "neutral",
            }
        )
    return {
        "total_scenes": len(scene_ids),
        "unique_locations": [f"TEST {idx}" for idx in range(1, len(scene_ids) + 1)],
        "unique_characters": ["ALPHA"],
        "estimated_runtime_minutes": float(len(scene_ids)),
        "scenes_passed_qa": len(scene_ids),
        "scenes_need_review": 0,
        "entries": entries,
    }


@pytest.mark.unit
def test_build_initial_timeline_defaults_story_order_without_continuity(tmp_path: Path) -> None:
    scene_ids = ["scene_001", "scene_002", "scene_003"]
    store = _seed_scene_artifacts(tmp_path, scene_ids)
    timeline = build_initial_timeline(
        scene_index=_scene_index(scene_ids),
        continuity_index=None,
        store=store,
        default_scene_duration_seconds=42.0,
    )

    assert timeline.total_scenes == 3
    assert timeline.chronology_source == "scene_index_fallback"
    assert timeline.estimated_runtime_seconds == pytest.approx(180.0)
    assert [entry.script_position for entry in timeline.entries] == [1, 2, 3]
    assert [entry.edit_position for entry in timeline.entries] == [1, 2, 3]
    assert [entry.story_position for entry in timeline.entries] == [1, 2, 3]
    assert all(entry.story_order_confidence == "low" for entry in timeline.entries)


@pytest.mark.unit
def test_build_initial_timeline_uses_continuity_when_available(tmp_path: Path) -> None:
    scene_ids = ["scene_001", "scene_002", "scene_003"]
    store = _seed_scene_artifacts(tmp_path, scene_ids)
    continuity_index = {
        "timelines": {
            "character:alpha": {
                "states": ["character_alpha_scene_002", "character_alpha_scene_001"]
            },
        },
        "total_gaps": 0,
        "overall_continuity_score": 0.9,
    }
    timeline = build_initial_timeline(
        scene_index=_scene_index(scene_ids),
        continuity_index=continuity_index,
        store=store,
    )

    assert timeline.chronology_source == "continuity_index"
    positions = {entry.scene_id: entry.story_position for entry in timeline.entries}
    assert positions["scene_002"] == 1
    assert positions["scene_001"] == 2
    assert positions["scene_003"] == 3
    confidences = {entry.scene_id: entry.story_order_confidence for entry in timeline.entries}
    assert confidences["scene_002"] == "medium"
    assert confidences["scene_001"] == "medium"
    assert confidences["scene_003"] == "low"


@pytest.mark.unit
def test_timeline_reorder_and_query_helpers(tmp_path: Path) -> None:
    scene_ids = ["scene_001", "scene_002", "scene_003"]
    store = _seed_scene_artifacts(tmp_path, scene_ids)
    timeline = build_initial_timeline(
        scene_index=_scene_index(scene_ids),
        continuity_index=None,
        store=store,
    )

    edited = reorder_edit_positions(timeline, ["scene_003", "scene_001", "scene_002"])
    assert scene_at_edit_position(edited, 1).scene_id == "scene_003"
    assert scene_at_edit_position(edited, 3).scene_id == "scene_002"

    storied = reorder_story_positions(edited, ["scene_002", "scene_003", "scene_001"])
    assert scene_at_story_position(storied, 1).scene_id == "scene_002"
    assert positions_for_scene(storied, "scene_001") == {
        "script_position": 1,
        "edit_position": 2,
        "story_position": 3,
    }
    with pytest.raises(ValueError, match="must include exactly timeline scene IDs"):
        reorder_edit_positions(timeline, ["scene_001", "scene_002"])
    with pytest.raises(ValueError, match="must include exactly timeline scene IDs"):
        reorder_story_positions(timeline, ["scene_001", "scene_002", "scene_003", "scene_999"])


@pytest.mark.unit
def test_timeline_add_and_remove_scene_entries(tmp_path: Path) -> None:
    scene_ids = ["scene_001", "scene_002"]
    store = _seed_scene_artifacts(tmp_path, scene_ids + ["scene_003"])
    base = build_initial_timeline(
        scene_index=_scene_index(scene_ids),
        continuity_index=None,
        store=store,
    )
    scene_003_ref = store.list_versions("scene", "scene_003")[-1]
    added = add_scene_entry(
        base,
        TimelineEntry(
            scene_id="scene_003",
            scene_ref=scene_003_ref,
            script_position=99,
            edit_position=99,
            story_position=99,
            estimated_duration_seconds=60.0,
        ),
        edit_position=2,
        story_position=3,
    )
    assert added.total_scenes == 3
    assert scene_at_edit_position(added, 2).scene_id == "scene_003"

    removed = remove_scene_entry(added, "scene_001")
    assert removed.total_scenes == 2
    assert positions_for_scene(removed, "scene_001") is None


@pytest.mark.unit
def test_run_module_builds_timeline_artifact_payload(tmp_path: Path) -> None:
    scene_ids = ["scene_001", "scene_002"]
    _seed_scene_artifacts(tmp_path, scene_ids)
    inputs = {"scene_index": _scene_index(scene_ids)}
    result = run_module(
        inputs=inputs,
        params={},
        context={"project_dir": str(tmp_path), "run_id": "r", "stage_id": "timeline"},
    )

    assert "artifacts" in result
    artifact = result["artifacts"][0]
    assert artifact["artifact_type"] == "timeline"
    assert artifact["entity_id"] == "project"
    assert artifact["data"]["total_scenes"] == 2
    assert len(artifact["data"]["entries"]) == 2
    assert len(artifact["metadata"]["lineage"]) == 2
