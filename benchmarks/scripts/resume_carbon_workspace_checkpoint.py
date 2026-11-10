"""Resume only the frozen original interaction's saved in-progress checkpoint."""

from __future__ import annotations

import hashlib
import json
import time
import urllib.error
from decimal import Decimal
from pathlib import Path

from preflight_carbon_workspace import FIXTURES, MODEL, ROOT, E, dump, google_request, sha
from run_carbon_workspace import (
    HOP,
    LEDGER,
    ONE,
    PRIVATE,
    TOTAL,
    protected,
    read_interaction,
    settlement,
    verify,
)
from whole_story_workspace_contract import (
    consumer_smoke,
    decode_native_envelope,
    materialize_workspace,
)

CASE = "open_frequency"


def main():
    verify()
    assert not (E / "background-recovery.json").exists()
    rows = json.loads(LEDGER.read_text())
    assert len(rows) == 1 and rows[0]["state"] == "unknown-held" and rows[0]["logical"] == CASE
    original = ROOT / rows[0]["wire"]
    assert sha(original) == rows[0]["wire_sha256"]
    events = [
        json.loads(x[5:]) for x in original.read_bytes().splitlines() if x.startswith(b"data:")
    ]
    first = events[0]["interaction"]
    final = json.loads((PRIVATE / (CASE + "-hop1-get.json")).read_text())
    assert (
        final["status"] == "failed"
        and final["model"] == first["model"] == MODEL
        and final["id"] == first["id"]
    )
    assert any(x.get("code") == "DEADLINE_EXCEEDED" for x in final["errors"])
    checkpoint = events[-1]
    assert checkpoint["status"] == "in_progress" and checkpoint["interaction_id"] == final["id"]
    assert checkpoint["usage"]["total_output_tokens"] == 0 and checkpoint["continuation_token"]
    assert all(x.get("delta", {}).get("type") != "text" for x in events)
    previous, token = final["id"], checkpoint["continuation_token"]
    progress = checkpoint["usage"]["total_thought_tokens"]
    output_parts = []
    frozen = json.loads((E / (CASE + "-request.json")).read_text())
    for hop in (2, 3):
        body = dict(frozen)
        del body["input"]
        body.update(previous_interaction_id=previous, continuation_token=token)
        inputs = 26000 + min(TOTAL, (hop - 1) * HOP)
        outputs = min(HOP, TOTAL - progress)
        assert outputs > 0
        reserve = Decimal(2 * inputs + 10 * outputs) / 1_000_000
        spent = sum(Decimal(r["accounted_usd"]) for r in rows)
        assert spent + reserve <= ONE, "Next complete cold reservation exceeds logical cap"
        name = f"{CASE}-hop{hop}"
        wire = PRIVATE / (name + ".wire")
        assert not wire.exists()
        encoded = json.dumps(body, ensure_ascii=False).encode()
        with protected(PRIVATE / (name + ".request")) as f:
            f.write(encoded)
        row = {
            "logical": CASE,
            "hop": hop,
            "input_bound": inputs,
            "output_bound": outputs,
            "reserve_usd": str(reserve),
            "state": "unknown-held",
            "accounted_usd": str(reserve),
            "previous_interaction_id": previous,
            "checkpoint_token_sha256": hashlib.sha256(token.encode()).hexdigest(),
            "request_sha256": hashlib.sha256(encoded).hexdigest(),
            "wire": str(wire.relative_to(ROOT)),
            "producer_sha256": sha(Path(__file__)),
            "checkpoint_progress_tokens": progress,
        }
        rows.append(row)
        dump(LEDGER, rows)
        start = time.monotonic()
        try:
            with google_request("/interactions", body, timeout=1200) as resp:
                row["http_status"] = resp.status
                result, text = read_interaction(resp, wire)
            assert result["model"] == MODEL
            cost, produced = settlement(result["usage"], inputs, outputs)
            assert cost <= reserve
            row.update(
                state="settled",
                accounted_usd=str(cost),
                model=MODEL,
                interaction_id=result["id"],
                usage=result["usage"],
                status=result["status"],
                visible_chars=len(text),
            )
            output_parts.append(text)
            (E / (CASE + "-visible.txt")).write_text("".join(output_parts))
            if result["status"] == "completed":
                break
            assert (
                result["status"] == "requires_continuation"
                and hop < 3
                and result.get("continuation_token")
            )
            progress += produced
            previous, token = result["id"], result["continuation_token"]
        except urllib.error.HTTPError as exc:
            with protected(wire) as f:
                f.write(exc.read())
            row.update(http_status=exc.code, error_type="HTTPError")
            raise RuntimeError(f"Checkpoint resume HTTP {exc.code}. No cold replay.") from None
        finally:
            row["elapsed_ms"] = round((time.monotonic() - start) * 1000)
            if wire.exists():
                row["wire_sha256"] = sha(wire)
            dump(LEDGER, rows)
    source = FIXTURES / (CASE + ".fountain")
    bundle = decode_native_envelope(
        json.loads("".join(output_parts)),
        source_bytes=source.read_bytes(),
        source_filename=source.name,
    ).model_dump(mode="json")
    dump(E / (CASE + "-bundle.json"), bundle)
    project = ROOT / "output" / ("carbon-20261110-" + CASE)
    materialize_workspace(
        bundle,
        source_bytes=source.read_bytes(),
        project_dir=project,
        run_context={"producer": MODEL, "logical": CASE},
    )
    smoke = consumer_smoke(
        repo_root=ROOT, project_dir=project, payload=bundle, source_bytes=source.read_bytes()
    )
    dump(E / (CASE + "-consumer.json"), smoke)
    print(CASE, smoke)


if __name__ == "__main__":
    main()
