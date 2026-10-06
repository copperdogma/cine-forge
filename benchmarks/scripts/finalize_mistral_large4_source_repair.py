#!/usr/bin/env python3
"""Write a separate final source-repaired result; retain original phase unchanged."""
from __future__ import annotations

import copy
import json

import run_mistral_large4_video_comparison as run

FINAL = (
    run.ROOT / "benchmarks/results/video-understanding-mistral-large4-vs-luna-v4-20261006-v2.json"
)


def main():
    run.check_freeze()
    result = copy.deepcopy(json.loads(run.RESULT.read_text()))
    result["original_result"] = run.inventory(run.RESULT)
    result["source_review"] = "docs/evals/story-229-source-review-v2.json"
    for row in result["rows"]:
        arm = row["arm"]
        row["original_rubric"] = row["rubric"]
        repaired = json.loads(
            (run.OUT / f"judge-opus-{arm}-source-repair-vfp_active_001.json").read_text()
        )
        row["rubric"] = repaired
        row["rubric_basis"] = "symmetric saved-answer Opus source-color/camera repair"
        row["combined"] = (row["assertion"]["score"] + repaired["score"]) / 2
        row["dual_pass"] = row["assertion"]["pass"] and repaired["score"] >= .8
        result["summary"][arm]["rubric"] = repaired["score"]
        result["summary"][arm]["overall"] = row["combined"]
        result["summary"][arm]["dual_passes"] = int(row["dual_pass"])
    result["ledger"] = run.ledger()
    result["accounted_usd"] = str(run.accounted())
    result["paid_retries"] = 2
    result["subject_retries"] = 0
    result["judge_repairs"] = 2
    assert len(run.ledger()) == 8 and all(r["state"] == "settled" for r in run.ledger())
    assert run.accounted() < run.CAP
    if FINAL.exists():
        assert json.loads(FINAL.read_text()) == result, "Immutable final result differs"
    else:
        run.dump(FINAL, result)
    for path in run.OUT.glob("judge-opus-*-source-repair-*.json"):
        (run.EVIDENCE / path.name).write_bytes(path.read_bytes())
    run.dump(run.EVIDENCE / "ledger-final.json", run.ledger())
    print(json.dumps(result["summary"], indent=2))
    print("Final all-provider USD", run.accounted())


if __name__ == "__main__":
    main()
