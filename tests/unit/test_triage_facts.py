from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def load_module():
    path = ROOT / "scripts" / "triage_facts.py"
    spec = importlib.util.spec_from_file_location("triage_facts", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


@pytest.mark.unit
def test_collect_facts_core_cine_forge_lanes(monkeypatch):
    monkeypatch.setenv("TRIAGE_FACTS_TODAY", "2026-04-26")
    module = load_module()
    module.TODAY = module.date.fromisoformat(os.environ["TRIAGE_FACTS_TODAY"])
    expected_lanes = {
        "triage-stories",
        "triage-inbox",
        "triage-evals",
        "triage-architecture",
        "triage-health",
        "codebase-improvement-scout",
        "discover-models",
        "loop-verify",
    }

    facts = module.collect_facts()

    assert facts["repo"] == "cine-forge"
    assert set(module.LANE_SKILLS) == expected_lanes
    assert set(facts["lanes"]) == expected_lanes
    assert all(status == "present" for status in facts["lanes"].values())
    assert facts["ui_scout"]["status"] == "present"
    assert facts["architecture"]["status"] == "present"
    assert facts["methodology_tooling"]["command_alias_status"] == "absent"
    assert facts["methodology_tooling"]["missing_command_aliases"] == []
    assert facts["methodology_tooling"]["extra_command_aliases"] == []


@pytest.mark.unit
def test_cli_json_is_parseable():
    completed = subprocess.run(
        [sys.executable, "scripts/triage_facts.py", "--json"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        encoding="utf-8",
    )

    parsed = json.loads(completed.stdout)
    assert parsed["repo"] == "cine-forge"
    assert parsed["ui_scout"]["status"] == "present"
