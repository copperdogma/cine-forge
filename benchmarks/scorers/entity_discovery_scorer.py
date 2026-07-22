"""
Entity discovery scorer for promptfoo.

Evaluates model output on precision/recall of character, location, and prop
discovery. Entity discovery is a RECALL task — finding everything matters more
than precision. A missed entity is worse than a false positive.

Scoring:
- Character recall (required): weight 0.45 — must find key characters
- Location recall (required): weight 0.25 — must find key locations
- Prop recall (required): weight 0.15 — must find at least one prop
- JSON validity: weight 0.10
- No hallucination penalty: weight 0.05 (minor, since over-discovery is ok)

Promptfoo calls get_assert(output, context).
"""

import json
import os
import re
import sys
from pathlib import Path

SCORER_ROOT = Path(__file__).resolve().parent
if str(SCORER_ROOT) not in sys.path:
    sys.path.insert(0, str(SCORER_ROOT))

from score_semantics import finalize_score  # noqa: E402

PASS_THRESHOLD = 0.70


EXPECTED_ROOT_FIELDS = {"characters", "locations", "props"}


def normalize_name(s: str) -> str:
    """Normalize entity name for matching."""
    s = s.upper().strip()
    s = re.sub(r"[^A-Z0-9\s&]", "", s)
    s = re.sub(r"\s+", " ", s)
    return s


def name_matches(found: str, target: str, aliases: list[str]) -> bool:
    """Check if a found name matches a target or any of its aliases."""
    found_n = normalize_name(found)
    target_n = normalize_name(target)
    if not found_n or not target_n:
        return False
    if found_n == target_n:
        return True
    for alias in aliases:
        alias_n = normalize_name(alias)
        if not alias_n:
            continue
        if found_n == alias_n:
            return True
    return False


def compute_recall(
    found_entities: list[str],
    required: list[str],
    aliases_map: dict[str, list[str]],
) -> tuple[float, list[str]]:
    """Compute recall of required entities against found list."""
    if not required:
        return 1.0, []
    found_count = 0
    missing = []
    for req in required:
        req_aliases = aliases_map.get(req, [])
        matched = any(name_matches(f, req, req_aliases) for f in found_entities)
        if matched:
            found_count += 1
        else:
            missing.append(req)
    return found_count / len(required), missing


def _resolve_golden_path(context: dict) -> str:
    golden_path = context.get("vars", {}).get("golden_path", "")
    if golden_path and not os.path.isabs(golden_path):
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidate = os.path.join(base, golden_path)
        if os.path.exists(candidate):
            golden_path = candidate
    return golden_path


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


def _entity_names(result: dict, key: str) -> list[str]:
    values = result.get(key, [])
    if not isinstance(values, list):
        return []
    return [value for value in values if isinstance(value, str) and normalize_name(value)]


def _schema_errors(result: dict) -> list[str]:
    """Return exact-contract errors instead of silently filtering bad values."""
    errors = [f"missing:{key}" for key in sorted(EXPECTED_ROOT_FIELDS - set(result))]
    errors.extend(f"extra:{key}" for key in sorted(set(result) - EXPECTED_ROOT_FIELDS))
    for key in sorted(EXPECTED_ROOT_FIELDS):
        values = result.get(key)
        if not isinstance(values, list):
            errors.append(f"{key}:not-array")
            continue
        if any(not isinstance(value, str) or not normalize_name(value) for value in values):
            errors.append(f"{key}:not-nonempty-string-array")
            continue
        normalized = [normalize_name(value) for value in values]
        if len(normalized) != len(set(normalized)):
            errors.append(f"{key}:duplicate")
    return errors


def _score_category(
    result: dict,
    golden: dict,
    key: str,
) -> tuple[float, list[str], list[str]]:
    config = golden.get(key, {})
    found = _entity_names(result, key)
    recall, missing = compute_recall(
        found,
        config.get("required", []),
        config.get("acceptable_aliases", {}),
    )
    return recall, missing, found


