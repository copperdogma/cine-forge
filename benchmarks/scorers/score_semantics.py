"""Shared score/pass finalization for maintained Promptfoo Python scorers."""

from __future__ import annotations

import math

SCORE_PRECISION = 4


def finalize_score(
    raw_score: float,
    *,
    pass_threshold: float,
    hard_gates: bool,
    reason: str,
) -> dict:
    """Return a score that cannot contradict a failed hard contract.

    The uncapped score remains in the diagnostic reason so failed candidates can
    still be compared during scorer development without advertising a passing
    Promptfoo score.
    """
    bounded = float(raw_score)
    if not math.isfinite(bounded) or not 0.0 <= bounded <= 1.0:
        raise ValueError("raw_score must be finite and within [0, 1]")
    if not math.isfinite(pass_threshold) or not 0.0 < pass_threshold <= 1.0:
        raise ValueError("pass_threshold must be finite and within (0, 1]")

    passed = bool(hard_gates) and bounded >= pass_threshold
    failure_ceiling = pass_threshold - 10**-SCORE_PRECISION
    reported = bounded if passed else min(bounded, failure_ceiling)
    if not passed:
        reason = f"raw_score={bounded:.4f} | {reason}"
    return {
        "pass": passed,
        "score": round(reported, SCORE_PRECISION),
        "reason": reason,
    }
