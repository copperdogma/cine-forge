#!/usr/bin/env python3
"""Symmetric saved-control judge repair for demonstrated source-contract faults."""

# ruff: noqa: E501

import inspect
import json

import run_deepseek1017_video_comparison as run

original_request = run._review_request


def repaired_request(kind, row):
    body, url, headers = original_request(kind, row)
    body["messages"][0]["content"][-1]["text"] += """
CORRECT DEMONSTRATED REVIEW-CONTRACT FAULTS ONLY:
Generic blue is absent from allowed color_tags: accurate red-to-blue text satisfies observation. Do not claim either answer failed to note the change properly when its summary/evidence explicitly locates it. Stillness describes the visible fixed geometry and is not an invented event. Evidence needs2-4 grounded entries, not every frame. Do not penalize wide_master/detached/none or mood where source does not discriminate. The declared continuity contract DOES call the unexplained color swap broken; both answers label intact. Retain this real semantic error. Apply the unchanged rubric and source images to both saved answers. Do not tune toward a passing score.
"""
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
