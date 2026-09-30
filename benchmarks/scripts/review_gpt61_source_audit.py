#!/usr/bin/env python3
"""Rejudge a source-proven indexing defect without repeating subject requests."""

from __future__ import annotations

import copy
import json

import run_gpt61_video_comparison as run

CLARIFICATION = """
Source-verified clarification for the prop-color packet, applied to both arms:
The five images use zero-based frame_index 0,1,2,3,4. The tabletop rectangle
is red at indexes 0 and 1; blue at indexes 2, 3 and 4. Thus the change between
the second and third samples means BETWEEN frame_index 1 and frame_index 2.
Do not penalize a claim that frame_index 2 is blue. The allowed color_tags
vocabulary has no generic blue tag, so do not penalize its absence. A stillness
tag is compatible with unchanged geometry even though the reference requires
no motion tag. Continue to penalize marking continuity_status intact when the
observed red-to-blue prop change requires broken. Return the same score and
reason schema under the original >=0.80 rubric.
"""


def main() -> None:
    if run.RESULT.exists():
        raise RuntimeError("Immutable comparison exists; preserve its judgment history")
    run.check_freeze()
    original_matrix = run.matrix

    def clarified_matrix():
        task, prompt, configs, tests = original_matrix()
        task = copy.deepcopy(task)
        task["tests"][0]["assert"][1]["value"] += CLARIFICATION
        return task, prompt, configs, tests

    run.matrix = clarified_matrix
    for arm in ("sol", "luna"):
        row = json.loads((run.OUT / f"subject-{arm}-vfp_active_004.json").read_text())
        row["arm"] = f"{arm}-source-audit"
        run.review("opus", row)


if __name__ == "__main__":
    main()
