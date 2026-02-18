"""
QA pass scorer for promptfoo.

Evaluates whether a model correctly judges AI-extracted scene data
as passing or failing QA against the original scene text.

Scoring dimensions:
- json_valid:         Valid JSON output (0.10)
- pass_correct:       passed bool matches expected (0.30)
- issue_detection:    Correct number/type of issues found (0.25)
- severity_accuracy:  Error vs warning severity appropriate (0.15)
- confidence_calibration: Confidence score reasonable (0.10)
- summary_quality:    Summary present and informative (0.10)

Pass threshold: 0.60
"""

import json
import os
import re


def get_assert(output: str, context: dict) -> dict:
    """Promptfoo assertion entry point."""

    golden_path = context.get("vars", {}).get("golden_path", "")
    test_key = context.get("vars", {}).get("test_key", "")

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

    if test_key not in all_golden:
        return {"pass": False, "score": 0, "reason": f"Test key '{test_key}' not in golden"}

    golden = all_golden[test_key]
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

    # --- 2. Pass/fail correct ---
    expected_passed = golden.get("expected_passed")
    model_passed = result.get("passed")

    if isinstance(model_passed, bool) and model_passed == expected_passed:
        scores["pass_correct"] = 1.0
    elif isinstance(model_passed, bool):
        scores["pass_correct"] = 0.0
        reasons.append(f"passed={model_passed}, expected={expected_passed}")
    else:
        scores["pass_correct"] = 0.0
        reasons.append("'passed' field missing or not boolean")

    # --- 3. Issue detection ---
    issues = result.get("issues", [])

    if expected_passed:
        # Good output — should have few/no errors
        max_errors = golden.get("max_errors", 0)
        error_count = sum(1 for i in issues if i.get("severity") == "error")
        if error_count <= max_errors:
            scores["issue_detection"] = 1.0
        else:
            scores["issue_detection"] = max(0.0, 1.0 - (error_count - max_errors) * 0.3)
            reasons.append(f"Good output: {error_count} errors found (max {max_errors})")
    else:
        # Bad output — should detect specific issues
        min_errors = golden.get("min_errors", 1)
        required_issues = golden.get("required_issues", [])
        error_count = sum(1 for i in issues if i.get("severity") in ("error", "warning"))

        if error_count >= min_errors:
            error_score = 1.0
        else:
            error_score = error_count / min_errors if min_errors > 0 else 0.0

        # Check if specific required issues were caught
        if required_issues:
            all_issue_text = " ".join(
                (i.get("description", "") + " " + i.get("location", "")).lower()
                for i in issues
            )
            caught = 0
            for req in required_issues:
                field = req.get("field", "").lower()
                reason_keywords = req.get("reason", "").lower().split()[:3]
                if field in all_issue_text or any(kw in all_issue_text for kw in reason_keywords):
                    caught += 1
            issue_recall = caught / len(required_issues)
        else:
            issue_recall = 1.0

        scores["issue_detection"] = error_score * 0.4 + issue_recall * 0.6

        if error_count < min_errors:
            reasons.append(f"Bad output: only {error_count} issues (need {min_errors}+)")

    # --- 4. Severity accuracy ---
    if issues:
        if expected_passed:
            # Good output: issues should mostly be notes/warnings, not errors
            non_error_ratio = sum(
                1 for i in issues if i.get("severity") in ("note", "warning")
            ) / len(issues)
            scores["severity_accuracy"] = non_error_ratio
        else:
            # Bad output: should have actual errors, not just notes
            has_errors = any(i.get("severity") == "error" for i in issues)
            scores["severity_accuracy"] = 1.0 if has_errors else 0.3
    else:
        scores["severity_accuracy"] = 1.0 if expected_passed else 0.0

    # --- 5. Confidence calibration ---
    confidence = result.get("confidence", 0.5)
    if isinstance(confidence, (int, float)):
        if 0.0 <= confidence <= 1.0:
            # Good output should have high confidence, bad should have high confidence in rejection
            scores["confidence_calibration"] = 1.0 if confidence >= 0.5 else 0.5
        else:
            scores["confidence_calibration"] = 0.0
    else:
        scores["confidence_calibration"] = 0.0

    # --- 6. Summary quality ---
    summary = result.get("summary", "")
    if summary and len(summary) > 10:
        scores["summary_quality"] = 1.0
    elif summary:
        scores["summary_quality"] = 0.5
    else:
        scores["summary_quality"] = 0.0
        reasons.append("No summary provided")

    # --- Weighted total ---
    weights = {
        "json_valid": 0.10,
        "pass_correct": 0.30,
        "issue_detection": 0.25,
        "severity_accuracy": 0.15,
        "confidence_calibration": 0.10,
        "summary_quality": 0.10,
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
