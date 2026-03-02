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
    if target_n in found_n or found_n in target_n:
        return True
    for alias in aliases:
        alias_n = normalize_name(alias)
        if alias_n in found_n or found_n in alias_n:
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


def get_assert(output: str, context: dict) -> dict:
    golden_path = context.get("vars", {}).get("golden_path", "")
    if golden_path and not os.path.isabs(golden_path):
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidate = os.path.join(base, golden_path)
        if os.path.exists(candidate):
            golden_path = candidate

    if not golden_path or not os.path.exists(golden_path):
        return {"pass": False, "score": 0, "reason": f"Golden not found: {golden_path}"}

    with open(golden_path) as f:
        golden = json.load(f)

    scores = {}
    reasons = []

    # 1. JSON validity
    try:
        result = json.loads(output)
        scores["json_valid"] = 1.0
    except json.JSONDecodeError:
        match = re.search(r"```(?:json)?\s*([\s\S]*?)```", output)
        if match:
            try:
                result = json.loads(match.group(1))
                scores["json_valid"] = 0.9
            except json.JSONDecodeError:
                return {"pass": False, "score": 0.0, "reason": "Invalid JSON"}
        else:
            return {"pass": False, "score": 0.0, "reason": "Invalid JSON"}

    # 2. Character recall
    char_config = golden.get("characters", {})
    found_chars = result.get("characters", [])
    if not isinstance(found_chars, list):
        found_chars = []
    char_recall, char_missing = compute_recall(
        found_chars,
        char_config.get("required", []),
        char_config.get("acceptable_aliases", {}),
    )
    scores["character_recall"] = char_recall
    if char_missing:
        reasons.append(f"Missing characters: {', '.join(char_missing)}")

    # 3. Location recall
    loc_config = golden.get("locations", {})
    found_locs = result.get("locations", [])
    if not isinstance(found_locs, list):
        found_locs = []
    loc_recall, loc_missing = compute_recall(
        found_locs,
        loc_config.get("required", []),
        loc_config.get("acceptable_aliases", {}),
    )
    scores["location_recall"] = loc_recall
    if loc_missing:
        reasons.append(f"Missing locations: {', '.join(loc_missing)}")

    # 4. Prop recall
    prop_config = golden.get("props", {})
    found_props = result.get("props", [])
    if not isinstance(found_props, list):
        found_props = []
    prop_recall, prop_missing = compute_recall(
        found_props,
        prop_config.get("required", []),
        prop_config.get("acceptable_aliases", {}),
    )
    scores["prop_recall"] = prop_recall
    if prop_missing:
        reasons.append(f"Missing props: {', '.join(prop_missing)}")

    # 5. Coverage (found at least some optional entities — shows thoroughness)
    optional_chars = char_config.get("optional", [])
    optional_locs = loc_config.get("optional", [])
    all_optional = optional_chars + optional_locs
    if all_optional:
        opt_found = sum(
            1 for opt in all_optional
            if any(normalize_name(opt) in normalize_name(f) or normalize_name(f) in normalize_name(opt)
                   for f in found_chars + found_locs)
        )
        scores["optional_coverage"] = min(1.0, opt_found / max(1, len(all_optional) * 0.4))
    else:
        scores["optional_coverage"] = 1.0

    # Weighted total — recall is the primary metric
    weights = {
        "json_valid": 0.10,
        "character_recall": 0.45,
        "location_recall": 0.25,
        "prop_recall": 0.15,
        "optional_coverage": 0.05,
    }

    total = sum(scores.get(k, 0) * w for k, w in weights.items())

    reason_parts = [f"{k}={v:.2f}" for k, v in sorted(scores.items())]
    if reasons:
        reason_parts.append(" | ".join(reasons))

    return {
        "pass": total >= 0.70,
        "score": round(total, 4),
        "reason": " | ".join(reason_parts),
    }
