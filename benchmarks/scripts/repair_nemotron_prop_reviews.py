#!/usr/bin/env python3
"""One symmetric source-backed judge-contract repair; reuses saved subjects."""

# ruff: noqa: E501

import inspect
import json

import run_nemotron_video_comparison as run

original_request = run._review_request


def repaired_request(kind, row):
    body, url, headers = original_request(kind, row)
    body["messages"][0]["content"][0]["text"] += """
CORRECT THE DEMONSTRATED REVIEW-CONTRACT FAULTS ONLY:
- Evidence requires 2-4 entries; frames0,2,4 suffice. Do not penalize omission of frame1.
- "changes from red to blue" does not assert gradual interpolation; accept as the visible discrete change.
- Static geometry and stillness are visible; neither stillness nor mentioning visible red is an invention.
- Generic blue has no allowed enum value. Correct blue in text satisfies color observation.
- Do not require wide_master, detached/none, mood, or an absent tag when the visible source does not discriminate it.
- The declared continuity contract DOES treat the unexplained rectangle-color swap as broken. Both outputs label intact: preserve this real semantic failure.
Return the same score/reason JSON on the unchanged output and full source images. Explain remaining source-backed errors without the exclusions above. Do not tune toward a passing score."""
    return body, url, headers


run._review_request = repaired_request
source = (
    inspect.getsource(run.review)
    .replace("def review(", "def repair_review(")
    .replace('f"judge-', 'f"repair-')
)
exec(source, run.__dict__)
if __name__ == "__main__":
    for arm in ("sol", "luna"):
        row = json.loads((run.EVIDENCE / f"subject-{arm}-vfp_active_004.json").read_text())
        run.repair_review("opus", row)
