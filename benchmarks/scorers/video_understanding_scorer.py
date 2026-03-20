"""Deterministic scorer for the Story 030 video-understanding benchmark."""

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
VideoAnalysisDimensionScore = _schemas.VideoAnalysisDimensionScore
VideoAnalysisPrediction = _schemas.VideoAnalysisPrediction
VideoAnalysisScore = _schemas.VideoAnalysisScore
VideoAnalysisTarget = _schemas.VideoAnalysisTarget

_TAG_ALIASES: dict[str, dict[str, str]] = {
    "tone_tags": {
        "melancholic": "mournful",
        "melancholy": "mournful",
        "warm": "hopeful",
        "threatening": "ominous",
    },
    "emotion_tags": {
        "awe": "wonder",
        "care": "tenderness",
        "determination": "resolve",
        "fear": "panic",
        "loneliness": "isolation",
        "regret": "vulnerability",
        "sadness": "grief",
    },
    "color_tags": {
        "blue": "navy",
        "cool_blue": "navy",
        "cyan": "teal",
        "purple": "violet",
    },
    "camera_tags": {
        "close_up_profile": "profile_closeup",
        "push_in": "slow_push_in",
        "pull_back": "slow_pull_back",
        "two_shot": "locked_two_shot",
        "zoom_in": "crash_zoom",
    },
    "motion_tags": {
        "calm": "stillness",
        "drifting": "slow_drift",
        "fast": "fast_lateral",
        "strobe": "pulsing_light",
    },
    "audio_tags": {
        "music": "soft_music",
        "piano": "soft_music",
        "silence": "silent",
        "siren": "alarm",
        "voice": "speech",
    },
}

_ALLOWED_TAGS: dict[str, set[str]] = {
    field_name: set(alias_map.values()) | set(alias_map.keys())
    for field_name, alias_map in _TAG_ALIASES.items()
}
_ALLOWED_TAGS.update(
    {
        "tone_tags": {
            "detached",
            "hopeful",
            "intimate",
            "mournful",
            "nostalgic",
            "ominous",
            "playful",
            "regretful",
            "surreal",
            "tense",
            "triumphant",
            "urgent",
        },
        "emotion_tags": {
            "anger",
            "grief",
            "hesitation",
            "isolation",
            "nostalgia",
            "panic",
            "relief",
            "resolve",
            "suspicion",
            "tenderness",
            "vulnerability",
            "wonder",
        },
        "color_tags": {
            "amber",
            "desaturated",
            "gold",
            "green",
            "magenta",
            "monochrome",
            "navy",
            "neon",
            "red",
            "sepia",
            "teal",
            "violet",
        },
        "camera_tags": {
            "cross_cut",
            "crash_zoom",
            "handheld_jitter",
            "lateral_track",
            "locked_two_shot",
            "overhead_reveal",
            "profile_closeup",
            "slow_pull_back",
            "slow_push_in",
            "static",
            "whip_pan",
            "wide_master",
        },
        "motion_tags": {
            "abrupt_cut",
            "escalating",
            "fast_lateral",
            "jitter",
            "match_cut",
            "measured",
            "pulsing_light",
            "slow_drift",
            "spiral_orbit",
            "stillness",
        },
        "audio_tags": {
            "alarm",
            "drone",
            "heartbeat",
            "muzak",
            "percussion",
            "radio",
            "silent",
            "soft_music",
            "speech",
            "voiceover",
        },
    }
)


def get_assert(output: str, context: dict) -> dict:
    """Promptfoo assertion entry point."""
    vars_data = context.get("vars", {})
    target_path = _resolve_relative(vars_data.get("target_path", ""))
    try:
        score = score_output_against_target(
            output=output,
            target_path=target_path,
            model_label="promptfoo-provider",
            prompt_version="video-understanding-v1",
        )
        return {
            "pass": score.hard_constraints_passed and score.overall_score >= 0.70,
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
) -> VideoAnalysisScore:
    target = VideoAnalysisTarget.model_validate(json.loads(target_path.read_text()))
    prediction = parse_prediction(output)
    return score_prediction_against_target(
        prediction=prediction,
        target=target,
        model_label=model_label,
        prompt_version=prompt_version,
    )


