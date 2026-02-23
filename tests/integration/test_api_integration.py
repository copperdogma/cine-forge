from __future__ import annotations

import time
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from cine_forge.api.app import create_app


def _await_run_done(client: TestClient, run_id: str, timeout_seconds: float = 60.0) -> dict:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        response = client.get(f"/api/runs/{run_id}/state")
        if response.status_code != 200:
            time.sleep(0.5)
            continue
        payload = response.json()
        stages = payload["state"]["stages"]
        
        # We need to know which stages are expected for this recipe
        # For mvp_ingest it's: ingest, normalize, breakdown_scenes, project_config
        # But let's just check overall run status or that no stages are running/pending
        statuses = {s["status"] for s in stages.values()}
        
        if "failed" in statuses:
            # Check for background errors too
            if payload.get("background_error"):
                raise AssertionError(f"Run {run_id} failed: {payload['background_error']}")
            raise AssertionError(f"Run {run_id} failed with statuses={statuses}")
            
        # If any stage is paused, the run is 'done' for now (awaiting human)
        if "paused" in statuses:
            return payload
            
        # Run is finished when ALL stages are done or skipped
        if statuses and all(s in {"done", "skipped_reused"} for s in statuses):
            # Also check if it's actually finished (finished_at set)
            if payload["state"].get("finished_at"):
                return payload
        
        time.sleep(0.5)
    raise AssertionError(f"Timed out waiting for run '{run_id}'")


@pytest.mark.integration
def test_operator_console_new_open_run_events_and_artifacts_flow(tmp_path: Path) -> None:
    workspace_root = Path(__file__).resolve().parents[2]
    app = create_app(workspace_root=workspace_root)
    client = TestClient(app)

    project_path = tmp_path / "operator-project-integration"
    created = client.post("/api/projects/new", json={"project_path": str(project_path)})
    assert created.status_code == 200
    project_id = created.json()["project_id"]
    recent = client.get("/api/projects/recent")
    assert recent.status_code == 200
    assert any(item["project_id"] == project_id for item in recent.json())

    opened = client.post("/api/projects/open", json={"project_path": str(project_path)})
    assert opened.status_code == 200
    assert opened.json()["project_id"] == project_id

    uploaded = client.post(
        f"/api/projects/{project_id}/inputs/upload",
        files={"file": ("sample.fountain", b"INT. ROOM - DAY\\n", "text/plain")},
    )
    assert uploaded.status_code == 200
    uploaded_input = uploaded.json()["stored_path"]

    run_id = f"operator-integration-accept-{uuid.uuid4().hex[:8]}"
    started = client.post(
        "/api/runs/start",
        json={
            "project_id": project_id,
            "input_file": uploaded_input,
            "default_model": "mock",
            "qa_model": "mock",
            "accept_config": True,
            "run_id": run_id,
            "force": True,
        },
    )
    assert started.status_code == 200
    assert started.json()["run_id"] == run_id

    state = _await_run_done(client, run_id)
    assert state["state"]["stages"]["project_config"]["status"] in {"done", "skipped_reused"}

    events = client.get(f"/api/runs/{run_id}/events")
    assert events.status_code == 200
    event_names = [item["event"] for item in events.json()["events"]]
    assert "stage_started" in event_names

    groups = client.get(f"/api/projects/{project_id}/artifacts")
    assert groups.status_code == 200
    group_types = {item["artifact_type"] for item in groups.json()}
    assert "project_config" in group_types


@pytest.mark.integration
def test_operator_console_config_review_edit_confirm_flow(tmp_path: Path) -> None:
    workspace_root = Path(__file__).resolve().parents[2]
    app = create_app(workspace_root=workspace_root)
    client = TestClient(app)

    project_path = tmp_path / "operator-project-review"
    created = client.post("/api/projects/new", json={"project_path": str(project_path)})
    assert created.status_code == 200
    project_id = created.json()["project_id"]

    draft_run_id = f"operator-integration-draft-{uuid.uuid4().hex[:8]}"
    draft_start = client.post(
        "/api/runs/start",
        json={
            "project_id": project_id,
            "input_file": str(workspace_root / "tests" / "fixtures" / "sample_screenplay.fountain"),
            "default_model": "mock",
            "qa_model": "mock",
            "accept_config": False,
            "run_id": draft_run_id,
            "force": True,
        },
    )
    assert draft_start.status_code == 200
    assert draft_start.json()["run_id"] == draft_run_id

    draft_state = _await_run_done(client, draft_run_id)
    assert draft_state["state"]["stages"]["project_config"]["status"] == "paused"

    groups = client.get(f"/api/projects/{project_id}/artifacts")
    assert groups.status_code == 200
    draft_group = next(
        item for item in groups.json() if item["artifact_type"] == "draft_project_config"
    )

    versions = client.get(
        f"/api/projects/{project_id}/artifacts/draft_project_config/{draft_group['entity_id']}"
    )
    assert versions.status_code == 200
    latest_version = versions.json()[-1]["version"]

    detail = client.get(
        f"/api/projects/{project_id}/artifacts/draft_project_config/{draft_group['entity_id']}/{latest_version}"
    )
    assert detail.status_code == 200
    draft_payload = detail.json()["payload"]
    draft_data = draft_payload["data"]

    edited_title = f"{draft_data['title']} (Reviewed)"
    confirm_run_id = f"operator-integration-confirm-{uuid.uuid4().hex[:8]}"
    confirm_start = client.post(
        "/api/runs/start",
        json={
            "project_id": project_id,
            "input_file": str(workspace_root / "tests" / "fixtures" / "sample_screenplay.fountain"),
            "default_model": "mock",
            "qa_model": "mock",
            "accept_config": True,
            "run_id": confirm_run_id,
            "force": True,
            "config_overrides": {
                "title": edited_title,
                "tone": draft_data["tone"],
                "genre": draft_data["genre"],
            },
        },
    )
    assert confirm_start.status_code == 200
    assert confirm_start.json()["run_id"] == confirm_run_id

    confirm_state = _await_run_done(client, confirm_run_id)
    assert confirm_state["state"]["stages"]["project_config"]["status"] in {
        "done",
        "skipped_reused",
    }

    post_groups = client.get(f"/api/projects/{project_id}/artifacts")
    project_group = next(
        item for item in post_groups.json() if item["artifact_type"] == "project_config"
    )
    project_versions = client.get(
        f"/api/projects/{project_id}/artifacts/project_config/{project_group['entity_id']}"
    )
    latest_confirmed = project_versions.json()[-1]["version"]

    confirmed_detail = client.get(
        f"/api/projects/{project_id}/artifacts/project_config/{project_group['entity_id']}/{latest_confirmed}"
    )
    confirmed_data = confirmed_detail.json()["payload"]["data"]
    assert confirmed_data["confirmed"] is True
    assert confirmed_data["title"] == edited_title
