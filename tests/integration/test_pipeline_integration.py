from __future__ import annotations

import json
from pathlib import Path

import pytest

from cine_forge.driver.engine import DriverEngine


@pytest.mark.integration
def test_recipe_executes_end_to_end() -> None:
    workspace_root = Path(__file__).resolve().parents[2]
    engine = DriverEngine(workspace_root=workspace_root)
    run_id = "integration-echo"
    state = engine.run(
        recipe_path=workspace_root / "configs" / "recipes" / "recipe-test-echo.yaml",
        run_id=run_id,
        force=True,
    )

    run_dir = workspace_root / "output" / "runs" / run_id
    state_path = run_dir / "run_state.json"
    events_path = run_dir / "pipeline_events.jsonl"

    assert run_dir.exists()
    assert state_path.exists()
    assert events_path.exists()
    assert state["stages"]["seed"]["status"] == "done"
    assert state["stages"]["echo"]["status"] == "done"

    run_state_data = json.loads(state_path.read_text(encoding="utf-8"))
    assert run_state_data["total_cost_usd"] >= 0.0
    assert run_state_data["stages"]["echo"]["artifact_refs"]
