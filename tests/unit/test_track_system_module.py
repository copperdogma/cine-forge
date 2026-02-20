from __future__ import annotations

from pathlib import Path

import pytest

from cine_forge.artifacts import ArtifactStore
from cine_forge.modules.timeline.track_system_v1.main import (
    add_track_entry,
    best_for_scene,
    best_for_time_range,
    build_track_manifest,
    build_track_registry,
    remove_track_entries,
    run_module,
    track_fill_summary,
    unresolved_gaps_by_fallback_layer,
    update_track_entry,
)
from cine_forge.schemas import ArtifactMetadata, ArtifactRef, Timeline, TimelineEntry, TrackEntry


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


def _seed_timeline_artifact(
    store: ArtifactStore, scene_ids: list[str]
) -> tuple[ArtifactRef, Timeline]:
    scene_refs = {scene_id: store.list_versions("scene", scene_id)[-1] for scene_id in scene_ids}
    timeline = Timeline(
        entries=[
            TimelineEntry(
                scene_id=scene_id,
                scene_ref=scene_refs[scene_id],
                script_position=idx,
                edit_position=idx,
                story_position=idx,
                estimated_duration_seconds=60.0,
            )
            for idx, scene_id in enumerate(scene_ids, start=1)
        ],
        total_scenes=len(scene_ids),
        estimated_runtime_seconds=float(len(scene_ids) * 60),
    )
    timeline_ref = store.save_artifact(
        artifact_type="timeline",
        entity_id="project",
        data=timeline.model_dump(mode="json"),
        metadata=ArtifactMetadata(
            lineage=list(scene_refs.values()),
            intent="seed timeline",
            rationale="unit test seed",
            confidence=1.0,
            source="code",
        ),
    )
    return timeline_ref, timeline


@pytest.mark.unit
def test_track_registry_defaults_and_overrides() -> None:
    registry = build_track_registry()
    assert {
        "script",
        "dialogue_audio",
        "shots",
        "storyboards",
        "animatics",
        "keyframes",
        "generated_video",
        "continuity_events",
        "music_sfx",
    }.issubset(set(registry.keys()))

    updated = build_track_registry(
        {"generated_video": {"priority": 10}, "new_track": {"priority": 55}}
    )
    assert updated["generated_video"]["priority"] == 10
    assert updated["new_track"]["priority"] == 55


@pytest.mark.unit
def test_best_for_scene_applies_fallback_and_status_filters(tmp_path: Path) -> None:
    scene_ids = ["scene_001"]
    store = _seed_scene_artifacts(tmp_path, scene_ids)
    timeline_ref, timeline = _seed_timeline_artifact(store, scene_ids)

    manifest = build_track_manifest(timeline=timeline, timeline_ref=timeline_ref, store=store)
    scene_ref = store.list_versions("scene", "scene_001")[-1]
    manifest = add_track_entry(
        manifest,
        TrackEntry(
            track_type="storyboards",
            scene_id="scene_001",
            artifact_ref=scene_ref,
            priority=200,
            status="failed",
        ),
    )
    manifest = add_track_entry(
        manifest,
        TrackEntry(
            track_type="animatics",
            scene_id="scene_001",
            artifact_ref=scene_ref,
            priority=150,
            status="pending",
        ),
    )

    resolved = best_for_scene(manifest, scene_id="scene_001")
    assert resolved["resolved"] is True
    assert resolved["selected_track_type"] == "script"

    manifest = add_track_entry(
        manifest,
        TrackEntry(
            track_type="generated_video",
            scene_id="scene_001",
            shot_id="shot_001",
            artifact_ref=scene_ref,
            priority=100,
            status="available",
        ),
    )

    resolved_shot = best_for_scene(manifest, scene_id="scene_001", shot_id="shot_001")
    assert resolved_shot["selected_track_type"] == "generated_video"


@pytest.mark.unit
def test_resolver_supports_mixed_fidelity_and_gap_reporting(tmp_path: Path) -> None:
    scene_ids = ["scene_001", "scene_002", "scene_003"]
    store = _seed_scene_artifacts(tmp_path, scene_ids)
    timeline_ref, timeline = _seed_timeline_artifact(store, scene_ids)
    manifest = build_track_manifest(timeline=timeline, timeline_ref=timeline_ref, store=store)

    scene_001_ref = store.list_versions("scene", "scene_001")[-1]
    scene_002_ref = store.list_versions("scene", "scene_002")[-1]
    manifest = add_track_entry(
        manifest,
        TrackEntry(
            track_type="storyboards",
            scene_id="scene_001",
            artifact_ref=scene_001_ref,
            priority=200,
            status="available",
        ),
    )
    manifest = add_track_entry(
        manifest,
        TrackEntry(
            track_type="animatics",
            scene_id="scene_002",
            artifact_ref=scene_002_ref,
            priority=150,
            status="available",
        ),
    )

    assert best_for_scene(manifest, scene_id="scene_001")["selected_track_type"] == "storyboards"
    assert best_for_scene(manifest, scene_id="scene_002")["selected_track_type"] == "animatics"
    assert best_for_scene(manifest, scene_id="scene_003")["selected_track_type"] == "script"

    summary = track_fill_summary(manifest, timeline=timeline)
    assert summary["track_counts"]["script"] == 3
    assert summary["track_counts"]["storyboards"] == 1
    assert summary["track_counts"]["animatics"] == 1

    gaps = unresolved_gaps_by_fallback_layer(manifest, timeline=timeline)
    assert gaps["unresolved_scenes"] == []

    time_range = best_for_time_range(
        manifest,
        timeline,
        start_time_seconds=30.0,
        end_time_seconds=130.0,
    )
    assert len(time_range["overlapping_scenes"]) == 3


