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
dimensions = importlib.import_module("video_understanding_dimensions")


@pytest.mark.unit
def test_push_in_summary_accepts_visible_enlargement_wording() -> None:
    aliases = {
        "closer": (
            r"\b(?:become|becomes|became)\s+(?:(?:slightly|gradually)\s+)*(?:larger|bigger)\b",
        )
    }
    positive = dimensions.score_keywords(
        dimension="summary",
        haystack="Both figures gradually become slightly larger across the samples.",
        required=["closer"],
        equivalents=aliases,
    )
    static = dimensions.score_keywords(
        dimension="summary",
        haystack="Both figures remain at unchanged scale across the samples.",
        required=["closer"],
        equivalents=aliases,
    )
    negated = dimensions.score_keywords(
        dimension="summary",
        haystack="The figures do not become larger across the samples.",
        required=["closer"],
        equivalents=aliases,
    )
    relative_size = dimensions.score_keywords(
        dimension="summary",
        haystack="A larger figure stands beside a smaller figure throughout.",
        required=["closer"],
        equivalents=aliases,
    )
    assert positive.score == 1.0
    assert static.score == 0.0
    assert negated.score == 0.0
    assert relative_size.score == 0.0


@pytest.mark.unit
def test_temporal_enlargement_does_not_credit_a_static_or_negated_claim() -> None:
    alias = {"closer": (r"\bacross\s+(?:the\s+)?samples\b.{0,80}\benlarg\w*\b",)}

    def score(text: str) -> float:
        return dimensions.score_keywords(
            dimension="summary", haystack=text, required=["closer"], equivalents=alias
        ).score

    assert score("Across the samples, both figures subtly enlarge.") == 1.0
    assert score("Across the samples, both figures do not enlarge.") == 0.0
    assert score("A larger man stands still beside a smaller woman.") == 0.0


@pytest.mark.unit
def test_static_and_temporal_growth_equivalents_are_source_constrained() -> None:
    static_alias = {
        "static": (
            r"\b(?:composition|arrangement|positions?|scene|frame)\s+"
            r"(?:remains?|stays?)\s+(?:visually\s+|completely\s+)?"
            r"(?:unchanged|fixed)\b",
            r"\bno\s+(?:visible\s+)?(?:motion|movement|change)\b",
        )
    }

    def static_score(value: str) -> float:
        return dimensions.score_keywords(
            dimension="summary",
            haystack=value,
            required=["static"],
            equivalents=static_alias,
        ).score

    assert static_score("The composition remains unchanged across all five samples.") == 1.0
    assert static_score("The camera is static.") == 1.0
    assert static_score("The camera is not static.") == 0.0
    assert static_score("There is no motion across the samples.") == 1.0
    assert static_score("Positions changed while color remained unchanged.") == 0.0

    growth_alias = {
        "closer": (
            r"\bacross\s+(?:the\s+)?(?:ordered\s+)?(?:frames|samples)\b.{0,100}"
            r"\b(?:grow|grows|grew)\s+(?:slightly|gradually|visibly|progressively|larger|bigger)\b",
        )
    }

    def growth_score(value: str) -> float:
        return dimensions.score_keywords(
            dimension="summary",
            haystack=value,
            required=["closer"],
            equivalents=growth_alias,
        ).score

    assert growth_score("Across the samples, both figures grow slightly.") == 1.0
    assert growth_score("Across the samples, figures do not grow slightly.") == 0.0
    assert growth_score("One larger figure stands beside another throughout.") == 0.0


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
def test_excluded_ambiguous_camera_renormalizes_without_bypassing_hard_constraints(
    tmp_path: Path,
) -> None:
    target_path = _write_target(tmp_path)
    target = json.loads(target_path.read_text())
    target["excluded_dimensions"] = ["camera"]
    target_path.write_text(json.dumps(target))
    prediction = _perfect_prediction()
    prediction["camera_tags"] = []
    score = scorer.score_output_against_target(
        output=prediction,
        target_path=target_path,
        model_label="Control",
        prompt_version="frame-packet-v3",
    )
    assert score.overall_score == pytest.approx(1.0)
    assert next(x for x in score.dimensions if x.dimension == "camera").score == 0.0

    wrong_id = scorer.score_output_against_target(
        output=prediction,
        target_path=target_path,
        model_label="Control",
        prompt_version="frame-packet-v3",
        expected_clip_id="other-evaluation",
    )
    assert wrong_id.hard_constraints_passed is False
    assert wrong_id.overall_score < score.overall_score
    assert "hard_constraints" in wrong_id.rationale

    target["excluded_dimensions"] = ["hard_constraints"]
    target_path.write_text(json.dumps(target))
    with pytest.raises(ValueError, match="cannot mask"):
        scorer.score_output_against_target(
            output=prediction,
            target_path=target_path,
            model_label="Control",
            prompt_version="frame-packet-v3",
        )


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


@pytest.mark.unit
@pytest.mark.parametrize(
    "summary",
    [
        "Two blue figures hold their positions; across the samples both gradually grow taller.",
        "An unchanging composition shows the two shapes beside a gray rectangle.",
        "Nothing visibly moves or changes across the samples.",
    ],
)
def test_source_equivalent_temporal_summary_words(summary):
    target_case = "dialogue_confession_push_in" if "taller" in summary else "quiet_bedside_vigil"
    target = scorer.VideoAnalysisTarget.model_validate_json(
        (
            REPO_ROOT / "benchmarks/video_understanding_truth_v4" / target_case / "target.json"
        ).read_text()
    )
    prediction = _perfect_prediction()
    prediction["summary"] = summary
    prediction["clip_id"] = target.clip_id
    scored = scorer.score_prediction_against_target(
        prediction=scorer.VideoAnalysisPrediction.model_validate(prediction),
        target=target,
        model_label="source-equivalent",
        prompt_version=None,
    )
    summary_score = next(x for x in scored.dimensions if x.dimension == "summary")
    assert ("closer" if "taller" in summary else "static") not in summary_score.missed


@pytest.mark.unit
def test_source_cue_geometry_does_not_require_semantic_action_names():
    target = scorer.VideoAnalysisTarget.model_validate_json(
        (
            REPO_ROOT
            / "benchmarks/video_understanding_truth_v4/storm_tunnel_lateral_run/target.json"
        ).read_text()
    )
    lexicon = dimensions.observable_cue_tokens(target)
    assert dimensions.cue_is_grounded("The figure is near the center beneath the arch.", lexicon)
    assert not dimensions.cue_is_grounded(
        "A police helicopter explodes above a burning car.", lexicon
    )
    assert not dimensions.cue_is_grounded("An arch is visible.", {"red", "table", "rectangle"})
