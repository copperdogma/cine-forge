"""
Scene enrichment scorer for promptfoo.

Evaluates whether a model correctly infers scene metadata (location,
time, characters, narrative beats, tone) from a raw scene excerpt.

Scoring dimensions:
- json_valid:          Valid JSON output (0.10)
- location_accuracy:   Correct location and int/ext (0.15)
- time_accuracy:       Correct time of day (0.10)
- character_recall:    All expected characters found (0.20)
- beat_quality:        Narrative beats present and relevant (0.20)
- tone_accuracy:       Tone matches expected mood (0.15)
- field_completeness:  All required fields present (0.10)

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

    # --- 2. Location accuracy ---
    expected_location = golden.get("location", "").upper()
    expected_int_ext = golden.get("int_ext", "").upper()

    model_location = str(result.get("location", "")).upper()
    model_int_ext = str(result.get("int_ext", "")).upper()

    loc_score = 0.0
    # Fuzzy match: check if key words from expected location appear
    if expected_location:
        expected_words = set(expected_location.split())
        model_words = set(model_location.split())
        # Remove common filler words
        filler = {"THE", "A", "AN", "-", ""}
        expected_words -= filler
        model_words -= filler
        if expected_words and expected_words & model_words:
            overlap = len(expected_words & model_words) / len(expected_words)
            loc_score += overlap * 0.6
        elif expected_location in model_location or model_location in expected_location:
            loc_score += 0.6
    if model_int_ext == expected_int_ext:
        loc_score += 0.4
    scores["location_accuracy"] = min(loc_score, 1.0)

    if loc_score < 0.8:
        reasons.append(f"Location: got '{model_location}' / '{model_int_ext}', "
                       f"expected '{expected_location}' / '{expected_int_ext}'")

    # --- 3. Time of day ---
    expected_time = golden.get("time_of_day", "").upper()
    model_time = str(result.get("time_of_day", "")).upper()
    if expected_time and model_time:
        if expected_time in model_time or model_time in expected_time:
            scores["time_accuracy"] = 1.0
        else:
            scores["time_accuracy"] = 0.0
            reasons.append(f"Time: got '{model_time}', expected '{expected_time}'")
    else:
        scores["time_accuracy"] = 0.5

    # --- 4. Character recall ---
    expected_chars = {c.upper() for c in golden.get("characters_present", [])}
    model_chars = {str(c).upper() for c in result.get("characters_present", [])}

    if expected_chars:
        # Allow partial name matches (e.g., "THE MARINER" matches "MARINER")
        matched = 0
        for ec in expected_chars:
            ec_words = set(ec.split())
            for mc in model_chars:
                mc_words = set(mc.split())
                if ec_words & mc_words:
                    matched += 1
                    break
        scores["character_recall"] = matched / len(expected_chars)
        if matched < len(expected_chars):
            reasons.append(f"Characters: {matched}/{len(expected_chars)} found")
    else:
        scores["character_recall"] = 1.0

    # --- 5. Narrative beat quality ---
    beats = result.get("narrative_beats", [])
    expected_beat_types = {bt.lower() for bt in golden.get("expected_beat_types", [])}
    key_details = [d.lower() for d in golden.get("key_details", [])]

    if expected_beat_types:
        # Check beat type coverage
        model_beat_types = {str(b.get("beat_type", "")).lower() for b in beats}
        type_overlap = len(expected_beat_types & model_beat_types) / len(expected_beat_types)

        # Check if descriptions mention key details
        all_descriptions = " ".join(
            str(b.get("description", "")).lower() for b in beats
        )
        detail_matches = sum(
            1 for d in key_details
            if any(word in all_descriptions for word in d.split()[:3])
        ) / len(key_details) if key_details else 0.5

        scores["beat_quality"] = type_overlap * 0.5 + detail_matches * 0.3 + (0.2 if len(beats) >= 2 else 0.0)
    else:
        scores["beat_quality"] = 0.5 if beats else 0.0

    if len(beats) == 0:
        reasons.append("No narrative beats found")

    # --- 6. Tone accuracy ---
    expected_tones = {t.lower() for t in golden.get("expected_tone", [])}
    model_tone = str(result.get("tone_mood", "")).lower()
    tone_shifts = [str(s).lower() for s in result.get("tone_shifts", [])]
    all_tone_text = model_tone + " " + " ".join(tone_shifts)

    if expected_tones:
        tone_matches = sum(1 for t in expected_tones if t in all_tone_text)
        scores["tone_accuracy"] = min(tone_matches / max(len(expected_tones) * 0.5, 1), 1.0)
        if tone_matches == 0:
            reasons.append(f"Tone: got '{model_tone}', expected one of {expected_tones}")
    else:
        scores["tone_accuracy"] = 0.5

    # --- 7. Field completeness ---
    required = ["heading", "location", "time_of_day", "int_ext",
                 "characters_present", "narrative_beats", "tone_mood"]
    present = sum(1 for f in required if f in result and result[f] is not None)
    scores["field_completeness"] = present / len(required)

    # --- Weighted total ---
    weights = {
        "json_valid": 0.10,
        "location_accuracy": 0.15,
        "time_accuracy": 0.10,
        "character_recall": 0.20,
        "beat_quality": 0.20,
        "tone_accuracy": 0.15,
        "field_completeness": 0.10,
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
