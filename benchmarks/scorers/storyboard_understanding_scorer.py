"""Deterministic scorer for storyboard-packet visual observations."""

from __future__ import annotations

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

from score_semantics import finalize_score  # noqa: E402

import cine_forge.schemas as _schemas  # noqa: E402

StoryboardAnalysisPrediction = _schemas.StoryboardAnalysisPrediction
StoryboardAnalysisScore = _schemas.StoryboardAnalysisScore
StoryboardAnalysisTarget = _schemas.StoryboardAnalysisTarget

import storyboard_understanding_dimensions as _dimensions  # noqa: E402

score_evidence = _dimensions.score_evidence
score_identity_consistency = _dimensions.score_identity_consistency
score_prop_discipline = _dimensions.score_prop_discipline
score_reference_fidelity = _dimensions.score_reference_fidelity
score_story_specificity = _dimensions.score_story_specificity
score_style_consistency = _dimensions.score_style_consistency
score_text_cleanliness = _dimensions.score_text_cleanliness

PROMPT_VERSION = "storyboard-understanding-v3"
PASS_THRESHOLD = 0.75


def get_assert(output: str, context: dict) -> dict:
    target_path = _resolve_relative(context.get("vars", {}).get("target_path", ""))
    try:
        score = score_output_against_target(
            output=output,
            target_path=target_path,
            model_label="promptfoo-provider",
            prompt_version=PROMPT_VERSION,
        )
        return finalize_score(
            score.overall_score,
            pass_threshold=PASS_THRESHOLD,
            hard_gates=score.hard_constraints_passed,
            reason=format_score_reason(score),
        )
    except Exception as exc:
        return {"pass": False, "score": 0.0, "reason": f"Scorer parse failure: {exc}"}


def score_output_against_target(
    *,
    output: str | dict[str, Any],
    target_path: Path,
    model_label: str,
    prompt_version: str | None,
) -> StoryboardAnalysisScore:
    del model_label
    if prompt_version != PROMPT_VERSION:
        raise ValueError(f"unsupported storyboard prompt contract: {prompt_version!r}")
    target = StoryboardAnalysisTarget.model_validate_json(target_path.read_text())
    prediction = parse_prediction(output)
    return score_prediction_against_target(prediction=prediction, target=target)


def parse_prediction(output: str | dict[str, Any]) -> StoryboardAnalysisPrediction:
    if isinstance(output, dict):
        return StoryboardAnalysisPrediction.model_validate(output)
    text = output.strip()
    if not text:
        raise ValueError("Empty provider output")
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError("Provider output must be one JSON object")
    return StoryboardAnalysisPrediction.model_validate(payload)


def score_prediction_against_target(
    *,
    prediction: StoryboardAnalysisPrediction,
    target: StoryboardAnalysisTarget,
) -> StoryboardAnalysisScore:
    dimensions = [
        score_story_specificity(prediction, target),
        score_style_consistency(prediction, target),
        score_identity_consistency(prediction, target),
        score_reference_fidelity(prediction, target),
        score_text_cleanliness(prediction, target),
        score_prop_discipline(prediction, target),
        score_evidence(prediction, target),
    ]
    by_name = {dimension.dimension: dimension for dimension in dimensions}
    weights = target.weights
    overall = sum(
        (
            by_name["story_specificity"].score * weights.story_specificity,
            by_name["style_consistency"].score * weights.style_consistency,
            by_name["identity_consistency"].score * weights.identity_consistency,
            by_name["reference_fidelity"].score * weights.reference_fidelity,
            by_name["text_cleanliness"].score * weights.text_cleanliness,
            by_name["prop_discipline"].score * weights.prop_discipline,
            by_name["evidence"].score * weights.evidence,
        )
    )
    packet_contract = _packet_contract_passes(prediction=prediction, target=target)
    hard_constraints = (
        packet_contract
        and by_name["evidence"].passed
        and by_name["story_specificity"].passed
        and by_name["style_consistency"].passed
        and by_name["identity_consistency"].passed
        and by_name["text_cleanliness"].passed
        and (not target.prop_discipline_evaluable or by_name["prop_discipline"].passed)
    )
    return StoryboardAnalysisScore(
        storyboard_id=target.storyboard_id,
        overall_score=round(overall, 4),
        hard_constraints_passed=hard_constraints,
        dimensions=dimensions,
    )


def format_score_reason(score: StoryboardAnalysisScore) -> str:
    parts = [f"{dimension.dimension}={dimension.score:.2f}" for dimension in score.dimensions]
    return (
        f"overall={score.overall_score:.4f}; "
        f"hard_constraints={'pass' if score.hard_constraints_passed else 'fail'}; "
        + ", ".join(parts)
    )


def _packet_contract_passes(
    *,
    prediction: StoryboardAnalysisPrediction,
    target: StoryboardAnalysisTarget,
) -> bool:
    return (
        prediction.storyboard_id == target.storyboard_id
        and target.expected_frame_min <= prediction.packet_frame_count <= target.expected_frame_max
        and prediction.packet_reference_count == len(target.reference_expectations)
    )


def _resolve_relative(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    candidates = [Path.cwd() / path, REPO_ROOT / path, REPO_ROOT / "benchmarks" / path]
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    return (REPO_ROOT / "benchmarks" / path).resolve()
