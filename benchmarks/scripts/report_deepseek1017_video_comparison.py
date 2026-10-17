#!/usr/bin/env python3
"""Offline evidence reconstruction for Scout096's source-stopped ordered-frame screen."""

# ruff: noqa: E501

from __future__ import annotations

import argparse
import json
from decimal import Decimal
from statistics import mean

import run_deepseek1017_video_comparison as run
from video_understanding_scorer import get_assert, score_output_against_target

RESULT = (
    run.ROOT / "benchmarks/results/video-understanding-deepseek1017-vs-sol-luna-v4-20261017-v2.json"
)
MANIFEST = run.ROOT / "docs/evals/story-226-deepseek101720261017-evidence.json"


def assemble():
    run.check_freeze()
    _, _, _, tests = run.matrix()
    rows = []
    for test in tests:
        case = test["vars"]["evaluation_id"]
        for arm in ("deepseek1017", "sol", "luna"):
            receipt_path = run.EVIDENCE / f"subject-{arm}-{case}.json"
            if not receipt_path.exists():
                assert arm == "deepseek1017" and case != "vfp_active_001"
                continue
            receipt = json.loads(receipt_path.read_text())
            judge = json.loads((run.EVIDENCE / f"judge-opus-{arm}-{case}.json").read_text())
            original_judge = dict(judge)
            repaired_path = run.EVIDENCE / f"repair-opus-{arm}-{case}.json"
            if repaired_path.exists():
                judge = json.loads(repaired_path.read_text())
            assertion = get_assert(receipt["response"]["output"], {"vars": test["vars"]})
            detail = score_output_against_target(
                output=receipt["response"]["output"],
                target_path=run.ROOT / "benchmarks" / test["vars"]["target_path"],
                model_label=arm,
                prompt_version="video-understanding-frame-packet-v3",
                expected_clip_id=case,
            ).model_dump()
            rows.append(
                {
                    **receipt,
                    "assertion": assertion,
                    "details": detail,
                    "rubric": judge,
                    "original_rubric": original_judge,
                    "combined": (assertion["score"] + judge["score"]) / 2,
                    "dual_pass": assertion["pass"] and judge["score"] >= 0.8,
                    "latency_gate_pass": receipt["response"]["latencyMs"] <= 15000,
                    "qualification": "diagnostic-accounting-quarantine"
                    if arm == "deepseek1017"
                    else "qualified-native-control",
                    "adoption_grade": arm != "deepseek1017",
                    "cost_gate_pass": receipt["response"]["cost"] <= 0.02,
                }
            )
    summary = {}
    for arm in ("deepseek1017", "sol", "luna"):
        group = [r for r in rows if r["arm"] == arm]
        summary[arm] = {
            "n": len(group),
            "deterministic": mean(r["assertion"]["score"] for r in group),
            "rubric": mean(r["rubric"]["score"] for r in group),
            "overall": mean(r["combined"] for r in group),
            "dual_passes": sum(r["dual_pass"] for r in group),
            "mean_latency_ms": mean(r["response"]["latencyMs"] for r in group),
            "mean_cost_usd": mean(r["response"]["cost"] for r in group),
        }
    ledger = json.loads((run.EVIDENCE / "ledger.json").read_text())
    assert len(ledger) >= 17 and all(r["state"] == "settled" for r in ledger)
    total = sum((Decimal(r["accounted_usd"]) for r in ledger), Decimal(0))
    assert total <= run.CAP
    split = {
        kind: str(
            sum(
                (Decimal(r["accounted_usd"]) for r in ledger if r["name"].startswith(prefix)),
                Decimal(0),
            )
        )
        for kind, prefix in [
            ("qualification", "native-"),
            ("subjects", "subject-"),
            ("judges", "judge-"),
            ("judge_repairs", "repair-"),
        ]
    }
    matched = [
        {k: r[k] for k in ("arm", "combined", "assertion", "rubric")}
        for r in rows
        if r["vars"]["evaluation_id"] == "vfp_active_001"
    ]
    return {
        "date": "2026-10-17",
        "base_git_sha": "9467abc51a6ea2bebf0867fe633691c5a13c7406",
        "evidence_status": "candidate-accounting-quarantined-diagnostic-only-controls-three-case-source-reviewed",
        "scope": "Candidate1/3 and fresh controls3/3; five authored synthetic JPEGs each; no six-case promotion",
        "rows": rows,
        "summary": summary,
        "matched_first_case": matched,
        "ledger": ledger,
        "spend_split": split,
        "settled_usd_mixed_reported_and_estimated": str(total),
        "unknown_exposure_usd": "0",
        "candidate_accounting": {
            "qualified": False,
            "native_completion_minus_reasoning": 55,
            "scored_completion_minus_reasoning": 14,
            "generation_normalized_completion": [2933, 2310],
            "billing": "reported router cost matches generation total_cost; token decomposition not repaired",
            "official_source": "https://openrouter.ai/docs/guides/best-practices/reasoning-tokens",
        },
        "cap_usd": "4",
        "subject_retries": 0,
        "judge_repairs": sum(x["name"].startswith("repair-") for x in ledger),
        "decision": "Defer DeepSeek1017 adoption: native usage accounting unqualified. Saved-answer diagnostic contradicts visible growth and exceeds latency gate; retain Sol quality/Luna economical research references, no autonomous QA.",
        "limits": "Maintained lexical/scorer and subjective rubric limits prevent quality-rank promotion. n1 candidate vs n3 controls; compare first case only. Cloudflare precision unknown; canonical1017 catalog mapping with no immutable backend attestation; high accepted and reasoning observed. Other effort levels and remaining candidate cases unmeasured.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    result = assemble()
    if args.verify:
        assert json.loads(RESULT.read_text()) == result
        for item in json.loads(MANIFEST.read_text())["files"]:
            actual = run.inventory(run.ROOT / item["path"])
            assert actual == item, item["path"]
        for arm in ("deepseek1017", "sol", "luna"):
            assert json.loads(
                (run.EVIDENCE / f"native-{arm}-vfp_active_001-request.json").read_text()
            ) == json.loads(
                (run.EVIDENCE / f"subject-{arm}-vfp_active_001-request.json").read_text()
            )
        print("PASS:7 reconstructed scores,settled calls,hashes,native/parity; network not used")
    else:
        if RESULT.exists():
            assert json.loads(RESULT.read_text()) == result
        else:
            run.dump(RESULT, result)
        print(json.dumps(result["summary"], indent=2))
        print(result["settled_usd_mixed_reported_and_estimated"], result["spend_split"])


if __name__ == "__main__":
    main()
