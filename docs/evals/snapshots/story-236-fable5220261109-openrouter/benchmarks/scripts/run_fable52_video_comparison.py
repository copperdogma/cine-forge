#!/usr/bin/env python3
"""Bounded fresh comparison using the maintained video adapter and v4 scorer."""

# ruff: noqa: E501

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.request
from decimal import Decimal
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [
    str(ROOT / "benchmarks/providers"),
    str(ROOT / "benchmarks/scorers"),
    str(ROOT / "src"),
]
import video_understanding_provider as provider  # noqa: E402

OUT = ROOT / "output/evals/fable52-20261109"
EVIDENCE = ROOT / "docs/evals/evidence/story-236-fable5220261109"
FREEZE = ROOT / "docs/evals/story-236-fable5220261109-fable52-freeze.json"
RESULT = ROOT / "benchmarks/results/video-understanding-fable52-vs-sol-luna-v4-20261109.json"
CAP = Decimal("20")
RATES = {
    "gpt-6.1-sol": (2, 10),
    "gpt-6-luna": (0.125, 0.5),
    "claude-opus-4-6": (5, 25),
}
RESERVE = {
    "fable52": Decimal("2.15872"),
    "sol": Decimal(".04624"),
    "luna": Decimal(".002"),
    "opus": Decimal(".3048"),
}
JUDGE_SCHEMA = {
    "type": "object",
    "properties": {"score": {"type": "number"}, "reason": {"type": "string"}},
    "required": ["score", "reason"],
    "additionalProperties": False,
}


def source_images(row):
    _, prompt, configs, _ = matrix()
    request = provider._prepare_subject_request(
        prompt, {"config": configs[row["arm"]]}, {"vars": row["vars"]}
    )
    result = []
    for i, frame in enumerate(request["packet"]["frames"]):
        result += [
            {"type": "text", "text": f"Source frame_index: {i}"},
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": frame["mime_type"],
                    "data": frame["base64"],
                },
            },
        ]
    return result


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def inventory(path):
    data = path.read_bytes()
    return {
        "path": str(path.relative_to(ROOT)),
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
    }


def matrix():
    task = yaml.safe_load((ROOT / "benchmarks/tasks/video-understanding.yaml").read_text())
    prompt = (ROOT / "benchmarks/prompts/video-understanding.txt").read_text()
    configs = {}
    for arm, model in [
        ("fable52", "anthropic/claude-fable-5.2"),
        ("sol", "gpt-6.1-sol"),
        ("luna", "gpt-6-luna"),
    ]:
        matches = [p for p in task["providers"] if p["config"]["model"] == model]
        if arm == "fable52":
            config = dict(
                provider="openrouter",
                upstream_provider="Anthropic",
                max_price={"prompt": 8, "completion": 40},
                request_timeout_seconds=360,
                model=model,
                reasoning_effort="xhigh",
                max_tokens=32768,
                max_frames=5,
                frame_policy="five_evenly_spaced_jpegs_v1",
                prompt_version="video-understanding-frame-packet-v3",
            )
        else:
            assert len(matches) == 1
            config = dict(matches[0]["config"])
        config["basePath"] = str(ROOT / "benchmarks/tasks")
        config["raw_output_dir"] = str((OUT / arm).relative_to(ROOT))
        configs[arm] = config
    tests = task["tests"]
    assert len(tests) == 6 and len({t["vars"]["evaluation_id"] for t in tests}) == 6
    return task, prompt, configs, tests


def frozen_files():
    paths = [
        Path(__file__),
        ROOT / "benchmarks/tasks/video-understanding.yaml",
        ROOT / "benchmarks/prompts/video-understanding.txt",
        ROOT / "src/cine_forge/schemas/video_analysis.py",
    ]
    paths += list((ROOT / "benchmarks/providers").glob("video_understanding*.py"))
    paths += list((ROOT / "benchmarks/scorers").glob("video_understanding*.py"))
    paths += [ROOT / "benchmarks/scorers/score_semantics.py"]
    paths += list((ROOT / "benchmarks/video_understanding_truth_v4").rglob("*"))
    _, prompt, configs, tests = matrix()
    for t in tests:
        request = provider._prepare_subject_request(
            prompt, {"config": configs["fable52"]}, {"vars": t["vars"]}
        )
        packet = request["packet"]
        assert packet["frame_count"] == 5
        assert t["vars"]["clip_id"] not in request["user_text"]
        paths += [f["path"] for f in packet["frames"]]
        paths += [ROOT / "benchmarks/video_understanding" / t["vars"]["clip_id"] / "meta.json"]
    return sorted(set(p for p in paths if p.is_file()))


