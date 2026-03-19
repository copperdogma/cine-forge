from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from cine_forge.api.app import create_app


def _make_client(workspace_root: Path) -> TestClient:
    return TestClient(create_app(workspace_root=workspace_root))


def _create_project(client: TestClient, project_path: Path) -> str:
    response = client.post("/api/projects/new", json={"project_path": str(project_path)})
    assert response.status_code == 200
    return response.json()["project_id"]


def _seed_cost_run(workspace_root: Path, project_path: Path, project_id: str, run_id: str) -> None:
    (project_path / "project.json").write_text(
        json.dumps(
            {
                "slug": project_id,
                "display_name": "Cost API Project",
                "project_budget_limit_usd": 12.0,
                "default_run_budget_limit_usd": 2.0,
                "budget_warning_threshold_ratio": 0.8,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    run_dir = workspace_root / "output" / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "run_state.json").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "recipe_id": "mvp_ingest",
                "started_at": 10.0,
                "finished_at": 15.0,
                "runtime_params": {
                    "run_budget_limit_usd": 2.0,
                    "project_budget_limit_usd": 12.0,
                    "budget_warning_threshold_ratio": 0.8,
                },
                "total_cost_usd": 1.2,
                "stages": {
                    "analyze": {
                        "status": "done",
                        "model_used": "claude-sonnet-4-6",
                        "call_count": 2,
                        "attempt_count": 1,
                        "input_tokens": 200,
                        "output_tokens": 80,
                        "cost_usd": 1.2,
                        "duration_seconds": 5.0,
                        "artifact_refs": [
                            {"artifact_type": "scene", "entity_id": "scene_001", "version": 1}
                        ],
                    }
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (run_dir / "run_meta.json").write_text(
        json.dumps(
            {
                "project_id": project_id,
                "project_path": str(project_path),
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    (project_path / "role_invocations.jsonl").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "stage_id": "analyze",
                "scene_id": "scene_001",
                "entity_id": "scene_001",
                "role_id": "script_qa",
                "model": "gpt-4.1-mini",
                "response": {
                    "cost_data": {
                        "estimated_cost_usd": 0.4,
                        "input_tokens": 100,
                        "output_tokens": 50,
                    }
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )


@pytest.mark.unit
def test_cost_summary_endpoints_return_project_and_run_data(tmp_path: Path) -> None:
    client = _make_client(tmp_path)
    project_path = tmp_path / "output" / "cost-api-project"
    project_id = _create_project(client, project_path)
    _seed_cost_run(tmp_path, project_path, project_id, "run-cost-api")

    project_response = client.get(f"/api/projects/{project_id}/costs")
    assert project_response.status_code == 200
    project_payload = project_response.json()
    assert project_payload["project_id"] == project_id
    assert project_payload["run_count"] == 1
    assert project_payload["total_cost_usd"] == pytest.approx(1.2)

    run_response = client.get("/api/runs/run-cost-api/costs")
    assert run_response.status_code == 200
    run_payload = run_response.json()
    assert run_payload["run_id"] == "run-cost-api"
    assert run_payload["total_cost_usd"] == pytest.approx(1.2)
    assert run_payload["by_role"][0]["role_id"] == "script_qa"


@pytest.mark.unit
def test_project_budget_settings_round_trip_and_resume_accepts_override(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _make_client(tmp_path)
    project_path = tmp_path / "output" / "settings-project"
    project_id = _create_project(client, project_path)

    response = client.patch(
        f"/api/projects/{project_id}/settings",
        json={
            "project_budget_limit_usd": 25.0,
            "default_run_budget_limit_usd": 3.5,
            "budget_warning_threshold_ratio": 0.7,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["project_budget_limit_usd"] == pytest.approx(25.0)
    assert payload["default_run_budget_limit_usd"] == pytest.approx(3.5)
    assert payload["budget_warning_threshold_ratio"] == pytest.approx(0.7)

    captured: dict[str, object] = {}
    service = client.app.state.console_service

    def _fake_resume_run(run_id: str, overrides: dict[str, object] | None = None) -> str:
        captured["run_id"] = run_id
        captured["overrides"] = overrides
        return "run-resumed-1234"

    monkeypatch.setattr(service, "resume_run", _fake_resume_run)

    resume = client.post(
        "/api/runs/run-paused-001/resume",
        json={"run_budget_limit_usd": 4.25},
    )
    assert resume.status_code == 200
    assert resume.json()["run_id"] == "run-resumed-1234"
    assert captured["run_id"] == "run-paused-001"
    assert captured["overrides"] == {"run_budget_limit_usd": 4.25}
