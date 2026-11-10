"""Reconcile the three frozen subjects, physical control receipts, and source reviews."""

from __future__ import annotations

import argparse
import json
from decimal import Decimal

from preflight_carbon_workspace import CASES, ROOT, E, dump, sha

D = Decimal
RESULT = ROOT / "benchmarks/results/whole-story-workspace-carbon-20261110.json"


def split(rows):
    settled = sum((D(r["accounted_usd"]) for r in rows if r["state"].startswith("settled")), D(0))
    held = sum((D(r["accounted_usd"]) for r in rows if not r["state"].startswith("settled")), D(0))
    return {
        "known_usage_usd": str(settled),
        "unknown_held_usd": str(held),
        "accounted_usd": str(settled + held),
    }


def main(verify_only=False):
    decisions = json.loads((E / "source-decisions.json").read_text())
    control_rows = json.loads((E / "physical-calls/ledger.json").read_text())
    all_rows = []
    results = {}
    for case in CASES:
        path = E / ("subject-ledger.json" if case == CASES[0] else case + "-ledger.json")
        rows = json.loads(path.read_text())
        assert len(rows) <= 3 and all("elapsed_ms" in r for r in rows)
        assert D(split(rows)["accounted_usd"]) <= D("1.859936")
        all_rows.extend(rows)
        ctrl = json.loads((E / (case + "-control-result.json")).read_text())
        consumer = json.loads((E / (case + "-control-consumer.json")).read_text())
        assert len(ctrl["physical_calls"]) == sum(
            r["group"] == "control-" + case for r in control_rows
        )
        raw = E / (case + "-visible.txt")
        host = E / (case + "-host-diagnostic.json")
        smoke = E / (case + "-consumer.json")
        diagnostic = E / (
            "diagnostic-only-lf-restored-consumer.json"
            if case == CASES[0]
            else case + "-diagnostic-lf-restored-consumer.json"
        )
        data = {
            "carbon": {
                "model": "gemini-4-carbon",
                "request": "MEDIUM/131072 foreground stored native structured outer envelope",
                "native_terminal_completed": rows[-1].get("status") == "completed",
                "served_model": rows[-1].get("model"),
                "physical_sends": len(rows),
                "elapsed_attempt_ms": sum(r["elapsed_ms"] for r in rows),
                "usage_by_hop": [r.get("usage") for r in rows],
                "visible_output_sha256": sha(raw) if raw.exists() else None,
                "original_consumer_loaded": smoke.exists(),
                "source_review": decisions[case]["carbon"],
                **split(rows),
            },
            "maintained_pipeline": {
                "complete": ctrl["success"],
                "elapsed_ms": ctrl["total_elapsed_ms"],
                "physical_sends": len(ctrl["physical_calls"]),
                "groups": len(consumer["artifacts"]),
                "source_review": decisions[case]["control"],
                **split(ctrl["physical_calls"]),
            },
        }
        if host.exists():
            data["carbon"]["strict_host_diagnostic"] = json.loads(host.read_text())
        if diagnostic.exists():
            data["carbon"]["lf_only_counterfactual_groups"] = json.loads(diagnostic.read_text())[
                "artifact_groups"
            ]
        results[case] = data
    assert D(split(control_rows)["accounted_usd"]) <= 5
    totals = split(all_rows + control_rows)
    assert D(totals["accounted_usd"]) <= 16
    result = {
        "date": "2026-11-10",
        "attempt": 59,
        "base": "3b44e158a74010a68bf8d2bbe7e7a92991f96a69",
        "branch": "codex/carbon-20261110-cine-forge",
        "cases": results,
        "candidate_totals": split(all_rows),
        "control_totals": split(control_rows),
        "fresh_provider_sends": len(control_rows) + len(all_rows),
        "independent_review_external_usd": 0,
        "totals": totals,
        "hard_cap_usd": 16,
        "pricing": (
            "Current introductory USD2/M input, USD0.10/M cached and USD10/M "
            "output incl thinking; daily published Dec 1 rates double."
        ),
        "scope": (
            "Only three exposed authored synthetic screenplays; analysis, "
            "candidate recommendation and production eligibility are "
            "separate."
        ),
        "validation": (
            "Exact unmodified consumer gate, source fidelity and "
            "derivative-only LF smoke reported separately."
        ),
    }
    if verify_only:
        assert result == json.loads(RESULT.read_text()), "Committed-style result does not reconcile"
        records = json.loads((E / "manifest.json").read_text())["paths"]
        for relative, rec in records.items():
            path = ROOT / relative
            assert (
                path.is_file()
                and path.stat().st_size == rec["bytes"]
                and sha(path) == rec["sha256"]
            ), relative
        for case in CASES:
            for role in ("carbon", "control"):
                assert (E / decisions[case][role]["review"]).is_file()
        print("Verified public evidence and ledger totals without reading protected raw wire.")
    else:
        dump(RESULT, result)
    print(RESULT, totals)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    main(ap.parse_args().verify)
