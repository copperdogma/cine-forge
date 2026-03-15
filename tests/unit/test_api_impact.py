from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from cine_forge.api.app import create_app
from cine_forge.artifacts import ArtifactStore
from cine_forge.schemas import (
    ArtifactHealth,
    ArtifactMetadata,
    ArtifactRef,
)
from cine_forge.services.impact_assessment import ImpactAssessmentService


def _make_client(workspace_root: Path) -> TestClient:
    app = create_app(workspace_root=workspace_root)
    return TestClient(app)


def _init_project(client: TestClient, project_path: Path) -> str:
    response = client.post("/api/projects/new", json={"project_path": str(project_path)})
    assert response.status_code == 200
    return response.json()["project_id"]


def _metadata(*, lineage: list[ArtifactRef] | None = None) -> ArtifactMetadata:
    return ArtifactMetadata(
        lineage=lineage or [],
        intent="seed",
        rationale="seed artifact",
        confidence=1.0,
        source="human",
        producing_module="test.module",
    )


def _seed_stale_graph(
    project_path: Path,
) -> tuple[ArtifactStore, ArtifactRef, ArtifactRef, ArtifactRef]:
    store = ArtifactStore(project_dir=project_path)
    trigger_v1 = store.save_artifact(
        artifact_type="character_bible",
        entity_id="billy",
        data={"name": "Billy", "motivation": "prove himself to his father"},
        metadata=_metadata(),
    )
    scene_ref = store.save_artifact(
        artifact_type="scene",
        entity_id="scene_001",
        data={"performance_note": "Billy wants to prove himself to his father."},
        metadata=_metadata(lineage=[trigger_v1]),
    )
    shot_ref = store.save_artifact(
        artifact_type="shot_plan",
        entity_id="scene_001",
        data={"visual_note": "Close on the protagonist as they hesitate."},
        metadata=_metadata(lineage=[trigger_v1]),
    )
    trigger_v2 = store.save_artifact(
        artifact_type="character_bible",
        entity_id="billy",
        data={"name": "Billy", "motivation": "protect his younger sister"},
        metadata=_metadata(),
    )
    return store, trigger_v2, scene_ref, shot_ref


def _fake_llm(prompt: str, model: str, response_schema, **_: object):
    if "performance_note" in prompt:
        payload = {
            "assessed_health": "needs_revision",
            "rationale": "The scene note depends on Billy's old motivation.",
            "upstream_change_summary": (
                "Billy's motivation changed from proving himself to protecting his "
                "sister."
            ),
            "suggested_revision": "Update the scene direction to focus on protective urgency.",
            "confidence": 0.91,
        }
    else:
        payload = {
            "assessed_health": "confirmed_valid",
            "rationale": "The visual note still works without the old motivation.",
            "upstream_change_summary": (
                "Billy's motivation changed from proving himself to protecting his "
                "sister."
            ),
            "suggested_revision": None,
            "confidence": 0.88,
        }
    return response_schema.model_validate(payload), {
        "model": model,
        "input_tokens": 100,
        "output_tokens": 50,
        "estimated_cost_usd": 0.001,
    }


@pytest.mark.unit
def test_artifact_detail_returns_live_health_overlay(tmp_path: Path) -> None:
    client = _make_client(tmp_path)
    project_path = tmp_path / "project-impact-detail"
    project_id = _init_project(client, project_path)
    _store, trigger_v2, scene_ref, _shot_ref = _seed_stale_graph(project_path)

    detail = client.get(f"/api/projects/{project_id}/artifacts/scene/scene_001/1")

    assert detail.status_code == 200
    payload = detail.json()
    assert payload["health"] == "stale"
    assert payload["payload"]["metadata"]["health"] == "stale"
    assert payload["health_details"]["source_kind"] == "structural_invalidation"
    assert payload["health_details"]["trigger_ref"]["artifact_type"] == trigger_v2.artifact_type
    assert payload["health_details"]["trigger_ref"]["version"] == trigger_v2.version
    assert payload["health_details"]["trigger_ref"]["path"] == trigger_v2.path
    assert payload["health_details"]["health"] == "stale"
    assert payload["health_details"]["trigger_ref"]["entity_id"] == "billy"
    assert payload["artifact_type"] == scene_ref.artifact_type


