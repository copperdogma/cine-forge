"""Strict deterministic scorer for the location- and prop-bible evals."""

from __future__ import annotations

import json
import math
import os
import re
import sys
from pathlib import Path
from typing import Any

SCORER_ROOT = Path(__file__).resolve().parent
if str(SCORER_ROOT) not in sys.path:
    sys.path.insert(0, str(SCORER_ROOT))

from score_semantics import finalize_score  # noqa: E402

LOCATION_FIELDS = {
    "location_id",
    "name",
    "aliases",
    "description",
    "physical_traits",
    "scene_presence",
    "narrative_significance",
    "overall_confidence",
}
PROP_FIELDS = {
    "prop_id",
    "name",
    "description",
    "scene_presence",
    "associated_characters",
    "narrative_significance",
    "overall_confidence",
}
STOP_WORDS = set("a an and are as at be by for from has in is it of on the to was with".split())
IRREGULAR_TOKENS = {
    "bottles": "bottle",
    "burning": "burn",
    "burns": "burn",
    "carries": "carry",
    "carried": "carry",
    "children": "child",
    "dad": "father",
    "dads": "father",
    "fights": "fight",
    "fought": "fight",
    "shown": "show",
    "shows": "show",
    "stole": "steal",
    "stolen": "steal",
    "taught": "teach",
    "teaches": "teach",
    "wielded": "wield",
}
NEGATORS = set(
    "cannot didnt doesnt isnt lacks lacking neither never no nor not wasnt without".split()
)
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
CHARACTER_SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")
PASS_THRESHOLD = 0.95


class DuplicateKeyError(ValueError):
    """Raised when a JSON object repeats a key."""


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(key)
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite number: {value}")


