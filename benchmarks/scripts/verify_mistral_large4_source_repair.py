#!/usr/bin/env python3
"""Verify original and source-repaired evaluation phases without provider calls."""
from __future__ import annotations

import hashlib
import json
from decimal import Decimal

import run_mistral_large4_video_comparison as run
import verify_mistral_large4_video_comparison as original
from finalize_mistral_large4_source_repair import FINAL


def main():
    original.main()
    manifest = json.loads(
        (run.ROOT / "docs/evals/story-229-mistral-large4-evidence-v2.json").read_text()
    )
    for item in manifest["retained_files"]:
        data = (run.ROOT / item["path"]).read_bytes()
        assert len(data) == item["bytes"]
        assert hashlib.sha256(data).hexdigest() == item["sha256"], item["path"]
    result = json.loads(FINAL.read_text())
    phase1 = json.loads(run.RESULT.read_text())
    for row in result["rows"]:
        arm = row["arm"]
        old = next(r for r in phase1["rows"] if r["arm"] == arm)
        assert row["response"] == old["response"]
        assert row["assertion"] == old["assertion"]
        assert row["original_rubric"] == old["rubric"]
        assert row["combined"] == (row["assertion"]["score"] + row["rubric"]["score"]) / 2
        old_request = json.loads(
            (run.EVIDENCE / f"judge-opus-{arm}-vfp_active_001-request.json").read_text()
        )
        repair_path = run.EVIDENCE / f"judge-opus-{arm}-source-repair-vfp_active_001-request.json"
        new_request = json.loads(repair_path.read_text())
        new_user = new_request["payload"]["messages"][0]["content"]
        assert new_user.startswith(old_request["payload"]["messages"][0]["content"])
        new_request["payload"]["messages"] = old_request["payload"]["messages"]
        assert new_request == old_request, "Repair changed more than source clarification"
        raw = json.loads(
            (run.EVIDENCE / f"judge-opus-{arm}-source-repair-vfp_active_001-raw.json").read_text()
        )
        assert raw["model"] == "claude-opus-4-6" and raw["stop_reason"] == "end_turn"
        assert raw["id"] == row["rubric"]["request_id"]
        cost = (Decimal(raw["usage"]["input_tokens"]) * 5
                + Decimal(raw["usage"]["output_tokens"]) * 25) / 1000000
        assert cost == Decimal(row["rubric"]["cost_usd"])
    assert len(result["ledger"]) == 8 and all(r["state"] == "settled" for r in result["ledger"])
    total = sum((Decimal(r["accounted_usd"]) for r in result["ledger"]), Decimal(0))
    assert total == Decimal(result["accounted_usd"]) == Decimal(manifest["accounted_usd"])
    assert total < Decimal(3) and result["unknown_exposure_usd"] == "0"
    assert result["subject_retries"] == 0 and result["judge_repairs"] == 2
    print(f"Story229 repaired phase PASS: {len(manifest['retained_files'])} retained hashes, "
          "unchanged subjects/scorer, two symmetric saved-answer repairs, eight settled calls")


if __name__ == "__main__":
    main()
