"""Strict prediction contract for ordered-frame-packet evaluation."""

from __future__ import annotations

import re
from typing import Any

TAG_FIELDS = (
    "tone_tags",
    "emotion_tags",
    "color_tags",
    "camera_tags",
    "motion_tags",
    "audio_tags",
)

EXPECTED_FIELDS = frozenset(
    {
        "clip_id",
        "summary",
        *TAG_FIELDS,
        "continuity_status",
        "continuity_notes",
        "audio_notes",
        "evidence",
        "overall_confidence",
    }
)

ALLOWED_TAGS: dict[str, set[str]] = {
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


def normalize_prediction_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate exact keys and tag vocabulary without dropping bad values."""
    if not isinstance(payload, dict):
        raise ValueError("Prediction must be one JSON object")
    keys = set(payload)
    missing = sorted(EXPECTED_FIELDS - keys)
    extra = sorted(keys - EXPECTED_FIELDS)
    if missing or extra:
        details = []
        if missing:
            details.append(f"missing keys: {', '.join(missing)}")
        if extra:
            details.append(f"unexpected keys: {', '.join(extra)}")
        raise ValueError("Prediction keys are invalid (" + "; ".join(details) + ")")

    normalized = dict(payload)
    for field_name in TAG_FIELDS:
        normalized[field_name] = normalize_tag_list(
            normalized[field_name],
            field_name=field_name,
        )
    for field_name in ("continuity_notes", "audio_notes"):
        value = normalized[field_name]
        if not isinstance(value, list) or any(
            not isinstance(item, str) or not item.strip() for item in value
        ):
            raise ValueError(f"{field_name} must be a list of non-empty strings")
    if not isinstance(normalized["evidence"], list):
        raise ValueError("evidence must be a list")
    return normalized


def normalize_tag_list(value: Any, *, field_name: str) -> list[str]:
    """Accept only exact allowed values and reject duplicates."""
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    normalized: list[str] = []
    allowed = ALLOWED_TAGS[field_name]
    for item in value:
        if not isinstance(item, str):
            raise ValueError(f"{field_name} entries must be strings")
        candidate = item.strip()
        if candidate not in allowed:
            raise ValueError(f"Unknown {field_name} value: {item!r}")
        if candidate in normalized:
            raise ValueError(f"Duplicate {field_name} value: {candidate}")
        normalized.append(candidate)
    return normalized


def extract_json_object(text: str) -> str | None:
    """Extract the first balanced JSON object from prose."""
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    in_string = False
    escaped = False
    for idx, char in enumerate(text[start:], start=start):
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : idx + 1]
    return None


def duplicate_tag_fields(prediction: Any) -> list[str]:
    """Defend direct scorer callers that bypass the strict JSON parser."""
    return [
        field_name
        for field_name in TAG_FIELDS
        if len(getattr(prediction, field_name)) != len(set(getattr(prediction, field_name)))
    ]


def contains_explicit_audio_claim(text: str) -> bool:
    """Detect explicit acoustic claims outside the dedicated audio fields."""
    patterns = (
        r"\b(?:hear|hears|heard|audible|soundtrack)\b",
        r"\b(?:heartbeat|music|muzak|percussion|piano|voiceover)\b",
        r"\b(?:sound|audio|voice|speech|dialogue)\s+(?:is|can be)\s+(?:heard|audible)\b",
        r"\b(?:music|piano|percussion|muzak|siren|heartbeat|voiceover)\s+"
        r"(?:plays|sounds|rises|continues|underscores|is heard)\b",
        r"\b(?:soft|loud|distant)\s+(?:music|piano|percussion|sound|voice|siren)\b",
    )
    lowered = text.lower()
    return any(re.search(pattern, lowered) for pattern in patterns)