def _parse_output(output: str) -> tuple[dict[str, Any] | None, str | None]:
    try:
        parsed = json.loads(
            output,
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except DuplicateKeyError:
        return None, "duplicate-key"
    except (json.JSONDecodeError, ValueError, TypeError):
        return None, "invalid-json"
    if not isinstance(parsed, dict):
        return None, "top-level-not-object"
    return parsed, None


def _resolve_golden_path(context: dict[str, Any]) -> str:
    path = context.get("vars", {}).get("golden_path", "")
    if path and not os.path.isabs(path):
        benchmark_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for candidate in (os.path.join(benchmark_root, path), os.path.join(os.getcwd(), path)):
            if os.path.exists(candidate):
                return candidate
    return path


def _canonical_token(token: str) -> str:
    token = token.lower()
    if token in IRREGULAR_TOKENS:
        return IRREGULAR_TOKENS[token]
    if token.endswith("ies") and len(token) > 4:
        return f"{token[:-3]}y"
    if token.endswith("ing") and len(token) > 5:
        return token[:-3]
    if token.endswith("ed") and len(token) > 4:
        return token[:-2]
    if token.endswith("es") and len(token) > 4:
        return token[:-2]
    if token.endswith("s") and len(token) > 3:
        return token[:-1]
    return token


def _tokens(value: object) -> list[str]:
    text = str(value or "").lower()
    text = re.sub(r"\b(?:isn|wasn|doesn|didn|can)\s*['’]?t\b", " not ", text)
    return [
        _canonical_token(token)
        for token in re.findall(r"[a-z0-9]+", text)
        if token not in STOP_WORDS
    ]


def _clauses(value: object) -> list[str]:
    values = value if isinstance(value, list) else [value]
    clauses: list[str] = []
    for item in values:
        if not isinstance(item, str):
            continue
        safe = re.sub(r"\bnot\s+(?:just|merely|only)\b", "", item, flags=re.IGNORECASE)
        clauses.extend(part.strip() for part in re.split(r"[.!?;\n]+", safe) if part.strip())
    return clauses


def _coverage(actual_tokens: list[str], expected_tokens: list[str]) -> float:
    expected = set(expected_tokens)
    if not expected:
        return 0.0
    return len(expected & set(actual_tokens)) / len(expected)


def _required_coverage(expected_tokens: list[str]) -> float:
    count = len(set(expected_tokens))
    if count <= 2:
        return 1.0
    if count == 3:
        return 2 / 3
    return 0.7


def _negates_expected(actual_tokens: list[str], expected_tokens: list[str]) -> bool:
    expected = set(expected_tokens)
    matches = [index for index, token in enumerate(actual_tokens) if token in expected]
    negations = [index for index, token in enumerate(actual_tokens) if token in NEGATORS]
    return any(0 <= match - negation <= 5 for match in matches for negation in negations)


def _concept_result(actual: object, concept: str) -> tuple[bool, bool]:
    expected_tokens = _tokens(concept)
    threshold = _required_coverage(expected_tokens)
    expected_is_negative = bool(set(expected_tokens) & NEGATORS)
    matched = False
    contradicted = False
    for clause in _clauses(actual):
        actual_tokens = _tokens(clause)
        coverage = _coverage(actual_tokens, expected_tokens)
        if (
            not expected_is_negative
            and coverage >= max(0.5, threshold - 0.2)
            and _negates_expected(actual_tokens, expected_tokens)
        ):
            contradicted = True
        elif coverage >= threshold:
            matched = True
    return matched, contradicted


def _concept_metrics(actual: object, concepts: object) -> tuple[float, list[str], list[str]]:
    if not isinstance(concepts, list) or any(not isinstance(item, str) for item in concepts):
        return 0.0, ["invalid-golden-concepts"], []
    if not concepts:
        return 1.0, [], []
    missing: list[str] = []
    contradictions: list[str] = []
    for concept in concepts:
        matched, contradicted = _concept_result(actual, concept)
        if not matched:
            missing.append(concept)
        if contradicted:
            contradictions.append(concept)
    return (len(concepts) - len(missing)) / len(concepts), missing, contradictions


def _array_errors(result: dict[str, Any], field: str, *, allow_empty: bool) -> list[str]:
    value = result.get(field)
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        return [f"{field}:not-string-array"]
    if any(not item.strip() for item in value):
        return [f"{field}:empty-item"]
    if not allow_empty and not value:
        return [f"{field}:empty"]
    if len(value) != len(set(value)):
        return [f"{field}:duplicate-item"]
    return []


def _schema_errors(result: dict[str, Any], kind: str) -> list[str]:
    expected_fields = LOCATION_FIELDS if kind == "location" else PROP_FIELDS
    errors = [f"missing:{field}" for field in sorted(expected_fields - set(result))]
    errors.extend(f"extra:{field}" for field in sorted(set(result) - expected_fields))
    identifier = f"{kind}_id"
    for field in (identifier, "name", "description", "narrative_significance"):
        if not isinstance(result.get(field), str) or not result.get(field, "").strip():
            errors.append(f"{field}:not-nonempty-string")
    if isinstance(result.get(identifier), str) and not SLUG_PATTERN.fullmatch(result[identifier]):
        errors.append(f"{identifier}:not-url-slug")
    errors.extend(_array_errors(result, "scene_presence", allow_empty=False))
    if kind == "location":
        errors.extend(_array_errors(result, "aliases", allow_empty=True))
        errors.extend(_array_errors(result, "physical_traits", allow_empty=False))
    else:
        errors.extend(_array_errors(result, "associated_characters", allow_empty=True))
        associated = result.get("associated_characters")
        if isinstance(associated, list) and any(
            isinstance(item, str) and not CHARACTER_SLUG_PATTERN.fullmatch(item)
            for item in associated
        ):
            errors.append("associated_characters:not-character-slug")
    confidence = result.get("overall_confidence")
    if (
        not isinstance(confidence, (int, float))
        or isinstance(confidence, bool)
        or not math.isfinite(confidence)
        or not 0.0 <= confidence <= 1.0
    ):
        errors.append("overall_confidence:not-finite-0-to-1")
    return errors


def _exact_set_metrics(actual: object, expected: object) -> tuple[float, bool]:
    if not isinstance(actual, list) or not isinstance(expected, list):
        return 0.0, False
    if any(not isinstance(value, str) for value in actual + expected):
        return 0.0, False
    actual_set, expected_set = set(actual), set(expected)
    union = actual_set | expected_set
    score = len(actual_set & expected_set) / len(union) if union else 1.0
    return score, actual_set == expected_set and len(actual) == len(actual_set)


def _failure(reason: str) -> dict[str, Any]:
    return {"pass": False, "score": 0.0, "reason": reason}


def _semantic_metrics(
    result: dict[str, Any], golden: dict[str, Any], kind: str
) -> tuple[float, list[str], list[str], float, list[str], list[str], float, list[str], list[str]]:
    physical_value = (
        result.get("physical_traits") if kind == "location" else result.get("description")
    )
    physical = _concept_metrics(physical_value, golden.get("physical_traits"))
    fact_value = [result.get("description", ""), result.get("narrative_significance", "")]
    facts = _concept_metrics(fact_value, golden.get("key_facts"))
    narrative = _concept_metrics(
        result.get("narrative_significance"),
        golden.get("narrative_significance_must_mention"),
    )
    return (*physical, *facts, *narrative)


def _diagnostics(
    schema_errors: list[str],
    identity_valid: bool,
    linked_set_valid: bool,
    linked_set_label: str,
    scenes_valid: bool,
    missing_groups: tuple[tuple[str, list[str]], ...],
) -> list[str]:
    values = ["schema_errors=" + ",".join(schema_errors)] if schema_errors else []
    if not identity_valid:
        values.append("identity_mismatch")
    if not linked_set_valid:
        values.append(f"{linked_set_label}_set_mismatch")
    if not scenes_valid:
        values.append("scene_set_mismatch")
    values.extend(f"{label}={len(items)}" for label, items in missing_groups if items)
    return values


def get_assert(output: str, context: dict[str, Any]) -> dict[str, Any]:
    """Score one strict, source-proxy bible object against a verified golden entry."""
    variables = context.get("vars", {})
    location_name = variables.get("location_name")
    prop_name = variables.get("prop_name")
    if bool(location_name) == bool(prop_name):
        return _failure("contract:exactly-one-entity-target-required")
    kind = "location" if location_name else "prop"
    entity_name = location_name or prop_name
    golden_path = _resolve_golden_path(context)
    if not golden_path or not os.path.exists(golden_path):
        return _failure(f"golden:not-found:{golden_path}")
    with open(golden_path, encoding="utf-8") as handle:
        all_golden = json.load(handle)
    golden = all_golden.get(entity_name) if isinstance(all_golden, dict) else None
    if not isinstance(golden, dict):
        return _failure(f"golden:no-exact-entity:{entity_name}")

    result, parse_error = _parse_output(output)
    if result is None:
        return _failure(f"json:{parse_error}")
    schema_errors = _schema_errors(result, kind)
    identifier = f"{kind}_id"
    identity_valid = (
        result.get(identifier) == golden.get(identifier)
        and result.get("name") == golden.get("name")
    )
    scene_score, scenes_valid = _exact_set_metrics(
        result.get("scene_presence"), golden.get("must_mention_scenes")
    )
    linked_set_label = "aliases" if kind == "location" else "associated_characters"
    linked_set_score, linked_set_valid = (1.0, True)
    if kind == "location":
        linked_set_score, linked_set_valid = _exact_set_metrics(
            result.get("aliases"), golden.get("aliases")
        )
    else:
        linked_set_score, linked_set_valid = _exact_set_metrics(
            result.get("associated_characters"), golden.get("associated_characters")
        )

    (
        physical_score,
        physical_missing,
        physical_contradictions,
        fact_score,
        fact_missing,
        fact_contradictions,
        narrative_score,
        narrative_missing,
        narrative_contradictions,
    ) = _semantic_metrics(result, golden, kind)
    contradictions = (
        physical_contradictions + fact_contradictions + narrative_contradictions
    )
    scores = {
        "json": 1.0,
        "schema": float(not schema_errors),
        "identity": float(identity_valid),
        linked_set_label: linked_set_score,
        "scenes": scene_score,
        "physical": physical_score,
        "facts": fact_score,
        "narrative": narrative_score,
    }
    weights = {
        "json": 0.05,
        "schema": 0.15,
        "identity": 0.10,
        linked_set_label: 0.05,
        "scenes": 0.15,
        "physical": 0.20,
        "facts": 0.15,
        "narrative": 0.15,
    }
    total = sum(scores[key] * weights[key] for key in scores)
    hard_gates = all(
        (
            not schema_errors,
            identity_valid,
            linked_set_valid,
            scenes_valid,
            not physical_missing,
            not fact_missing,
            not narrative_missing,
            not contradictions,
        )
    )
    diagnostics = _diagnostics(
        schema_errors,
        identity_valid,
        linked_set_valid,
        linked_set_label,
        scenes_valid,
        (
            ("physical_missing", physical_missing),
            ("fact_missing", fact_missing),
            ("narrative_missing", narrative_missing),
            ("contradictions", contradictions),
        ),
    )
    detail = " ".join(f"{key}={value:.2f}" for key, value in scores.items())
    if diagnostics:
        detail += " | " + " | ".join(diagnostics)
    return finalize_score(
        total,
        pass_threshold=PASS_THRESHOLD,
        hard_gates=hard_gates,
        reason=detail,
    )
