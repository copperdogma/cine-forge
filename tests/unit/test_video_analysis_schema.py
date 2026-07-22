from __future__ import annotations

import pytest

from cine_forge.driver.schema_registry import build_schema_registry
from cine_forge.schemas import (
    VideoAnalysisPrediction,
    VideoAnalysisScore,
    VideoAnalysisTarget,
    VideoAnalysisWeights,
)


def _target() -> VideoAnalysisTarget:
    return VideoAnalysisTarget(
        clip_id="clip_regret_confession",
        title="Regret confession push-in",
        source_type="synthetic_previz",
        source_description="Generated from the Story 030 synthetic dataset generator",
        rights="Project-owned synthetic benchmark asset",
        duration_seconds=4.0,
        resolution="640x360",
        has_audio=True,
        transcript="I should have told you before the train left.",
        audio_description="Soft piano under a single confession line.",
        summary_reference="A cool-blue two-shot slowly pushes toward the hesitant speaker.",
        required_keywords=["confession", "push-in", "blue"],
        tone_tags=["intimate", "regretful"],
        emotion_tags=["hesitation", "vulnerability"],
        color_tags=["navy", "teal"],
        camera_tags=["locked_two_shot", "slow_push_in"],
        motion_tags=["measured"],
        continuity_status="intact",
        continuity_notes=["White envelope remains in the speaker's right hand."],
        audio_tags=["soft_music", "speech"],
        clip_tags=["dialogue", "quiet_emotion"],
        anchor_subset=True,
    )


@pytest.mark.unit
def test_video_analysis_target_round_trip() -> None:
    target = _target()
    restored = VideoAnalysisTarget.model_validate_json(target.model_dump_json())
    assert restored == target


@pytest.mark.unit
def test_video_analysis_target_rejects_transcript_without_audio() -> None:
    with pytest.raises(ValueError, match="transcript must be empty"):
        VideoAnalysisTarget(
            clip_id="clip_silent",
            title="Silent clip",
            source_type="synthetic_previz",
            source_description="Synthetic",
            rights="Project-owned synthetic benchmark asset",
            duration_seconds=3.0,
            resolution="640x360",
            has_audio=False,
            transcript="This should not be present.",
            summary_reference="A silent static frame.",
            audio_tags=["silent"],
        )


@pytest.mark.unit
def test_video_analysis_weights_must_sum_to_one() -> None:
    with pytest.raises(ValueError, match="sum to 1.0"):
        VideoAnalysisWeights(summary=0.5, tone=0.5, emotion=0.5)


@pytest.mark.unit
def test_video_analysis_prediction_and_score_validate() -> None:
    prediction = VideoAnalysisPrediction(
        clip_id="clip_regret_confession",
        summary="A blue-toned confession scene with a slow push-in and hushed piano.",
        tone_tags=["intimate", "regretful"],
        emotion_tags=["hesitation", "vulnerability"],
        color_tags=["navy", "teal"],
        camera_tags=["locked_two_shot", "slow_push_in"],
        motion_tags=["measured"],
        continuity_status="intact",
        continuity_notes=["The white envelope stays with the same speaker."],
        audio_tags=["soft_music", "speech"],
        audio_notes=["One confession line over restrained piano."],
        evidence=[{"frame_index": 1, "cue": "The frame tightens toward the speaker."}],
        overall_confidence=0.82,
    )
    score = VideoAnalysisScore(
        clip_id=prediction.clip_id,
        model_label="Fixture Model",
        overall_score=0.91,
        uncertainty=0.08,
        hard_constraints_passed=True,
        dimensions=[
            {
                "dimension": "summary",
                "score": 1.0,
                "matched": ["confession", "push-in"],
                "missed": [],
                "rationale": "Summary covered the required cues.",
            }
        ],
        rationale="Fixture score",
        prompt_version="video-understanding-v1",
    )

    assert prediction.clip_id == "clip_regret_confession"
    assert score.overall_score == 0.91


@pytest.mark.unit
def test_schema_registry_includes_video_analysis_types() -> None:
    registry = build_schema_registry()
    assert registry.get("video_analysis_target") is not None
    assert registry.get("video_analysis_prediction") is not None
    assert registry.get("video_analysis_score") is not None
