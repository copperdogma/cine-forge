"""Strict, source-grounded continuity extraction scorer."""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

SCORER_ROOT = Path(__file__).resolve().parent
if str(SCORER_ROOT) not in sys.path:
    sys.path.insert(0, str(SCORER_ROOT))

from score_semantics import finalize_score  # noqa: E402

RESULT_FIELDS = {"scene_id", "entity_states"}
ENTITY_FIELDS = {"entity_key", "properties", "change_events", "confidence"}
PROPERTY_FIELDS = {"key", "value", "confidence"}
CHANGE_FIELDS = {
    "property_key",
    "previous_value",
    "new_value",
    "reason",
    "evidence",
    "is_explicit",
    "confidence",
}
VALUE_GLUE = {
    "a", "an", "and", "are", "as", "at", "by", "he",
    "her", "his", "in", "is", "it", "its", "of", "on",
    "or", "she", "the", "their", "to", "was", "were", "with",
}
REASON_GLUE = VALUE_GLUE | {
    "became",
    "becomes",
    "change",
    "changed",
    "changes",
    "current",
    "established",
    "from",
    "materially",
    "new",
    "newly",
    "now",
    "previous",
    "previously",
    "prior",
    "shift",
    "shifted",
    "state",
    "then",
}
PASS_THRESHOLD = 0.75


def _resolve_golden_path(context: dict) -> str:
    path = context.get("vars", {}).get("golden_path", "")
    if path and not os.path.isabs(path):
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for candidate in (os.path.join(base, path), os.path.join(os.getcwd(), path)):
            if os.path.exists(candidate):
                return candidate
    return path


def _parse_output(output: str) -> tuple[dict | None, float]:
    try:
        parsed = json.loads(output)
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


def _words(value: object) -> list[str]:
    return re.findall(r"[a-z0-9]+", str(value or "").lower())


def _normalize(value: object) -> str:
    return " ".join(_words(value))


def _content_words(value: object, *, reason: bool = False) -> set[str]:
    ignored = REASON_GLUE if reason else VALUE_GLUE
    return {word for word in _words(value) if word not in ignored}


def _number(value: object, low: float = 0.0, high: float = 1.0) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and low <= value <= high
    )


def _phrase_in(value: object, pattern: object) -> bool:
    normalized_value = f" {_normalize(value)} "
    normalized_pattern = _normalize(pattern)
    return bool(normalized_pattern) and f" {normalized_pattern} " in normalized_value


def _exact_any(value: object, patterns: list[str]) -> bool:
    normalized = _normalize(value)
    return bool(normalized) and any(normalized == _normalize(pattern) for pattern in patterns)


def _select_component(value: object, patterns: list[str]) -> str | None:
    matches = [pattern for pattern in patterns if _phrase_in(value, pattern)]
    return max(matches, key=lambda pattern: len(_words(pattern)), default=None)


def _property_value_valid(value: object, specs: list[dict]) -> bool:
    selected: list[str] = []
    for spec in specs:
        component = _select_component(value, spec.get("value_patterns", []))
        if component is None:
            return False
        selected.append(component)
    allowed = set().union(*(_content_words(component) for component in selected))
    return bool(allowed) and _content_words(value) <= allowed


def _evidence_in_text(evidence: object, scene_text: str) -> bool:
    evidence_words = _words(evidence)
    if len(evidence_words) < 3:
        return False
    return f" {' '.join(evidence_words)} " in f" {_normalize(scene_text)} "


def _entity_schema_valid(entity: object) -> bool:
    if not isinstance(entity, dict) or set(entity) != ENTITY_FIELDS:
        return False
    if not isinstance(entity.get("entity_key"), str) or not entity["entity_key"].strip():
        return False
    if not _number(entity.get("confidence")):
        return False
    properties = entity.get("properties")
    changes = entity.get("change_events")
    if not isinstance(properties, list) or not isinstance(changes, list):
        return False
    return _properties_schema_valid(properties) and _changes_schema_valid(changes)


def _properties_schema_valid(properties: list) -> bool:
    return all(
        isinstance(prop, dict)
        and set(prop) == PROPERTY_FIELDS
        and bool(str(prop.get("key", "")).strip())
        and bool(str(prop.get("value", "")).strip())
        and _number(prop.get("confidence"))
        for prop in properties
    )


