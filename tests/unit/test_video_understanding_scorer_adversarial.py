from __future__ import annotations

import importlib
import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCORER_ROOT = REPO_ROOT / "benchmarks" / "scorers"
if str(SCORER_ROOT) not in sys.path:
    sys.path.insert(0, str(SCORER_ROOT))

contract = importlib.import_module("video_understanding_contract")
scorer = importlib.import_module("video_understanding_scorer")


def _write_target(tmp_path: Path) -> Path:
    target_path = tmp_path / "target.json"
    target_path.write_text(
        json.dumps(
            {
                "clip_id": "clip_1",
                "title": "Hidden target title",
                "source_type": "synthetic_previz",
                "source_description": "Synthetic test packet",
                "rights": "Project-owned",
                "duration_seconds": 4.0,
                "resolution": "640x360",
                "has_audio": True,
                "transcript": "This must never be submitted.",
                "audio_description": "This must never be scored.",
                "summary_reference": "Urgent red pulses follow a runner carrying a bag.",
                "required_keywords": ["urgent", "red", "runner", "percussion"],
                "tone_tags": ["urgent", "tense"],
                "emotion_tags": ["panic"],
                "color_tags": ["red"],
                "camera_tags": ["whip_pan"],
                "motion_tags": ["pulsing_light", "fast_lateral"],
                "continuity_status": "intact",
                "continuity_notes": ["The red bag stays with the runner."],
                "audio_tags": ["alarm", "speech", "percussion"],
                "clip_tags": ["action"],
                "anchor_subset": True,
                "weights": {
                    "summary": 0.18,
                    "tone": 0.14,
                    "emotion": 0.12,
                    "color": 0.10,
                    "camera": 0.12,
                    "motion": 0.10,
                    "continuity": 0.12,
                    "audio": 0.08,
                    "evidence": 0.04,
                },
            }
        )
    )
    return target_path


def _perfect_prediction() -> dict[str, object]:
    return {
        "clip_id": "clip_1",
        "summary": "An urgent red sequence follows a runner carrying a bag.",
        "tone_tags": ["urgent", "tense"],
        "emotion_tags": ["panic"],
        "color_tags": ["red"],
        "camera_tags": ["whip_pan"],
        "motion_tags": ["pulsing_light", "fast_lateral"],
        "continuity_status": "intact",
        "continuity_notes": ["The red bag stays with the runner."],
        "audio_tags": [],
        "audio_notes": [],
        "evidence": [
            {
                "frame_index": 1,
                "cue": "Red pulsing light crosses the runner and bag.",
            },
            {
                "frame_index": 2,
                "cue": "Whip pan follows the runner carrying the red bag.",
            },
        ],
        "overall_confidence": 0.9,
    }


def _assert_result(tmp_path: Path, prediction: dict[str, object]) -> dict:
    target_path = _write_target(tmp_path)
    return scorer.get_assert(
        json.dumps(prediction),
        {"vars": {"target_path": str(target_path), "evaluation_id": "clip_1"}},
    )


@pytest.mark.unit
def test_promptfoo_contract_requires_opaque_evaluation_id(tmp_path: Path) -> None:
    target_path = _write_target(tmp_path)
    result = scorer.get_assert(
        json.dumps(_perfect_prediction()),
        {"vars": {"target_path": str(target_path)}},
    )

    assert result["pass"] is False
    assert result["score"] == 0.0
    assert "evaluation_id" in result["reason"]


@pytest.mark.unit
def test_promptfoo_contract_scores_opaque_id_instead_of_semantic_target_id(
    tmp_path: Path,
) -> None:
    target_path = _write_target(tmp_path)
    prediction = _perfect_prediction()
    prediction["clip_id"] = "frame_case_001"
    result = scorer.get_assert(
        json.dumps(prediction),
        {
            "vars": {
                "target_path": str(target_path),
                "evaluation_id": "frame_case_001",
            }
        },
    )

    assert result["pass"] is True
    assert result["score"] == 1.0


