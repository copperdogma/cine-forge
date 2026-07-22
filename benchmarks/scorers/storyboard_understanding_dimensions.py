"""Observable dimension scoring for storyboard packet analyses."""

from __future__ import annotations

import re
from collections.abc import Iterable

from cine_forge.schemas import (
    StoryboardAnalysisDimensionScore,
    StoryboardAnalysisPrediction,
    StoryboardAnalysisTarget,
)

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_NEGATION_RE = re.compile(r"\b(?:no|not|without|absent|missing|lacks?|never)\b")
_GENERIC_TRAIT_TOKENS = {
    "adult",
    "appears",
    "character",
    "figure",
    "human",
    "person",
    "prominent",
    "recurring",
    "subject",
}


def score_story_specificity(
    prediction: StoryboardAnalysisPrediction,
    target: StoryboardAnalysisTarget,
) -> StoryboardAnalysisDimensionScore:
    evidence_text = " ".join(item.cue for item in prediction.evidence)
    hits = [
        cue.cue_id
        for cue in target.required_visual_cues
        if any(_contains_positive_phrase(evidence_text, keyword) for keyword in cue.keywords)
    ]
    score = len(hits) / len(target.required_visual_cues)
    return _dimension(
        "story_specificity",
        score,
        0.7,
        f"Grounded visual cue groups matched: {len(hits)}/{len(target.required_visual_cues)}.",
    )


def score_style_consistency(
    prediction: StoryboardAnalysisPrediction,
    target: StoryboardAnalysisTarget,
) -> StoryboardAnalysisDimensionScore:
    assessment = prediction.style_assessment
    valid_halves = _ids_match_halves(
        first_ids=assessment.first_half_frame_ids,
        second_ids=assessment.second_half_frame_ids,
        frame_count=prediction.packet_frame_count,
    )
    first_text = " ".join(assessment.first_half_mediums)
    second_text = " ".join(assessment.second_half_mediums)
    expected_hits = sum(
        any(_contains_positive_phrase(f"{first_text} {second_text}", keyword) for keyword in group)
        for group in target.expected_style_keyword_groups
    )
    expected_score = expected_hits / len(target.expected_style_keyword_groups)
    overlap = _token_overlap(
        _tokens(assessment.first_half_mediums),
        _tokens(assessment.second_half_mediums),
    )
    score = (expected_score + overlap) / 2 if valid_halves else 0.0
    return _dimension(
        "style_consistency",
        score,
        0.6,
        (
            f"Expected medium groups: {expected_hits}/"
            f"{len(target.expected_style_keyword_groups)}; early/late overlap={overlap:.3f}; "
            f"half-bound evidence={'valid' if valid_halves else 'invalid'}."
        ),
    )


def score_identity_consistency(
    prediction: StoryboardAnalysisPrediction,
    target: StoryboardAnalysisTarget,
) -> StoryboardAnalysisDimensionScore:
    expected_names = [item.name for item in target.recurring_characters]
    assessments = prediction.character_assessments
    observed_names = [item.name for item in assessments]
    if observed_names != expected_names:
        return _dimension(
            "identity_consistency",
            0.0,
            0.6,
            f"Expected ordered subject slots {expected_names}; got {observed_names}.",
        )

    values: list[float] = []
    for assessment in assessments:
        first_tokens = _tokens(assessment.first_half_traits) - _GENERIC_TRAIT_TOKENS
        second_tokens = _tokens(assessment.second_half_traits) - _GENERIC_TRAIT_TOKENS
        valid_halves = _ids_match_halves(
            first_ids=assessment.first_half_frame_ids,
            second_ids=assessment.second_half_frame_ids,
            frame_count=prediction.packet_frame_count,
        )
        informative = len(first_tokens) >= 2 and len(second_tokens) >= 2
        values.append(
            _token_overlap(first_tokens, second_tokens) if valid_halves and informative else 0.0
        )
    score = sum(values) / len(values) if values else 1.0
    return _dimension(
        "identity_consistency",
        score,
        0.6,
        f"Derived early/late trait overlaps: {[round(value, 3) for value in values]}.",
    )


def score_reference_fidelity(
    prediction: StoryboardAnalysisPrediction,
    target: StoryboardAnalysisTarget,
) -> StoryboardAnalysisDimensionScore:
    expected_labels = [item.label for item in target.reference_expectations]
    observed_labels = [item.label for item in prediction.reference_assessments]
    if observed_labels != expected_labels:
        return _dimension(
            "reference_fidelity",
            0.0,
            1.0,
            f"Expected reference slots {expected_labels}; got {observed_labels}.",
        )
    if not target.reference_quality_evaluable:
        return _dimension(
            "reference_fidelity",
            1.0,
            1.0,
            "Reference cards are transport-only; visual fidelity is excluded from quality.",
        )
    valid_frames = _valid_frame_ids(prediction.packet_frame_count)
    values = [
        1.0
        if item.observed_similarities
        and item.generated_frame_ids
        and set(item.generated_frame_ids) <= valid_frames
        else 0.0
        for item in prediction.reference_assessments
    ]
    score = sum(values) / len(values) if values else 1.0
    return _dimension(
        "reference_fidelity",
        score,
        0.75,
        f"Grounded reference observations: {sum(value == 1.0 for value in values)}/{len(values)}.",
    )


