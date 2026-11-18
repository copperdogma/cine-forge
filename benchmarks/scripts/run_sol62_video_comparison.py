#!/usr/bin/env python3
"""Scout117 fresh ordered-frame screen with strict native wire and parity replay."""

from __future__ import annotations

import argparse
import base64
import fcntl
import json
import os
import sys
import time
import urllib.error
import urllib.request
from decimal import Decimal as D
from pathlib import Path
from unittest.mock import patch

import run_fable52_video_comparison as maintained
from PIL import Image

ROOT = maintained.ROOT
provider = maintained.provider
inventory = maintained.inventory
E = ROOT / "output/evals/sol62-frames-20261117"
FREEZE = E / "preflight.json"
ARMS = ("sol62", "sol", "luna")
MODELS = {
    "sol62": "gpt-6.2-sol",
    "sol": "gpt-6.1-sol",
    "luna": "gpt-6-luna",
    "opus": "claude-opus-4-6",
}
OUTPUT_CAPS = {"sol62": 4096, "sol": 4096, "luna": 1400}
LIMITS = {"sol62": 8, "controls": 12, "opus": 18}
RESERVES = {"sol62": D(".09096"), "sol": D(".09096"), "luna": D(".00320"), "opus": D(".3048")}
CAP = D("7")
BASE = "accb76dd6377d1a6a1ce65c2ac04f66e1458eb3e"

from video_understanding_scorer import get_assert  # noqa: E402


def read(path):
    return json.loads(path.read_text())


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def configured():
    task, prompt, configs, tests = maintained.matrix()
    del configs["fable52"]
    configs["sol62"] = dict(configs["sol"], model=MODELS["sol62"], reasoning_effort="medium")
    for arm in ARMS:
        configs[arm]["raw_output_dir"] = str((E / "native" / arm).relative_to(ROOT))
    return task, prompt, configs, tests


def request_for(arm, test):
    _, prompt, configs, _ = configured()
    return provider._prepare_subject_request(
        prompt, {"config": configs[arm]}, {"vars": test["vars"]}
    )


def render(arm, test):
    class Captured(Exception):
        pass

    wire = {}

    def capture(url, **kwargs):
        wire.update(url=url, payload=kwargs["body"])
        raise Captured

    with patch.object(provider, "_request_json", capture):
        try:
            provider._dispatch_subject_request(request_for(arm, test))
        except Captured:
            pass
    assert wire
    return wire


def owner_headers():
    return {"Authorization": "Bearer " + provider._require_env("OPENAI_API_KEY")}


def catalog():
    checked = {}
    for arm in ARMS:
        slug = MODELS[arm]
        url = f"https://api.openai.com/v1/models/{slug}"
        with urllib.request.urlopen(
            urllib.request.Request(url, headers=owner_headers()), timeout=40
        ) as result:
            entry = json.load(result)
        assert entry["id"] == slug
        checked[arm] = {"url": url, "id": slug}
    return checked


def count_openai(wire):
    payload = wire["payload"]
    body = {key: payload[key] for key in ("model", "input", "text")}
    return provider._request_json(
        wire["url"] + "/input_tokens",
        body=body,
        headers={
            **owner_headers(),
            "Content-Type": "application/json",
        },
    )["input_tokens"]


def judge_packet(row):
    # The old arm key is used only to retrieve identical frame bytes offline.
    return maintained._review_request("opus", dict(row, arm="sol"))


