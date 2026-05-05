from __future__ import annotations

import json
from pathlib import Path

import pytest

from cine_forge.api.artifact_editing import apply_artifact_edit
from cine_forge.api.exceptions import ServiceError
from cine_forge.artifacts.store import ArtifactStore
from cine_forge.schemas import ArtifactMetadata, ArtifactRef


def _seed_metadata() -> ArtifactMetadata:
    return ArtifactMetadata(
        intent="seed",
        rationale="seed artifact",
        confidence=1.0,
        source="human",
        producing_module="tests.seed",
    )


def _seed_brick_bible(store: ArtifactStore) -> ArtifactRef:
    return store.save_bible_entry(
        entity_type="character",
        entity_id="brick_braddock",
        display_name="BRICK BRADDOCK",
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
                {
                    "character_id": "brick_braddock",
                    "name": "BRICK BRADDOCK",
                    "description": "Duplicate full-name artifact.",
                },
                indent=2,
            )
        },
        metadata=_seed_metadata(),
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
                {
                    "character_id": "aria",
                    "name": "Aria",
                    "description": "A sharp-eyed mechanic.",
                },
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
                "character_id": "aria",
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
def test_apply_artifact_edit_rejects_bible_identity_merge_in_master_file(
    tmp_path: Path,
) -> None:
    store = ArtifactStore(project_dir=tmp_path)
    initial_ref = _seed_brick_bible(store)
    manifest, _ = store.load_bible_entry(initial_ref)

    with pytest.raises(ServiceError) as excinfo:
        apply_artifact_edit(
            project_path=tmp_path,
            artifact_type="bible_manifest",
            entity_id="character_brick_braddock",
            data=manifest.model_dump(mode="json"),
            rationale="Merge duplicate Brick Braddock into Brick.",
            source="ai",
            producing_role="assistant",
            chat_message_id="user_198",
            bible_files={
                "master_v1.json": {
                    "character_id": "brick",
                    "name": "BRICK",
                    "description": "Canonical Brick artifact.",
                }
            },
        )

    assert excinfo.value.code == "unsupported_artifact_edit"
    assert "identity merge/deprecation" in excinfo.value.message
    assert store.list_versions("bible_manifest", "character_brick_braddock") == [
        initial_ref
    ]


@pytest.mark.unit
def test_apply_artifact_edit_rejects_bible_identity_removal_in_master_file(
    tmp_path: Path,
) -> None:
    store = ArtifactStore(project_dir=tmp_path)
    initial_ref = _seed_brick_bible(store)
    manifest, _ = store.load_bible_entry(initial_ref)

    with pytest.raises(ServiceError) as excinfo:
        apply_artifact_edit(
            project_path=tmp_path,
            artifact_type="bible_manifest",
            entity_id="character_brick_braddock",
            data=manifest.model_dump(mode="json"),
            rationale="Deprecate duplicate Brick Braddock without updating references.",
            source="ai",
            producing_role="assistant",
            chat_message_id="user_198",
            bible_files={
                "master_v1.json": {
                    "name": "BRICK BRADDOCK",
                    "description": "Duplicate full-name artifact.",
                }
            },
        )

    assert excinfo.value.code == "unsupported_artifact_edit"
    assert "identity merge/deprecation" in excinfo.value.message
    assert store.list_versions("bible_manifest", "character_brick_braddock") == [
        initial_ref
    ]


