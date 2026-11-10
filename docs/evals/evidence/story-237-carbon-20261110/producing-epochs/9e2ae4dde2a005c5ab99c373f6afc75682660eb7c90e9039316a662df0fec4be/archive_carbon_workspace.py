"""Preserve source-reviewable public wires alongside hashes for protected native state."""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

from preflight_carbon_workspace import CASES, E, ROOT, dump, sha


def public_fields(value):
    if isinstance(value, list):
        return [public_fields(item) for item in value]
    if not isinstance(value, dict):
        return value
    result = {}
    for key, item in value.items():
        if isinstance(item,str) and key in {"continuation_token","signature","thought_signature"}:
            result[key] = {"redacted_bytes":len(item.encode()),"sha256":hashlib.sha256(item.encode()).hexdigest()}
        else:
            result[key] = public_fields(item)
    return result


def archive():
    ledgers = [E/"subject-ledger.json", *(E/(c+"-ledger.json") for c in CASES[1:])]
    rows = [r for path in ledgers for r in json.loads(path.read_text())]
    for row in rows:
        assert "elapsed_ms" in row, "inference still running"
        raw=ROOT/row["wire"]
        assert sha(raw)==row["wire_sha256"]
        outgoing=raw.with_suffix(".request")
        assert sha(outgoing)==row["request_sha256"]
        dest=E/"native-wire"
        dest.mkdir(exist_ok=True)
        dump(dest/(raw.stem+"-request.json"), public_fields(json.loads(outgoing.read_bytes())))
        try:
            envelope=json.loads(raw.read_bytes())
            events=[public_fields(envelope)]
        except ValueError:
            events=[]
            for line in raw.read_bytes().splitlines():
                if line.startswith(b"data:") and line[5:].strip() not in (b"",b"[DONE]"):
                    events.append(public_fields(json.loads(line[5:].strip())))
        safe=b"".join((json.dumps(e,ensure_ascii=False,separators=(",",":"))+"\n").encode() for e in events)
        (dest/(raw.stem+"-events.jsonl.gz")).write_bytes(gzip.compress(safe,mtime=0))
        related=raw.with_suffix(".get.json")
        if related.exists():
            dump(dest/(raw.stem+"-original-stored-get.json"),public_fields(json.loads(related.read_bytes())))
    paths=sorted(p for p in E.rglob("*") if p.is_file() and p.name!="manifest.json")
    scripts=[ROOT/"benchmarks/scripts"/(name+".py") for name in ["archive_carbon_workspace",
             "blind_carbon_workspace_review","preflight_carbon_workspace","run_carbon_workspace",
             "run_carbon_workspace_control","resume_carbon_workspace_checkpoint",
             "run_carbon_workspace_variants","diagnose_carbon_workspace","report_carbon_workspace"]]
    reports=[ROOT/"benchmarks/results/whole-story-workspace-carbon-20261110.json",
             ROOT/"docs/evals/attempts/059-carbon-whole-story-workspace.md",
             ROOT/"docs/stories/story-237-whole-story-workspace-capability.md"]
    dump(E/"manifest.json",{"paths":{str(p.relative_to(ROOT)): {"sha256":sha(p),"bytes":p.stat().st_size}
                                    for p in paths+scripts+reports},
                            "protected_wires":"Exact bytes indexed by native ledger; neutralized native events preserved here"})


if __name__ == "__main__":
    archive()
