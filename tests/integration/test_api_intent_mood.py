from __future__ import annotations

import io
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from cine_forge.api.app import create_app
from cine_forge.artifacts.store import ArtifactStore
from cine_forge.schemas import ArtifactMetadata
from cine_forge.services import InjectedAssetService


def _metadata(intent: str) -> ArtifactMetadata:
    return ArtifactMetadata(
        intent=intent,
        rationale=f"{intent} fixture",
        confidence=1.0,
        source="human",
        producing_module="test",
    )


def _jpeg_bytes(color: tuple[int, int, int] = (34, 56, 82)) -> bytes:
    buffer = io.BytesIO()
    image = Image.new("RGB", (1280, 720), color=color)
    image.save(buffer, format="JPEG", quality=90)
    return buffer.getvalue()


@pytest.mark.integration
def test_intent_mood_roundtrip_and_creative_brief_preview(tmp_path: Path) -> None:
    workspace_root = Path(__file__).resolve().parents[2]
    app = create_app(workspace_root=workspace_root)
    client = TestClient(app)

    project_path = tmp_path / "intent-brief-integration"
    created = client.post("/api/projects/new", json={"project_path": str(project_path)})
    assert created.status_code == 200
    project_id = created.json()["project_id"]

    store = ArtifactStore(project_dir=project_path)
    store.save_artifact(
        artifact_type="project_config",
        entity_id="project",
        data={
            "title": "The Mariner",
            "format": "feature",
            "genre": ["nautical drama"],
            "tone": ["bleak", "windswept"],
            "production_format": "live_action",
        },
        metadata=_metadata("seed project config"),
    )
    InjectedAssetService(project_path).inject_asset(
        target_kind="project",
        target_id="project",
        purpose="mood_board",
        filename="storm_palette_board.jpg",
        content=_jpeg_bytes(),
        lock_status="soft_locked",
        content_type="image/jpeg",
    )

    save_resp = client.post(
        f"/api/projects/{project_id}/intent-mood",
        json={
            "scope": "project",
            "mood_descriptors": ["lonely", "ominous"],
            "reference_films": ["The Lighthouse"],
            "filmmaker_anchors": ["Robert Eggers"],
            "style_preset_id": "gothic-horror",
            "natural_language_intent": "Make the world feel ancient and judging.",
            "look_notes": "Salt-crusted wardrobe and cold cyan palette.",
        },
    )
    assert save_resp.status_code == 200, save_resp.text
    payload = save_resp.json()
    assert payload["filmmaker_anchors"] == ["Robert Eggers"]
    assert payload["look_notes"] == "Salt-crusted wardrobe and cold cyan palette."

    preview_resp = client.get(f"/api/projects/{project_id}/intent-mood/creative-brief")
    assert preview_resp.status_code == 200, preview_resp.text
    preview = preview_resp.json()
    assert preview["visual_medium"] == "live_action"
    assert preview["filmmaker_anchors"] == ["Robert Eggers"]
    assert "project_references" in preview["sources_used"]
    assert preview["active_project_references"][0]["filename"] == "storm_palette_board.jpg"
