"""Fresh Scout109 ordered-frame panel. Reuse maintained rendering, adapter, scorer and rubric."""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import run_fable52_video_comparison as previous
from PIL import Image

ROOT = previous.ROOT
provider = previous.provider
dump = previous.dump
inventory = previous.inventory
E = ROOT / "docs/evals/evidence/story-236-carbon-20261110"
RAW = ROOT / "output/evals/carbon-frames-20261110"
ARMS = ("carbon", "sol", "luna")
MODELS = dict(
    carbon="gemini-4-carbon", sol="gpt-6.1-sol", luna="gpt-6-luna", opus="claude-opus-4-6"
)
CAP = Decimal("11")
D = Decimal
FREEZE = E / "preflight.json"
RESULT = ROOT / "benchmarks/results/video-understanding-carbon-sol-luna-v4-20261110.json"
sys.path.insert(0, str(ROOT / "benchmarks/scorers"))
from video_understanding_scorer import get_assert  # noqa: E402


def read(path):
    return json.loads(path.read_text())


def configured():
    task, prompt, configs, tests = previous.matrix()
    del configs["fable52"]
    configs["carbon"] = dict(
        configs["sol"],
        provider="google",
        model=MODELS["carbon"],
        reasoning_effort="high",
        max_tokens=32768,
    )
    configs["carbon"].pop("transport", None)
    for arm in ARMS:
        configs[arm]["raw_output_dir"] = str((RAW / arm).relative_to(ROOT))
    return task, prompt, configs, tests


def prep(arm, test):
    _, prompt, cfg, _ = configured()
    return provider._prepare_subject_request(prompt, {"config": cfg[arm]}, {"vars": test["vars"]})


def render(arm, test):
    body = {}

    class Captured(Exception):
        pass

    def capture(url, **kwargs):
        body.update(url=url, payload=kwargs["body"])
        raise Captured

    with patch.object(provider, "_request_json", capture):
        try:
            provider._dispatch_subject_request(prep(arm, test))
        except Captured:
            pass
    assert body
    return body


def post(url, data, headers):
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=150) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"{url}: HTTP{exc.code}: {exc.read().decode()[:1200]}") from None


def count(arm, wire):
    body = wire["payload"]
    if arm == "carbon":
        req = {"generateContentRequest": {"model": "models/gemini-4-carbon", **body}}
        return post(
            wire["url"].replace(":generateContent", ":countTokens"),
            req,
            {"x-goog-api-key": provider._require_env("GEMINI_API_KEY")},
        )["totalTokens"]
    # Token-counting endpoint accepts input and exact schema, without inference.
    req = {k: body[k] for k in ("model", "input", "text")}
    return post(
        wire["url"] + "/input_tokens",
        req,
        {"Authorization": "Bearer " + provider._require_env("OPENAI_API_KEY")},
    )["input_tokens"]


def judge_body(row):
    # Prior maintainer's frozen rubric and five original images; no arm identity on wire.
    source = dict(row, arm="sol")
    return previous._review_request("opus", source)


def preflight():
    if FREEZE.exists():
        verify_freeze()
        return
    task, prompt, cfg, tests = configured()
    paths = {
        Path(__file__),
        Path(previous.__file__),
        ROOT / "benchmarks/tasks/video-understanding.yaml",
        ROOT / "benchmarks/prompts/video-understanding.txt",
        ROOT / "src/cine_forge/schemas/video_analysis.py",
        ROOT / "src/cine_forge/ai/token_usage.py",
        ROOT / "benchmarks/scorers/score_semantics.py",
    }
    paths.update((ROOT / "benchmarks/providers").glob("video_understanding*.py"))
    paths.update((ROOT / "benchmarks/scorers").glob("video_understanding*.py"))
    paths.update(
        p for p in (ROOT / "benchmarks/video_understanding_truth_v4").rglob("*") if p.is_file()
    )
    rows = []
    for test in tests:
        cid = test["vars"]["evaluation_id"]
        ref = read(ROOT / f"docs/evals/evidence/story-236-fable5220261109/native-sol-{cid}.json")
        judge, _, _ = judge_body(ref)
        judge_tokens = previous.count_review(judge)
        assert judge_tokens <= 20000
        for arm in ARMS:
            request = prep(arm, test)
            frames = request["packet"]["frames"]
            assert len(frames) == 5 and all(
                Image.open(f["path"]).size == (640, 360) for f in frames
            )
            paths.update(f["path"] for f in frames)
            paths.add(
                ROOT / "benchmarks/video_understanding" / test["vars"]["clip_id"] / "meta.json"
            )
            assert test["vars"]["clip_id"] not in request["user_text"]
            wire = render(arm, test)
            token_count = count(arm, wire)
            assert token_count <= (106000 if arm == "carbon" else 26000)
            body = wire["payload"]
            if arm == "carbon":
                assert len(body["generationConfig"]["responseSchema"]["required"]) == 13
            else:
                assert body["store"] is False and body["reasoning"]["effort"] == "low"
            reserve = subject_reserve(arm, token_count)
            rows.append(
                dict(
                    arm=arm,
                    case=cid,
                    tokens=token_count,
                    reserved=str(reserve),
                    sample_judge_tokens=judge_tokens,
                    frames=[inventory(f["path"]) for f in frames],
                )
            )
            dump(E / "wire" / f"{cid}-{arm}.json", wire)
    control_pool = sum(D(r["reserved"]) for r in rows if r["arm"] in ("sol", "luna"))
    print("Rendered18 fresh subjects and18 reviews; control worst case", control_pool, flush=True)
    assert control_pool <= D(".30")
    dump(
        FREEZE,
        dict(
            base="3b44e158a74010a68bf8d2bbe7e7a92991f96a69",
            files=[inventory(p) for p in sorted(paths)],
            rendered=rows,
            cap="11",
            control_pool=str(control_pool),
            carbon_pool="3.238080",
            judge_pool="5.4864",
            recovery="1.97552",
            cache="No adapter result cache; implicit input cache measured",
            order="Six serial Carbon/Sol/Luna subjects, one blind full source review per output",
            routes=MODELS,
            data="Public authored synthetic 640x360 JPEGs. Paid API abuse logging possible.",
            effort="Carbon high32768; Sol low4096; Luna low1400. Opus8192. No tuning or repeats.",
        ),
    )


