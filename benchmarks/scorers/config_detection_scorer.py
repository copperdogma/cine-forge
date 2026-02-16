"""
Project config detection scorer.
Evaluates accuracy of auto-detected project metadata against golden reference.

Scoring dimensions:
- json_valid (0.10): Valid JSON output with all 10 fields
- title_accuracy (0.15): Correct title identification
- format_accuracy (0.10): Correct format detection
- genre_accuracy (0.15): Genre keyword overlap
- tone_accuracy (0.10): Tone keyword overlap
- duration_accuracy (0.10): Duration within expected range
- character_accuracy (0.15): Primary/supporting character identification
- location_accuracy (0.10): Location count and summary
- confidence_quality (0.05): Confidence scores are calibrated
"""

import json
import os
import re


def get_assert(output: str, context: dict) -> dict:
    scores = {}
    reasons = []

    # Load golden reference
    golden_path = context.get("vars", {}).get("golden_path", "")
    if golden_path and not os.path.isabs(golden_path):
        golden_path = os.path.join(os.path.dirname(__file__), "..", golden_path)
    try:
        with open(golden_path) as f:
            golden = json.load(f)
    except Exception as e:
        return {"pass": False, "score": 0.0, "reason": f"Cannot load golden reference: {e}"}

    fields = golden.get("fields", {})

    # Parse JSON output
    text = output.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json|javascript)?\s*", "", text)
        text = re.sub(r"\s*```\s*$", "", text)

    try:
        parsed = json.loads(text)
        scores["json_valid"] = 0.9 if output.strip().startswith("```") else 1.0
    except json.JSONDecodeError:
        return {"pass": False, "score": 0.0, "reason": "Invalid JSON output"}

    def get_field_value(field_name):
        """Extract value from {value, confidence, rationale} wrapper or plain value."""
        raw = parsed.get(field_name)
        if isinstance(raw, dict) and "value" in raw:
            return raw["value"], raw.get("confidence", 0.5)
        return raw, 0.5

    # Title accuracy
    title_golden = fields.get("title", {})
    title_val, title_conf = get_field_value("title")
    if title_val and title_golden.get("expected_value", "").lower() in str(title_val).lower():
        scores["title_accuracy"] = 1.0
    elif title_val:
        scores["title_accuracy"] = 0.3
        reasons.append(f"Title mismatch: got '{title_val}'")
    else:
        scores["title_accuracy"] = 0.0
        reasons.append("Title missing")

    # Format accuracy
    format_golden = fields.get("format", {})
    format_val, _ = get_field_value("format")
    format_expected = format_golden.get("expected_values", [])
    if format_val and any(kw.lower() in str(format_val).lower() for kw in format_expected):
        scores["format_accuracy"] = 1.0
    elif format_val:
        scores["format_accuracy"] = 0.3
    else:
        scores["format_accuracy"] = 0.0

    # Genre accuracy — keyword overlap
    genre_golden = fields.get("genre", {})
    genre_val, _ = get_field_value("genre")
    genre_keywords = genre_golden.get("expected_keywords", [])
    genre_min = genre_golden.get("must_include_at_least", 1)
    if isinstance(genre_val, list):
        genre_text = " ".join(str(g).lower() for g in genre_val)
    else:
        genre_text = str(genre_val or "").lower()
    genre_matches = sum(1 for kw in genre_keywords if kw.lower() in genre_text)
    if genre_matches >= genre_min:
        scores["genre_accuracy"] = min(1.0, genre_matches / len(genre_keywords))
    else:
        scores["genre_accuracy"] = genre_matches / max(1, genre_min) * 0.5
        reasons.append(f"Genre: found {genre_matches}/{genre_min} required keywords")

    # Tone accuracy — keyword overlap
    tone_golden = fields.get("tone", {})
    tone_val, _ = get_field_value("tone")
    tone_keywords = tone_golden.get("expected_keywords", [])
    tone_min = tone_golden.get("must_include_at_least", 1)
    if isinstance(tone_val, list):
        tone_text = " ".join(str(t).lower() for t in tone_val)
    else:
        tone_text = str(tone_val or "").lower()
    tone_matches = sum(1 for kw in tone_keywords if kw.lower() in tone_text)
    if tone_matches >= tone_min:
        scores["tone_accuracy"] = min(1.0, tone_matches / len(tone_keywords))
    else:
        scores["tone_accuracy"] = 0.3

    # Duration accuracy — within range
    dur_golden = fields.get("estimated_duration_minutes", {})
    dur_val, _ = get_field_value("estimated_duration_minutes")
    dur_range = dur_golden.get("expected_range", [0, 999])
    try:
        dur_num = int(dur_val) if dur_val else 0
        if dur_range[0] <= dur_num <= dur_range[1]:
            scores["duration_accuracy"] = 1.0
        elif dur_num > 0:
            # Partial credit for close estimates
            mid = (dur_range[0] + dur_range[1]) / 2
            distance = abs(dur_num - mid) / mid
            scores["duration_accuracy"] = max(0.0, 1.0 - distance)
        else:
            scores["duration_accuracy"] = 0.0
    except (ValueError, TypeError):
        scores["duration_accuracy"] = 0.0

    # Character accuracy — must include primary characters
    primary_golden = fields.get("primary_characters", {})
    primary_val, _ = get_field_value("primary_characters")
    must_include = primary_golden.get("must_include", [])
    if isinstance(primary_val, list):
        primary_text = " ".join(str(c).upper() for c in primary_val)
    else:
        primary_text = str(primary_val or "").upper()
    primary_found = sum(1 for c in must_include if c.upper() in primary_text)

    supporting_golden = fields.get("supporting_characters", {})
    supporting_val, _ = get_field_value("supporting_characters")
    should_include = supporting_golden.get("should_include_any", [])
    if isinstance(supporting_val, list):
        supp_text = " ".join(str(c).upper() for c in supporting_val)
    else:
        supp_text = str(supporting_val or "").upper()
    supp_found = sum(1 for c in should_include if c.upper() in supp_text)

    primary_score = primary_found / max(1, len(must_include))
    supp_score = min(1.0, supp_found / max(1, supporting_golden.get("min_count", 2)))
    scores["character_accuracy"] = 0.6 * primary_score + 0.4 * supp_score

    # Location accuracy
    loc_count_golden = fields.get("location_count", {})
    loc_val, _ = get_field_value("location_count")
    loc_range = loc_count_golden.get("expected_range", [0, 999])
    try:
        loc_num = int(loc_val) if loc_val else 0
        loc_count_score = 1.0 if loc_range[0] <= loc_num <= loc_range[1] else 0.5
    except (ValueError, TypeError):
        loc_count_score = 0.0

    loc_summ_golden = fields.get("locations_summary", {})
    loc_summ_val, _ = get_field_value("locations_summary")
    must_mention = loc_summ_golden.get("must_mention", [])
    summ_text = str(loc_summ_val or "").lower()
    summ_found = sum(1 for kw in must_mention if kw.lower() in summ_text)
    summ_score = summ_found / max(1, len(must_mention))

    scores["location_accuracy"] = 0.4 * loc_count_score + 0.6 * summ_score

    # Confidence quality — check that confidence scores exist and are reasonable
    conf_scores = []
    for field_name in ["title", "format", "genre", "tone", "estimated_duration_minutes",
                       "primary_characters", "supporting_characters", "location_count",
                       "locations_summary", "target_audience"]:
        raw = parsed.get(field_name)
        if isinstance(raw, dict) and "confidence" in raw:
            c = raw["confidence"]
            if isinstance(c, (int, float)) and 0.0 <= c <= 1.0:
                conf_scores.append(1.0)
            else:
                conf_scores.append(0.0)
        else:
            conf_scores.append(0.0)
    scores["confidence_quality"] = sum(conf_scores) / len(conf_scores) if conf_scores else 0.0

    # Weighted composite
    weights = {
        "json_valid": 0.10,
        "title_accuracy": 0.15,
        "format_accuracy": 0.10,
        "genre_accuracy": 0.15,
        "tone_accuracy": 0.10,
        "duration_accuracy": 0.10,
        "character_accuracy": 0.15,
        "location_accuracy": 0.10,
        "confidence_quality": 0.05,
    }

    total = sum(scores.get(k, 0) * w for k, w in weights.items())

    detail_parts = [f"{k}={v:.2f}" for k, v in sorted(scores.items())]
    detail = ", ".join(detail_parts)
    if reasons:
        detail += " | " + "; ".join(reasons)

    return {
        "pass": total >= 0.60,
        "score": round(total, 4),
        "reason": detail,
    }
