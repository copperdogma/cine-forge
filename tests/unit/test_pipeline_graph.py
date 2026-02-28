"""Unit tests for the pipeline capability graph."""

from __future__ import annotations

from pathlib import Path

import pytest

from cine_forge.artifacts import ArtifactStore
from cine_forge.pipeline.graph import (
    PIPELINE_NODES,
    PIPELINE_PHASES,
    NodeStatus,
    PhaseStatus,
    check_prerequisites,
    compute_node_status,
    compute_phase_status,
    compute_pipeline_graph,
    get_available_actions,
    trace_staleness,
)
from cine_forge.schemas import ArtifactMetadata


def _metadata() -> ArtifactMetadata:
    return ArtifactMetadata(
        lineage=[],
        intent="test",
        rationale="test",
        confidence=1.0,
        source="human",
    )


# ---------------------------------------------------------------------------
# Graph definition integrity
# ---------------------------------------------------------------------------

_NODE_MAP = {n.id: n for n in PIPELINE_NODES}
_PHASE_MAP = {p.id: p for p in PIPELINE_PHASES}


@pytest.mark.unit
def test_all_node_ids_are_unique() -> None:
    ids = [n.id for n in PIPELINE_NODES]
    assert len(ids) == len(set(ids)), f"Duplicate node IDs: {ids}"


@pytest.mark.unit
def test_all_phase_ids_are_unique() -> None:
    ids = [p.id for p in PIPELINE_PHASES]
    assert len(ids) == len(set(ids)), f"Duplicate phase IDs: {ids}"


@pytest.mark.unit
def test_all_dependencies_reference_valid_nodes() -> None:
    for node in PIPELINE_NODES:
        for dep in node.dependencies:
            assert dep in _NODE_MAP, (
                f"Node '{node.id}' has invalid dependency '{dep}'"
            )


@pytest.mark.unit
def test_all_phase_node_ids_reference_valid_nodes() -> None:
    for phase in PIPELINE_PHASES:
        for nid in phase.node_ids:
            assert nid in _NODE_MAP, (
                f"Phase '{phase.id}' references invalid node '{nid}'"
            )


@pytest.mark.unit
def test_no_dependency_cycles() -> None:
    """Dependencies must always reference earlier nodes in the list."""
    order = {n.id: i for i, n in enumerate(PIPELINE_NODES)}
    for node in PIPELINE_NODES:
        for dep in node.dependencies:
            assert order[dep] < order[node.id], (
                f"Cycle: '{node.id}' depends on '{dep}' which comes after it"
            )


@pytest.mark.unit
def test_every_node_belongs_to_a_phase() -> None:
    all_phase_nodes = set()
    for phase in PIPELINE_PHASES:
        all_phase_nodes.update(phase.node_ids)
    for node in PIPELINE_NODES:
        assert node.id in all_phase_nodes, (
            f"Node '{node.id}' is not listed in any phase"
        )


# ---------------------------------------------------------------------------
# Status computation — empty store
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_empty_store_first_node_available(tmp_path: Path) -> None:
    """script_import has no dependencies, so it should be available in an empty store."""
    store = ArtifactStore(project_dir=tmp_path / "project")
    node = _NODE_MAP["script_import"]
    status, count = compute_node_status(node, store, {})
    assert status == NodeStatus.AVAILABLE
    assert count == 0


@pytest.mark.unit
def test_empty_store_dependent_node_blocked(tmp_path: Path) -> None:
    """normalization depends on script_import, which isn't completed."""
    store = ArtifactStore(project_dir=tmp_path / "project")
    resolved = {"script_import": NodeStatus.AVAILABLE}
    node = _NODE_MAP["normalization"]
    status, _count = compute_node_status(node, store, resolved)
    assert status == NodeStatus.BLOCKED