def subject_reserve(arm, tokens):
    if arm == "carbon":
        return D(".53968")
    # Native count plus a small allowance for provider-side format additions.
    padded = tokens + 128
    if arm == "sol":
        return (D(padded) * D("2.5") + 4096 * 10) / 1000000
    return (D(padded) * D(".125") + 1400 * D(".5")) / 1000000


def verify_freeze():
    for item in read(FREEZE)["files"]:
        path = ROOT / item["path"]
        if RESULT.exists() and inventory(path) != item:
            frozen = E / "producer" / path.name
            assert frozen.is_file() and inventory(frozen)["sha256"] == item["sha256"], item["path"]
        else:
            assert inventory(path) == item, item["path"]


def ledger():
    path = E / "ledger.json"
    return read(path) if path.exists() else []


def record(name, amount, state):
    rows = ledger()
    existing = next((r for r in rows if r["name"] == name), None)
    if state == "reserved":
        assert not existing, f"Existing request: {name}"
        assert sum(D(r["usd"]) for r in rows) + amount <= CAP
        rows.append(dict(name=name, state=state, reserved=str(amount), usd=str(amount)))
    else:
        assert existing and existing["state"] == "reserved" and amount <= D(existing["reserved"]), (
            name
        )
        existing.update(state=state, usd=str(amount))
    dump(E / "ledger.json", rows)


def subject(arm, test):
    cid = test["vars"]["evaluation_id"]
    name = f"{cid}-{arm}"
    receipt = E / f"{name}-subject.json"
    if receipt.exists():
        return read(receipt)
    wire = read(E / "wire" / f"{name}.json")
    row = next(r for r in read(FREEZE)["rendered"] if r["case"] == cid and r["arm"] == arm)
    request = prep(arm, test)
    original = provider._request_json

    def live(url, **kwargs):
        assert {"url": url, "payload": kwargs["body"]} == wire
        record(name, D(row["reserved"]), "reserved")
        try:
            raw = original(url, **kwargs)
        except Exception as exc:
            dump(E / f"{name}-error.json", {"type": type(exc).__name__, "message": str(exc)})
            raise
        dump(E / f"{name}-raw.json", raw)
        return raw

    start = time.monotonic()
    with patch.object(provider, "_request_json", live):
        result = provider._dispatch_subject_request(request)
    elapsed = round((time.monotonic() - start) * 1000)
    response = provider._build_promptfoo_response(
        request=request,
        response=result,
        latency_ms=elapsed,
        cost_usd=provider._response_cost(request, result),
        subject_contract_sha256=None,
    )
    record(name, D(str(response["cost"])), "settled")
    _, prompt, cfg, _ = configured()

    def replay(url, **kwargs):
        assert {"url": url, "payload": kwargs["body"]} == wire
        return read(E / f"{name}-raw.json")

    with patch.object(provider, "_request_json", replay):
        parsed = provider.call_api(prompt, {"config": cfg[arm]}, {"vars": test["vars"]})
    assert not parsed.get("error"), parsed.get("error")
    assert parsed["output"] == response["output"]
    assert parsed["metadata"]["returned_model"] == response["metadata"]["returned_model"]
    assert set(json.loads(response["output"])) == set(
        provider._VIDEO_ANALYSIS_RESPONSE_SCHEMA["required"]
    )
    row = dict(
        arm=arm,
        vars=test["vars"],
        response=response,
        parity="Complete native wire/envelope matched maintained call_api offline",
        structural=get_assert(response["output"], {"vars": test["vars"]}),
    )
    dump(receipt, row)
    print(name, "settled", response["cost"], "seconds", elapsed / 1000, flush=True)
    return row


def judge(row):
    name = row["vars"]["evaluation_id"] + "-" + row["arm"] + "-opus"
    receipt = E / f"{name}.json"
    if receipt.exists():
        return
    body, url, headers = judge_body(row)
    tokens = previous.count_review(body)
    assert tokens <= 20000
    dump(E / f"{name}-request.json", {"url": url, "payload": body, "count": tokens})
    record(name, D(".3048"), "reserved")
    raw = post(url, body, headers)
    dump(E / f"{name}-raw.json", raw)
    assert raw["model"] == MODELS["opus"] and raw["id"] and raw["stop_reason"] == "end_turn"
    usage = raw["usage"]
    assert not usage.get("cache_read_input_tokens") and not usage.get("cache_creation_input_tokens")
    cost = D(usage["input_tokens"] * 5 + usage["output_tokens"] * 25) / 1000000
    record(name, cost, "settled")
    answer = json.loads(next(c["text"] for c in raw["content"] if c["type"] == "text"))
    assert 0 <= answer["score"] <= 1 and answer["reason"]
    dump(receipt, dict(**answer, cost=str(cost), observed=usage, model=raw["model"]))
    print(name, "score", answer["score"], flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["preflight", "first", "remaining"])
    command = parser.parse_args().mode
    if command == "preflight":
        preflight()
        return
    verify_freeze()
    assert not RESULT.exists()
    tests = configured()[3]
    for test in tests[:1] if command == "first" else tests[1:]:
        for arm in ARMS:
            judge(subject(arm, test))


if __name__ == "__main__":
    main()
