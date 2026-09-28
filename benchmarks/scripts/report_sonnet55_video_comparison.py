#!/usr/bin/env python3
"""Offline symmetric regrade, including unchanged invalid strict outputs."""

from __future__ import annotations

import argparse
import json
from statistics import mean

import run_sonnet55_video_comparison as run


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--original", action="store_true")
    args = parser.parse_args()
    _, _, _, tests = run.matrix()
    rows = []
    for test in tests:
        for arm in ("sonnet", "luna"):
            row = json.loads(
                (run.OUT / f"subject-{arm}-{test['vars']['evaluation_id']}.json").read_text()
            )
            effective = run.scorer.get_assert(row["response"]["output"], {"vars": row["vars"]})
            try:
                structural = run.scorer.score_output_against_target(
                    output=row["response"]["output"],
                    target_path=run.ROOT
                    / "benchmarks/video_understanding_truth_v4"
                    / row["vars"]["clip_id"]
                    / "target.json",
                    model_label=arm,
                    prompt_version="video-understanding-frame-packet-v3",
                    expected_clip_id=row["vars"]["evaluation_id"],
                ).model_dump()
                strict_error = None
            except ValueError as exc:
                structural = None
                strict_error = str(exc)
            opus = json.loads(
                (run.OUT / f"judge-opus-{arm}-{test['vars']['evaluation_id']}.json").read_text()
            )
            sol = json.loads(
                (run.OUT / f"judge-sol-{arm}-{test['vars']['evaluation_id']}.json").read_text()
            )
            audit = run.OUT / f"judge-opus-{arm}-source-audit-{test['vars']['evaluation_id']}.json"
            corrected_opus = (
                json.loads(audit.read_text()) if audit.exists() and not args.original else opus
            )
            rows.append(
                {
                    **row,
                    "structural": structural,
                    "strict_error": strict_error,
                    "structural_effective": effective["score"],
                    "structural_reason": effective["reason"],
                    "original_opus": opus,
                    "opus": corrected_opus,
                    "sol": sol,
                    "combined_opus": (effective["score"] + corrected_opus["score"]) / 2,
                    "combined_sol": (effective["score"] + sol["score"]) / 2,
                    "dual_assertion_pass": bool(
                        effective["pass"] and corrected_opus["score"] >= 0.8
                    ),
                    "overall_gate_pass": bool(
                        effective["pass"]
                        and corrected_opus["score"] >= 0.8
                        and (effective["score"] + corrected_opus["score"]) / 2 >= 0.8
                    ),
                }
            )
    summaries = {}
    for arm in ("sonnet", "luna"):
        selected = [r for r in rows if r["arm"] == arm]
        summaries[arm] = {
            k: mean(r[k] for r in selected)
            for k in ["structural_effective", "combined_opus", "combined_sol"]
        }
        summaries[arm].update(
            opus_mean=mean(r["opus"]["score"] for r in selected),
            sol_mean=mean(r["sol"]["score"] for r in selected),
            mean_latency_ms=mean(r["response"]["latencyMs"] for r in selected),
            max_latency_ms=max(r["response"]["latencyMs"] for r in selected),
            mean_cost_usd=mean(r["response"]["cost"] for r in selected),
            max_cost_usd=max(r["response"]["cost"] for r in selected),
            strict_contract_passes=sum(r["strict_error"] is None for r in selected),
            hard_gate_passes=sum(
                bool(r["structural"] and r["structural"]["hard_constraints_passed"])
                for r in selected
            ),
            case_passes=sum(r["overall_gate_pass"] for r in selected),
        )
    out = (
        run.ROOT
        / "benchmarks/results"
        / (
            "video-understanding-sonnet55-vs-luna-v4-original-20260928.json"
            if args.original
            else "video-understanding-sonnet55-vs-luna-v4-20260928.json"
        )
    )
    run.dump(
        out,
        {
            "base_git_sha": "a3ac35743c94e253e0406fafe6ee4964a0330bf3",
            "evidence_status": "bounded-six-case-uncommitted",
            "calltime_freeze": run.inventory(run.FREEZE),
            "rows": rows,
            "summary": summaries,
            "ledger": run.ledger(),
            "accounted_usd": str(run.accounted()),
            "cap_usd": "3",
            "scorer_identity": run.inventory(
                run.ROOT / "benchmarks/scorers/video_understanding_scorer.py"
            ),
            "dimensions_identity": run.inventory(
                run.ROOT / "benchmarks/scorers/video_understanding_dimensions.py"
            ),
            "report_identity": run.inventory(__import__("pathlib").Path(__file__)),
        },
    )
    print(json.dumps(summaries, indent=2))
    print("accounted_usd", run.accounted())


if __name__ == "__main__":
    main()
