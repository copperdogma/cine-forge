from __future__ import annotations

import json
from pathlib import Path

import pytest

from cine_forge.api.artifact_editing import apply_artifact_edit
from cine_forge.artifacts.store import ArtifactStore
from cine_forge.schemas import ArtifactMetadata


def _seed_metadata() -> ArtifactMetadata:
    return ArtifactMetadata(
        intent="seed",
        rationale="seed artifact",
        confidence=1.0,
        source="human",
        producing_module="tests.seed",
    )


@pytest.mark.unit
def test_apply_artifact_edit_versions_bible_manifest_and_master_file(tmp_path: Path) -> None:
    store = ArtifactStore(project_dir=tmp_path)
    metadata = _seed_metadata()
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
        metadata=metadata,
    )
    manifest, _ = store.load_bible_entry(initial_ref)

    next_ref = apply_artifact_edit(
        project_path=tmp_path,
        artifact_type="bible_manifest",
        entity_id="character_aria",
        data=manifest.model_dump(mode="json"),
        rationale="Age Aria up for the revised script draft.",
        source="ai",
        producing_role="assistant",
        chat_message_id="user_789",
        bible_files={
            "master_v1.json": {
                "name": "Aria",
                "description": "An older, sharp-eyed mechanic with deep crow's feet.",
            }
        },
    )

    assert next_ref.version == 2
    assert next_ref.path.endswith("artifacts/bibles/character_aria/manifest_v2.json")
    assert [
        ref.version for ref in store.list_versions("bible_manifest", "character_aria")
    ] == [1, 2]

    latest_manifest, latest_metadata = store.load_bible_entry(next_ref)
    latest_master = json.loads(
        (tmp_path / "artifacts" / "bibles" / "character_aria" / "master_v2.json").read_text(
            encoding="utf-8"
        )
    )

    assert latest_manifest.display_name == "Aria"
    assert latest_manifest.files[0].filename == "master_v2.json"
    assert latest_manifest.files[0].version == 2
    assert latest_manifest.files[0].provenance == "ai_inferred"
    assert latest_master["description"] == "An older, sharp-eyed mechanic with deep crow's feet."
    assert latest_metadata.source == "ai"
    assert latest_metadata.producing_role == "assistant"
    assert latest_metadata.annotations["chat_message_id"] == "user_789"
    assert latest_metadata.annotations["edit_origin"] == "chat"


@pytest.mark.unit
def test_apply_artifact_edit_records_ai_metadata_for_plain_json_artifact(tmp_path: Path) -> None:
    store = ArtifactStore(project_dir=tmp_path)
    initial_ref = store.save_artifact(
        artifact_type="script_bible",
        entity_id=None,
        data={"premise": "A sailor returns home."},
        metadata=_seed_metadata(),
    )

    next_ref = apply_artifact_edit(
        project_path=tmp_path,
        artifact_type="script_bible",
        entity_id=None,
        data={"premise": "A sailor returns home older and more haunted."},
        rationale="Apply the user's canon revision.",
        source="ai",
        producing_role="assistant",
        chat_message_id="user_101",
    )

    artifact = store.load_artifact(next_ref)

    assert initial_ref.version == 1
    assert next_ref.version == 2
    assert artifact.data["premise"] == "A sailor returns home older and more haunted."
    assert artifact.metadata.source == "ai"
    assert artifact.metadata.producing_role == "assistant"
    assert artifact.metadata.annotations["chat_message_id"] == "user_101"
    assert artifact.metadata.lineage == [initial_ref]
