from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import pytest

from cine_forge.artifacts import ArtifactStore
from cine_forge.modules.shot_planning.shot_plan_v1.main import (
    _build_scene_context,
    _build_scene_prompt,
    _character_bible_map,
    _character_performance_map,
    _CoverageResponse,
    _scene_map,
    _ScenePlanResponse,
    _ShotResponse,
    run_module,
)
from cine_forge.schemas import (
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
        rationale="unit test seed",
        confidence=1.0,
        source="code",
    )


def _save(
    store: ArtifactStore,
    artifact_type: str,
    entity_id: str | None,
    data: dict[str, Any],
) -> ArtifactRef:
    return store.save_artifact(
        artifact_type=artifact_type,
        entity_id=entity_id,
        data=data,
        metadata=_metadata(f"seed {artifact_type}"),
    )


def _seed_shot_planning_inputs(
    tmp_path: Path,
    *,
    scene_count: int = 2,
) -> tuple[Path, dict[str, Any]]:
    project_dir = tmp_path / "project"
    project_dir.mkdir(parents=True, exist_ok=True)
    store = ArtifactStore(project_dir=project_dir)

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

    scene_specs = [
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
            "elements": [
                {"element_type": "action", "content": "MARA studies the console."},
                {"element_type": "character", "content": "MARA"},
                {"element_type": "dialogue", "content": "We can still stop this."},
                {"element_type": "character", "content": "OWEN"},
                {"element_type": "dialogue", "content": "No. We let it run."},
            ],
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
            "elements": [
                {"element_type": "action", "content": "Wind tears at Mara's coat."},
                {"element_type": "character", "content": "MARA"},
                {"element_type": "dialogue", "content": "Then tell me what it cost."},
            ],
        },
    ][:scene_count]

    scene_entries: list[dict[str, Any]] = []
    scene_refs: dict[str, ArtifactRef] = {}
    for spec in scene_specs:
        scene_payload = {
            **spec,
            "narrative_beats": [],
            "tone_shifts": [],
            "inferences": [],
            "provenance": [],
            "confidence": 1.0,
        }
        scene_entries.append({key: value for key, value in spec.items() if key != "elements"})
        scene_refs[spec["scene_id"]] = _save(
            store,
            "scene",
            spec["scene_id"],
            scene_payload,
        )

    for bible in [
        {
            "character_id": "mara",
            "name": "MARA",
            "description": "A systems engineer running on resolve and exhaustion.",
            "inferred_traits": [{"trait": "Guarded"}, {"trait": "Relentless"}],
        },
        {
            "character_id": "owen",
            "name": "OWEN",
            "description": "A pragmatist willing to accept collateral damage.",
            "inferred_traits": [{"trait": "Cold"}, {"trait": "Calculating"}],
        },
    ]:
        _save(store, "character_bible", bible["character_id"], bible)

    rhythm_and_flow = [
        {
            "scene_id": "scene_001",
            "scene_function": "confrontation",
            "coverage_priority": "master plus sharp reactions",
            "transition_strategy": "hard cut into aftermath",
        },
        {
            "scene_id": "scene_002",
            "scene_function": "aftershock",
            "coverage_priority": "isolated singles",
            "transition_strategy": "hold on silence",
        },
    ][:scene_count]
    look_and_feel = [
        {
            "scene_id": "scene_001",
            "lighting_concept": "Cold practical spill with hard monitor highlights.",
            "camera_personality": "Measured pushes with rigid framing.",
        },
        {
            "scene_id": "scene_002",
            "lighting_concept": "Blue dawn haze and exposed sky.",
            "camera_personality": "Wind-buffeted handheld restraint.",
        },
    ][:scene_count]
    sound_and_music = [
        {
            "scene_id": "scene_001",
            "ambient_environment": "Electrical hum and distant rain.",
            "music_intent": "No score until the decision lands.",
        },
        {
            "scene_id": "scene_002",
            "ambient_environment": "Open-air wind and city rumble.",
            "music_intent": "Let silence dominate the beat.",
        },
    ][:scene_count]

    for payload in rhythm_and_flow:
        _save(store, "rhythm_and_flow", payload["scene_id"], payload)
    for payload in look_and_feel:
        _save(store, "look_and_feel", payload["scene_id"], payload)
    for payload in sound_and_music:
        _save(store, "sound_and_music", payload["scene_id"], payload)

    intent_mood = {
        "scope": "project",
        "scene_id": None,
        "mood_descriptors": ["tense", "spent", "wind-scoured"],
        "reference_films": ["Sicario (2015)", "Michael Clayton (2007)"],
        "style_preset_id": None,
        "natural_language_intent": "Hold pressure inside scenes, then let silence expose cost.",
        "user_approved": False,
    }
    _save(store, "intent_mood", "project", intent_mood)
    story_world = {
        "character_design_baselines": ["mara", "owen"],
        "location_design_baselines": ["lab", "roof"],
        "visual_motif_annotations": [
            {
                "motif_name": "Threshold Glass",
                "description": (
                    "Transparent barriers mark the line between control and consequence."
                ),
                "scope": "location",
                "entity_id": "lab",
                "scene_refs": ["scene_001"],
            }
        ],
        "audio_motif_annotations": [
            {
                "motif_name": "Held Silence",
                "description": "Silence lands once the moral price is undeniable.",
                "scope": "scene",
                "entity_id": "scene_002",
                "scene_refs": ["scene_002"],
            }
        ],
    }
    _save(store, "story_world", "project", story_world)

    continuity_states = [
        {
            "artifact_type": "continuity_state",
            "entity_id": "character_mara_scene_001",
            "data": {
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
        },
        {
            "artifact_type": "continuity_state",
            "entity_id": "character_owen_scene_001",
            "data": {
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
        },
        {
            "artifact_type": "continuity_state",
            "entity_id": "location_lab_scene_001",
            "data": {
                "entity_type": "location",
                "entity_id": "lab",
                "scene_id": "scene_001",
                "story_time_position": 1,
                "properties": [
                    {"key": "lighting", "value": "flickering fluorescents", "confidence": 0.9}
                ],
                "change_events": [],
                "overall_confidence": 0.9,
            },
        },
        {
            "artifact_type": "continuity_state",
            "entity_id": "character_mara_scene_002",
            "data": {
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
        },
        {
            "artifact_type": "continuity_state",
            "entity_id": "location_roof_scene_002",
            "data": {
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
        },
    ]
    if scene_count == 1:
        continuity_states = continuity_states[:3]

    continuity_index = {
        "timelines": {
            "character:mara": {
                "entity_type": "character",
                "entity_id": "mara",
                "states": ["character_mara_scene_001", "character_mara_scene_002"][:scene_count],
                "gaps": [],
            },
            "character:owen": {
                "entity_type": "character",
                "entity_id": "owen",
                "states": (
                    ["character_owen_scene_001"]
                    if scene_count == 1
                    else ["character_owen_scene_001"]
                ),
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
                "states": ["location_roof_scene_002"] if scene_count > 1 else [],
                "gaps": [],
            },
        },
        "total_gaps": 0,
        "overall_continuity_score": 0.95,
    }
    if scene_count == 1:
        continuity_index["timelines"]["character:mara"]["states"] = ["character_mara_scene_001"]
        continuity_index["timelines"]["location:roof"]["states"] = []

    for payload in continuity_states:
        _save(store, payload["artifact_type"], payload["entity_id"], payload["data"])
    _save(store, "continuity_index", "project", continuity_index)

    timeline = Timeline(
        entries=[
            TimelineEntry(
                scene_id=entry["scene_id"],
                scene_ref=scene_refs[entry["scene_id"]],
                script_position=idx,
                edit_position=idx,
                story_position=idx,
                estimated_duration_seconds=60.0,
            )
            for idx, entry in enumerate(scene_entries, start=1)
        ],
        total_scenes=len(scene_entries),
        estimated_runtime_seconds=float(len(scene_entries) * 60),
    )
    timeline_ref = _save(
        store,
        "timeline",
        "project",
        timeline.model_dump(mode="json"),
    )
    manifest_entries = [
        TrackEntry(
            track_type="script",
            scene_id=entry["scene_id"],
            artifact_ref=scene_refs[entry["scene_id"]],
            priority=400,
            status="available",
        )
        for entry in scene_entries
    ]
    manifest = TrackManifest(
        timeline_ref=timeline_ref,
        entries=manifest_entries,
        track_fill_counts={"script": len(manifest_entries)},
    )
    _save(store, "track_manifest", "project", manifest.model_dump(mode="json"))

    inputs = {
        "normalize": {
            "title": "Pressure Test",
            "script_text": script_text,
            "line_count": len(script_text.splitlines()),
            "scene_count": len(scene_entries),
        },
        "scene_index": {
            "total_scenes": len(scene_entries),
            "unique_locations": sorted({entry["location"] for entry in scene_entries}),
            "unique_characters": ["MARA", "OWEN"],
            "estimated_runtime_minutes": float(len(scene_entries)),
            "scenes_passed_qa": len(scene_entries),
            "scenes_need_review": 0,
            "entries": scene_entries,
        },
        "timeline": timeline.model_dump(mode="json"),
        "track_manifest": manifest.model_dump(mode="json"),
        "continuity_index": continuity_index,
        "rhythm_and_flow": rhythm_and_flow,
        "look_and_feel": look_and_feel,
        "sound_and_music": sound_and_music,
        "character_bible": [
            store.load_artifact(store.list_versions("character_bible", "mara")[-1]).data,
            store.load_artifact(store.list_versions("character_bible", "owen")[-1]).data,
        ],
        "character_and_performance": [],
        "intent_mood": intent_mood,
        "story_world": story_world,
    }
    return project_dir, inputs


def _scene_context_for_first_scene(tmp_path: Path):
    project_dir, inputs = _seed_shot_planning_inputs(tmp_path, scene_count=1)
    store = ArtifactStore(project_dir=project_dir)
    timeline = Timeline.model_validate(inputs["timeline"])
    perf_by_scene, perf_ref_map = _character_performance_map(
        inputs["character_and_performance"]
    )
    scene_context = _build_scene_context(
        scene_entry=inputs["scene_index"]["entries"][0],
        canonical_script=inputs["normalize"],
        timeline=timeline,
        store=store,
        rhythm_by_scene=_scene_map(inputs["rhythm_and_flow"]),
        look_by_scene=_scene_map(inputs["look_and_feel"]),
        sound_by_scene=_scene_map(inputs["sound_and_music"]),
        story_world=inputs["story_world"],
        intent_mood=inputs["intent_mood"],
        char_bible_map=_character_bible_map(inputs["character_bible"]),
        perf_by_scene=perf_by_scene,
        perf_ref_map=perf_ref_map,
        continuity_index=inputs["continuity_index"],
    )
    return scene_context


@pytest.mark.unit
def test_run_module_mock_updates_timeline_and_tracks(tmp_path: Path) -> None:
    project_dir, inputs = _seed_shot_planning_inputs(tmp_path, scene_count=2)

    result = run_module(
        inputs=inputs,
        params={"work_model": "mock", "skip_qa": True, "concurrency": 1},
        context={"project_dir": str(project_dir), "run_id": "r", "stage_id": "shot_planning"},
    )

    shot_plan_artifacts = [
        artifact for artifact in result["artifacts"] if artifact["artifact_type"] == "shot_plan"
    ]
    assert len(shot_plan_artifacts) == 2
    assert result["cost"]["model"] == "mock"

    for artifact in shot_plan_artifacts:
        plan = ShotPlan.model_validate(artifact["data"])
        assert plan.coverage_strategy.adequacy_check.verdict == "adequate"
        assert len(plan.shots) == 3
        assert artifact["exclude_upstream_lineage_types"] == ["timeline", "track_manifest"]
        assert artifact["metadata"]["annotations"]["shot_count"] == 3
        for shot in plan.shots:
            assert shot.continuity_state_refs
            assert shot.upstream_artifact_refs

    timeline_artifact = next(
        artifact for artifact in result["artifacts"] if artifact["artifact_type"] == "timeline"
    )
    updated_timeline = Timeline.model_validate(timeline_artifact["data"])
    assert [entry.shot_count for entry in updated_timeline.entries] == [3, 3]
    assert all(entry.shot_ids for entry in updated_timeline.entries)

    manifest_artifact = next(
        artifact
        for artifact in result["artifacts"]
        if artifact["artifact_type"] == "track_manifest"
    )
    manifest = TrackManifest.model_validate(manifest_artifact["data"])
    shot_entries = [entry for entry in manifest.entries if entry.track_type == "shots"]
    assert len(shot_entries) == 6
    assert all(entry.shot_id for entry in shot_entries)
    assert manifest.timeline_ref.version == 2
    assert manifest.track_fill_counts["shots"] == 6


@pytest.mark.unit
def test_run_module_mock_tolerates_missing_direction_inputs(tmp_path: Path) -> None:
    project_dir, inputs = _seed_shot_planning_inputs(tmp_path, scene_count=1)
    inputs = {
        **inputs,
        "rhythm_and_flow": [],
        "look_and_feel": [],
        "sound_and_music": [],
    }

    result = run_module(
        inputs=inputs,
        params={"work_model": "mock", "skip_qa": True, "concurrency": 1},
        context={"project_dir": str(project_dir), "run_id": "r", "stage_id": "shot_planning"},
    )

    shot_plan_artifact = next(
        artifact for artifact in result["artifacts"] if artifact["artifact_type"] == "shot_plan"
    )
    plan = ShotPlan.model_validate(shot_plan_artifact["data"])

    assert plan.coverage_strategy.rhythm_and_flow_intent == "No explicit notes."
    assert plan.coverage_strategy.look_and_feel_intent == "No explicit notes."
    assert plan.coverage_strategy.sound_and_music_intent == "No explicit notes."
    assert len(plan.shots) == 3


@pytest.mark.unit
def test_run_module_honors_runtime_default_model(tmp_path: Path) -> None:
    project_dir, inputs = _seed_shot_planning_inputs(tmp_path, scene_count=1)

    result = run_module(
        inputs=inputs,
        params={"skip_qa": True, "concurrency": 1},
        context={
            "project_dir": str(project_dir),
            "run_id": "r",
            "stage_id": "shot_planning",
            "runtime_params": {"default_model": "mock"},
        },
    )

    assert result["cost"]["model"] == "mock"
    shot_plan_artifacts = [
        artifact for artifact in result["artifacts"] if artifact["artifact_type"] == "shot_plan"
    ]
    assert len(shot_plan_artifacts) == 1


@pytest.mark.unit
def test_run_module_preserves_adequacy_review_from_model_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_dir, inputs = _seed_shot_planning_inputs(tmp_path, scene_count=1)

    def _fake_call_llm(**kwargs: Any) -> tuple[_ScenePlanResponse, dict[str, Any]]:
        assert "SCENE ID: scene_001" in kwargs["prompt"]
        return (
            _ScenePlanResponse(
                coverage_strategy=_CoverageResponse(
                    coverage_approach="Singles and inserts around a fragile confrontation.",
                    rhythm_and_flow_intent="Start controlled, then tighten aggressively.",
                    look_and_feel_intent="Monitor spill and rigid negative space.",
                    sound_and_music_intent="Mechanical hum under held silence.",
                    character_and_performance_notes="Mara pushes; Owen refuses to blink.",
                    coverage_patterns=["Single", "Reaction", "Insert"],
                    adequacy_verdict="Borderline",
                    adequacy_rationale="The beat works, but the console insert is essential.",
                    missing_coverage_risks=["Missing insert of the console activation."],
                    rationale="The editor needs pressure and detail coverage.",
                    alternatives_considered=["Play entirely in a master."],
                    confidence=0.86,
                ),
                shots=[
                    _ShotResponse(
                        shot_id="S001-A",
                        shot_size="Medium Two-Shot",
                        camera_angle="Eye level",
                        camera_movement="Static",
                        lens_focal_length="Normal (40-60mm)",
                        coverage_role="Two-shot",
                        characters_in_frame=["MARA", "OWEN"],
                        blocking="Hold both at the console, divided by the monitor bank.",
                        action_description="The argument begins without relief.",
                        dialogue_lines=["We can still stop this.", "No. We let it run."],
                        duration_estimate_seconds=11.0,
                        edit_intent="Establish power balance before fragmenting coverage.",
                        rationale="The edit needs shared geography before isolates.",
                        alternatives_considered=["Open on Mara alone."],
                        confidence=0.83,
                    ),
                    _ShotResponse(
                        shot_id="S001-B",
                        shot_size="Medium Close-Up",
                        camera_angle="Eye level",
                        camera_movement="Slow push",
                        lens_focal_length="Telephoto (85mm+)",
                        coverage_role="Single",
                        characters_in_frame=["MARA"],
                        point_of_view_character="MARA",
                        blocking="Mara leans into frame as she challenges Owen.",
                        action_description="Track Mara's push toward the decision point.",
                        dialogue_lines=["We can still stop this."],
                        duration_estimate_seconds=7.0,
                        edit_intent="Isolate Mara's urgency.",
                        rationale="Her emotional pressure drives the cut.",
                        alternatives_considered=["Keep Mara only in the two-shot."],
                        confidence=0.84,
                    ),
                    _ShotResponse(
                        shot_id="S001-C",
                        shot_size="Insert",
                        camera_angle="High",
                        camera_movement="Static",
                        lens_focal_length="Wide (18-35mm)",
                        coverage_role="Insert",
                        characters_in_frame=[],
                        blocking="Frame the activation switch and Mara's hovering hand.",
                        action_description="Show the console controls she could still kill.",
                        dialogue_lines=[],
                        duration_estimate_seconds=3.0,
                        edit_intent="Give the editor the missing decision detail.",
                        rationale="Without the insert, the action beat is abstract.",
                        alternatives_considered=["Stay on Mara's face only."],
                        confidence=0.88,
                    ),
                ],
            ),
            {
                "model": kwargs["model"],
                "input_tokens": 120,
                "output_tokens": 220,
                "estimated_cost_usd": 0.01,
            },
        )

    monkeypatch.setattr(
        "cine_forge.modules.shot_planning.shot_plan_v1.main.call_llm",
        _fake_call_llm,
    )

    result = run_module(
        inputs=inputs,
        params={"work_model": "fixture", "skip_qa": True, "concurrency": 1},
        context={"project_dir": str(project_dir), "run_id": "r", "stage_id": "shot_planning"},
    )

    plan_artifact = next(
        artifact for artifact in result["artifacts"] if artifact["artifact_type"] == "shot_plan"
    )
    plan = ShotPlan.model_validate(plan_artifact["data"])
    adequacy = plan.coverage_strategy.adequacy_check

    assert adequacy.verdict == "borderline"
    assert adequacy.missing_coverage_risks == ["Missing insert of the console activation."]
    assert plan.shots[-1].coverage_role == "Insert"
    assert plan.shots[-1].audit.intent == "Give the editor the missing decision detail."


@pytest.mark.unit
def test_previz_fast_prompt_profile_compacts_scene_prompt(tmp_path: Path) -> None:
    scene_context = _scene_context_for_first_scene(tmp_path)
    scene_context.rhythm_and_flow["coverage_priority"] = " ".join(
        ["master plus sharp reactions and inserts around the console beat"] * 12
    )
    scene_context.look_and_feel["camera_personality"] = " ".join(
        ["static, observational, patient camera with deliberate restrained pushes"] * 12
    )
    scene_context.sound_and_music["ambient_environment"] = " ".join(
        ["electrical hum, rain on metal, and room tone carrying tension"] * 12
    )
    scene_context.intent_mood["natural_language_intent"] = " ".join(
        ["hold pressure inside the room and let silence expose the cost of the choice"] * 12
    )

    full_prompt = _build_scene_prompt(scene_context)
    previz_prompt = _build_scene_prompt(
        scene_context,
        prompt_profile="previz_fast",
        max_shots=5,
    )

    assert "Create 3 to 8 shots only." in full_prompt
    assert "Create 3 to 5 shots only." in previz_prompt
    assert "Keep shot rationale and edit_intent to one short sentence." in previz_prompt
    assert len(previz_prompt) < len(full_prompt)
    assert len(previz_prompt) <= int(len(full_prompt) * 0.75)
    assert "..." in previz_prompt


@pytest.mark.unit
def test_scene_prompt_includes_story_world_context(tmp_path: Path) -> None:
    scene_context = _scene_context_for_first_scene(tmp_path)
    prompt = _build_scene_prompt(scene_context)

    assert "STORY WORLD:" in prompt
    assert "Threshold Glass" in prompt
    assert "Held Silence" in prompt


@pytest.mark.unit
def test_run_module_previz_fast_profile_passes_compact_prompt_and_max_tokens(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_dir, inputs = _seed_shot_planning_inputs(tmp_path, scene_count=1)
    captured: dict[str, Any] = {}

    def _fake_call_llm(**kwargs: Any) -> tuple[_ScenePlanResponse, dict[str, Any]]:
        captured["prompt"] = kwargs["prompt"]
        captured["max_tokens"] = kwargs["max_tokens"]
        return (
            _ScenePlanResponse(
                coverage_strategy=_CoverageResponse(
                    coverage_approach="Master plus a few selective singles.",
                    rhythm_and_flow_intent="Measured escalation.",
                    look_and_feel_intent="Observational, monitor-lit restraint.",
                    sound_and_music_intent="Room tone and held silence.",
                    character_and_performance_notes="Mara drives urgency; Owen resists.",
                    coverage_patterns=["Master", "Single", "Insert"],
                    adequacy_verdict="adequate",
                    adequacy_rationale="Coverage remains cuttable with the core beats visible.",
                    missing_coverage_risks=[],
                    rationale="Compact previz coverage still preserves the scene turn.",
                    alternatives_considered=[],
                    confidence=0.84,
                ),
                shots=[
                    _ShotResponse(
                        shot_id="S001-A",
                        shot_size="Wide",
                        camera_angle="Eye level",
                        camera_movement="Static",
                        lens_focal_length="35mm",
                        coverage_role="Master",
                        characters_in_frame=["MARA", "OWEN"],
                        blocking="Hold both characters at the console.",
                        action_description="Establish the confrontation geography.",
                        dialogue_lines=["We can still stop this.", "No. We let it run."],
                        duration_estimate_seconds=10.0,
                        edit_intent="Anchor the beat.",
                        rationale="The cut needs clean geography first.",
                        alternatives_considered=[],
                        confidence=0.83,
                    ),
                    _ShotResponse(
                        shot_id="S001-B",
                        shot_size="Medium Close-Up",
                        camera_angle="Eye level",
                        camera_movement="Slow push",
                        lens_focal_length="50mm",
                        coverage_role="Single",
                        characters_in_frame=["MARA"],
                        blocking="Lean Mara toward the switch.",
                        action_description="Push into her urgency.",
                        dialogue_lines=["We can still stop this."],
                        duration_estimate_seconds=6.0,
                        edit_intent="Isolate urgency.",
                        rationale="Her pressure shapes the turn.",
                        alternatives_considered=[],
                        confidence=0.82,
                    ),
                    _ShotResponse(
                        shot_id="S001-C",
                        shot_size="Insert",
                        camera_angle="High",
                        camera_movement="Static",
                        lens_focal_length="85mm",
                        coverage_role="Insert",
                        characters_in_frame=[],
                        blocking="Frame the switch and hovering hand.",
                        action_description="Show the irreversible choice.",
                        dialogue_lines=[],
                        duration_estimate_seconds=3.0,
                        edit_intent="Clarify the choice.",
                        rationale="The action beat needs visible detail.",
                        alternatives_considered=[],
                        confidence=0.85,
                    ),
                ],
            ),
            {
                "model": kwargs["model"],
                "input_tokens": 100,
                "output_tokens": 200,
                "estimated_cost_usd": 0.01,
            },
        )

    monkeypatch.setattr(
        "cine_forge.modules.shot_planning.shot_plan_v1.main.call_llm",
        _fake_call_llm,
    )

    result = run_module(
        inputs=inputs,
        params={
            "work_model": "fixture",
            "skip_qa": True,
            "concurrency": 1,
            "prompt_profile": "previz_fast",
            "max_tokens": 2200,
        },
        context={"project_dir": str(project_dir), "run_id": "r", "stage_id": "shot_planning"},
    )

    assert result["cost"]["model"] == "fixture"
    assert captured["max_tokens"] == 2200
    assert "Create 3 to 5 shots only." in captured["prompt"]
    assert "Keep shot rationale and edit_intent to one short sentence." in captured["prompt"]


@pytest.mark.unit
def test_dynamic_import_rebuilds_scene_plan_response_schema() -> None:
    module_path = (
        Path(__file__).resolve().parents[2]
        / "src/cine_forge/modules/shot_planning/shot_plan_v1/main.py"
    )
    spec = importlib.util.spec_from_file_location("shot_plan_v1_dynamic_test", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    schema = module._ScenePlanResponse.model_json_schema()

    assert schema["type"] == "object"
    assert "coverage_strategy" in schema["properties"]
    assert "shots" in schema["properties"]
