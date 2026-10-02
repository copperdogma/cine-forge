#!/usr/bin/env python3
"""Offline verification of retained Grok effort calibration and its source freeze."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "benchmarks/scorers"), str(ROOT / "src")]
from video_understanding_scorer import get_assert  # noqa: E402


def main() -> None:
    manifest = json.loads((ROOT / "docs/evals/story-227-evidence.json").read_text())
    for item in manifest["files"]:
        data = (ROOT / item["path"]).read_bytes()
        assert len(data) == item["bytes"]
        assert hashlib.sha256(data).hexdigest() == item["sha256"]
    for item in manifest["frozen_source_files"]:
        path = item["path"]
        if path == "benchmarks/scripts/run_grok47_effort.py":
            path = "docs/evals/snapshots/story-227-original-run_grok47_effort.py.txt"
        data = (ROOT / path).read_bytes()
        assert len(data) == item["bytes"]
        assert hashlib.sha256(data).hexdigest() == item["sha256"]
    result = json.loads((ROOT / manifest["result"]).read_text())
    rows = result["rows"]
    assert len(rows) == 9
    assert {r["arm"] for r in rows} == {"low", "medium", "high"}
    evidence = ROOT / "docs/evals/evidence/story-227"
    seen = set()
    for row in rows:
        name = row["name"]
        request = json.loads((evidence / f"{name}-request.json").read_text())["payload"]
        raw = json.loads((evidence / f"{name}-full-raw.json").read_text())
        assert raw["model"] == request["model"] == "grok-4.7"
        assert raw["status"] == "completed" and raw.get("incomplete_details") is None
        assert raw["id"] not in seen
        seen.add(raw["id"])
        assert request["store"] is False and request["max_output_tokens"] == 8192
        assert request["reasoning"]["effort"] == row["arm"]
        assert request["text"]["format"]["strict"] is True
        assert len(request["input"]) == 1
        content = request["input"][0]["content"]
        assert sum(x["type"] == "input_image" for x in content) == 5
        assert row["vars"]["clip_id"] not in content[0]["text"]
        usage = raw["usage"]
        assert usage["total_tokens"] == usage["input_tokens"] + usage["output_tokens"]
        assert usage["output_tokens_details"]["reasoning_tokens"] <= usage["output_tokens"]
        assert row["response"]["cost"] == usage["cost_in_usd_ticks"] / 10_000_000_000
        actual = get_assert(row["response"]["output"], {"vars": row["vars"]})
        assert actual == row["assertion"]
    for case in {r["vars"]["evaluation_id"] for r in rows}:
        bodies = []
        for arm in ("low", "medium", "high"):
            request = json.loads((evidence / f"subject-{arm}-{case}-request.json").read_text())[
                "payload"
            ]
            request.pop("reasoning")
            bodies.append(request)
        assert bodies[0] == bodies[1] == bodies[2]
    assert all(r["state"] == "settled" for r in result["ledger"])
    print(
        "Verified 9 exact native strict subjects, unique IDs, 5-image parity across efforts, usage, scores and all retained hashes; no provider calls"  # noqa: E501
    )


if __name__ == "__main__":
    main()
