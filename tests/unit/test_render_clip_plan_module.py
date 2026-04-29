from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from cine_forge.artifacts import ArtifactStore
from cine_forge.modules.generation.render_clip_plan_v1.main import run_module
from cine_forge.modules.generation.render_clip_plan_v1.prompting import (
    RenderClipPlanningResponse,
    RenderClipPlanningResponseClip,
)
from cine_forge.schemas import ArtifactMetadata, RenderClipPlan
from tests.storyboard_fixtures import seed_storyboard_project


def _inputs_for_seeded_project(
    seeded: dict[str, Any],
    *,
    include_shot_plan: bool = True,
) -> dict[str, Any]:
    store: ArtifactStore = seeded["store"]
    project_dir: Path = seeded["project_dir"]
    timeline_ref = store.list_versions("timeline", "project")[-1]
    track_ref = store.list_versions("track_manifest", "project")[-1]
    scene_entries = []
    script_lines = []
    line_number = 1
    for scene_id in seeded["scene_ids"]:
        scene_ref = store.list_versions("scene", scene_id)[-1]
        scene = store.load_artifact(scene_ref).data
        scene_entries.append(
            {
                "scene_id": scene_id,
                "scene_number": scene["scene_number"],
                "heading": scene["heading"],
                "source_span": {"start_line": line_number, "end_line": line_number + 5},
            }
        )
        script_lines.extend(
            [
                scene["heading"],
                "MARA",
                "We can still stop this.",
                "OWEN",
                "No. We let it run.",
                "",
            ]
        )
        line_number += 6
    inputs = {
        "scene_index": {"entries": scene_entries},
        "timeline": store.load_artifact(timeline_ref).data,
        "track_manifest": store.load_artifact(track_ref).data,
        "normalize": {"title": "Pressure Test", "script_text": "\n".join(script_lines)},
    }
    if include_shot_plan:
        inputs["shot_plan"] = seeded["inputs"]["shot_plan"]
    (project_dir / "inputs").mkdir(exist_ok=True)
    return inputs


def _context(project_dir: Path) -> dict[str, Any]:
    return {"project_dir": str(project_dir), "runtime_params": {}}


@pytest.mark.unit
def test_render_clip_plan_from_full_shot_plan_respects_engine_limit(tmp_path: Path) -> None:
    seeded = seed_storyboard_project(tmp_path, scene_count=1)

    result = run_module(
        _inputs_for_seeded_project(seeded),
        {"planner_model": "mock", "engine_pack_id": "google_veo31"},
        _context(seeded["project_dir"]),
    )

    artifacts = result["artifacts"]
    assert len(artifacts) == 1
    plan = RenderClipPlan.model_validate(artifacts[0]["data"])
    assert plan.scene_id == "scene_001"
    assert plan.shot_plan_ref is not None
    assert plan.provenance_mode == "shot_plan_code"
    assert plan.target_dramatic_duration_seconds == pytest.approx(10.0)
    assert [clip.target_duration_seconds for clip in plan.clips] == [7.0, 3.0]
    assert all(clip.target_duration_seconds <= 8.0 for clip in plan.clips)
    assert "shot_plan" not in plan.missing_upstream_categories


@pytest.mark.unit
def test_render_clip_plan_falls_back_without_shot_plan(tmp_path: Path) -> None:
    seeded = seed_storyboard_project(tmp_path, scene_count=1)

    result = run_module(
        _inputs_for_seeded_project(seeded, include_shot_plan=False),
        {"planner_model": "mock", "engine_pack_id": "google_veo31"},
        _context(seeded["project_dir"]),
    )

    plan = RenderClipPlan.model_validate(result["artifacts"][0]["data"])
    assert plan.shot_plan_ref is None
    assert plan.provenance_mode == "fallback_code"
    assert plan.source == "code"
    assert "shot_plan" in plan.missing_upstream_categories
    assert plan.confidence < 0.5
    assert plan.clips[0].fallback_beat_ids


