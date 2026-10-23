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
    "hallucinated": "hallucinate",
    "hallucinates": "hallucinate",
    "hallucination": "hallucinate",
    "hallucinations": "hallucinate",
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
    "revelation": "reveal",
    "revelations": "reveal",
    "speaking": "speak",
    "three": "3",
    "unfaithful": "inaccurate",
    "unjustified": "overconfident",
    "unjustifiably": "overconfident",
    "unsupported": "unsupported",
    "violence": "violent",
    "warnings": "warning",
    "wrongly": "wrong",
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
FIELD_GROUPS = {
    "heading_metadata": {"heading", "location", "time_of_day"},
}
REPAIR_FAMILIES = {
    "metadata": {"heading", "location", "time_of_day", "heading_metadata"},
    "cast_identity": {"characters_present"},
    "summary_plot": {"summary"},
    "beats_events": {"narrative_beats"},
    "tone": {"tone_mood"},
    "candidate_confidence": {"confidence"},
}
POSITIVE_REVIEW_DIMENSIONS = {
    "metadata": {"heading", "location", "metadata", "setting", "time"},
    "cast_identity": {"cast", "character", "identity", "roster"},
    "summary_plot": {"plot", "story", "summary"},
    "beats_events": {"action", "beat", "event"},
    "tone": {"mood", "tone"},
    "candidate_confidence": {"confidence", "calibration"},
}

