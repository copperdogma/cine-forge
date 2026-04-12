from __future__ import annotations

import json
from pathlib import Path

import pytest

from cine_forge.driver.engine import DriverEngine


@pytest.mark.unit
def test_write_run_state_replaces_file_without_leaving_temp_sidecar(tmp_path: Path) -> None:
    state_path = tmp_path / "output" / "runs" / "run-atomic" / "run_state.json"

    DriverEngine._write_run_state(
        state_path,
        {
            "run_id": "run-atomic",
            "recipe_id": "test_recipe",
            "dry_run": False,
            "started_at": 1.0,
            "stages": {
                "render": {
                    "status": "running",
                    "model_used": None,
                    "call_count": 0,
                    "attempt_count": 0,
                    "attempts": [],
                    "final_error_class": None,
                    "artifact_refs": [],
                    "duration_seconds": 0.0,
                    "cost_usd": 0.0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "started_at": 1.0,
                    "pause_reason": None,
                }
            },
            "runtime_params": {},
            "total_cost_usd": 0.0,
            "project_cost_baseline_usd": 0.0,
            "budget_warning_scopes": [],
            "stage_order": ["render"],
            "instrumented": False,
            "finished_at": None,
        },
    )

    persisted = json.loads(state_path.read_text(encoding="utf-8"))
    assert persisted["run_id"] == "run-atomic"
    assert persisted["stages"]["render"]["status"] == "running"
    assert not state_path.with_name(".run_state.json.tmp").exists()
