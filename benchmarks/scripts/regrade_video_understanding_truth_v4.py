#!/usr/bin/env python3
"""Combine saved subjects, v4 structural scores, and bounded revised rubrics."""

from __future__ import annotations

import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[2]
BENCHMARKS = ROOT / "benchmarks"
sys.path[:0] = [str(BENCHMARKS / "scorers"), str(BENCHMARKS / "scripts")]
import rejudge_video_understanding_truth_v4 as judge  # noqa: E402
import video_understanding_scorer as scorer  # noqa: E402

OUT = BENCHMARKS / "results/video-understanding-truth-v4-saved-subject-regrade-20260926.json"


def _file(path: Path) -> dict:
    data = path.read_bytes()
    return {
        "path": str(path.relative_to(ROOT)),
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def main() -> None:
    judge._check_freeze()
    saved = judge._saved_rows()
    overlay = json.loads((BENCHMARKS / "video_understanding_truth_v4/manifest.json").read_text())
    changed = set(judge.CASES)
    entries: dict[str, list[dict]] = {"luna": [], "gemini": []}
    extra_judge_cost = Decimal(0)
    for case_info in overlay["cases"]:
        case = case_info["clip_id"]
        target_path = BENCHMARKS / "video_understanding_truth_v4" / case / "target.json"
        for arm in entries:
            row = saved[(arm, case)]
            output = row["response"]["output"]
            structural = scorer.score_output_against_target(
                output=output,
                target_path=target_path,
                model_label=arm,
                prompt_version="video-understanding-frame-packet-v3",
                expected_clip_id=row["vars"]["evaluation_id"],
            )
            structural_assertion = scorer.get_assert(
                output,
                {
                    "vars": {
                        "target_path": str(target_path),
                        "evaluation_id": row["vars"]["evaluation_id"],
                    }
                },
            )
            if case in changed:
                raw_path = judge.OUT / f"{case}-{arm}-raw.json"
                parsed = judge._parse_judge(json.loads(raw_path.read_text()))
                rubric = parsed["score"]
                rubric_pass = parsed["pass"]
                judge_receipt = _file(raw_path)
                judge_receipt.update({"kind": "v4_rejudged", **parsed})
                extra_judge_cost += Decimal(parsed["cost_estimated_usd"])
            else:
                component = row["gradingResult"]["componentResults"][1]
                rubric = component["score"]
                rubric_pass = component["pass"]
                old_usage = component["tokensUsed"]
                judge_receipt = {
                    "kind": "retained_v3_unchanged_reference",
                    "source_result": _file(judge.RESULTS[arm]),
                    "usage": old_usage,
                }
            combined = round((structural_assertion["score"] + rubric) / 2, 5)
            entries[arm].append(
                {
                    "case": case,
                    "evaluation_id": row["vars"]["evaluation_id"],
                    "source_response_id": row["response"]["metadata"]["request_id"],
                    "returned_model": row["response"]["metadata"]["returned_model"],
                    "source_output_sha256": hashlib.sha256(output.encode()).hexdigest(),
                    "target": _file(target_path),
                    "target_md_sha256": case_info["target_md_sha256"],
                    "frame_sha256": case_info["sampled_frame_sha256"],
                    "structural_raw": structural.overall_score,
                    "structural_effective": structural_assertion["score"],
                    "structural_pass": structural_assertion["pass"],
                    "hard_constraints_passed": structural.hard_constraints_passed,
                    "dimensions": {x.dimension: x.score for x in structural.dimensions},
                    "rubric_score": rubric,
                    "rubric_pass": rubric_pass,
                    "rubric_receipt": judge_receipt,
                    "combined": combined,
                    "case_pass": bool(structural_assertion["pass"] and rubric_pass),
                    "latency_ms_subject": row["latencyMs"],
                    "cost_usd_subject": str(Decimal(str(row["cost"]))),
                }
            )
    summary = {}
    for arm, rows in entries.items():
        summary[arm] = {
            "structural_mean": round(mean(x["structural_effective"] for x in rows), 4),
            "rubric_mean": round(mean(x["rubric_score"] for x in rows), 4),
            "combined_mean": round(mean(x["combined"] for x in rows), 4),
            "case_passes": sum(x["case_pass"] for x in rows),
            "case_count": len(rows),
            "latency_ms_mean_subject": round(mean(x["latency_ms_subject"] for x in rows)),
            "cost_usd_mean_subject": str(
                sum((Decimal(x["cost_usd_subject"]) for x in rows), Decimal(0)) / len(rows)
            ),
        }
    verdict = {
        "schema_version": 1,
        "kind": "saved_subject_derived_v4_score_not_new_subject_call",
        "date": "2026-09-26",
        "freeze": _file(ROOT / "docs/evals/story-222-truth-v4-freeze.json"),
        "source_results": [_file(path) for path in judge.RESULTS.values()],
        "target_overlay": _file(BENCHMARKS / "video_understanding_truth_v4/manifest.json"),
        "method": (
            "Same 12 saved subject outputs and JPEG bytes. Current v4 deterministic scorer "
            "on all six; pinned Opus 4.6 rejudge only dialogue, bedside, rooftop for both arms; "
            "reuse original judge scores for three byte-identical references. No subject calls."
        ),
        "judge_cost_incremental_estimated_usd": str(extra_judge_cost),
        "campaign_accounted_usd": str(judge.PRIOR_SPEND_USD + extra_judge_cost),
        "summary": summary,
        "case_rows": entries,
        "recommendation": (
            "Luna preferred headless ordered-frame reference; "
            "hold autonomous QA/default gate"
        ),
        "limits": [
            "Six abstract synthetic cases; no product ordered-frame inference call exists.",
            "Rooftop and dialogue source-backed corrections are explicit; "
            "bedside objects and tone remain interpretive.",
            "Revised Opus rubric still penalizes some plausible bedside readings; "
            "numerical scores are bounded, not fully truth-clean.",
        ],
    }
    if OUT.exists():
        raise SystemExit(f"Refusing to overwrite derived score: {OUT}")
    OUT.write_text(json.dumps(verdict, indent=2, ensure_ascii=False) + "\n")
    print(OUT)
    print(json.dumps(summary, indent=2))
    print("incremental_judge_usd", extra_judge_cost)


if __name__ == "__main__":
    main()