def preflight():
    if FREEZE.exists():
        verify_freeze()
        return
    _, _, _, tests = configured()
    access = catalog()
    paths = {
        Path(__file__),
        Path(maintained.__file__),
        ROOT / "benchmarks/tasks/video-understanding.yaml",
        ROOT / "benchmarks/prompts/video-understanding.txt",
        ROOT / "docs/evals/attempts/062-sol62-ordered-frame-screen.md",
        ROOT / "docs/evals/evidence/story-236-sol62-20261117/source-baseline.json",
        ROOT / "src/cine_forge/schemas/video_analysis.py",
        ROOT / "src/cine_forge/ai/model_identity.py",
        ROOT / "src/cine_forge/ai/token_usage.py",
        ROOT / "benchmarks/scorers/score_semantics.py",
        ROOT / "benchmarks/providers/video_understanding_transport.py",
    }
    paths.update((ROOT / "benchmarks/providers").glob("video_understanding*.py"))
    paths.update((ROOT / "benchmarks/scorers").glob("video_understanding*.py"))
    paths.update(
        p for p in (ROOT / "benchmarks/video_understanding_truth_v4").rglob("*") if p.is_file()
    )
    rows = []
    overlay = read(ROOT / "benchmarks/video_understanding_truth_v4/manifest.json")["cases"]
    assert [row["clip_id"] for row in overlay] == [test["vars"]["clip_id"] for test in tests]
    assert tests[0]["vars"]["evaluation_id"] == "vfp_active_001"
    for test, truth in zip(tests, overlay, strict=True):
        case = test["vars"]["evaluation_id"]
        clip = test["vars"]["clip_id"]
        baseline = ROOT / f"docs/evals/evidence/story-236-fable5220261109/native-sol-{case}.json"
        paths.add(baseline)
        sample, url, _ = judge_packet(read(baseline))
        assert sample["model"] == MODELS["opus"] and sample["max_tokens"] == 8192
        assert len(sample["messages"]) == 1 and "cache_control" not in json.dumps(sample)
        sample_count = maintained.count_review(sample)
        assert sample_count + 128 <= 20000
        dump(E / "wire" / f"{case}-judge-template.json", {"url": url, "payload": sample})
        for arm in ARMS:
            name = f"{case}-{arm}"
            request = request_for(arm, test)
            frames = request["packet"]["frames"]
            files = [inventory(frame["path"]) for frame in frames]
            assert [item["sha256"] for item in files] == truth["sampled_frame_sha256"]
            for frame in frames:
                with Image.open(frame["path"]) as picture:
                    assert picture.size == (640, 360) and picture.format == "JPEG"
                paths.add(frame["path"])
            paths.add(ROOT / "benchmarks/video_understanding" / clip / "meta.json")
            wire = render(arm, test)
            payload = wire["payload"]
            assert set(payload) == {
                "model",
                "input",
                "reasoning",
                "store",
                "service_tier",
                "max_output_tokens",
                "text",
            }
            assert payload["model"] == MODELS[arm] and payload["store"] is False
            assert payload["service_tier"] == "default"
            assert payload["reasoning"]["effort"] == ("medium" if arm == "sol62" else "low")
            assert payload["max_output_tokens"] == OUTPUT_CAPS[arm]
            assert payload["text"]["format"]["strict"] is True
            assert len(payload["text"]["format"]["schema"]["required"]) == 13
            assert len(payload["input"]) == 1 and payload["input"][0]["role"] == "user"
            parts = payload["input"][0]["content"]
            assert parts[0]["text"] == request["user_text"] and clip not in parts[0]["text"]
            assert len(parts) == 11
            for index, frame in enumerate(frames):
                assert parts[1 + 2 * index]["text"] == f"frame_index: {index}"
                part = parts[2 + 2 * index]
                assert part["detail"] == "high" and part["image_url"].startswith("data:image/jpeg;")
                assert (
                    base64.b64decode(part["image_url"].split(",", 1)[1])
                    == frame["path"].read_bytes()
                )
                assert (
                    sample["messages"][0]["content"][2 * index + 1]["source"]["data"]
                    == frame["base64"]
                )
            token_count = count_openai(wire)
            assert 0 < token_count + 128 <= 20000
            target = E / "wire" / f"{name}.json"
            dump(target, wire)
            rows.append(
                dict(
                    arm=arm,
                    case=case,
                    group=name,
                    input_tokens=token_count,
                    reserved=str(RESERVES[arm]),
                    judge_template_tokens=sample_count,
                    frames=files,
                    wire=inventory(target),
                )
            )
        print(case, "rendered, counted and independently grouped", flush=True)
    assert len({row["wire"]["sha256"] for row in rows}) == 18
    cap_plan = {
        "sol62": LIMITS["sol62"] * RESERVES["sol62"],
        "controls": 6 * (RESERVES["sol"] + RESERVES["luna"]),
        "opus": LIMITS["opus"] * RESERVES["opus"],
    }
    assert cap_plan["controls"] <= D(".60") and sum(cap_plan.values()) <= CAP
    dump(
        FREEZE,
        dict(
            base=BASE,
            files=[inventory(path) for path in sorted(paths)],
            rendered=rows,
            cap=str(CAP),
            bounds={key: str(value) for key, value in cap_plan.items()},
            limits=LIMITS,
            catalog=access,
            models=MODELS,
            cache="Serial; no subject-result or judge cache. Raw receipts only resume same run. "
            "Implicit OpenAI input cache metered as returned. No Anthropic cache controls.",
            grouping="Separate single user turns without prior response IDs or shared sessions.",
            classification="Authored synthetic source only; Standard logging may apply.",
            tariff_usd_per_million={
                "sol62": [2, 0.1, 2.5, 10],
                "sol": [2, 0.1, 2.5, 10],
                "luna": [0.1, 0.01, 0.125, 0.5],
                "opus": [5, 25],
            },
        ),
    )


