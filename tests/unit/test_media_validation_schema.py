from __future__ import annotations

import pytest

from cine_forge.schemas import (
    ArtifactHealth,
    ArtifactRef,
    DeterministicMediaProbe,
    MediaFile,
    MediaValidationArtifact,
)


@pytest.mark.unit
def test_media_validation_artifact_accepts_runtime_contract() -> None:
    artifact = MediaValidationArtifact(
        scene_id="scene_001",
        scene_number=1,
        scene_heading="INT. LAB - NIGHT",
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


@pytest.mark.unit
def test_deterministic_probe_rejects_extracted_frames_beyond_request() -> None:
    with pytest.raises(ValueError, match="sample_count_extracted"):
        DeterministicMediaProbe(
            file_exists=True,
            sample_count_requested=2,
            sample_count_extracted=3,
        )