def parse_prediction(output: str | dict[str, Any]) -> VideoAnalysisPrediction:
    if isinstance(output, dict):
        return VideoAnalysisPrediction.model_validate(_normalize_prediction_payload(output))

    text = output.strip()
    if not text:
        raise ValueError("Empty provider output")

    try:
        return VideoAnalysisPrediction.model_validate(
            _normalize_prediction_payload(json.loads(text))
        )
    except json.JSONDecodeError:
        pass

    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fenced:
        return VideoAnalysisPrediction.model_validate(
            _normalize_prediction_payload(json.loads(fenced.group(1)))
        )

    candidate = _extract_json_object(text)
    if candidate:
        return VideoAnalysisPrediction.model_validate(
            _normalize_prediction_payload(json.loads(candidate))
        )

    raise ValueError("Could not parse model output as JSON")


def _normalize_prediction_payload(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(payload)
    for field_name in ("continuity_notes", "audio_notes"):
        value = normalized.get(field_name)
        if isinstance(value, str):
            normalized[field_name] = [value]
    for field_name in (
        "tone_tags",
        "emotion_tags",
        "color_tags",
        "camera_tags",
        "motion_tags",
        "audio_tags",
    ):
        normalized[field_name] = _normalize_tag_list(
            normalized.get(field_name, []),
            field_name=field_name,
        )
    return normalized


def _normalize_tag_list(value: Any, *, field_name: str) -> list[str]:
    if isinstance(value, str):
        raw_items = [value]
    else:
        raw_items = list(value or [])
    normalized_items = []
    allowed = _ALLOWED_TAGS[field_name]
    aliases = _TAG_ALIASES.get(field_name, {})
    for item in raw_items:
        candidate = str(item).strip().lower().replace("-", "_").replace(" ", "_")
        if candidate in aliases:
            candidate = aliases[candidate]
        if candidate in allowed:
            normalized_items.append(candidate)
    return normalized_items


def score_prediction_against_target(
    *,
    prediction: VideoAnalysisPrediction,
    target: VideoAnalysisTarget,
    model_label: str,
    prompt_version: str | None,
) -> VideoAnalysisScore:
    summary_text = " ".join(
        [
            prediction.summary,
            *prediction.continuity_notes,
            *prediction.audio_notes,
            *(item.cue for item in prediction.evidence),
        ]
    ).lower()

    summary_dimension = _score_keywords(
        dimension="summary",
        haystack=summary_text,
        required=target.required_keywords,
        positive_rationale="Summary covered the required keywords.",
    )
    tone_dimension = _score_tag_dimension("tone", prediction.tone_tags, target.tone_tags)
    emotion_dimension = _score_tag_dimension(
        "emotion",
        prediction.emotion_tags,
        target.emotion_tags,
    )
    color_dimension = _score_tag_dimension("color", prediction.color_tags, target.color_tags)
    camera_dimension = _score_tag_dimension("camera", prediction.camera_tags, target.camera_tags)
    motion_dimension = _score_tag_dimension("motion", prediction.motion_tags, target.motion_tags)
    continuity_dimension = _score_continuity(prediction, target)
    audio_dimension = _score_audio(prediction, target)
    evidence_dimension = _score_evidence(prediction, target)
    hard_dimension = _score_hard_constraints(prediction, target)

    weighted = {
        "summary": summary_dimension.score * target.weights.summary,
        "tone": tone_dimension.score * target.weights.tone,
        "emotion": emotion_dimension.score * target.weights.emotion,
        "color": color_dimension.score * target.weights.color,
        "camera": camera_dimension.score * target.weights.camera,
        "motion": motion_dimension.score * target.weights.motion,
        "continuity": continuity_dimension.score * target.weights.continuity,
        "audio": audio_dimension.score * target.weights.audio,
        "evidence": evidence_dimension.score * target.weights.evidence,
    }
    overall_score = sum(weighted.values())
    if not hard_dimension.score:
        overall_score *= 0.5

    missed = []
    for dimension in (
        summary_dimension,
        tone_dimension,
        emotion_dimension,
        color_dimension,
        camera_dimension,
        motion_dimension,
        continuity_dimension,
        audio_dimension,
        evidence_dimension,
        hard_dimension,
    ):
        if dimension.missed:
            missed.append(f"{dimension.dimension}: {', '.join(dimension.missed)}")

    uncertainty = min(
        1.0,
        max(
            0.0,
            (1.0 - prediction.overall_confidence) + (0.15 if not hard_dimension.score else 0.0),
        ),
    )
    rationale = " | ".join(missed) if missed else "Prediction aligned with the normalized target."

    return VideoAnalysisScore(
        clip_id=target.clip_id,
        model_label=model_label,
        overall_score=round(overall_score, 4),
        uncertainty=round(uncertainty, 4),
        hard_constraints_passed=bool(hard_dimension.score),
        dimensions=[
            summary_dimension,
            tone_dimension,
            emotion_dimension,
            color_dimension,
            camera_dimension,
            motion_dimension,
            continuity_dimension,
            audio_dimension,
            evidence_dimension,
            hard_dimension,
        ],
        rationale=rationale,
        prompt_version=prompt_version,
    )


def format_score_reason(score: VideoAnalysisScore) -> str:
    parts = [f"overall={score.overall_score:.3f}", f"uncertainty={score.uncertainty:.3f}"]
    for dimension in score.dimensions:
        parts.append(f"{dimension.dimension}={dimension.score:.2f}")
    parts.append(score.rationale)
    return " | ".join(parts)


def _resolve_relative(value: str) -> Path:
    if not value:
        raise ValueError("target_path test var is required")
    path = Path(value)
    if path.is_absolute():
        return path
    return (REPO_ROOT / "benchmarks" / value).resolve()


def _extract_json_object(text: str) -> str | None:
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    for idx, char in enumerate(text[start:], start=start):
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : idx + 1]
    return None


