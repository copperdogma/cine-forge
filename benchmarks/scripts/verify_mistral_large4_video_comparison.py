#!/usr/bin/env python3
"""Replay Story229 hashes, transport/usage and scores offline without inference."""
from __future__ import annotations

import hashlib
import json
from decimal import Decimal

import run_mistral_large4_video_comparison as run
from video_understanding_scorer import get_assert


def main():
    run.check_freeze()
    manifest_path = run.ROOT / "docs/evals/story-229-mistral-large4-evidence.json"
    manifest = json.loads(manifest_path.read_text())
    for item in manifest["retained_files"]:
        data = (run.ROOT / item["path"]).read_bytes()
        assert len(data) == item["bytes"]
        assert hashlib.sha256(data).hexdigest() == item["sha256"], item["path"]
    result = json.loads(run.RESULT.read_text())
    ids = set()
    for arm in ("mistral", "luna"):
        bodies = []
        for stage in ("native", "subject"):
            name = f"{stage}-{arm}-vfp_active_001"
            row = json.loads((run.EVIDENCE / f"{name}.json").read_text())
            response = row["response"]
            assert response["raw"]["id"] not in ids
            ids.add(response["raw"]["id"])
            run.provider.VideoAnalysisPrediction.model_validate_json(response["output"])
            usage = response["raw"]["usage"]
            request = json.loads((run.EVIDENCE / f"{name}-request.json").read_text())
            bodies.append(request)
            body = request["payload"]
            if arm == "mistral":
                assert response["raw"]["model"] == "mistralai/mistral-large-4-0"
                assert response["raw"]["provider"] == "Mistral"
                assert body["provider"] == {
                    "order": ["Mistral"], "allow_fallbacks": False,
                    "require_parameters": True, "max_price": {"prompt": .68, "completion": 2.09},
                }
                assert body["response_format"]["json_schema"]["strict"] is True
                assert "reasoning" not in body
                content = body["messages"][0]["content"]
                assert usage["total_tokens"] == usage["prompt_tokens"] + usage["completion_tokens"]
                assert response["cost"] == usage["cost"] >= 0
                assert usage["completion_tokens"] <= body["max_completion_tokens"] == 4096
            else:
                assert response["raw"]["model"] == "gpt-6-luna"
                assert response["raw"]["status"] == "completed"
                assert response["raw"]["service_tier"] == "default"
                assert body["reasoning"] == {"effort": "low"}
                assert body["text"]["format"]["strict"] is True
                assert body["max_output_tokens"] == 1400
                content = body["input"][0]["content"]
                assert usage["total_tokens"] == usage["input_tokens"] + usage["output_tokens"]
            assert sum(x["type"] in ("image_url", "input_image") for x in content) == 5
            assert "dialogue_confession_push_in" not in json.dumps(body)
        assert bodies[0] == bodies[1], "Native/parity payload mismatch"
        saved = next(r for r in result["rows"] if r["arm"] == arm)
        assertion = get_assert(saved["response"]["output"], {"vars": saved["vars"]})
        assert assertion == saved["assertion"]
        judge = json.loads((run.EVIDENCE / f"judge-opus-{arm}-vfp_active_001.json").read_text())
        assert judge["model"] == "claude-opus-4-6" and judge["request_id"] not in ids
        ids.add(judge["request_id"])
        assert (assertion["score"] + judge["score"]) / 2 == saved["combined"]
        assert saved["combined"] == result["summary"][arm]["overall"]
    assert len(ids) == 6 and len(result["rows"]) == 2
    ledger = result["ledger"]
    assert len(ledger) == 6 and all(r["state"] == "settled" for r in ledger)
    total = sum((Decimal(r["accounted_usd"]) for r in ledger), Decimal(0))
    assert total == Decimal(result["accounted_usd"]) < Decimal(3)
    assert all(not r["estimated"] for r in ledger if r["arm"] == "mistral")
    assert result["unknown_exposure_usd"] == "0" and result["paid_retries"] == 0
    print(f"Story229 PASS: {len(manifest['retained_files'])} retained hashes, "
          "six unique paid IDs, four five-image strict requests, two scored rows, "
          "no provider calls")


if __name__ == "__main__":
    main()
