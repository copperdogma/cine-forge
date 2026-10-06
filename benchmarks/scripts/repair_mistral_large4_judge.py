#!/usr/bin/env python3
"""Two symmetric saved-answer judge repairs for a demonstrated source-reason defect."""
from __future__ import annotations

import json

import run_mistral_large4_video_comparison as run


def main():
    run.check_freeze()
    original = run._review_request

    def clarified(kind, row):
        body, url, headers = original(kind, row)
        body["messages"][0]["content"] += (
            "\nAdditional original-pixel source verification: The left figure is visibly "
            "cream/tan and the right figure pale/light blue; these literal descriptions "
            "are source-accurate, not imprecise hallucinations. Background is blue/navy. "
            "Camera mechanism is excluded from this case's scoring: do not reward or penalize "
            "static versus inferred push-in as a verified camera mechanism. The observable "
            "figure enlargement is required regardless of that excluded mechanism. "
            "Subjective tone labels should be reported as interpretive disagreement, not "
            "a factual source contradiction. Preserve the maintained rubric and score scale."
        )
        return body, url, headers

    run._review_request = clarified
    for arm in ("mistral", "luna"):
        row = json.loads((run.OUT / f"subject-{arm}-vfp_active_001.json").read_text())
        row["arm"] = arm + "-source-repair"
        run.review("opus", row)


if __name__ == "__main__":
    main()
