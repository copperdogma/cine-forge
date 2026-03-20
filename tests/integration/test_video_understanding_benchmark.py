from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
BENCHMARK_PROVIDER_ROOT = REPO_ROOT / "benchmarks" / "providers"
BENCHMARK_SCORER_ROOT = REPO_ROOT / "benchmarks" / "scorers"
for path in (BENCHMARK_PROVIDER_ROOT, BENCHMARK_SCORER_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

provider = importlib.import_module("video_understanding_provider")
scorer = importlib.import_module("video_understanding_scorer")


@pytest.mark.integration
def test_generated_clip_packet_and_scoring_fixture_align() -> None:
    clip_dir = REPO_ROOT / "benchmarks" / "video_understanding" / "dialogue_confession_push_in"
    packet = provider._load_clip_packet(clip_dir, max_frames=5)

    assert packet["meta"]["clip_id"] == "dialogue_confession_push_in"
    assert len(packet["frames"]) == 5
    assert packet["meta"]["has_audio"] is True

    fixture_output = {
        "clip_id": "dialogue_confession_push_in",
        "summary": (
            "A blue confession scene slowly pushes toward the hesitant speaker "
            "with the envelope."
        ),
        "tone_tags": ["intimate", "regretful"],
        "emotion_tags": ["hesitation", "vulnerability"],
        "color_tags": ["navy", "teal"],
        "camera_tags": ["locked_two_shot", "slow_push_in"],
        "motion_tags": ["measured"],
        "continuity_status": "intact",
        "continuity_notes": [
            "The white envelope stays in the same speaker's hand through the push-in."
        ],
        "audio_tags": ["soft_music", "speech"],
        "audio_notes": ["Soft piano sits under a single confession line."],
        "evidence": [
            {"timestamp_seconds": 0.9, "cue": "Two-shot starts in cool blue light."},
            {
                "timestamp_seconds": 2.7,
                "cue": "The camera has pushed closer to the speaker holding the envelope.",
            },
        ],
        "overall_confidence": 0.88,
    }
    score = scorer.score_output_against_target(
        output=fixture_output,
        target_path=clip_dir / "target.json",
        model_label="Fixture",
        prompt_version="video-understanding-v1",
    )

    assert score.hard_constraints_passed is True
    assert score.overall_score > 0.8
