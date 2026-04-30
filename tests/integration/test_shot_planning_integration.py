from __future__ import annotations

from pathlib import Path

import pytest

from cine_forge.driver.engine import DriverEngine
from cine_forge.schemas import (
    ArtifactHealth,
    ArtifactMetadata,
    ArtifactRef,
    ShotPlan,
    Timeline,
    TimelineEntry,
    TrackEntry,
    TrackManifest,
)


def _metadata(intent: str) -> ArtifactMetadata:
    return ArtifactMetadata(
        lineage=[],
        intent=intent,
        rationale="integration seed",
        confidence=1.0,
        source="code",
    )


def _seed_upstream_artifacts(engine: DriverEngine) -> None:
    store = engine.store
    script_text = (
        "INT. LAB - NIGHT\n"
        "MARA studies the console.\n"
        "MARA\n"
        "We can still stop this.\n"
        "OWEN\n"
        "No. We let it run.\n"
        "\n"
        "EXT. ROOF - DAWN\n"
        "Wind tears at Mara's coat.\n"
        "MARA\n"
        "Then tell me what it cost.\n"
    )

    scene_entries = [
        {
            "scene_id": "scene_001",
            "scene_number": 1,
            "heading": "INT. LAB - NIGHT",
            "location": "LAB",
            "time_of_day": "NIGHT",
            "int_ext": "INT",
            "characters_present": ["MARA", "OWEN"],
            "characters_present_ids": ["mara", "owen"],
            "props_mentioned": ["console"],
            "tone_mood": "tense",
            "source_span": {"start_line": 1, "end_line": 6},
        },
        {
            "scene_id": "scene_002",
            "scene_number": 2,
            "heading": "EXT. ROOF - DAWN",
            "location": "ROOF",
            "time_of_day": "DAWN",
            "int_ext": "EXT",
            "characters_present": ["MARA"],
            "characters_present_ids": ["mara"],
            "props_mentioned": [],
            "tone_mood": "bleak",
            "source_span": {"start_line": 8, "end_line": 11},
        },
    ]

    scene_refs: dict[str, ArtifactRef] = {}
    scene_payloads = {
        "scene_001": {
            **scene_entries[0],
            "elements": [
                {"element_type": "action", "content": "MARA studies the console."},
                {"element_type": "character", "content": "MARA"},
                {"element_type": "dialogue", "content": "We can still stop this."},
                {"element_type": "character", "content": "OWEN"},
                {"element_type": "dialogue", "content": "No. We let it run."},
            ],
            "narrative_beats": [],
            "tone_shifts": [],
            "inferences": [],
            "provenance": [],
            "confidence": 1.0,
        },
        "scene_002": {
            **scene_entries[1],
            "elements": [
                {"element_type": "action", "content": "Wind tears at Mara's coat."},
                {"element_type": "character", "content": "MARA"},
                {"element_type": "dialogue", "content": "Then tell me what it cost."},
            ],
            "narrative_beats": [],
            "tone_shifts": [],
            "inferences": [],
            "provenance": [],
            "confidence": 1.0,
        },
    }
    for scene_id, payload in scene_payloads.items():
        scene_refs[scene_id] = store.save_artifact(
            artifact_type="scene",
            entity_id=scene_id,
            data=payload,
            metadata=_metadata(f"seed {scene_id}"),
        )

    store.save_artifact(
        artifact_type="canonical_script",
        entity_id="project",
        data={
            "title": "Pressure Test",
            "script_text": script_text,
            "line_count": len(script_text.splitlines()),
            "scene_count": 2,
        },
        metadata=_metadata("seed canonical script"),
    )
    store.save_artifact(
        artifact_type="scene_index",
        entity_id="project",
        data={
            "total_scenes": 2,
            "unique_locations": ["LAB", "ROOF"],
            "unique_characters": ["MARA", "OWEN"],
            "estimated_runtime_minutes": 2.0,
            "scenes_passed_qa": 2,
            "scenes_need_review": 0,
            "entries": scene_entries,
        },
        metadata=_metadata("seed scene index"),
    )

    for bible in [
        {
            "character_id": "mara",
            "name": "MARA",
            "description": "A systems engineer refusing collapse.",
            "inferred_traits": [{"trait": "Guarded"}],
        },
        {
            "character_id": "owen",
            "name": "OWEN",
            "description": "A pragmatist who has already compromised.",
            "inferred_traits": [{"trait": "Cold"}],
        },
    ]:
        store.save_artifact(
            artifact_type="character_bible",
            entity_id=bible["character_id"],
            data=bible,
            metadata=_metadata(f"seed {bible['character_id']} bible"),
        )

    for artifact_type, payloads in {
        "rhythm_and_flow": [
            {
                "scene_id": "scene_001",
                "scene_function": "confrontation",
                "coverage_priority": "master plus selective pressure coverage",
            },
            {
                "scene_id": "scene_002",
                "scene_function": "aftershock",
                "coverage_priority": "singles against empty space",
            },
        ],
        "look_and_feel": [
            {
                "scene_id": "scene_001",
                "lighting_concept": "Cold monitor spill and deep falloff.",
            },
            {
                "scene_id": "scene_002",
                "lighting_concept": "Blue dawn haze and hard wind.",
            },
        ],
        "sound_and_music": [
            {
                "scene_id": "scene_001",
                "ambient_environment": "Electrical hum and distant rain.",
            },
            {
                "scene_id": "scene_002",
                "ambient_environment": "Open wind and city rumble.",
            },
        ],
    }.items():
        for payload in payloads:
            store.save_artifact(
                artifact_type=artifact_type,
                entity_id=payload["scene_id"],
                data=payload,
                metadata=_metadata(f"seed {artifact_type} {payload['scene_id']}"),
            )

    store.save_artifact(
        artifact_type="intent_mood",
        entity_id="project",
        data={
            "scope": "project",
            "scene_id": None,
            "mood_descriptors": ["tense", "spent", "wind-scoured"],
            "reference_films": ["Sicario (2015)", "Michael Clayton (2007)"],
            "style_preset_id": None,
            "natural_language_intent": "Pressure first, silence after the choice.",
            "user_approved": False,
        },
        metadata=_metadata("seed intent mood"),
    )

    for entity_id, payload in {
        "character_mara_scene_001": {
            "entity_type": "character",
            "entity_id": "mara",
            "scene_id": "scene_001",
            "story_time_position": 1,
            "properties": [
                {"key": "wardrobe", "value": "navy rain jacket", "confidence": 0.95}
            ],
            "change_events": [],
            "overall_confidence": 0.95,
        },
        "character_owen_scene_001": {
            "entity_type": "character",
            "entity_id": "owen",
            "scene_id": "scene_001",
            "story_time_position": 1,
            "properties": [
                {"key": "wardrobe", "value": "dark coat", "confidence": 0.93}
            ],
            "change_events": [],
            "overall_confidence": 0.93,
        },
        "location_lab_scene_001": {
            "entity_type": "location",
            "entity_id": "lab",
            "scene_id": "scene_001",
            "story_time_position": 1,
            "properties": [
                {
                    "key": "lighting",
                    "value": "flickering fluorescents",
                    "confidence": 0.9,
                }
            ],
            "change_events": [],
            "overall_confidence": 0.9,
        },
        "character_mara_scene_002": {
            "entity_type": "character",
            "entity_id": "mara",
            "scene_id": "scene_002",
            "story_time_position": 2,
            "properties": [
                {"key": "wardrobe", "value": "coat whipped by wind", "confidence": 0.92}
            ],
            "change_events": [],
            "overall_confidence": 0.92,
        },
        "location_roof_scene_002": {
            "entity_type": "location",
            "entity_id": "roof",
            "scene_id": "scene_002",
            "story_time_position": 2,
            "properties": [
                {"key": "weather", "value": "high wind", "confidence": 0.94}
            ],
            "change_events": [],
            "overall_confidence": 0.94,
        },
    }.items():
        store.save_artifact(
            artifact_type="continuity_state",
            entity_id=entity_id,
            data=payload,
            metadata=_metadata(f"seed {entity_id}"),
        )

    store.save_artifact(
        artifact_type="continuity_index",
        entity_id="project",
        data={
            "timelines": {
                "character:mara": {
                    "entity_type": "character",
                    "entity_id": "mara",
                    "states": ["character_mara_scene_001", "character_mara_scene_002"],
                    "gaps": [],
                },
                "character:owen": {
                    "entity_type": "character",
                    "entity_id": "owen",
                    "states": ["character_owen_scene_001"],
                    "gaps": [],
                },
                "location:lab": {
                    "entity_type": "location",
                    "entity_id": "lab",
                    "states": ["location_lab_scene_001"],
                    "gaps": [],
                },
                "location:roof": {
                    "entity_type": "location",
                    "entity_id": "roof",
                    "states": ["location_roof_scene_002"],
                    "gaps": [],
                },
            },
            "total_gaps": 0,
            "overall_continuity_score": 0.95,
        },
        metadata=_metadata("seed continuity index"),
    )

    timeline = Timeline(
        entries=[
            TimelineEntry(
                scene_id=scene["scene_id"],
                scene_ref=scene_refs[scene["scene_id"]],
                script_position=idx,
                edit_position=idx,
                story_position=idx,
                estimated_duration_seconds=60.0,
            )
            for idx, scene in enumerate(scene_entries, start=1)
        ],
        total_scenes=2,
        estimated_runtime_seconds=120.0,
    )
    timeline_ref = store.save_artifact(
        artifact_type="timeline",
        entity_id="project",
        data=timeline.model_dump(mode="json"),
        metadata=_metadata("seed timeline"),
    )
    manifest = TrackManifest(
        timeline_ref=timeline_ref,
        entries=[
            TrackEntry(
                track_type="script",
                scene_id=scene["scene_id"],
                artifact_ref=scene_refs[scene["scene_id"]],
                priority=400,
                status="available",
            )
            for scene in scene_entries
        ],
        track_fill_counts={"script": 2},
    )
    store.save_artifact(
        artifact_type="track_manifest",
        entity_id="project",
        data=manifest.model_dump(mode="json"),
        metadata=_metadata("seed track manifest"),
    )


