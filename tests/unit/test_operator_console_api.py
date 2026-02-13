from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from cine_forge.artifacts import ArtifactStore
from cine_forge.operator_console.app import create_app
from cine_forge.schemas import ArtifactMetadata


def _make_client(workspace_root: Path) -> TestClient:
    app = create_app(workspace_root=workspace_root)
    return TestClient(app)


def _init_project(client: TestClient, project_path: Path) -> str:
    response = client.post("/api/projects/new", json={"project_path": str(project_path)})
    assert response.status_code == 200
    payload = response.json()
    assert "project_id" in payload
    assert "project_path" not in payload
    return payload["project_id"]


def test_new_and_open_project_validate_structure(tmp_path: Path) -> None:
    client = _make_client(tmp_path)
    project_path = tmp_path / "project-a"

    created_id = _init_project(client, project_path)

    opened = client.post("/api/projects/open", json={"project_path": str(project_path)})
    assert opened.status_code == 200
    assert opened.json()["project_id"] == created_id

    broken_path = tmp_path / "broken-project"
    broken_path.mkdir(parents=True, exist_ok=True)
    invalid = client.post("/api/projects/open", json={"project_path": str(broken_path)})
    assert invalid.status_code == 422
    payload = invalid.json()
    assert payload["code"] == "invalid_project_structure"


def test_recent_projects_lists_initialized_paths(tmp_path: Path) -> None:
    client = _make_client(tmp_path)
    project_path = tmp_path / "output" / "project-recent"
    _init_project(client, project_path)

    response = client.get("/api/projects/recent")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["display_name"] == "project-recent"
    assert payload[0]["project_path"] == str(project_path)


