from __future__ import annotations

from pathlib import Path

import pytest

from cine_forge.driver.engine import DriverEngine
from cine_forge.modules.timeline.track_system_v1.main import best_for_scene
from cine_forge.schemas import ArtifactRef, Storyboard, TrackManifest
from tests.storyboard_fixtures import seed_storyboard_project


@pytest.mark.integration
def test_storyboard_recipe_persists_artifacts_files_and_track_entries(tmp_path: Path) -> None:
    workspace_root = Path(__file__).resolve().parents[2]
    seeded = seed_storyboard_project(tmp_path, scene_count=2)
    engine = DriverEngine(workspace_root=workspace_root, project_dir=seeded["project_dir"])

    run_state = engine.run(
        recipe_path=workspace_root / "configs" / "recipes" / "recipe-storyboard-generation.yaml",
        run_id="integration-storyboards",
        force=True,
        runtime_params={"image_model": "mock", "storyboard_style": "clean_line"},
    )

    assert run_state["stages"]["storyboards"]["status"] == "done"

    refs = [
        ArtifactRef.model_validate(item)
        for item in run_state["stages"]["storyboards"]["artifact_refs"]
    ]
    storyboard_refs = [ref for ref in refs if ref.artifact_type == "storyboard"]
    assert len(storyboard_refs) == 2

    first_storyboard = Storyboard.model_validate(
        engine.store.load_artifact(storyboard_refs[0]).data
    )
    assert (seeded["project_dir"] / first_storyboard.frames[0].image.relative_path).exists()

    track_ref = next(ref for ref in refs if ref.artifact_type == "track_manifest")
    manifest = TrackManifest.model_validate(engine.store.load_artifact(track_ref).data)
    assert best_for_scene(manifest, scene_id="scene_001")["selected_track_type"] == "storyboards"
