"""
Relationship discovery scorer for entity graph benchmarks.
Evaluates quality of discovered relationships against golden reference.

Scoring dimensions:
- json_valid (0.10): Valid JSON output with edges array
- field_completeness (0.10): All required EntityEdge fields present
- must_find_recall (0.25): Coverage of critical must-find relationships
- evidence_quality (0.20): Evidence lists are non-empty and specific
- relationship_type_accuracy (0.10): Relationship type labels are meaningful
- direction_accuracy (0.05): Direction field is correctly set
- confidence_calibration (0.05): Confidence scores are reasonable
- precision (0.15): No obviously false or fabricated relationships
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

    must_find = golden.get("must_find_relationships", [])
    min_must_find = golden.get("min_must_find", 3)
    max_total = golden.get("max_total_edges", 15)

    # 1. JSON validity
    text = output.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json|javascript)?\s*", "", text)
        text = re.sub(r"\s*```\s*$", "", text)

    try:
        parsed = json.loads(text)
        edges = parsed.get("edges", parsed if isinstance(parsed, list) else [])
        if isinstance(parsed, list):
            edges = parsed
        scores["json_valid"] = 0.9 if output.strip().startswith("```") else 1.0
    except json.JSONDecodeError:
        return {"pass": False, "score": 0.0, "reason": "Invalid JSON output"}

    if not isinstance(edges, list) or len(edges) == 0:
        return {"pass": False, "score": 0.05, "reason": "No edges found in output"}

    # 2. Field completeness
    required_fields = ["source_type", "source_id", "target_type", "target_id",
                       "relationship_type", "direction", "evidence", "confidence"]
    field_scores = []
    for edge in edges:
        if not isinstance(edge, dict):
            field_scores.append(0.0)
            continue
        present = sum(1 for f in required_fields if f in edge and edge[f] is not None)
        field_scores.append(present / len(required_fields))
    scores["field_completeness"] = sum(field_scores) / len(field_scores)

    # 3. Must-find recall — the most important dimension
    found_count = 0
    found_details = []
    for mf in must_find:
        keywords = [k.lower() for k in mf.get("relationship_type_keywords", [])]
        source_id = mf.get("source_id", "").lower()
        target_id = mf.get("target_id", "").lower()

        matched = False
        for edge in edges:
            if not isinstance(edge, dict):
                continue
            e_src = str(edge.get("source_id", "")).lower().replace("_", "-")
            e_tgt = str(edge.get("target_id", "")).lower().replace("_", "-")
            e_type = str(edge.get("relationship_type", "")).lower()

            # Check if source and target match (in either direction)
            ids_match = (
                (source_id in e_src and target_id in e_tgt) or
                (target_id in e_src and source_id in e_tgt)
            )
            if not ids_match:
                continue

            # Check if relationship type matches any keyword
            type_match = any(kw in e_type for kw in keywords)
            if type_match or ids_match:
                matched = True
                found_details.append(mf["relationship_id"])
                break

        if matched:
            found_count += 1

    critical = [mf for mf in must_find if mf.get("importance") == "critical"]
    critical_found = sum(1 for mf in critical if mf["relationship_id"] in found_details)

    # Weight critical relationships more heavily
    if len(critical) > 0:
        critical_ratio = critical_found / len(critical)
    else:
        critical_ratio = 1.0
    overall_ratio = found_count / len(must_find) if must_find else 1.0
    scores["must_find_recall"] = (0.6 * critical_ratio) + (0.4 * overall_ratio)

    if found_count < min_must_find:
        reasons.append(
            "Only found "
            f"{found_count}/{len(must_find)} must-find relationships "
            f"(min: {min_must_find})"
        )

    # 4. Evidence quality
    evidence_scores = []
    for edge in edges:
        if not isinstance(edge, dict):
            evidence_scores.append(0.0)
            continue
        ev = edge.get("evidence", [])
        if not isinstance(ev, list):
            evidence_scores.append(0.0)
            continue
        if len(ev) == 0:
            evidence_scores.append(0.0)
        elif len(ev) == 1:
            evidence_scores.append(0.5)
        else:
            # Check evidence specificity — longer evidence is generally more specific
            avg_len = sum(len(str(e)) for e in ev) / len(ev)
            specificity = min(1.0, avg_len / 40)  # 40+ chars = full score
            evidence_scores.append(min(1.0, 0.5 + 0.5 * specificity))
    scores["evidence_quality"] = (
        sum(evidence_scores) / len(evidence_scores) if evidence_scores else 0.0
    )

    # 5. Relationship type accuracy
    # Check that types are meaningful labels, not empty or generic
    type_scores = []
    generic_types = {"related", "associated", "connected", "linked", "relationship"}
    for edge in edges:
        if not isinstance(edge, dict):
            type_scores.append(0.0)
            continue
        rtype = str(edge.get("relationship_type", "")).lower().strip()
        if not rtype:
            type_scores.append(0.0)
        elif rtype in generic_types:
            type_scores.append(0.3)
        else:
            type_scores.append(1.0)
    scores["relationship_type_accuracy"] = (
        sum(type_scores) / len(type_scores) if type_scores else 0.0
    )

    # 6. Direction accuracy
    valid_dirs = {"symmetric", "source_to_target", "target_to_source"}
    dir_scores = []
    for edge in edges:
        if not isinstance(edge, dict):
            dir_scores.append(0.0)
            continue
        d = str(edge.get("direction", "")).lower().strip()
        dir_scores.append(1.0 if d in valid_dirs else 0.0)
    scores["direction_accuracy"] = sum(dir_scores) / len(dir_scores) if dir_scores else 0.0

    # 7. Confidence calibration
    conf_scores = []
    for edge in edges:
        if not isinstance(edge, dict):
            conf_scores.append(0.0)
            continue
        c = edge.get("confidence", None)
        if isinstance(c, (int, float)) and 0.0 <= c <= 1.0:
            conf_scores.append(1.0)
        else:
            conf_scores.append(0.0)
    scores["confidence_calibration"] = sum(conf_scores) / len(conf_scores) if conf_scores else 0.0

    # 8. Precision — penalize too many edges (likely noise)
    edge_count = len(edges)
    if edge_count <= max_total:
        scores["precision"] = 1.0
    else:
        # Graceful degradation for slight excess
        scores["precision"] = max(0.3, 1.0 - (edge_count - max_total) * 0.1)

    # Weighted composite
    weights = {
        "json_valid": 0.10,
        "field_completeness": 0.10,
        "must_find_recall": 0.25,
        "evidence_quality": 0.20,
        "relationship_type_accuracy": 0.10,
        "direction_accuracy": 0.05,
        "confidence_calibration": 0.05,
        "precision": 0.15,
    }

    total = sum(scores.get(k, 0) * w for k, w in weights.items())

    detail_parts = [f"{k}={v:.2f}" for k, v in sorted(scores.items())]
    detail = (
        f"Found {found_count}/{len(must_find)} must-find "
        f"({critical_found}/{len(critical)} critical), {edge_count} total edges. "
        + ", ".join(detail_parts)
    )
    if reasons:
        detail += " | " + "; ".join(reasons)

    return {
        "pass": total >= 0.55 and found_count >= min_must_find,
        "score": round(total, 4),
        "reason": detail,
    }
