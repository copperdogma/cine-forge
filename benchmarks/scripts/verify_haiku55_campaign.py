#!/usr/bin/env python3
"""Offline proof of preserved identities, parity, bills and frozen bytes."""
import hashlib
import json
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
E = ROOT / "docs/evals/evidence/haiku55-20261007"
S = ROOT / "docs/evals/snapshots/haiku55-20261007"


def read(path):
    return json.loads(path.read_text())


def main():
    rows = read(E / "ledger.json")
    assert len(rows) == 23 and len({r["name"] for r in rows}) == 23
    assert all(r["state"] == "settled" for r in rows)
    cost = sum(Decimal(r["accounted_usd"]) for r in rows)
    assert cost <= 3
    for arm in ["medium", "luna"]:
        assert read(E / f"native-{arm}-vfp_active_001-request.json") == read(
            E / f"subject-{arm}-vfp_active_001-request.json"
        )
    assert read(E / "bible-native-medium-1-request.json") == read(
        E / "bible-subject-medium-1-request.json"
    )
    for arm in ["low", "medium", "high"]:
        expected = "disabled" if arm == "low" else "adaptive"
        for path in [
            E / f"subject-{arm}-vfp_active_001-request.json",
            E / f"bible-subject-{arm}-1-request.json",
        ]:
            request = read(path)
            body = request.get("payload", request)
            assert body["model"] == "claude-haiku-5-5"
            assert body["thinking"]["type"] == expected
            assert body["output_config"]["effort"] == arm
            assert body["output_config"]["format"]["type"] == "json_schema"
        raw = read(E / f"bible-subject-{arm}-1-raw.json")
        assert raw["model"] == "claude-haiku-5-5" and raw["stop_reason"] == "end_turn"
    for fname in ["haiku55-20261007-freeze.json", "haiku55-20261007-bible-freeze.json"]:
        for item in read(ROOT / "docs/evals" / fname)["files"]:
            path = ROOT / item["path"]
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            if actual != item["sha256"]:
                archive = S / (path.name + ".txt")
                if path.name == "run_haiku55_bible.py":
                    archive = S / "run_haiku55_bible-pre-gemini-capture.py.txt"
                assert hashlib.sha256(archive.read_bytes()).hexdigest() == item["sha256"], path
    manifest = ROOT / "docs/evals/haiku55-20261007-manifest.json"
    if manifest.exists():
        for item in read(manifest)["files"]:
            data = (ROOT / item["path"]).read_bytes()
            assert hashlib.sha256(data).hexdigest() == item["sha256"]
            assert len(data) == item["bytes"]
    print(f"Verified 23 calls, USD{cost}, strict arms, native/parity, frozen bytes")


if __name__ == "__main__":
    main()
