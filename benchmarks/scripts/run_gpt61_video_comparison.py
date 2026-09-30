#!/usr/bin/env python3
"""Bounded fresh comparison using the maintained video adapter and v4 scorer."""

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

OUT = ROOT / "output/evals/gpt61-sol-20260929"
EVIDENCE = ROOT / "docs/evals/evidence/story-226"
FREEZE = ROOT / "docs/evals/story-226-gpt61-sol-freeze.json"
RESULT = ROOT / "benchmarks/results/video-understanding-gpt61-sol-vs-luna-v4-20260929.json"
CAP = Decimal("4")
RATES = {
    "gpt-6.1-sol": (2, 10),
    "gpt-6-luna": (0.125, 0.5),
    "claude-opus-4-6": (5, 25),

}
RESERVE = {
    "sol": Decimal(".30596"),
    "luna": Decimal(".0032"),
    "opus": Decimal(".0756"),

}
JUDGE_SCHEMA = {
    "type": "object",
    "properties": {"score": {"type": "number"}, "reason": {"type": "string"}},
    "required": ["score", "reason"],
    "additionalProperties": False,
}


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
    for arm, model in [("sol", "gpt-6.1-sol"), ("luna", "gpt-6-luna")]:
        matches = [p for p in task["providers"] if p["config"]["model"] == model]
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
            prompt, {"config": configs["sol"]}, {"vars": t["vars"]}
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
        if path == "benchmarks/scripts/run_gpt61_video_comparison.py":
            path = "docs/evals/snapshots/story-226-calltime-run_gpt61_video_comparison.py.txt"
        actual = inventory(ROOT / path)
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
    system = "You are an impartial evaluator. Return exactly a JSON object with score (number 0 to 1) and reason (string). Explain concrete mismatches against visible source facts. Do not reveal chain of thought."  # noqa: E501
    if kind == "opus":
        body = {
            "model": "claude-opus-4-6",
            "max_tokens": 1024,
            "system": system,
            "messages": [{"role": "user", "content": user}],
            "output_config": {"format": {"type": "json_schema", "schema": JUDGE_SCHEMA}},
        }
        url = provider.ANTHROPIC_MESSAGES_URL
        headers = {
            "x-api-key": provider._require_env("ANTHROPIC_API_KEY"),
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
    else:
        raise RuntimeError("Only cross-provider Opus review is approved")
    return body, url, headers


def review(kind, row):
    name = f"judge-{kind}-{row['arm']}-{row['vars']['evaluation_id']}"
    parsed_path = OUT / f"{name}.json"
    if parsed_path.exists():
        return json.loads(parsed_path.read_text())
    body, url, headers = _review_request(kind, row)
    dump(OUT / f"{name}-request.json", {"url": url, "payload": body})
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
        raise RuntimeError("Only cross-provider Opus review is approved")
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["preflight", "qualify", "subjects", "judges"])
    args = parser.parse_args()
    _, prompt, configs, tests = matrix()
    if args.mode == "preflight":
        assert provider._require_env("ANTHROPIC_API_KEY") and provider._require_env(
            "OPENAI_API_KEY"
        )
        files = [inventory(p) for p in frozen_files()]
        if FREEZE.exists():
            check_freeze()
        else:
            dump(
                FREEZE,
                {
                    "date": "2026-09-29",
                    "base_git_sha": "58a001716c2f20a07e4aefcc99d280e5a0c8bb10",
                    "files": files,
                    "matrix": {
                        "subject_models": ["gpt-6.1-sol", "gpt-6-luna"],
                        "cases": [t["vars"]["clip_id"] for t in tests],
                        "subjects": 12,
                        "native_probes": 2,
                        "judges": {"claude-opus-4-6": 12},
                        "concurrency": 1,
                        "fresh": True,
                    },
                    "reservations": {k: str(v) for k, v in RESERVE.items()},
                    "total_worst_planned_usd": "3.38048",
                    "recovery_remaining_usd": "0.61952",
                    "cap_usd": "4",
                    "input_bound": "106K input tokens per candidate including five original 640x360 JPEGs, 4096 output; Luna 20K input/1400 output; Opus text rubric 10K input/1024 output. Bound all eight possible subject calls per arm and twelve Opus judgments before dispatch.",  # noqa: E501
                },
            )
        print(
            "Zero-cost topology:",
            len(tests),
            "independent cases, 5 JPEGs each; no cache; no chained conversations. Frozen",
            len(files),
            "files",
        )
        return
    check_freeze()
    if args.mode in {"qualify", "subjects", "judges"} and RESULT.exists():
        raise RuntimeError(
            "Immutable comparison exists; paid work requires a new authorized run identity"
        )
    if args.mode == "qualify":
        for arm in ("sol", "luna"):
            subject(arm, tests[0], native=True)
            subject(arm, tests[0])
            n = json.loads(
                (OUT / f"native-{arm}-{tests[0]['vars']['evaluation_id']}-request.json").read_text()
            )
            p = json.loads(
                (
                    OUT / f"subject-{arm}-{tests[0]['vars']['evaluation_id']}-request.json"
                ).read_text()
            )
            assert n == p, "Native/parity request differs"
            print(
                arm,
                "native and maintained call_api parity complete; exact identical request",
                flush=True,
            )
    elif args.mode == "subjects":
        for test in tests:
            for arm in ("sol", "luna"):
                subject(arm, test)
    elif args.mode == "judges":
        for test in tests:
            for arm in ("sol", "luna"):
                row = json.loads(
                    (OUT / f"subject-{arm}-{test['vars']['evaluation_id']}.json").read_text()
                )
                for kind in ("opus",):
                    review(kind, row)


if __name__ == "__main__":
    main()
