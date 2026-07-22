"""Deterministic project-config detection scorer for promptfoo."""

from __future__ import annotations

import json
import math
import os
import re
import sys
from pathlib import Path

SCORER_ROOT = Path(__file__).resolve().parent
if str(SCORER_ROOT) not in sys.path:
    sys.path.insert(0, str(SCORER_ROOT))

from score_semantics import finalize_score  # noqa: E402

PASS_THRESHOLD = 0.60


NEGATIONS = {"no", "not", "never", "without"}
GENERIC_RATIONALES = {
    "based on source",
    "screenplay evidence",
    "source evidence",
    "source support",
    "supported by source",
}
SOURCE_BOUND_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "by",
    "for",
    "from",
    "in",
    "into",
    "is",
    "of",
    "on",
    "the",
    "to",
    "with",
}


def _resolve_golden_path(context: dict) -> str:
    golden_path = context.get("vars", {}).get("golden_path", "")
    if golden_path and not os.path.isabs(golden_path):
        golden_path = os.path.join(os.path.dirname(__file__), "..", golden_path)
    return golden_path


def _parse_output(output: str) -> tuple[dict | None, float]:
    text = output.strip()
    fenced = text.startswith("```")
    if fenced:
        text = re.sub(r"^```(?:json|javascript)?\s*", "", text)
        text = re.sub(r"\s*```\s*$", "", text)
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None, 0.0
    return (parsed if isinstance(parsed, dict) else None), 0.9 if fenced else 1.0


def _tokens(value: object) -> list[str]:
    return [_canonical_token(token) for token in re.findall(r"[a-z0-9]+", str(value or "").lower())]


def _canonical_token(token: str) -> str:
    if (
        len(token) > 3
        and token.endswith("s")
        and token not in {"series"}
        and not token.endswith(("ss", "us", "is"))
    ):
        return token[:-1]
    return token


def _contains_phrase(value: object, phrase: object) -> bool:
    haystack = _tokens(value)
    needle = _tokens(phrase)
    if not needle:
        return False
    for index in range(len(haystack) - len(needle) + 1):
        if haystack[index : index + len(needle)] != needle:
            continue
        if NEGATIONS & set(haystack[max(0, index - 3) : index]):
            continue
        return True
    return False


def _field_value(parsed: dict, field_name: str) -> tuple[object, object]:
    raw = parsed.get(field_name)
    if isinstance(raw, dict) and "value" in raw:
        return raw["value"], raw.get("confidence")
    return raw, None


def _value_text(value: object) -> str:
    if isinstance(value, list):
        return " ".join(str(item) for item in value)
    return str(value or "")


def _normalized_value(value: object) -> str:
    return " ".join(_tokens(value))


def _rationale_contains_anchor(
    rationale: str,
    anchor: str,
    field_name: str,
) -> bool:
    """Match an anchor only when the local clause does not negate its field claim."""
    haystack = _tokens(rationale)
    needle = _tokens(anchor)
    field_tokens = set(_tokens(field_name.replace("_", " ")))
    for index in range(len(haystack) - len(needle) + 1):
        if haystack[index : index + len(needle)] != needle:
            continue
        before = haystack[max(0, index - 3) : index]
        after = haystack[index + len(needle) : index + len(needle) + 6]
        if NEGATIONS & set(before):
            continue
        copula_negated = (
            len(after) >= 2
            and after[0] in {"is", "are", "was", "were"}
            and after[1] in NEGATIONS
        )
        field_negated = bool(NEGATIONS & set(after) and field_tokens & set(after))
        if copula_negated or field_negated:
            continue
        return True
    return False


