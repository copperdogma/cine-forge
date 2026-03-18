from __future__ import annotations

from pathlib import Path

import pytest

from cine_forge.modules.timeline.track_system_v1.main import best_for_scene
from cine_forge.modules.visualization.storyboard_v1.main import run_module
from cine_forge.schemas import Storyboard, TrackManifest
from tests.storyboard_fixtures import seed_storyboard_project


@pytest.mark.unit
def test_run_module_mock_generates_storyboards_and_track_entries(tmp_path: Path) -> None:
    seeded = seed_storyboard_project(tmp_path, scene_count=2)

    result = run_module(
        inputs=seeded["inputs"],
        params={"image_model": "mock", "style": "clean_line"},
        context={
            "project_dir": str(seeded["project_dir"]),
            "run_id": "storyboard-unit",
            "stage_id": "storyboards",
        },
    )

    storyboard_artifacts = [
        artifact for artifact in result["artifacts"] if artifact["artifact_type"] == "storyboard"
    ]
    assert len(storyboard_artifacts) == 2
    assert result["cost"]["estimated_cost_usd"] == 0.0

    first_storyboard = Storyboard.model_validate(storyboard_artifacts[0]["data"])
    assert first_storyboard.style == "clean_line"
    assert len(first_storyboard.frames) == 2
    assert "Scene heading: INT. LAB - NIGHT" in first_storyboard.frames[0].prompt_used
    assert "Single storyboard frame only" in first_storyboard.frames[0].prompt_used
    assert first_storyboard.frames[0].visual_reference_images

    for frame in first_storyboard.frames:
        assert (seeded["project_dir"] / frame.image.relative_path).exists()

    manifest_artifact = next(
        artifact
        for artifact in result["artifacts"]
        if artifact["artifact_type"] == "track_manifest"
    )
    manifest = TrackManifest.model_validate(manifest_artifact["data"])
    storyboard_entries = [entry for entry in manifest.entries if entry.track_type == "storyboards"]
    assert len(storyboard_entries) == 4
    assert best_for_scene(manifest, scene_id="scene_001")["selected_track_type"] == "storyboards"
    assert (
        best_for_scene(
            manifest,
            scene_id="scene_001",
            shot_id=first_storyboard.frames[0].primary_shot_id,
        )["selected_track_type"]
        == "storyboards"
    )


@pytest.mark.unit
def test_run_module_uses_project_config_storyboard_style_when_param_missing(
    tmp_path: Path,
) -> None:
    seeded = seed_storyboard_project(
        tmp_path,
        scene_count=1,
        storyboard_style="animation_style",
    )

    result = run_module(
        inputs=seeded["inputs"],
        params={"image_model": "mock"},
        context={"project_dir": str(seeded["project_dir"]), "run_id": "style-fallback"},
    )

    storyboard_artifact = next(
        artifact for artifact in result["artifacts"] if artifact["artifact_type"] == "storyboard"
    )
    storyboard = Storyboard.model_validate(storyboard_artifact["data"])
    assert storyboard.style == "animation_style"


@pytest.mark.unit
def test_run_module_rejects_photoreal_without_opt_in(tmp_path: Path) -> None:
    seeded = seed_storyboard_project(tmp_path, scene_count=1)

    with pytest.raises(ValueError, match="photoreal style requires"):
        run_module(
            inputs=seeded["inputs"],
            params={"image_model": "mock", "style": "photoreal"},
            context={"project_dir": str(seeded["project_dir"]), "run_id": "photoreal-block"},
        )


@pytest.mark.unit
def test_prompt_sources_capture_all_context_layers(tmp_path: Path) -> None:
    seeded = seed_storyboard_project(tmp_path, scene_count=1)

    result = run_module(
        inputs=seeded["inputs"],
        params={"image_model": "mock", "style": "sketch"},
        context={"project_dir": str(seeded["project_dir"]), "run_id": "prompt-sources"},
    )

    storyboard_artifact = next(
        artifact for artifact in result["artifacts"] if artifact["artifact_type"] == "storyboard"
    )
    storyboard = Storyboard.model_validate(storyboard_artifact["data"])
    prompt_sources = set(storyboard.frames[0].prompt_sources_used)

    assert {
        "shot_plan",
        "look_and_feel",
        "project_config",
        "intent_mood",
        "character_bible",
        "location_bible",
        "continuity_state",
        "bible_manifest",
    }.issubset(prompt_sources)
