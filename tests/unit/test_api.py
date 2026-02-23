from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from cine_forge.api.app import create_app
from cine_forge.api.service import OperatorConsoleService, ServiceError
from cine_forge.artifacts import ArtifactStore
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


def test_get_project_input_content_uses_ingest_extraction_for_pdf(
    tmp_path: Path, monkeypatch,
) -> None:
    client = _make_client(tmp_path)
    project_id = _create_project(client, "project-pdf-preview", "Project PDF Preview")

    uploaded = client.post(
        f"/api/projects/{project_id}/inputs/upload",
        files={"file": ("script.pdf", b"%PDF-1.7\nbinary", "application/pdf")},
    )
    assert uploaded.status_code == 200
    filename = Path(uploaded.json()["stored_path"]).name

    def _fake_read_source_text_with_diagnostics(_path: Path) -> tuple[str, dict[str, object]]:
        return "INT. HARBOR - NIGHT\nTHE MARINER watches the tide.", {"pdf_preview": True}

    monkeypatch.setattr(
        "cine_forge.api.service.read_source_text_with_diagnostics",
        _fake_read_source_text_with_diagnostics,
    )

    content = client.get(f"/api/projects/{project_id}/inputs/{filename}")
    assert content.status_code == 200
    assert content.text.startswith("INT. HARBOR - NIGHT")


def test_get_project_input_content_returns_422_on_empty_extraction(
    tmp_path: Path, monkeypatch,
) -> None:
    client = _make_client(tmp_path)
    project_id = _create_project(client, "project-pdf-empty", "Project PDF Empty")

    uploaded = client.post(
        f"/api/projects/{project_id}/inputs/upload",
        files={"file": ("script.pdf", b"%PDF-1.7\nbinary", "application/pdf")},
    )
    assert uploaded.status_code == 200
    filename = Path(uploaded.json()["stored_path"]).name

    def _fake_read_source_text_with_diagnostics(_path: Path) -> tuple[str, dict[str, object]]:
        return "   ", {"pdf_extractor_selected": "fallback_sparse"}

    monkeypatch.setattr(
        "cine_forge.api.service.read_source_text_with_diagnostics",
        _fake_read_source_text_with_diagnostics,
    )

    content = client.get(f"/api/projects/{project_id}/inputs/{filename}")
    assert content.status_code == 422
    payload = content.json()
    assert payload["code"] == "input_extraction_failed"


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


@pytest.mark.unit
def test_retry_failed_stage_endpoint_returns_new_run_urls(tmp_path: Path, monkeypatch) -> None:
    client = _make_client(tmp_path)
    service = client.app.state.console_service

    def _fake_retry_failed_stage(run_id: str) -> str:
        assert run_id == "run-failed-1"
        return "run-failed-1-retry-abcd"

    monkeypatch.setattr(service, "retry_failed_stage", _fake_retry_failed_stage)

    response = client.post("/api/runs/run-failed-1/retry-failed-stage")
    assert response.status_code == 200
    payload = response.json()
    assert payload["run_id"] == "run-failed-1-retry-abcd"
    assert payload["state_url"] == "/api/runs/run-failed-1-retry-abcd/state"
    assert payload["events_url"] == "/api/runs/run-failed-1-retry-abcd/events"


