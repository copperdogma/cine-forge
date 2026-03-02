"""
Generalized bible extraction scorer for promptfoo.

Evaluates model output against a golden reference for entity extraction quality.
Works for characters, locations, and props — the golden reference format determines
which dimensions are scored.

Scored dimensions (weighted):
- json_valid (0.10): Valid JSON output
- field_completeness (0.10): Required schema fields present
- name_identification (0.10): Correct entity name and aliases
- physical_coverage (0.15): Physical traits / evidence match
- scene_coverage (0.10): Scene presence matches reference
- fact_recall (0.20): Key facts about the entity recalled
- narrative_quality (0.15): Narrative significance captures key themes
- description_quality (0.10): Description is substantive and accurate

Promptfoo calls get_assert(output, context) where:
- output: str — the model's raw text response
- context: dict with 'vars' (test case variables), 'prompt', etc.

Returns: dict with 'pass' (bool), 'score' (0-1), 'reason' (str).
"""

import json
import os
import re


def normalize(s: str) -> str:
    """Normalize a string for fuzzy comparison."""
    s = s.upper().strip()
    s = re.sub(r"\\-", "-", s)
    s = re.sub(r"[^A-Z0-9\s]", "", s)
    s = re.sub(r"\s+", " ", s)
    return s


def text_contains(haystack: str, needle: str) -> bool:
    """Check if normalized needle appears in normalized haystack."""
    return normalize(needle) in normalize(haystack)


def stem_match(text: str, phrase: str) -> bool:
    """Check if key word stems from phrase appear in text."""
    words = phrase.lower().split()
    text_lower = text.lower()
    for word in words:
        stem = word[:5] if len(word) >= 5 else word
        if len(stem) >= 3 and stem in text_lower:
            return True
    return False


