from __future__ import annotations

import io
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from cine_forge.artifacts import ArtifactStore
from cine_forge.schemas import (
    ArtifactMetadata,
    CoverageAdequacyCheck,
    CoverageStrategy,
    PlanningAudit,
    ProjectConfig,
    ShotDefinition,
    ShotPlan,
    Timeline,
    TimelineEntry,
    TrackEntry,
    TrackManifest,
)


def metadata(intent: str) -> ArtifactMetadata:
    return ArtifactMetadata(
        lineage=[],
        intent=intent,
        rationale="storyboard test seed",
        confidence=1.0,
        source="code",
    )


def save_artifact(
    store: ArtifactStore,
    artifact_type: str,
    entity_id: str | None,
    data: dict[str, Any],
) -> None:
    store.save_artifact(
        artifact_type=artifact_type,
        entity_id=entity_id,
        data=data,
        metadata=metadata(f"seed {artifact_type}"),
    )


def reference_raster_bytes(label: str, *, accent: tuple[int, int, int]) -> bytes:
    buffer = io.BytesIO()
    image = Image.new("RGB", (640, 360), color=(18, 24, 38))
    draw = ImageDraw.Draw(image)
    draw.rectangle((28, 28, 612, 332), outline=accent, width=6)
    draw.text((56, 68), "Reference", fill=(255, 255, 255))
    draw.text((56, 118), label, fill=accent)
    image.save(buffer, format="JPEG", quality=90)
    return buffer.getvalue()


