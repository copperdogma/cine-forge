from __future__ import annotations

import pytest

from cine_forge.schemas import (
    ArtifactRef,
    CoverageAdequacyCheck,
    CoverageStrategy,
    PlanningAudit,
    ShotDefinition,
    ShotPlan,
)


def _audit() -> PlanningAudit:
    return PlanningAudit(
        intent="Scene coverage strategy",
        rationale="Cuttable dialogue coverage with room for reaction beats.",
        alternatives_considered=["Master-only coverage"],
        confidence=0.87,
        source="ai",
    )


def _scene_ref() -> ArtifactRef:
    return ArtifactRef(
        artifact_type="scene",
        entity_id="scene_001",
        version=1,
        path="artifacts/scene/scene_001/v1.json",
    )


@pytest.mark.unit
def test_shot_plan_round_trip() -> None:
    plan = ShotPlan(
        scene_id="scene_001",
        scene_number=1,
        scene_heading="INT. CONTROL ROOM - NIGHT",
        scene_ref=_scene_ref(),
        coverage_strategy=CoverageStrategy(
            coverage_approach="Master plus selective singles.",
            rhythm_and_flow_intent="Slow-burn pacing with restrained cuts.",
            look_and_feel_intent="Cold green practicals and wary compositions.",
            sound_and_music_intent="Hum and distant thunder with held silence after activation.",
            character_and_performance_notes="Mara hopeful, Owen shut down.",
            coverage_patterns=["Master", "Single", "Reaction"],
            adequacy_check=CoverageAdequacyCheck(
                verdict="adequate",
                rationale="All dialogue and the action beat are covered.",
            ),
            audit=_audit(),
        ),
        shots=[
            ShotDefinition(
                scene_id="scene_001",
                shot_id="S001-A",
                shot_size="Wide Master",
                camera_angle="Eye level",
                camera_movement="Static",
                lens_focal_length="Normal (40-60mm)",
                coverage_role="Master",
                characters_in_frame=["MARA", "OWEN"],
                blocking="Hold both characters in their original positions.",
                action_description="Play the exchange start to finish.",
                dialogue_lines=["If this tower still has power, we can call them."],
                duration_estimate_seconds=14.0,
                edit_intent="Editorial safety net and geography anchor.",
                continuity_state_refs=[],
                upstream_artifact_refs=[_scene_ref()],
                audit=_audit(),
            )
        ],
        total_estimated_duration_seconds=14.0,
    )

    restored = ShotPlan.model_validate_json(plan.model_dump_json())
    assert restored == plan


@pytest.mark.unit
def test_shot_plan_rejects_mismatched_scene_id() -> None:
    with pytest.raises(ValueError, match="share the parent scene_id"):
        ShotPlan(
            scene_id="scene_001",
            scene_number=1,
            scene_heading="INT. CONTROL ROOM - NIGHT",
            scene_ref=_scene_ref(),
            coverage_strategy=CoverageStrategy(
                coverage_approach="Master only.",
                rhythm_and_flow_intent="Hold.",
                look_and_feel_intent="Dark.",
                sound_and_music_intent="Quiet.",
                character_and_performance_notes="Tense.",
                adequacy_check=CoverageAdequacyCheck(
                    verdict="borderline",
                    rationale="Needs reaction coverage.",
                ),
                audit=_audit(),
            ),
            shots=[
                ShotDefinition(
                    scene_id="scene_002",
                    shot_id="S001-A",
                    shot_size="Wide",
                    camera_angle="Eye level",
                    camera_movement="Static",
                    lens_focal_length="Wide (18-35mm)",
                    coverage_role="Master",
                    blocking="Stand still.",
                    action_description="Play the scene.",
                    dialogue_lines=[],
                    duration_estimate_seconds=10.0,
                    edit_intent="Safety.",
                    continuity_state_refs=[],
                    upstream_artifact_refs=[_scene_ref()],
                    audit=_audit(),
                )
            ],
            total_estimated_duration_seconds=10.0,
        )


@pytest.mark.unit
def test_shot_plan_rejects_duplicate_shot_ids() -> None:
    shot = ShotDefinition(
        scene_id="scene_001",
        shot_id="S001-A",
        shot_size="Wide",
        camera_angle="Eye level",
        camera_movement="Static",
        lens_focal_length="Wide (18-35mm)",
        coverage_role="Master",
        blocking="Stand still.",
        action_description="Play the scene.",
        dialogue_lines=[],
        duration_estimate_seconds=10.0,
        edit_intent="Safety.",
        continuity_state_refs=[],
        upstream_artifact_refs=[_scene_ref()],
        audit=_audit(),
    )
    with pytest.raises(ValueError, match="unique within a ShotPlan"):
        ShotPlan(
            scene_id="scene_001",
            scene_number=1,
            scene_heading="INT. CONTROL ROOM - NIGHT",
            scene_ref=_scene_ref(),
            coverage_strategy=CoverageStrategy(
                coverage_approach="Master and insert.",
                rhythm_and_flow_intent="Hold.",
                look_and_feel_intent="Dark.",
                sound_and_music_intent="Quiet.",
                character_and_performance_notes="Tense.",
                adequacy_check=CoverageAdequacyCheck(
                    verdict="adequate",
                    rationale="Enough coverage for the beat.",
                ),
                audit=_audit(),
            ),
            shots=[shot, shot],
            total_estimated_duration_seconds=20.0,
        )