def check_freeze():
    freeze = json.loads(FREEZE.read_text())
    for item in freeze["files"]:
        path = item["path"]
        archived = (
            ROOT / "docs/evals/snapshots/story-236-fable5220261109" / (Path(path).name + ".txt")
        )  # noqa: E501
        actual = inventory(archived if archived.exists() else ROOT / path)
        assert (actual["sha256"], actual["bytes"]) == (item["sha256"], item["bytes"]), (
            f"Frozen bytes changed: {item['path']}"
        )


def ledger():
    path = OUT / "ledger.json"
    return json.loads(path.read_text()) if path.exists() else []


def accounted():
    return sum((Decimal(str(x["accounted_usd"])) for x in ledger()), Decimal(0))


def begin(name, arm):
    assert not any(x["name"] == name for x in ledger()), f"Do not repeat {name}"
    if accounted() + RESERVE[arm] > CAP:
        raise RuntimeError("Hard budget cap blocks next full reservation")
    rows = ledger()
    rows.append(
        {
            "name": name,
            "arm": arm,
            "state": "reserved",
            "accounted_usd": str(RESERVE[arm]),
            "reservation_usd": str(RESERVE[arm]),
        }
    )
    dump(OUT / "ledger.json", rows)


def settle(name, cost):
    rows = ledger()
    row = next(x for x in rows if x["name"] == name)
    row.update(state="settled", accounted_usd=str(cost), estimated=True)
    dump(OUT / "ledger.json", rows)


def subject(arm, test, *, native=False):
    _, prompt, configs, _ = matrix()
    config = dict(configs[arm])
    prefix = "native" if native else "subject"
    name = f"{prefix}-{arm}-{test['vars']['evaluation_id']}"
    receipt = OUT / f"{name}.json"
    if receipt.exists():
        return json.loads(receipt.read_text())
    config["raw_output_dir"] = str((OUT / prefix / arm).relative_to(ROOT))
    prepared = provider._prepare_subject_request(prompt, {"config": config}, {"vars": test["vars"]})
    original = provider._request_json

    def capture(url, **kwargs):
        dump(OUT / f"{name}-request.json", {"url": url, "payload": kwargs["body"]})
        return original(url, **kwargs)

    provider._request_json = capture
    assert __import__("shutil").disk_usage(ROOT).free >= 512 * 1024**2
    begin(name, arm)
    start = time.perf_counter()
    try:
        if native:
            response = provider._dispatch_subject_request(prepared)
            response = provider._build_promptfoo_response(
                request=prepared,
                response=response,
                latency_ms=round((time.perf_counter() - start) * 1000),
                cost_usd=provider._response_cost(prepared, response),
                subject_contract_sha256=None,
            )
        else:
            response = provider.call_api(prompt, {"config": config}, {"vars": test["vars"]})
    finally:
        provider._request_json = original
    row = {"name": name, "arm": arm, "vars": test["vars"], "response": response}
    dump(receipt, row)
    if response.get("error"):
        raise RuntimeError(response["error"])
    provider.VideoAnalysisPrediction.model_validate_json(response["output"])
    settle(name, response["cost"])
    raw_path = ROOT / response["raw"]["raw_envelope_path"]
    for path in [receipt, raw_path, OUT / f"{name}-request.json"]:
        target = EVIDENCE / path.relative_to(OUT)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(path.read_bytes())
    print(name, "latency", response["latencyMs"], "cost", response["cost"], flush=True)
    return row