def _changes_schema_valid(changes: list) -> bool:
    return all(
        isinstance(change, dict)
        and set(change) == CHANGE_FIELDS
        and bool(str(change.get("property_key", "")).strip())
        and _previous_value_schema_valid(change.get("previous_value"))
        and bool(str(change.get("new_value", "")).strip())
        and bool(str(change.get("reason", "")).strip())
        and bool(str(change.get("evidence", "")).strip())
        and isinstance(change.get("is_explicit"), bool)
        and _number(change.get("confidence"))
        for change in changes
    )


def _previous_value_schema_valid(value: object) -> bool:
    return value is None or (isinstance(value, str) and bool(value.strip()))


def _property_score(entity: dict, specs: list[dict]) -> tuple[float, bool]:
    required = [spec for spec in specs if spec.get("required", False)]
    grouped_specs: dict[str, list[dict]] = {}
    for spec in required:
        grouped_specs.setdefault(spec.get("key"), []).append(spec)
    keyed: dict[str, list[dict]] = {}
    for prop in entity.get("properties", []):
        keyed.setdefault(prop.get("key"), []).append(prop)
    results = [
        len(keyed.get(key, [])) == 1
        and _property_value_valid(keyed[key][0].get("value"), key_specs)
        for key, key_specs in grouped_specs.items()
    ]
    exact_keys = set(keyed) == set(grouped_specs) and all(
        len(values) == 1 for values in keyed.values()
    )
    score = sum(results) / len(results) if results else float(not keyed)
    return score, exact_keys and all(results)


def _reason_is_grounded(change: dict) -> bool:
    reason = change.get("reason")
    previous = change.get("previous_value")
    new = change.get("new_value")
    new_at = _normalize(reason).find(_normalize(new))
    if new_at < 0:
        return False
    if previous is None:
        direction_valid = bool({"new", "newly", "now", "established"} & set(_words(reason)))
    else:
        old_at = _normalize(reason).find(_normalize(previous))
        direction_valid = 0 <= old_at < new_at
    supported = _content_words(reason, reason=True) <= (
        _content_words(previous) | _content_words(new)
    )
    return direction_valid and supported


def _change_matches(change: dict, spec: dict, scene_text: str) -> bool:
    previous_patterns = spec.get("previous_patterns", [])
    previous_matches = (
        change.get("previous_value") is None
        if not previous_patterns
        else _exact_any(change.get("previous_value"), previous_patterns)
    )
    evidence = change.get("evidence")
    return all(
        (
            change.get("property_key") == spec.get("property_key"),
            previous_matches,
            _exact_any(change.get("new_value"), spec.get("new_patterns", [])),
            _evidence_in_text(evidence, scene_text),
            any(_phrase_in(evidence, pattern) for pattern in spec.get("evidence_patterns", [])),
            change.get("is_explicit") is spec.get("is_explicit"),
            _reason_is_grounded(change),
        )
    )


def _maximum_change_matches(changes: list[dict], specs: list[dict], scene_text: str) -> int:
    edges = [
        [index for index, spec in enumerate(specs) if _change_matches(change, spec, scene_text)]
        for change in changes
    ]
    assigned: dict[int, int] = {}

    def assign(change_index: int, seen: set[int]) -> bool:
        for spec_index in edges[change_index]:
            if spec_index in seen:
                continue
            seen.add(spec_index)
            previous_change = assigned.get(spec_index)
            if previous_change is None or assign(previous_change, seen):
                assigned[spec_index] = change_index
                return True
        return False

    return sum(assign(index, set()) for index in range(len(changes)))


def _change_score(entity: dict, specs: list[dict], scene_text: str) -> tuple[float, bool]:
    changes = entity.get("change_events", [])
    if not specs and not changes:
        return 1.0, True
    matched = _maximum_change_matches(changes, specs, scene_text)
    denominator = max(len(changes), len(specs), 1)
    return matched / denominator, matched == len(specs) == len(changes)


