#!/usr/bin/env python3
"""Verify immutable Story 226 results from tracked receipts without provider calls."""

from __future__ import annotations

import hashlib
import json
from statistics import mean

import run_gpt61_video_comparison as run
from video_understanding_scorer import get_assert


def main() -> None:
    run.check_freeze()
    manifest = json.loads(
        (run.ROOT / "docs/evals/story-226-gpt61-sol-evidence.json").read_text()
    )
    for item in manifest["tracked_receipts"]:
        data = (run.ROOT / item["path"]).read_bytes()
        assert len(data) == item["bytes"]
        assert hashlib.sha256(data).hexdigest() == item["sha256"], item["path"]
    result = json.loads(run.RESULT.read_text())
    _, _, _, tests = run.matrix()
    scores: dict[str, list[float]] = {"sol": [], "luna": []}
    for test in tests:
        case = test["vars"]["evaluation_id"]
        for arm in scores:
            subject = json.loads((run.EVIDENCE / f"subject-{arm}-{case}.json").read_text())
            judge_name = (
                f"judge-sonnet-source-adjudication-{arm}-{case}.json"
                if case == "vfp_active_004" else f"judge-opus-{arm}-{case}.json"
            )
            judge = json.loads((run.EVIDENCE / judge_name).read_text())
            structural = get_assert(subject["response"]["output"], {"vars": test["vars"]})
            combined = (structural["score"] + judge["score"]) / 2
            saved = next(
                r for r in result["rows"]
                if r["arm"] == arm and r["vars"]["evaluation_id"] == case
            )
            assert saved["response"] == subject["response"]
            assert saved["combined_adjudicated"] == combined
            scores[arm].append(combined)
    for arm, values in scores.items():
        assert mean(values) == result["summary"][arm]["combined_mean"]
    ledger = result["ledger"]
    assert len(ledger) == 30 and all(row["state"] == "settled" for row in ledger)
    total = sum((run.Decimal(str(row["accounted_usd"])) for row in ledger), run.Decimal(0))
    assert total == run.Decimal(result["settled_estimated_usd"]) < run.Decimal(4)
    assert total == run.Decimal(manifest["settled_estimated_usd"])
    print("Story 226: PASS — 90 receipt hashes, 12 scores, 30 settled calls; no provider calls")


if __name__ == "__main__":
    main()
