"""
Continuity extraction scorer for promptfoo.

Evaluates whether a model correctly extracts entity state from scene text
and detects continuity changes between scenes.

Scoring dimensions:
- json_valid:              Valid JSON output (0.10)
- entity_coverage:         All expected entities present (0.15)
- property_extraction:     Properties match golden (0.25)
- change_detection:        Change events detected correctly (0.25)
- evidence_quality:        Evidence quotes from actual scene text (0.15)
- confidence_calibration:  Confidence scores in reasonable range (0.10)

Pass threshold: 0.60
"""

import json
import os
import re


def get_assert(output: str, context: dict) -> dict:
    """Promptfoo assertion entry point."""

    golden_path = context.get("vars", {}).get("golden_path", "")
    scene_key = context.get("vars", {}).get("scene_key", "")

    # Resolve relative path from the benchmarks directory
    if golden_path and not os.path.isabs(golden_path):
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidate = os.path.join(base, golden_path)
        if os.path.exists(candidate):
            golden_path = candidate
        else:
            candidate = os.path.join(os.getcwd(), golden_path)
            if os.path.exists(candidate):
                golden_path = candidate

    if not golden_path or not os.path.exists(golden_path):
        return {"pass": False, "score": 0, "reason": f"Golden file not found: {golden_path}"}

    with open(golden_path) as f:
        all_golden = json.load(f)

    if scene_key not in all_golden:
        return {"pass": False, "score": 0, "reason": f"Scene key '{scene_key}' not in golden"}

    golden = all_golden[scene_key]
    scores = {}
    reasons = []

    # --- 1. JSON validity ---
    text = output.strip()
    try:
        result = json.loads(text)
        scores["json_valid"] = 1.0
    except json.JSONDecodeError:
        match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if match:
            try:
                result = json.loads(match.group(1))
                scores["json_valid"] = 0.9
                reasons.append("JSON extracted from code block")
            except json.JSONDecodeError:
                return {"pass": False, "score": 0.0, "reason": "Invalid JSON output"}
        else:
            return {"pass": False, "score": 0.0, "reason": "Invalid JSON output"}

    # --- 2. Entity coverage ---
    expected_entities = set(golden.get("expected_entities", []))
    entity_states = result.get("entity_states", [])
    model_entities = {es.get("entity_key", "") for es in entity_states}

    if expected_entities:
        # Fuzzy match: allow minor key format differences
        matched = 0
        for expected in expected_entities:
            if expected in model_entities:
                matched += 1
            else:
                # Try partial match (e.g. "billy" in "character:billy")
                for model_ek in model_entities:
                    if expected.split(":")[-1] in model_ek or model_ek.split(":")[-1] in expected:
                        matched += 1
                        break
        scores["entity_coverage"] = matched / len(expected_entities)
        if matched < len(expected_entities):
            missing = expected_entities - model_entities
            reasons.append(f"Missing entities: {missing}")
    else:
        scores["entity_coverage"] = 1.0

    # --- 3. Property extraction ---
    expected_props = golden.get("expected_properties", {})
    prop_scores = []

    for entity_key, props_list in expected_props.items():
        # Find this entity in model output
        entity_state = _find_entity(entity_states, entity_key)
        if not entity_state:
            # Count all required props as missed
            required_count = sum(1 for p in props_list if p.get("required", False))
            if required_count > 0:
                prop_scores.extend([0.0] * required_count)
            continue

        model_props = {p.get("key", "").lower(): p for p in entity_state.get("properties", [])}

        for prop_spec in props_list:
            prop_key = prop_spec["key"].lower()
            value_patterns = [p.lower() for p in prop_spec.get("value_patterns", [])]
            required = prop_spec.get("required", False)

            # Find matching property (fuzzy key match)
            matched_prop = _find_property(model_props, prop_key)

            if matched_prop:
                model_value = str(matched_prop.get("value", "")).lower()
                # Check if any value pattern matches
                pattern_matches = sum(
                    1 for pat in value_patterns if pat in model_value
                )
                if value_patterns:
                    prop_score = min(pattern_matches / max(len(value_patterns) * 0.5, 1), 1.0)
                else:
                    prop_score = 0.5  # Property exists but no patterns to check
                prop_scores.append(prop_score)
            elif required:
                prop_scores.append(0.0)
                reasons.append(f"Missing required prop: {entity_key}.{prop_key}")

    scores["property_extraction"] = (
        sum(prop_scores) / len(prop_scores) if prop_scores else 0.5
    )

    # --- 4. Change detection ---
    expected_changes = golden.get("expected_changes", {})
    change_scores = []

    for entity_key, changes_list in expected_changes.items():
        entity_state = _find_entity(entity_states, entity_key)
        if not entity_state:
            change_scores.extend([0.0] * len(changes_list))
            continue

        model_changes = entity_state.get("change_events", [])

        for change_spec in changes_list:
            expected_prop_key = change_spec["property_key"].lower()
            new_patterns = [p.lower() for p in change_spec.get("new_patterns", [])]
            prev_patterns = [p.lower() for p in change_spec.get("previous_patterns", [])]

            # Find matching change event
            best_score = 0.0
            for mc in model_changes:
                mc_key = str(mc.get("property_key", "")).lower()
                # Fuzzy key match
                if not _keys_match(mc_key, expected_prop_key):
                    continue

                score = 0.3  # Base score for detecting the right property changed

                # Check new_value matches
                mc_new = str(mc.get("new_value", "")).lower()
                if new_patterns:
                    new_matches = sum(1 for p in new_patterns if p in mc_new)
                    score += 0.35 * min(new_matches / max(len(new_patterns) * 0.5, 1), 1.0)

                # Check previous_value matches
                mc_prev = str(mc.get("previous_value", "") or "").lower()
                if prev_patterns:
                    prev_matches = sum(1 for p in prev_patterns if p in mc_prev)
                    score += 0.15 * min(prev_matches / max(len(prev_patterns) * 0.5, 1), 1.0)

                # Has evidence
                if mc.get("evidence"):
                    score += 0.1

                # Has reason
                if mc.get("reason"):
                    score += 0.1

                best_score = max(best_score, score)

            change_scores.append(best_score)
            if best_score < 0.3:
                reasons.append(f"Missed change: {entity_key}.{expected_prop_key}")

    scores["change_detection"] = (
        sum(change_scores) / len(change_scores) if change_scores else 0.5
    )

    # --- 5. Evidence quality ---
    key_evidence = [e.lower() for e in golden.get("key_evidence", [])]
    scene_text = context.get("vars", {}).get("scene_text", "").lower()

    # Collect all evidence quotes from model output
    all_evidence = []
    for es in entity_states:
        for ce in es.get("change_events", []):
            ev = ce.get("evidence", "")
            if ev:
                all_evidence.append(ev.lower())

    if key_evidence and all_evidence:
        # Check that evidence quotes actually appear in the scene text
        valid_evidence = sum(
            1 for ev in all_evidence
            if _evidence_in_text(ev, scene_text)
        )
        evidence_validity = valid_evidence / len(all_evidence) if all_evidence else 0

        # Check that key evidence pieces are referenced
        key_found = sum(
            1 for ke in key_evidence
            if any(ke in ev or ev in ke for ev in all_evidence)
        )
        key_coverage = key_found / len(key_evidence) if key_evidence else 0

        scores["evidence_quality"] = evidence_validity * 0.6 + key_coverage * 0.4
    elif all_evidence:
        # Has evidence but no key_evidence to compare against
        valid_evidence = sum(
            1 for ev in all_evidence
            if _evidence_in_text(ev, scene_text)
        )
        scores["evidence_quality"] = valid_evidence / len(all_evidence) if all_evidence else 0
    else:
        scores["evidence_quality"] = 0.0
        reasons.append("No evidence quotes in change events")

    # --- 6. Confidence calibration ---
    conf_range = golden.get("expected_confidence_range", [0.5, 1.0])
    entity_confidences = [
        es.get("confidence", 0) for es in entity_states
        if isinstance(es.get("confidence"), (int, float))
    ]

    if entity_confidences:
        avg_conf = sum(entity_confidences) / len(entity_confidences)
        if conf_range[0] <= avg_conf <= conf_range[1]:
            scores["confidence_calibration"] = 1.0
        elif avg_conf < conf_range[0]:
            # Under-confident: still okay, just conservative
            scores["confidence_calibration"] = 0.6
        else:
            # Over-confident: penalize slightly
            scores["confidence_calibration"] = 0.4
    else:
        scores["confidence_calibration"] = 0.0
        reasons.append("No confidence scores found")

    # --- Weighted total ---
    weights = {
        "json_valid": 0.10,
        "entity_coverage": 0.15,
        "property_extraction": 0.25,
        "change_detection": 0.25,
        "evidence_quality": 0.15,
        "confidence_calibration": 0.10,
    }

    total = sum(scores.get(k, 0) * w for k, w in weights.items())

    reason_parts = [f"{k}={v:.2f}" for k, v in sorted(scores.items())]
    if reasons:
        reason_parts.append(" | ".join(reasons))

    return {
        "pass": total >= 0.60,
        "score": round(total, 4),
        "reason": " | ".join(reason_parts),
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _find_entity(entity_states: list, entity_key: str) -> dict | None:
    """Find an entity state by key, with fuzzy matching."""
    for es in entity_states:
        model_key = es.get("entity_key", "")
        if model_key == entity_key:
            return es
        # Fuzzy: match on the ID part
        if entity_key.split(":")[-1] in model_key or model_key.split(":")[-1] in entity_key:
            return es
    return None


def _find_property(model_props: dict, prop_key: str) -> dict | None:
    """Find a property by key with fuzzy matching."""
    if prop_key in model_props:
        return model_props[prop_key]
    # Try partial matches
    for mk, mv in model_props.items():
        if prop_key in mk or mk in prop_key:
            return mv
        # Handle common synonyms
        synonyms = {
            "costume": ["wardrobe", "clothing", "outfit", "attire"],
            "physical_condition": ["injuries", "injury", "physical_state", "body"],
            "emotional_state": ["emotion", "mood", "demeanor", "expression"],
            "props_carried": ["items", "carrying", "possessions"],
            "time_of_day": ["time", "period"],
            "weather": ["conditions", "atmosphere"],
            "condition": ["state", "status", "integrity"],
            "position": ["location", "placement", "where"],
            "ownership": ["holder", "possessor", "carried_by"],
        }
        for canon, alts in synonyms.items():
            if (prop_key == canon and mk in alts) or (mk == canon and prop_key in alts):
                return mv
    return None


def _keys_match(model_key: str, expected_key: str) -> bool:
    """Check if two property keys match, accounting for naming variation."""
    if model_key == expected_key:
        return True
    if expected_key in model_key or model_key in expected_key:
        return True
    # Check synonyms
    synonyms = {
        "costume": ["wardrobe", "clothing", "outfit", "attire"],
        "physical_condition": ["injuries", "injury", "physical_state"],
        "emotional_state": ["emotion", "mood", "demeanor"],
        "time_of_day": ["time", "period"],
        "condition": ["state", "status", "integrity"],
    }
    for canon, alts in synonyms.items():
        all_names = {canon} | set(alts)
        if model_key in all_names and expected_key in all_names:
            return True
    return False


def _evidence_in_text(evidence: str, scene_text: str) -> bool:
    """Check if an evidence quote appears in the scene text (fuzzy)."""
    # Exact match
    if evidence in scene_text:
        return True
    # Try with normalized whitespace
    norm_ev = " ".join(evidence.split())
    norm_text = " ".join(scene_text.split())
    if norm_ev in norm_text:
        return True
    # Try significant words (at least 3 consecutive words match)
    words = norm_ev.split()
    if len(words) >= 3:
        for i in range(len(words) - 2):
            trigram = " ".join(words[i:i + 3])
            if trigram in norm_text:
                return True
    return False
