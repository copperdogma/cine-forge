"""
Character extraction scorer for promptfoo.

Evaluates model output against a golden reference for character analysis quality.
Scores on: JSON validity, narrative role, trait coverage, relationship identification,
evidence grounding, scene coverage, and key fact recall.

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


def get_assert(output: str, context: dict) -> dict:
    """Promptfoo assertion entry point."""

    golden_path = context.get("vars", {}).get("golden_path", "")
    character_name = context.get("vars", {}).get("character_name", "")

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

    if not character_name:
        return {"pass": False, "score": 0, "reason": "No character_name in vars"}

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

    golden_key = character_name.upper().strip()
    golden = all_golden.get(golden_key)
    if not golden:
        # Try partial match
        for k in all_golden:
            if (
                normalize(character_name) in normalize(k)
                or normalize(k) in normalize(character_name)
            ):
                golden = all_golden[k]
                break

    if not golden:
        return {
            "pass": False,
            "score": 0,
            "reason": f"No golden data for character: {character_name}",
        }

    # --- 3. Narrative role ---
    model_role = (result.get("narrative_role") or "").lower().strip()
    expected_role = golden["narrative_role"].lower()
    if model_role == expected_role:
        scores["narrative_role"] = 1.0
    elif (
        model_role in ("protagonist", "supporting")
        and expected_role in ("protagonist", "supporting")
    ):
        # Close enough — co-protagonist vs supporting is debatable
        scores["narrative_role"] = 0.7
        reasons.append(f"Role: '{model_role}' vs expected '{expected_role}'")
    else:
        scores["narrative_role"] = 0.0
        reasons.append(f"Role: '{model_role}' vs expected '{expected_role}'")

    # --- 4. Trait coverage ---
    golden_traits = golden.get("key_traits", [])
    if golden_traits:
        # Flatten all model output text that could contain traits
        model_text = json.dumps(result.get("inferred_traits", []) or []).lower()
        model_text += " " + json.dumps(result.get("explicit_evidence", []) or []).lower()
        model_text += " " + (result.get("description") or "").lower()

        found = 0
        missing = []
        for trait in golden_traits:
            # Check if any word stem (5+ char prefix) from the trait appears
            trait_words = trait.lower().split()
            matched = False
            for word in trait_words:
                # Use first 5 chars as stem for fuzzy matching
                stem = word[:5] if len(word) >= 5 else word
                if stem in model_text:
                    matched = True
                    break
            if matched:
                found += 1
            else:
                missing.append(trait)

        scores["trait_coverage"] = found / len(golden_traits)
        if missing:
            reasons.append(f"Missing traits: {', '.join(missing[:3])}")
    else:
        scores["trait_coverage"] = 1.0

    # --- 5. Relationship identification ---
    golden_rels = golden.get("must_have_relationships", [])
    if golden_rels:
        model_rels = result.get("relationships", []) or []
        model_rels_text = json.dumps(model_rels).upper()
        # Also check description for relationship mentions
        model_rels_text += " " + (result.get("description") or "").upper()

        found = 0
        missing = []
        for rel in golden_rels:
            target = normalize(rel["target"])
            # Check if target character is mentioned anywhere in relationships
            if target in normalize(model_rels_text):
                found += 1
            else:
                missing.append(f"{rel['target']} ({rel['type']})")

        scores["relationship_recall"] = found / len(golden_rels)
        if missing:
            reasons.append(f"Missing rels: {', '.join(missing[:3])}")
    else:
        scores["relationship_recall"] = 1.0

    # --- 6. Evidence grounding ---
    golden_evidence = golden.get("must_have_evidence", [])
    if golden_evidence:
        model_evidence_text = json.dumps(result.get("explicit_evidence", []) or []).lower()
        model_evidence_text += " " + json.dumps(result.get("inferred_traits", []) or []).lower()
        model_evidence_text += " " + (result.get("description") or "").lower()

        found = 0
        for ev in golden_evidence:
            if ev.lower() in model_evidence_text:
                found += 1

        scores["evidence_grounding"] = found / len(golden_evidence)
        if found < len(golden_evidence):
            reasons.append(f"Evidence: {found}/{len(golden_evidence)} key items found")
    else:
        scores["evidence_grounding"] = 1.0

    # --- 7. Key fact recall ---
    golden_facts = golden.get("key_facts", [])
    if golden_facts:
        # Serialize entire model output for broad matching
        full_output = json.dumps(result).lower()

        found = 0
        for fact in golden_facts:
            # Extract key terms from the fact (2+ word phrases)
            terms = re.findall(r'\b\w{3,}\b', fact.lower())
            # Require at least half the key terms to appear
            matches = sum(1 for t in terms if t in full_output)
            if terms and matches >= len(terms) * 0.5:
                found += 1

        scores["fact_recall"] = found / len(golden_facts)
        if found < len(golden_facts):
            reasons.append(f"Facts: {found}/{len(golden_facts)} recalled")
    else:
        scores["fact_recall"] = 1.0

    # --- 8. Scene coverage ---
    golden_scenes = golden.get("must_mention_scenes", [])
    if golden_scenes:
        model_scenes = json.dumps(result.get("scene_presence", []) or []).upper()
        # Also check explicit_evidence source_scene fields
        model_scenes += " " + json.dumps(result.get("explicit_evidence", []) or []).upper()

        found = 0
        for scene in golden_scenes:
            # Fuzzy match on key location words
            scene_words = [w for w in normalize(scene).split() if len(w) > 2]
            if scene_words and all(w in normalize(model_scenes) for w in scene_words):
                found += 1

        scores["scene_coverage"] = found / len(golden_scenes)
        if found < len(golden_scenes):
            reasons.append(f"Scenes: {found}/{len(golden_scenes)} covered")
    else:
        scores["scene_coverage"] = 1.0

    # --- 9. Field completeness ---
    required_fields = [
        "character_id", "name", "description", "narrative_role",
        "scene_presence", "dialogue_summary", "relationships",
        "overall_confidence",
    ]
    present = sum(1 for f in required_fields if f in result and result[f] is not None)
    scores["field_completeness"] = present / len(required_fields)

    # --- 10. Alias identification ---
    golden_aliases = [a.upper() for a in golden.get("aliases", [])]
    if golden_aliases:
        model_aliases = [a.upper().strip() for a in (result.get("aliases") or [])]
        # Also check if aliases appear in description
        model_alias_text = " ".join(model_aliases) + " " + (result.get("description") or "").upper()
        found = sum(1 for a in golden_aliases if a in model_alias_text)
        scores["alias_recall"] = found / len(golden_aliases)
        if found < len(golden_aliases):
            reasons.append(f"Aliases: found {found}/{len(golden_aliases)}")
    else:
        scores["alias_recall"] = 1.0

    # --- Weighted total ---
    weights = {
        "json_valid": 0.10,
        "narrative_role": 0.10,
        "trait_coverage": 0.15,
        "relationship_recall": 0.15,
        "evidence_grounding": 0.10,
        "fact_recall": 0.15,
        "scene_coverage": 0.10,
        "field_completeness": 0.05,
        "alias_recall": 0.10,
    }

    total = sum(scores.get(k, 0) * w for k, w in weights.items())

    reason_parts = [f"{k}={v:.2f}" for k, v in sorted(scores.items())]
    if reasons:
        reason_parts.append(" | ".join(reasons))

    return {
        "pass": total >= 0.65,
        "score": round(total, 4),
        "reason": " | ".join(reason_parts),
    }
