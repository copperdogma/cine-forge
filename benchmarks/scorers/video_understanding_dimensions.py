"""Observable-dimension scoring for ordered JPEG frame packets."""

from __future__ import annotations

import re

from video_understanding_contract import contains_explicit_audio_claim, duplicate_tag_fields

from cine_forge.schemas import (
    VideoAnalysisDimensionScore,
    VideoAnalysisPrediction,
    VideoAnalysisTarget,
)

_STOPWORDS = {
    "about",
    "after",
    "against",
    "before",
    "between",
    "camera",
    "clip",
    "during",
    "each",
    "frame",
    "from",
    "into",
    "light",
    "same",
    "scene",
    "shot",
    "that",
    "their",
    "there",
    "these",
    "this",
    "through",
    "toward",
    "with",
}

_AUDIO_ONLY_TAGS = {
    "drone",
    "heartbeat",
    "muzak",
    "percussion",
    "soft_music",
    "speech",
    "voiceover",
}


def score_keywords(
    *,
    dimension: str,
    haystack: str,
    required: list[str],
) -> VideoAnalysisDimensionScore:
    if not required:
        return _dimension(dimension, 1.0, rationale="No target keywords are required.")
    lowered = haystack.lower()
    matched = [keyword for keyword in required if keyword.lower() in lowered]
    missed = [keyword for keyword in required if keyword not in matched]
    return _dimension(
        dimension,
        len(matched) / len(required),
        matched=matched,
        missed=missed,
        rationale=(
            "Summary covered the required observable cues."
            if not missed
            else f"Missing summary cues: {', '.join(missed)}"
        ),
    )


def observable_required_keywords(target: VideoAnalysisTarget) -> list[str]:
    """Exclude target keywords whose only declared modality is unavailable audio."""
    unavailable = _AUDIO_ONLY_TAGS & set(target.audio_tags)
    return [
        keyword
        for keyword in target.required_keywords
        if keyword.lower().replace("-", "_").replace(" ", "_") not in unavailable
    ]


def score_tag_dimension(
    dimension: str,
    predicted: list[str],
    target: list[str],
) -> VideoAnalysisDimensionScore:
    """Use set F1 so all-tags predictions cannot exploit recall-only scoring."""
    predicted_set = set(predicted)
    target_set = set(target)
    matched = sorted(predicted_set & target_set)
    missing = sorted(target_set - predicted_set)
    extras = sorted(predicted_set - target_set)
    if not predicted_set and not target_set:
        score = 1.0
    elif not predicted_set or not target_set:
        score = 0.0
    else:
        precision = len(matched) / len(predicted_set)
        recall = len(matched) / len(target_set)
        score = _f1(precision, recall)
    missed = [*missing, *(f"unexpected={item}" for item in extras)]
    return _dimension(
        dimension,
        score,
        matched=matched,
        missed=missed,
        rationale=(
            "Tags matched the target exactly."
            if not missed
            else f"Tag mismatches: {', '.join(missed)}"
        ),
    )


def score_continuity(
    prediction: VideoAnalysisPrediction,
    target: VideoAnalysisTarget,
) -> VideoAnalysisDimensionScore:
    status_score = 1.0 if prediction.continuity_status == target.continuity_status else 0.0
    expected = target.continuity_notes
    predicted = prediction.continuity_notes
    matched_expected = [
        note for note in expected if any(note_matches(note, candidate) for candidate in predicted)
    ]
    extra_predicted = [
        note
        for note in predicted
        if not any(note_matches(candidate, note) for candidate in expected)
    ]
    if not expected and not predicted:
        notes_score = 1.0
    elif not expected or not predicted:
        notes_score = 0.0
    else:
        precision = (len(predicted) - len(extra_predicted)) / len(predicted)
        recall = len(matched_expected) / len(expected)
        notes_score = _f1(precision, recall)
    score = status_score * 0.75 + notes_score * 0.25
    missed: list[str] = []
    if status_score == 0.0:
        missed.append(f"status={target.continuity_status}")
    missed.extend(note for note in expected if note not in matched_expected)
    missed.extend(f"unexpected={note}" for note in extra_predicted)
    return _dimension(
        "continuity",
        score,
        matched=[target.continuity_status, *matched_expected] if status_score else matched_expected,
        missed=missed,
        rationale=(
            "Continuity status and notes matched the observable target."
            if not missed
            else f"Continuity mismatches: {', '.join(missed)}"
        ),
    )


def score_audio_unavailable(prediction: VideoAnalysisPrediction) -> VideoAnalysisDimensionScore:
    claims = [*prediction.audio_tags, *prediction.audio_notes]
    return _dimension(
        "audio",
        0.0,
        missed=["invented audio claim"] if claims else [],
        rationale=(
            "Audio is not scored because no audio was submitted."
            if not claims
            else "Audio claims are invalid because no audio was submitted."
        ),
    )


