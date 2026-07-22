"""Deterministic source-grounded scorer for scene enrichment."""

from __future__ import annotations

import json
import math
import os
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

SCORER_ROOT = Path(__file__).resolve().parent
if str(SCORER_ROOT) not in sys.path:
    sys.path.insert(0, str(SCORER_ROOT))

from score_semantics import finalize_score  # noqa: E402

PASS_THRESHOLD = 0.80


STOP_WORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "by",
    "for",
    "from",
    "in",
    "is",
    "of",
    "on",
    "the",
    "to",
    "with",
}
TOP_LEVEL_FIELDS = {
    "heading",
    "location",
    "time_of_day",
    "int_ext",
    "characters_present",
    "narrative_beats",
    "tone_mood",
    "tone_shifts",
}
BEAT_FIELDS = {"beat_type", "description", "confidence"}


def _resolve_golden_path(context: dict) -> str:
    golden_path = context.get("vars", {}).get("golden_path", "")
    if golden_path and not os.path.isabs(golden_path):
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for candidate in (os.path.join(base, golden_path), os.path.join(os.getcwd(), golden_path)):
            if os.path.exists(candidate):
                return candidate
    return golden_path


def _parse_output(output: str) -> tuple[dict | None, float]:
    try:
        parsed = json.loads(output.strip())
        return (parsed if isinstance(parsed, dict) else None), 1.0
    except json.JSONDecodeError:
        match = re.search(r"```(?:json)?\s*([\s\S]*?)```", output)
        if not match:
            return None, 0.0
        try:
            parsed = json.loads(match.group(1))
        except json.JSONDecodeError:
            return None, 0.0
        return (parsed if isinstance(parsed, dict) else None), 0.9


def _normalize(value: object) -> str:
    return " ".join(re.findall(r"[A-Z0-9]+", str(value or "").upper()))


def _heading_score(result: dict, golden: dict) -> float:
    expected = _normalize(golden.get("heading"))
    actual = _normalize(result.get("heading"))
    return 1.0 if expected and actual == expected else 0.0


def _location_score(result: dict, golden: dict) -> float:
    expected_location = _normalize(golden.get("location"))
    actual_location = _normalize(result.get("location"))
    location_similarity = (
        SequenceMatcher(None, actual_location, expected_location).ratio()
        if actual_location and expected_location
        else 0.0
    )
    int_ext = 1.0 if _normalize(result.get("int_ext")) == _normalize(golden.get("int_ext")) else 0.0
    return 0.6 * location_similarity + 0.4 * int_ext


def _time_score(result: dict, golden: dict) -> float:
    expected = _normalize(golden.get("time_of_day"))
    actual = _normalize(result.get("time_of_day"))
    unspecified = {"UNSPECIFIED", "UNKNOWN", "NOT SPECIFIED"}
    if expected in unspecified:
        return 1.0 if actual in unspecified else 0.0
    return 1.0 if expected and actual == expected else 0.0


def _character_name(value: object) -> str:
    normalized = _normalize(value)
    return normalized[4:] if normalized.startswith("THE ") else normalized


def _character_score(result: dict, golden: dict) -> tuple[float, float]:
    expected = {_character_name(value) for value in golden.get("characters_present", [])}
    actual_values = result.get("characters_present", [])
    actual = (
        {_character_name(value) for value in actual_values if _character_name(value)}
        if isinstance(actual_values, list)
        else set()
    )
    if not expected:
        return (1.0 if not actual else 0.0), 1.0
    overlap = len(expected & actual)
    recall = overlap / len(expected)
    precision = overlap / len(actual) if actual else 0.0
    f1 = 2 * recall * precision / (recall + precision) if recall + precision else 0.0
    return f1, recall


def _schema_errors(result: dict) -> list[str]:
    errors = [f"missing:{field}" for field in sorted(TOP_LEVEL_FIELDS - set(result))]
    errors.extend(f"extra:{field}" for field in sorted(set(result) - TOP_LEVEL_FIELDS))
    for field in ("heading", "location", "time_of_day", "int_ext", "tone_mood"):
        if not isinstance(result.get(field), str) or not result.get(field, "").strip():
            errors.append(f"{field}:not-nonempty-string")
    if result.get("int_ext") not in {"INT", "EXT", "INT/EXT"}:
        errors.append("int_ext:not-supported")

    characters = result.get("characters_present")
    if not isinstance(characters, list) or any(
        not isinstance(value, str) or not _character_name(value) for value in characters
    ):
        errors.append("characters_present:not-nonempty-string-array")
    elif len({_character_name(value) for value in characters}) != len(characters):
        errors.append("characters_present:duplicate")

    beats = result.get("narrative_beats")
    if not isinstance(beats, list) or not beats:
        errors.append("narrative_beats:not-nonempty-array")
    else:
        for index, beat in enumerate(beats):
            if not isinstance(beat, dict) or set(beat) != BEAT_FIELDS:
                errors.append(f"narrative_beats[{index}]:wrong-fields")
                continue
            if not isinstance(beat.get("beat_type"), str) or not beat["beat_type"].strip():
                errors.append(f"narrative_beats[{index}].beat_type:not-nonempty-string")
            if not isinstance(beat.get("description"), str) or not beat["description"].strip():
                errors.append(f"narrative_beats[{index}].description:not-nonempty-string")
            confidence = beat.get("confidence")
            if (
                not isinstance(confidence, (int, float))
                or isinstance(confidence, bool)
                or not math.isfinite(confidence)
                or not 0.0 <= confidence <= 1.0
            ):
                errors.append(f"narrative_beats[{index}].confidence:not-finite-0-to-1")

    tone_shifts = result.get("tone_shifts")
    if not isinstance(tone_shifts, list) or any(
        not isinstance(value, str) or not value.strip() for value in tone_shifts
    ):
        errors.append("tone_shifts:not-string-array")
    return errors


