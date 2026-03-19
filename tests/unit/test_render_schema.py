from __future__ import annotations

import pytest

from cine_forge.schemas import (
    ArtifactRef,
    CompiledRenderPrompt,
    CostRecord,
    GeneratedVideoArtifact,
    MediaFile,
    RenderCompletenessCheck,
    RenderPromptSection,
)


def _scene_ref() -> ArtifactRef:
    return ArtifactRef(
        artifact_type="scene",
        entity_id="scene_001",
        version=1,
        path="artifacts/scene/scene_001/v1.json",
    )


def _shot_plan_ref() -> ArtifactRef:
    return ArtifactRef(
        artifact_type="shot_plan",
        entity_id="scene_001",
        version=1,
        path="artifacts/shot_plan/scene_001/v1.json",
    )


def _prompt_ref() -> ArtifactRef:
    return ArtifactRef(
        artifact_type="render_prompt",
        entity_id="scene_001",
        version=1,
        path="artifacts/render_prompt/scene_001/v1.json",
    )


@pytest.mark.unit
def test_compiled_render_prompt_round_trip() -> None:
    prompt = CompiledRenderPrompt(
        scene_id="scene_001",
        scene_number=1,
        scene_heading="INT. CONTROL ROOM - NIGHT",
        scene_ref=_scene_ref(),
        shot_plan_ref=_shot_plan_ref(),
        keyframe_ref=None,
        target_provider="openai",
        target_model="sora-2",
        engine_pack_id="openai_sora2",
        compiler_model="gpt-5.4-mini",
        requested_duration_seconds=8.0,
        resolved_duration_seconds=8.0,
        resolution="1280x720",
        aspect_ratio="16:9",
        provider_params={},
        prompt_text="Render the tense control-room confrontation with a measured push.",
        sections=[
            RenderPromptSection(
                section_id="shot_definition",
                title="Shot Definition",
                body="Use a slow push on Mara as the console glow hardens around her.",
                source_role_id="shot_planning",
                source_artifact_types=["shot_plan"],
            )
        ],
        completeness=RenderCompletenessCheck(
            included_categories=["shot_definition"],
            missing_categories=[],
            notes=[],
        ),
        prompt_sources_used=["shot_plan"],
        resolved_inputs=[],
    )

    restored = CompiledRenderPrompt.model_validate_json(prompt.model_dump_json())
    assert restored == prompt


@pytest.mark.unit
def test_generated_video_artifact_requires_positive_duration() -> None:
    with pytest.raises(ValueError, match="greater than or equal to 0"):
        GeneratedVideoArtifact(
            scene_id="scene_001",
            scene_number=1,
            scene_heading="INT. CONTROL ROOM - NIGHT",
            scene_ref=_scene_ref(),
            shot_plan_ref=_shot_plan_ref(),
            prompt_ref=_prompt_ref(),
            keyframe_ref=None,
            video=MediaFile(
                relative_path="artifacts/generated_video_media/scene_001/v1.mp4",
                media_type="video/mp4",
            ),
            duration_seconds=-1.0,
            resolution="1280x720",
            aspect_ratio="16:9",
            generation_params={},
            target_provider="openai",
            target_model="sora-2",
            engine_pack_id="openai_sora2",
            request_id="video-001",
            cost=CostRecord(
                model="gpt-5.4-mini+sora-2",
                input_tokens=100,
                output_tokens=50,
                estimated_cost_usd=0.01,
            ),
            resolved_inputs=[],
            notes=[],
        )
