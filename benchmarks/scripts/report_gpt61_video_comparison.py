#!/usr/bin/env python3
"""Offline report over immutable fresh subjects and source-reviewed rubric receipts."""

from __future__ import annotations

import json
from pathlib import Path
from statistics import mean

import run_gpt61_video_comparison as run
from video_understanding_scorer import get_assert, score_output_against_target

ROOT = run.ROOT


def main() -> None:
    run.check_freeze()
    _, _, _, tests = run.matrix()
    source_review = ROOT / "docs/evals/story-226-source-review.json"
    rows = []
    for test in tests:
        case_id = test["vars"]["evaluation_id"]
        for arm in ("sol", "luna"):
            row = json.loads((run.OUT / f"subject-{arm}-{case_id}.json").read_text())
            output = row["response"]["output"]
            structural = score_output_against_target(
                output=output,
                target_path=ROOT / "benchmarks/video_understanding_truth_v4"
                / test["vars"]["clip_id"] / "target.json",
                model_label=arm,
                prompt_version="video-understanding-frame-packet-v3",
                expected_clip_id=case_id,
            ).model_dump()
            assertion = get_assert(output, {"vars": test["vars"]})
            original_opus = json.loads(
                (run.OUT / f"judge-opus-{arm}-{case_id}.json").read_text()
            )
            repaired_path = run.OUT / f"judge-opus-{arm}-source-audit-{case_id}.json"
            repaired_opus = (
                json.loads(repaired_path.read_text()) if repaired_path.exists() else None
            )
            adjudication_path = run.OUT / f"judge-sonnet-source-adjudication-{arm}-{case_id}.json"
            adjudicator = (
                json.loads(adjudication_path.read_text())
                if adjudication_path.exists() else None
            )
            if case_id == "vfp_active_004":
                assert adjudicator is not None and repaired_opus is not None
                rubric = adjudicator
                rubric_basis = (
                    "source-first-sonnet-adjudication; original-and-repaired-opus-invalid"
                )
            else:
                rubric = original_opus
                rubric_basis = "original-cross-provider-opus"
            combined = (assertion["score"] + rubric["score"]) / 2
            rows.append({
                **row,
                "structural": structural,
                "structural_effective": assertion["score"],
                "structural_reason": assertion["reason"],
                "original_opus": original_opus,
                "repaired_opus": repaired_opus,
                "adjudicator": adjudicator,
                "effective_rubric": rubric,
                "rubric_basis": rubric_basis,
                "combined_adjudicated": combined,
                "quality_case_pass": bool(
                    assertion["pass"] and rubric["score"] >= 0.8 and combined >= 0.8
                ),
                "latency_gate_pass": row["response"]["latencyMs"] <= 15000,
                "cost_gate_pass": row["response"]["cost"] <= .02,
            })
    summary = {}
    for arm in ("sol", "luna"):
        selected = [r for r in rows if r["arm"] == arm]
        summary[arm] = {
            "structural_mean": mean(r["structural_effective"] for r in selected),
            "rubric_mean": mean(r["effective_rubric"]["score"] for r in selected),
            "combined_mean": mean(r["combined_adjudicated"] for r in selected),
            "quality_case_passes": sum(r["quality_case_pass"] for r in selected),
            "hard_constraint_passes": sum(
                r["structural"]["hard_constraints_passed"] for r in selected
            ),
            "latency_gate_passes": sum(r["latency_gate_pass"] for r in selected),
            "cost_gate_passes": sum(r["cost_gate_pass"] for r in selected),
            "mean_latency_ms": mean(r["response"]["latencyMs"] for r in selected),
            "max_latency_ms": max(r["response"]["latencyMs"] for r in selected),
            "mean_cost_usd": mean(r["response"]["cost"] for r in selected),
            "max_cost_usd": max(r["response"]["cost"] for r in selected),
        }
    run.dump(run.RESULT, {
        "date": "2026-09-29",
        "base_git_sha": "58a001716c2f20a07e4aefcc99d280e5a0c8bb10",
        "evidence_status": "bounded-six-case-uncommitted-source-reviewed",
        "calltime_freeze": run.inventory(run.FREEZE),
        "source_review": run.inventory(source_review),
        "scorer_identity": run.inventory(ROOT / "benchmarks/scorers/video_understanding_scorer.py"),
        "dimensions_identity": run.inventory(
            ROOT / "benchmarks/scorers/video_understanding_dimensions.py"
        ),
        "report_identity": run.inventory(Path(__file__)),
        "rows": rows,
        "summary": summary,
        "ledger": run.ledger(),
        "settled_estimated_usd": str(run.accounted()),
        "unresolved_exposure_usd": str(sum(
            (run.Decimal(str(r["accounted_usd"])) for r in run.ledger() if r["state"] != "settled"),
            run.Decimal(0),
        )),
        "cap_usd": "4",
    })
    print(json.dumps(summary, indent=2))
    print("settled_estimated_usd", run.accounted())


if __name__ == "__main__":
    main()