SUMMARY_JUDGMENT_CONCEPTS = {
    "contradict",
    "fail",
    "inaccurate",
    "hallucinate",
    "invent",
    "omit",
    "reject",
    "unsupported",
    "wrong",
}
MATERIAL_FAULT_CONCEPTS = SUMMARY_JUDGMENT_CONCEPTS | {
    "defect",
    "flaw",
    "incomplete",
    "misleading",
    "misstate",
}
POSITIVE_SUMMARY_CONCEPTS = {
    "accurate",
    "accurately",
    "acceptable",
    "complete",
    "comprehensive",
    "comprehensively",
    "correct",
    "faithful",
    "grounded",
    "supported",
}
CLAUSE_SPLIT_RE = re.compile(
    r"[.!?;]+|\b(?:but|however|although|though|except|yet|whereas|while)\b",
    flags=re.IGNORECASE,
)
NEGATION_RE = re.compile(
    r"\b(?:no|zero|not|never|without|neither|nor|cannot|can't|doesn't|isn't|aren't|"
    r"wasn't|weren't|didn't|won't)\b",
    flags=re.IGNORECASE,
)
CORRECTNESS_RE = re.compile(
    r"\b(?:correct|correctly|accurate|accurately|faithful|faithfully)\b",
    flags=re.IGNORECASE,
)
UNCERTAINTY_RE = re.compile(
    r"\b(?:may|might|could|perhaps|possibly|probably|potentially|apparently|"
    r"arguably|suggests?|indicates?|appears?\s+to|seems?\s+to|looks?\s+like)\b",
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


def _all_concepts(value: object) -> set[str]:
    return {_canonical_token(token) for token in _tokens(value)}


def _clauses(value: object) -> list[str]:
    normalized = re.sub(r"\b(INT|EXT)\.", r"\1", str(value or ""), flags=re.IGNORECASE)
    return [clause.strip() for clause in CLAUSE_SPLIT_RE.split(normalized) if clause.strip()]


def _affirmed_clauses(value: object) -> list[tuple[str, set[str]]]:
    """Return unambiguously affirmative clauses; negation/modality fail closed.

    This deliberately does not attempt double-negation interpretation. A benchmark
    answer can always state the defect directly, and pretending to solve general
    entailment here would recreate the scorer weakness this guard replaces.
    """
    return [
        (clause, _reason_concepts(clause))
        for clause in _clauses(value)
        if not NEGATION_RE.search(clause) and not UNCERTAINTY_RE.search(clause)
    ]


def _affirmed_claim_clauses(value: object) -> list[tuple[str, set[str]]]:
    return [
        (clause, _all_concepts(clause))
        for clause in _clauses(value)
        if not NEGATION_RE.search(clause) and not UNCERTAINTY_RE.search(clause)
    ]


def _claim_clauses(value: object) -> list[tuple[str, set[str], bool, bool]]:
    return [
        (
            clause,
            _all_concepts(clause),
            bool(NEGATION_RE.search(clause)),
            bool(UNCERTAINTY_RE.search(clause)),
        )
        for clause in _clauses(value)
    ]


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
    field_matches = (
        not expected_field
        or expected_field == actual_field
        or expected_field in FIELD_GROUPS.get(actual_field, set())
        or actual_field in FIELD_GROUPS.get(expected_field, set())
    )
    expected_reason = _reason_concepts(requirement.get("reason", ""))
    affirmative_concepts = [
        concepts
        for clause, concepts in _affirmed_clauses(issue.get("description", ""))
        if not CORRECTNESS_RE.search(clause)
    ]
    actual_reason = set().union(*affirmative_concepts) if affirmative_concepts else set()
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


def _requirement_family(requirement: dict) -> str | None:
    field = _normalize_field(requirement.get("field", ""))
    return next(
        (family for family, fields in REPAIR_FAMILIES.items() if field in fields),
        None,
    )


def _issue_family(issue: dict) -> str | None:
    field = _normalize_field(issue.get("location", ""))
    return next((family for family, fields in REPAIR_FAMILIES.items() if field in fields), None)


def _concept_alternatives(values: object) -> set[str]:
    if not isinstance(values, list):
        return set()
    return set().union(*(_all_concepts(value) for value in values)) if values else set()


def _matches_alternative(concepts: set[str], alternatives: object) -> bool:
    if not isinstance(alternatives, list):
        return False
    return any(
        bool(expected) and expected <= concepts
        for expected in (_all_concepts(value) for value in alternatives)
    )


def _matches_negated_alternative(concepts: set[str], alternatives: object) -> bool:
    if not isinstance(alternatives, list):
        return False
    return any(
        NEGATION_RE.search(str(value)) is not None
        and bool(expected)
        and expected <= concepts
        for value in alternatives
        for expected in [_all_concepts(value)]
    )


def _family_claim_matches(description: object, contract: object) -> bool:
    if not isinstance(contract, dict):
        return False
    clauses = _claim_clauses(description)
    defect_clauses = [
        concepts
        for clause, concepts, negated, uncertain in clauses
        if not negated
        and not uncertain
        if _matches_alternative(concepts, contract.get("candidate_terms"))
        and _matches_alternative(concepts, contract.get("defect_relations"))
        and not CORRECTNESS_RE.search(clause)
    ]
    correction_clauses = [
        concepts
        for _clause, concepts, negated, uncertain in clauses
        if not uncertain
        and (
            not negated
            or _matches_negated_alternative(
                concepts, contract.get("source_corrections")
            )
        )
        and _matches_alternative(concepts, contract.get("source_corrections"))
        and _matches_alternative(concepts, contract.get("source_relations"))
    ]
    defect_asserted = bool(defect_clauses)
    correction_asserted = bool(correction_clauses)
    return defect_asserted and correction_asserted


def _family_statuses(
    golden: dict, issues: list[dict]
) -> dict[str, tuple[bool, bool]]:
    """Return one non-duplicating (actionable, error) credit per repair family."""
    statuses: dict[str, tuple[bool, bool]] = {}
    claim_contracts = golden.get("family_claim_contracts", {})
    for family in REPAIR_FAMILIES:
        matches = [
            issue
            for issue in issues
            if _issue_family(issue) == family
            and _family_claim_matches(issue.get("description"), claim_contracts.get(family))
        ]
        statuses[family] = (
            any(issue.get("severity") in {"error", "warning"} for issue in matches),
            any(issue.get("severity") == "error" for issue in matches),
        )
    return statuses


def _summary_recall(summary: str, requirements: list[str]) -> float:
    if not requirements:
        return 1.0
    segments = [
        concepts
        for _clause, concepts in _affirmed_clauses(summary)
        if concepts & MATERIAL_FAULT_CONCEPTS
    ]
    matched = 0
    for requirement in requirements:
        expected = _reason_concepts(requirement)
        if expected and any(
            len(expected & concepts) / len(expected) >= 0.5
            for concepts in segments
        ):
            matched += 1
    return matched / len(requirements)


def _bad_summary_quality(summary: object, requirements: list[dict]) -> float:
    if not isinstance(summary, str) or not summary.strip():
        return 0.0
    affirmative_faults = [
        concepts
        for _clause, concepts in _affirmed_clauses(summary)
        if concepts & SUMMARY_JUDGMENT_CONCEPTS
    ]
    concepts = set().union(*affirmative_faults) if affirmative_faults else set()
    expected = (
        set().union(
            *(_reason_concepts(requirement.get("reason", "")) for requirement in requirements)
        )
        if requirements
        else set()
    )
    substantive = len(concepts) >= 3
    has_judgment = bool(affirmative_faults)
    grounded = not expected or bool(concepts & expected)
    if substantive and has_judgment and grounded:
        return 1.0
    return 0.5


def _bad_summary_has_source_anchor(summary: object, anchors: list[str]) -> bool:
    if not isinstance(summary, str) or not summary.strip():
        return False
    return any(_summary_recall(summary, [anchor]) == 1.0 for anchor in anchors)


def _good_summary_quality(summary: object) -> float:
    """Score the prompt's substantive positive judgment without fixture anchors.

    Production consumers only use ``passed`` for a successful QA result. The
    benchmark still asks for an explanatory summary, but it must not require a
    hidden recitation of source details that the runtime prompt never requests.
    """
    if not isinstance(summary, str) or not summary.strip():
        return 0.0
    concepts = _reason_concepts(summary)
    reviewed_dimensions = {
        dimension
        for dimension, alternatives in POSITIVE_REVIEW_DIMENSIONS.items()
        if concepts & alternatives
    }
    substantive = len(concepts) >= 6 and len(reviewed_dimensions) >= 3
    positive_judgment = bool(concepts & POSITIVE_SUMMARY_CONCEPTS)
    material_fault = any(
        bool(concepts & MATERIAL_FAULT_CONCEPTS)
        for _clause, concepts in _affirmed_clauses(summary)
    )
    return 1.0 if substantive and positive_judgment and not material_fault else 0.5


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
    summary_score = _good_summary_quality(result.get("summary"))
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
        reasons.append("Summary must substantively explain the positive QA judgment")
    return issue_detection, severity, hard_gate, reasons


def _bad_case_scores(
    result: dict,
    golden: dict,
    issues: list[dict],
) -> tuple[float, float, float, bool, list[str]]:
    requirements = golden.get("required_issues", [])
    if "required_families" not in golden:
        min_errors = golden.get("min_errors", 1)
        statuses = _required_issue_statuses(requirements, issues)
        denominator = max(1, len(requirements))
        matched_reason_count = sum(matched for matched, _, _ in statuses)
        actionable_count = sum(actionable for _, actionable, _ in statuses)
        matched_error_count = sum(error for _, _, error in statuses)
        reason_recall = matched_reason_count / denominator
        actionable_recall = actionable_count / denominator
        error_quota = min(1.0, matched_error_count / max(1, min_errors))
        issue_detection = 0.6 * reason_recall + 0.4 * error_quota
        severity = 0.5 * actionable_recall + 0.5 * error_quota
        summary_quality = _bad_summary_quality(result.get("summary"), requirements)
        hard_gate = matched_error_count >= min_errors and summary_quality == 1.0
        reasons = []
        if matched_reason_count < min_errors:
            reasons.append(
                f"Only {matched_reason_count} required issue fields/reason concepts were "
                f"detected; need {min_errors}"
            )
        if actionable_count < min_errors:
            reasons.append(
                f"Only {actionable_count} required issues are actionable "
                f"(warning or error, not a note); need {min_errors}"
            )
        if matched_error_count < min_errors:
            reasons.append(
                f"Only {matched_error_count} required issues have error severity; "
                f"need {min_errors}"
            )
        if summary_quality < 1.0:
            reasons.append(
                "Summary must substantively reject the extraction using a grounded defect"
            )
        return issue_detection, severity, summary_quality, hard_gate, reasons

    family_statuses = _family_statuses(golden, issues)
    required_families = set(golden.get("required_families", REPAIR_FAMILIES))
    critical_families = set(golden.get("critical_error_families", required_families))
    family_count = max(1, len(required_families))
    actionable_families = {
        family for family in required_families if family_statuses.get(family, (False, False))[0]
    }
    error_families = {
        family for family in critical_families if family_statuses.get(family, (False, False))[1]
    }
    issue_detection = len(actionable_families) / family_count
    severity = len(error_families) / max(1, len(critical_families))
    summary_quality = _bad_summary_quality(result.get("summary"), requirements)
    summary_anchored = _bad_summary_has_source_anchor(
        result.get("summary"), golden.get("required_in_summary_any", [])
    )
    hard_gate = (
        actionable_families == required_families
        and error_families == critical_families
        and summary_quality == 1.0
        and summary_anchored
    )
    reasons = []
    missing_families = sorted(required_families - actionable_families)
    if missing_families:
        reasons.append(f"Missing actionable repair families: {', '.join(missing_families)}")
    non_error_critical = sorted(critical_families - error_families)
    if non_error_critical:
        reasons.append(
            "Critical repair families must have error severity: "
            + ", ".join(non_error_critical)
        )
    if summary_quality < 1.0:
        reasons.append("Summary must substantively reject the extraction using a grounded defect")
    if not summary_anchored:
        reasons.append("Failure summary must name a specific source-grounded critical defect")
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
        summary_quality = _good_summary_quality(result.get("summary"))
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
