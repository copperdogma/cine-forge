"""Run the existing whole-workspace control with its independent $5 physical meter."""
from __future__ import annotations

import json
import sys
from functools import partial

import run_whole_story_workspace_control as maintained
from preflight_carbon_workspace import CASES, E, dump, sha


def main():
    case = sys.argv[2] if sys.argv[1:2] == ["--case"] and len(sys.argv) == 3 else None
    if case not in CASES:
        raise SystemExit("Specify --case and a frozen case ID")
    freeze = json.loads((E / "freeze.json").read_text())
    for name, digest in freeze["files"].items():
        assert sha(maintained.ROOT / name) == digest, name
    assert not (E / "CLOSED.json").exists()
    ledger = E / "physical-calls/ledger.json"
    prior = json.loads(ledger.read_text()) if ledger.exists() else []
    assert not any(row["group"] == "control-"+case for row in prior)
    if case != CASES[0]:
        assert (E / (case+"-consumer.json")).is_file()
    dump(E / ("admit-"+case+".json"), {"control":True, "pool_usd":5})
    maintained.E = E
    maintained.PhysicalMeter = partial(maintained.PhysicalMeter, cap="5")
    maintained.main()


if __name__ == "__main__":
    main()