@pytest.mark.unit
def test_apply_artifact_edit_rejects_bible_camel_identity_drift_in_master_file(
    tmp_path: Path,
) -> None:
    store = ArtifactStore(project_dir=tmp_path)
    initial_ref = _seed_brick_bible(store)
    manifest, _ = store.load_bible_entry(initial_ref)

    with pytest.raises(ServiceError) as excinfo:
        apply_artifact_edit(
            project_path=tmp_path,
            artifact_type="bible_manifest",
            entity_id="character_brick_braddock",
            data=manifest.model_dump(mode="json"),
            rationale="Merge duplicate Brick Braddock into Brick.",
            source="ai",
            producing_role="assistant",
            chat_message_id="user_198",
            bible_files={
                "master_v1.json": {
                    "character_id": "brick_braddock",
                    "characterId": "brick",
                    "name": "BRICK BRADDOCK",
                    "description": "Duplicate full-name artifact.",
                }
            },
        )

    assert excinfo.value.code == "unsupported_artifact_edit"
    assert "identity merge/deprecation" in excinfo.value.message
    assert store.list_versions("bible_manifest", "character_brick_braddock") == [
        initial_ref
    ]


@pytest.mark.unit
def test_apply_artifact_edit_rejects_bible_generic_entity_id_drift_in_master_file(
    tmp_path: Path,
) -> None:
    store = ArtifactStore(project_dir=tmp_path)
    initial_ref = _seed_brick_bible(store)
    manifest, _ = store.load_bible_entry(initial_ref)

    with pytest.raises(ServiceError) as excinfo:
        apply_artifact_edit(
            project_path=tmp_path,
            artifact_type="bible_manifest",
            entity_id="character_brick_braddock",
            data=manifest.model_dump(mode="json"),
            rationale="Merge duplicate Brick Braddock into Brick.",
            source="ai",
            producing_role="assistant",
            chat_message_id="user_198",
            bible_files={
                "master_v1.json": {
                    "character_id": "brick_braddock",
                    "entityId": "brick",
                    "name": "BRICK BRADDOCK",
                    "description": "Duplicate full-name artifact.",
                }
            },
        )

    assert excinfo.value.code == "unsupported_artifact_edit"
    assert "identity merge/deprecation" in excinfo.value.message
    assert store.list_versions("bible_manifest", "character_brick_braddock") == [
        initial_ref
    ]


@pytest.mark.unit
@pytest.mark.parametrize(
    "identity_payload",
    [
        {"profile": {"characterId": "brick"}},
        {"profile.characterId": "brick"},
        {"character.id": "brick"},
        {"entity.id": "brick"},
        {"profile": {"character": {"id": "brick"}}},
        {"references": [{"character": {"id": "brick"}}]},
    ],
)
def test_apply_artifact_edit_rejects_nested_identity_drift_in_master_file(
    tmp_path: Path,
    identity_payload: dict[str, object],
) -> None:
    store = ArtifactStore(project_dir=tmp_path)
    initial_ref = _seed_brick_bible(store)
    manifest, _ = store.load_bible_entry(initial_ref)

    with pytest.raises(ServiceError) as excinfo:
        apply_artifact_edit(
            project_path=tmp_path,
            artifact_type="bible_manifest",
            entity_id="character_brick_braddock",
            data=manifest.model_dump(mode="json"),
            rationale="Merge duplicate Brick Braddock into Brick.",
            source="ai",
            producing_role="assistant",
            chat_message_id="user_198",
            bible_files={
                "master_v1.json": {
                    "character_id": "brick_braddock",
                    **identity_payload,
                    "name": "BRICK BRADDOCK",
                    "description": "Duplicate full-name artifact.",
                }
            },
        )

    assert excinfo.value.code == "unsupported_artifact_edit"
    assert "identity merge/deprecation" in excinfo.value.message
    assert store.list_versions("bible_manifest", "character_brick_braddock") == [
        initial_ref
    ]


