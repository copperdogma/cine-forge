from __future__ import annotations

from pathlib import Path

import pytest

from cine_forge.driver.engine import DriverEngine
from cine_forge.schemas import ArtifactHealth, ArtifactMetadata, ArtifactRef


@pytest.mark.integration
def test_timeline_recipe_builds_project_timeline_from_store_inputs(tmp_path: Path) -> None:
    workspace_root = Path(__file__).resolve().parents[2]
    # Use tmp_path for project_dir to ensure no stale artifacts
    project_dir = tmp_path / "project"
    engine = DriverEngine(workspace_root=workspace_root, project_dir=project_dir)

    ingest_state = engine.run(
        recipe_path=workspace_root / "configs" / "recipes" / "recipe-ingest-extract.yaml",
        run_id="integration-timeline-upstream",
        force=True,
        runtime_params={
            "input_file": str(workspace_root / "samples" / "sample-screenplay.fountain")
        },
    )
    assert ingest_state["stages"]["extract"]["status"] == "done"

    timeline_state = engine.run(
        recipe_path=workspace_root / "configs" / "recipes" / "recipe-timeline.yaml",
        run_id="integration-timeline-build",
        force=True,
    )
    assert timeline_state["stages"]["timeline"]["status"] == "done"

    refs = [
        ArtifactRef.model_validate(item)
        for item in timeline_state["stages"]["timeline"]["artifact_refs"]
    ]
    timeline_ref = next(ref for ref in refs if ref.artifact_type == "timeline")
    timeline_artifact = engine.store.load_artifact(timeline_ref)

    assert timeline_artifact.data["total_scenes"] >= 1
    assert timeline_artifact.data["estimated_runtime_seconds"] >= 0.0
    assert len(timeline_artifact.data["entries"]) == timeline_artifact.data["total_scenes"]

    first_scene_ref = ArtifactRef.model_validate(timeline_artifact.data["entries"][0]["scene_ref"])
    old_health = engine.store.graph.get_health(timeline_ref)
    assert old_health in {ArtifactHealth.VALID, ArtifactHealth.CONFIRMED_VALID}

    scene_artifact = engine.store.load_artifact(first_scene_ref)
    engine.store.save_artifact(
        artifact_type="scene",
        entity_id=first_scene_ref.entity_id,
        data=scene_artifact.data,
        metadata=ArtifactMetadata(
            lineage=[first_scene_ref],
            intent="integration update",
            rationale="trigger downstream staleness for timeline",
            confidence=1.0,
            source="code",
        ),
    )
    assert engine.store.graph.get_health(timeline_ref) == ArtifactHealth.STALE
