from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from cine_forge.api.app import create_app
from cine_forge.artifacts import ArtifactStore
from cine_forge.schemas import ArtifactMetadata


def _make_client(workspace_root: Path) -> TestClient:
    return TestClient(create_app(workspace_root=workspace_root))


def _init_project(client: TestClient, project_path: Path) -> str:
    response = client.post("/api/projects/new", json={"project_path": str(project_path)})
    assert response.status_code == 200
    return response.json()["project_id"]


def _seed_metadata() -> ArtifactMetadata:
    return ArtifactMetadata(
        intent="seed",
        rationale="seed artifact",
        confidence=1.0,
        source="human",
        producing_module="tests.seed",
    )


def _seed_artifact(
    store: ArtifactStore,
    *,
    artifact_type: str,
    entity_id: str | None,
    data: dict[str, object],
) -> None:
    store.save_artifact(
        artifact_type=artifact_type,
        entity_id=entity_id,
        data=data,
        metadata=_seed_metadata(),
    )


@pytest.mark.unit
def test_scene_readiness_endpoint_returns_canonical_states(tmp_path: Path) -> None:
    client = _make_client(tmp_path)
    project_path = tmp_path / "output" / "scene-readiness-project"
    project_id = _init_project(client, project_path)

    store = ArtifactStore(project_dir=project_path)
    _seed_artifact(
        store,
        artifact_type="scene",
        entity_id="scene_001",
        data={"display_name": "INT. KITCHEN - NIGHT"},
    )
    _seed_artifact(
        store,
        artifact_type="intent_mood",
        entity_id="project",
        data={"mood_descriptors": ["tense"], "user_approved": True},
    )
    _seed_artifact(
        store,
        artifact_type="look_and_feel",
        entity_id="scene_001",
        data={"lighting_concept": "Low-key practicals.", "user_approved": True},
    )
    _seed_artifact(
        store,
        artifact_type="sound_and_music",
        entity_id="scene_001",
        data={"ambient_environment": "Fridge hum and distant traffic.", "user_approved": False},
    )
    _seed_artifact(
        store,
        artifact_type="character_and_performance",
        entity_id="scene_001",
        data={
            "scene_id": "scene_001",
            "entries": [{"character_id": "john"}],
            "user_approved": False,
        },
    )
    _seed_artifact(
        store,
        artifact_type="story_world",
        entity_id="project",
        data={
            "character_design_baselines": ["john_default"],
            "user_approved": True,
        },
    )

    response = client.get(f"/api/projects/{project_id}/scenes/scene_001/readiness")

    assert response.status_code == 200
    payload = response.json()
    assert payload == {
        "scene_id": "scene_001",
        "intent_mood": "green",
        "look_and_feel": "green",
        "sound_and_music": "yellow",
        "rhythm_and_flow": "red",
        "character_and_performance": "yellow",
        "story_world": "green",
    }


@pytest.mark.unit
def test_scene_readiness_endpoint_returns_404_for_missing_scene(tmp_path: Path) -> None:
    client = _make_client(tmp_path)
    project_path = tmp_path / "output" / "scene-readiness-missing-scene"
    project_id = _init_project(client, project_path)

    response = client.get(f"/api/projects/{project_id}/scenes/scene_missing/readiness")

    assert response.status_code == 404
    assert response.json()["code"] == "scene_not_found"