def _score_keywords(
    *,
    dimension: str,
    haystack: str,
    required: list[str],
    positive_rationale: str,
) -> VideoAnalysisDimensionScore:
    if not required:
        return VideoAnalysisDimensionScore(
            dimension=dimension,
            score=1.0,
            matched=[],
            missed=[],
            rationale="No normalized keywords were required.",
        )
    matched = [keyword for keyword in required if keyword.lower() in haystack]
    missed = [keyword for keyword in required if keyword not in matched]
    score = len(matched) / len(required)
    rationale = positive_rationale if not missed else f"Missing keywords: {', '.join(missed)}"
    return VideoAnalysisDimensionScore(
        dimension=dimension,
        score=score,
        matched=matched,
        missed=missed,
        rationale=rationale,
    )


def _score_tag_dimension(
    dimension: str,
    predicted: list[str],
    target: list[str],
) -> VideoAnalysisDimensionScore:
    if not target:
        return VideoAnalysisDimensionScore(
            dimension=dimension,
            score=1.0,
            matched=[],
            missed=[],
            rationale="No target tags were required for this dimension.",
        )
    matched = sorted(set(predicted) & set(target))
    missed = sorted(set(target) - set(predicted))
    score = len(matched) / len(target)
    rationale = (
        "Matched the normalized target tags."
        if not missed
        else f"Missing target tags: {', '.join(missed)}"
    )
    return VideoAnalysisDimensionScore(
        dimension=dimension,
        score=score,
        matched=matched,
        missed=missed,
        rationale=rationale,
    )


def _score_continuity(
    prediction: VideoAnalysisPrediction,
    target: VideoAnalysisTarget,
) -> VideoAnalysisDimensionScore:
    status_score = 0.8 if prediction.continuity_status == target.continuity_status else 0.0
    notes_text = " ".join(prediction.continuity_notes).lower()
    matched_notes = [note for note in target.continuity_notes if _note_matches(note, notes_text)]
    note_score = 0.2 if not target.continuity_notes else 0.2 * (
        len(matched_notes) / len(target.continuity_notes)
    )
    score = min(status_score + note_score, 1.0)
    missed = []
    if prediction.continuity_status != target.continuity_status:
        missed.append(f"status={target.continuity_status}")
    for note in target.continuity_notes:
        if note not in matched_notes:
            missed.append(note)
    return VideoAnalysisDimensionScore(
        dimension="continuity",
        score=score,
        matched=[target.continuity_status, *matched_notes],
        missed=missed,
        rationale=(
            "Continuity status and notes matched the target."
            if not missed
            else f"Continuity mismatches: {', '.join(missed)}"
        ),
    )


