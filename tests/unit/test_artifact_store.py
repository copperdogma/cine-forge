from __future__ import annotations

from pathlib import Path

import pytest

from cine_forge.artifacts import ArtifactStore, DependencyGraph
from cine_forge.schemas import ArtifactHealth, ArtifactMetadata, ArtifactRef


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


# ---------------------------------------------------------------------------
# DependencyGraph staleness propagation regression tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_new_version_not_marked_stale(tmp_path: Path) -> None:
    """Regression for Bug 1: saving A:v2 must not mark A:v2 itself as stale."""
    graph = DependencyGraph(project_dir=tmp_path)
    ref_v1 = ArtifactRef(artifact_type="scene", entity_id="a", version=1, path="s/v1.json")
    ref_v2 = ArtifactRef(artifact_type="scene", entity_id="a", version=2, path="s/v2.json")

    graph.register_artifact(ref_v1, [])
    graph.register_artifact(ref_v2, [ref_v1])
    graph.propagate_stale_for_new_version(ref_v2)

    assert graph.get_health(ref_v2) == ArtifactHealth.VALID
    assert ref_v2 not in graph.get_stale()


@pytest.mark.unit
def test_sibling_not_marked_stale_via_shared_intermediate(tmp_path: Path) -> None:
    """Sibling artifacts must not be marked stale through a shared intermediate.

    Reproduces the world-building recipe scenario where 13 scenes are enriched
    in parallel, each listing scene_index:v2 in its lineage. When scene_001:v3's
    propagation runs, it must not contaminate scene_002:v3 via scene_index:v2.

    Graph (→ = downstream edge):
        scene_index:v1 → scene:001:v2, scene:002:v2
        scene:001:v2   → scene_index:v2
        scene:002:v2   → scene_index:v2
        scene_index:v2 → scene:001:v3, scene:002:v3
        scene:001:v3   → scene_index:v3
        scene:002:v3   → scene_index:v3
    """
    graph = DependencyGraph(project_dir=tmp_path)

    idx_v1 = ArtifactRef(artifact_type="scene_index", entity_id=None, version=1, path="idx/v1.json")
    s001_v2 = ArtifactRef(artifact_type="scene", entity_id="001", version=2, path="s001/v2.json")
    s002_v2 = ArtifactRef(artifact_type="scene", entity_id="002", version=2, path="s002/v2.json")
    idx_v2 = ArtifactRef(artifact_type="scene_index", entity_id=None, version=2, path="idx/v2.json")
    s001_v3 = ArtifactRef(artifact_type="scene", entity_id="001", version=3, path="s001/v3.json")
    s002_v3 = ArtifactRef(artifact_type="scene", entity_id="002", version=3, path="s002/v3.json")
    idx_v3 = ArtifactRef(artifact_type="scene_index", entity_id=None, version=3, path="idx/v3.json")

    graph.register_artifact(idx_v1, [])
    graph.register_artifact(s001_v2, [idx_v1])
    graph.register_artifact(s002_v2, [idx_v1])
    graph.register_artifact(idx_v2, [s001_v2, s002_v2])
    graph.register_artifact(s001_v3, [idx_v2])
    graph.register_artifact(s002_v3, [idx_v2])
    graph.register_artifact(idx_v3, [s001_v3, s002_v3])  # rebuilt index — key for the fix

    # Simulate: scene_001:v3 is saved first and propagation runs.
    # Without the fix, scene_002:v3 is incorrectly marked stale via scene_index:v2.
    graph.propagate_stale_for_new_version(s001_v3)

    assert graph.get_health(s002_v3) == ArtifactHealth.VALID
