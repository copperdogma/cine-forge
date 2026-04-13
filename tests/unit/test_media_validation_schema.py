from __future__ import annotations

import pytest

from cine_forge.schemas import (
    ArtifactHealth,
    ArtifactRef,
    DeterministicMediaProbe,
    MediaFile,
    MediaValidationArtifact,
    MediaValidationTarget,
)


@pytest.mark.unit
def test_media_validation_artifact_accepts_runtime_contract() -> None:
    artifact = MediaValidationArtifact(
        target=MediaValidationTarget(
            scope_kind="scene",
            entity_id="scene_001",
            label="Scene 1: INT. LAB - NIGHT",
            scene_id="scene_001",
            scene_number=1,
            scene_heading="INT. LAB - NIGHT",
        ),
        target_ref=ArtifactRef(
            artifact_type="generated_video",
            entity_id="scene_001",
            version=1,
            path="artifacts/generated_video/scene_001/v1.json",
        ),
        prompt_ref=ArtifactRef(
            artifact_type="render_prompt",
            entity_id="scene_001",
            version=1,
            path="artifacts/render_prompt/scene_001/v1.json",
        ),
        validated_media=MediaFile(
            relative_path="artifacts/generated_video_media/scene_001/v1/scene_render.mp4",
            media_type="video/mp4",
            duration_seconds=8.0,
        ),
        validator_id="media_validation_v1",
        validation_mode="hybrid",
        sampling_policy="5_evenly_spaced_jpegs_v1",
        config_digest="abc123",
        deterministic_probe=DeterministicMediaProbe(
            file_exists=True,
            ffprobe_available=True,
            ffmpeg_available=True,
            probe_succeeded=True,
            decode_succeeded=True,
            duration_seconds=8.0,
            video_stream_present=True,
            audio_stream_present=False,
            sample_count_requested=5,
            sample_count_extracted=5,
        ),
        semantic_review={
            "status": "needs_review",
            "mode": "sampled_frames",
            "model": "gpt-5.4",
            "summary": "Samples look usable but motion continuity still needs a human pass.",
            "confidence": 0.78,
            "findings": [],
        },
        recommended_health=ArtifactHealth.NEEDS_REVIEW,
        summary=(
            "Deterministic validation passed, but semantic review still needs "
            "operator confirmation."
        ),
    )

    assert artifact.recommended_health == ArtifactHealth.NEEDS_REVIEW
    assert artifact.semantic_review.mode == "sampled_frames"
    assert artifact.target.scope_kind == "scene"


@pytest.mark.unit
def test_media_validation_artifact_accepts_project_scoped_target() -> None:
    artifact = MediaValidationArtifact(
        target=MediaValidationTarget(
            scope_kind="project",
            entity_id="project",
            label="Project final output",
            coverage_state="partial",
            included_scene_count=3,
            omitted_scene_count=1,
        ),
        target_ref=ArtifactRef(
            artifact_type="final_output",
            entity_id="project",
            version=2,
            path="artifacts/final_output/project/v2.json",
        ),
        validated_media=MediaFile(
            relative_path="artifacts/final_output_media/project/v2/final_output.mp4",
            media_type="video/mp4",
            duration_seconds=12.5,
        ),
        validator_id="media_validation_v1",
        validation_mode="deterministic_only",
        sampling_policy="5_evenly_spaced_jpegs_v1",
        config_digest="abc123",
        deterministic_probe=DeterministicMediaProbe(
            file_exists=True,
            ffprobe_available=True,
            ffmpeg_available=True,
            probe_succeeded=True,
            decode_succeeded=True,
            duration_seconds=12.5,
            video_stream_present=True,
            audio_stream_present=False,
            sample_count_requested=5,
            sample_count_extracted=5,
        ),
        recommended_health=ArtifactHealth.NEEDS_REVIEW,
        summary="Final output still needs semantic review before it can be treated as clean.",
    )

    assert artifact.target.scope_kind == "project"
    assert artifact.target.omitted_scene_count == 1


@pytest.mark.unit
def test_deterministic_probe_rejects_extracted_frames_beyond_request() -> None:
    with pytest.raises(ValueError, match="sample_count_extracted"):
        DeterministicMediaProbe(
            file_exists=True,
            sample_count_requested=2,
            sample_count_extracted=3,
        )