def score_evidence(
    prediction: VideoAnalysisPrediction,
    target: VideoAnalysisTarget,
) -> VideoAnalysisDimensionScore:
    failures = evidence_failures(prediction, target)
    invalid_indexes = {index for index, _reason in failures}
    valid_count = len(prediction.evidence) - len(invalid_indexes)
    if not prediction.evidence:
        score = 0.0
    else:
        precision = valid_count / len(prediction.evidence)
        coverage = min(valid_count / 2.0, 1.0)
        score = _f1(precision, coverage)
    missed = [f"item {index + 1}: {reason}" for index, reason in failures]
    if len(prediction.evidence) < 2:
        missed.append("at least 2 distinct evidence items")
    elif len(prediction.evidence) > 4:
        missed.append("at most 4 evidence items")
    matched = [
        f"frame {item.frame_index}"
        for index, item in enumerate(prediction.evidence)
        if index not in invalid_indexes
    ]
    return _dimension(
        "evidence",
        score,
        matched=matched,
        missed=missed,
        rationale=(
            "Evidence cites specific target-supported cues at submitted frame times."
            if not missed
            else "Evidence is missing, generic, invented, duplicated, or not tied to a frame."
        ),
    )


def score_hard_constraints(
    prediction: VideoAnalysisPrediction,
    target: VideoAnalysisTarget,
    *,
    expected_clip_id: str,
) -> VideoAnalysisDimensionScore:
    missed: list[str] = []
    if prediction.clip_id != expected_clip_id:
        missed.append("clip_id")
    if prediction.audio_tags or prediction.audio_notes:
        missed.append("audio_unavailable")
    narrative_text = " ".join(
        [
            prediction.summary,
            *prediction.continuity_notes,
            *(item.cue for item in prediction.evidence),
        ]
    )
    if contains_explicit_audio_claim(narrative_text):
        missed.append("invented_audio_narrative")
    missed.extend(f"duplicate_{field}" for field in duplicate_tag_fields(prediction))
    if not 2 <= len(prediction.evidence) <= 4:
        missed.append("evidence_count")
    evidence_issues = evidence_failures(prediction, target)
    missed.extend(f"evidence_{index + 1}_{reason}" for index, reason in evidence_issues)
    return _dimension(
        "hard_constraints",
        0.0 if missed else 1.0,
        matched=[] if missed else ["ordered frame packet contract"],
        missed=missed,
        rationale=(
            "Hard constraints satisfied."
            if not missed
            else f"Hard failures: {', '.join(missed)}"
        ),
    )


def evidence_failures(
    prediction: VideoAnalysisPrediction,
    target: VideoAnalysisTarget,
) -> list[tuple[int, str]]:
    """Return one deterministic reason per invalid evidence item."""
    failures: list[tuple[int, str]] = []
    cue_lexicon = observable_cue_tokens(target)
    seen_cues: set[str] = set()
    seen_items: set[tuple[int, str]] = set()
    for index, item in enumerate(prediction.evidence):
        normalized_cue = " ".join(item.cue.lower().split())
        item_key = (item.frame_index, normalized_cue)
        reason = ""
        if normalized_cue in seen_cues or item_key in seen_items:
            reason = "duplicate"
        elif not cue_is_grounded(item.cue, cue_lexicon):
            reason = "cue_not_target_grounded"
        if reason:
            failures.append((index, reason))
        seen_cues.add(normalized_cue)
        seen_items.add(item_key)
    return failures


def observable_cue_tokens(target: VideoAnalysisTarget) -> set[str]:
    """Build the best available cue lexicon without audio or answer metadata."""
    source_parts = [
        target.summary_reference,
        *target.required_keywords,
        *target.color_tags,
        *target.camera_tags,
        *target.motion_tags,
        *target.continuity_notes,
    ]
    tokens = set(tokenize(" ".join(source_parts)))
    unavailable_tokens = set(
        tokenize(" ".join(_AUDIO_ONLY_TAGS & set(target.audio_tags)))
    )
    return tokens - unavailable_tokens


def cue_is_grounded(cue: str, lexicon: set[str]) -> bool:
    tokens = tokenize(cue)
    if len(tokens) < 3:
        return False
    matches = {
        token
        for token in tokens
        if any(tokens_related(token, expected) for expected in lexicon)
    }
    return len(matches) >= 2


def tokenize(text: str) -> list[str]:
    return [
        token
        for token in re.split(r"[^a-z0-9]+", text.lower().replace("_", " "))
        if len(token) >= 3 and token not in _STOPWORDS
    ]


def tokens_related(left: str, right: str) -> bool:
    left_stem = _stem(left)
    right_stem = _stem(right)
    if left_stem == right_stem:
        return True
    shorter, longer = sorted((left_stem, right_stem), key=len)
    return len(shorter) >= 4 and longer.startswith(shorter)


def note_matches(expected_note: str | None, actual_note: str) -> bool:
    if not expected_note:
        return False
    expected = expected_note.lower()
    actual = actual_note.lower()
    if expected in actual or actual in expected:
        return True
    keywords = tokenize(expected)
    if not keywords:
        return False
    overlap = sum(
        1 for token in keywords if any(tokens_related(token, item) for item in tokenize(actual))
    )
    return overlap >= max(2, (len(keywords) + 1) // 2)


def _stem(token: str) -> str:
    for ending in ("ingly", "edly", "ing", "ed", "es", "s"):
        if token.endswith(ending) and len(token) - len(ending) >= 4:
            return token[: -len(ending)]
    return token


def _f1(precision: float, recall: float) -> float:
    return 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)


def _dimension(
    dimension: str,
    score: float,
    *,
    matched: list[str] | None = None,
    missed: list[str] | None = None,
    rationale: str,
) -> VideoAnalysisDimensionScore:
    return VideoAnalysisDimensionScore(
        dimension=dimension,
        score=max(0.0, min(1.0, score)),
        matched=matched or [],
        missed=missed or [],
        rationale=rationale,
    )