@pytest.mark.unit
def test_apply_artifact_edit_rejects_bible_merge_marker_in_master_file(
    tmp_path: Path,
) -> None:
    store = ArtifactStore(project_dir=tmp_path)
    initial_ref = _seed_brick_bible(store)
    manifest, _ = store.load_bible_entry(initial_ref)

    with pytest.raises(ServiceError) as excinfo:
        apply_artifact_edit(
            project_path=tmp_path,
            artifact_type="bible_manifest",
            entity_id="character_brick_braddock",
            data=manifest.model_dump(mode="json"),
            rationale="Mark duplicate Brick Braddock as merged into Brick.",
            source="ai",
            producing_role="assistant",
            chat_message_id="user_198",
            bible_files={
                "master_v1.json": {
                    "character_id": "brick_braddock",
                    "name": "BRICK BRADDOCK",
                    "description": "Duplicate full-name artifact.",
                    "merge_into": "brick",
                }
            },
        )

    assert excinfo.value.code == "unsupported_artifact_edit"
    assert "identity merge/deprecation" in excinfo.value.message
    assert store.list_versions("bible_manifest", "character_brick_braddock") == [
        initial_ref
    ]


@pytest.mark.unit
def test_apply_artifact_edit_rejects_nested_canonical_marker_in_master_file(
    tmp_path: Path,
) -> None:
    store = ArtifactStore(project_dir=tmp_path)
    initial_ref = _seed_brick_bible(store)
    manifest, _ = store.load_bible_entry(initial_ref)

    with pytest.raises(ServiceError) as excinfo:
        apply_artifact_edit(
            project_path=tmp_path,
            artifact_type="bible_manifest",
            entity_id="character_brick_braddock",
            data=manifest.model_dump(mode="json"),
            rationale="Mark duplicate Brick Braddock as canonicalized into Brick.",
            source="ai",
            producing_role="assistant",
            chat_message_id="user_198",
            bible_files={
                "master_v1.json": {
                    "character_id": "brick_braddock",
                    "name": "BRICK BRADDOCK",
                    "description": "Duplicate full-name artifact.",
                    "canonical": {"characterId": "brick"},
                }
            },
        )

    assert excinfo.value.code == "unsupported_artifact_edit"
    assert "identity merge/deprecation" in excinfo.value.message
    assert store.list_versions("bible_manifest", "character_brick_braddock") == [
        initial_ref
    ]


@pytest.mark.unit
def test_apply_artifact_edit_rejects_bible_manifest_identity_drift(
    tmp_path: Path,
) -> None:
    store = ArtifactStore(project_dir=tmp_path)
    initial_ref = _seed_brick_bible(store)
    manifest, _ = store.load_bible_entry(initial_ref)
    drifted_manifest = manifest.model_copy(update={"entity_id": "brick"})

    with pytest.raises(ServiceError) as excinfo:
        apply_artifact_edit(
            project_path=tmp_path,
            artifact_type="bible_manifest",
            entity_id="character_brick_braddock",
            data=drifted_manifest.model_dump(mode="json"),
            rationale="Move duplicate Brick Braddock into Brick.",
            source="ai",
            producing_role="assistant",
            chat_message_id="user_198",
        )

    assert excinfo.value.code == "unsupported_artifact_edit"
    assert "identity merge/deprecation" in excinfo.value.message
    assert store.list_versions("bible_manifest", "character_brick_braddock") == [
        initial_ref
    ]
    assert store.list_versions("bible_manifest", "character_brick") == []


@pytest.mark.unit
def test_apply_artifact_edit_rejects_existing_master_identity_drift(
    tmp_path: Path,
) -> None:
    store = ArtifactStore(project_dir=tmp_path)
    initial_ref = store.save_bible_entry(
        entity_type="character",
        entity_id="brick_braddock",
        display_name="BRICK BRADDOCK",
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
                {
                    "character_id": "brick",
                    "name": "BRICK",
                    "description": "Drifted master-definition artifact.",
                },
                indent=2,
            )
        },
        metadata=_seed_metadata(),
    )
    manifest, _ = store.load_bible_entry(initial_ref)

    with pytest.raises(ServiceError) as excinfo:
        apply_artifact_edit(
            project_path=tmp_path,
            artifact_type="bible_manifest",
            entity_id="character_brick_braddock",
            data=manifest.model_copy(update={"display_name": "Brick"}).model_dump(
                mode="json"
            ),
            rationale="Rename only the manifest display label.",
            source="ai",
            producing_role="assistant",
            chat_message_id="user_198",
        )

    assert excinfo.value.code == "unsupported_artifact_edit"
    assert "identity merge/deprecation" in excinfo.value.message
    assert store.list_versions("bible_manifest", "character_brick_braddock") == [
        initial_ref
    ]


