"""Deterministic scorer for storyboard-sequence quality analysis."""

from __future__ import annotations

import importlib
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

_schemas = importlib.import_module("cine_forge.schemas")
StoryboardAnalysisDimensionScore = _schemas.StoryboardAnalysisDimensionScore
StoryboardAnalysisPrediction = _schemas.StoryboardAnalysisPrediction
StoryboardAnalysisScore = _schemas.StoryboardAnalysisScore
StoryboardAnalysisTarget = _schemas.StoryboardAnalysisTarget

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)

_IDENTITY_STATUS_SCORE = {
    "consistent": 1.0,
    "minor_drift": 0.5,
    "drifted": 0.0,
    "absent": 0.0,
}
_REFERENCE_STATUS_SCORE = {
    "matched": 1.0,
    "unclear": 0.5,
    "ignored": 0.0,
    "not_supplied": 0.0,
}


def get_assert(output: str, context: dict) -> dict:
    vars_data = context.get("vars", {})
    target_path = _resolve_relative(vars_data.get("target_path", ""))
    try:
        score = score_output_against_target(
            output=output,
            target_path=target_path,
            model_label="promptfoo-provider",
            prompt_version="storyboard-understanding-v1",
        )
        return {
            "pass": score.hard_constraints_passed and score.overall_score >= 0.75,
            "score": round(score.overall_score, 4),
            "reason": format_score_reason(score),
        }
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
) -> StoryboardAnalysisScore:
    del model_label, prompt_version
    target = StoryboardAnalysisTarget.model_validate(json.loads(target_path.read_text()))
    prediction = parse_prediction(output)
    return score_prediction_against_target(prediction=prediction, target=target)


def parse_prediction(output: str | dict[str, Any]) -> StoryboardAnalysisPrediction:
    if isinstance(output, dict):
        return StoryboardAnalysisPrediction.model_validate(
            _normalize_prediction_payload(output)
        )

    text = output.strip()
    if not text:
        raise ValueError("Empty provider output")

    try:
        return StoryboardAnalysisPrediction.model_validate(
            _normalize_prediction_payload(json.loads(text))
        )
    except json.JSONDecodeError:
        pass

    fenced = _JSON_FENCE_RE.search(text)
    if fenced:
        return StoryboardAnalysisPrediction.model_validate(
            _normalize_prediction_payload(json.loads(fenced.group(1)))
        )

    candidate = _extract_json_object(text)
    if candidate:
        return StoryboardAnalysisPrediction.model_validate(
            _normalize_prediction_payload(json.loads(candidate))
        )

    raise ValueError("Could not parse model output as JSON")


def score_prediction_against_target(
    *,
    prediction: StoryboardAnalysisPrediction,
    target: StoryboardAnalysisTarget,
) -> StoryboardAnalysisScore:
    story_dimension = _score_story_specificity(prediction=prediction, target=target)
    style_dimension = _score_style_consistency(prediction=prediction)
    identity_dimension = _score_identity_consistency(prediction=prediction, target=target)
    reference_dimension = _score_reference_fidelity(prediction=prediction, target=target)
    text_dimension = _score_text_cleanliness(prediction=prediction, target=target)
    prop_dimension = _score_prop_discipline(prediction=prediction, target=target)
    evidence_dimension = _score_evidence(prediction=prediction)

    dimensions = [
        story_dimension,
        style_dimension,
        identity_dimension,
        reference_dimension,
        text_dimension,
        prop_dimension,
        evidence_dimension,
    ]

    weights = target.weights
    overall = round(
        story_dimension.score * weights.story_specificity
        + style_dimension.score * weights.style_consistency
        + identity_dimension.score * weights.identity_consistency
        + reference_dimension.score * weights.reference_fidelity
        + text_dimension.score * weights.text_cleanliness
        + prop_dimension.score * weights.prop_discipline
        + evidence_dimension.score * weights.evidence,
        4,
    )

    hard_constraints_passed = text_dimension.passed and prop_dimension.passed
    return StoryboardAnalysisScore(
        storyboard_id=target.storyboard_id,
        overall_score=overall,
        hard_constraints_passed=hard_constraints_passed,
        dimensions=dimensions,
    )


def format_score_reason(score: StoryboardAnalysisScore) -> str:
    parts = [
        f"{dimension.dimension}={dimension.score:.2f}"
        for dimension in score.dimensions
    ]
    return (
        f"overall={score.overall_score:.4f}; "
        f"hard_constraints={'pass' if score.hard_constraints_passed else 'fail'}; "
        + ", ".join(parts)
    )


def _score_story_specificity(
    *,
    prediction: StoryboardAnalysisPrediction,
    target: StoryboardAnalysisTarget,
) -> StoryboardAnalysisDimensionScore:
    if not target.required_keywords:
        return StoryboardAnalysisDimensionScore(
            dimension="story_specificity",
            score=1.0,
            passed=True,
            rationale="No required keywords defined.",
        )
    combined = " ".join([prediction.summary, *prediction.keywords]).lower()
    hits = sum(1 for keyword in target.required_keywords if keyword.lower() in combined)
    score = hits / len(target.required_keywords)
    return StoryboardAnalysisDimensionScore(
        dimension="story_specificity",
        score=round(score, 4),
        passed=score >= 0.6,
        rationale=f"Matched {hits}/{len(target.required_keywords)} required keywords.",
    )


