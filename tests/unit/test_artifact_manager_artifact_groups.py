from __future__ import annotations

import json
from pathlib import Path

import pytest

from cine_forge.api.artifact_manager import ArtifactManager
from cine_forge.artifacts import ArtifactStore
from cine_forge.schemas import ArtifactMetadata, ArtifactRef


def _manager(project_path: Path) -> ArtifactManager:
    return ArtifactManager(
        project_path_resolver=lambda _project_id: project_path,
        role_context_factory=lambda _project_id: None,
        role_catalog=object(),
    )


def _metadata(intent: str) -> ArtifactMetadata:
    return ArtifactMetadata(
        intent=intent,
        rationale="seed test artifact",
        confidence=1.0,
        source="code",
        producing_module="tests.unit",
    )


def _save_character_bible(
    store: ArtifactStore,
    *,
    character_id: str,
    name: str,
) -> ArtifactRef:
    return store.save_artifact(
        artifact_type="character_bible",
        entity_id=character_id,
        data={"character_id": character_id, "name": name},
        metadata=_metadata(f"seed {name} character bible"),
    )


def _save_character_manifest(
    store: ArtifactStore,
    *,
    character_id: str,
    name: str,
) -> ArtifactRef:
    return _save_bible_manifest(
        store,
        entity_type="character",
        entity_id=character_id,
        name=name,
    )


def _save_bible_manifest(
    store: ArtifactStore,
    *,
    entity_type: str,
    entity_id: str,
    name: str,
) -> ArtifactRef:
    master_filename = "master_v1.json"
    return store.save_bible_entry(
        entity_type=entity_type,
        entity_id=entity_id,
        display_name=name,
        files=[
            {
                "filename": master_filename,
                "purpose": "master_definition",
                "version": 1,
                "provenance": "ai_extracted",
            }
        ],
        data_files={
            master_filename: json.dumps(
                {"entity_id": entity_id, "name": name},
                indent=2,
            )
        },
        metadata=_metadata(f"seed {name} bible manifest"),
    )