@pytest.mark.unit
def test_brick_steel_style_fixture_gets_multiple_render_clips(tmp_path: Path) -> None:
    seeded = seed_storyboard_project(tmp_path, scene_count=1)
    store: ArtifactStore = seeded["store"]
    brick_scene = {
        "scene_id": "scene_001",
        "scene_number": 1,
        "heading": "EXT. SUBURBAN PATIO - DAY",
        "location": "SUBURBAN PATIO",
        "time_of_day": "DAY",
        "int_ext": "EXT",
        "characters_present": ["BRICK", "STEEL"],
        "characters_present_ids": ["brick", "steel"],
        "props_mentioned": ["beer bottles", "lawn chairs"],
        "tone_mood": "dry, restless retirement malaise",
        "source_span": {"start_line": 1, "end_line": 20},
        "elements": [
            {"element_type": "action", "content": "Brick sits still in harsh daylight."},
            {"element_type": "character", "content": "STEEL"},
            {"element_type": "dialogue", "content": "Beer's ready!"},
            {"element_type": "character", "content": "BRICK"},
            {"element_type": "dialogue", "content": "Are they cold?"},
            {"element_type": "character", "content": "STEEL"},
            {"element_type": "dialogue", "content": "Does a bear crap in the woods?"},
            {"element_type": "character", "content": "STEEL"},
            {"element_type": "dialogue", "content": "To retirement."},
            {"element_type": "character", "content": "BRICK"},
            {"element_type": "dialogue", "content": "To retirement."},
            {
                "element_type": "action",
                "content": "A long uncomfortable silence holds while both men go still.",
            },
            {"element_type": "character", "content": "STEEL"},
            {"element_type": "dialogue", "content": "Screw retirement."},
            {"element_type": "character", "content": "BRICK"},
            {"element_type": "dialogue", "content": "Screw retirement."},
        ],
        "narrative_beats": [],
        "tone_shifts": [],
        "inferences": [],
        "provenance": [],
        "confidence": 1.0,
    }
    store.save_artifact(
        artifact_type="scene",
        entity_id="scene_001",
        data=brick_scene,
        metadata=ArtifactMetadata(
            lineage=[],
            intent="seed brick scene",
            rationale="test",
            confidence=1.0,
            source="code",
        ),
    )

    result = run_module(
        _inputs_for_seeded_project(seeded, include_shot_plan=False),
        {"planner_model": "mock", "engine_pack_id": "google_veo31"},
        _context(seeded["project_dir"]),
    )

    plan = RenderClipPlan.model_validate(result["artifacts"][0]["data"])
    assert plan.target_dramatic_duration_seconds > 8.0
    assert len(plan.clips) >= 4
    assert all(clip.target_duration_seconds <= 8.0 for clip in plan.clips)
    assert "silence" in plan.duration_rationale.lower() or any(
        "silence" in " ".join(clip.action_beats).lower() for clip in plan.clips
    )


@pytest.mark.unit
def test_ai_clip_plan_is_validated_and_split_to_engine_cap(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seeded = seed_storyboard_project(tmp_path, scene_count=1)

    def _fake_call_llm(**_: Any) -> tuple[RenderClipPlanningResponse, dict[str, Any]]:
        return (
            RenderClipPlanningResponse(
                target_dramatic_duration_seconds=20.0,
                duration_rationale="The scene needs one long tense run.",
                confidence=0.82,
                clips=[
                    RenderClipPlanningResponseClip(
                        source_shot_ids=["SCENE_001_A"],
                        target_duration_seconds=20.0,
                        dialogue_lines=["MARA: We can still stop this."],
                        action_beats=["Hold one long pressure beat."],
                        rationale="AI grouped the beat too long for the engine.",
                        confidence=0.8,
                    )
                ],
            ),
            {
                "model": "claude-opus-4-6",
                "input_tokens": 100,
                "output_tokens": 100,
                "estimated_cost_usd": 0.01,
            },
        )

    monkeypatch.setattr(
        "cine_forge.modules.generation.render_clip_plan_v1.prompting.call_llm",
        _fake_call_llm,
    )

    result = run_module(
        _inputs_for_seeded_project(seeded),
        {"planner_model": "claude-opus-4-6", "engine_pack_id": "google_veo31"},
        _context(seeded["project_dir"]),
    )

    plan = RenderClipPlan.model_validate(result["artifacts"][0]["data"])
    assert plan.provenance_mode == "shot_plan_ai"
    assert plan.planner_model == "claude-opus-4-6"
    assert plan.target_dramatic_duration_seconds == pytest.approx(20.0)
    assert len(plan.clips) == 3
    assert all(clip.target_duration_seconds <= 8.0 for clip in plan.clips)
    assert result["cost"]["estimated_cost_usd"] == pytest.approx(0.01)
