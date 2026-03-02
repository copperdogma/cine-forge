"""
Script bible scorer for promptfoo.

Evaluates model output for structural completeness and screenplay-specific
grounding. This is a smoke test + specificity check — not a golden-comparison
scorer (no single "correct" bible exists). Tests:

1. JSON validity
2. Required field presence and non-emptiness
3. Title accuracy (must be "The Mariner")
4. Act structure validity (2-4 acts with required sub-fields)
5. Themes (at least 2, non-generic)
6. Keyword grounding — are screenplay-specific elements present?

Promptfoo calls get_assert(output, context).
"""

import json
import os
import re


def normalize(s: str) -> str:
    return s.lower().strip()


def contains_any(text: str, keywords: list[str]) -> bool:
    text_lower = normalize(text)
    return any(kw.lower() in text_lower for kw in keywords)


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

    full_text = json.dumps(result).lower()

    # 2. Required field presence
    required = golden.get("required_fields", [])
    present = [f for f in required if f in result and result[f] is not None and result[f] != "" and result[f] != []]
    scores["field_completeness"] = len(present) / len(required) if required else 1.0
    missing = [f for f in required if f not in present]
    if missing:
        reasons.append(f"Missing fields: {', '.join(missing[:4])}")

    # 3. Title accuracy
    title = str(result.get("title", "")).strip()
    expected_title = golden.get("must_include_title", "")
    if expected_title.lower() in title.lower():
        scores["title_correct"] = 1.0
    elif title:
        scores["title_correct"] = 0.3
        reasons.append(f"Title: '{title}' (expected '{expected_title}')")
    else:
        scores["title_correct"] = 0.0
        reasons.append("Missing title")

    # 4. Act structure
    acts = result.get("act_structure", [])
    act_min = golden.get("act_count_min", 2)
    act_max = golden.get("act_count_max", 4)
    if not isinstance(acts, list) or len(acts) == 0:
        scores["act_structure"] = 0.0
        reasons.append("No act structure")
    elif act_min <= len(acts) <= act_max:
        # Check sub-fields on first act
        act_fields = ["act_number", "summary"]
        has_fields = all(f in acts[0] for f in act_fields) if acts else False
        scores["act_structure"] = 1.0 if has_fields else 0.7
        if not has_fields:
            reasons.append("Acts missing sub-fields")
    else:
        scores["act_structure"] = 0.5
        reasons.append(f"Act count {len(acts)} outside range [{act_min},{act_max}]")

    # 5. Themes (at least 2)
    themes = result.get("themes", [])
    if not isinstance(themes, list):
        themes = []
    if len(themes) >= 2:
        scores["themes"] = 1.0
    elif len(themes) == 1:
        scores["themes"] = 0.5
        reasons.append("Only 1 theme (expect ≥2)")
    else:
        scores["themes"] = 0.0
        reasons.append("No themes identified")

    # Check must-have theme keywords
    must_themes = golden.get("must_include_themes", [])
    themes_text = json.dumps(themes).lower()
    found_themes = 0
    for theme_req in must_themes:
        if contains_any(themes_text, theme_req["keywords"]):
            found_themes += 1
        else:
            reasons.append(f"Missing theme: {theme_req['description']}")
    if must_themes:
        scores["theme_grounding"] = found_themes / len(must_themes)
    else:
        scores["theme_grounding"] = 1.0

    # 6. Logline quality
    logline = str(result.get("logline", ""))
    logline_kw = golden.get("logline_keywords", [])
    if logline and len(logline) > 20:
        kw_hits = sum(1 for kw in logline_kw if kw.lower() in logline.lower())
        scores["logline_grounding"] = min(1.0, kw_hits / max(1, len(logline_kw) * 0.5))
        if len(logline) > golden.get("logline_max_length", 300):
            scores["logline_grounding"] *= 0.9
            reasons.append(f"Logline too long ({len(logline)} chars)")
    else:
        scores["logline_grounding"] = 0.0
        reasons.append("Empty or trivial logline")

    # 7. Protagonist journey grounding
    pj = str(result.get("protagonist_journey", ""))
    pj_kw = golden.get("protagonist_journey_keywords", [])
    if pj and pj_kw:
        hits = sum(1 for kw in pj_kw if kw.lower() in pj.lower())
        scores["protagonist_journey"] = min(1.0, hits / max(1, len(pj_kw) * 0.4))
    else:
        scores["protagonist_journey"] = 0.5 if pj else 0.0

    # 8. Synopsis length check
    synopsis = str(result.get("synopsis", ""))
    min_len = golden.get("synopsis_min_length", 200)
    if len(synopsis) >= min_len:
        scores["synopsis_length"] = 1.0
    elif len(synopsis) > 50:
        scores["synopsis_length"] = len(synopsis) / min_len
        reasons.append(f"Synopsis short ({len(synopsis)} chars, expect ≥{min_len})")
    else:
        scores["synopsis_length"] = 0.0
        reasons.append("Synopsis too short or missing")

    # 9. Setting grounding
    setting = str(result.get("setting_overview", ""))
    setting_kw = golden.get("setting_keywords", [])
    if setting and setting_kw:
        hits = sum(1 for kw in setting_kw if kw.lower() in setting.lower())
        scores["setting_grounding"] = min(1.0, hits / max(1, len(setting_kw) * 0.4))
    else:
        scores["setting_grounding"] = 0.5 if setting else 0.0

    # Weighted total
    weights = {
        "json_valid": 0.05,
        "field_completeness": 0.20,
        "title_correct": 0.10,
        "act_structure": 0.10,
        "themes": 0.10,
        "theme_grounding": 0.15,
        "logline_grounding": 0.10,
        "protagonist_journey": 0.10,
        "synopsis_length": 0.05,
        "setting_grounding": 0.05,
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
