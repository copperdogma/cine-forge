from __future__ import annotations

import pytest

from cine_forge.schemas import (
    ArtifactRef,
    CompiledRenderPrompt,
    CostRecord,
    GeneratedVideoArtifact,
    MediaFile,
    PreviewProvenance,
    PrevizPromptContract,
    PrevizStyleProfile,
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
        preview_provenance=PreviewProvenance(
            mode="generated_render",
            fidelity_intent="render_preview",
            intended_use=["human_review", "ai_conditioning"],
            upstream_inputs=["shot_plan"],
            estimated_cost_usd=0.01,
            generation_latency_ms=1200,
        ),
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


@pytest.mark.unit
def test_previz_prompt_contract_round_trip() -> None:
    contract = PrevizPromptContract(
        target_engine_pack_id="google_veo31_fast",
        consistency_strategy="prompt_only",
        style_profile=PrevizStyleProfile(
            profile_id="cineforge_low_fidelity_previz_v1",
            title="CineForge Low-Fidelity Previz",
            summary="Blocking-first, non-final previz house style.",
            identity_strategy="Use silhouette and wardrobe color coding.",
            location_strategy="Keep only staging-relevant environment detail.",
            motion_priority="Prioritize camera path and body positions.",
            detail_suppression=["photoreal texture", "beauty pass"],
            prompt_guidance=["Keep the image schematic and readable."],
        ),
        prompt_text="Create a low-fidelity previz clip with readable blocking.",
        negative_prompt_terms=["photoreal skin detail"],
        notes=["prompt-only consistency"],
    )

    restored = PrevizPromptContract.model_validate_json(contract.model_dump_json())
    assert restored == contract


@pytest.mark.unit
def test_generated_video_artifact_round_trip_supports_previz_refs() -> None:
    artifact = GeneratedVideoArtifact(
        scene_id="scene_001",
        scene_number=1,
        scene_heading="INT. CONTROL ROOM - NIGHT",
        scene_ref=_scene_ref(),
        shot_plan_ref=_shot_plan_ref(),
        prompt_ref=ArtifactRef(
            artifact_type="ai_previz_prompt",
            entity_id="scene_001",
            version=1,
            path="artifacts/ai_previz_prompt/scene_001/v1.json",
        ),
        keyframe_ref=None,
        video=MediaFile(
            relative_path="artifacts/ai_previz_video_media/scene_001/v1.mp4",
            media_type="video/mp4",
        ),
        duration_seconds=8.0,
        resolution="1280x720",
        aspect_ratio="16:9",
        generation_params={},
        target_provider="google",
        target_model="veo-3.1-lite-generate-preview",
        engine_pack_id="google_veo31_lite",
        request_id="video-001",
        cost=CostRecord(
            model="veo-3.1-lite-generate-preview",
            input_tokens=0,
            output_tokens=0,
            estimated_cost_usd=0.0,
        ),
        resolved_inputs=[],
        notes=[],
        preview_provenance=PreviewProvenance(
            mode="ai_previz",
            fidelity_intent="blocking_review",
            intended_use=["human_review"],
            upstream_inputs=["shot_plan", "look_and_feel"],
            consistency_strategy="prompt_only",
            estimated_cost_usd=None,
            generation_latency_ms=2400,
        ),
    )

    restored = GeneratedVideoArtifact.model_validate_json(artifact.model_dump_json())
    assert restored == artifact
