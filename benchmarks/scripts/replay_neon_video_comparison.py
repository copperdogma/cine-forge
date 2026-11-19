#!/usr/bin/env python3
"""Verify Scout 119 from tracked synthetic receipts with the network denied."""

from __future__ import annotations

import hashlib
import json
import socket
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import run_neon_video_comparison as run

EVIDENCE = run.ROOT / "docs/evals/evidence/story-236-neon-20261118"
RESULT = run.ROOT / "benchmarks/results/video-understanding-neon-sol61-luna-v4-20261118.json"
MANIFEST = run.ROOT / "docs/evals/story-236-neon-20261118-manifest.json"


def serialized(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def digest(value):
    return hashlib.sha256(serialized(value)).hexdigest()


def verify_inventory(rows):
    for row in rows:
        assert run.inventory(run.ROOT / row["path"]) == row, row["path"]


def deny_network(*_args, **_kwargs):
    raise AssertionError("Unexpected network call from offline replay")


def replay(run_dir, arm, recorded, frozen, saved, test, prompt, configs):
    row = run.provider._prepare_subject_request(
        prompt, {"config": configs[arm]}, {"vars": test["vars"]}
    )
    assert [run.inventory(frame["path"]) for frame in row["packet"]["frames"]] == frozen["frames"]

    def fixture_http(url, **kwargs):
        assert digest({"url": url, "payload": kwargs["body"]}) == frozen["wire"]["sha256"]
        return saved["subject"]

    replay_config = dict(configs[arm], raw_output_dir=str(run_dir.relative_to(run.ROOT)))
    with patch.object(run.provider, "_request_json", fixture_http):
        response = run.provider.call_api(prompt, {"config": replay_config}, {"vars": test["vars"]})
    assert not response.get("error"), response.get("error")
    assert response["metadata"]["returned_model"] == recorded["requested_and_returned_model"]
    assert json.loads(response["output"]) == recorded["output"]
    assert response["tokenUsage"] == recorded["usage"]
    assert Decimal(str(response["cost"])) == Decimal(recorded["cost"])

    scored = run.get_assert(response["output"], {"vars": test["vars"]})
    assert scored["score"] == recorded["structural"] and scored["reason"] == recorded["score_notes"]
    body, url, _ = run.judge_packet({"response": response, "vars": test["vars"]})
    wire = {"url": url, "payload": body, "count": saved["judge_input_count"]}
    assert digest(wire) == saved["protected_judge_request_sha256"]

    judge = saved["judge"]
    assert judge["model"] == run.MODELS["opus"] and judge["stop_reason"] == "end_turn"
    review = json.loads(judge["text"])
    assert review["score"] == recorded["rubric"] and review["reason"] == recorded["judge_review"]
    assert judge["usage"]["cache_creation_input_tokens"] == 0
    assert judge["usage"]["cache_read_input_tokens"] == 0
    charge = judge["usage"]["input_tokens"] * 5 + judge["usage"]["output_tokens"] * 25
    assert Decimal(charge) / 1_000_000 == Decimal(recorded["judge_cost"])
    assert (Decimal(str(scored["score"])) + Decimal(str(review["score"]))) / 2 == Decimal(
        str(recorded["combined"])
    )


def main():
    manifest = run.read(MANIFEST)
    verify_inventory(
        manifest[key]
        for key in ("producer_freeze", "ledger", "result", "source_adjudication", "safe_replay")
    )
    frozen = run.read(EVIDENCE / "preflight.json")
    verify_inventory(frozen["files"])
    result = run.read(RESULT)
    receipt = run.read(EVIDENCE / "safe-replay.json")
    assert receipt["case"] == result["matched_cases"][0]

    _, prompt, configs, tests = run.configured()
    test = next(test for test in tests if test["vars"]["evaluation_id"] == receipt["case"])
    ledger = run.read(EVIDENCE / "ledger.json")
    assert sum(Decimal(row["usd"]) for row in ledger) == Decimal(result["exact_estimated_usd"])
    assert len(ledger) == result["calls"] == 6 and all(row["state"] == "settled" for row in ledger)

    output = run.ROOT / "output"
    output.mkdir(exist_ok=True)
    with (
        TemporaryDirectory(prefix="neon-replay-", dir=output) as temporary,
        patch.object(run.provider, "_require_env", return_value="offline-only"),
        patch.object(socket, "create_connection", deny_network),
        patch.object(socket.socket, "connect", deny_network),
    ):
        for row in result["rows"]:
            arm = row["arm"]
            preflight_row = next(
                item
                for item in frozen["rendered"]
                if item["case"] == receipt["case"] and item["arm"] == arm
            )
            replay(
                Path(temporary),
                arm,
                row,
                preflight_row,
                receipt["arms"][arm],
                test,
                prompt,
                configs,
            )
    print(
        "Verified three native-contract replays, frozen subject/judge wires and six settled calls."
    )


if __name__ == "__main__":
    main()
