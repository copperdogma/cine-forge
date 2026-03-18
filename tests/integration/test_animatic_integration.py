from __future__ import annotations

from pathlib import Path

import pytest

from cine_forge.driver.engine import DriverEngine
from cine_forge.modules.timeline.track_system_v1.main import best_for_scene
from cine_forge.schemas import Animatic, ArtifactRef, KeyframeArtifact, PrevizReel, TrackManifest
from tests.animatic_fixtures import seed_animatic_project


@pytest.mark.integration
def test_animatics_recipe_persists_animatics_keyframes_and_previz(tmp_path: Path) -> None:
    import shutil

    if shutil.which("ffmpeg") is None:
        pytest.skip("ffmpeg is required for animatic integration tests")

    workspace_root = Path(__file__).resolve().parents[2]
    seeded = seed_animatic_project(
        tmp_path,
        scene_count=2,
        include_storyboards=True,
        include_audio=True,
    )
    engine = DriverEngine(workspace_root=workspace_root, project_dir=seeded["project_dir"])

    run_state = engine.run(
        recipe_path=workspace_root / "configs" / "recipes" / "recipe-animatics-generation.yaml",
        run_id="integration-animatics",
        force=True,
    )

    assert run_state["stages"]["animatics"]["status"] == "done"
    assert run_state["stages"]["keyframes"]["status"] == "done"

    animatic_refs = [
        ArtifactRef.model_validate(item)
        for item in run_state["stages"]["animatics"]["artifact_refs"]
        if item["artifact_type"] == "animatic"
    ]
    assert len(animatic_refs) == 2

    first_animatic = Animatic.model_validate(engine.store.load_artifact(animatic_refs[0]).data)
    assert (seeded["project_dir"] / first_animatic.video.relative_path).exists()
    assert len(first_animatic.segments) == 2
    assert first_animatic.audio_refs

    previz_ref = next(
        ArtifactRef.model_validate(item)
        for item in run_state["stages"]["animatics"]["artifact_refs"]
        if item["artifact_type"] == "previz_reel"
    )
    previz = PrevizReel.model_validate(engine.store.load_artifact(previz_ref).data)
    assert (seeded["project_dir"] / previz.reel_video.relative_path).exists()
    assert len(previz.scenes) == 2

    keyframe_refs = [
        ArtifactRef.model_validate(item)
        for item in run_state["stages"]["keyframes"]["artifact_refs"]
        if item["artifact_type"] == "keyframe"
    ]
    assert len(keyframe_refs) == 2
    first_keyframe = KeyframeArtifact.model_validate(
        engine.store.load_artifact(keyframe_refs[0]).data
    )
    assert len(first_keyframe.keyframes) == 6

    track_ref = next(
        ArtifactRef.model_validate(item)
        for item in run_state["stages"]["keyframes"]["artifact_refs"]
        if item["artifact_type"] == "track_manifest"
    )
    manifest = TrackManifest.model_validate(engine.store.load_artifact(track_ref).data)
    assert best_for_scene(manifest, scene_id="scene_001")["selected_track_type"] == "animatics"
