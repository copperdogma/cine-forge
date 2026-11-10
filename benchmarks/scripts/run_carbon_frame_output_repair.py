"""One disclosed output-allowance repair for the Scout109 frame panel."""

import argparse
import fcntl
import hashlib
import json
import multiprocessing
import os
import time
import urllib.error
import urllib.request
from concurrent.futures import ProcessPoolExecutor
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import run_carbon_video_comparison as p

from cine_forge.ai.token_usage import validate_gemini_token_usage

E = p.E
FREEZE = E / "stream-preflight.json"
RESERVE = Decimal(".70736")


def repair_record(name, amount, state):
    """Reserve a distinct subpool and settle with read-under-lock and atomic replacement."""
    file = E / "ledger64.json"
    with (E / ".ledger64.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        rows = p.read(file) if file.exists() else []
        current = next((r for r in rows if r["name"] == name), None)
        if state == "reserved":
            if current:
                raise RuntimeError(f"Duplicate admission {name}")
            if sum(Decimal(r["usd"]) for r in rows) + amount > Decimal("5.0608"):
                raise RuntimeError("Streaming subject and reviewer subpool exhausted")
            rows.append(dict(name=name, state=state, usd=str(amount), reserved=str(amount)))
        else:
            if not current or current["state"] != "reserved" or amount > Decimal(current["usd"]):
                raise RuntimeError(f"Invalid settlement {name}")
            current.update(state=state, usd=str(amount))
        pending = file.with_suffix(".new")
        p.dump(pending, rows)
        os.replace(pending, file)


def wire(request):
    original = p.provider._build_gemini_payload(
        user_text=request["user_text"],
        frames=request["packet"]["frames"],
        max_tokens=65536,
        response_schema=p.provider._VIDEO_ANALYSIS_RESPONSE_SCHEMA,
    )
    original["generationConfig"]["thinkingConfig"] = {"thinkingLevel": "high"}
    return {
        "url": p.provider.GEMINI_MODELS_URL + "/gemini-4-carbon:streamGenerateContent?alt=sse",
        "payload": original,
    }


def preflight():
    assert not FREEZE.exists()
    rows = []
    for t in p.configured()[3][1:]:
        case = t["vars"]["evaluation_id"]
        orig = p.render("carbon", t)
        new = wire(p.prep("carbon", t))
        frozen = p.read(E / "wire" / f"{case}-carbon.json")
        assert orig == frozen
        expected = json.loads(json.dumps(frozen["payload"]))
        expected["generationConfig"]["maxOutputTokens"] = 65536
        assert new["payload"] == expected
        count = p.count("carbon", dict(url=orig["url"], payload=new["payload"]))
        assert count <= 26000
        rows.append(
            dict(
                case=case,
                input_count=count,
                payload_sha256=hashlib.sha256(json.dumps(new, sort_keys=True).encode()).hexdigest(),
            )
        )
        p.dump(E / "wire" / f"{case}-carbon64.json", new)
    paid = sum(Decimal(r["usd"]) for r in p.ledger())
    remaining_controls = sum(
        Decimal(r["reserved"])
        for r in p.read(p.FREEZE)["rendered"]
        if r["arm"] != "carbon" and not (E / f"{r['case']}-{r['arm']}-subject.json").exists()
    )
    remaining_reviews = 18 - len(list(E.glob("*-opus.json")))
    total = paid + 5 * RESERVE + remaining_reviews * Decimal(".3048") + remaining_controls
    assert total <= 11
    p.dump(
        FREEZE,
        dict(
            producer=p.inventory(Path(__file__)),
            rendered=rows,
            measured_inputs=(
                "Original native count 6725 vs 7534 actual billed on both genuine "
                "cases; reserve up to 26000."
            ),
            decision="Original case002 HIGH32768 emitted zero visible characters at MAX_TOKENS. "
            "Coordinator approved one HIGH65536 streaming output-allowance repair for case002 "
            "and that arm for cases004-006. Case003 raced the hold and is reused if valid. "
            "Never replay a completed 32K subject. "
            "No schema, imagery, prompt, effort, quality threshold, control or judge changes.",
            raw_custody=(
                "Complete SSE stored for native replay; settle last cumulative terminal usage once."
            ),
            reserve_each=str(RESERVE),
            future_bound_with_actuals=str(total),
            max_cases=5,
            further_output_repair=False,
            cap=11,
        ),
    )
    print("Five native payloads recounted; total cold admitted", total, flush=True)


def acquire(request, name):
    actual = wire(request)
    assert actual == p.read(E / "wire" / f"{name}.json")
    http = urllib.request.Request(
        actual["url"],
        data=json.dumps(actual["payload"]).encode(),
        headers={
            "x-goog-api-key": p.provider._require_env("GEMINI_API_KEY"),
            "Content-Type": "application/json",
        },
    )
    p.record(name, RESERVE, "reserved")
    started = time.monotonic()
    path = E / f"{name}.sse"
    try:
        with urllib.request.urlopen(http, timeout=1200) as response, path.open("xb") as f:
            for line in response:
                f.write(line)
                f.flush()
    except Exception as exc:
        detail = (
            exc.read().decode(errors="replace")
            if isinstance(exc, urllib.error.HTTPError)
            else str(exc)
        )
        p.dump(E / f"{name}-error.json", dict(error=detail, elapsed=time.monotonic() - started))
        raise
    return path, round((time.monotonic() - started) * 1000)


def decode(path):
    pieces = []
    final = None
    ids = set()
    for line in path.read_text().splitlines():
        if not line.startswith("data:"):
            continue
        data = json.loads(line[5:].strip())
        assert data.get("modelVersion") == "gemini-4-carbon" and data["responseId"]
        ids.add(data["responseId"])
        assert len(ids) == 1 and "error" not in data
        for cand in data.get("candidates", []):
            assert cand.get("index", 0) == 0 and final is None
            for part in cand.get("content", {}).get("parts", []):
                if not part.get("thought") and "text" in part:
                    pieces.append(part["text"])
            if cand.get("finishReason"):
                final = (cand["finishReason"], data)
    assert final is not None, "No terminal native finish/usage; full reservation remains"
    finish, event = final
    assert finish in ("STOP", "MAX_TOKENS")
    usage = event["usageMetadata"]
    tokens = validate_gemini_token_usage(
        prompt_tokens=usage["promptTokenCount"],
        visible_completion_tokens=usage.get("candidatesTokenCount", 0),
        total_tokens=usage["totalTokenCount"],
        reasoning_completion_tokens=usage.get("thoughtsTokenCount", 0),
    )
    cached = usage.get("cachedContentTokenCount", 0)
    assert 0 <= cached <= tokens.prompt and tokens.billed_completion <= 65536
    cost = (
        2 * (tokens.prompt - cached) + Decimal(".1") * cached + 10 * tokens.billed_completion
    ) / 1000000
    raw = {
        "modelVersion": event["modelVersion"],
        "responseId": event["responseId"],
        "finishReason": finish,
        "usageMetadata": usage,
        "raw_sse_path": str(path.relative_to(p.ROOT)),
        "raw_sse_sha256": p.inventory(path)["sha256"],
    }
    return dict(
        output="".join(pieces),
        token_usage=dict(
            prompt=tokens.prompt,
            completion=tokens.visible_completion,
            total=tokens.total,
            billed_completion=tokens.billed_completion,
            reasoning_completion=usage.get("thoughtsTokenCount", 0),
        ),
        raw=raw,
        reported_cost_usd=float(cost),
        cost_estimated=True,
    ), cost


def execute(test):
    case = test["vars"]["evaluation_id"]
    name = case + "-carbon64"
    receipt = E / f"{name}-subject.json"
    if receipt.exists():
        p.judge(p.read(receipt))
        return
    if (E / f"{name}-incomplete.json").exists():
        return
    req = p.prep("carbon", test)
    req["max_tokens"] = 65536
    path, ms = acquire(req, name)
    result, cost = decode(path)
    p.record(name, cost, "settled")
    p.dump(E / f"{name}-raw.json", result["raw"])
    if result["raw"]["finishReason"] != "STOP":
        p.dump(
            E / f"{name}-incomplete.json",
            dict(
                state="terminal-output-allowance",
                raw=result["raw"],
                elapsed_s=ms / 1000,
                cost=str(cost),
                text_bytes=len(result["output"].encode()),
                semantics="Unmeasured; no further re-inference, no judge without complete output",
            ),
        )
        print(name, "MAX_TOKENS", cost, ms / 1000, flush=True)
        return
    p.provider.VideoAnalysisPrediction.model_validate_json(result["output"])
    assert set(json.loads(result["output"])) == set(
        p.provider._VIDEO_ANALYSIS_RESPONSE_SCHEMA["required"]
    )
    response = p.provider._build_promptfoo_response(
        request=req,
        response=result,
        latency_ms=ms,
        cost_usd=float(cost),
        subject_contract_sha256=None,
    )
    _, prompt, cfg, _ = p.configured()
    config = dict(cfg["carbon"], max_tokens=65536)

    def saved(prepared):
        assert prepared["max_tokens"] == 65536 and wire(prepared) == p.read(
            E / "wire" / f"{name}.json"
        )
        return decode(path)[0]

    with patch.object(p.provider, "_dispatch_subject_request", saved):
        replay = p.provider.call_api(prompt, {"config": config}, {"vars": test["vars"]})
    assert (
        replay["output"] == response["output"]
        and replay["metadata"]["returned_model"] == "gemini-4-carbon"
    )
    row = dict(
        arm="carbon",
        vars=test["vars"],
        response=response,
        configuration="high65536",
        parity="Maintained harness builds identical wire and consumes identical native SSE replay",
        structural=p.get_assert(response["output"], {"vars": test["vars"]}),
    )
    p.dump(receipt, row)
    print(name, "settled", cost, ms / 1000, flush=True)
    p.judge(row)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["preflight", "qualify", "remaining"])
    command = parser.parse_args().mode
    if command == "preflight":
        preflight()
        return
    assert p.read(FREEZE)["producer"] == p.inventory(Path(__file__))
    assert not p.RESULT.exists()
    tests = p.configured()[3]
    if command == "qualify":
        run_locked(tests[1])
        return
    assert (E / "vfp_active_002-carbon64-subject.json").exists()
    assert len(list(E.glob("*-sol-opus.json"))) == len(list(E.glob("*-luna-opus.json"))) == 6
    eligible = [
        t
        for t in tests[2:]
        if not (E / (t["vars"]["evaluation_id"] + "-carbon-subject.json")).exists()
    ]
    with ProcessPoolExecutor(
        max_workers=2, mp_context=multiprocessing.get_context("spawn")
    ) as pool:
        list(pool.map(run_locked, eligible))


def run_locked(test):
    p.record = repair_record
    execute(test)


if __name__ == "__main__":
    main()