def _tokens(value: object) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", str(value or "").lower())
        if len(token) > 2 and token not in STOP_WORDS
    }


def _detail_match(description: str, expected: str) -> bool:
    expected_tokens = _tokens(expected)
    if not expected_tokens:
        return False
    return len(expected_tokens & _tokens(description)) / len(expected_tokens) >= 0.5


def _beat_metrics(
    result: dict,
    golden: dict,
    scene_text: str,
) -> tuple[float, float, float, float]:
    beats = result.get("narrative_beats", [])
    if not isinstance(beats, list) or any(not isinstance(beat, dict) for beat in beats):
        return 0.0, 0.0, 0.0, 0.0
    expected_types = {str(value).lower() for value in golden.get("expected_beat_types", [])}
    actual_types = {str(beat.get("beat_type", "")).lower() for beat in beats}
    type_recall = (
        len(expected_types & actual_types) / len(expected_types)
        if expected_types
        else 1.0
    )
    descriptions = " ".join(str(beat.get("description", "")) for beat in beats)
    details = golden.get("key_details", [])
    detail_recall = (
        sum(_detail_match(descriptions, detail) for detail in details) / len(details)
        if details
        else 1.0
    )
    description_tokens = _tokens(descriptions)
    support_tokens = _tokens(scene_text)
    for detail in details:
        support_tokens.update(_tokens(detail))
    semantic_grounding = (
        len(description_tokens & support_tokens) / len(description_tokens)
        if description_tokens
        else 0.0
    )
    substantive = (
        1.0
        if beats and all(len(str(beat.get("description", ""))) >= 10 for beat in beats)
        else 0.0
    )
    score = (
        0.3 * type_recall
        + 0.4 * detail_recall
        + 0.2 * semantic_grounding
        + 0.1 * substantive
    )
    return score, type_recall, detail_recall, semantic_grounding


def _tone_score(result: dict, golden: dict) -> float:
    actual = _normalize(
        f"{result.get('tone_mood', '')} {' '.join(map(str, result.get('tone_shifts', [])))}"
    )
    expected = golden.get("expected_tone", [])
    return 1.0 if not expected or any(_normalize(value) in actual for value in expected) else 0.0


def _field_score(result: dict) -> float:
    required = (
        "heading",
        "location",
        "time_of_day",
        "int_ext",
        "characters_present",
        "narrative_beats",
        "tone_mood",
        "tone_shifts",
    )
    present = sum(
        field in result and result[field] is not None and result[field] != ""
        for field in required
    )
    return present / len(required)


def get_assert(output: str, context: dict) -> dict:
    golden_path = _resolve_golden_path(context)
    scene_key = context.get("vars", {}).get("scene_key", "")
    if not golden_path or not os.path.exists(golden_path):
        return {"pass": False, "score": 0.0, "reason": f"Golden file not found: {golden_path}"}
    with open(golden_path) as handle:
        all_golden = json.load(handle)
    golden = all_golden.get(scene_key)
    if not isinstance(golden, dict):
        return {"pass": False, "score": 0.0, "reason": f"Scene key {scene_key!r} not in golden"}
    result, json_score = _parse_output(output)
    if result is None:
        return {"pass": False, "score": 0.0, "reason": "Invalid JSON object"}
    schema_errors = _schema_errors(result)
    character_score, character_recall = _character_score(result, golden)
    expected_characters = {
        _character_name(value) for value in golden.get("characters_present", [])
    }
    actual_characters = {
        _character_name(value)
        for value in result.get("characters_present", [])
        if isinstance(value, str) and _character_name(value)
    }
    character_exact = actual_characters == expected_characters
    beat_quality, beat_type_recall, beat_detail_recall, beat_grounding = _beat_metrics(
        result,
        golden,
        str(context.get("vars", {}).get("scene_text", "")),
    )
    scores = {
        "json_valid": json_score,
        "heading_accuracy": _heading_score(result, golden),
        "location_accuracy": _location_score(result, golden),
        "time_accuracy": _time_score(result, golden),
        "character_accuracy": character_score,
        "beat_quality": beat_quality,
        "tone_accuracy": _tone_score(result, golden),
        "field_completeness": _field_score(result),
    }
    weights = {
        "json_valid": 0.10,
        "heading_accuracy": 0.10,
        "location_accuracy": 0.15,
        "time_accuracy": 0.10,
        "character_accuracy": 0.20,
        "beat_quality": 0.20,
        "tone_accuracy": 0.10,
        "field_completeness": 0.05,
    }
    total = sum(scores[key] * weight for key, weight in weights.items())
    details = " | ".join(f"{key}={value:.2f}" for key, value in sorted(scores.items()))
    if schema_errors:
        details += " | schema_errors=" + ",".join(schema_errors)
    details += (
        f" | beat_type_recall={beat_type_recall:.2f}"
        f" | beat_detail_grounding={beat_detail_recall:.2f}"
        f" | beat_source_grounding={beat_grounding:.2f}"
    )
    hard_gates = (
        not schema_errors
        and scores["heading_accuracy"] == 1.0
        and scores["location_accuracy"] == 1.0
        and scores["time_accuracy"] == 1.0
        and character_recall == 1.0
        and character_exact
        and beat_type_recall == 1.0
        and beat_detail_recall >= 0.5
        and beat_grounding >= 0.5
        and scores["tone_accuracy"] == 1.0
    )
    return finalize_score(
        total,
        pass_threshold=PASS_THRESHOLD,
        hard_gates=hard_gates,
        reason=details,
    )
