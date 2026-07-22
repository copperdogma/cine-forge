"""Deterministic scorer for source-grounded QA-pass judgments."""

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


STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "was",
    "with",
}

VALID_SEVERITIES = {"error", "warning", "note"}
TOP_LEVEL_FIELDS = {"passed", "confidence", "issues", "summary"}
ISSUE_FIELDS = {"severity", "description", "location"}


class DuplicateKeyError(ValueError):
    """Raised when model JSON repeats a key that would otherwise be hidden."""


def _strict_object(pairs: list[tuple[str, object]]) -> dict:
    result: dict = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(key)
        result[key] = value
    return result

# Words that describe the evaluation machinery rather than the underlying defect.
# Excluding them prevents phrases such as "extraction error" from satisfying an
# otherwise unrelated source-truth requirement.
GENERIC_REASON_WORDS = {
    "actual",
    "candidate",
    "data",
    "error",
    "extract",
    "extraction",
    "fact",
    "factual",
    "field",
    "issue",
    "quality",
    "required",
    "scene",
    "screenplay",
    "source",
}

TOKEN_ALIASES = {
    "3": "3",
    "absent": "unsupported",
    "casualness": "casual",
    "cast": "character",
    "characters": "character",
    "complained": "complain",
    "complaining": "complain",
    "complains": "complain",
    "contradicted": "contradict",
    "contradiction": "contradict",
    "contradictions": "contradict",
    "discussed": "discuss",
    "discusses": "discuss",
    "discussion": "discuss",
    "fabricated": "invent",
    "fabricates": "invent",
    "fabrication": "invent",
    "fabrications": "invent",
    "failed": "fail",
    "fails": "fail",
    "failure": "fail",
    "groceries": "grocery",
    "gunmen": "thug",
    "high": "overconfident",
    "inaccuracies": "inaccurate",
    "incorrect": "wrong",
    "incorrectly": "wrong",
    "invented": "invent",
    "inventing": "invent",
    "invents": "invent",
    "left": "omit",
    "leaves": "omit",
    "missing": "omit",
    "misstated": "misstate",
    "misstates": "misstate",
    "mood": "tone",
    "no": "unsupported",
    "none": "unsupported",
    "not": "unsupported",
    "omission": "omit",
    "omissions": "omit",
    "omits": "omit",
    "omitted": "omit",
    "omitting": "omit",
    "overconfidence": "overconfident",
    "plans": "plan",
    "rejected": "reject",
    "rejects": "reject",
    "speaking": "speak",
    "three": "3",
    "unfaithful": "inaccurate",
    "unjustified": "overconfident",
    "unjustifiably": "overconfident",
    "unsupported": "unsupported",
    "violence": "violent",
    "warnings": "warning",
}

FIELD_ALIASES = {
    "beats": "narrative_beats",
    "cast": "characters_present",
    "characters": "characters_present",
    "character_list": "characters_present",
    "mood": "tone_mood",
    "narrative_beat": "narrative_beats",
    "time": "time_of_day",
    "tone": "tone_mood",
}

SUMMARY_JUDGMENT_CONCEPTS = {
    "contradict",
    "fail",
    "inaccurate",
    "invent",
    "omit",
    "reject",
    "unsupported",
    "wrong",
}
SUMMARY_DENIAL_RE = re.compile(
    r"(?:\b(?:does|do|did)\s+not\s+"
    r"(?:contain|include|capture|mention|establish|show|state|report|cover)\b|"
    r"\b(?:is|are|was|were)\s+not\s+(?:source[- ]grounded|complete|present)\b|"
    r"\bnever\s+(?:contains?|includes?|captures?|mentions?|establishes?|shows?|states?)\b)",
    flags=re.IGNORECASE,
)


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
        parsed = json.loads(output.strip(), object_pairs_hook=_strict_object)
        return (parsed if isinstance(parsed, dict) else None), 1.0
    except (json.JSONDecodeError, DuplicateKeyError):
        match = re.search(r"```(?:json)?\s*([\s\S]*?)```", output)
        if not match:
            return None, 0.0
        try:
            parsed = json.loads(match.group(1), object_pairs_hook=_strict_object)
        except (json.JSONDecodeError, DuplicateKeyError):
            return None, 0.0
        return (parsed if isinstance(parsed, dict) else None), 0.9


def _tokens(value: object) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", str(value or "").lower())
        if len(token) > 2 and token not in STOP_WORDS
    }


def _canonical_token(token: str) -> str:
    token = TOKEN_ALIASES.get(token, token)
    if token in TOKEN_ALIASES.values():
        return token
    if len(token) > 4 and token.endswith("ies"):
        token = f"{token[:-3]}y"
    elif len(token) > 4 and token.endswith("s") and not token.endswith("ss"):
        token = token[:-1]
    return TOKEN_ALIASES.get(token, token)