def seed_storyboard_project(
    tmp_path: Path,
    *,
    scene_count: int = 2,
    storyboard_style: str | None = None,
) -> dict[str, Any]:
    project_dir = tmp_path / "project"
    project_dir.mkdir(parents=True, exist_ok=True)
    store = ArtifactStore(project_dir=project_dir)

    scenes = [
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
                {"element_type": "action", "content": "Mara studies the console."},
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

    scene_refs: dict[str, Any] = {}
    for scene in scenes:
        scene_payload = {
            **scene,
            "narrative_beats": [],
            "tone_shifts": [],
            "inferences": [],
            "provenance": [],
            "confidence": 1.0,
        }
        scene_refs[scene["scene_id"]] = store.save_artifact(
            artifact_type="scene",
            entity_id=scene["scene_id"],
            data=scene_payload,
            metadata=metadata("seed scene"),
        )

    script_lines: list[str] = []
    line_number = 1
    scene_index_entries: list[dict[str, Any]] = []
    for scene in scenes:
        scene_start = line_number
        script_lines.append(scene["heading"])
        line_number += 1
        for element in scene["elements"]:
            script_lines.append(str(element["content"]))
            line_number += 1
        script_lines.append("")
        scene_index_entries.append(
            {
                "scene_id": scene["scene_id"],
                "scene_number": scene["scene_number"],
                "heading": scene["heading"],
                "location": scene["location"],
                "time_of_day": scene["time_of_day"],
                "characters_present": scene["characters_present"],
                "characters_present_ids": scene["characters_present_ids"],
                "props_mentioned": scene["props_mentioned"],
                "source_span": {
                    "start_line": scene_start,
                    "end_line": line_number - 1,
                },
                "tone_mood": scene["tone_mood"],
            }
        )
        line_number += 1
    save_artifact(
        store,
        "canonical_script",
        "project",
        {"title": "Pressure Test", "script_text": "\n".join(script_lines)},
    )
    save_artifact(
        store,
        "scene_index",
        "project",
        {
            "total_scenes": len(scenes),
            "unique_locations": sorted({scene["location"] for scene in scenes}),
            "unique_characters": sorted(
                {
                    character
                    for scene in scenes
                    for character in scene["characters_present"]
                }
            ),
            "estimated_runtime_minutes": float(len(scenes)),
            "scenes_passed_qa": len(scenes),
            "scenes_need_review": 0,
            "entries": scene_index_entries,
        },
    )

    project_config = ProjectConfig(
        title="Pressure Test",
        format="screenplay",
        genre=["thriller"],
        tone=["tense", "bleak"],
        estimated_duration_minutes=2.0,
        primary_characters=["mara"],
        supporting_characters=["owen"],
        location_count=2,
        locations_summary=["lab", "roof"],
        target_audience="adults",
        aspect_ratio="2.39:1",
        production_mode="ai_generated",
        production_format="live_action",
        storyboard_style=storyboard_style,
        human_control_mode="advisory",
        style_packs={},
        budget_cap_usd=250.0,
        default_model="claude-sonnet-4-6",
        confirmed=True,
    )
    save_artifact(store, "project_config", "project", project_config.model_dump(mode="json"))

    characters = [
        {
            "character_id": "mara",
            "name": "MARA",
            "aliases": [],
            "description": "A systems engineer running on resolve and exhaustion.",
            "prominence": "primary",
            "explicit_evidence": [],
            "inferred_traits": [
                {
                    "trait": "wardrobe",
                    "value": "navy rain jacket",
                    "confidence": 0.95,
                    "rationale": "Observed across key scenes.",
                }
            ],
            "scene_presence": [scene["scene_id"] for scene in scenes],
            "dialogue_summary": "Pushes for accountability under pressure.",
            "narrative_role": "protagonist",
            "narrative_role_confidence": 0.96,
            "relationships": [],
            "overall_confidence": 0.96,
        },
        {
            "character_id": "owen",
            "name": "OWEN",
            "aliases": [],
            "description": "A pragmatist willing to accept collateral damage.",
            "prominence": "secondary",
            "explicit_evidence": [],
            "inferred_traits": [
                {
                    "trait": "wardrobe",
                    "value": "dark wool coat",
                    "confidence": 0.93,
                    "rationale": "Observed in the confrontation sequence.",
                }
            ],
            "scene_presence": ["scene_001"],
            "dialogue_summary": "Accepts the moral cost of the plan.",
            "narrative_role": "supporting",
            "narrative_role_confidence": 0.9,
            "relationships": [],
            "overall_confidence": 0.92,
        },
    ]
    for character in characters[: max(scene_count, 1)]:
        save_artifact(
            store,
            "character_bible",
            character["character_id"],
            character,
        )

    locations = [
        {
            "location_id": "lab",
            "name": "LAB",
            "aliases": [],
            "description": "A humming control lab washed in monitor glow and hard practical spill.",
            "physical_traits": ["monitor banks", "steel tables", "wet concrete floor"],
            "scene_presence": ["scene_001"],
            "narrative_significance": "Decision chamber for the moral break.",
            "overall_confidence": 0.94,
        },
        {
            "location_id": "roof",
            "name": "ROOF",
            "aliases": [],
            "description": "An exposed rooftop with open sky, wind, and a dangerous city drop.",
            "physical_traits": ["roof edge", "wind-swept coat", "cold dawn light"],
            "scene_presence": ["scene_002"],
            "narrative_significance": "Aftermath and reckoning space.",
            "overall_confidence": 0.95,
        },
    ]
    for location in locations[:scene_count]:
        save_artifact(store, "location_bible", location["location_id"], location)

    look_and_feel = [
        {
            "scene_id": "scene_001",
            "lighting_concept": "Cold practical spill with hard monitor highlights.",
            "color_palette": "Steel blue, sickly green, and clipped white highlights.",
            "composition_philosophy": "Use monitor banks to divide the frame and isolate Mara.",
            "camera_personality": "Measured pushes with rigid framing.",
            "production_design_notes": "Keep the console bank dominant in the foreground.",
            "aspect_ratio_override": "2.39:1",
        },
        {
            "scene_id": "scene_002",
            "lighting_concept": "Blue dawn haze and exposed sky.",
            "color_palette": "Slate blue, pale skin, and wind-burned highlights.",
            "composition_philosophy": "Lean into negative space and the edge drop.",
            "camera_personality": "Wind-buffeted handheld restraint.",
            "production_design_notes": "Show the empty skyline behind Mara.",
            "aspect_ratio_override": "16:9",
        },
    ][:scene_count]
    for payload in look_and_feel:
        save_artifact(store, "look_and_feel", payload["scene_id"], payload)

    intent_mood = {
        "scope": "project",
        "scene_id": None,
        "mood_descriptors": ["tense", "spent", "wind-scoured"],
        "reference_films": ["Sicario (2015)", "Michael Clayton (2007)"],
        "style_preset_id": None,
        "natural_language_intent": "Hold pressure inside scenes, then let silence expose cost.",
        "user_approved": False,
    }
    save_artifact(store, "intent_mood", "project", intent_mood)

    continuity_refs: dict[str, Any] = {}
    continuity_payloads = [
        {
            "entity_type": "character",
            "entity_id": "mara",
            "scene_id": "scene_001",
            "story_time_position": 1,
            "properties": [{"key": "wardrobe", "value": "navy rain jacket", "confidence": 0.95}],
            "change_events": [],
            "overall_confidence": 0.95,
        },
        {
            "entity_type": "character",
            "entity_id": "owen",
            "scene_id": "scene_001",
            "story_time_position": 1,
            "properties": [{"key": "wardrobe", "value": "dark wool coat", "confidence": 0.93}],
            "change_events": [],
            "overall_confidence": 0.93,
        },
        {
            "entity_type": "location",
            "entity_id": "lab",
            "scene_id": "scene_001",
            "story_time_position": 1,
            "properties": [{"key": "lighting", "value": "monitor glow", "confidence": 0.9}],
            "change_events": [],
            "overall_confidence": 0.9,
        },
        {
            "entity_type": "character",
            "entity_id": "mara",
            "scene_id": "scene_002",
            "story_time_position": 2,
            "properties": [
                {
                    "key": "wardrobe",
                    "value": "coat whipped by wind",
                    "confidence": 0.92,
                }
            ],
            "change_events": [],
            "overall_confidence": 0.92,
        },
        {
            "entity_type": "location",
            "entity_id": "roof",
            "scene_id": "scene_002",
            "story_time_position": 2,
            "properties": [{"key": "weather", "value": "high wind", "confidence": 0.94}],
            "change_events": [],
            "overall_confidence": 0.94,
        },
    ]
    for payload in continuity_payloads[: 3 if scene_count == 1 else len(continuity_payloads)]:
        entity_key = f"{payload['entity_type']}_{payload['entity_id']}_{payload['scene_id']}"
        continuity_refs[entity_key] = store.save_artifact(
            artifact_type="continuity_state",
            entity_id=entity_key,
            data=payload,
            metadata=metadata("seed continuity"),
        )

    track_timeline = Timeline(
        entries=[
            TimelineEntry(
                scene_id=scene["scene_id"],
                scene_ref=scene_refs[scene["scene_id"]],
                script_position=idx,
                edit_position=idx,
                story_position=idx,
                estimated_duration_seconds=60.0,
            )
            for idx, scene in enumerate(scenes, start=1)
        ],
        total_scenes=len(scenes),
        estimated_runtime_seconds=float(len(scenes) * 60),
    )
    timeline_ref = store.save_artifact(
        artifact_type="timeline",
        entity_id="project",
        data=track_timeline.model_dump(mode="json"),
        metadata=metadata("seed timeline"),
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
            for scene in scenes
        ],
        track_fill_counts={"script": len(scenes)},
    )
    save_artifact(store, "track_manifest", "project", manifest.model_dump(mode="json"))

    for entity_type, entity_id, display_name, filename, accent in [
        ("character", "mara", "MARA", "mara_ref.jpg", (125, 211, 252)),
        ("location", "lab", "LAB", "lab_ref.jpg", (248, 250, 252)),
        ("location", "roof", "ROOF", "roof_ref.jpg", (196, 181, 253)),
    ]:
        files = [
            {
                "filename": filename,
                "purpose": "reference_image",
                "version": 1,
                "provenance": "system",
            }
        ]
        store.save_bible_entry(
            entity_type=entity_type,
            entity_id=entity_id,
            display_name=display_name,
            files=files,
            data_files={filename: reference_raster_bytes(display_name, accent=accent)},
            metadata=metadata("seed bible manifest"),
            visual_reference_image=filename,
        )

    shot_plans: list[ShotPlan] = []
    for scene in scenes:
        scene_id = scene["scene_id"]
        location_state_key = (
            "location_roof_scene_002" if scene_id == "scene_002" else "location_lab_scene_001"
        )
        scene_continuity_refs = [
            continuity_refs[f"character_mara_{scene_id}"],
            continuity_refs[location_state_key],
        ]
        if scene_id == "scene_001":
            scene_continuity_refs.append(continuity_refs["character_owen_scene_001"])
        coverage = CoverageStrategy(
            coverage_approach="Singles and inserts around a brittle confrontation.",
            rhythm_and_flow_intent="Start controlled and tighten into pressure.",
            look_and_feel_intent="Use negative space and practical light to trap the characters.",
            sound_and_music_intent="Let machinery and wind do most of the work.",
            character_and_performance_notes="Keep Mara active and Owen rigid.",
            coverage_patterns=["single", "insert", "reaction"],
            adequacy_check=CoverageAdequacyCheck(
                verdict="adequate",
                rationale="The edit can cut between pressure and detail.",
                missing_coverage_risks=[],
            ),
            audit=PlanningAudit(
                intent="Build storyboards from editorially useful coverage.",
                rationale="Scene already has clear shot geometry.",
                alternatives_considered=["Play only in a master."],
                confidence=0.87,
                source="ai",
            ),
        )
        shots = [
            ShotDefinition(
                scene_id=scene_id,
                shot_id=f"{scene_id.upper()}_A",
                shot_size="Medium Single",
                camera_angle="Eye level",
                camera_movement="Slow push",
                lens_focal_length="Telephoto (85mm+)",
                coverage_role="Single",
                characters_in_frame=["MARA"] if scene_id == "scene_002" else ["MARA", "OWEN"],
                point_of_view_character="MARA",
                blocking="Keep Mara tense in the foreground while the environment presses inward.",
                action_description="Hold on the pressure point of the conversation.",
                dialogue_lines=["We can still stop this."] if scene_id == "scene_001" else [],
                duration_estimate_seconds=7.0,
                edit_intent="Establish emotional pressure.",
                continuity_state_refs=scene_continuity_refs,
                upstream_artifact_refs=[scene_refs[scene_id]],
                audit=PlanningAudit(
                    intent="Create a clean hero storyboard frame.",
                    rationale="This shot anchors the scene geography.",
                    alternatives_considered=[],
                    confidence=0.86,
                    source="ai",
                ),
            ),
            ShotDefinition(
                scene_id=scene_id,
                shot_id=f"{scene_id.upper()}_B",
                shot_size="Insert",
                camera_angle="High",
                camera_movement="Static",
                lens_focal_length="Wide (18-35mm)",
                coverage_role="Insert",
                characters_in_frame=[],
                point_of_view_character=None,
                blocking=(
                    "Frame the physical trigger object or environmental detail that "
                    "carries the beat."
                ),
                action_description="Show the detail that the edit needs for the turn.",
                dialogue_lines=[],
                duration_estimate_seconds=3.0,
                edit_intent="Give the storyboard a concrete cutaway beat.",
                continuity_state_refs=[continuity_refs[location_state_key]],
                upstream_artifact_refs=[scene_refs[scene_id]],
                audit=PlanningAudit(
                    intent="Add a practical insert for the board.",
                    rationale="The editor needs a tactile detail beat.",
                    alternatives_considered=[],
                    confidence=0.84,
                    source="ai",
                ),
            ),
        ]
        shot_plan = ShotPlan(
            scene_id=scene_id,
            scene_number=scene["scene_number"],
            scene_heading=scene["heading"],
            scene_ref=scene_refs[scene_id],
            coverage_strategy=coverage,
            shots=shots,
            total_estimated_duration_seconds=sum(shot.duration_estimate_seconds for shot in shots),
        )
        shot_plans.append(shot_plan)
        save_artifact(store, "shot_plan", scene_id, shot_plan.model_dump(mode="json"))

    inputs = {
        "shot_plan": [plan.model_dump(mode="json") for plan in shot_plans],
        "track_manifest": manifest.model_dump(mode="json"),
        "project_config": project_config.model_dump(mode="json"),
        "intent_mood": intent_mood,
        "look_and_feel": look_and_feel,
        "character_bible": characters,
        "location_bible": locations[:scene_count],
    }
    return {
        "project_dir": project_dir,
        "inputs": inputs,
        "scene_ids": [scene["scene_id"] for scene in scenes],
        "store": store,
    }
