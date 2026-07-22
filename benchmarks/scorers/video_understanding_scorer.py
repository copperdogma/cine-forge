"""Deterministic scorer for ordered-JPEG frame-packet comprehension."""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
SCORER_ROOT = Path(__file__).resolve().parent
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))
if str(SCORER_ROOT) not in sys.path:
    sys.path.insert(0, str(SCORER_ROOT))

_schemas = importlib.import_module("cine_forge.schemas")
VideoAnalysisPrediction = _schemas.VideoAnalysisPrediction
VideoAnalysisScore = _schemas.VideoAnalysisScore
VideoAnalysisTarget = _schemas.VideoAnalysisTarget

_contract = importlib.import_module("video_understanding_contract")
_normalize_prediction_payload = _contract.normalize_prediction_payload
_normalize_tag_list = _contract.normalize_tag_list

_dimensions = importlib.import_module("video_understanding_dimensions")
_score_semantics = importlib.import_module("score_semantics")
finalize_score = _score_semantics.finalize_score
_score_audio = _dimensions.score_audio_unavailable
_score_continuity = _dimensions.score_continuity
_score_evidence = _dimensions.score_evidence
_score_hard_constraints = _dimensions.score_hard_constraints
_score_keywords = _dimensions.score_keywords
_score_tag_dimension = _dimensions.score_tag_dimension
_observable_required_keywords = _dimensions.observable_required_keywords

_OBSERVABLE_DIMENSIONS = (
    "summary",
    "tone",
    "emotion",
    "color",
    "camera",
    "motion",
    "continuity",
    "evidence",
)
PASS_THRESHOLD = 0.70


def get_assert(output: str, context: dict) -> dict:
    """Promptfoo assertion entry point."""
    vars_data = context.get("vars", {})
    target_path = _resolve_relative(vars_data.get("target_path", ""))
    evaluation_id = str(vars_data.get("evaluation_id", "")).strip()
    try:
        if not evaluation_id:
            raise ValueError("evaluation_id test var is required")
        score = score_output_against_target(
            output=output,
            target_path=target_path,
            model_label="promptfoo-provider",
            prompt_version="video-understanding-frame-packet-v3",
            expected_clip_id=evaluation_id,
        )
        return finalize_score(
            score.overall_score,
            pass_threshold=PASS_THRESHOLD,
            hard_gates=score.hard_constraints_passed,
            reason=format_score_reason(score),
        )
    except Exception as exc:
        return {
            "pass": False,
            "score": 0.0,
            "reason": f"Scorer parse failure: {exc}",
        }


def score_output_against_target(
    *,
    output: str | dict[str, Any],
    target_path: Path,
    model_label: str,
    prompt_version: str | None,
    expected_clip_id: str | None = None,
) -> VideoAnalysisScore:
    target = VideoAnalysisTarget.model_validate(json.loads(target_path.read_text()))
    prediction = parse_prediction(output)
    return score_prediction_against_target(
        prediction=prediction,
        target=target,
        model_label=model_label,
        prompt_version=prompt_version,
        expected_clip_id=expected_clip_id,
    )


def parse_prediction(output: str | dict[str, Any]) -> VideoAnalysisPrediction:
    """Parse strict JSON while rejecting missing, extra, duplicate, or unknown tags."""
    if isinstance(output, dict):
        return VideoAnalysisPrediction.model_validate(_normalize_prediction_payload(output))

    text = output.strip()
    if not text:
        raise ValueError("Empty provider output")

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        message = "Prediction must be one strict JSON object with no prose or fences"
        raise ValueError(message) from exc
    if not isinstance(payload, dict):
        raise ValueError("Prediction must be one JSON object")
    return VideoAnalysisPrediction.model_validate(_normalize_prediction_payload(payload))


def score_prediction_against_target(
    *,
    prediction: VideoAnalysisPrediction,
    target: VideoAnalysisTarget,
    model_label: str,
    prompt_version: str | None,
    expected_clip_id: str | None = None,
) -> VideoAnalysisScore:
    """Score only dimensions observable from the submitted ordered JPEGs."""
    dimensions = {
        "summary": _score_keywords(
            dimension="summary",
            haystack=prediction.summary,
            required=_observable_required_keywords(target),
        ),
        "tone": _score_tag_dimension("tone", prediction.tone_tags, target.tone_tags),
        "emotion": _score_tag_dimension(
            "emotion", prediction.emotion_tags, target.emotion_tags
        ),
        "color": _score_tag_dimension("color", prediction.color_tags, target.color_tags),
        "camera": _score_tag_dimension("camera", prediction.camera_tags, target.camera_tags),
        "motion": _score_tag_dimension("motion", prediction.motion_tags, target.motion_tags),
        "continuity": _score_continuity(prediction, target),
        "audio": _score_audio(prediction),
        "evidence": _score_evidence(prediction, target),
    }
    hard_dimension = _score_hard_constraints(
        prediction,
        target,
        expected_clip_id=expected_clip_id or target.clip_id,
    )

    raw_weights = target.weights.model_dump()
    observable_weight = sum(raw_weights[name] for name in _OBSERVABLE_DIMENSIONS)
    if observable_weight <= 0:
        raise ValueError("Target assigns no weight to observable frame dimensions")
    overall_score = sum(
        dimensions[name].score * raw_weights[name] for name in _OBSERVABLE_DIMENSIONS
    ) / observable_weight
    if not hard_dimension.score:
        overall_score *= 0.5

    ordered_dimensions = [
        dimensions["summary"],
        dimensions["tone"],
        dimensions["emotion"],
        dimensions["color"],
        dimensions["camera"],
        dimensions["motion"],
        dimensions["continuity"],
        dimensions["audio"],
        dimensions["evidence"],
        hard_dimension,
    ]
    missed = [
        f"{dimension.dimension}: {', '.join(dimension.missed)}"
        for dimension in ordered_dimensions
        if dimension.missed
    ]
    uncertainty = min(
        1.0,
        max(
            0.0,
            (1.0 - prediction.overall_confidence)
            + (0.15 if not hard_dimension.score else 0.0),
        ),
    )
    rationale = " | ".join(missed) if missed else "Prediction matched the frame target."

    return VideoAnalysisScore(
        clip_id=target.clip_id,
        model_label=model_label,
        overall_score=round(overall_score, 4),
        uncertainty=round(uncertainty, 4),
        hard_constraints_passed=bool(hard_dimension.score),
        dimensions=ordered_dimensions,
        rationale=rationale,
        prompt_version=prompt_version,
    )


def format_score_reason(score: VideoAnalysisScore) -> str:
    parts = [f"overall={score.overall_score:.3f}", f"uncertainty={score.uncertainty:.3f}"]
    parts.extend(
        f"{dimension.dimension}={dimension.score:.2f}" for dimension in score.dimensions
    )
    parts.append(score.rationale)
    return " | ".join(parts)


def _resolve_relative(value: str) -> Path:
    if not value:
        raise ValueError("target_path test var is required")
    path = Path(value)
    if path.is_absolute():
        return path
    return (REPO_ROOT / "benchmarks" / value).resolve()