@pytest.mark.unit
def test_apply_artifact_edit_rejects_existing_missing_master_identity(
    tmp_path: Path,
) -> None:
    store = ArtifactStore(project_dir=tmp_path)
    initial_ref = store.save_bible_entry(
        entity_type="character",
        entity_id="brick_braddock",
        display_name="BRICK BRADDOCK",
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
                {
                    "name": "BRICK BRADDOCK",
                    "description": "Master definition has lost its identity field.",
                },
                indent=2,
            )
        },
        metadata=_seed_metadata(),
    )
    manifest, _ = store.load_bible_entry(initial_ref)

    with pytest.raises(ServiceError) as excinfo:
        apply_artifact_edit(
            project_path=tmp_path,
            artifact_type="bible_manifest",
            entity_id="character_brick_braddock",
            data=manifest.model_copy(update={"display_name": "Brick"}).model_dump(
                mode="json"
            ),
            rationale="Rename only the manifest display label.",
            source="ai",
            producing_role="assistant",
            chat_message_id="user_198",
        )

    assert excinfo.value.code == "unsupported_artifact_edit"
    assert "identity merge/deprecation" in excinfo.value.message
    assert store.list_versions("bible_manifest", "character_brick_braddock") == [
        initial_ref
    ]


@pytest.mark.unit
def test_apply_artifact_edit_rejects_existing_master_drift_even_if_removed(
    tmp_path: Path,
) -> None:
    store = ArtifactStore(project_dir=tmp_path)
    initial_ref = store.save_bible_entry(
        entity_type="character",
        entity_id="brick_braddock",
        display_name="BRICK BRADDOCK",
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
                {
                    "character_id": "brick_braddock",
                    "entityId": "brick",
                    "name": "BRICK BRADDOCK",
                    "description": "Master definition has drifted toward Brick.",
                },
                indent=2,
            )
        },
        metadata=_seed_metadata(),
    )
    manifest, _ = store.load_bible_entry(initial_ref)

    with pytest.raises(ServiceError) as excinfo:
        apply_artifact_edit(
            project_path=tmp_path,
            artifact_type="bible_manifest",
            entity_id="character_brick_braddock",
            data=manifest.model_dump(mode="json"),
            rationale="Remove the drifted identity field while updating description.",
            source="ai",
            producing_role="assistant",
            chat_message_id="user_198",
            bible_files={
                "master_v1.json": {
                    "character_id": "brick_braddock",
                    "name": "BRICK BRADDOCK",
                    "description": "Keep the duplicate artifact description current.",
                }
            },
        )

    assert excinfo.value.code == "unsupported_artifact_edit"
    assert "identity merge/deprecation" in excinfo.value.message
    assert store.list_versions("bible_manifest", "character_brick_braddock") == [
        initial_ref
    ]


