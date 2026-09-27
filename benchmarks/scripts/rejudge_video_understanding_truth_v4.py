#!/usr/bin/env python3
"""Rejudge saved v3 subject outputs against frozen v4 source references."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import urllib.request
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BENCHMARKS = ROOT / "benchmarks"
FREEZE = ROOT / "docs/evals/story-222-truth-v4-freeze.json"
OUT = ROOT / "output/evals/gpt6-sol-luna-20260926/truth-v4-judge"
MODEL = "claude-opus-4-6"
CALL_TIME_ARCHIVES = {
    "benchmarks/scripts/build_video_understanding_truth_v4.py": (
        "docs/evals/snapshots/story-222-v4-calltime-overlay-builder.py.txt"
    ),
    "benchmarks/scripts/rejudge_video_understanding_truth_v4.py": (
        "docs/evals/snapshots/story-222-v4-calltime-judge-runner.py.txt"
    ),
}
CASES = (
    "dialogue_confession_push_in",
    "quiet_bedside_vigil",
    "rooftop_escape_crash_zoom",
)
RESULTS = {
    "luna": BENCHMARKS / "results/video-understanding-gpt6-luna-six-repaired-20260926.json",
    "gemini": BENCHMARKS
    / "results/video-understanding-gemini35-lite-six-gpt6-control-20260926.json",
}
RESERVE_USD = Decimal("0.0756")
PRIOR_SPEND_USD = Decimal("0.390639095")
CAMPAIGN_CAP_USD = Decimal("1.50")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _check_freeze() -> dict:
    freeze = json.loads(FREEZE.read_text())
    for item in [*freeze["candidate_results"], *freeze["frozen_contract_files"]]:
        path = ROOT / CALL_TIME_ARCHIVES.get(item["path"], item["path"])
        if path.stat().st_size != item["bytes"] or _sha(path) != item["sha256"]:
            raise RuntimeError(f"Frozen file changed: {item['path']}")
    return freeze


def _saved_rows() -> dict[tuple[str, str], dict]:
    rows = {}
    for arm, path in RESULTS.items():
        result = json.loads(path.read_text())
        for row in result["results"]["results"]:
            rows[(arm, row["vars"]["clip_id"])] = row
    return rows


def _messages(row: dict, case: str) -> tuple[str, str]:
    component = row["gradingResult"]["componentResults"][1]
    metadata = component["metadata"]
    old_rubric = metadata["renderedAssertionValue"]
    template = component["assertion"]["value"]
    if template.count("{{target_markdown}}") != 1:
        raise RuntimeError("Rubric reference insertion is not unique")
    target = (BENCHMARKS / "video_understanding_truth_v4" / case / "target.md").read_text()
    rubric = template.replace("{{target_markdown}}", target)
    old_messages = json.loads(metadata["renderedGradingPrompt"])
    if [part["role"] for part in old_messages] != ["system", "user"]:
        raise RuntimeError("Unexpected saved judge message roles")
    system, user = (part["content"] for part in old_messages)
    if user.count(old_rubric) != 1:
        raise RuntimeError("Saved judge rubric is not unique")
    output_match = re.search(r"\A<Output>\n(.*?)\n</Output>", user, re.DOTALL)
    if output_match is None:
        raise RuntimeError("Saved judge prompt lacks a unique output section")
    if json.loads(output_match.group(1)) != json.loads(row["response"]["output"]):
        raise RuntimeError("Saved judge prompt changed the subject output semantics")
    return system, user.replace(old_rubric, rubric)


def _parse_judge(raw: dict) -> dict:
    if raw.get("model") != MODEL or raw.get("stop_reason") != "end_turn":
        raise RuntimeError("Judge identity or terminal status mismatch")
    blocks = raw.get("content", [])
    if len(blocks) != 1 or blocks[0].get("type") != "text":
        raise RuntimeError("Judge returned unexpected content blocks")
    text = blocks[0]["text"].strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        candidates = list(re.finditer(r"\{", text))
        data = None
        for match in reversed(candidates):
            try:
                parsed, end = json.JSONDecoder().raw_decode(text[match.start() :])
            except json.JSONDecodeError:
                continue
            if not text[match.start() + end :].strip():
                data = parsed
                break
        if data is None:
            raise RuntimeError("Saved judge output has no terminal JSON object") from None
    if not isinstance(data, dict) or not isinstance(data.get("reason"), str):
        raise RuntimeError("Judge output lacks reason or object structure")
    score = data.get("score")
    if isinstance(score, bool) or not isinstance(score, (int, float)) or not 0 <= score <= 1:
        raise RuntimeError("Judge output lacks numeric 0..1 score")
    usage = raw["usage"]
    input_tokens = usage["input_tokens"]
    output_tokens = usage["output_tokens"]
    if any(
        isinstance(x, bool) or not isinstance(x, int) or x < 0
        for x in (input_tokens, output_tokens)
    ):
        raise RuntimeError("Invalid judge usage")
    cost = Decimal(input_tokens) * Decimal("0.000005") + Decimal(output_tokens) * Decimal(
        "0.000025"
    )
    return {
        "score": score,
        "pass": bool(score >= 0.8),
        "reason": data["reason"],
        "judge_id": raw.get("id"),
        "returned_model": raw["model"],
        "stop_reason": raw["stop_reason"],
        "usage": {"input_tokens": input_tokens, "output_tokens": output_tokens},
        "cost_estimated_usd": str(cost),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight", action="store_true")
    mode.add_argument("--run", action="store_true")
    args = parser.parse_args()
    _check_freeze()
    rows = _saved_rows()
    matrix = [(case, arm, rows[(arm, case)]) for case in CASES for arm in ("luna", "gemini")]
    prompts = [(case, arm, *_messages(row, case)) for case, arm, row in matrix]
    print(
        f"Frozen judge matrix: {len(prompts)} saved outputs; {MODEL}; max 1024 output; no retries"
    )
    if args.preflight:
        for case, arm, system, user in prompts:
            print(
                case,
                arm,
                len(system),
                len(user),
                "cached" if (OUT / f"{case}-{arm}-raw.json").exists() else "new",
            )
        return
    OUT.mkdir(parents=True, exist_ok=True)
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY absent from owner wrapper")
    charged = Decimal("0")
    for case, arm, system, user in prompts:
        path = OUT / f"{case}-{arm}-raw.json"
        if path.exists():
            raw = json.loads(path.read_text())
        else:
            if PRIOR_SPEND_USD + charged + RESERVE_USD > CAMPAIGN_CAP_USD:
                raise RuntimeError("Next judge reservation exceeds campaign ceiling")
            print("Calling", case, arm, flush=True)
            request = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data=json.dumps(
                    {
                        "model": MODEL,
                        "max_tokens": 1024,
                        "system": system,
                        "messages": [{"role": "user", "content": user}],
                    }
                ).encode(),
                headers={
                    "x-api-key": key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=60) as response:
                envelope = response.read()
            path.write_bytes(envelope)
            raw = json.loads(envelope)
        parsed = _parse_judge(raw)
        charged += Decimal(parsed["cost_estimated_usd"])
        print(case, arm, parsed["score"], parsed["cost_estimated_usd"], _sha(path), flush=True)
    print("incremental_estimated_usd", charged)
    print("campaign_accounted_usd", PRIOR_SPEND_USD + charged)


if __name__ == "__main__":
    main()