def get_assert(output: str, context: dict) -> dict:
    """Promptfoo assertion entry point."""

    golden_path = context.get("vars", {}).get("golden_path", "")
    entity_name = (
        context.get("vars", {}).get("location_name", "")
        or context.get("vars", {}).get("prop_name", "")
        or context.get("vars", {}).get("character_name", "")
    )

    # Resolve golden path
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

    if not entity_name:
        return {"pass": False, "score": 0, "reason": "No entity name in vars"}

    scores = {}
    reasons = []

    # --- 1. JSON validity ---
    try:
        result = json.loads(output)
        scores["json_valid"] = 1.0
    except json.JSONDecodeError:
        match = re.search(r"```(?:json)?\s*([\s\S]*?)```", output)
        if match:
            try:
                result = json.loads(match.group(1))
                scores["json_valid"] = 0.9
                reasons.append("JSON extracted from code block")
            except json.JSONDecodeError:
                return {"pass": False, "score": 0.0, "reason": "Invalid JSON output"}
        else:
            return {"pass": False, "score": 0.0, "reason": "Invalid JSON output"}

    # --- 2. Load golden reference ---
    with open(golden_path) as f:
        all_golden = json.load(f)

    golden_key = entity_name.upper().strip()
    golden = all_golden.get(golden_key)
    if not golden:
        # Try partial match
        for k in all_golden:
            if normalize(entity_name) in normalize(k) or normalize(k) in normalize(entity_name):
                golden = all_golden[k]
                break

    if not golden:
        return {"pass": False, "score": 0, "reason": f"No golden data for entity: {entity_name}"}

    # --- 3. Field completeness ---
    # Detect entity type from golden keys
    if "prop_id" in golden:
        # Prop (check before physical_traits — props also have physical_traits)
        required_fields = [
            "prop_id", "name", "description", "scene_presence",
            "narrative_significance", "overall_confidence",
        ]
    elif "physical_traits" in golden:
        # Location
        required_fields = [
            "location_id", "name", "description", "physical_traits",
            "scene_presence", "narrative_significance", "overall_confidence",
        ]
    else:
        # Character (fallback)
        required_fields = [
            "character_id", "name", "description", "scene_presence",
            "overall_confidence",
        ]

    present = sum(1 for f in required_fields if f in result and result[f] is not None)
    scores["field_completeness"] = present / len(required_fields)
    if present < len(required_fields):
        missing = [f for f in required_fields if f not in result or result[f] is None]
        reasons.append(f"Missing fields: {', '.join(missing[:3])}")

    # --- 4. Name and alias identification ---
    golden_aliases = [a.upper() for a in golden.get("aliases", [])]
    model_name = (result.get("name") or "").upper()
    model_aliases = [a.upper().strip() for a in (result.get("aliases") or [])]
    all_model_names = model_name + " " + " ".join(model_aliases)

    # Check entity name is present
    name_score = 1.0 if normalize(entity_name) in normalize(all_model_names) else 0.5

    # Check aliases
    if golden_aliases:
        model_text = all_model_names + " " + (result.get("description") or "").upper()
        found = sum(1 for a in golden_aliases if normalize(a) in normalize(model_text))
        alias_score = found / len(golden_aliases)
        scores["name_identification"] = (name_score + alias_score) / 2
        if found < len(golden_aliases):
            reasons.append(f"Aliases: {found}/{len(golden_aliases)}")
    else:
        scores["name_identification"] = name_score

    # --- 5. Physical traits / evidence coverage ---
    golden_traits = golden.get("physical_traits", golden.get("must_have_evidence", []))
    if golden_traits:
        model_text = json.dumps(result).lower()
        found = 0
        missing_traits = []
        for trait in golden_traits:
            if stem_match(model_text, trait):
                found += 1
            else:
                missing_traits.append(trait)
        scores["physical_coverage"] = found / len(golden_traits)
        if missing_traits:
            reasons.append(f"Missing traits: {', '.join(missing_traits[:2])}")
    else:
        scores["physical_coverage"] = 1.0

    # --- 6. Scene coverage ---
    golden_scenes = golden.get("must_mention_scenes", [])
    if golden_scenes:
        model_scenes = json.dumps(result.get("scene_presence", []) or []).upper()
        model_scenes += " " + json.dumps(result).upper()

        found = 0
        for scene in golden_scenes:
            scene_words = [w for w in normalize(scene).split() if len(w) > 2]
            if scene_words and all(w in normalize(model_scenes) for w in scene_words):
                found += 1
        scores["scene_coverage"] = found / len(golden_scenes)
        if found < len(golden_scenes):
            reasons.append(f"Scenes: {found}/{len(golden_scenes)} covered")
    else:
        scores["scene_coverage"] = 1.0

    # --- 7. Key fact recall ---
    # Use stem matching (first 5 chars) for facts, same as physical_coverage.
    # Filter stop words to avoid inflating the denominator with trivial matches.
    STOP_WORDS = {
        "the", "and", "for", "was", "are", "has", "had", "his", "her",
        "its", "that", "this", "with", "from", "into", "also", "been",
        "were", "these", "those", "their", "them", "they", "via", "who",
    }
    golden_facts = golden.get("key_facts", [])
    if golden_facts:
        full_output = json.dumps(result).lower()
        found = 0
        for fact in golden_facts:
            terms = [
                t for t in re.findall(r'\b\w{3,}\b', fact.lower())
                if t not in STOP_WORDS
            ]
            if not terms:
                found += 1
                continue
            matches = sum(1 for t in terms if stem_match(full_output, t))
            if matches >= len(terms) * 0.5:
                found += 1
        scores["fact_recall"] = found / len(golden_facts)
        if found < len(golden_facts):
            reasons.append(f"Facts: {found}/{len(golden_facts)} recalled")
    else:
        scores["fact_recall"] = 1.0

    # --- 8. Narrative significance quality ---
    narrative_musts = golden.get("narrative_significance_must_mention", [])
    if narrative_musts:
        narr_text = (result.get("narrative_significance") or "").lower()
        narr_text += " " + (result.get("description") or "").lower()
        found = 0
        for term in narrative_musts:
            if term.lower() in narr_text:
                found += 1
        scores["narrative_quality"] = found / len(narrative_musts)
        if found < len(narrative_musts):
            reasons.append(f"Narrative themes: {found}/{len(narrative_musts)}")
    else:
        # Fallback: just check narrative_significance is non-empty and substantive
        narr = result.get("narrative_significance") or ""
        scores["narrative_quality"] = 1.0 if len(narr) > 30 else 0.5 if len(narr) > 10 else 0.0

    # --- 9. Description quality ---
    desc = result.get("description") or ""
    if len(desc) > 100:
        scores["description_quality"] = 1.0
    elif len(desc) > 40:
        scores["description_quality"] = 0.7
    elif len(desc) > 10:
        scores["description_quality"] = 0.4
    else:
        scores["description_quality"] = 0.0
        reasons.append("Description too short or missing")

    # --- Weighted total ---
    weights = {
        "json_valid": 0.10,
        "field_completeness": 0.10,
        "name_identification": 0.10,
        "physical_coverage": 0.15,
        "scene_coverage": 0.10,
        "fact_recall": 0.20,
        "narrative_quality": 0.15,
        "description_quality": 0.10,
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