@pytest.mark.unit
def test_track_operations_and_versioning_behavior(tmp_path: Path) -> None:
    scene_ids = ["scene_001"]
    store = _seed_scene_artifacts(tmp_path, scene_ids)
    timeline_ref, timeline = _seed_timeline_artifact(store, scene_ids)
    manifest = build_track_manifest(timeline=timeline, timeline_ref=timeline_ref, store=store)

    scene_ref = store.list_versions("scene", "scene_001")[-1]
    manifest2 = add_track_entry(
        manifest,
        TrackEntry(
            track_type="storyboards",
            scene_id="scene_001",
            artifact_ref=scene_ref,
            priority=200,
            status="available",
        ),
    )
    assert len(manifest2.entries) == len(manifest.entries) + 1

    manifest3 = update_track_entry(
        manifest2,
        track_type="storyboards",
        scene_id="scene_001",
        updates={"status": "failed"},
    )
    resolved = best_for_scene(manifest3, scene_id="scene_001")
    assert resolved["selected_track_type"] == "script"

    manifest4 = remove_track_entries(manifest3, track_type="storyboards", scene_id="scene_001")
    assert len(manifest4.entries) == len(manifest3.entries) - 1

    ref1 = store.save_artifact(
        artifact_type="track_manifest",
        entity_id="project",
        data=manifest3.model_dump(mode="json"),
        metadata=ArtifactMetadata(
            lineage=[timeline_ref],
            intent="seed track manifest",
            rationale="unit test versioning",
            confidence=1.0,
            source="code",
        ),
    )
    ref2 = store.save_artifact(
        artifact_type="track_manifest",
        entity_id="project",
        data=manifest4.model_dump(mode="json"),
        metadata=ArtifactMetadata(
            lineage=[timeline_ref],
            intent="updated track manifest",
            rationale="unit test versioning",
            confidence=1.0,
            source="code",
        ),
    )
    assert ref2.version == ref1.version + 1


@pytest.mark.unit
def test_run_module_builds_track_manifest_payload(tmp_path: Path) -> None:
    scene_ids = ["scene_001", "scene_002"]
    store = _seed_scene_artifacts(tmp_path, scene_ids)
    timeline_ref, timeline = _seed_timeline_artifact(store, scene_ids)

    continuity_state_ref = store.save_artifact(
        artifact_type="continuity_state",
        entity_id="character_alpha_scene_001",
        data={
            "entity_type": "character",
            "entity_id": "alpha",
            "scene_id": "scene_001",
            "story_time_position": 1,
            "properties": [],
            "change_events": [],
            "overall_confidence": 0.8,
        },
        metadata=ArtifactMetadata(
            lineage=[timeline.entries[0].scene_ref],
            intent="continuity",
            rationale="unit test seed",
            confidence=0.8,
            source="code",
        ),
    )

    continuity_index = {
        "timelines": {
            "character:alpha": {
                "entity_type": "character",
                "entity_id": "alpha",
                "states": ["character_alpha_scene_001"],
                "gaps": [],
            }
        },
        "total_gaps": 0,
        "overall_continuity_score": 0.9,
    }
    continuity_index_ref = store.save_artifact(
        artifact_type="continuity_index",
        entity_id="project",
        data=continuity_index,
        metadata=ArtifactMetadata(
            lineage=[continuity_state_ref],
            intent="continuity index",
            rationale="unit test seed",
            confidence=0.9,
            source="code",
        ),
    )

    result = run_module(
        inputs={"timeline": timeline.model_dump(mode="json"), "continuity_index": continuity_index},
        params={},
        context={"project_dir": str(tmp_path), "run_id": "r", "stage_id": "tracks"},
    )

    artifact = result["artifacts"][0]
    assert artifact["artifact_type"] == "track_manifest"
    assert artifact["entity_id"] == "project"
    assert artifact["data"]["timeline_ref"]["version"] == timeline_ref.version
    assert artifact["data"]["track_fill_counts"]["script"] == 2
    assert artifact["data"]["track_fill_counts"]["continuity_events"] == 1

    lineage = [
        ArtifactRef.model_validate(item)
        for item in artifact["metadata"]["lineage"]
    ]
    assert any(ref.artifact_type == "timeline" for ref in lineage)
    assert any(ref.artifact_type == "continuity_index" for ref in lineage)
    assert any(ref.artifact_type == "continuity_state" for ref in lineage)
    assert continuity_index_ref.version >= 1