def _optional_coverage(golden: dict, found_by_key: dict[str, list[str]]) -> float:
    optional: list[tuple[str, str]] = []
    for key in ("characters", "locations", "props"):
        optional.extend((key, name) for name in golden.get(key, {}).get("optional", []))
    if not optional:
        return 1.0
    found_count = sum(
        1
        for key, target in optional
        if any(name_matches(found, target, []) for found in found_by_key[key])
    )
    return min(1.0, found_count / max(1, len(optional) * 0.4))


def _precision_guard(
    golden: dict,
    found_by_key: dict[str, list[str]],
) -> tuple[float, int, int]:
    recognized = 0
    total = 0
    for key, found_names in found_by_key.items():
        config = golden.get(key, {})
        targets = config.get("required", []) + config.get("optional", [])
        aliases = config.get("acceptable_aliases", {})
        for found in found_names:
            total += 1
            if any(name_matches(found, target, aliases.get(target, [])) for target in targets):
                recognized += 1
    precision = recognized / total if total else 0.0
    return precision, total - recognized, recognized


def _excluded_matches(golden: dict, found_by_key: dict[str, list[str]]) -> list[str]:
    matches: list[str] = []
    for key, found_names in found_by_key.items():
        excluded = golden.get(key, {}).get("excluded", [])
        for found in found_names:
            found_normalized = normalize_name(found)
            if any(
                found_normalized == normalize_name(target)
                or found_normalized in normalize_name(target)
                or normalize_name(target) in found_normalized
                for target in excluded
            ):
                matches.append(f"{key}:{found}")
    return matches


def get_assert(output: str, context: dict) -> dict:
    golden_path = _resolve_golden_path(context)

    if not golden_path or not os.path.exists(golden_path):
        return {"pass": False, "score": 0, "reason": f"Golden not found: {golden_path}"}

    with open(golden_path) as f:
        golden = json.load(f)

    result, json_score = _parse_output(output)
    if result is None:
        return {"pass": False, "score": 0.0, "reason": "Invalid JSON object"}

    schema_errors = _schema_errors(result)
    scores = {"json_valid": json_score}
    reasons: list[str] = []
    found_by_key: dict[str, list[str]] = {}
    for key, score_key in (
        ("characters", "character_recall"),
        ("locations", "location_recall"),
        ("props", "prop_recall"),
    ):
        recall, missing, found = _score_category(result, golden, key)
        scores[score_key] = recall
        found_by_key[key] = found
        if missing:
            reasons.append(f"Missing {key}: {', '.join(missing)}")

    scores["optional_coverage"] = _optional_coverage(golden, found_by_key)
    precision, unknown_count, recognized_count = _precision_guard(golden, found_by_key)
    scores["precision"] = precision
    required_complete = all(
        scores[key] == 1.0
        for key in ("character_recall", "location_recall", "prop_recall")
    )
    excluded = _excluded_matches(golden, found_by_key)
    if unknown_count:
        reasons.append(f"Unrecognized entities: {unknown_count}")
    if excluded:
        reasons.append(f"Explicitly excluded entities: {', '.join(excluded)}")
    if schema_errors:
        reasons.append(f"Schema errors: {', '.join(schema_errors)}")

    # Weighted total — recall is the primary metric
    weights = {
        "json_valid": 0.10,
        "character_recall": 0.45,
        "location_recall": 0.25,
        "prop_recall": 0.15,
        "optional_coverage": 0.025,
        "precision": 0.025,
    }

    total = sum(scores.get(k, 0) * w for k, w in weights.items())

    reason_parts = [f"{k}={v:.2f}" for k, v in sorted(scores.items())]
    if reasons:
        reason_parts.append(" | ".join(reasons))

    hard_gates = (
        not schema_errors
        and required_complete
        and unknown_count == 0
        and not excluded
    )
    return finalize_score(
        total,
        pass_threshold=PASS_THRESHOLD,
        hard_gates=hard_gates,
        reason=" | ".join(reason_parts),
    )