def _reason_concepts(value: object) -> set[str]:
    concepts: set[str] = set()
    for raw in re.findall(r"[a-z0-9]+(?:\.[0-9]+)?", str(value or "").lower()):
        canonical = _canonical_token(raw)
        if canonical in STOP_WORDS or canonical in GENERIC_REASON_WORDS:
            continue
        if len(canonical) <= 2 and not canonical.isdigit():
            continue
        concepts.add(canonical)
    return concepts


def _normalize_field(value: object) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")
    return FIELD_ALIASES.get(normalized, normalized)


def _issues(result: dict) -> tuple[list[dict], bool]:
    raw = result.get("issues", [])
    if not isinstance(raw, list) or any(not isinstance(issue, dict) for issue in raw):
        return [], False
    shape_valid = all(
        set(issue) == ISSUE_FIELDS
        and issue.get("severity") in VALID_SEVERITIES
        and bool(_normalize_field(issue.get("location", "")))
        and isinstance(issue.get("description"), str)
        and bool(issue.get("description", "").strip())
        for issue in raw
    )
    return raw, shape_valid


def _required_issue_matches(requirement: dict, issue: dict) -> bool:
    expected_field = _normalize_field(requirement.get("field", ""))
    actual_field = _normalize_field(issue.get("location", ""))
    field_matches = not expected_field or expected_field == actual_field
    expected_reason = _reason_concepts(requirement.get("reason", ""))
    actual_reason = _reason_concepts(issue.get("description", ""))
    shared = expected_reason & actual_reason
    minimum_shared = min(2, len(expected_reason))
    reason_matches = not expected_reason or len(shared) >= minimum_shared
    return field_matches and reason_matches


def _required_issue_statuses(
    requirements: list[dict], issues: list[dict]
) -> list[tuple[bool, bool, bool]]:
    """Return (reason matched, actionable severity, error severity) per requirement."""
    statuses = []
    for requirement in requirements:
        matches = [issue for issue in issues if _required_issue_matches(requirement, issue)]
        statuses.append(
            (
                bool(matches),
                any(issue.get("severity") in {"error", "warning"} for issue in matches),
                any(issue.get("severity") == "error" for issue in matches),
            )
        )
    return statuses


def _summary_recall(summary: str, requirements: list[str]) -> float:
    if not requirements:
        return 1.0
    segments = [
        segment.strip()
        for segment in re.split(r"[.!?;]+|\bbut\b", summary, flags=re.IGNORECASE)
        if segment.strip()
    ]
    matched = 0
    for requirement in requirements:
        expected = _tokens(requirement)
        if expected and any(
            len(expected & _tokens(segment)) / len(expected) >= 0.5
            and not SUMMARY_DENIAL_RE.search(segment)
            for segment in segments
        ):
            matched += 1
    return matched / len(requirements)


def _bad_summary_quality(summary: object, requirements: list[dict]) -> float:
    if not isinstance(summary, str) or not summary.strip():
        return 0.0
    concepts = _reason_concepts(summary)
    expected = (
        set().union(
            *(_reason_concepts(requirement.get("reason", "")) for requirement in requirements)
        )
        if requirements
        else set()
    )
    substantive = len(concepts) >= 3
    has_judgment = bool(concepts & SUMMARY_JUDGMENT_CONCEPTS)
    grounded = not expected or bool(concepts & expected)
    if substantive and has_judgment and grounded:
        return 1.0
    return 0.5


def _good_case_scores(
    result: dict,
    golden: dict,
    issues: list[dict],
) -> tuple[float, float, bool, list[str]]:
    errors = sum(issue.get("severity") == "error" for issue in issues)
    warnings = sum(issue.get("severity") == "warning" for issue in issues)
    max_errors = golden.get("max_errors", 0)
    max_warnings = golden.get("max_warnings", 0)
    error_score = max(0.0, 1.0 - max(0, errors - max_errors) * 0.5)
    warning_score = max(0.0, 1.0 - max(0, warnings - max_warnings) * 0.25)
    summary_score = _summary_recall(
        str(result.get("summary", "")),
        golden.get("required_in_summary", []),
    )
    issue_detection = (error_score + warning_score + summary_score) / 3
    severity = (
        sum(issue.get("severity") in {"note", "warning"} for issue in issues) / len(issues)
        if issues
        else 1.0
    )
    hard_gate = errors <= max_errors and warnings <= max_warnings and summary_score == 1.0
    reasons = []
    if errors > max_errors or warnings > max_warnings:
        reasons.append(
            f"Expected at most {max_errors} errors/{max_warnings} warnings; got {errors}/{warnings}"
        )
    if summary_score < 1.0:
        reasons.append("Summary misses required source-grounded conclusions")
    return issue_detection, severity, hard_gate, reasons


