from __future__ import annotations

from pathlib import Path

import pytest

from cine_forge.artifacts import ArtifactStore
from cine_forge.schemas import ArtifactMetadata


def _metadata(*, lineage: list = None) -> ArtifactMetadata:
    return ArtifactMetadata(
        lineage=lineage or [],
        intent="test artifact",
        rationale="unit validation",
        alternatives_considered=[],
        confidence=1.0,
        source="human",
        schema_version="1.0.0",
    )


@pytest.mark.unit
def test_artifact_store_save_load_list_and_diff(tmp_path: Path) -> None:
    store = ArtifactStore(project_dir=tmp_path / "project")
    ref_v1 = store.save_artifact(
        artifact_type="scene",
        entity_id="scene_1",
        data={"content": "A"},
        metadata=_metadata(),
    )
    ref_v2 = store.save_artifact(
        artifact_type="scene",
        entity_id="scene_1",
        data={"content": "B"},
        metadata=_metadata(),
    )

    loaded = store.load_artifact(ref_v2)
    versions = store.list_versions(artifact_type="scene", entity_id="scene_1")
    diff = store.diff_versions(ref_a=ref_v1, ref_b=ref_v2)

    assert loaded.data["content"] == "B"
    assert [ref.version for ref in versions] == [1, 2]
    assert diff["content"]["kind"] == "changed"


@pytest.mark.unit
def test_artifact_store_immutability_enforced(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = ArtifactStore(project_dir=tmp_path / "project")
    ref = store.save_artifact(
        artifact_type="script",
        entity_id="script",
        data={"text": "draft"},
        metadata=_metadata(),
    )
    monkeypatch.setattr(store, "_next_version", lambda artifact_dir: ref.version)

    with pytest.raises(FileExistsError):
        store.save_artifact(
            artifact_type="script",
            entity_id="script",
            data={"text": "draft 2"},
            metadata=_metadata(),
        )


@pytest.mark.unit
def test_dependency_tracking_and_staleness_propagation(tmp_path: Path) -> None:
    store = ArtifactStore(project_dir=tmp_path / "project")
    source_v1 = store.save_artifact(
        artifact_type="script",
        entity_id="project",
        data={"text": "v1"},
        metadata=_metadata(),
    )
    dependent = store.save_artifact(
        artifact_type="scene",
        entity_id="scene_1",
        data={"summary": "derived"},
        metadata=_metadata(lineage=[source_v1]),
    )
    _ = store.save_artifact(
        artifact_type="script",
        entity_id="project",
        data={"text": "v2"},
        metadata=_metadata(),
    )

    upstream = store.graph.get_dependencies(dependent)
    stale_refs = store.graph.get_stale()

    assert upstream and upstream[0].version == 1
    assert any(ref.artifact_type == "scene" and ref.entity_id == "scene_1" for ref in stale_refs)