@pytest.mark.unit
def test_impact_preview_endpoint_returns_scope(tmp_path: Path) -> None:
    client = _make_client(tmp_path)
    project_path = tmp_path / "project-impact-preview"
    project_id = _init_project(client, project_path)
    _store, trigger_v2, scene_ref, _shot_ref = _seed_stale_graph(project_path)

    response = client.post(
        f"/api/projects/{project_id}/impact/preview",
        json={
            "artifact_ref": scene_ref.model_dump(mode="json"),
            "model": "claude-sonnet-4-6",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["trigger_artifact_ref"]["path"] == trigger_v2.path
    assert payload["requested_artifact_ref"]["path"] == scene_ref.path
    assert payload["total_stale"] == 2
    assert set(payload["affected_types"]) == {"scene", "shot_plan"}


@pytest.mark.unit
def test_impact_assess_and_override_endpoints(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _make_client(tmp_path)
    project_path = tmp_path / "project-impact-routes"
    project_id = _init_project(client, project_path)
    _store, _trigger_v2, scene_ref, _shot_ref = _seed_stale_graph(project_path)

    class _FakeImpactService(ImpactAssessmentService):
        def __init__(self, *, project_dir, store=None, role_catalog=None, llm_callable=_fake_llm):
            super().__init__(
                project_dir=project_dir,
                store=store,
                role_catalog=role_catalog,
                llm_callable=_fake_llm,
            )

    monkeypatch.setattr(
        "cine_forge.api.artifact_manager.ImpactAssessmentService",
        _FakeImpactService,
    )

    assess = client.post(
        f"/api/projects/{project_id}/impact/assess",
        json={"artifact_ref": scene_ref.model_dump(mode="json"), "role_id": "director"},
    )
    assert assess.status_code == 200
    assess_payload = assess.json()
    assert assess_payload["assessment"]["total_needs_revision"] == 1
    assert assess_payload["assessment"]["total_confirmed_valid"] == 1

    detail_after_assess = client.get(f"/api/projects/{project_id}/artifacts/scene/scene_001/1")
    assert detail_after_assess.status_code == 200
    assert detail_after_assess.json()["health"] == ArtifactHealth.NEEDS_REVISION.value

    override = client.post(
        f"/api/projects/{project_id}/impact/override",
        json={
            "artifact_ref": scene_ref.model_dump(mode="json"),
            "target_health": "valid",
            "rationale": "User updated the scene manually.",
        },
    )
    assert override.status_code == 200
    override_payload = override.json()
    assert override_payload["health"] == ArtifactHealth.VALID.value
    assert override_payload["health_details"]["source_kind"] == "manual_override"


@pytest.mark.unit
def test_impact_assess_endpoint_supports_selected_refs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _make_client(tmp_path)
    project_path = tmp_path / "project-impact-selected"
    project_id = _init_project(client, project_path)
    _store, _trigger_v2, scene_ref, shot_ref = _seed_stale_graph(project_path)

    class _FakeImpactService(ImpactAssessmentService):
        def __init__(self, *, project_dir, store=None, role_catalog=None, llm_callable=_fake_llm):
            super().__init__(
                project_dir=project_dir,
                store=store,
                role_catalog=role_catalog,
                llm_callable=_fake_llm,
            )

    monkeypatch.setattr(
        "cine_forge.api.artifact_manager.ImpactAssessmentService",
        _FakeImpactService,
    )

    assess = client.post(
        f"/api/projects/{project_id}/impact/assess",
        json={
            "artifact_ref": scene_ref.model_dump(mode="json"),
            "selected_artifact_refs": [scene_ref.model_dump(mode="json")],
            "role_id": "director",
        },
    )

    assert assess.status_code == 200
    payload = assess.json()
    assert len(payload["assessment"]["assessments"]) == 1
    assert payload["assessment"]["assessments"][0]["artifact_ref"]["path"] == scene_ref.path

    detail_after_assess = client.get(f"/api/projects/{project_id}/artifacts/scene/scene_001/1")
    assert detail_after_assess.status_code == 200
    assert detail_after_assess.json()["health"] == ArtifactHealth.NEEDS_REVISION.value

    shot_detail = client.get(f"/api/projects/{project_id}/artifacts/shot_plan/scene_001/1")
    assert shot_detail.status_code == 200
    assert shot_detail.json()["health"] == ArtifactHealth.STALE.value
    assert shot_detail.json()["artifact_type"] == shot_ref.artifact_type
    assert shot_detail.json()["version"] == shot_ref.version


@pytest.mark.unit
def test_impact_assess_endpoint_rejects_budget_cap(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _make_client(tmp_path)
    project_path = tmp_path / "project-impact-budget"
    project_id = _init_project(client, project_path)
    _store, _trigger_v2, scene_ref, _shot_ref = _seed_stale_graph(project_path)

    class _FakeImpactService(ImpactAssessmentService):
        def __init__(self, *, project_dir, store=None, role_catalog=None, llm_callable=_fake_llm):
            super().__init__(
                project_dir=project_dir,
                store=store,
                role_catalog=role_catalog,
                llm_callable=_fake_llm,
            )

    monkeypatch.setattr(
        "cine_forge.api.artifact_manager.ImpactAssessmentService",
        _FakeImpactService,
    )

    assess = client.post(
        f"/api/projects/{project_id}/impact/assess",
        json={
            "artifact_ref": scene_ref.model_dump(mode="json"),
            "role_id": "director",
            "budget_cap_usd": 0.0001,
        },
    )

    assert assess.status_code == 422
    payload = assess.json()
    assert "budget cap" in payload["message"]
