"""
Scene extraction scorer for promptfoo.

Promptfoo calls get_assert(output, context) where:
- output: str — the model's raw text response
- context: dict with 'vars' (test case variables), 'prompt', etc.

Returns: dict with 'pass' (bool), 'score' (0-1), 'reason' (str).
"""

import json
import os
import re
from difflib import SequenceMatcher


def normalize(s: str) -> str:
    """Normalize a string for fuzzy comparison."""
    s = s.upper().strip()
    s = re.sub(r"\\-", "-", s)
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[^\w\s/-]", "", s)
    return s


def heading_similarity(a: str, b: str) -> float:
    """Fuzzy match two scene headings."""
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()


def get_assert(output: str, context: dict) -> dict:
    """Promptfoo assertion entry point."""

    golden_path = context.get("vars", {}).get("golden_path", "")

    # Resolve relative path from the benchmarks directory
    if golden_path and not os.path.isabs(golden_path):
        # Try relative to the config file's parent (benchmarks/)
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidate = os.path.join(base, golden_path)
        if os.path.exists(candidate):
            golden_path = candidate
        else:
            # Try relative to CWD
            candidate = os.path.join(os.getcwd(), golden_path)
            if os.path.exists(candidate):
                golden_path = candidate

    if not golden_path or not os.path.exists(golden_path):
        return {"pass": False, "score": 0, "reason": f"Golden file not found: {golden_path}"}

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

    # --- 2. Structure check ---
    if "scenes" not in result or not isinstance(result["scenes"], list):
        return {"pass": False, "score": 0.1, "reason": "Missing 'scenes' array"}

    # --- 3. Load golden reference ---
    with open(golden_path) as f:
        golden = json.load(f)

    model_scenes = result["scenes"]
    golden_scenes = golden["scenes"]

    # --- 4. Scene count accuracy ---
    count_diff = abs(len(model_scenes) - len(golden_scenes))
    if count_diff == 0:
        scores["scene_count"] = 1.0
    elif count_diff <= 2:
        scores["scene_count"] = 0.7
        reasons.append(f"Count: {len(model_scenes)} vs {len(golden_scenes)} golden (off by {count_diff})")
    else:
        scores["scene_count"] = max(0.0, 1.0 - (count_diff / len(golden_scenes)))
        reasons.append(f"Count: {len(model_scenes)} vs {len(golden_scenes)} golden (off by {count_diff})")

    # --- 5. Heading matching ---
    matched = 0
    heading_scores = []
    used_golden = set()

    for ms in model_scenes:
        mh = ms.get("heading", "")
        best_sim = 0.0
        best_idx = -1
        for i, gs in enumerate(golden_scenes):
            if i in used_golden:
                continue
            sim = heading_similarity(mh, gs["heading"])
            if sim > best_sim:
                best_sim = sim
                best_idx = i
        if best_sim > 0.5:
            matched += 1
            used_golden.add(best_idx)
            heading_scores.append(best_sim)

    if golden_scenes:
        scores["heading_match"] = matched / len(golden_scenes)
        scores["heading_quality"] = sum(heading_scores) / len(heading_scores) if heading_scores else 0.0

    if matched < len(golden_scenes):
        reasons.append(f"Matched {matched}/{len(golden_scenes)} headings")

    # --- 6. Character extraction ---
    golden_chars = set()
    for gs in golden_scenes:
        for c in gs.get("characters", []):
            golden_chars.add(normalize(c))

    model_chars = set()
    for ms in model_scenes:
        for c in ms.get("characters", []):
            model_chars.add(normalize(c))

    if golden_chars:
        char_recall = len(golden_chars & model_chars) / len(golden_chars)
        scores["character_recall"] = char_recall
        missing = golden_chars - model_chars
        if missing:
            reasons.append(f"Missing chars: {', '.join(sorted(missing)[:5])}")
    else:
        scores["character_recall"] = 1.0

    # --- 7. Summary quality ---
    summaries_present = sum(1 for ms in model_scenes if ms.get("summary", "").strip())
    scores["summary_completeness"] = summaries_present / len(model_scenes) if model_scenes else 0.0

    # --- 8. Field completeness ---
    required_fields = ["scene_number", "heading", "int_ext", "location", "time_of_day", "summary", "characters"]
    field_scores = []
    for ms in model_scenes:
        present = sum(1 for f in required_fields if f in ms and ms[f] is not None)
        field_scores.append(present / len(required_fields))
    scores["field_completeness"] = sum(field_scores) / len(field_scores) if field_scores else 0.0

    # --- Weighted total ---
    weights = {
        "json_valid": 0.15,
        "scene_count": 0.20,
        "heading_match": 0.20,
        "heading_quality": 0.10,
        "character_recall": 0.10,
        "summary_completeness": 0.10,
        "field_completeness": 0.15,
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