def verify_freeze():
    freeze = read(FREEZE)
    for item in freeze["files"] + [row["wire"] for row in freeze["rendered"]]:
        assert inventory(ROOT / item["path"]) == item, item["path"]


def ledger():
    target = E / "ledger.json"
    return read(target) if target.exists() else []


def charge(name, arm, amount=None):
    rows = ledger()
    row = next((row for row in rows if row["name"] == name), None)
    group = "controls" if arm in {"sol", "luna"} else arm
    if amount is None:
        assert row is None, f"Request already dispatched: {name}"
        assert sum(row["group"] == group for row in rows) < LIMITS[group]
        reserved = RESERVES[arm]
        assert sum(D(row["usd"]) for row in rows) + reserved <= CAP
        rows.append(
            dict(
                name=name,
                arm=arm,
                group=group,
                state="reserved",
                reserved=str(reserved),
                usd=str(reserved),
            )
        )
    elif row["state"] == "reserved":
        assert 0 <= amount <= D(row["reserved"]), name
        row.update(state="settled", usd=str(amount))
    else:
        assert D(row["usd"]) == amount
    dump(E / "ledger.json", rows)


def subject(arm, test, retry):
    case = test["vars"]["evaluation_id"]
    name = f"{case}-{arm}"
    receipt = E / f"{name}-subject.json"
    if receipt.exists():
        return read(receipt)
    wire = read(E / "wire" / f"{name}.json")
    request = request_for(arm, test)
    physical_name = name + (
        "-recovery" if retry and any(row["name"] == name for row in ledger()) else ""
    )
    native = E / "native" / arm
    config = request["config"]
    config["raw_output_dir"] = str((native / physical_name).relative_to(ROOT))
    full_envelope = E / f"{physical_name}-raw.json"
    original = provider._request_json

    def live(url, **kwargs):
        assert {"url": url, "payload": kwargs["body"]} == wire
        if full_envelope.exists():
            return read(full_envelope)
        charge(physical_name, arm)
        started = time.monotonic()
        try:
            raw = original(url, **kwargs)
        except Exception as exc:
            # Preserve status/class without copying potentially sensitive response text.
            dump(
                E / f"{physical_name}-error.json",
                {"class": type(exc).__name__, "status": getattr(exc, "status_code", None)},
            )
            raise
        dump(full_envelope, raw)
        dump(E / f"{physical_name}-timing.json", round((time.monotonic() - started) * 1000))
        return raw

    # Meter valid native usage even when the subsequent strict parser rejects output.
    try:
        with patch.object(provider, "_request_json", live):
            result = provider._dispatch_subject_request(request)
    finally:
        if full_envelope.exists():
            raw = read(full_envelope)
            if raw.get("model") == MODELS[arm] and raw.get("service_tier") == "default":
                usage, inputs, outputs, _, _, _, cost = (
                    provider._provider_support.openai_usage_and_cost(
                        vars(provider), raw, MODELS[arm]
                    )
                )
                assert inputs <= 20000 and outputs <= OUTPUT_CAPS[arm] and usage
                charge(physical_name, arm, D(str(cost)))
    elapsed = read(E / f"{physical_name}-timing.json")
    response = provider._build_promptfoo_response(
        request=request,
        response=result,
        latency_ms=elapsed,
        cost_usd=provider._response_cost(request, result),
        subject_contract_sha256=None,
    )
    _, prompt, configs, _ = configured()
    configs[arm]["raw_output_dir"] = config["raw_output_dir"]

    def replay(url, **kwargs):
        assert {"url": url, "payload": kwargs["body"]} == wire
        return read(full_envelope)

    with patch.object(provider, "_request_json", replay):
        parsed = provider.call_api(prompt, {"config": configs[arm]}, {"vars": test["vars"]})
    assert not parsed.get("error"), parsed.get("error")
    assert parsed["output"] == response["output"]
    assert parsed["metadata"]["returned_model"] == MODELS[arm]
    assert set(json.loads(response["output"])) == set(
        provider._VIDEO_ANALYSIS_RESPONSE_SCHEMA["required"]
    )
    row = dict(
        arm=arm,
        vars=test["vars"],
        response=response,
        native_call=physical_name,
        parity="Exact native request and complete response replayed through call_api.",
        structural=get_assert(response["output"], {"vars": test["vars"]}),
    )
    dump(receipt, row)
    print(name, "native and parity passed", response["cost"], elapsed / 1000, flush=True)
    return row


