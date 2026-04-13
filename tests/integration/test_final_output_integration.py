from __future__ import annotations

from pathlib import Path

import pytest

from cine_forge.driver.engine import DriverEngine
from cine_forge.schemas import (
    ArtifactHealth,
    ArtifactRef,
    FinalOutputArtifact,
    MediaValidationArtifact,
)
from tests.render_fixtures import seed_final_output_project


@pytest.mark.integration
def test_final_output_recipe_builds_partial_project_cut(tmp_path: Path) -> None:
    workspace_root = Path(__file__).resolve().parents[2]
    seeded = seed_final_output_project(tmp_path, rendered_scene_ids=["scene_001"])
    engine = DriverEngine(workspace_root=workspace_root, project_dir=seeded["project_dir"])

    run_state = engine.run(
        recipe_path=workspace_root / "configs" / "recipes" / "recipe-final-output.yaml",
        run_id="integration-final-output-partial",
        force=True,
    )

    assert run_state["stages"]["final_output"]["status"] == "done"
    assert run_state["stages"]["final_output_validation"]["status"] == "done"
    refs = [
        ArtifactRef.model_validate(item)
        for item in run_state["stages"]["final_output"]["artifact_refs"]
    ]
    validation_refs = [
        ArtifactRef.model_validate(item)
        for item in run_state["stages"]["final_output_validation"]["artifact_refs"]
    ]
    assert len(refs) == 1
    assert refs[0].artifact_type == "final_output"
    assert len(validation_refs) == 1
    assert validation_refs[0].artifact_type == "media_validation"
    assert validation_refs[0].entity_id == "project"

    artifact = FinalOutputArtifact.model_validate(engine.store.load_artifact(refs[0]).data)
    validation = MediaValidationArtifact.model_validate(
        engine.store.load_artifact(validation_refs[0]).data
    )
    assert artifact.coverage_state == "partial"
    assert artifact.included_scene_ids == ["scene_001"]
    assert artifact.omitted_scene_ids == ["scene_002"]
    assert artifact.video.duration_seconds == pytest.approx(4.0, rel=0.1)
    assert (seeded["project_dir"] / artifact.video.relative_path).exists()
    assert validation.target.scope_kind == "project"
    assert validation.target.coverage_state == "partial"
    assert validation.target_ref.key() == refs[0].key()


@pytest.mark.integration
def test_final_output_recipe_builds_complete_project_cut(tmp_path: Path) -> None:
    workspace_root = Path(__file__).resolve().parents[2]
    seeded = seed_final_output_project(tmp_path, rendered_scene_ids=["scene_001", "scene_002"])
    engine = DriverEngine(workspace_root=workspace_root, project_dir=seeded["project_dir"])

    run_state = engine.run(
        recipe_path=workspace_root / "configs" / "recipes" / "recipe-final-output.yaml",
        run_id="integration-final-output-complete",
        force=True,
    )

    assert run_state["stages"]["final_output"]["status"] == "done"
    assert run_state["stages"]["final_output_validation"]["status"] == "done"
    refs = [
        ArtifactRef.model_validate(item)
        for item in run_state["stages"]["final_output"]["artifact_refs"]
    ]
    validation_refs = [
        ArtifactRef.model_validate(item)
        for item in run_state["stages"]["final_output_validation"]["artifact_refs"]
    ]
    artifact = FinalOutputArtifact.model_validate(engine.store.load_artifact(refs[0]).data)
    validation = MediaValidationArtifact.model_validate(
        engine.store.load_artifact(validation_refs[0]).data
    )

    assert artifact.coverage_state == "complete"
    assert artifact.included_scene_ids == ["scene_001", "scene_002"]
    assert artifact.omitted_scene_ids == []
    assert artifact.video.duration_seconds is not None
    assert artifact.video.duration_seconds > seeded["clip_meta"]["duration_seconds"]
    assert (seeded["project_dir"] / artifact.video.relative_path).exists()
    assert validation.target.scope_kind == "project"
    assert validation.target.coverage_state == "complete"
    assert validation.target_ref.key() == refs[0].key()


@pytest.mark.integration
def test_final_output_recipe_allows_stale_but_compatible_timeline_refs(tmp_path: Path) -> None:
    workspace_root = Path(__file__).resolve().parents[2]
    seeded = seed_final_output_project(tmp_path, rendered_scene_ids=["scene_001"])
    engine = DriverEngine(workspace_root=workspace_root, project_dir=seeded["project_dir"])

    timeline_ref = engine.store.latest_ref("timeline", "project")
    track_manifest_ref = engine.store.latest_ref("track_manifest", "project")
    assert timeline_ref is not None
    assert track_manifest_ref is not None

    engine.store.graph.set_manual_health_override(
        timeline_ref,
        health=ArtifactHealth.STALE,
        trigger_ref=track_manifest_ref,
        source_artifact_ref=track_manifest_ref,
        rationale="Exercise final_output recipe against a stale-but-compatible timeline.",
        decided_by="tests.integration",
    )

    run_state = engine.run(
        recipe_path=workspace_root / "configs" / "recipes" / "recipe-final-output.yaml",
        run_id="integration-final-output-stale-compatible-timeline",
        force=True,
    )

    assert run_state["stages"]["final_output"]["status"] == "done"
    assert run_state["stages"]["final_output_validation"]["status"] == "done"
