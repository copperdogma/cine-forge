"""Execute only a frozen whole-workspace arm, pricing physical hops before dispatch."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
import urllib.error
from decimal import Decimal

from preflight_carbon_workspace import CASES, FIXTURES, MODEL, ROOT, E, dump, google_request, sha
from whole_story_workspace_contract import (
    consumer_smoke,
    decode_native_envelope,
    materialize_workspace,
)

LEDGER = E / "subject-ledger.json"
PRIVATE = ROOT / "output/carbon-20261110-private-wire"
USD = Decimal
HOP = 65536
TOTAL = 131072
ONE = USD("1.859936")
POOL = ONE * 4


def protected(path, mode="wb"):
    return open(path, mode, opener=lambda fn, flags: os.open(fn, flags, 0o600))


def verify():
    assert not (E / "CLOSED.json").exists()
    for name, expected in json.loads((E / "freeze.json").read_text())["files"].items():
        assert sha(ROOT / name) == expected, name


def settlement(usage, inputs, outputs):
    def n(key, optional=False):
        number = usage.get(key, 0 if optional else None)
        assert type(number) is int and number >= 0, key
        return number

    i, c = n("total_input_tokens"), n("total_cached_tokens", True)
    v, t = n("total_output_tokens"), n("total_thought_tokens", True)
    assert i > 0 and c <= i <= inputs and 0 < v + t <= outputs
    assert n("total_tokens") == i + v + t
    return ((i - c) * 2 + c * USD(".1") + (v + t) * 10) / 1_000_000, v + t


def read_interaction(resp, raw_path):
    content_type = resp.headers.get("Content-Type", "")
    text, model, identity, terminal, steps = [], None, None, None, {}
    with protected(raw_path) as wire:
        if "application/json" in content_type:
            raw = resp.read()
            wire.write(raw)
            result = json.loads(raw)
            return result, "".join(
                p["text"]
                for s in result.get("steps", [])
                if s["type"] == "model_output"
                for p in s.get("content", [])
                if p["type"] == "text"
            )
        assert "text/event-stream" in content_type, content_type
        for line in resp:
            wire.write(line)
            wire.flush()
            if not line.startswith(b"data:") or line[5:].strip() in (b"", b"[DONE]"):
                continue
            event = json.loads(line[5:].strip())
            kind = event.get("event_type")
            if kind == "interaction.created":
                model, identity = event["interaction"]["model"], event["interaction"]["id"]
            elif kind == "step.start":
                steps[event["index"]] = event["step"]["type"]
            elif kind == "step.delta" and event["delta"]["type"] == "text":
                assert steps.get(event["index"]) == "model_output"
                text.append(event["delta"]["text"])
            elif kind == "interaction.completed":
                assert terminal is None
                terminal = event["interaction"]
            elif kind == "error":
                raise RuntimeError("provider returned stream error; retained full wire")
    assert terminal and terminal["id"] == identity and model == MODEL, (
        "terminal or served ID missing"
    )
    terminal.setdefault("model", model)
    return terminal, "".join(text)


def subject(case, recovery):
    verify()
    frozen = json.loads((E / (case + "-request.json")).read_text())
    rows = json.loads(LEDGER.read_text()) if LEDGER.exists() else []
    logical = case + ("-operational-recovery" if recovery else "")
    assert logical not in {r["logical"] for r in rows}
    if recovery:
        assert any(r["logical"] == case for r in rows)
        assert not any(r["logical"].endswith("recovery") for r in rows)
    order = list(CASES)
    if case != order[0]:
        assert (E / (order[0] + "-consumer.json")).exists(), "first subject must qualify first"
    assert len({r["logical"] for r in rows}) < 4
    assert sum(USD(r["accounted_usd"]) for r in rows) + ONE <= POOL
    PRIVATE.mkdir(parents=True, exist_ok=True, mode=0o700)
    used, previous, token, parts = 0, None, None, []
    for hop in range(1, 4):
        outgoing = dict(frozen)
        if previous:
            outgoing.pop("input")
            outgoing.update(previous_interaction_id=previous, continuation_token=token)
        inputs, outputs = 26000 + used, min(HOP, TOTAL - used)
        assert outputs > 0
        reserve = USD(2 * inputs + 10 * outputs) / 1_000_000
        assert (
            sum(USD(r["accounted_usd"]) for r in rows if r["logical"] == logical) + reserve <= ONE
        )
        name = f"{logical}-hop{hop}"
        path = PRIVATE / (name + ".wire")
        assert not path.exists()
        wire_body = json.dumps(outgoing, ensure_ascii=False).encode()
        row = {
            "logical": logical,
            "hop": hop,
            "input_bound": inputs,
            "output_bound": outputs,
            "reserve_usd": str(reserve),
            "accounted_usd": str(reserve),
            "state": "unknown-held",
            "request_sha256": hashlib.sha256(wire_body).hexdigest(),
            "wire": str(path.relative_to(ROOT)),
        }
        rows.append(row)
        dump(LEDGER, rows)
        with protected(PRIVATE / (name + ".request")) as f:
            f.write(wire_body)
        start = time.monotonic()
        try:
            with google_request("/interactions", outgoing, timeout=1200) as resp:
                row["http_status"] = resp.status
                terminal, text = read_interaction(resp, path)
            assert terminal["model"] == MODEL and terminal.get("id"), "served model or ID missing"
            usage, status = terminal["usage"], terminal["status"]
            cost, produced = settlement(usage, inputs, outputs)
            assert cost <= reserve
            row.update(
                state="settled",
                accounted_usd=str(cost),
                model=terminal["model"],
                usage=usage,
                status=status,
                interaction_id=terminal["id"],
                visible_chars=len(text),
            )
            used += produced
            parts.append(text)
            (E / (logical + "-visible.txt")).write_text("".join(parts))
            if status == "completed":
                break
            if status != "requires_continuation" or used >= TOTAL or hop == 3:
                raise RuntimeError(
                    f"Logical inference ended with status {status} after {hop} hop(s)"
                )
            previous, token = terminal["id"], terminal["continuation_token"]
            assert previous and token
        except urllib.error.HTTPError as exc:
            raw = exc.read()
            with protected(path) as f:
                f.write(raw)
            row.update(http_status=exc.code, error_type="HTTPError")
            raise RuntimeError(f"HTTP {exc.code}; quarantined raw, exposure held") from None
        finally:
            row["elapsed_ms"] = round((time.monotonic() - start) * 1000)
            if path.is_file():
                row["wire_sha256"] = sha(path)
            dump(LEDGER, rows)
    source = FIXTURES / (case + ".fountain")
    result = decode_native_envelope(
        json.loads("".join(parts)), source_bytes=source.read_bytes(), source_filename=source.name
    ).model_dump(mode="json")
    dump(E / (case + "-bundle.json"), result)
    project = ROOT / "output" / ("carbon-20261110-" + case)
    materialize_workspace(
        result,
        source_bytes=source.read_bytes(),
        project_dir=project,
        run_context={"producer": MODEL, "logical": logical},
    )
    smoke = consumer_smoke(
        repo_root=ROOT, project_dir=project, payload=result, source_bytes=source.read_bytes()
    )
    dump(E / (case + "-consumer.json"), smoke)
    print(case, smoke)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("case", choices=CASES)
    parser.add_argument("--operational-recovery", action="store_true")
    args = parser.parse_args()
    subject(args.case, args.operational_recovery)