def _score_entities(
    states: list[dict],
    golden: dict,
    scene_text: str,
) -> tuple[list[float], list[float], bool, bool]:
    state_by_key = {state["entity_key"]: state for state in states}
    property_scores: list[float] = []
    change_scores: list[float] = []
    properties_valid = True
    changes_valid = True
    for entity_key in golden.get("expected_entities", []):
        state = state_by_key.get(entity_key)
        if state is None:
            property_scores.append(0.0)
            change_scores.append(0.0)
            properties_valid = changes_valid = False
            continue
        property_score, property_valid = _property_score(
            state, golden.get("expected_properties", {}).get(entity_key, [])
        )
        change_score, change_valid = _change_score(
            state, golden.get("expected_changes", {}).get(entity_key, []), scene_text
        )
        property_scores.append(property_score)
        change_scores.append(change_score)
        properties_valid &= property_valid
        changes_valid &= change_valid
    return property_scores, change_scores, properties_valid, changes_valid


def _confidence_valid(states: list[dict], confidence_range: list[float]) -> bool:
    low, high = confidence_range
    return all(
        _number(state.get("confidence"), low, high)
        and all(_number(prop.get("confidence"), low, high) for prop in state["properties"])
        and all(_number(change.get("confidence"), low, high) for change in state["change_events"])
        for state in states
    )


def _load_case(context: dict) -> tuple[dict | None, dict]:
    variables = context.get("vars", {})
    golden_path = _resolve_golden_path(context)
    scene_key = variables.get("scene_key", "")
    if not golden_path or not os.path.exists(golden_path) or not scene_key:
        return None, variables
    with open(golden_path) as handle:
        return json.load(handle).get(scene_key), variables


def get_assert(output: str, context: dict) -> dict:
    """Promptfoo assertion entry point."""
    golden, variables = _load_case(context)
    if not isinstance(golden, dict):
        return {"pass": False, "score": 0.0, "reason": "Missing golden or scene key"}
    result, json_score = _parse_output(output)
    if result is None:
        return {"pass": False, "score": 0.0, "reason": "Invalid JSON object"}
    if set(result) != RESULT_FIELDS:
        return {"pass": False, "score": 0.0, "reason": "Invalid result schema"}
    states = result.get("entity_states")
    if not isinstance(states, list) or not all(_entity_schema_valid(state) for state in states):
        return {"pass": False, "score": 0.0, "reason": "Invalid entity-state schema"}

    expected_entities = set(golden.get("expected_entities", []))
    keys = [state["entity_key"] for state in states]
    entity_valid = set(keys) == expected_entities and len(keys) == len(set(keys))
    scene_text = str(variables.get("scene_text", ""))
    property_scores, change_scores, properties_valid, changes_valid = _score_entities(
        states, golden, scene_text
    )
    evidence = [change["evidence"] for state in states for change in state["change_events"]]
    key_evidence = golden.get("key_evidence", [])
    has_expected_changes = any(golden.get("expected_changes", {}).values())
    evidence_coverage = (
        sum(any(_phrase_in(quote, key) for quote in evidence) for key in key_evidence)
        / len(key_evidence)
        if key_evidence and has_expected_changes
        else 1.0
    )
    evidence_valid = all(_evidence_in_text(quote, scene_text) for quote in evidence)
    confidence_valid = _confidence_valid(
        states, golden.get("expected_confidence_range", [0.5, 1.0])
    )
    scene_valid = result.get("scene_id") == variables.get("scene_id")
    scores = {
        "json_valid": json_score,
        "scene_identity": float(scene_valid),
        "entity_accuracy": (
            len(set(keys) & expected_entities) / len(set(keys) | expected_entities)
            if set(keys) | expected_entities
            else 1.0
        ),
        "property_accuracy": sum(property_scores) / len(property_scores),
        "change_accuracy": sum(change_scores) / len(change_scores),
        "evidence_coverage": evidence_coverage,
        "confidence_calibration": float(confidence_valid),
    }
    weights = {
        "json_valid": 0.05,
        "scene_identity": 0.05,
        "entity_accuracy": 0.15,
        "property_accuracy": 0.25,
        "change_accuracy": 0.25,
        "evidence_coverage": 0.15,
        "confidence_calibration": 0.10,
    }
    total = sum(scores[key] * weight for key, weight in weights.items())
    hard_gates = all(
        (
            scene_valid,
            entity_valid,
            properties_valid,
            changes_valid,
            evidence_coverage == 1.0,
            evidence_valid,
            confidence_valid,
        )
    )
    details = " | ".join(f"{key}={value:.2f}" for key, value in sorted(scores.items()))
    return finalize_score(
        total,
        pass_threshold=PASS_THRESHOLD,
        hard_gates=hard_gates,
        reason=details,
    )