def _precision_quality(
    parsed: dict,
    fields: dict,
    source_text: str,
) -> tuple[float, list[str]]:
    """Reject unsupported categorical padding declared by the source-first golden."""
    checked = 0
    passed = 0
    errors: list[str] = []
    for field_name, config in fields.items():
        value, _ = _field_value(parsed, field_name)
        field_valid = True
        allowed = config.get("allowed_values", [])
        forbidden = config.get("forbidden_keywords", [])
        require_null = config.get("require_null") is True
        source_bounded = config.get("source_bounded_value") is True
        has_contract = bool(allowed or forbidden or require_null or source_bounded)
        if has_contract:
            checked += 1
        if allowed:
            allowed_normalized = {_normalized_value(item) for item in allowed}
            values = value if isinstance(value, list) else [value]
            unsupported = [
                str(item)
                for item in values
                if _normalized_value(item) not in allowed_normalized
            ]
            if unsupported:
                field_valid = False
                errors.append(
                    f"{field_name}: unsupported values: {', '.join(unsupported)}"
                )
        if forbidden:
            matches = [
                phrase
                for phrase in forbidden
                if _contains_phrase(_value_text(value), phrase)
            ]
            if matches:
                field_valid = False
                errors.append(
                    f"{field_name}: forbidden unsupported claims: {', '.join(matches)}"
                )
        if require_null and value is not None:
            field_valid = False
            errors.append(f"{field_name}: value must be null for this source")
        if source_bounded:
            if not source_text:
                field_valid = False
                errors.append(
                    f"{field_name}: source text unavailable for value grounding"
                )
            else:
                allowed_novel = set(
                    _tokens(" ".join(config.get("allowed_novel_tokens", [])))
                )
                source_tokens = set(_tokens(source_text))
                declared_source_tokens = set(
                    _tokens(" ".join(config.get("allowed_source_tokens", [])))
                )
                absent_declared_tokens = declared_source_tokens - source_tokens
                if absent_declared_tokens:
                    field_valid = False
                    errors.append(
                        f"{field_name}: golden source allowances absent from source: "
                        f"{', '.join(sorted(absent_declared_tokens))}"
                    )
                source_allowance = declared_source_tokens or source_tokens
                unsupported_tokens = sorted(
                    set(_tokens(value))
                    - source_allowance
                    - allowed_novel
                    - SOURCE_BOUND_STOPWORDS
                )
                if unsupported_tokens:
                    field_valid = False
                    errors.append(
                        f"{field_name}: unsupported source-bounded terms: "
                        f"{', '.join(unsupported_tokens)}"
                    )
        if has_contract and field_valid:
            passed += 1
    return (passed / checked if checked else 1.0), errors


def _rationale_quality(
    parsed: dict,
    fields: dict,
    source_text: str,
) -> tuple[float, list[str]]:
    """Require each rationale to bind to a field-specific source anchor."""
    passed = 0
    errors: list[str] = []
    for field_name, config in fields.items():
        raw = parsed.get(field_name)
        rationale = raw.get("rationale", "") if isinstance(raw, dict) else ""
        normalized = _normalized_value(rationale)
        anchors = config.get("rationale_must_mention_any", [])
        field_errors: list[str] = []
        if normalized in GENERIC_RATIONALES:
            field_errors.append("generic rationale")
        if anchors:
            if not source_text:
                field_errors.append("source text unavailable for rationale verification")
            else:
                source_anchors = [
                    anchor for anchor in anchors if _contains_phrase(source_text, anchor)
                ]
                if not source_anchors:
                    field_errors.append("golden rationale anchors absent from source")
                elif not any(
                    _rationale_contains_anchor(rationale, anchor, field_name)
                    for anchor in source_anchors
                ):
                    field_errors.append("rationale lacks concrete source evidence")
        if field_errors:
            errors.append(f"{field_name}: {', '.join(field_errors)}")
        else:
            passed += 1
    return (passed / len(fields) if fields else 1.0), errors


def _keyword_group_score(value: object, keywords: list[str], minimum: int) -> float:
    if not keywords:
        return 1.0
    matches = sum(_contains_phrase(_value_text(value), keyword) for keyword in keywords)
    if matches >= minimum:
        return 1.0
    return 0.5 * matches / max(1, minimum)


def _categorical_group_score(value: object, config: dict) -> float:
    """Credit distinct accepted qualities without double-counting synonyms."""
    accepted = {
        _normalized_value(item)
        for item in [
            *config.get("expected_keywords", []),
            *config.get("allowed_values", []),
        ]
        if _normalized_value(item)
    }
    group_by_value: dict[str, str] = {}
    for index, group in enumerate(config.get("equivalent_value_groups", [])):
        for item in group:
            group_by_value[_normalized_value(item)] = f"group:{index}"
    values = value if isinstance(value, list) else [value]
    matched_groups = {
        group_by_value.get(normalized, f"value:{normalized}")
        for item in values
        if (normalized := _normalized_value(item)) in accepted
    }
    minimum = int(config.get("must_include_at_least", 1))
    if len(matched_groups) >= minimum:
        return 1.0
    return 0.5 * len(matched_groups) / max(1, minimum)