@pytest.mark.integration
def test_shot_planning_recipe_builds_plans_and_updates_project_artifacts(
    tmp_path: Path,
) -> None:
    workspace_root = Path(__file__).resolve().parents[2]
    engine = DriverEngine(workspace_root=workspace_root, project_dir=tmp_path / "project")
    _seed_upstream_artifacts(engine)

    state = engine.run(
        recipe_path=workspace_root / "configs" / "recipes" / "recipe-shot-planning.yaml",
        run_id="integration-shot-planning",
        force=True,
        runtime_params={"default_model": "mock", "work_model": "mock"},
    )

    assert state["stages"]["shot_planning"]["status"] == "done"

    refs = [
        ArtifactRef.model_validate(item)
        for item in state["stages"]["shot_planning"]["artifact_refs"]
    ]
    shot_refs = [ref for ref in refs if ref.artifact_type == "shot_plan"]
    timeline_ref = next(ref for ref in refs if ref.artifact_type == "timeline")
    manifest_ref = next(ref for ref in refs if ref.artifact_type == "track_manifest")

    assert len(shot_refs) == 2
    assert timeline_ref.version >= 2
    assert manifest_ref.version >= 2

    first_plan_artifact = engine.store.load_artifact(shot_refs[0])
    first_plan = ShotPlan.model_validate(first_plan_artifact.data)
    lineage_types = {ref.artifact_type for ref in first_plan_artifact.metadata.lineage}

    assert len(first_plan.shots) == 3
    assert first_plan.coverage_strategy.adequacy_check.verdict == "adequate"
    assert {
        "scene",
        "rhythm_and_flow",
        "look_and_feel",
        "sound_and_music",
        "continuity_state",
    }.issubset(lineage_types)
    assert "timeline" not in lineage_types
    assert "track_manifest" not in lineage_types
    assert engine.store.graph.get_health(shot_refs[0]) in {
        ArtifactHealth.VALID,
        ArtifactHealth.CONFIRMED_VALID,
        None,
    }
    assert engine.store.graph.get_health(timeline_ref) in {
        ArtifactHealth.VALID,
        ArtifactHealth.CONFIRMED_VALID,
        None,
    }
    timeline_lineage_types = {
        ref.artifact_type
        for ref in engine.store.load_artifact(timeline_ref).metadata.lineage
    }
    assert "shot_plan" in timeline_lineage_types
    assert "track_manifest" not in timeline_lineage_types

    timeline = Timeline.model_validate(engine.store.load_artifact(timeline_ref).data)
    assert [entry.shot_count for entry in timeline.entries] == [3, 3]

    manifest = TrackManifest.model_validate(engine.store.load_artifact(manifest_ref).data)
    shot_entries = [entry for entry in manifest.entries if entry.track_type == "shots"]
    assert len(shot_entries) == 6
    assert all(entry.artifact_ref.artifact_type == "shot_plan" for entry in shot_entries)