@pytest.mark.unit
def test_apply_artifact_edit_rejects_existing_merge_marker_even_if_removed(
    tmp_path: Path,
) -> None:
    store = ArtifactStore(project_dir=tmp_path)
    initial_ref = store.save_bible_entry(
        entity_type="character",
        entity_id="brick_braddock",
        display_name="BRICK BRADDOCK",
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
                {
                    "character_id": "brick_braddock",
                    "merge_into": "brick",
                    "name": "BRICK BRADDOCK",
                    "description": "Master definition has a merge marker.",
                },
                indent=2,
            )
        },
        metadata=_seed_metadata(),
    )
    manifest, _ = store.load_bible_entry(initial_ref)

    with pytest.raises(ServiceError) as excinfo:
        apply_artifact_edit(
            project_path=tmp_path,
            artifact_type="bible_manifest",
            entity_id="character_brick_braddock",
            data=manifest.model_dump(mode="json"),
            rationale="Remove the merge marker while updating description.",
            source="ai",
            producing_role="assistant",
            chat_message_id="user_198",
            bible_files={
                "master_v1.json": {
                    "character_id": "brick_braddock",
                    "name": "BRICK BRADDOCK",
                    "description": "Keep the duplicate artifact description current.",
                }
            },
        )

    assert excinfo.value.code == "unsupported_artifact_edit"
    assert "identity merge/deprecation" in excinfo.value.message
    assert store.list_versions("bible_manifest", "character_brick_braddock") == [
        initial_ref
    ]


@pytest.mark.unit
def test_apply_artifact_edit_rejects_empty_master_definition_update(
    tmp_path: Path,
) -> None:
    store = ArtifactStore(project_dir=tmp_path)
    initial_ref = _seed_brick_bible(store)
    manifest, _ = store.load_bible_entry(initial_ref)

    with pytest.raises(ServiceError) as excinfo:
        apply_artifact_edit(
            project_path=tmp_path,
            artifact_type="bible_manifest",
            entity_id="character_brick_braddock",
            data=manifest.model_dump(mode="json"),
            rationale="Replace the duplicate master with an empty file.",
            source="ai",
            producing_role="assistant",
            chat_message_id="user_198",
            bible_files={"master_v1.json": {}},
        )

    assert excinfo.value.code == "artifact_edit_invalid"
    assert "structured JSON content" in excinfo.value.message
    assert store.list_versions("bible_manifest", "character_brick_braddock") == [
        initial_ref
    ]


@pytest.mark.unit
def test_apply_artifact_edit_rejects_removed_master_definition_entry(
    tmp_path: Path,
) -> None:
    store = ArtifactStore(project_dir=tmp_path)
    initial_ref = _seed_brick_bible(store)
    manifest, _ = store.load_bible_entry(initial_ref)
    manifest_without_master = manifest.model_copy(update={"files": []})

    with pytest.raises(ServiceError) as excinfo:
        apply_artifact_edit(
            project_path=tmp_path,
            artifact_type="bible_manifest",
            entity_id="character_brick_braddock",
            data=manifest_without_master.model_dump(mode="json"),
            rationale="Remove the duplicate master definition.",
            source="ai",
            producing_role="assistant",
            chat_message_id="user_198",
        )

    assert excinfo.value.code == "artifact_edit_invalid"
    assert "preserve the current master-definition entry" in excinfo.value.message
    assert store.list_versions("bible_manifest", "character_brick_braddock") == [
        initial_ref
    ]


@pytest.mark.unit
def test_apply_artifact_edit_rejects_master_entry_metadata_drift(
    tmp_path: Path,
) -> None:
    store = ArtifactStore(project_dir=tmp_path)
    initial_ref = _seed_brick_bible(store)
    manifest, _ = store.load_bible_entry(initial_ref)
    drifted_entry = manifest.files[0].model_copy(
        update={"version": 99, "provenance": "user_injected"}
    )
    drifted_manifest = manifest.model_copy(update={"files": [drifted_entry]})

    with pytest.raises(ServiceError) as excinfo:
        apply_artifact_edit(
            project_path=tmp_path,
            artifact_type="bible_manifest",
            entity_id="character_brick_braddock",
            data=drifted_manifest.model_dump(mode="json"),
            rationale="Rewrite master entry metadata without a replacement payload.",
            source="ai",
            producing_role="assistant",
            chat_message_id="user_198",
        )

    assert excinfo.value.code == "artifact_edit_invalid"
    assert "preserve the current master-definition entry" in excinfo.value.message
    assert store.list_versions("bible_manifest", "character_brick_braddock") == [
        initial_ref
    ]


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
