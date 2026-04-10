from __future__ import annotations

import json
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from cine_forge.api.app import create_app
from cine_forge.driver.engine import DriverEngine


def _write_budget_pause_module(workspace_root: Path) -> None:
    module_dir = workspace_root / "src" / "cine_forge" / "modules" / "test" / "budget_pause_v1"
    module_dir.mkdir(parents=True, exist_ok=True)
    (module_dir / "module.yaml").write_text(
        "\n".join(
            [
                "module_id: test.budget_pause_v1",
                "stage: test",
                "description: budget pause module",
                "input_schemas: []",
                "output_schemas:",
                "  - dict",
                "parameters: {}",
            ]
        ),
        encoding="utf-8",
    )
    (module_dir / "main.py").write_text(
        "\n".join(
            [
                "def run_module(inputs, params, context):",
                "    del inputs, context",
                "    entity_id = params.get('entity_id', 'project')",
                "    return {",
                "        'artifacts': [{",
                "            'artifact_type': 'dict',",
                "            'entity_id': entity_id,",
                "            'data': {'entity_id': entity_id},",
                "            'metadata': {",
                "                'lineage': [],",
                "                'intent': 'integration budget pause',",
                "                'rationale': 'test budget cap pause behavior',",
                "                'confidence': 1.0,",
                "                'source': 'human',",
                "            },",
                "        }],",
                "        'cost': {",
                "            'model': params.get('model', 'fixture'),",
                "            'input_tokens': 10,",
                "            'output_tokens': 5,",
                "            'estimated_cost_usd': 1.1,",
                "        },",
                "    }",
            ]
        ),
        encoding="utf-8",
    )


def _write_budget_pause_recipe(workspace_root: Path) -> Path:
    recipe_dir = workspace_root / "configs" / "recipes"
    recipe_dir.mkdir(parents=True, exist_ok=True)
    recipe_path = recipe_dir / "recipe-budget-pause.yaml"
    recipe_path.write_text(
        "\n".join(
            [
                "recipe_id: budget-pause",
                "description: integration test for budget pause",
                "stages:",
                "  - id: spend",
                "    module: test.budget_pause_v1",
                "    params:",
                "      entity_id: spend",
                "      model: fixture",
                "    needs: []",
                "  - id: downstream",
                "    module: test.budget_pause_v1",
                "    params:",
                "      entity_id: downstream",
                "      model: fixture",
                "    needs: [spend]",
            ]
        ),
        encoding="utf-8",
    )
    return recipe_path


def _make_client(workspace_root: Path) -> TestClient:
    return TestClient(create_app(workspace_root=workspace_root))


def _create_project(client: TestClient, project_path: Path) -> str:
    response = client.post("/api/projects/new", json={"project_path": str(project_path)})
    assert response.status_code == 200
    return response.json()["project_id"]


def _await_run_terminal_state(
    client: TestClient,
    run_id: str,
    *,
    timeout_seconds: float = 10.0,
) -> dict[str, object]:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        response = client.get(f"/api/runs/{run_id}/state")
        if response.status_code != 200:
            time.sleep(0.05)
            continue

        payload = response.json()
        background_error = payload.get("background_error")
        if background_error:
            raise AssertionError(f"Run {run_id} failed: {background_error}")

        stages = payload["state"].get("stages", {})
        statuses = {stage["status"] for stage in stages.values()}
        if "failed" in statuses:
            raise AssertionError(f"Run {run_id} failed with statuses={statuses}")
        if "paused" in statuses:
            return payload
        if (
            statuses
            and statuses <= {"done", "skipped_reused"}
            and payload["state"].get("finished_at")
        ):
            return payload

        time.sleep(0.05)

    raise AssertionError(f"Timed out waiting for run '{run_id}'")


@pytest.mark.integration
def test_pipeline_pauses_cleanly_when_run_budget_cap_is_reached(tmp_path: Path) -> None:
    _write_budget_pause_module(tmp_path)
    recipe_path = _write_budget_pause_recipe(tmp_path)
    engine = DriverEngine(workspace_root=tmp_path)

    state = engine.run(
        recipe_path=recipe_path,
        run_id="integration-budget-pause",
        runtime_params={
            "default_model": "fixture",
            "run_budget_limit_usd": 1.0,
            "budget_warning_threshold_ratio": 0.8,
        },
    )

    assert state["stages"]["spend"]["status"] == "done"
    assert state["stages"]["downstream"]["status"] == "paused"
    assert "budget" in state["stages"]["downstream"]["pause_reason"].lower()
    assert state["total_cost_usd"] == pytest.approx(1.1)

    run_dir = tmp_path / "output" / "runs" / "integration-budget-pause"
    events_path = run_dir / "pipeline_events.jsonl"
    assert events_path.exists()
    events_text = events_path.read_text(encoding="utf-8")
    assert "stage_paused" in events_text
    assert '"budget_limit_usd":1.0' in events_text.replace(" ", "")

    run_state = json.loads((run_dir / "run_state.json").read_text(encoding="utf-8"))
    assert run_state["stages"]["downstream"]["status"] == "paused"


@pytest.mark.integration
def test_paused_budget_run_can_resume_with_higher_budget_via_api(tmp_path: Path) -> None:
    _write_budget_pause_module(tmp_path)
    _write_budget_pause_recipe(tmp_path)
    client = _make_client(tmp_path)
    project_path = tmp_path / "output" / "budget-resume-project"
    project_id = _create_project(client, project_path)
    input_path = project_path / "inputs" / "resume-input.txt"
    input_path.parent.mkdir(parents=True, exist_ok=True)
    input_path.write_text("INT. TEST - DAY\n", encoding="utf-8")

    run_id = "integration-budget-resume"
    start = client.post(
        "/api/runs/start",
        json={
            "project_id": project_id,
            "input_file": str(input_path),
            "default_model": "fixture",
            "recipe_id": "budget-pause",
            "run_id": run_id,
            "force": True,
            "run_budget_limit_usd": 1.0,
            "budget_warning_threshold_ratio": 0.8,
        },
    )
    assert start.status_code == 200
    assert start.json()["run_id"] == run_id

    paused_payload = _await_run_terminal_state(client, run_id)
    assert paused_payload["state"]["stages"]["spend"]["status"] == "done"
    assert paused_payload["state"]["stages"]["downstream"]["status"] == "paused"

    resume = client.post(
        f"/api/runs/{run_id}/resume",
        json={"run_budget_limit_usd": 4.25},
    )
    assert resume.status_code == 200
    resumed_run_id = resume.json()["run_id"]
    assert resumed_run_id != run_id

    resumed_events_immediate = client.get(f"/api/runs/{resumed_run_id}/events")
    assert resumed_events_immediate.status_code == 200
    resumed_immediate_payload = resumed_events_immediate.json()
    assert resumed_immediate_payload["run_id"] == resumed_run_id
    assert isinstance(resumed_immediate_payload["events"], list)

    resumed_payload = _await_run_terminal_state(client, resumed_run_id)
    resumed_stages = resumed_payload["state"]["stages"]
    assert resumed_stages["spend"]["status"] == "skipped_reused"
    assert resumed_stages["downstream"]["status"] == "done"
    assert resumed_payload["state"]["runtime_params"]["run_budget_limit_usd"] == pytest.approx(4.25)
    assert resumed_payload["state"]["total_cost_usd"] == pytest.approx(1.1)

    resumed_events = client.get(f"/api/runs/{resumed_run_id}/events")
    assert resumed_events.status_code == 200
    event_names = [event["event"] for event in resumed_events.json()["events"]]
    assert "pipeline_started" in event_names
    assert "stage_started" in event_names
