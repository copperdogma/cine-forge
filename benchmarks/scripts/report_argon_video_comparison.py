#!/usr/bin/env python3
"""Offline result and replay validation for the frozen Argon three-case screen."""

from __future__ import annotations

import argparse
import hashlib
import json
from decimal import Decimal
from statistics import mean

import run_argon_video_comparison as run
from video_understanding_scorer import get_assert, score_output_against_target


def assemble():
    run.check_freeze()
    _, _, _, tests = run.matrix()
    rows = []
    for test in tests:
        case = test["vars"]["evaluation_id"]
        for arm in ("argon", "sol", "luna"):
            receipt = json.loads((run.EVIDENCE / f"subject-{arm}-{case}.json").read_text())
            original_judge = json.loads(
                (run.EVIDENCE / f"judge-opus-{arm}-{case}.json").read_text()
            )  # noqa: E501
            repaired = run.EVIDENCE / f"repair-opus-{arm}-{case}.json"
            judge = json.loads(repaired.read_text()) if repaired.exists() else original_judge
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
                    "original_combined": (assertion["score"] + original_judge["score"]) / 2,
                    "combined": (assertion["score"] + judge["score"]) / 2,
                    "dual_pass": assertion["pass"] and judge["score"] >= 0.8,
                    "latency_gate_pass": receipt["response"]["latencyMs"] <= 15000,
                    "cost_gate_pass": receipt["response"]["cost"] <= 0.02,
                }
            )
    summary = {}
    for arm in ("argon", "sol", "luna"):
        group = [r for r in rows if r["arm"] == arm]
        summary[arm] = {
            "n": len(group),
            "deterministic": mean(r["assertion"]["score"] for r in group),
            "rubric": mean(r["original_rubric"]["score"] for r in group),
            "source_adjudicated_rubric": mean(r["rubric"]["score"] for r in group),
            "overall": mean(r["original_combined"] for r in group),
            "source_adjudicated_overall": mean(r["combined"] for r in group),
            "original_overall": mean(r["original_combined"] for r in group),
            "original_rubric": mean(r["original_rubric"]["score"] for r in group),
            "dual_passes": sum(
                r["assertion"]["pass"] and r["original_rubric"]["score"] >= 0.8 for r in group
            ),
            "source_adjudicated_dual_passes": sum(r["dual_pass"] for r in group),
            "hard_constraint_passes": sum(r["details"]["hard_constraints_passed"] for r in group),
            "latency_passes": sum(r["latency_gate_pass"] for r in group),
            "cost_passes": sum(r["cost_gate_pass"] for r in group),
            "mean_latency_ms": mean(r["response"]["latencyMs"] for r in group),
            "mean_cost_usd": mean(r["response"]["cost"] for r in group),
        }
    # Tracked custody is authoritative; replay must work without ignored output/.
    ledger = json.loads((run.EVIDENCE / "ledger.json").read_text())
    assert len(ledger) == 24 and all(r["state"] == "settled" for r in ledger)
    total = sum((Decimal(r["accounted_usd"]) for r in ledger), Decimal(0))
    assert total < run.CAP
    split = {
        group: str(
            sum(
                (Decimal(r["accounted_usd"]) for r in ledger if r["name"].startswith(prefix)),
                Decimal(0),
            )
        )
        for group, prefix in [
            ("qualification", "native-"),
            ("subjects", "subject-"),
            ("judges", "judge-"),
            ("judge_repairs", "repair-"),
        ]
    }
    split["candidate_total"] = str(
        sum((Decimal(r["accounted_usd"]) for r in ledger if r["arm"] == "argon"), Decimal(0))
    )
    split["controls_total"] = str(
        sum(
            (Decimal(r["accounted_usd"]) for r in ledger if r["arm"] in {"sol", "luna"}), Decimal(0)
        )
    )
    return {
        "date": "2026-10-13",
        "base_git_sha": "1a38bbae97382abdffe99b2abe959154b02dace6",
        "evidence_status": "bounded-three-case-uncommitted-source-reviewed",
        "scope": "maintained v4 three-case synthetic five-JPEG screen; no six-case promotion",
        "rows": rows,
        "summary": summary,
        "ledger": ledger,
        "spend_split": split,
        "settled_estimated_usd": str(total),
        "cap_usd": "5",
        "unknown_exposure_usd": "0",
        "subject_retries": 0,
        "judge_repairs": 3,
        "source_review": "docs/evals/story-226-argon20261013-source-review.json",
        "known_score_validity_limit": "Preserved dialogue summary mechanism false-credit; no score promotion",  # noqa: E501
        "decision": "Do not adopt Argon medium for ordered-frame lane; retain references. "
        "No full-six qualification, no product/default decision.",
        "repair_latency_limit": "First repairedArgon rawresponse reused after local Decimal parsing fault; receipt1ms is parse time, provider latencyunknown. Other repairedreviews retain measuredlatency.",  # noqa: E501
        "economics_limit": "Token-price estimates, billed dollars unavailable. Natural implicit "
        "caches reported separately; launch Google rates double December1.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    result = assemble()
    if args.verify:
        assert json.loads(run.RESULT.read_text()) == result
        manifest = json.loads(
            (run.ROOT / "docs/evals/story-226-argon20261013-evidence-v2.json").read_text()
        )  # noqa: E501
        for entry in manifest["files"]:
            data = (run.ROOT / entry["path"]).read_bytes()
            assert len(data) == entry["bytes"]
            assert hashlib.sha256(data).hexdigest() == entry["sha256"]
        for arm in ("argon", "sol", "luna"):
            native = run.EVIDENCE / f"native-{arm}-vfp_active_001-request.json"
            parity = run.EVIDENCE / f"subject-{arm}-vfp_active_001-request.json"
            assert json.loads(native.read_text()) == json.loads(parity.read_text())
        print("PASS: all retained hashes,9 reconstructed scores,24settledcalls, native/parity")
    else:
        if run.RESULT.exists():
            assert json.loads(run.RESULT.read_text()) == result, "Immutable result changed"
        else:
            run.dump(run.RESULT, result)
        print(json.dumps(result["summary"], indent=2))
        print(result["settled_estimated_usd"], result["spend_split"])


if __name__ == "__main__":
    main()
