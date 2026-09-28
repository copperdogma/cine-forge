#!/usr/bin/env python3
"""Source-backed judge recovery; preserves all original subject and judge bytes."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import run_sonnet55_video_comparison as run

GUARD = """
Source-verification clarifications for this rubric (apply identically to both arms):
- The reference is a concise description, not an exhaustive list of visible shapes.
  Concrete additional details supported by the source are valid, not invented.
- In the red lateral-motion packet, the central outlined rectangle and triangular
  diagonal outline are present in every JPEG. Calling them visible shapes is valid.
- In the static warm packet, the left circle/post can read as an abstract figure or
  lamp. The right body is rounded with a smaller circular head. Tan/peach wording
  is compatible with the pixels. Do not enforce hidden object identity.
- The visible small prop changes red-to-blue in the prop packet; both the color
  observation and the continuity-status requirement must be evaluated separately.
  The subject's allowed color vocabulary includes navy, red, teal, etc., but has no
  blue tag. Do not penalize absence of an unavailable tag. Stillness is supported
  by fixed geometry even when the reference has no required motion tag.
- Emotion/tone readings are interpretive for these abstract shapes. Keep reference
  tag mismatch separate from factual invention; do not claim reference tone is
  directly proved by a pixel. Camera mechanism in dialogue is excluded from the
  deterministic aggregate and remains physically ambiguous.
Return score 0..1 and concrete reason under the same >=.80 rubric threshold.
"""


def main():
    if run.RESULT.exists():
        raise RuntimeError(
            "Immutable comparison exists; further paid review requires a new identity"
        )
    run.check_freeze()
    _, _, _, tests = run.matrix()
    selected = [
        t
        for t in tests
        if t["vars"]["evaluation_id"] in {"vfp_active_002", "vfp_active_003", "vfp_active_004"}
    ]
    original_matrix = run.matrix

    def clarified_matrix():
        task, prompt, configs, matrix = original_matrix()
        task = copy.deepcopy(task)
        task["tests"][0]["assert"][1]["value"] += GUARD
        return task, prompt, configs, matrix

    run.matrix = clarified_matrix
    freeze = run.ROOT / "docs/evals/story-225-source-audit-freeze.json"
    if not freeze.exists():
        run.dump(
            freeze,
            {
                "files": [run.inventory(Path(__file__))],
                "scope": "Symmetric Opus recovery on cases002/003/004, actual saved outputs unchanged",  # noqa: E501
                "reason": "Original Opus judge called visible rectangle/triangle invented, disallowed visible head/color descriptors, and asked for unavailable blue color tag.",  # noqa: E501
                "guard": GUARD,
                "judge": "claude-opus-4-6",
                "maximum_six_reservations_usd": ".4536",
                "prior_settled_usd": str(run.accounted()),
            },
        )
    for test in selected:
        for arm in ("sonnet", "luna"):
            row = json.loads(
                (run.OUT / f"subject-{arm}-{test['vars']['evaluation_id']}.json").read_text()
            )
            row["arm"] += "-source-audit"
            run.review("opus", row)


if __name__ == "__main__":
    main()