@pytest.mark.unit
def test_artifact_groups_hide_stage_retired_entity_groups(tmp_path: Path) -> None:
    project_path = tmp_path / "project"
    store = ArtifactStore(project_dir=project_path)
    brick_ref = _save_character_bible(store, character_id="brick", name="BRICK")
    _save_character_bible(
        store,
        character_id="brick_braddock",
        name="BRICK BRADDOCK",
    )
    brick_manifest_ref = _save_character_manifest(
        store,
        character_id="brick",
        name="Brick",
    )
    _save_character_manifest(
        store,
        character_id="brick_braddock",
        name="Brick Braddock",
    )
    brick_state_ref = store.save_artifact(
        artifact_type="continuity_state",
        entity_id="character_brick_scene_001",
        data={"entity_id": "brick", "scene_id": "scene_001"},
        metadata=_metadata("seed Brick continuity state"),
    )
    store.save_artifact(
        artifact_type="continuity_state",
        entity_id="character_brick_braddock_scene_001",
        data={"entity_id": "brick_braddock", "scene_id": "scene_001"},
        metadata=_metadata("seed Brick Braddock continuity state"),
    )

    (project_path / "stage_cache.json").write_text(
        json.dumps(
            {
                "world_building": {
                    "character_bible": {
                        "artifact_refs": [
                            brick_ref.model_dump(mode="json"),
                            brick_manifest_ref.model_dump(mode="json"),
                            brick_state_ref.model_dump(mode="json"),
                        ],
                        "stage_fingerprint": "test",
                        "updated_at": 1,
                    }
                }
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    groups = _manager(project_path).list_artifact_groups("project-id")
    group_keys = {
        (group["artifact_type"], group["entity_id"])
        for group in groups
        if "brick" in str(group["entity_id"])
    }

    assert ("character_bible", "brick") in group_keys
    assert ("bible_manifest", "character_brick") in group_keys
    assert ("continuity_state", "character_brick_scene_001") in group_keys
    assert ("character_bible", "brick_braddock") not in group_keys
    assert ("bible_manifest", "character_brick_braddock") not in group_keys
    assert ("continuity_state", "character_brick_braddock_scene_001") not in group_keys

    retired_bible_versions = _manager(project_path).list_artifact_versions(
        "project-id",
        "character_bible",
        "brick_braddock",
    )
    retired_manifest_versions = _manager(project_path).list_artifact_versions(
        "project-id",
        "bible_manifest",
        "character_brick_braddock",
    )
    retired_state_versions = _manager(project_path).list_artifact_versions(
        "project-id",
        "continuity_state",
        "character_brick_braddock_scene_001",
    )

    assert [version["version"] for version in retired_bible_versions] == [1]
    assert [version["version"] for version in retired_manifest_versions] == [1]
    assert [version["version"] for version in retired_state_versions] == [1]
    assert (
        _manager(project_path).read_artifact(
            "project-id",
            "character_bible",
            "brick_braddock",
            1,
        )["payload"]["data"]["name"]
        == "BRICK BRADDOCK"
    )


@pytest.mark.unit
def test_artifact_groups_preserve_directory_listing_without_stage_cache(
    tmp_path: Path,
) -> None:
    project_path = tmp_path / "project"
    store = ArtifactStore(project_dir=project_path)
    _save_character_bible(store, character_id="brick", name="BRICK")
    _save_character_bible(
        store,
        character_id="brick_braddock",
        name="BRICK BRADDOCK",
    )

    groups = _manager(project_path).list_artifact_groups("project-id")
    character_ids = {
        group["entity_id"]
        for group in groups
        if group["artifact_type"] == "character_bible"
    }

    assert character_ids == {"brick", "brick_braddock"}


@pytest.mark.unit
def test_artifact_groups_preserve_directory_listing_without_usable_stage_cache(
    tmp_path: Path,
) -> None:
    project_path = tmp_path / "project"
    store = ArtifactStore(project_dir=project_path)
    _save_character_bible(store, character_id="brick", name="BRICK")
    _save_character_bible(
        store,
        character_id="brick_braddock",
        name="BRICK BRADDOCK",
    )

    (project_path / "stage_cache.json").write_text(
        json.dumps(
            {
                "world_building": {
                    "character_bible": {
                        "artifact_refs": [
                            {
                                "artifact_type": "character_bible",
                                "entity_id": "brick",
                                "path": "artifacts/character_bible/brick/missing.json",
                                "version": 99,
                            }
                        ],
                        "stage_fingerprint": "test",
                        "updated_at": 1,
                    }
                }
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    groups = _manager(project_path).list_artifact_groups("project-id")
    character_ids = {
        group["entity_id"]
        for group in groups
        if group["artifact_type"] == "character_bible"
    }

    assert character_ids == {"brick", "brick_braddock"}


@pytest.mark.unit
def test_artifact_groups_do_not_hide_unrelated_bible_namespaces(
    tmp_path: Path,
) -> None:
    project_path = tmp_path / "project"
    store = ArtifactStore(project_dir=project_path)
    brick_ref = _save_character_bible(store, character_id="brick", name="BRICK")
    _save_character_bible(
        store,
        character_id="brick_braddock",
        name="BRICK BRADDOCK",
    )
    brick_manifest_ref = _save_character_manifest(
        store,
        character_id="brick",
        name="Brick",
    )
    _save_character_manifest(
        store,
        character_id="brick_braddock",
        name="Brick Braddock",
    )
    diner_manifest_ref = _save_bible_manifest(
        store,
        entity_type="location",
        entity_id="diner",
        name="Diner",
    )

    (project_path / "stage_cache.json").write_text(
        json.dumps(
            {
                "world_building": {
                    "character_bible": {
                        "artifact_refs": [
                            brick_ref.model_dump(mode="json"),
                            brick_manifest_ref.model_dump(mode="json"),
                        ],
                        "stage_fingerprint": "test",
                        "updated_at": 1,
                    }
                }
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    group_keys = {
        (group["artifact_type"], group["entity_id"])
        for group in _manager(project_path).list_artifact_groups("project-id")
    }

    assert ("bible_manifest", "character_brick") in group_keys
    assert ("bible_manifest", "character_brick_braddock") not in group_keys
    assert ("bible_manifest", "location_diner") in group_keys
    assert (
        _manager(project_path).read_artifact(
            "project-id",
            "bible_manifest",
            diner_manifest_ref.entity_id or "",
            diner_manifest_ref.version,
        )["payload"]["data"]["display_name"]
        == "Diner"
    )