@pytest.mark.unit
def test_unimplemented_node_status(tmp_path: Path) -> None:
    store = ArtifactStore(project_dir=tmp_path / "project")
    node = _NODE_MAP["shot_planning"]
    assert not node.implemented
    status, count = compute_node_status(node, store, {})
    assert status == NodeStatus.NOT_IMPLEMENTED
    assert count == 0


# ---------------------------------------------------------------------------
# Status computation — populated store
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_node_completed_when_artifact_exists(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    store = ArtifactStore(project_dir=project_dir)
    store.save_artifact(
        artifact_type="raw_input",
        entity_id="project",
        data={"content": "test script"},
        metadata=_metadata(),
    )
    node = _NODE_MAP["script_import"]
    status, count = compute_node_status(node, store, {})
    assert status == NodeStatus.COMPLETED
    assert count >= 1


@pytest.mark.unit
def test_bible_node_completed_when_entries_exist(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    store = ArtifactStore(project_dir=project_dir)
    store.save_bible_entry(
        entity_type="character",
        entity_id="mariner",
        display_name="The Mariner",
        files=[{
            "filename": "bible.md",
            "purpose": "master_definition",
            "version": 1,
            "provenance": "ai_extracted",
        }],
        data_files={"bible.md": "Character description"},
        metadata=_metadata(),
    )
    node = _NODE_MAP["characters"]
    resolved = {"entity_discovery": NodeStatus.COMPLETED}
    status, count = compute_node_status(node, store, resolved)
    assert status == NodeStatus.COMPLETED
    assert count >= 1


@pytest.mark.unit
def test_in_progress_status(tmp_path: Path) -> None:
    store = ArtifactStore(project_dir=tmp_path / "project")
    node = _NODE_MAP["script_import"]
    status, _count = compute_node_status(
        node, store, {}, active_stages={"script_import"},
    )
    assert status == NodeStatus.IN_PROGRESS


@pytest.mark.unit
def test_node_available_when_deps_completed(tmp_path: Path) -> None:
    """normalization should be available when script_import is completed."""
    project_dir = tmp_path / "project"
    store = ArtifactStore(project_dir=project_dir)
    store.save_artifact(
        artifact_type="raw_input",
        entity_id="project",
        data={"content": "test"},
        metadata=_metadata(),
    )
    resolved = {"script_import": NodeStatus.COMPLETED}
    node = _NODE_MAP["normalization"]
    status, _count = compute_node_status(node, store, resolved)
    assert status == NodeStatus.AVAILABLE


# ---------------------------------------------------------------------------
# Phase status derivation
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_phase_completed_when_all_implemented_nodes_done() -> None:
    phase = _PHASE_MAP["script"]
    node_statuses = {
        "script_import": NodeStatus.COMPLETED,
        "normalization": NodeStatus.COMPLETED,
        "scene_extraction": NodeStatus.COMPLETED,
        "project_config": NodeStatus.COMPLETED,
    }
    assert compute_phase_status(phase, node_statuses) == PhaseStatus.COMPLETED


@pytest.mark.unit
def test_phase_partial_when_some_nodes_done() -> None:
    phase = _PHASE_MAP["script"]
    node_statuses = {
        "script_import": NodeStatus.COMPLETED,
        "normalization": NodeStatus.AVAILABLE,
        "scene_extraction": NodeStatus.BLOCKED,
        "project_config": NodeStatus.AVAILABLE,
    }
    assert compute_phase_status(phase, node_statuses) == PhaseStatus.PARTIAL


@pytest.mark.unit
def test_phase_blocked_when_all_blocked() -> None:
    phase = _PHASE_MAP["world"]
    node_statuses = {
        "entity_discovery": NodeStatus.BLOCKED,
        "characters": NodeStatus.BLOCKED,
        "locations": NodeStatus.BLOCKED,
        "props": NodeStatus.BLOCKED,
        "entity_graph": NodeStatus.BLOCKED,
        "continuity": NodeStatus.BLOCKED,
    }
    assert compute_phase_status(phase, node_statuses) == PhaseStatus.BLOCKED


@pytest.mark.unit
def test_phase_not_started_when_all_unimplemented() -> None:
    """A phase with only unimplemented nodes shows as not_started."""
    phase = _PHASE_MAP["production"]
    node_statuses = {
        "render": NodeStatus.NOT_IMPLEMENTED,
        "final_output": NodeStatus.NOT_IMPLEMENTED,
    }
    assert compute_phase_status(phase, node_statuses) == PhaseStatus.NOT_STARTED


# ---------------------------------------------------------------------------
# Full graph computation
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_compute_pipeline_graph_empty_store(tmp_path: Path) -> None:
    store = ArtifactStore(project_dir=tmp_path / "project")
    graph = compute_pipeline_graph(store)

    assert "phases" in graph
    assert "nodes" in graph
    assert "edges" in graph
    assert len(graph["phases"]) == 6
    assert len(graph["nodes"]) == 23

    # script_import should be available (no deps).
    si = next(n for n in graph["nodes"] if n["id"] == "script_import")
    assert si["status"] == "available"

    # normalization should be blocked (depends on script_import).
    norm = next(n for n in graph["nodes"] if n["id"] == "normalization")
    assert norm["status"] == "blocked"

    # Look & Feel is implemented but blocked (deps not met in empty store).
    lf = next(n for n in graph["nodes"] if n["id"] == "look_and_feel")
    assert lf["status"] == "blocked"


@pytest.mark.unit
def test_compute_pipeline_graph_with_artifacts(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    store = ArtifactStore(project_dir=project_dir)

    # Simulate completed script phase.
    for atype in ["raw_input", "canonical_script", "script_bible", "scene_index", "project_config"]:
        store.save_artifact(
            artifact_type=atype,
            entity_id="project",
            data={"content": "test"},
            metadata=_metadata(),
        )

    graph = compute_pipeline_graph(store)

    # Script phase should be completed.
    script_phase = next(p for p in graph["phases"] if p["id"] == "script")
    assert script_phase["status"] == "completed"

    # Entity discovery should be available (depends on scene_extraction which is done).
    ed = next(n for n in graph["nodes"] if n["id"] == "entity_discovery")
    assert ed["status"] == "available"


@pytest.mark.unit
def test_active_run_marks_in_progress(tmp_path: Path) -> None:
    store = ArtifactStore(project_dir=tmp_path / "project")
    graph = compute_pipeline_graph(store, active_run_stages={"script_import"})

    si = next(n for n in graph["nodes"] if n["id"] == "script_import")
    assert si["status"] == "in_progress"


@pytest.mark.unit
def test_edges_match_dependencies() -> None:
    """Every dependency should produce an edge."""
    expected_edges = set()
    for node in PIPELINE_NODES:
        for dep in node.dependencies:
            expected_edges.add((dep, node.id))

    assert len(expected_edges) > 0, "Expected some edges in the graph"


# ---------------------------------------------------------------------------
# Navigation helpers — get_available_actions
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_get_available_actions_empty_store(tmp_path: Path) -> None:
    """Only script_import should be available in an empty store."""
    store = ArtifactStore(project_dir=tmp_path / "project")
    graph = compute_pipeline_graph(store)
    actions = get_available_actions(graph)

    assert len(actions) >= 1
    assert actions[0]["node_id"] == "script_import"


@pytest.mark.unit
def test_get_available_actions_partial_script(tmp_path: Path) -> None:
    """With script_import done, normalization and project_config should be available."""
    project_dir = tmp_path / "project"
    store = ArtifactStore(project_dir=project_dir)
    store.save_artifact(
        artifact_type="raw_input",
        entity_id="project",
        data={"content": "test"},
        metadata=_metadata(),
    )
    graph = compute_pipeline_graph(store)
    actions = get_available_actions(graph)

    action_ids = [a["node_id"] for a in actions]
    assert "normalization" in action_ids
    assert "project_config" in action_ids


@pytest.mark.unit
def test_get_available_actions_prioritizes_partial_phase(tmp_path: Path) -> None:
    """Actions in a partial phase should come before actions in other phases."""
    project_dir = tmp_path / "project"
    store = ArtifactStore(project_dir=project_dir)

    # Complete most of script phase but not all.
    for atype in ["raw_input", "canonical_script", "scene_index"]:
        store.save_artifact(
            artifact_type=atype,
            entity_id="project",
            data={"content": "test"},
            metadata=_metadata(),
        )

    graph = compute_pipeline_graph(store)
    actions = get_available_actions(graph)

    # project_config is in partial "script" phase, so should come first.
    assert len(actions) >= 1
    first_action = actions[0]
    assert first_action["phase_id"] == "script"
    reason = first_action["reason"].lower()
    assert "partial" in reason or "continue" in reason


@pytest.mark.unit
def test_get_available_actions_none_when_all_done_or_blocked(tmp_path: Path) -> None:
    """With script done and world blocked (no entity_discovery), no world actions available."""
    project_dir = tmp_path / "project"
    store = ArtifactStore(project_dir=project_dir)

    # Complete all script phase.
    for atype in ["raw_input", "canonical_script", "scene_index", "project_config"]:
        store.save_artifact(
            artifact_type=atype,
            entity_id="project",
            data={"content": "test"},
            metadata=_metadata(),
        )

    graph = compute_pipeline_graph(store)
    actions = get_available_actions(graph)

    # Entity discovery should be available since script is done.
    action_ids = [a["node_id"] for a in actions]
    assert "entity_discovery" in action_ids
    # But characters should not be (depends on entity_discovery).
    assert "characters" not in action_ids


# ---------------------------------------------------------------------------
# Navigation helpers — check_prerequisites
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_check_prerequisites_all_met(tmp_path: Path) -> None:
    """Normalization prereqs are met when script_import is completed."""
    project_dir = tmp_path / "project"
    store = ArtifactStore(project_dir=project_dir)
    store.save_artifact(
        artifact_type="raw_input",
        entity_id="project",
        data={"content": "test"},
        metadata=_metadata(),
    )
    graph = compute_pipeline_graph(store)
    prereqs = check_prerequisites("normalization", graph)

    assert prereqs["is_ready"] is True
    assert len(prereqs["met"]) == 1
    assert prereqs["met"][0]["id"] == "script_import"
    assert len(prereqs["unmet"]) == 0


@pytest.mark.unit
def test_check_prerequisites_missing(tmp_path: Path) -> None:
    """Characters has unmet prereqs when entity_discovery hasn't run."""
    store = ArtifactStore(project_dir=tmp_path / "project")
    graph = compute_pipeline_graph(store)
    prereqs = check_prerequisites("characters", graph)

    assert prereqs["is_ready"] is False
    assert len(prereqs["unmet"]) >= 1
    unmet_ids = [u["id"] for u in prereqs["unmet"]]
    assert "entity_discovery" in unmet_ids


@pytest.mark.unit
def test_check_prerequisites_node_with_no_deps(tmp_path: Path) -> None:
    """script_import has no dependencies — always ready."""
    store = ArtifactStore(project_dir=tmp_path / "project")
    graph = compute_pipeline_graph(store)
    prereqs = check_prerequisites("script_import", graph)

    assert prereqs["is_ready"] is True
    assert len(prereqs["met"]) == 0
    assert len(prereqs["unmet"]) == 0


@pytest.mark.unit
def test_check_prerequisites_unknown_node(tmp_path: Path) -> None:
    """Unknown node ID returns not-ready with error."""
    store = ArtifactStore(project_dir=tmp_path / "project")
    graph = compute_pipeline_graph(store)
    prereqs = check_prerequisites("nonexistent_node", graph)

    assert prereqs["is_ready"] is False


@pytest.mark.unit
def test_check_prerequisites_unimplemented_dep(tmp_path: Path) -> None:
    """shot_planning depends on look_and_feel which is not implemented."""
    store = ArtifactStore(project_dir=tmp_path / "project")
    graph = compute_pipeline_graph(store)
    prereqs = check_prerequisites("shot_planning", graph)

    assert prereqs["is_ready"] is False
    unmet_ids = [u["id"] for u in prereqs["unmet"]]
    assert "look_and_feel" in unmet_ids


# ---------------------------------------------------------------------------
# Staleness tracing
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_trace_staleness_returns_cause(tmp_path: Path) -> None:
    """When an upstream artifact is updated, downstream shows stale reason."""
    project_dir = tmp_path / "project"
    store = ArtifactStore(project_dir=project_dir)

    # Create v1 of raw_input and canonical_script (with lineage).
    from cine_forge.schemas import ArtifactRef

    store.save_artifact(
        artifact_type="raw_input",
        entity_id="project",
        data={"content": "v1"},
        metadata=_metadata(),
    )
    raw_ref_v1 = ArtifactRef(
        artifact_type="raw_input",
        entity_id="project",
        version=1,
        path="artifacts/raw_input/project/v1/data.json",
    )
    store.save_artifact(
        artifact_type="canonical_script",
        entity_id="project",
        data={"content": "v1"},
        metadata=ArtifactMetadata(
            lineage=[raw_ref_v1],
            intent="test",
            rationale="test",
            confidence=1.0,
            source="ai",
        ),
    )
    # Now update raw_input to v2 — this should mark canonical_script stale.
    store.save_artifact(
        artifact_type="raw_input",
        entity_id="project",
        data={"content": "v2"},
        metadata=_metadata(),
    )

    node = _NODE_MAP["normalization"]
    reason = trace_staleness(node, store)
    assert reason is not None
    assert "Script Import" in reason


@pytest.mark.unit
def test_trace_staleness_returns_none_when_not_stale(tmp_path: Path) -> None:
    """Non-stale nodes should return None."""
    project_dir = tmp_path / "project"
    store = ArtifactStore(project_dir=project_dir)
    store.save_artifact(
        artifact_type="raw_input",
        entity_id="project",
        data={"content": "test"},
        metadata=_metadata(),
    )
    node = _NODE_MAP["script_import"]
    reason = trace_staleness(node, store)
    assert reason is None


@pytest.mark.unit
def test_stale_reason_in_graph_output(tmp_path: Path) -> None:
    """The compute_pipeline_graph output should include stale_reason."""
    project_dir = tmp_path / "project"
    store = ArtifactStore(project_dir=project_dir)

    from cine_forge.schemas import ArtifactRef

    store.save_artifact(
        artifact_type="raw_input",
        entity_id="project",
        data={"content": "v1"},
        metadata=_metadata(),
    )
    raw_ref_v1 = ArtifactRef(
        artifact_type="raw_input",
        entity_id="project",
        version=1,
        path="artifacts/raw_input/project/v1/data.json",
    )
    store.save_artifact(
        artifact_type="canonical_script",
        entity_id="project",
        data={"content": "v1"},
        metadata=ArtifactMetadata(
            lineage=[raw_ref_v1],
            intent="test",
            rationale="test",
            confidence=1.0,
            source="ai",
        ),
    )
    # Update raw_input to v2.
    store.save_artifact(
        artifact_type="raw_input",
        entity_id="project",
        data={"content": "v2"},
        metadata=_metadata(),
    )

    graph = compute_pipeline_graph(store)
    norm = next(n for n in graph["nodes"] if n["id"] == "normalization")
    assert norm["status"] == "stale"
    assert "stale_reason" in norm
    assert "Script Import" in norm["stale_reason"]