def _review_request(kind, row):
    task, prompt, configs, _ = matrix()
    t = row["vars"]
    target = (
        ROOT / "benchmarks/video_understanding_truth_v4" / t["clip_id"] / "target.md"
    ).read_text()
    rubric = task["tests"][0]["assert"][1]["value"].replace("{{target_markdown}}", target)
    user = "<Output>\n" + row["response"]["output"] + "\n</Output>\n\n" + rubric
    user += "\nAll five original source images follow. Treat them as primary truth; source-grounded exact facts outrank lexical keyword overlap. Tone/emotion/camera mechanism may be ambiguous. Give no credit for invented camera mechanisms.\nSource-verified interpretation boundaries: frame indexes are zero-based. Bedside lamp/bed or abstract figure/barrier readings are permitted. Dialogue bodies enlarge while prop/background do not scale, so no camera mechanism is established; unsupported camera push-in must not count as body growth. In prop-swap indexes0-1 are red and2-4 blue; generic blue is absent from allowed color_tags, so correct blue text suffices. Evidence requires2-4 grounded entries, not coverage of all5 frames. Do not invent tag requirements outside the frozen reference/enum."  # noqa: E501
    system = "You are an impartial evaluator. Return exactly a JSON object with score (number 0 to 1) and reason (string). Explain concrete mismatches against visible source facts. Do not reveal chain of thought."  # noqa: E501
    if kind == "opus":
        body = {
            "model": "claude-opus-4-6",
            "max_tokens": 8192,
            "system": system,
            "messages": [
                {"role": "user", "content": source_images(row) + [{"type": "text", "text": user}]}
            ],
            "output_config": {"format": {"type": "json_schema", "schema": JUDGE_SCHEMA}},
        }
        url = provider.ANTHROPIC_MESSAGES_URL
        headers = {
            "x-api-key": provider._require_env("ANTHROPIC_API_KEY"),
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
    else:
        raise RuntimeError("Only frozen independent Opus review is approved; Anthropic subject shares provider")
    return body, url, headers


def review(kind, row):
    name = f"judge-{kind}-{row['arm']}-{row['vars']['evaluation_id']}"
    parsed_path = OUT / f"{name}.json"
    if parsed_path.exists():
        return json.loads(parsed_path.read_text())
    body, url, headers = _review_request(kind, row)
    dump(OUT / f"{name}-request.json", {"url": url, "payload": body})
    assert count_review(body) <= 20000, "Complete Opus packet exceeds admitted bound"
    begin(name, kind)
    start = time.perf_counter()
    request = urllib.request.Request(
        url, data=json.dumps(body).encode(), headers=headers, method="POST"
    )
    raw_path = OUT / f"{name}-raw.json"
    with urllib.request.urlopen(request, timeout=60) as response:
        raw_bytes = response.read()
    raw_path.write_bytes(raw_bytes)
    raw = json.loads(raw_bytes)
    assert raw["model"] == body["model"] and raw.get("id")
    if kind == "opus":
        assert raw["stop_reason"] == "end_turn"
        text = "\n".join(x["text"] for x in raw["content"] if x["type"] == "text")
        usage = raw["usage"]
        cost = (Decimal(usage["input_tokens"]) * 5 + Decimal(usage["output_tokens"]) * 25) / 1000000
        assert not usage.get("cache_read_input_tokens", 0) and not usage.get(
            "cache_creation_input_tokens", 0
        )
    else:
        raise RuntimeError("Only frozen independent Opus review is approved; Anthropic subject shares provider")
    # Settle valid terminal usage even if judge parsing subsequently needs repair.
    settle(name, cost)
    parsed = json.loads(text)
    assert (
        isinstance(parsed["score"], (int, float))
        and 0 <= parsed["score"] <= 1
        and isinstance(parsed["reason"], str)
    )
    parsed.update(
        model=raw["model"],
        request_id=raw["id"],
        usage=usage,
        cost_usd=str(cost),
        latency_ms=round((time.perf_counter() - start) * 1000),
        raw=inventory(raw_path),
    )
    dump(parsed_path, parsed)
    for path in [parsed_path, raw_path, OUT / f"{name}-request.json"]:
        target_path = EVIDENCE / path.relative_to(OUT)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(path.read_bytes())
    print(name, "score", parsed["score"], "cost", cost, flush=True)
    return parsed


def count_review(body):
    count_body = {k: v for k, v in body.items() if k not in {"max_tokens", "output_config"}}
    # Include output schema as system text for conservative accounting of full contract.
    count_body["system"] += "\n" + json.dumps(body["output_config"])
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages/count_tokens",
        data=json.dumps(count_body).encode(),
        headers={
            "x-api-key": provider._require_env("ANTHROPIC_API_KEY"),
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as response:
        count = json.load(response)["input_tokens"]
    return count


def preflight():
    from PIL import Image

    task, prompt, configs, tests = matrix()
    assert all(
        provider._require_env(n)
        for n in ("OPENROUTER_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY")
    )
    rows = []
    for t in tests:
        for arm in configs:
            req = provider._prepare_subject_request(
                prompt, {"config": configs[arm]}, {"vars": t["vars"]}
            )
            frames = req["packet"]["frames"]
            assert len(frames) == 5 and all(
                Image.open(f["path"]).size == (640, 360) for f in frames
            )
            # Complete text/schema UTF8 upper bound; DeepSeek documented1024/image, conservative OpenAI3072/image.
            text_bound = (
                len(
                    (
                        req["user_text"]
                        + json.dumps(provider.VideoAnalysisPrediction.model_json_schema())
                    ).encode()
                )
                + 1024
            )
            bound = 106000 if arm == "fable52" else text_bound + 5 * 3072
            assert bound <= (106000 if arm == "fable52" else 26000), bound
            # Representative full saved Sol reference answer, used only for anticipated packet admission.
            synthetic = {
                "arm": arm,
                "vars": t["vars"],
                "response": {
                    "output": json.loads(
                        (
                            ROOT
                            / "docs/evals/evidence/story-226-nemotron20261016"
                            / "subject-sol-vfp_active_001.json"
                        ).read_text()
                    )["response"]["output"]
                },
            }
            body, _, _ = _review_request("opus", synthetic)
            count = count_review(body)
            # Arbitrary future answer length is unknown; exact actual full review is re-admitted before each POST.
            rows.append(
                {
                    "arm": arm,
                    "case": t["vars"]["evaluation_id"],
                    "subject_input_bound": bound,
                    "frames": [inventory(f["path"]) for f in frames],
                    "complete_saved_reference_output_judge_tokens": count,
                }
            )
    assert 6 * (RESERVE["fable52"] + RESERVE["sol"] + RESERVE["luna"]) + 18 * RESERVE["opus"] < CAP
    files = [inventory(p) for p in frozen_files()]
    if FREEZE.exists():
        check_freeze()
    else:
        dump(
            FREEZE,
            {
                "date": "2026-11-09",
                "base_git_sha": "0693227394bd9a63b1df1300070421000e0dd7b6",
                "files": files,
                "matrix": {
                    "subjects": 18,
                    "native_probes": "first scored native calls reused with offline adapter replay",
                    "judges": 18,
                    "concurrency": 1,
                    "cache": "no subject output cache; disclose provider input cache",
                    "cases": [t["vars"]["clip_id"] for t in tests],
                },
                "cap_usd": "20",
                "reservations": {k: str(v) for k, v in RESERVE.items()},
                "rendered_packets": rows,
                "review_admission": "Full source actual output counted before every judge; 20K input/8192 output .3048. Oversized actual outputs require bounded recovery/admission, never truncation.",
            },
        )
    print(
        "Zero-cost preflight rendered18 packets,5 original JPEGs each; full-source saved-reference-output review token counts:",
        [(r["arm"], r["case"], r["complete_saved_reference_output_judge_tokens"]) for r in rows],
        flush=True,
    )


def replay_parity(row):
    """Same complete native envelope through maintained call_api; no second paid call."""
    _, prompt, configs, _ = matrix()
    config = dict(configs[row["arm"]])
    config["raw_output_dir"] = str((OUT / "native" / row["arm"]).relative_to(ROOT))
    raw = json.loads((ROOT / row["response"]["raw"]["raw_envelope_path"]).read_text())
    expected = json.loads((OUT / (row["name"] + "-request.json")).read_text())
    original = provider._request_json
    def saved(url, **kwargs):
        assert {"url": url, "payload": kwargs["body"]} == expected
        return raw
    provider._request_json = saved
    try:
        replay = provider.call_api(prompt, {"config": config}, {"vars": row["vars"]})
    finally:
        provider._request_json = original
    assert not replay.get("error"), replay.get("error")
    assert replay["output"] == row["response"]["output"]
    assert replay["raw"]["model"] == row["response"]["raw"]["model"]
    dump(EVIDENCE / (row["name"] + "-parity.json"), {"same_wire_body": True, "same_output": True, "mode": "offline complete native envelope replay through maintained call_api; no extra inference"})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["preflight", "case"])
    parser.add_argument("--case")
    args = parser.parse_args()
    if args.mode == "preflight":
        preflight()
        return
    check_freeze()
    assert not RESULT.exists(), "Immutable result closes paid runner"
    _, _, _, tests = matrix()
    test = next(t for t in tests if t["vars"]["evaluation_id"] == args.case)
    for arm in ("fable52", "sol", "luna"):
        row = subject(arm, test, native=True)
        replay_parity(row)
        review("opus", row)
    dump(EVIDENCE / "ledger.json", ledger())


if __name__ == "__main__":
    main()