@pytest.mark.unit
def test_start_run_accepts_retry_failed_stage_for_run_id(tmp_path: Path, monkeypatch) -> None:
    client = _make_client(tmp_path)
    service = client.app.state.console_service

    def _fake_retry_failed_stage(run_id: str) -> str:
        assert run_id == "run-failed-2"
        return "run-failed-2-retry-zz99"

    monkeypatch.setattr(service, "retry_failed_stage", _fake_retry_failed_stage)

    response = client.post(
        "/api/runs/start",
        json={
            "project_id": "unused-for-retry-path",
            "input_file": "unused",
            "default_model": "fixture",
            "accept_config": True,
            "retry_failed_stage_for_run_id": "run-failed-2",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["run_id"] == "run-failed-2-retry-zz99"


@pytest.mark.unit
def test_service_retry_failed_stage_bootstraps_new_run_from_failed_stage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = OperatorConsoleService(workspace_root=tmp_path)
    project_path = tmp_path / "output" / "resume-project"
    (project_path / "artifacts").mkdir(parents=True, exist_ok=True)
    (project_path / "graph").mkdir(parents=True, exist_ok=True)
    store = ArtifactStore(project_dir=project_path)
    raw_ref = store.save_artifact(
        artifact_type="raw_input",
        entity_id=None,
        data={
            "content": "INT. LAB - NIGHT\nMARA\nGo.",
            "source_info": {"original_filename": "sample.fountain"},
            "classification": {"detected_format": "screenplay", "confidence": 0.9, "evidence": []},
        },
        metadata=ArtifactMetadata(
            intent="seed",
            rationale="seed",
            confidence=1.0,
            source="human",
            producing_module="test.module",
        ),
    )

    recipe_dir = tmp_path / "configs" / "recipes"
    recipe_dir.mkdir(parents=True, exist_ok=True)
    recipe_path = recipe_dir / "recipe-mvp-ingest.yaml"
    recipe_path.write_text(
        "recipe_id: mvp_ingest\ndescription: test\nstages: []\n",
        encoding="utf-8",
    )

    run_id = "run-failed-service"
    run_dir = tmp_path / "output" / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    run_state = {
        "run_id": run_id,
        "recipe_id": "mvp_ingest",
        "runtime_params": {"input_file": "x.fountain", "default_model": "fixture"},
        "stages": {
            "ingest": {"status": "done", "artifact_refs": [raw_ref.model_dump(mode="json")]},
            "normalize": {"status": "failed"},
            "breakdown_scenes": {"status": "pending"},
        },
    }
    (run_dir / "run_state.json").write_text(json.dumps(run_state), encoding="utf-8")
    (run_dir / "run_meta.json").write_text(
        json.dumps(
            {"project_id": "resume-project", "project_path": str(project_path)},
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    captured: dict[str, object] = {}

    class _FakeThread:
        def __init__(self, *, target, kwargs, daemon):  # type: ignore[no-untyped-def]
            captured["target"] = target
            captured["kwargs"] = kwargs
            captured["daemon"] = daemon
            captured["started"] = False

        def start(self) -> None:
            captured["started"] = True

    monkeypatch.setattr("cine_forge.api.service.threading.Thread", _FakeThread)

    new_run_id = service.retry_failed_stage(run_id)
    assert new_run_id.startswith(f"{run_id}-retry-")
    assert captured["started"] is True

    worker_kwargs = captured["kwargs"]
    assert isinstance(worker_kwargs, dict)
    assert worker_kwargs["run_id"] == new_run_id
    assert worker_kwargs["start_from"] == "normalize"
    assert worker_kwargs["runtime_params"]["input_file"] == "x.fountain"
    assert worker_kwargs["runtime_params"]["default_model"] == "fixture"
    assert worker_kwargs["runtime_params"]["__resume_artifact_refs_by_stage"] == {
        "ingest": [raw_ref.model_dump(mode="json")],
        "normalize": [],
        "breakdown_scenes": [],
    }
    assert worker_kwargs["recipe_path"] == recipe_path
    assert worker_kwargs["project_path"] == project_path

    new_run_dir = tmp_path / "output" / "runs" / new_run_id
    assert (new_run_dir / "run_meta.json").exists()
    assert service.require_project_path("resume-project") == project_path


@pytest.mark.unit
def test_service_retry_failed_stage_steps_back_to_ingest_for_empty_raw_input(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = OperatorConsoleService(workspace_root=tmp_path)
    project_path = tmp_path / "output" / "resume-project-empty"
    (project_path / "artifacts").mkdir(parents=True, exist_ok=True)
    (project_path / "graph").mkdir(parents=True, exist_ok=True)
    store = ArtifactStore(project_dir=project_path)
    raw_ref = store.save_artifact(
        artifact_type="raw_input",
        entity_id=None,
        data={
            "content": "   ",
            "source_info": {"original_filename": "empty.pdf"},
            "classification": {"detected_format": "unknown", "confidence": 0.2, "evidence": []},
        },
        metadata=ArtifactMetadata(
            intent="seed",
            rationale="seed",
            confidence=1.0,
            source="human",
            producing_module="test.module",
        ),
    )

    recipe_dir = tmp_path / "configs" / "recipes"
    recipe_dir.mkdir(parents=True, exist_ok=True)
    recipe_path = recipe_dir / "recipe-mvp-ingest.yaml"
    recipe_path.write_text(
        "recipe_id: mvp_ingest\ndescription: test\nstages: []\n",
        encoding="utf-8",
    )

    run_id = "run-failed-empty-raw"
    run_dir = tmp_path / "output" / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    run_state = {
        "run_id": run_id,
        "recipe_id": "mvp_ingest",
        "runtime_params": {"input_file": "empty.pdf", "default_model": "fixture"},
        "stages": {
            "ingest": {"status": "done", "artifact_refs": [raw_ref.model_dump(mode="json")]},
            "normalize": {"status": "failed"},
            "breakdown_scenes": {"status": "pending"},
        },
    }
    (run_dir / "run_state.json").write_text(json.dumps(run_state), encoding="utf-8")
    (run_dir / "run_meta.json").write_text(
        json.dumps({"project_id": "resume-project-empty", "project_path": str(project_path)}),
        encoding="utf-8",
    )

    captured: dict[str, object] = {}

    class _FakeThread:
        def __init__(self, *, target, kwargs, daemon):  # type: ignore[no-untyped-def]
            captured["target"] = target
            captured["kwargs"] = kwargs
            captured["daemon"] = daemon
            captured["started"] = False

        def start(self) -> None:
            captured["started"] = True

    monkeypatch.setattr("cine_forge.api.service.threading.Thread", _FakeThread)

    _ = service.retry_failed_stage(run_id)
    worker_kwargs = captured["kwargs"]
    assert isinstance(worker_kwargs, dict)
    assert worker_kwargs["start_from"] == "ingest"
    assert worker_kwargs["recipe_path"] == recipe_path


@pytest.mark.unit
def test_service_retry_failed_stage_rejects_runs_without_failed_stage(tmp_path: Path) -> None:
    service = OperatorConsoleService(workspace_root=tmp_path)
    run_id = "run-no-failure"
    run_dir = tmp_path / "output" / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "run_state.json").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "recipe_id": "mvp_ingest",
                "runtime_params": {},
                "stages": {"ingest": {"status": "done"}},
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ServiceError, match="no failed stage"):
        service.retry_failed_stage(run_id)


def _create_project(client: TestClient, slug: str, display_name: str) -> str:
    """Create a project using the new slug-based API and return the project_id."""
    response = client.post(
        "/api/projects/new",
        json={"slug": slug, "display_name": display_name},
    )
    assert response.status_code == 200
    return response.json()["project_id"]


def test_search_returns_scenes_and_entities(tmp_path: Path) -> None:
    """Test search endpoint finds scenes and entities."""
    client = _make_client(tmp_path)
    project_id = _create_project(client, "search-test", "Search Test")
    project_path = tmp_path / "output" / "search-test"

    store = ArtifactStore(project_dir=project_path)
    metadata = ArtifactMetadata(
        intent="seed",
        rationale="test fixture",
        confidence=1.0,
        source="human",
        producing_module="test.fixture",
    )

    # Seed a scene_index artifact
    store.save_artifact(
        artifact_type="scene_index",
        entity_id=None,
        data={
            "entries": [
                {
                    "scene_id": "scene-001",
                    "heading": "INT. WAREHOUSE - NIGHT",
                    "location": "Warehouse",
                    "time_of_day": "NIGHT",
                },
                {
                    "scene_id": "scene-002",
                    "heading": "EXT. ROOFTOP - DAY",
                    "location": "Rooftop",
                    "time_of_day": "DAY",
                },
            ]
        },
        metadata=metadata,
    )

    # Seed bible_manifest artifacts using save_bible_entry (production code path)
    store.save_bible_entry(
        entity_type="character",
        entity_id="detective-jones",
        display_name="Detective Jones",
        files=[],
        data_files={},
        metadata=metadata,
    )

    store.save_bible_entry(
        entity_type="location",
        entity_id="warehouse",
        display_name="The Warehouse",
        files=[],
        data_files={},
        metadata=metadata,
    )

    store.save_bible_entry(
        entity_type="prop",
        entity_id="revolver",
        display_name="Revolver",
        files=[],
        data_files={},
        metadata=metadata,
    )

    # Search for "warehouse" — should match scene + location
    resp = client.get(f"/api/projects/{project_id}/search?q=warehouse")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["query"] == "warehouse"
    assert len(payload["scenes"]) == 1
    assert payload["scenes"][0]["scene_id"] == "scene-001"
    assert payload["scenes"][0]["int_ext"] == "INT"
    assert len(payload["locations"]) == 1
    assert payload["locations"][0]["display_name"] == "The Warehouse"
    assert payload["locations"][0]["entity_type"] == "location"
    assert len(payload["characters"]) == 0
    assert len(payload["props"]) == 0

    # Search for "jones" — should match character only
    resp2 = client.get(f"/api/projects/{project_id}/search?q=jones")
    assert resp2.status_code == 200
    payload2 = resp2.json()
    assert len(payload2["characters"]) == 1
    assert payload2["characters"][0]["display_name"] == "Detective Jones"
    assert len(payload2["scenes"]) == 0

    # Search for "revolver" — should match prop
    resp3 = client.get(f"/api/projects/{project_id}/search?q=revolver")
    assert resp3.status_code == 200
    payload3 = resp3.json()
    assert len(payload3["props"]) == 1
    assert payload3["props"][0]["display_name"] == "Revolver"

    # Empty query returns empty results
    resp4 = client.get(f"/api/projects/{project_id}/search?q=")
    assert resp4.status_code == 200
    payload4 = resp4.json()
    assert payload4["scenes"] == []
    assert payload4["characters"] == []


def test_search_requires_open_project(tmp_path: Path) -> None:
    """Test that searching a non-opened project returns 404."""
    client = _make_client(tmp_path)
    resp = client.get("/api/projects/unknown/search?q=test")
    assert resp.status_code == 404
    assert resp.json()["code"] == "project_not_opened"


def test_project_scoped_endpoint_requires_open_project(tmp_path: Path) -> None:
    client = _make_client(tmp_path)
    response = client.get("/api/projects/unknown/artifacts")
    assert response.status_code == 404
    payload = response.json()
    assert payload["code"] == "project_not_opened"


def test_project_slug_routes_survive_backend_restart(tmp_path: Path) -> None:
    """Existing output/<slug> projects should resolve without explicit /open after restart."""
    client_a = _make_client(tmp_path)
    project_id = _create_project(client_a, "deep-link-project", "Deep Link Project")

    # Simulate backend restart: new app instance with empty in-memory registry.
    client_b = _make_client(tmp_path)

    summary = client_b.get(f"/api/projects/{project_id}")
    assert summary.status_code == 200
    assert summary.json()["project_id"] == project_id

    # Any project-scoped endpoint should now work from slug-only routing.
    artifacts = client_b.get(f"/api/projects/{project_id}/artifacts")
    assert artifacts.status_code == 200


def test_project_resolution_falls_back_to_run_metadata(tmp_path: Path) -> None:
    """If a project isn't under output/<slug>, resolve it via run_meta project_path."""
    service = OperatorConsoleService(workspace_root=tmp_path)

    external_project = tmp_path / "external-project-dir"
    (external_project / "artifacts").mkdir(parents=True, exist_ok=True)
    (external_project / "graph").mkdir(parents=True, exist_ok=True)

    run_dir = tmp_path / "output" / "runs" / "run-meta-project-map"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "run_meta.json").write_text(
        json.dumps(
            {
                "project_id": "external-project",
                "project_path": str(external_project),
            }
        ),
        encoding="utf-8",
    )

    assert service.require_project_path("external-project") == external_project


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


def test_edit_artifact_creates_new_version(tmp_path: Path) -> None:
    """Test that editing an artifact creates a new version with human provenance."""
    client = _make_client(tmp_path)
    project_path = tmp_path / "project-edit"
    project_id = _init_project(client, project_path)

    # Create an initial artifact
    store = ArtifactStore(project_dir=project_path)
    metadata = ArtifactMetadata(
        intent="initial",
        rationale="First version",
        confidence=0.9,
        source="ai",
        producing_module="test.module",
    )
    store.save_artifact(
        artifact_type="entity_graph",
        entity_id=None,
        data={"entities": ["Alice", "Bob"], "relationships": []},
        metadata=metadata,
    )

    # Edit the artifact
    edit_response = client.post(
        f"/api/projects/{project_id}/artifacts/entity_graph/__project__/edit",
        json={
            "data": {"entities": ["Alice", "Bob", "Charlie"], "relationships": ["friends"]},
            "rationale": "Added Charlie and defined friendship relationship",
        },
    )
    assert edit_response.status_code == 200
    edit_payload = edit_response.json()
    assert edit_payload["artifact_type"] == "entity_graph"
    assert edit_payload["entity_id"] is None
    assert edit_payload["version"] == 2
    assert "path" in edit_payload

    # Verify the new version was created
    versions = client.get(f"/api/projects/{project_id}/artifacts/entity_graph/__project__")
    assert versions.status_code == 200
    versions_payload = versions.json()
    assert len(versions_payload) == 2
    assert versions_payload[1]["version"] == 2
    assert versions_payload[1]["producing_module"] == "operator_console.manual_edit"

    # Verify the new version has the edited data
    detail = client.get(f"/api/projects/{project_id}/artifacts/entity_graph/__project__/2")
    assert detail.status_code == 200
    detail_payload = detail.json()
    assert detail_payload["payload"]["data"]["entities"] == ["Alice", "Bob", "Charlie"]
    assert detail_payload["payload"]["data"]["relationships"] == ["friends"]
    assert detail_payload["payload"]["metadata"]["source"] == "human"
    assert detail_payload["payload"]["metadata"]["confidence"] == 1.0
    assert (
        detail_payload["payload"]["metadata"]["rationale"]
        == "Added Charlie and defined friendship relationship"
    )

    # Verify lineage points to v1
    lineage = detail_payload["payload"]["metadata"]["lineage"]
    assert len(lineage) == 1
    assert lineage[0]["version"] == 1


def test_edit_artifact_requires_existing_artifact(tmp_path: Path) -> None:
    """Test that editing a non-existent artifact returns 404."""
    client = _make_client(tmp_path)
    project_path = tmp_path / "project-edit-missing"
    project_id = _init_project(client, project_path)

    # Try to edit a non-existent artifact
    edit_response = client.post(
        f"/api/projects/{project_id}/artifacts/nonexistent/__project__/edit",
        json={"data": {"test": "data"}, "rationale": "Test edit"},
    )
    assert edit_response.status_code == 404
    edit_payload = edit_response.json()
    assert edit_payload["code"] == "artifact_not_found"


def test_project_ui_preferences_persist(tmp_path: Path) -> None:
    """Test that UI preferences can be saved and retrieved via project settings."""
    client = _make_client(tmp_path)
    project_id = _create_project(client, "pref-test", "Preference Test")

    # Initial project should have empty ui_preferences
    resp = client.get(f"/api/projects/{project_id}")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["ui_preferences"] == {}

    # Update with some preferences
    update_resp = client.patch(
        f"/api/projects/{project_id}/settings",
        json={
            "ui_preferences": {
                "characters.sort": "prominence",
                "characters.density": "compact",
            }
        },
    )
    assert update_resp.status_code == 200
    update_payload = update_resp.json()
    assert update_payload["ui_preferences"]["characters.sort"] == "prominence"
    assert update_payload["ui_preferences"]["characters.density"] == "compact"

    # Verify preferences persist across reads
    resp2 = client.get(f"/api/projects/{project_id}")
    assert resp2.status_code == 200
    payload2 = resp2.json()
    assert payload2["ui_preferences"]["characters.sort"] == "prominence"

    # Update again (shallow merge — new keys added, existing preserved)
    update_resp2 = client.patch(
        f"/api/projects/{project_id}/settings",
        json={
            "ui_preferences": {
                "locations.sort": "script-order",
                "characters.density": "medium",  # overwrite existing key
            }
        },
    )
    assert update_resp2.status_code == 200
    final_payload = update_resp2.json()
    assert final_payload["ui_preferences"]["characters.sort"] == "prominence"  # preserved
    assert final_payload["ui_preferences"]["characters.density"] == "medium"  # updated
    assert final_payload["ui_preferences"]["locations.sort"] == "script-order"  # added

    # Verify project.json file contains the preferences
    project_path = tmp_path / "output" / "pref-test"
    project_json_path = project_path / "project.json"
    assert project_json_path.exists()
    project_data = json.loads(project_json_path.read_text(encoding="utf-8"))
    assert "ui_preferences" in project_data
    assert project_data["ui_preferences"]["characters.sort"] == "prominence"
    assert project_data["ui_preferences"]["locations.sort"] == "script-order"