def _score_style_consistency(
    *,
    prediction: StoryboardAnalysisPrediction,
) -> StoryboardAnalysisDimensionScore:
    if prediction.style_assessment is None:
        return StoryboardAnalysisDimensionScore(
            dimension="style_consistency",
            score=0.5,
            passed=False,
            rationale="No explicit visual style consistency assessment.",
        )
    score = _IDENTITY_STATUS_SCORE.get(prediction.style_assessment.consistency_status, 0.0)
    mediums = ", ".join(prediction.style_assessment.observed_mediums) or "unspecified medium"
    return StoryboardAnalysisDimensionScore(
        dimension="style_consistency",
        score=round(score, 4),
        passed=score >= 0.6,
        rationale=f"Style status {prediction.style_assessment.consistency_status}; {mediums}.",
    )


def _score_identity_consistency(
    *,
    prediction: StoryboardAnalysisPrediction,
    target: StoryboardAnalysisTarget,
) -> StoryboardAnalysisDimensionScore:
    if not target.recurring_characters:
        return StoryboardAnalysisDimensionScore(
            dimension="identity_consistency",
            score=1.0,
            passed=True,
            rationale="No recurring characters defined.",
        )
    assessments = {_slug(item.name): item for item in prediction.character_assessments}
    values: list[float] = []
    missing: list[str] = []
    for character in target.recurring_characters:
        assessment = assessments.get(_slug(character.name))
        if assessment is None:
            values.append(0.0)
            missing.append(character.name)
            continue
        values.append(_IDENTITY_STATUS_SCORE.get(assessment.consistency_status, 0.0))
    score = sum(values) / len(values)
    rationale = "All recurring characters assessed." if not missing else (
        "Missing assessments for " + ", ".join(missing) + "."
    )
    return StoryboardAnalysisDimensionScore(
        dimension="identity_consistency",
        score=round(score, 4),
        passed=score >= 0.6,
        rationale=rationale,
    )


def _score_reference_fidelity(
    *,
    prediction: StoryboardAnalysisPrediction,
    target: StoryboardAnalysisTarget,
) -> StoryboardAnalysisDimensionScore:
    if not target.reference_expectations:
        return StoryboardAnalysisDimensionScore(
            dimension="reference_fidelity",
            score=1.0,
            passed=True,
            rationale="No reference expectations defined.",
        )
    assessments = {_slug(item.label): item for item in prediction.reference_assessments}
    values: list[float] = []
    missing: list[str] = []
    for reference in target.reference_expectations:
        assessment = assessments.get(_slug(reference.label))
        if assessment is None:
            values.append(0.0)
            missing.append(reference.label)
            continue
        values.append(_REFERENCE_STATUS_SCORE.get(assessment.status, 0.0))
    score = sum(values) / len(values)
    rationale = "All reference lanes assessed." if not missing else (
        "Missing assessments for " + ", ".join(missing) + "."
    )
    return StoryboardAnalysisDimensionScore(
        dimension="reference_fidelity",
        score=round(score, 4),
        passed=score >= 0.5,
        rationale=rationale,
    )


def _score_text_cleanliness(
    *,
    prediction: StoryboardAnalysisPrediction,
    target: StoryboardAnalysisTarget,
) -> StoryboardAnalysisDimensionScore:
    score = 0.0 if (target.should_avoid_readable_text and prediction.readable_text_present) else 1.0
    rationale = (
        "Readable text detected in storyboard frames."
        if score == 0.0
        else "No readable storyboard text detected."
    )
    return StoryboardAnalysisDimensionScore(
        dimension="text_cleanliness",
        score=score,
        passed=score >= 1.0,
        rationale=rationale,
    )


def _score_prop_discipline(
    *,
    prediction: StoryboardAnalysisPrediction,
    target: StoryboardAnalysisTarget,
) -> StoryboardAnalysisDimensionScore:
    score = (
        0.0
        if (target.should_avoid_prop_only_non_insert and prediction.prop_only_non_insert_present)
        else 1.0
    )
    rationale = (
        "Non-insert prop-only collapse detected."
        if score == 0.0
        else "No non-insert prop-only collapse detected."
    )
    return StoryboardAnalysisDimensionScore(
        dimension="prop_discipline",
        score=score,
        passed=score >= 1.0,
        rationale=rationale,
    )


def _score_evidence(prediction: StoryboardAnalysisPrediction) -> StoryboardAnalysisDimensionScore:
    evidence_count = len(prediction.evidence)
    if 2 <= evidence_count <= 4 and all(item.cue.strip() for item in prediction.evidence):
        score = 1.0
    elif evidence_count >= 1:
        score = 0.5
    else:
        score = 0.0
    return StoryboardAnalysisDimensionScore(
        dimension="evidence",
        score=score,
        passed=score >= 0.5,
        rationale=f"Evidence items: {evidence_count}.",
    )


def _extract_json_object(text: str) -> str | None:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    return text[start : end + 1]


def _normalize_prediction_payload(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(payload)
    evidence = normalized.get("evidence")
    if not isinstance(evidence, list):
        return normalized

    normalized_evidence: list[Any] = []
    for item in evidence:
        if not isinstance(item, dict):
            normalized_evidence.append(item)
            continue
        normalized_item = dict(item)
        frame_id = normalized_item.get("frame_id")
        if frame_id is not None and not isinstance(frame_id, str):
            normalized_item["frame_id"] = str(frame_id)
        normalized_evidence.append(normalized_item)
    normalized["evidence"] = normalized_evidence
    return normalized


def _resolve_relative(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path

    candidates = [
        Path.cwd() / path,
        REPO_ROOT / path,
        REPO_ROOT / "benchmarks" / path,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()

    return (REPO_ROOT / "benchmarks" / path).resolve()


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")