def test_upload_project_input_stores_file(tmp_path: Path) -> None:
    client = _make_client(tmp_path)
    project_path = tmp_path / "output" / "project-upload"
    project_id = _init_project(client, project_path)

    response = client.post(
        f"/api/projects/{project_id}/inputs/upload",
        files={"file": ("sample.fountain", b"INT. OFFICE - DAY\\n", "text/plain")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["original_name"] == "sample.fountain"
    assert payload["size_bytes"] > 0
    stored_path = Path(payload["stored_path"])
    assert stored_path.exists()
    assert stored_path.read_text(encoding="utf-8").startswith("INT. OFFICE")


def test_artifact_browse_endpoints_return_versions_and_payload(tmp_path: Path) -> None:
    client = _make_client(tmp_path)
    project_path = tmp_path / "project-b"
    project_id = _init_project(client, project_path)

    store = ArtifactStore(project_dir=project_path)
    metadata = ArtifactMetadata(
        intent="seed",
        rationale="seed artifact",
        confidence=0.9,
        source="human",
        producing_module="test.module",
    )
    store.save_artifact(
        artifact_type="raw_input",
        entity_id=None,
        data={"content": "hello"},
        metadata=metadata,
    )
    store.save_artifact(
        artifact_type="raw_input",
        entity_id=None,
        data={"content": "hello v2"},
        metadata=metadata,
    )

    groups = client.get(f"/api/projects/{project_id}/artifacts")
    assert groups.status_code == 200
    groups_payload = groups.json()
    assert len(groups_payload) == 1
    assert groups_payload[0]["artifact_type"] == "raw_input"
    assert groups_payload[0]["latest_version"] == 2

    versions = client.get(f"/api/projects/{project_id}/artifacts/raw_input/__project__")
    assert versions.status_code == 200
    versions_payload = versions.json()
    assert [item["version"] for item in versions_payload] == [1, 2]

    detail = client.get(f"/api/projects/{project_id}/artifacts/raw_input/__project__/2")
    assert detail.status_code == 200
    detail_payload = detail.json()
    assert detail_payload["payload"]["data"]["content"] == "hello v2"


def test_run_start_and_run_polling_endpoints(tmp_path: Path, monkeypatch) -> None:
    client = _make_client(tmp_path)
    project_path = tmp_path / "project-c"
    project_id = _init_project(client, project_path)

    service = client.app.state.console_service

    def _fake_start_run(_: str, request: dict[str, object]) -> str:
        run_id = str(request.get("run_id") or "run-fake-001")
        run_dir = tmp_path / "output" / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        run_state = {
            "run_id": run_id,
            "recipe_id": "mvp_ingest",
            "dry_run": False,
            "started_at": 1.0,
            "finished_at": 2.0,
            "stages": {
                "ingest": {
                    "status": "done",
                    "artifact_refs": [],
                    "duration_seconds": 1.0,
                    "cost_usd": 0.0,
                }
            },
            "total_cost_usd": 0.0,
            "instrumented": False,
        }
        (run_dir / "run_state.json").write_text(json.dumps(run_state), encoding="utf-8")
        (run_dir / "pipeline_events.jsonl").write_text(
            json.dumps({"event": "stage_started", "stage_id": "ingest"}) + "\n",
            encoding="utf-8",
        )
        return run_id

    monkeypatch.setattr(service, "start_run", _fake_start_run)

    start = client.post(
        "/api/runs/start",
        json={
            "project_id": project_id,
            "input_file": "tests/fixtures/sample_screenplay.fountain",
            "default_model": "fixture",
            "accept_config": True,
        },
    )
    assert start.status_code == 200
    run_id = start.json()["run_id"]

    state = client.get(f"/api/runs/{run_id}/state")
    assert state.status_code == 200
    assert state.json()["state"]["run_id"] == run_id

    events = client.get(f"/api/runs/{run_id}/events")
    assert events.status_code == 200
    assert events.json()["events"][0]["event"] == "stage_started"


def test_project_scoped_endpoint_requires_open_project(tmp_path: Path) -> None:
    client = _make_client(tmp_path)
    response = client.get("/api/projects/unknown/artifacts")
    assert response.status_code == 404
    payload = response.json()
    assert payload["code"] == "project_not_opened"


def test_project_runs_endpoint_filters_by_project(tmp_path: Path) -> None:
    client = _make_client(tmp_path)
    project_a = tmp_path / "project-runs-a"
    project_b = tmp_path / "project-runs-b"
    project_a_id = _init_project(client, project_a)
    project_b_id = _init_project(client, project_b)

    # Seed one artifact in each project so fallback ownership inference can work.
    metadata = ArtifactMetadata(
        intent="seed",
        rationale="seed artifact",
        confidence=0.9,
        source="human",
        producing_module="test.module",
    )
    ref_a = ArtifactStore(project_dir=project_a).save_artifact(
        artifact_type="raw_input",
        entity_id=None,
        data={"content": "a"},
        metadata=metadata,
    )
    ref_b = ArtifactStore(project_dir=project_b).save_artifact(
        artifact_type="raw_input",
        entity_id=None,
        data={"content": "b"},
        metadata=metadata,
    )

    runs_dir = tmp_path / "output" / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)

    run_a_dir = runs_dir / "run-a"
    run_a_dir.mkdir(parents=True, exist_ok=True)
    (run_a_dir / "run_state.json").write_text(
        json.dumps(
            {
                "run_id": "run-a",
                "recipe_id": "mvp_ingest",
                "dry_run": False,
                "started_at": 1.0,
                "finished_at": 2.0,
                "stages": {
                    "ingest": {
                        "status": "done",
                        "artifact_refs": [ref_a.model_dump()],
                        "duration_seconds": 0.1,
                        "cost_usd": 0.0,
                    }
                },
                "total_cost_usd": 0.0,
                "instrumented": False,
            }
        ),
        encoding="utf-8",
    )
    (run_a_dir / "operator_console_run_meta.json").write_text(
        json.dumps({"project_id": project_a_id, "project_path": str(project_a)}),
        encoding="utf-8",
    )

    run_b_dir = runs_dir / "run-b"
    run_b_dir.mkdir(parents=True, exist_ok=True)
    (run_b_dir / "run_state.json").write_text(
        json.dumps(
            {
                "run_id": "run-b",
                "recipe_id": "mvp_ingest",
                "dry_run": False,
                "started_at": 1.0,
                "finished_at": 2.0,
                "stages": {
                    "ingest": {
                        "status": "done",
                        "artifact_refs": [ref_b.model_dump()],
                        "duration_seconds": 0.1,
                        "cost_usd": 0.0,
                    }
                },
                "total_cost_usd": 0.0,
                "instrumented": False,
            }
        ),
        encoding="utf-8",
    )
    (run_b_dir / "operator_console_run_meta.json").write_text(
        json.dumps({"project_id": project_b_id, "project_path": str(project_b)}),
        encoding="utf-8",
    )

    runs_a = client.get(f"/api/projects/{project_a_id}/runs")
    assert runs_a.status_code == 200
    assert [item["run_id"] for item in runs_a.json()] == ["run-a"]

    runs_b = client.get(f"/api/projects/{project_b_id}/runs")
    assert runs_b.status_code == 200
    assert [item["run_id"] for item in runs_b.json()] == ["run-b"]
