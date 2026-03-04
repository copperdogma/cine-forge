"""Integration tests for the Design Study API endpoints.

Covers the full loop: bible exists → generate → view state → decide → verify persistence.
Uses TestClient (no real HTTP server) and mocks generate_image to avoid Imagen API calls.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from cine_forge.api.app import create_app
from cine_forge.artifacts.store import ArtifactStore
from cine_forge.schemas import ArtifactMetadata


def _create_mock_bible(project_path: Path, entity_id: str) -> None:
    """Write a minimal bible_manifest artifact so the generate endpoint can load it.

    entity_id is the full prefixed form: 'character_mariner'.
    save_bible_entry takes entity_type + slug separately and builds the full key internally.
    """
    store = ArtifactStore(project_dir=project_path)

    # entity_id is e.g. "character_mariner" — split into type + slug
    entity_type, _, slug = entity_id.partition("_")

    master_definition = json.dumps({
        "name": "The Mariner",
        "description": "A grizzled old sailor.",
        "narrative_role": "protagonist",
        "inferred_traits": [
            {"trait": "build", "value": "broad-shouldered"},
        ],
    })

    store.save_bible_entry(
        entity_type=entity_type,
        entity_id=slug,
        display_name="The Mariner",
        files=[{
            "filename": "master_definition.json",
            "purpose": "master_definition",
            "version": 1,
            "provenance": "ai_extracted",
        }],
        data_files={"master_definition.json": master_definition},
        metadata=ArtifactMetadata(
            intent="test bible",
            rationale="integration test fixture",
            confidence=1.0,
            source="human",
            producing_module="test",
        ),
    )


_FAKE_JPEG = bytes([0xFF, 0xD8, 0xFF, 0xE0] + [0x00] * 100)  # minimal JPEG header stub


@pytest.mark.integration
def test_design_study_generate_decide_loop(tmp_path: Path) -> None:
    """Full loop: bible ready → generate → state has image → decide → state updated."""
    workspace_root = Path(__file__).resolve().parents[2]
    app = create_app(workspace_root=workspace_root)
    client = TestClient(app)

    # Create and open a project
    project_path = tmp_path / "design-study-integration"
    created = client.post("/api/projects/new", json={"project_path": str(project_path)})
    assert created.status_code == 200
    project_id = created.json()["project_id"]

    entity_id = "character_mariner"

    # Seed a bible so the generate endpoint can load bible data
    _create_mock_bible(project_path, entity_id)

    # --- Step 1: GET before any study exists → 404 ---
    resp = client.get(f"/api/projects/{project_id}/design-study/{entity_id}")
    assert resp.status_code == 404

    # --- Step 2: Generate — mock generate_image to avoid real API call ---
    with patch(
        "cine_forge.api.routers.design_study.generate_image",
        return_value=(_FAKE_JPEG, "imagen-4.0-generate-001"),
    ):
        resp = client.post(
            f"/api/projects/{project_id}/design-study/{entity_id}/generate",
            json={"entity_type": "character", "count": 2},
        )

    assert resp.status_code == 200, resp.text
    state = resp.json()
    assert state["entity_id"] == entity_id
    assert len(state["rounds"]) == 1
    assert len(state["rounds"][0]["images"]) == 2
    image_filename = state["rounds"][0]["images"][0]["filename"]
    assert image_filename.startswith("design_study_r1_img")

    # Verify the image file was actually written to disk
    image_path = project_path / "artifacts" / "bibles" / entity_id / image_filename
    assert image_path.exists(), f"Image file not written: {image_path}"

    # --- Step 3: GET state returns same data ---
    resp = client.get(f"/api/projects/{project_id}/design-study/{entity_id}")
    assert resp.status_code == 200
    fetched = resp.json()
    assert fetched["entity_id"] == entity_id
    assert len(fetched["rounds"]) == 1

    # --- Step 4: Decide — mark first image as selected_final ---
    resp = client.post(
        f"/api/projects/{project_id}/design-study/{entity_id}/decide",
        json={"filename": image_filename, "decision": "selected_final"},
    )
    assert resp.status_code == 200
    assert resp.json()["updated"] is True

    # --- Step 5: Verify decision persisted ---
    resp = client.get(f"/api/projects/{project_id}/design-study/{entity_id}")
    assert resp.status_code == 200
    final_state = resp.json()
    assert final_state["selected_final_filename"] == image_filename
    img_entry = final_state["rounds"][0]["images"][0]
    assert img_entry["decision"] == "selected_final"

    # --- Step 6: Decide — mark second image as seed_for_variants with guidance ---
    second_filename = state["rounds"][0]["images"][1]["filename"]
    resp = client.post(
        f"/api/projects/{project_id}/design-study/{entity_id}/decide",
        json={
            "filename": second_filename,
            "decision": "seed_for_variants",
            "guidance": "more weathered, darker costume",
        },
    )
    assert resp.status_code == 200

    # Verify guidance persisted
    resp = client.get(f"/api/projects/{project_id}/design-study/{entity_id}")
    assert resp.status_code == 200
    second_entry = resp.json()["rounds"][0]["images"][1]
    assert second_entry["decision"] == "seed_for_variants"
    assert second_entry["guidance"] == "more weathered, darker costume"

    # --- Step 7: Generate a second round (count=1) ---
    with patch(
        "cine_forge.api.routers.design_study.generate_image",
        return_value=(_FAKE_JPEG, "imagen-4.0-generate-001"),
    ):
        resp = client.post(
            f"/api/projects/{project_id}/design-study/{entity_id}/generate",
            json={
                "entity_type": "character",
                "count": 1,
                "guidance": "more weathered",
                "seed_image_filename": second_filename,
            },
        )
    assert resp.status_code == 200
    state2 = resp.json()
    assert len(state2["rounds"]) == 2
    assert state2["rounds"][1]["round_number"] == 2
    assert len(state2["rounds"][1]["images"]) == 1
    # selected_final from round 1 should still be set
    assert state2["selected_final_filename"] == image_filename

    # --- Step 8: Serve image file ---
    resp = client.get(
        f"/api/projects/{project_id}/design-study/{entity_id}/images/{image_filename}"
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/jpeg"


@pytest.mark.integration
def test_design_study_generate_requires_bible(tmp_path: Path) -> None:
    """Generate returns 404 when no bible exists for the entity."""
    workspace_root = Path(__file__).resolve().parents[2]
    app = create_app(workspace_root=workspace_root)
    client = TestClient(app)

    project_path = tmp_path / "design-study-no-bible"
    created = client.post("/api/projects/new", json={"project_path": str(project_path)})
    assert created.status_code == 200
    project_id = created.json()["project_id"]

    resp = client.post(
        f"/api/projects/{project_id}/design-study/character_ghost/generate",
        json={"entity_type": "character", "count": 1},
    )
    assert resp.status_code == 404
    assert "bible" in resp.json()["message"].lower()


@pytest.mark.integration
def test_design_study_decide_unknown_image(tmp_path: Path) -> None:
    """Decide returns 404 for a filename not in the study."""
    workspace_root = Path(__file__).resolve().parents[2]
    app = create_app(workspace_root=workspace_root)
    client = TestClient(app)

    project_path = tmp_path / "design-study-decide-404"
    created = client.post("/api/projects/new", json={"project_path": str(project_path)})
    assert created.status_code == 200
    project_id = created.json()["project_id"]

    entity_id = "character_mariner"
    _create_mock_bible(project_path, entity_id)

    # Generate one image first
    with patch(
        "cine_forge.api.routers.design_study.generate_image",
        return_value=(_FAKE_JPEG, "imagen-4.0-generate-001"),
    ):
        client.post(
            f"/api/projects/{project_id}/design-study/{entity_id}/generate",
            json={"entity_type": "character", "count": 1},
        )

    # Try to decide on a nonexistent filename
    resp = client.post(
        f"/api/projects/{project_id}/design-study/{entity_id}/decide",
        json={"filename": "design_study_r99_img1.jpg", "decision": "favorite"},
    )
    assert resp.status_code == 404
