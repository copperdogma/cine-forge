from __future__ import annotations

from pathlib import Path

import pytest

from cine_forge.driver.engine import DriverEngine
from cine_forge.modules.timeline.track_system_v1.main import best_for_scene
from cine_forge.schemas import ArtifactHealth, ArtifactMetadata, ArtifactRef, TrackManifest


@pytest.mark.integration
def test_track_system_recipe_builds_manifest_and_stale_propagates(tmp_path: Path) -> None:
    workspace_root = Path(__file__).resolve().parents[2]
    engine = DriverEngine(workspace_root=workspace_root, project_dir=tmp_path / "project")

    ingest_state = engine.run(
        recipe_path=(
            workspace_root / "tests" / "fixtures" / "recipes" / "recipe-ingest-extract.yaml"
        ),
        run_id="integration-track-upstream",
        force=True,
        runtime_params={
            "input_file": str(workspace_root / "samples" / "sample-screenplay.fountain")
        },
    )
    assert ingest_state["stages"]["breakdown_scenes"]["status"] == "done"

    timeline_state = engine.run(
        recipe_path=workspace_root / "configs" / "recipes" / "recipe-timeline.yaml",
        run_id="integration-track-timeline",
        force=True,
    )
    assert timeline_state["stages"]["timeline"]["status"] == "done"

    track_state = engine.run(
        recipe_path=workspace_root / "configs" / "recipes" / "recipe-track-system.yaml",
        run_id="integration-track-build",
        force=True,
    )
    assert track_state["stages"]["tracks"]["status"] == "done"

    refs = [
        ArtifactRef.model_validate(item)
        for item in track_state["stages"]["tracks"]["artifact_refs"]
    ]
    track_ref = next(ref for ref in refs if ref.artifact_type == "track_manifest")
    track_artifact = engine.store.load_artifact(track_ref)
    manifest = TrackManifest.model_validate(track_artifact.data)

    assert manifest.track_fill_counts.get("script", 0) >= 1

    first_scene = manifest.entries[0].scene_id
    resolved = best_for_scene(manifest, scene_id=first_scene)
    assert resolved["resolved"] is True

    script_entry = next(entry for entry in manifest.entries if entry.track_type == "script")
    old_health = engine.store.graph.get_health(track_ref)
    assert old_health in {ArtifactHealth.VALID, ArtifactHealth.CONFIRMED_VALID}

    scene_artifact = engine.store.load_artifact(script_entry.artifact_ref)
    engine.store.save_artifact(
        artifact_type="scene",
        entity_id=script_entry.artifact_ref.entity_id,
        data=scene_artifact.data,
        metadata=ArtifactMetadata(
            lineage=[script_entry.artifact_ref],
            intent="integration update",
            rationale="trigger downstream staleness for track manifest",
            confidence=1.0,
            source="code",
        ),
    )

    assert engine.store.graph.get_health(track_ref) == ArtifactHealth.STALE
