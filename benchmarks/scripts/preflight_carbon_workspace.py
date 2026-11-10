"""Qualify the frozen screenplay, transport projection and real workspace consumers."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

from run_whole_story_workspace import CASES, FIXTURES, ROOT, dump, request_body
from whole_story_workspace_contract import (
    NativeWorkspaceEnvelope,
    consumer_smoke,
    decode_native_envelope,
    materialize_workspace,
    subject_payload,
)

from cine_forge.env import require_env

E = ROOT / "docs/evals/evidence/story-237-carbon-20261110"
MODEL = "gemini-4-carbon"
BASE = "https://generativelanguage.googleapis.com/v1beta"
FORMAT = {
    "type": "text",
    "mime_type": "application/json",
    "schema": NativeWorkspaceEnvelope.model_json_schema(),
}


def body(case):
    return {
        "model": MODEL,
        "input": request_body(case)["messages"][0]["content"],
        "response_format": FORMAT,
        "generation_config": {"thinking_level": "medium", "max_output_tokens": 131072},
        "stream": True,
        "store": True,
    }


def google_request(endpoint, payload=None, timeout=60):
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode()
    return urllib.request.urlopen(
        urllib.request.Request(
            BASE + endpoint,
            data=data,
            headers={
                "x-goog-api-key": require_env("GEMINI_API_KEY"),
                "Content-Type": "application/json",
                "Api-Revision": "2026-05-20",
            },
        ),
        timeout=timeout,
    )


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def preflight():
    prior = json.loads((FIXTURES / "freeze.json").read_text())
    for f in prior["files"]:
        assert sha(FIXTURES / f["path"]) == f["sha256"]
    E.mkdir(parents=True, exist_ok=True)
    assert shutil.disk_usage(E).free > 512 * 1024**2
    original = json.loads((FIXTURES / "open_frequency-consumer-example.json").read_text())
    source = FIXTURES / "open_frequency.fountain"
    encoded = json.dumps(
        {
            "bundle_json": json.dumps(
                subject_payload(original), ensure_ascii=False, separators=(",", ":")
            )
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )
    decoded = decode_native_envelope(
        json.loads(encoded), source_bytes=source.read_bytes(), source_filename=source.name
    ).model_dump(mode="json")
    assert decoded == original
    local = ROOT / "output/carbon-20261110-mechanical-open-frequency"
    if not local.exists():
        materialize_workspace(
            decoded,
            source_bytes=source.read_bytes(),
            project_dir=local,
            run_context={"producer": "frozen mechanical exemplar only"},
        )
    smoke = consumer_smoke(
        repo_root=ROOT, project_dir=local, payload=decoded, source_bytes=source.read_bytes()
    )
    dump(E / "mechanical-consumer.json", smoke)
    inputs = {"mechanical-exemplar": encoded}
    for case in CASES:
        value = body(case)
        dump(E / (case + "-request.json"), value)
        inputs[case] = value["input"] + "\n" + json.dumps(value["response_format"])
    counts = {}
    for case, text in inputs.items():
        with google_request(
            "/models/" + MODEL + ":countTokens", {"contents": [{"parts": [{"text": text}]}]}
        ) as resp:
            counts[case] = json.load(resp)
        n = counts[case]["totalTokens"]
        if case == "mechanical-exemplar":
            assert n < 65536
        else:
            assert n + 2048 <= 26000
    dump(E / "native-counts.json", counts)
    producer_files = [
        Path(__file__).resolve(),
        ROOT / "benchmarks/scripts/run_carbon_workspace.py",
        ROOT / "benchmarks/scripts/run_whole_story_workspace.py",
        ROOT / "benchmarks/scripts/run_whole_story_workspace_control.py",
        ROOT / "benchmarks/scripts/full_script_throughput_eval.py",
        ROOT / "benchmarks/scripts/full_script_throughput_support.py",
        ROOT / "benchmarks/scripts/whole_story_workspace_control_meter.py",
        ROOT / "benchmarks/scripts/whole_story_workspace_meter.py",
        ROOT / "benchmarks/scripts/whole_story_workspace_contract.py",
        ROOT / "configs/recipes/recipe-world-building.yaml",
        ROOT / "configs/recipes/recipe-mvp-ingest.yaml",
    ]
    files = producer_files + sorted(FIXTURES.glob("*")) + sorted(E.glob("*-request.json"))
    dump(
        E / "freeze.json",
        {
            "base": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            "files": {str(p.relative_to(ROOT)): sha(p) for p in files if p.is_file()},
            "order": CASES,
            "counts": counts,
            "source_class": "owner-authored synthetic only",
            "native_enforcement": (
                "outer required bundle_json string, full maintained host schema after decoding"
            ),
            "qualified_hops": (
                "foreground streaming REST, stored only for linked "
                "continuation/retrieval, no semantic followup"
            ),
            "subject": {
                "max_hops": 3,
                "max_output_tokens": 131072,
                "thinking_level": "medium",
                "max_logicals": 4,
                "max_per_usd": 1.859936,
                "pool_usd": 7.439744,
            },
            "control": {
                "fresh": True,
                "changed_settings": False,
                "pool_usd": 5,
                "meter": (
                    "per physical request inclusive inner retries, cache writes and escalation"
                ),
                "topology_source": (
                    "configs/recipes/recipe-mvp-ingest.yaml + recipe-world-"
                    "building.yaml, runtime discovery Haiku"
                ),
            },
            "independent_review": (
                "Complete original source and neutral candidate outputs, offline, capped USD2"
            ),
            "contingency_usd": 1.560256,
            "hard_usd": 16,
        },
    )
    print({k: v["totalTokens"] for k, v in counts.items()})
    print({k: v for k, v in smoke.items() if isinstance(v, (str, int, bool))})


if __name__ == "__main__":
    try:
        preflight()
    except urllib.error.HTTPError as exc:
        dump(
            E / "preflight-http-error.json",
            {
                "status": exc.code,
                "error": exc.read()
                .decode()[:4096]
                .replace(require_env("GEMINI_API_KEY"), "[redacted]"),
            },
        )
        sys.exit(f"Native preflight HTTP {exc.code}, see sanitized evidence")