def _bad_case_scores(
    result: dict,
    golden: dict,
    issues: list[dict],
) -> tuple[float, float, float, bool, list[str]]:
    min_errors = golden.get("min_errors", 1)
    requirements = golden.get("required_issues", [])
    statuses = _required_issue_statuses(requirements, issues)
    denominator = max(1, len(requirements))
    reason_recall = sum(matched for matched, _, _ in statuses) / denominator
    actionable_recall = sum(actionable for _, actionable, _ in statuses) / denominator
    matched_error_count = sum(error for _, _, error in statuses)
    error_quota = min(1.0, matched_error_count / max(1, min_errors))
    issue_detection = 0.6 * reason_recall + 0.4 * error_quota
    severity = 0.5 * actionable_recall + 0.5 * error_quota
    summary_quality = _bad_summary_quality(result.get("summary"), requirements)
    hard_gate = (
        reason_recall == 1.0
        and actionable_recall == 1.0
        and matched_error_count >= min_errors
        and summary_quality == 1.0
    )
    reasons = []
    if reason_recall < 1.0:
        reasons.append("Required issue fields/reason concepts were not all detected")
    if actionable_recall < 1.0:
        reasons.append("Every required issue must be a warning or error, not a note")
    if matched_error_count < min_errors:
        reasons.append(
            f"Only {matched_error_count} required issues have error severity; need {min_errors}"
        )
    if summary_quality < 1.0:
        reasons.append("Summary must substantively reject the extraction using a grounded defect")
    return issue_detection, severity, summary_quality, hard_gate, reasons


def get_assert(output: str, context: dict) -> dict:
    golden_path = _resolve_golden_path(context)
    test_key = context.get("vars", {}).get("test_key", "")
    if not golden_path or not os.path.exists(golden_path):
        return {"pass": False, "score": 0.0, "reason": f"Golden file not found: {golden_path}"}
    with open(golden_path) as handle:
        all_golden = json.load(handle)
    golden = all_golden.get(test_key)
    if not isinstance(golden, dict):
        return {"pass": False, "score": 0.0, "reason": f"Test key {test_key!r} not in golden"}
    result, json_score = _parse_output(output)
    if result is None:
        return {"pass": False, "score": 0.0, "reason": "Invalid JSON object"}
    root_shape_valid = set(result) == TOP_LEVEL_FIELDS
    issues, issue_shape_valid = _issues(result)
    expected_passed = golden.get("expected_passed")
    pass_correct = isinstance(result.get("passed"), bool) and result["passed"] == expected_passed
    if expected_passed:
        issue_detection, severity, case_gate, reasons = _good_case_scores(result, golden, issues)
        summary_value = result.get("summary")
        summary_quality = (
            1.0
            if isinstance(summary_value, str)
            and bool(summary_value.strip())
            and _summary_recall(summary_value, golden.get("required_in_summary", [])) == 1.0
            else 0.0
        )
    else:
        issue_detection, severity, summary_quality, case_gate, reasons = _bad_case_scores(
            result, golden, issues
        )
    confidence = result.get("confidence")
    confidence_valid = (
        isinstance(confidence, (int, float))
        and not isinstance(confidence, bool)
        and math.isfinite(confidence)
        and 0.0 <= confidence <= 1.0
    )
    confidence_score = 1.0 if confidence_valid else 0.0
    scores = {
        "json_valid": json_score,
        "pass_correct": 1.0 if pass_correct else 0.0,
        "issue_detection": issue_detection,
        "severity_accuracy": severity,
        "confidence_calibration": confidence_score,
        "summary_quality": summary_quality,
    }
    weights = {
        "json_valid": 0.10,
        "pass_correct": 0.30,
        "issue_detection": 0.25,
        "severity_accuracy": 0.15,
        "confidence_calibration": 0.10,
        "summary_quality": 0.10,
    }
    total = sum(scores[key] * weight for key, weight in weights.items())
    if not pass_correct:
        reasons.append(f"passed={result.get('passed')!r}, expected={expected_passed!r}")
    if not issue_shape_valid:
        reasons.append(
            "issues must contain exactly severity, description, and location with valid values"
        )
    if not root_shape_valid:
        reasons.append("result must contain exactly passed, confidence, issues, and summary")
    if not confidence_valid:
        reasons.append("confidence must be a finite number from 0.0 through 1.0")
    if summary_quality < 1.0 and not any(reason.startswith("Summary") for reason in reasons):
        reasons.append("summary must be a substantive, source-grounded string")
    details = " | ".join(f"{key}={value:.2f}" for key, value in sorted(scores.items()))
    if reasons:
        details += " | " + "; ".join(reasons)
    hard_gates = (
        root_shape_valid
        and pass_correct
        and issue_shape_valid
        and confidence_valid
        and case_gate
    )
    return finalize_score(
        total,
        pass_threshold=PASS_THRESHOLD,
        hard_gates=hard_gates,
        reason=details,
    )
