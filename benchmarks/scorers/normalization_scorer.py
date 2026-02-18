"""
Normalization scorer for promptfoo.

Evaluates whether a model correctly converts prose or broken formatting
into valid Fountain screenplay format.

Scoring dimensions:
- scene_headings:      Scene headings present and ALL CAPS (0.20)
- character_cues:      Character names as ALL CAPS cues (0.20)
- dialogue_preserved:  Key dialogue fragments preserved (0.20)
- no_markdown:         No forbidden markdown patterns (0.15)
- structure_quality:   Blank lines before cues, parentheticals correct (0.15)
- content_completeness: All expected characters appear (0.10)

Pass threshold: 0.65
"""

import json
import os
import re


def get_assert(output: str, context: dict) -> dict:
    """Promptfoo assertion entry point."""

    golden_path = context.get("vars", {}).get("golden_path", "")

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
        golden = json.load(f)

    # Strip markdown code fences if model wrapped the output
    text = output.strip()
    fence_match = re.search(r"```(?:\w+)?\s*([\s\S]*?)```", text)
    if fence_match:
        text = fence_match.group(1).strip()

    lines = text.split("\n")
    scores = {}
    reasons = []

    # --- 1. Scene headings present and ALL CAPS ---
    expected_scenes = golden.get("expected_scenes", [])
    scene_heading_pattern = re.compile(r"^\s*(INT\.|EXT\.|INT\./EXT\.)\s+.+", re.IGNORECASE)
    found_headings = [l.strip() for l in lines if scene_heading_pattern.match(l.strip())]
    uppercase_headings = [h for h in found_headings if h == h.upper()]

    if expected_scenes:
        # Check how many expected scenes have a matching heading
        matched = 0
        for expected in expected_scenes:
            exp_upper = expected.upper()
            for heading in found_headings:
                if exp_upper in heading.upper():
                    matched += 1
                    break
        heading_recall = matched / len(expected_scenes)
        uppercase_ratio = len(uppercase_headings) / len(found_headings) if found_headings else 0.0
        scores["scene_headings"] = heading_recall * 0.6 + uppercase_ratio * 0.4
        if matched < len(expected_scenes):
            reasons.append(f"Headings: {matched}/{len(expected_scenes)} matched")
        if uppercase_ratio < 1.0:
            reasons.append(f"Non-uppercase headings found")
    else:
        scores["scene_headings"] = 1.0 if found_headings else 0.0

    # --- 2. Character cues ALL CAPS ---
    expected_chars = [c.upper() for c in golden.get("expected_characters", [])]
    # A character cue is an all-caps line preceded by a blank line
    char_cue_pattern = re.compile(r"^[A-Z][A-Z\s.'()]+$")
    found_cues = set()
    for i, line in enumerate(lines):
        stripped = line.strip()
        if char_cue_pattern.match(stripped) and len(stripped) < 60:
            # Check it's preceded by a blank line (or is line 0)
            if i == 0 or lines[i - 1].strip() == "":
                # Extract base name (remove parenthetical extensions like "(V.O.)")
                base = re.sub(r"\s*\(.*?\)\s*$", "", stripped).strip()
                if base:
                    found_cues.add(base)

    if expected_chars:
        char_recall = sum(1 for c in expected_chars if c in found_cues) / len(expected_chars)
        scores["character_cues"] = char_recall
        missing = [c for c in expected_chars if c not in found_cues]
        if missing:
            reasons.append(f"Missing cues: {', '.join(missing[:3])}")
    else:
        scores["character_cues"] = 1.0 if found_cues else 0.0

    # --- 3. Dialogue preserved ---
    required_dialogue = golden.get("required_dialogue", [])
    text_lower = text.lower()
    if required_dialogue:
        found_count = sum(
            1 for d in required_dialogue
            if d["fragment"].lower() in text_lower
        )
        scores["dialogue_preserved"] = found_count / len(required_dialogue)
        if found_count < len(required_dialogue):
            reasons.append(f"Dialogue: {found_count}/{len(required_dialogue)} fragments found")
    else:
        scores["dialogue_preserved"] = 1.0

    # --- 4. No markdown formatting ---
    forbidden = golden.get("forbidden_patterns", [])
    violations = 0
    for pattern in forbidden:
        try:
            if re.search(pattern, text, re.MULTILINE):
                violations += 1
                reasons.append(f"Forbidden pattern: {pattern}")
        except re.error:
            pass
    if forbidden:
        scores["no_markdown"] = max(0.0, 1.0 - (violations / len(forbidden)))
    else:
        scores["no_markdown"] = 1.0

    # --- 5. Structure quality ---
    structure_score = 0.0
    checks = 0

    # Blank line before character cues
    cue_blank_count = 0
    cue_total = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if char_cue_pattern.match(stripped) and len(stripped) < 60 and stripped in found_cues:
            cue_total += 1
            if i > 0 and lines[i - 1].strip() == "":
                cue_blank_count += 1
    if cue_total > 0:
        structure_score += cue_blank_count / cue_total
        checks += 1

    # Parentheticals in parens
    paren_pattern = re.compile(r"^\s*\([^)]+\)\s*$")
    parens_found = [l for l in lines if paren_pattern.match(l)]
    # If source had parentheticals, check they're formatted
    if "trying to sound calm" in text_lower or "half-smiling" in text_lower or "half smiling" in text_lower:
        has_parens = len(parens_found) > 0
        structure_score += 1.0 if has_parens else 0.0
        checks += 1

    scores["structure_quality"] = structure_score / checks if checks > 0 else 0.5

    # --- 6. Content completeness ---
    if expected_chars:
        text_upper = text.upper()
        chars_mentioned = sum(1 for c in expected_chars if c in text_upper)
        scores["content_completeness"] = chars_mentioned / len(expected_chars)
    else:
        scores["content_completeness"] = 1.0

    # --- Weighted total ---
    weights = {
        "scene_headings": 0.20,
        "character_cues": 0.20,
        "dialogue_preserved": 0.20,
        "no_markdown": 0.15,
        "structure_quality": 0.15,
        "content_completeness": 0.10,
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
