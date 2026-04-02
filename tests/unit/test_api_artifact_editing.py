from __future__ import annotations

import json
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


@pytest.mark.unit
def test_edit_artifact_endpoint_records_ai_provenance_for_plain_json(tmp_path: Path) -> None:
    client = _make_client(tmp_path)
    project_path = tmp_path / "output" / "project-ai-edit"
    project_id = _init_project(client, project_path)

    store = ArtifactStore(project_dir=project_path)
    store.save_artifact(
        artifact_type="script_bible",
        entity_id=None,
        data={"premise": "A sailor returns home."},
        metadata=_seed_metadata(),
    )

    response = client.post(
        f"/api/projects/{project_id}/artifacts/script_bible/__project__/edit",
        json={
            "data": {"premise": "A sailor returns home older and more haunted."},
            "rationale": "Apply the user's canon revision.",
            "source": "ai",
            "producing_role": "assistant",
            "chat_message_id": "user_101",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["version"] == 2

    detail = client.get(f"/api/projects/{project_id}/artifacts/script_bible/__project__/2")
    assert detail.status_code == 200
    detail_payload = detail.json()

    assert detail_payload["payload"]["data"]["premise"] == (
        "A sailor returns home older and more haunted."
    )
    assert detail_payload["payload"]["metadata"]["source"] == "ai"
    assert detail_payload["payload"]["metadata"]["producing_role"] == "assistant"
    assert (
        detail_payload["payload"]["metadata"]["annotations"]["chat_message_id"]
        == "user_101"
    )


@pytest.mark.unit
def test_edit_artifact_endpoint_versions_bible_manifest_through_manifest_path(
    tmp_path: Path,
) -> None:
    client = _make_client(tmp_path)
    project_path = tmp_path / "output" / "project-bible-ai-edit"
    project_id = _init_project(client, project_path)

    store = ArtifactStore(project_dir=project_path)
    initial_ref = store.save_bible_entry(
        entity_type="character",
        entity_id="aria",
        display_name="Aria",
        files=[
            {
                "filename": "master_v1.json",
                "purpose": "master_definition",
                "version": 1,
                "provenance": "system",
            }
        ],
        data_files={
            "master_v1.json": json.dumps(
                {"name": "Aria", "description": "A sharp-eyed mechanic."},
                indent=2,
            )
        },
        metadata=_seed_metadata(),
    )
    manifest, _ = store.load_bible_entry(initial_ref)

    response = client.post(
        f"/api/projects/{project_id}/artifacts/bible_manifest/character_aria/edit",
        json={
            "data": manifest.model_dump(mode="json"),
            "rationale": "Age Aria up for the revised script draft.",
            "source": "ai",
            "producing_role": "assistant",
            "chat_message_id": "user_789",
            "bible_files": {
                "master_v1.json": {
                    "name": "Aria",
                    "description": "An older, sharp-eyed mechanic with deep crow's feet.",
                }
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["version"] == 2
    assert payload["path"].endswith("artifacts/bibles/character_aria/manifest_v2.json")

    versions = client.get(f"/api/projects/{project_id}/artifacts/bible_manifest/character_aria")
    assert versions.status_code == 200
    assert [item["version"] for item in versions.json()] == [1, 2]

    detail = client.get(f"/api/projects/{project_id}/artifacts/bible_manifest/character_aria/2")
    assert detail.status_code == 200
    detail_payload = detail.json()

    assert "master_v2.json" in detail_payload["bible_files"]
    assert detail_payload["bible_files"]["master_v2.json"]["description"] == (
        "An older, sharp-eyed mechanic with deep crow's feet."
    )
    assert detail_payload["payload"]["metadata"]["source"] == "ai"
    assert detail_payload["payload"]["metadata"]["producing_role"] == "assistant"
