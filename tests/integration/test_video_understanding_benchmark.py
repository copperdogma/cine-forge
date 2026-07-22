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
    assert packet["sample_times_seconds"] == [0.0, 1.0, 2.0, 3.0, 3.875]
    assert packet["meta"]["has_audio"] is True

    fixture_output = {
        "clip_id": "dialogue_confession_push_in",
        "summary": "Two blue figures appear closer across the ordered frame packet.",
        "tone_tags": ["intimate"],
        "emotion_tags": [],
        "color_tags": ["navy", "teal"],
        "camera_tags": ["locked_two_shot", "slow_push_in"],
        "motion_tags": ["measured"],
        "continuity_status": "intact",
        "continuity_notes": [
            "The pale rectangle stays beside the right figure across all five frames."
        ],
        "audio_tags": [],
        "audio_notes": [],
        "evidence": [
            {"frame_index": 1, "cue": "Two blue figures hold the two-shot."},
            {
                "frame_index": 2,
                "cue": "The pale rectangle stays beside the closer right figure.",
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