@pytest.mark.unit
def test_perfect_frame_only_control_passes_without_audio_credit_or_requirement(
    tmp_path: Path,
) -> None:
    target_path = _write_target(tmp_path)
    score = scorer.score_output_against_target(
        output=_perfect_prediction(),
        target_path=target_path,
        model_label="Control",
        prompt_version="frame-packet-v2",
    )

    dimensions = {item.dimension: item.score for item in score.dimensions}
    assert score.hard_constraints_passed is True
    assert score.overall_score == pytest.approx(1.0)
    assert dimensions["audio"] == 0.0


@pytest.mark.unit
def test_generic_prose_cannot_pass_as_grounded_analysis(tmp_path: Path) -> None:
    prediction = _perfect_prediction()
    prediction.update(
        {
            "summary": "This is a well-made scene with clear visual storytelling.",
            "tone_tags": [],
            "emotion_tags": [],
            "color_tags": [],
            "camera_tags": [],
            "motion_tags": [],
            "continuity_status": "ambiguous",
            "continuity_notes": [],
            "evidence": [
                {"frame_index": 1, "cue": "The visuals support the analysis."},
                {"frame_index": 2, "cue": "The scene communicates its intent."},
            ],
        }
    )
    result = _assert_result(tmp_path, prediction)

    assert result["pass"] is False
    assert result["score"] < 0.70
    assert "cue_not_target_grounded" in result["reason"]


@pytest.mark.unit
def test_all_tags_overprediction_is_penalized_by_precision(tmp_path: Path) -> None:
    prediction = _perfect_prediction()
    for field_name in contract.TAG_FIELDS:
        if field_name != "audio_tags":
            prediction[field_name] = sorted(contract.ALLOWED_TAGS[field_name])
    result = _assert_result(tmp_path, prediction)

    assert result["pass"] is False
    assert result["score"] < 0.70
    assert "unexpected=" in result["reason"]


@pytest.mark.unit
def test_invented_evidence_hard_fails(tmp_path: Path) -> None:
    prediction = _perfect_prediction()
    prediction["evidence"] = [
        {"frame_index": 1, "cue": "A dragon burns an unseen city."},
        {"frame_index": 2, "cue": "The moon explodes behind a castle."},
    ]
    result = _assert_result(tmp_path, prediction)

    assert result["pass"] is False
    assert result["score"] < 0.70
    assert "cue_not_target_grounded" in result["reason"]


@pytest.mark.unit
def test_audio_claims_hard_fail_when_audio_was_not_submitted(tmp_path: Path) -> None:
    prediction = _perfect_prediction()
    prediction["audio_tags"] = ["speech"]
    prediction["audio_notes"] = ["A voice is heard over loud music."]
    result = _assert_result(tmp_path, prediction)

    assert result["pass"] is False
    assert result["score"] < 0.70
    assert "audio_unavailable" in result["reason"]


@pytest.mark.unit
@pytest.mark.parametrize(
    ("field_name", "bad_value", "reason_fragment"),
    [
        ("tone_tags", ["urgent", "urgent"], "Duplicate tone_tags"),
        ("camera_tags", ["dolly_zoom"], "Unknown camera_tags"),
    ],
)
def test_duplicate_and_unknown_tags_are_rejected(
    tmp_path: Path,
    field_name: str,
    bad_value: list[str],
    reason_fragment: str,
) -> None:
    prediction = _perfect_prediction()
    prediction[field_name] = bad_value
    result = _assert_result(tmp_path, prediction)

    assert result["pass"] is False
    assert result["score"] == 0.0
    assert reason_fragment in result["reason"]


@pytest.mark.unit
def test_wrong_clip_id_hard_fails(tmp_path: Path) -> None:
    prediction = _perfect_prediction()
    prediction["clip_id"] = "another_clip"
    result = _assert_result(tmp_path, prediction)

    assert result["pass"] is False
    assert result["score"] < 0.70
    assert "clip_id" in result["reason"]


@pytest.mark.unit
def test_out_of_range_frame_index_hard_fails(tmp_path: Path) -> None:
    prediction = deepcopy(_perfect_prediction())
    prediction["evidence"][0]["frame_index"] = 5
    result = _assert_result(tmp_path, prediction)

    assert result["pass"] is False
    assert result["score"] < 0.70
    assert "frame_index" in result["reason"]