def judge(row, retry):
    name = row["vars"]["evaluation_id"] + "-" + row["arm"] + "-opus"
    receipt = E / f"{name}.json"
    if receipt.exists():
        return
    body, url, headers = judge_packet(row)
    physical_name = name + (
        "-recovery" if retry and any(item["name"] == name for item in ledger()) else ""
    )
    raw_path = E / f"{physical_name}-raw.json"
    if not raw_path.exists():
        tokens = maintained.count_review(body)
        assert tokens + 128 <= 20000
        dump(E / f"{physical_name}-request.json", {"url": url, "payload": body, "count": tokens})
        charge(physical_name, "opus")
        start = time.monotonic()
        raw = provider._request_json(
            url, body=body, headers=headers, timeout_seconds=100, raw_output_path=raw_path
        )
        dump(E / f"{physical_name}-timing.json", round((time.monotonic() - start) * 1000))
    else:
        raw = read(raw_path)
    assert raw["model"] == MODELS["opus"] and raw["id"]
    usage = raw["usage"]
    assert not usage.get("cache_read_input_tokens") and not usage.get("cache_creation_input_tokens")
    assert usage["input_tokens"] <= 20000 and usage["output_tokens"] <= 8192
    cost = D(usage["input_tokens"] * 5 + usage["output_tokens"] * 25) / 1000000
    charge(physical_name, "opus", cost)
    assert raw["stop_reason"] == "end_turn"
    answer = json.loads(next(part["text"] for part in raw["content"] if part["type"] == "text"))
    assert 0 <= answer["score"] <= 1 and answer["reason"]
    dump(
        receipt,
        dict(
            **answer, cost=str(cost), observed=usage, model=raw["model"], native_call=physical_name
        ),
    )
    print(name, "rubric", answer["score"], flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["preflight", "first", "next"])
    parser.add_argument("--case")
    parser.add_argument("--recover", help="One failed physical subject/judge name after diagnosis.")
    args = parser.parse_args()
    os.umask(0o077)
    E.mkdir(parents=True, exist_ok=True)
    with (E / "run.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if args.mode == "preflight":
            preflight()
            return
        verify_freeze()
        tests = configured()[3]
        if args.mode == "first":
            test = tests[0]
        else:
            found = {test["vars"]["evaluation_id"]: test for test in tests[1:]}
            test = found[args.case]
            assert read(E / "first-source-review.json")["expand"] is True
        case = test["vars"]["evaluation_id"]
        subjects = [subject(arm, test, args.recover == f"{case}-{arm}") for arm in ARMS]
        for row in subjects:
            judge(row, args.recover == f"{case}-{row['arm']}-opus")


if __name__ == "__main__":
    try:
        main()
    except (urllib.error.URLError, provider.ProviderHTTPError) as error:
        print(
            type(error).__name__,
            getattr(error, "status_code", getattr(error, "code", "")),
            file=sys.stderr,
        )
        raise SystemExit(1) from None
