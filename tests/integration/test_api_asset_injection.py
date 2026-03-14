from __future__ import annotations

import base64
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from cine_forge.api.app import create_app
from cine_forge.artifacts import ArtifactStore
from cine_forge.schemas import ArtifactMetadata

_PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAAAAAA6fptVAAAACklEQVR4nGNgAAAAAgABSK+kcQAAAABJRU5ErkJggg=="
)


def _init_project(client: TestClient, project_path: Path) -> str:
    response = client.post("/api/projects/new", json={"project_path": str(project_path)})
    assert response.status_code == 200
    return response.json()["project_id"]


def _seed_character_bible(project_path: Path, character_id: str = "aria") -> None:
    store = ArtifactStore(project_dir=project_path)
    store.save_bible_entry(
        entity_type="character",
        entity_id=character_id,
        display_name="Aria",
        files=[
            {
                "filename": "master_v1.json",
                "purpose": "master_definition",
                "version": 1,
                "provenance": "ai_extracted",
            }
        ],
        data_files={"master_v1.json": '{"character_id":"aria","name":"Aria"}'},
        metadata=ArtifactMetadata(
            lineage=[],
            intent="seed character bible",
            rationale="integration test seed",
            confidence=1.0,
            source="code",
        ),
    )


@pytest.mark.integration
def test_asset_api_injects_file_and_accepts_lock_change(tmp_path: Path) -> None:
    client = TestClient(create_app(workspace_root=tmp_path))
    project_path = tmp_path / "asset-project"
    project_id = _init_project(client, project_path)
    _seed_character_bible(project_path)

    inject = client.post(
        f"/api/projects/{project_id}/assets/inject",
        data={
            "target_kind": "character",
            "target_id": "aria",
            "purpose": "actor_photo",
            "lock_status": "hard_locked",
        },
        files={"file": ("aria.png", _PNG_BYTES, "image/png")},
    )
    assert inject.status_code == 200
    manifest = inject.json()
    asset = manifest["assets"][0]
    assert asset["lock_status"] == "hard_locked"

    served = client.get(f"/api/projects/{project_id}/assets/file/{asset['file_path']}")
    assert served.status_code == 200
    assert served.headers["content-type"].startswith("image/")

    proposal = client.post(
        f"/api/projects/{project_id}/assets/character/aria/{asset['asset_id']}/propose-lock-change",
        json={
            "source_role": "director",
            "proposed_lock_status": "soft_locked",
            "rationale": "Allow wardrobe exploration while keeping the actor likeness.",
            "confidence": 0.88,
        },
    )
    assert proposal.status_code == 200
    suggestion_id = proposal.json()["suggestion_id"]

    response = client.post(
        f"/api/projects/{project_id}/assets/lock-proposals/{suggestion_id}/respond",
        json={
            "decision": "accept",
            "decided_by": "human",
            "reason": "Approved for iterative look development.",
        },
    )
    assert response.status_code == 200
    assert response.json()["target_version"] == "2"

    latest = client.get(f"/api/projects/{project_id}/assets/character/aria")
    assert latest.status_code == 200
    assert latest.json()["assets"][0]["lock_status"] == "soft_locked"


@pytest.mark.integration
def test_asset_api_returns_empty_manifest_before_first_upload(tmp_path: Path) -> None:
    client = TestClient(create_app(workspace_root=tmp_path))
    project_path = tmp_path / "asset-project"
    project_id = _init_project(client, project_path)
    _seed_character_bible(project_path)

    response = client.get(f"/api/projects/{project_id}/assets/character/aria")
    assert response.status_code == 200
    assert response.json() == {
        "target_kind": "character",
        "target_id": "aria",
        "display_name": "Aria",
        "assets": [],
        "version": 0,
        "created_at": response.json()["created_at"],
    }