def score_text_cleanliness(
    prediction: StoryboardAnalysisPrediction,
    target: StoryboardAnalysisTarget,
) -> StoryboardAnalysisDimensionScore:
    valid = _ids_are_valid(prediction.readable_text_frame_ids, prediction.packet_frame_count)
    clean = not target.should_avoid_readable_text or not prediction.readable_text_frame_ids
    score = 1.0 if valid and clean else 0.0
    return _dimension(
        "text_cleanliness",
        score,
        1.0,
        (
            "No readable text reported."
            if clean
            else f"Readable text reported in {prediction.readable_text_frame_ids}."
        ),
    )


def score_prop_discipline(
    prediction: StoryboardAnalysisPrediction,
    target: StoryboardAnalysisTarget,
) -> StoryboardAnalysisDimensionScore:
    valid = _ids_are_valid(prediction.prop_only_frame_ids, prediction.packet_frame_count)
    if not target.prop_discipline_evaluable:
        return _dimension(
            "prop_discipline",
            1.0 if valid else 0.0,
            1.0,
            "Shot-role truth is unavailable; prop discipline is excluded from quality.",
        )
    score = 1.0 if valid and not prediction.prop_only_frame_ids else 0.0
    return _dimension(
        "prop_discipline",
        score,
        1.0,
        f"Prop-only frame ids: {prediction.prop_only_frame_ids}.",
    )


def score_evidence(
    prediction: StoryboardAnalysisPrediction,
    target: StoryboardAnalysisTarget,
) -> StoryboardAnalysisDimensionScore:
    ids = [item.frame_id for item in prediction.evidence]
    valid_ids = _ids_are_valid(ids, prediction.packet_frame_count)
    unique_ids = len(ids) == len(set(ids))
    first, second = _split_frame_ids(prediction.packet_frame_count)
    spans_packet = bool(set(ids) & first) and bool(set(ids) & second)
    informative = all(len(_tokens([item.cue])) >= 2 for item in prediction.evidence)
    serialized = prediction.model_dump_json().lower()
    forbidden = [term for term in target.forbidden_output_terms if term.lower() in serialized]
    checks = [valid_ids, unique_ids, spans_packet, informative, not forbidden]
    score = sum(checks) / len(checks)
    return _dimension(
        "evidence",
        score,
        1.0,
        (
            f"valid_ids={valid_ids}; unique_ids={unique_ids}; spans_packet={spans_packet}; "
            f"informative={informative}; forbidden_terms={forbidden}."
        ),
    )


def _dimension(
    name: str,
    score: float,
    threshold: float,
    rationale: str,
) -> StoryboardAnalysisDimensionScore:
    bounded = max(0.0, min(1.0, score))
    return StoryboardAnalysisDimensionScore(
        dimension=name,
        score=round(bounded, 4),
        passed=bounded >= threshold,
        rationale=rationale,
    )


def _ids_match_halves(*, first_ids: list[str], second_ids: list[str], frame_count: int) -> bool:
    first, second = _split_frame_ids(frame_count)
    return (
        bool(first_ids)
        and bool(second_ids)
        and len(first_ids) == len(set(first_ids))
        and len(second_ids) == len(set(second_ids))
        and set(first_ids) <= first
        and set(second_ids) <= second
    )


def _ids_are_valid(ids: list[str], frame_count: int) -> bool:
    return len(ids) == len(set(ids)) and set(ids) <= _valid_frame_ids(frame_count)


def _valid_frame_ids(frame_count: int) -> set[str]:
    return {f"frame_{index:03d}" for index in range(1, frame_count + 1)}


def _split_frame_ids(frame_count: int) -> tuple[set[str], set[str]]:
    midpoint = (frame_count + 1) // 2
    first = {f"frame_{index:03d}" for index in range(1, midpoint + 1)}
    second = {f"frame_{index:03d}" for index in range(midpoint + 1, frame_count + 1)}
    return first, second


def _contains_positive_phrase(text: str, phrase: str) -> bool:
    lowered = text.lower()
    phrase_lower = phrase.lower()
    start = lowered.find(phrase_lower)
    while start >= 0:
        prefix = lowered[max(0, start - 28) : start]
        if not _NEGATION_RE.search(prefix):
            return True
        start = lowered.find(phrase_lower, start + len(phrase_lower))
    return False


def _tokens(values: Iterable[str]) -> set[str]:
    return {token for value in values for token in _TOKEN_RE.findall(value.lower())}


def _token_overlap(first: set[str], second: set[str]) -> float:
    if not first or not second:
        return 0.0
    return (2 * len(first & second)) / (len(first) + len(second))