def _score_audio(
    prediction: VideoAnalysisPrediction,
    target: VideoAnalysisTarget,
) -> VideoAnalysisDimensionScore:
    if not target.audio_tags:
        return VideoAnalysisDimensionScore(
            dimension="audio",
            score=1.0,
            matched=[],
            missed=[],
            rationale="No audio cues were required for this clip.",
        )
    tag_overlap = len(set(prediction.audio_tags) & set(target.audio_tags)) / len(target.audio_tags)
    note_text = " ".join(prediction.audio_notes).lower()
    note_targets = [target.audio_description] if target.audio_description else []
    matched_notes = [note for note in note_targets if _note_matches(note, note_text)]
    note_score = 0.3 if note_targets and matched_notes else (0.3 if not note_targets else 0.0)
    score = min(tag_overlap * 0.7 + note_score, 1.0)
    missed = [tag for tag in target.audio_tags if tag not in set(prediction.audio_tags)]
    if note_targets and not matched_notes:
        missed.append("audio_description")
    return VideoAnalysisDimensionScore(
        dimension="audio",
        score=score,
        matched=sorted(set(prediction.audio_tags) & set(target.audio_tags)),
        missed=missed,
        rationale=(
            "Audio cues matched the target."
            if not missed
            else f"Audio mismatches: {', '.join(missed)}"
        ),
    )


def _score_evidence(
    prediction: VideoAnalysisPrediction,
    target: VideoAnalysisTarget,
) -> VideoAnalysisDimensionScore:
    if not prediction.evidence:
        return VideoAnalysisDimensionScore(
            dimension="evidence",
            score=0.0,
            matched=[],
            missed=["at least 2 grounded evidence items"],
            rationale="No evidence snippets were provided.",
        )
    valid = [
        item
        for item in prediction.evidence
        if item.cue and item.timestamp_seconds <= target.duration_seconds + 0.25
    ]
    score = min(len(valid) / 2.0, 1.0)
    missed = [] if score >= 1.0 else ["at least 2 grounded evidence items"]
    return VideoAnalysisDimensionScore(
        dimension="evidence",
        score=score,
        matched=[f"{item.timestamp_seconds:.1f}s" for item in valid],
        missed=missed,
        rationale=(
            "Evidence snippets were grounded and timestamped."
            if not missed
            else "Evidence coverage was too thin or out of range."
        ),
    )


def _score_hard_constraints(
    prediction: VideoAnalysisPrediction,
    target: VideoAnalysisTarget,
) -> VideoAnalysisDimensionScore:
    missed = []
    if prediction.clip_id != target.clip_id:
        missed.append("clip_id")
    if not target.has_audio and any(tag != "silent" for tag in prediction.audio_tags):
        missed.append("silent_audio_contract")
    if any(item.timestamp_seconds > target.duration_seconds + 0.25 for item in prediction.evidence):
        missed.append("evidence_timestamp_range")
    score = 0.0 if missed else 1.0
    return VideoAnalysisDimensionScore(
        dimension="hard_constraints",
        score=score,
        matched=[] if missed else ["clip packet contract"],
        missed=missed,
        rationale=(
            "Hard constraints satisfied."
            if not missed
            else f"Hard failures: {', '.join(missed)}"
        ),
    )


def _note_matches(expected_note: str | None, note_text: str) -> bool:
    if not expected_note:
        return False
    expected = expected_note.lower()
    if expected in note_text:
        return True
    keywords = [token for token in re.split(r"[^a-z0-9]+", expected) if len(token) > 3]
    if not keywords:
        return False
    overlap = sum(1 for token in keywords if token in note_text)
    return overlap >= max(1, len(keywords) // 2)
