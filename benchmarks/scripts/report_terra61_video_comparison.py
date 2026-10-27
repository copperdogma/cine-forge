#!/usr/bin/env python3
"""Offline replay of retained Scout103 evidence; never dispatch provider calls."""

import argparse
import base64
import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "benchmarks/scorers"))
from video_understanding_scorer import get_assert  # noqa: E402

EVIDENCE = ROOT / "docs/evals/evidence/story-226-terra6120261026"
RESULT = ROOT / "benchmarks/results/video-understanding-terra61-vs-sol-luna-v4-20261026-v2.json"
FREEZE = ROOT / "docs/evals/story-226-terra6120261026-terra61-freeze.json"
MANIFEST = ROOT / "docs/evals/story-226-terra6120261026-evidence.json"
ARMS = ("terra61", "sol", "luna")
CASES = ("vfp_active_001", "vfp_active_004", "vfp_active_006")


def read(path):
    return json.loads(path.read_text())


def assemble():
    rows = []
    for case in CASES:
        for arm in ARMS:
            receipt = read(EVIDENCE / f"subject-{arm}-{case}.json")
            judge = read(EVIDENCE / f"judge-opus-{arm}-{case}.json")
            response = receipt["response"]
            assertion = get_assert(response["output"], {"vars": receipt["vars"]})
            combined = (assertion["score"] + judge["score"]) / 2
            rows.append({
                "arm": arm, "case": case, "deterministic": assertion,
                "rubric": judge["score"], "combined": combined,
                "quality_pass": bool(assertion["pass"] and judge["score"] >= .8
                                     and combined >= .8),
                "latency_ms": response["latencyMs"], "cost_usd": response["cost"],
                "continuity_status": json.loads(response["output"])["continuity_status"],
                "supplementary_post_stop": case == "vfp_active_006",
                "reasoning_tokens": response["tokenUsage"]["completionDetails"]["reasoning"],
            })
    summary = {}
    for arm in ARMS:
        primary = [r for r in rows if r["arm"] == arm and not r["supplementary_post_stop"]]
        summary[arm] = {
            "decision_bearing_cases": 2,
            "deterministic_mean": mean(r["deterministic"]["score"] for r in primary),
            "rubric_mean": mean(r["rubric"] for r in primary),
            "combined_mean": mean(r["combined"] for r in primary),
            "quality_passes": sum(r["quality_pass"] for r in primary),
            "mean_latency_ms": mean(r["latency_ms"] for r in primary),
            "mean_cost_usd": mean(r["cost_usd"] for r in primary),
            "subject_total_usd": sum(r["cost_usd"] for r in primary),
        }
    ledger = read(EVIDENCE / "ledger.json")
    assert all(r["state"] == "settled" for r in ledger)
    total = sum(Decimal(str(r["accounted_usd"])) for r in ledger)
    assert total <= 5
    supplementary = sum(Decimal(str(r["accounted_usd"])) for r in ledger
                        if "vfp_active_006" in r["name"])
    return {
        "date": "2026-10-26",
        "base_git_sha": "6e6783e47eec4d053452c83606e18dc6e96df312",
        "candidate": "gpt-6.1-terra", "route": "direct OpenAI Responses Standard",
        "candidate_effort": "high", "candidate_max_output_tokens": 32768,
        "rows": rows, "summary": summary, "ledger": ledger,
        "conservative_usage_estimated_spend_usd": str(total),
        "supplementary_post_stop_spend_usd": str(supplementary),
        "unknown_exposure_usd": "0", "cap_usd": "5",
        "verdict": "Retain references; reject tested Terra high32768 direct replacement. "
                   "All arms miss declared prop continuity label; no quality winner.",
        "protocol_deviation": "Producing runner automatically advanced subjects/judges to "
                              "tunnel before prop source adjudication. Preserve tunnel as "
                              "supplementary post-stop evidence, not qualification or rescue. "
                              "Final runner requires explicit per-case admission and selection.",
        "limits": "Two exposed decision-bearing cases; no independent or six-case promotion. "
                  "Tone/color/motion/lexical rubric limits remain. Correct color-change "
                  "recognition does not waive broken-label contract. Costs are token-price "
                  "usage estimates with all cache-read/write counts known, "
                  "not provider invoices. Metadata-only v2 corrects the earlier generic "
                  "missing-write "
                  "description; original v1 and all outputs/scores remain retained. "
                  "Other efforts unmeasured; no within-task effort comparison.",
    }


def verify():
    assert read(RESULT) == assemble()
    for entry in read(MANIFEST)["files"]:
        data = (ROOT / entry["path"]).read_bytes()
        assert len(data) == entry["bytes"]
        assert hashlib.sha256(data).hexdigest() == entry["sha256"], entry["path"]
    freeze = read(FREEZE)
    archived = ROOT / "docs/evals/snapshots/story-226-terra6120261026"
    for entry in freeze["files"]:
        snapshot = archived / (Path(entry["path"]).name + ".txt")
        path = snapshot if snapshot.exists() else ROOT / entry["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == entry["sha256"]
    for arm in ARMS:
        assert read(EVIDENCE / f"native-{arm}-vfp_active_001-request.json") == read(
            EVIDENCE / f"subject-{arm}-vfp_active_001-request.json")
        for case in CASES:
            payload = read(EVIDENCE / f"subject-{arm}-{case}-request.json")["payload"]
            assert payload["store"] is False and payload["service_tier"] == "default"
            assert payload["text"]["format"]["strict"] is True
            images = [c for c in payload["input"][0]["content"] if c["type"] == "input_image"]
            hashes = [hashlib.sha256(base64.b64decode(c["image_url"].split(",", 1)[1])).hexdigest()
                      for c in images]
            expected = next(r for r in freeze["rendered_packets"]
                            if r["arm"] == arm and r["case"] == case)
            assert hashes == [f["sha256"] for f in expected["frames"]]
            if arm == "terra61":
                assert payload["model"] == "gpt-6.1-terra"
                assert payload["reasoning"] == {"effort": "high"}
                assert payload["max_output_tokens"] == 32768
    print("Verified scores, settled ledger, original images, call-time hashes and native/parity")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.verify:
        verify()
    else:
        assert not RESULT.exists(), "Immutable result already exists"
        RESULT.write_text(json.dumps(assemble(), indent=2, sort_keys=True) + "\n")
        print(json.dumps(read(RESULT)["summary"], indent=2))


if __name__ == "__main__":
    main()