def _numeric_value(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    match = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*(?:minutes?|mins?)?\s*", str(value or ""), re.I)
    return float(match.group(1)) if match else None


def _range_score(value: object, expected: list[float]) -> float:
    number = _numeric_value(value)
    if number is None or len(expected) != 2:
        return 0.0
    if expected[0] <= number <= expected[1]:
        return 1.0
    midpoint = (expected[0] + expected[1]) / 2
    return max(0.0, 1.0 - abs(number - midpoint) / max(1.0, midpoint))


def _title_and_format_scores(parsed: dict, fields: dict, reasons: list[str]) -> dict[str, float]:
    title, _ = _field_value(parsed, "title")
    expected_title = fields.get("title", {}).get("expected_value", "")
    title_score = 1.0 if _contains_phrase(title, expected_title) else 0.0
    if not title_score:
        reasons.append(f"Title mismatch: got {title!r}")
    format_value, _ = _field_value(parsed, "format")
    expected_formats = fields.get("format", {}).get("expected_values", [])
    format_score = 1.0 if any(
        _contains_phrase(format_value, expected) for expected in expected_formats
    ) else 0.0
    if not format_score:
        reasons.append(f"Format mismatch: got {format_value!r}")
    return {"title_accuracy": title_score, "format_accuracy": format_score}


def _genre_and_tone_scores(parsed: dict, fields: dict) -> dict[str, float]:
    scores = {}
    for field_name in ("genre", "tone"):
        value, _ = _field_value(parsed, field_name)
        config = fields.get(field_name, {})
        scores[f"{field_name}_accuracy"] = _categorical_group_score(value, config)
    return scores


def _character_score(parsed: dict, fields: dict) -> float:
    primary, _ = _field_value(parsed, "primary_characters")
    supporting, _ = _field_value(parsed, "supporting_characters")
    required = fields.get("primary_characters", {}).get("must_include", [])
    alternatives = fields.get("supporting_characters", {}).get("should_include_any", [])
    minimum = fields.get("supporting_characters", {}).get("min_count", 1)
    primary_found = sum(_contains_phrase(_value_text(primary), name) for name in required)
    supporting_found = sum(
        _contains_phrase(_value_text(supporting), name) for name in alternatives
    )
    primary_score = primary_found / max(1, len(required))
    supporting_score = min(1.0, supporting_found / max(1, minimum))
    return 0.6 * primary_score + 0.4 * supporting_score


def _location_score(parsed: dict, fields: dict) -> float:
    count, _ = _field_value(parsed, "location_count")
    summary, _ = _field_value(parsed, "locations_summary")
    count_score = _range_score(
        count,
        fields.get("location_count", {}).get("expected_range", [0, 999]),
    )
    required = fields.get("locations_summary", {}).get("must_mention", [])
    summary_found = sum(_contains_phrase(summary, phrase) for phrase in required)
    summary_score = summary_found / max(1, len(required))
    return 0.4 * count_score + 0.6 * summary_score


def _audience_score(parsed: dict, fields: dict) -> float:
    value, _ = _field_value(parsed, "target_audience")
    config = fields.get("target_audience", {})
    if config.get("require_null") is True:
        return 1.0 if value is None else 0.0
    if value is None or str(value).strip().lower() in {"", "null", "none"}:
        return 0.5 if config.get("allow_null", False) else 0.0
    keywords = config.get("expected_keywords", [])
    return 1.0 if not keywords or any(_contains_phrase(value, item) for item in keywords) else 0.0


def _confidence_score(parsed: dict, fields: dict) -> float:
    values = []
    for field_name, config in fields.items():
        _, confidence = _field_value(parsed, field_name)
        minimum = config.get("min_confidence", 0.0)
        if (
            isinstance(confidence, (int, float))
            and not isinstance(confidence, bool)
            and 0.0 <= confidence <= 1.0
        ):
            values.append(min(1.0, confidence / max(minimum, 0.01)))
        else:
            values.append(0.0)
    return sum(values) / len(values) if values else 0.0


def _schema_errors(parsed: dict, fields: dict) -> list[str]:
    errors: list[str] = []
    expected_names = set(fields)
    extra_names = sorted(set(parsed) - expected_names)
    if extra_names:
        errors.append(f"Unexpected fields: {', '.join(extra_names)}")

    list_fields = {"genre", "tone", "primary_characters", "supporting_characters"}
    integer_fields = {"estimated_duration_minutes", "location_count"}
    string_fields = {"title", "format", "locations_summary"}
    for name in fields:
        raw = parsed.get(name)
        if not isinstance(raw, dict) or set(raw) != {"value", "confidence", "rationale"}:
            errors.append(f"{name}: expected exactly value/confidence/rationale")
            continue
        confidence = raw["confidence"]
        if (
            not isinstance(confidence, (int, float))
            or isinstance(confidence, bool)
            or not math.isfinite(float(confidence))
            or not 0.0 <= float(confidence) <= 1.0
        ):
            errors.append(f"{name}: confidence must be a finite number from 0 to 1")
        elif float(confidence) < float(fields[name].get("min_confidence", 0.0)):
            errors.append(
                f"{name}: confidence {float(confidence):.2f} is below minimum "
                f"{float(fields[name].get('min_confidence', 0.0)):.2f}"
            )
        rationale = raw["rationale"]
        if not isinstance(rationale, str) or len(_tokens(rationale)) < 2:
            errors.append(f"{name}: rationale must be substantive")
        value = raw["value"]
        if name in list_fields and (
            not isinstance(value, list)
            or not value
            or any(not isinstance(item, str) or not item.strip() for item in value)
        ):
            errors.append(f"{name}: value must be a non-empty string array")
        elif name in integer_fields and (
            not isinstance(value, int) or isinstance(value, bool)
        ):
            errors.append(f"{name}: value must be an integer")
        elif name in string_fields and (not isinstance(value, str) or not value.strip()):
            errors.append(f"{name}: value must be a non-empty string")
        elif name == "target_audience" and value is not None and (
            not isinstance(value, str) or not value.strip()
        ):
            errors.append("target_audience: value must be a string or null")
    return errors


def _critical_gate(fields: dict, field_scores: dict[str, float]) -> bool:
    score_keys = {
        "title": "title_accuracy",
        "format": "format_accuracy",
        "genre": "genre_accuracy",
        "tone": "tone_accuracy",
        "estimated_duration_minutes": "duration_accuracy",
        "primary_characters": "character_accuracy",
        "supporting_characters": "character_accuracy",
        "location_count": "location_accuracy",
        "locations_summary": "location_accuracy",
        "target_audience": "audience_accuracy",
    }
    thresholds = {"critical": 0.8, "important": 0.5}
    return all(
        field_scores.get(score_keys[name], 0.0)
        >= thresholds.get(str(fields[name].get("importance", "")).lower(), 0.0)
        for name in fields
    )


def get_assert(output: str, context: dict) -> dict:
    golden_path = _resolve_golden_path(context)
    try:
        with open(golden_path) as handle:
            golden = json.load(handle)
    except Exception as exc:
        return {"pass": False, "score": 0.0, "reason": f"Cannot load golden reference: {exc}"}
    parsed, json_score = _parse_output(output)
    if parsed is None:
        return {"pass": False, "score": 0.0, "reason": "Invalid JSON object"}
    fields = golden.get("fields", {})
    reasons: list[str] = []
    scores = {"json_valid": json_score}
    scores.update(_title_and_format_scores(parsed, fields, reasons))
    scores.update(_genre_and_tone_scores(parsed, fields))
    duration, _ = _field_value(parsed, "estimated_duration_minutes")
    scores["duration_accuracy"] = _range_score(
        duration,
        fields.get("estimated_duration_minutes", {}).get("expected_range", [0, 999]),
    )
    scores["character_accuracy"] = _character_score(parsed, fields)
    scores["location_accuracy"] = _location_score(parsed, fields)
    scores["audience_accuracy"] = _audience_score(parsed, fields)
    scores["confidence_quality"] = _confidence_score(parsed, fields)
    source_text = str(
        context.get("vars", {}).get("screenplay")
        or context.get("vars", {}).get("source_text")
        or ""
    )
    precision_quality, precision_errors = _precision_quality(
        parsed,
        fields,
        source_text,
    )
    rationale_quality, rationale_errors = _rationale_quality(
        parsed,
        fields,
        source_text,
    )
    scores["precision_quality"] = precision_quality
    scores["rationale_grounding"] = rationale_quality
    weights = {
        "json_valid": 0.08,
        "title_accuracy": 0.12,
        "format_accuracy": 0.10,
        "genre_accuracy": 0.13,
        "tone_accuracy": 0.10,
        "duration_accuracy": 0.10,
        "character_accuracy": 0.13,
        "location_accuracy": 0.09,
        "audience_accuracy": 0.10,
        "confidence_quality": 0.05,
    }
    base_total = sum(scores[key] * weight for key, weight in weights.items())
    total = base_total * (
        0.90 + 0.05 * precision_quality + 0.05 * rationale_quality
    )
    missing_fields = [name for name in fields if name not in parsed or parsed[name] is None]
    if missing_fields:
        reasons.append(f"Missing fields: {', '.join(missing_fields)}")
    details = ", ".join(f"{key}={value:.2f}" for key, value in sorted(scores.items()))
    if reasons:
        details += " | " + "; ".join(reasons)
    schema_errors = _schema_errors(parsed, fields)
    contract_errors = schema_errors + precision_errors + rationale_errors
    if contract_errors:
        reasons.extend(contract_errors)
        details = ", ".join(f"{key}={value:.2f}" for key, value in sorted(scores.items()))
        details += " | " + "; ".join(reasons)
    hard_gates = (
        not missing_fields
        and not contract_errors
        and _critical_gate(fields, scores)
    )
    return finalize_score(
        total,
        pass_threshold=PASS_THRESHOLD,
        hard_gates=hard_gates,
        reason=details,
    )
