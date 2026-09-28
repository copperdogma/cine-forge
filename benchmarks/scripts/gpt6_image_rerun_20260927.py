#!/usr/bin/env python3
"""Fresh bounded owner six-case image comparison; unchanged subject/scoring contract."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.request
from decimal import Decimal
from pathlib import Path
from statistics import mean

import yaml

ROOT = Path(__file__).resolve().parents[2]
B = ROOT / "benchmarks"
sys.path[:0] = [str(ROOT / "src"), str(B / "providers"), str(B / "scorers"), str(B / "scripts")]
import rejudge_video_understanding_truth_v4 as oldjudge  # noqa: E402
import video_understanding_provider as provider  # noqa: E402
import video_understanding_scorer as scorer  # noqa: E402

OUT = ROOT / "output/evals/gpt6-image-rerun-20260927"
RESULT = B / "results/video-understanding-gpt6-image-rerun-20260927.json"
FREEZE = ROOT / "docs/evals/gpt6-image-rerun-20260927-freeze.json"
ARMS = {
    "sol": "GPT-6 Sol / direct Responses low",
    "luna": "GPT-6 Luna / direct Responses low",
    "gemini": "Gemini 3.5 Flash-Lite",
}
RESERVES = {
    "gpt-6-sol": Decimal(".064"),
    "gpt-6-luna": Decimal(".0032"),
    "gemini-3.5-flash-lite": Decimal(".16984"),
    "claude-opus-4-6": Decimal(".0756"),
}
CAP = Decimal("1.50")
CURRENT = None


def dump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def artifact(path):
    data = path.read_bytes()
    return {
        "path": str(path.relative_to(ROOT)),
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
    }


def ledger():
    p = OUT / "ledger.json"
    return json.loads(p.read_text()) if p.exists() else {"cap_usd": str(CAP), "entries": []}


def accounted(data):
    return sum(
        (Decimal(e.get("settled_usd", e["reserved_usd"])) for e in data["entries"]), Decimal(0)
    )


def settle(raw, model):
    if model.startswith("gpt-6-"):
        return Decimal(
            str(provider._provider_support.openai_usage_and_cost(vars(provider), raw, model)[-1])
        )
    if model.startswith("gemini"):
        u = raw["usageMetadata"]
        p, o = u["promptTokenCount"], u["candidatesTokenCount"] + u.get("thoughtsTokenCount", 0)
        if u["totalTokenCount"] != p + o or min(p, o) < 0:
            raise RuntimeError("Gemini usage does not reconcile")
        return Decimal(p) * Decimal(".00000030") + Decimal(o) * Decimal(".00000250")
    u = raw["usage"]
    p, o = u["input_tokens"], u["output_tokens"]
    read, write = u.get("cache_read_input_tokens", 0), u.get("cache_creation_input_tokens", 0)
    if any(not isinstance(x, int) or isinstance(x, bool) or x < 0 for x in (p, o, read, write)):
        raise RuntimeError("Invalid judge usage")
    return (
        Decimal(p) * Decimal(".000005")
        + Decimal(read) * Decimal(".0000005")
        + Decimal(write) * Decimal(".00000625")
        + Decimal(o) * Decimal(".000025")
    )


def guarded_http(url, *, headers, body, timeout_seconds=60, raw_output_path=None):
    model = body.get("model") or "gemini-3.5-flash-lite"
    reserve = RESERVES[model]
    data = ledger()
    if any(e["call"] == CURRENT for e in data["entries"]):
        raise RuntimeError(f"Refusing repeated dispatch identity {CURRENT}")
    if accounted(data) + reserve > CAP:
        raise RuntimeError(f"Hard cap admission blocked {CURRENT}")
    entry = {"call": CURRENT, "model": model, "reserved_usd": str(reserve), "state": "reserved"}
    data["entries"].append(entry)
    dump(OUT / "ledger.json", data)
    dump(OUT / f"{CURRENT}-request.json", body)
    path = OUT / f"{CURRENT}-raw.json"
    started = time.perf_counter()
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(), headers=headers, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as response:
            envelope = response.read()
        path.write_bytes(envelope)  # terminal bytes before parsing
        raw = json.loads(envelope)
        actual = settle(raw, model)
        if actual > reserve:
            raise RuntimeError("Usage cost exceeded request reservation")
        entry.update(
            state="settled",
            settled_usd=str(actual),
            raw=artifact(path),
            latency_ms=round((time.perf_counter() - started) * 1000),
        )
        dump(OUT / "ledger.json", data)
        if raw_output_path is not None:
            raw_output_path.parent.mkdir(parents=True, exist_ok=True)
            raw_output_path.write_bytes(envelope)
        return raw
    except urllib.error.HTTPError as exc:
        path.write_bytes(exc.read())
        entry.update(state="http-error-reservation-retained", status=exc.code, raw=artifact(path))
        dump(OUT / "ledger.json", data)
        raise RuntimeError(f"{CURRENT}: HTTP {exc.code}; raw response preserved") from None
    except Exception as exc:
        entry.update(state="unknown-reservation-retained", error=type(exc).__name__)
        dump(OUT / "ledger.json", data)
        raise


def config():
    task = yaml.safe_load((B / "tasks/video-understanding.yaml").read_text())
    providers = {}
    for arm, label in ARMS.items():
        item = next(x for x in task["providers"] if x["label"] == label)
        cfg = copy.deepcopy(item["config"])
        cfg["basePath"] = str(B / "tasks")
        cfg["raw_output_dir"] = f"output/evals/gpt6-image-rerun-20260927/{arm}"
        providers[arm] = cfg
    return task, providers


def verify_freeze():
    frozen = json.loads(FREEZE.read_text())
    for item in frozen["files"]:
        path = ROOT / item["path"]
        if item["path"] == "benchmarks/scripts/gpt6_image_rerun_20260927.py":
            path = ROOT / "docs/evals/snapshots/gpt6-image-rerun-20260927-calltime.py.txt"
        actual = artifact(path)
        if actual["sha256"] != item["sha256"] or actual["bytes"] != item["bytes"]:
            raise RuntimeError(f"Frozen contract changed: {item['path']}")


def subjects():
    global CURRENT
    task, configs = config()
    prompt = (B / "prompts/video-understanding.txt").read_text()
    provider._request_json = guarded_http
    for test in task["tests"]:
        for arm, cfg in configs.items():
            CURRENT = f"{arm}-{test['vars']['evaluation_id']}-subject"
            path = OUT / f"{CURRENT}-normalized.json"
            if path.exists():
                continue  # resume within same invocation; never reused from another run
            print("Subject", CURRENT, flush=True)
            request = provider._prepare_subject_request(
                prompt, {"config": cfg}, {"vars": test["vars"]}
            )
            started = time.perf_counter()
            normalized = provider._dispatch_subject_request(request)
            provider.VideoAnalysisPrediction.model_validate_json(normalized["output"])
            if arm == "gemini":
                raw = json.loads((OUT / f"{CURRENT}-raw.json").read_text())
                if (
                    len(raw.get("candidates", [])) != 1
                    or raw["candidates"][0].get("finishReason") != "STOP"
                ):
                    raise RuntimeError("Gemini terminal completion missing")
            # Offline parity through the maintained entrypoint, replaying its native envelope.
            original_dispatch = provider._dispatch_subject_request
            provider._dispatch_subject_request = lambda _, response=normalized: response
            try:
                parity = provider.call_api(prompt, {"config": cfg}, {"vars": test["vars"]})
                if parity.get("error") or parity["output"] != normalized["output"]:
                    raise RuntimeError("Owner entrypoint parity failed")
            finally:
                provider._dispatch_subject_request = original_dispatch
            dump(
                path,
                {
                    "arm": arm,
                    "vars": test["vars"],
                    "configuration": cfg,
                    "latency_ms": round((time.perf_counter() - started) * 1000),
                    "response": normalized,
                    "parity": parity,
                },
            )
            print("Settled", CURRENT, str(accounted(ledger())), flush=True)


def judge_messages(row):
    saved = json.loads(
        (B / "results/video-understanding-gpt6-luna-six-repaired-20260926.json").read_text()
    )
    source = copy.deepcopy(
        next(
            x for x in saved["results"]["results"] if x["vars"]["clip_id"] == row["vars"]["clip_id"]
        )
    )
    comp = source["gradingResult"]["componentResults"][1]
    messages = json.loads(comp["metadata"]["renderedGradingPrompt"])
    messages[1]["content"] = re.sub(
        r"\A<Output>\n.*?\n</Output>",
        lambda _: "<Output>\n" + row["response"]["output"] + "\n</Output>",
        messages[1]["content"],
        count=1,
        flags=re.DOTALL,
    )
    source["response"]["output"] = row["response"]["output"]
    comp["metadata"]["renderedGradingPrompt"] = json.dumps(messages)
    return oldjudge._messages(source, row["vars"]["clip_id"])


def judges():
    global CURRENT
    task, _ = config()
    for test in task["tests"]:
        for arm in ARMS:
            base = f"{arm}-{test['vars']['evaluation_id']}"
            path = OUT / f"{base}-judge-parsed.json"
            if path.exists():
                continue
            row = json.loads((OUT / f"{base}-subject-normalized.json").read_text())
            system, user = judge_messages(row)
            CURRENT = f"{base}-judge"
            print("Judge", CURRENT, flush=True)
            raw = guarded_http(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": provider._require_env("ANTHROPIC_API_KEY"),
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                body={
                    "model": oldjudge.MODEL,
                    "max_tokens": 1024,
                    "system": system,
                    "messages": [{"role": "user", "content": user}],
                },
            )
            parsed = oldjudge._parse_judge(raw)
            dump(path, parsed)
            print("Settled", CURRENT, parsed["score"], str(accounted(ledger())), flush=True)


def report():
    if RESULT.exists():
        raise RuntimeError("Refusing to overwrite the immutable paid-run result")
    task, _ = config()
    rows = []
    for test in task["tests"]:
        for arm in ARMS:
            base = f"{arm}-{test['vars']['evaluation_id']}"
            p = OUT / f"{base}-subject-normalized.json"
            if not p.exists():
                continue
            row = json.loads(p.read_text())
            structural = scorer.get_assert(
                row["response"]["output"],
                {"vars": {**test["vars"], "target_path": str(B / test["vars"]["target_path"])}},
            )
            detailed = scorer.score_output_against_target(
                output=row["response"]["output"],
                target_path=B / test["vars"]["target_path"],
                model_label=arm,
                prompt_version="video-understanding-frame-packet-v3",
                expected_clip_id=test["vars"]["evaluation_id"],
            )
            judge = json.loads((OUT / f"{base}-judge-parsed.json").read_text())
            cost = next(
                e["settled_usd"] for e in ledger()["entries"] if e["call"] == f"{base}-subject"
            )
            rows.append(
                {
                    "arm": arm,
                    "case": test["vars"]["clip_id"],
                    "evaluation_id": test["vars"]["evaluation_id"],
                    "response": row["response"],
                    "structural": structural,
                    "dimensions": detailed.model_dump(mode="json"),
                    "rubric": judge,
                    "combined": round((structural["score"] + judge["score"]) / 2, 5),
                    "case_pass": structural["pass"] and judge["pass"],
                    "latency_ms_subject": row["latency_ms"],
                    "cost_usd_subject": cost,
                }
            )
    summary = {}
    for arm in ARMS:
        own = [x for x in rows if x["arm"] == arm]
        summary[arm] = {
            "count": len(own),
            "combined": round(mean(x["combined"] for x in own), 4),
            "deterministic": round(mean(x["structural"]["score"] for x in own), 4),
            "rubric": round(mean(x["rubric"]["score"] for x in own), 4),
            "passes": sum(x["case_pass"] for x in own),
            "latency_ms_mean_subject": round(mean(x["latency_ms_subject"] for x in own)),
            "cost_usd_mean_subject": str(
                sum((Decimal(x["cost_usd_subject"]) for x in own), Decimal(0)) / len(own)
            ),
        }
    dump(
        RESULT,
        {
            "date": "2026-09-27",
            "kind": "fresh-subjects-v4-six-case-low-reasoning-image-rerun",
            "code_sha": "f4a0dec",
            "freeze": artifact(FREEZE),
            "summary": summary,
            "rows": rows,
            "ledger": ledger(),
            "known_plus_reserved_usd": str(accounted(ledger())),
            "raw_manifest": [artifact(p) for p in sorted(OUT.glob("*.json"))],
        },
    )
    print(json.dumps(summary, indent=2))
    print("All providers known+reserved USD", str(accounted(ledger())))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["preflight", "subjects", "judges", "report"])
    args = parser.parse_args()
    if args.mode in {"subjects", "judges"} and RESULT.exists():
        raise RuntimeError("Completed run cannot dispatch paid calls again")
    if args.mode == "preflight":
        if FREEZE.exists():
            raise RuntimeError("Refusing to overwrite the immutable call-time freeze")
        task, configs = config()
        assert len(task["tests"]) == 6 and len(configs) == 3
        paths = [
            Path(__file__),
            B / "tasks/video-understanding.yaml",
            B / "prompts/video-understanding.txt",
            B / "video_understanding_truth_v4/manifest.json",
        ]
        paths.extend((B / "providers").glob("video_understanding*.py"))
        paths.extend((B / "scorers").glob("video_understanding*.py"))
        paths.extend((B / "video_understanding_truth_v4").glob("*/target.*"))
        paths.extend(
            [
                B / "scripts/rejudge_video_understanding_truth_v4.py",
                B / "results/video-understanding-gpt6-luna-six-repaired-20260926.json",
            ]
        )
        paths.extend((ROOT / "src/cine_forge/schemas").glob("*video*.py"))
        for test in task["tests"]:
            request = provider._prepare_subject_request(
                (B / "prompts/video-understanding.txt").read_text(),
                {"config": configs["sol"]},
                {"vars": test["vars"]},
            )
            paths.extend(x["path"] for x in request["packet"]["frames"])
            assert len(request["packet"]["frames"]) == 5
        dump(
            FREEZE,
            {
                "base_sha": "f4a0dec",
                "date": "2026-09-27",
                "cap_usd": str(CAP),
                "reservations": {k: str(v) for k, v in RESERVES.items()},
                "files": [artifact(p) for p in sorted(set(paths))],
                "configs": configs,
                "cases": [x["vars"] for x in task["tests"]],
                "cache": "fresh-no-subject-reuse",
                "concurrency": 1,
                "image_detail": "high for both OpenAI arms; unchanged Gemini inline_data defaults",
                "pricing_source_date": "2026-09-27",
                "bug_fix_status": "user-reported-unverified",
            },
        )
        print(
            "Frozen 6x3 subjects +18 independent Opus4.6 judges, reservations enforced; "
            "no SDK/automatic retries."
        )
        return
    verify_freeze()
    OUT.mkdir(parents=True, exist_ok=True)
    {"subjects": subjects, "judges": judges, "report": report}[args.mode]()


if __name__ == "__main__":
    main()
