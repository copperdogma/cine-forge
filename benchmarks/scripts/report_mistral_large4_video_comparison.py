#!/usr/bin/env python3
"""Offline report for the predeclared first-case semantic stop."""
from __future__ import annotations

import json
from statistics import mean

import run_mistral_large4_video_comparison as run
from video_understanding_scorer import get_assert, score_output_against_target


def main():
    run.check_freeze()
    _, _, _, tests = run.matrix()
    rows = []
    for test in tests:
        case = test["vars"]["evaluation_id"]
        for arm in ("mistral", "luna"):
            judge_path = run.OUT / f"judge-opus-{arm}-{case}.json"
            if not judge_path.exists():
                continue
            row = json.loads((run.OUT / f"subject-{arm}-{case}.json").read_text())
            grade = json.loads(judge_path.read_text())
            assertion = get_assert(row["response"]["output"], {"vars": test["vars"]})
            details = score_output_against_target(
                output=row["response"]["output"],
                target_path=run.ROOT / "benchmarks" / test["vars"]["target_path"],
                model_label=arm, prompt_version="video-understanding-frame-packet-v3",
                expected_clip_id=case,
            ).model_dump()
            rows.append({
                **row, "assertion": assertion, "details": details, "rubric": grade,
                "combined": (assertion["score"] + grade["score"]) / 2,
                "dual_pass": assertion["pass"] and grade["score"] >= .8,
                "latency_gate_pass": row["response"]["latencyMs"] <= 15000,
                "cost_gate_pass": row["response"]["cost"] <= .02,
            })
    assert len(rows) == 2, "The reviewed progressive stop must remain first-case only"
    summary = {}
    for arm in ("mistral", "luna"):
        group = [r for r in rows if r["arm"] == arm]
        summary[arm] = {
            "n": len(group),
            "deterministic": mean(r["assertion"]["score"] for r in group),
            "rubric": mean(r["rubric"]["score"] for r in group),
            "overall": mean(r["combined"] for r in group),
            "dual_passes": sum(r["dual_pass"] for r in group),
            "hard_constraint_passes": sum(r["details"]["hard_constraints_passed"] for r in group),
            "mean_latency_ms": mean(r["response"]["latencyMs"] for r in group),
            "mean_cost_usd": mean(r["response"]["cost"] for r in group),
        }
    result = {
        "date": "2026-10-06", "base_git_sha": "2e148974583e731bedd32e4896b282a94134aeff",
        "evidence_status": "first-case-progressive-stop-uncommitted-source-reviewed",
        "scope": "headless synthetic ordered JPEGs; other five cases not measured",
        "calltime_freeze": run.inventory(run.FREEZE), "rows": rows, "summary": summary,
        "ledger": run.ledger(), "accounted_usd": str(run.accounted()), "cap_usd": "3",
        "unknown_exposure_usd": "0", "paid_retries": 0,
        "decision": "retain economical Luna headless reference; do not adopt Mistral for this lane",
        "cache_limit": "Luna parity output fresh; 2887/2890 input tokens cached after native probe",
        "source_review": "docs/evals/story-229-source-review.json",
    }
    assert all(r["state"] == "settled" for r in run.ledger())
    assert len(run.ledger()) == 6 and run.accounted() < run.CAP
    if run.RESULT.exists():
        assert json.loads(run.RESULT.read_text()) == result, "Immutable result differs"
    else:
        run.dump(run.RESULT, result)
    print(json.dumps(summary, indent=2))
    print("Settled all-provider USD", run.accounted())


if __name__ == "__main__":
    main()
