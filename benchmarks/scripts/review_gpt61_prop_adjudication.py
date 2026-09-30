#!/usr/bin/env python3
"""Source-first cross-provider adjudication of the Opus case004 review defect."""

from __future__ import annotations

import json
import time
import urllib.request
from decimal import Decimal

import run_gpt61_video_comparison as run

MODEL = "claude-sonnet-5-5"
CASE = "vfp_active_004"
RESERVATION = Decimal(".09096")  # 20K input at cache-write upper $2.50 + 4096 output at $10


def adjudicate(arm: str) -> None:
    name = f"judge-sonnet-source-adjudication-{arm}-{CASE}"
    parsed_path = run.OUT / f"{name}.json"
    if parsed_path.exists():
        raise RuntimeError(f"Do not repeat {name}")
    task, prompt, configs, tests = run.matrix()
    test = next(t for t in tests if t["vars"]["evaluation_id"] == CASE)
    packet = run.provider._prepare_subject_request(
        prompt, {"config": configs[arm]}, {"vars": test["vars"]}
    )["packet"]
    assert len(packet["frames"]) == 5
    output = json.loads((run.OUT / f"subject-{arm}-{CASE}.json").read_text())["response"]["output"]
    target = (
        run.ROOT / "benchmarks/video_understanding_truth_v4"
        / test["vars"]["clip_id"] / "target.md"
    ).read_text()
    rubric = task["tests"][0]["assert"][1]["value"].replace("{{target_markdown}}", target)
    content = [{"type": "text", "text": (
        "Read the five images in zero-based order first. Independently identify the "
        "rectangle color at each frame_index before evaluating the output. Then use "
        "the same rubric/reference below and return a 0..1 score with concrete reasons. "
        "Do not infer that 'red in frame 1' means it was absent from frame 0. "
        "Evidence entries need only cover the frames necessary to ground the claims; "
        "the schema has no all-five-frames requirement. The allowed color_tags enum "
        "has no generic blue tag; correct blue text suffices. A stillness tag is "
        "compatible with a static scene. Penalize wrong continuity_status."
    )}]
    for i, frame in enumerate(packet["frames"]):
        content.append({"type": "text", "text": f"frame_index: {i}"})
        content.append({"type": "image", "source": {
            "type": "base64", "media_type": "image/jpeg", "data": frame["base64"]
        }})
    content.append({"type": "text", "text": f"<Output>\n{output}\n</Output>\n\n{rubric}"})
    body = {
        "model": MODEL,
        "max_tokens": 4096,
        "thinking": {"type": "adaptive"},
        "output_config": {"effort": "medium", "format": {
            "type": "json_schema", "schema": run.JUDGE_SCHEMA,
        }},
        "messages": [{"role": "user", "content": content}],
    }
    request_path = run.OUT / f"{name}-request.json"
    run.dump(request_path, {"url": run.provider.ANTHROPIC_MESSAGES_URL, "payload": body})
    run.RESERVE["adjudicator"] = RESERVATION
    run.begin(name, "adjudicator")
    started = time.perf_counter()
    req = urllib.request.Request(
        run.provider.ANTHROPIC_MESSAGES_URL,
        data=json.dumps(body).encode(),
        headers={
            "x-api-key": run.provider._require_env("ANTHROPIC_API_KEY"),
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    raw_path = run.OUT / f"{name}-raw.json"
    with urllib.request.urlopen(req, timeout=90) as response:
        raw_bytes = response.read()
    raw_path.write_bytes(raw_bytes)
    raw = json.loads(raw_bytes)
    assert raw.get("model") == MODEL and raw.get("id") and raw.get("stop_reason") == "end_turn"
    usage = raw["usage"]
    assert not usage.get("cache_read_input_tokens", 0)
    assert not usage.get("cache_creation_input_tokens", 0)
    cost = (Decimal(usage["input_tokens"]) * 2 + Decimal(usage["output_tokens"]) * 10) / 1_000_000
    run.settle(name, cost)
    text = "\n".join(x["text"] for x in raw["content"] if x["type"] == "text")
    parsed = json.loads(text)
    assert isinstance(parsed["score"], (int, float)) and 0 <= parsed["score"] <= 1
    assert isinstance(parsed["reason"], str) and parsed["reason"]
    parsed.update(
        model=MODEL, request_id=raw["id"], usage=usage, cost_usd=str(cost),
        latency_ms=round((time.perf_counter() - started) * 1000), raw=run.inventory(raw_path),
    )
    run.dump(parsed_path, parsed)
    for path in (request_path, raw_path, parsed_path):
        target_path = run.EVIDENCE / path.relative_to(run.OUT)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(path.read_bytes())
    print(name, "score", parsed["score"], "cost", cost, flush=True)


def main() -> None:
    if run.RESULT.exists():
        raise RuntimeError("Immutable report exists")
    run.check_freeze()
    for arm in ("sol", "luna"):
        adjudicate(arm)


if __name__ == "__main__":
    main()
