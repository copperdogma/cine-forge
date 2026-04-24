from __future__ import annotations

import io
from pathlib import Path

import pytest
from PIL import Image

from cine_forge.ai.image import REFERENCE_IMAGE_FALLBACK_MODEL
from cine_forge.modules.timeline.track_system_v1.main import best_for_scene
from cine_forge.modules.visualization.storyboard_v1 import generation as storyboard_generation
from cine_forge.modules.visualization.storyboard_v1.main import run_module
from cine_forge.modules.visualization.storyboard_v1.prompting import _sanitize_visual_text
from cine_forge.schemas import Storyboard, TrackManifest
from tests.storyboard_fixtures import seed_storyboard_project


def _jpeg_bytes(size: str = "1536x1024") -> bytes:
    width, height = (int(part) for part in size.split("x", maxsplit=1))
    image = Image.new("RGB", (width, height), (240, 240, 240))
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=90)
    return buffer.getvalue()


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
    lock_by_name = {lock.name: lock for lock in first_storyboard.character_identity_locks}
    assert set(lock_by_name) == {"MARA", "OWEN"}
    assert lock_by_name["MARA"].wardrobe_summary == "navy rain jacket"
    assert lock_by_name["MARA"].source == "heuristic"
    assert len(first_storyboard.frames) == 2
    first_prompt = first_storyboard.frames[0].prompt_used
    insert_prompt = first_storyboard.frames[1].prompt_used
    assert "Scene setting: int LAB night." in first_prompt
    assert "Scene style lock:" in first_prompt
    assert "Character identity locks:" in first_prompt
    assert "navy rain jacket" in first_prompt
    assert "Do not render live-action photography" in first_prompt
    assert "same face structure" in first_prompt
    assert "Do not render dialogue, captions, speech bubbles" in first_prompt
    assert "We can still stop this." not in first_prompt
    assert "This is not a prop-only cutaway." in first_prompt
    assert "Single storyboard frame only." in first_prompt
    assert "Prop/detail insert only" in insert_prompt
    assert "This is not a prop-only cutaway." not in insert_prompt
    assert first_storyboard.frames[0].visual_reference_images
    assert "reference_images" in first_storyboard.frames[0].prompt_sources_used
    assert first_storyboard.frames[0].direct_reference_images == []

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
        "reference_images",
    }.issubset(prompt_sources)
    assert "bible_manifest" not in prompt_sources


@pytest.mark.unit
def test_run_module_falls_back_to_reference_capable_image_model_for_conditioned_storyboards(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seeded = seed_storyboard_project(tmp_path, scene_count=1)
    calls: list[dict[str, object]] = []

    def fake_generate_image(
        prompt: str,
        entity_type: str = "character",
        model: str = "gpt-image-1",
        aspect_ratio: str | None = None,
        quality: str = "auto",
        reference_image_paths: list[str] | None = None,
        size: str | None = None,
    ) -> tuple[bytes, str]:
        calls.append(
            {
                "prompt": prompt,
                "entity_type": entity_type,
                "model": model,
                "aspect_ratio": aspect_ratio,
                "quality": quality,
                "reference_image_paths": list(reference_image_paths or []),
                "size": size,
            }
        )
        return b"storyboard-bytes", model

    monkeypatch.setattr(storyboard_generation, "generate_image", fake_generate_image)

    result = run_module(
        inputs=seeded["inputs"],
        params={
            "image_model": "imagen-4.0-generate-001",
            "identity_model": "mock",
            "style": "clean_line",
            "grid_mode": "off",
        },
        context={
            "project_dir": str(seeded["project_dir"]),
            "run_id": "storyboard-reference-fallback",
            "stage_id": "storyboards",
        },
    )

    storyboard_artifact = next(
        artifact for artifact in result["artifacts"] if artifact["artifact_type"] == "storyboard"
    )
    storyboard = Storyboard.model_validate(storyboard_artifact["data"])

    assert calls
    first_call = calls[0]
    assert first_call["model"] == REFERENCE_IMAGE_FALLBACK_MODEL
    reference_paths = list(first_call["reference_image_paths"])
    assert reference_paths
    assert all(Path(path).is_absolute() for path in reference_paths)
    assert all(Path(path).exists() for path in reference_paths)
    assert (
        storyboard.frames[0].direct_reference_images == storyboard.frames[0].visual_reference_images
    )
    assert storyboard.frames[0].cost.model == REFERENCE_IMAGE_FALLBACK_MODEL


@pytest.mark.unit
def test_run_module_defaults_storyboards_to_openai_template_grid_lane(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seeded = seed_storyboard_project(tmp_path, scene_count=1)
    calls: list[dict[str, object]] = []

    def fake_generate_image(
        prompt: str,
        entity_type: str = "character",
        model: str = "gpt-image-1",
        aspect_ratio: str | None = None,
        quality: str = "auto",
        reference_image_paths: list[str] | None = None,
        size: str | None = None,
    ) -> tuple[bytes, str]:
        calls.append(
            {
                "prompt": prompt,
                "entity_type": entity_type,
                "model": model,
                "aspect_ratio": aspect_ratio,
                "quality": quality,
                "reference_image_paths": list(reference_image_paths or []),
                "size": size,
            }
        )
        return _jpeg_bytes(str(size or "1536x1024")), model

    monkeypatch.setattr(storyboard_generation, "generate_image", fake_generate_image)

    result = run_module(
        inputs=seeded["inputs"],
        params={"identity_model": "mock", "style": "clean_line"},
        context={
            "project_dir": str(seeded["project_dir"]),
            "run_id": "storyboard-default-openai",
            "stage_id": "storyboards",
        },
    )

    storyboard_artifact = next(
        artifact for artifact in result["artifacts"] if artifact["artifact_type"] == "storyboard"
    )
    storyboard = Storyboard.model_validate(storyboard_artifact["data"])

    assert calls
    assert calls[0]["model"] == "gpt-image-2"
    assert "Panel 1" in str(calls[0]["prompt"])
    assert calls[0]["reference_image_paths"]
    assert Path(str(calls[0]["reference_image_paths"][0])).name == "grid_01_template.jpg"
    assert calls[0]["size"] == "1536x1024"
    assert storyboard.frames[0].cost.model == "gpt-image-2"
    assert storyboard_artifact["metadata"]["annotations"]["grid_mode"] == "template"


@pytest.mark.unit
def test_run_module_can_disable_default_storyboard_grid(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seeded = seed_storyboard_project(tmp_path, scene_count=1)
    calls: list[dict[str, object]] = []

    def fake_generate_image(
        prompt: str,
        entity_type: str = "character",
        model: str = "gpt-image-1",
        aspect_ratio: str | None = None,
        quality: str = "auto",
        reference_image_paths: list[str] | None = None,
        size: str | None = None,
    ) -> tuple[bytes, str]:
        calls.append(
            {
                "prompt": prompt,
                "model": model,
                "reference_image_paths": list(reference_image_paths or []),
                "size": size,
            }
        )
        return b"storyboard-bytes", model

    monkeypatch.setattr(storyboard_generation, "generate_image", fake_generate_image)

    result = run_module(
        inputs=seeded["inputs"],
        params={"identity_model": "mock", "style": "clean_line"},
        context={
            "project_dir": str(seeded["project_dir"]),
            "run_id": "storyboard-default-grid-disabled",
            "stage_id": "storyboards",
            "runtime_params": {"storyboard_grid_mode": "off"},
        },
    )

    storyboard_artifact = next(
        artifact for artifact in result["artifacts"] if artifact["artifact_type"] == "storyboard"
    )
    storyboard = Storyboard.model_validate(storyboard_artifact["data"])

    assert len(calls) == 2
    assert "Single storyboard frame only." in str(calls[0]["prompt"])
    assert "Panel 1" not in str(calls[0]["prompt"])
    assert storyboard.frames[0].cost.model == "gpt-image-2"
    assert storyboard_artifact["metadata"]["annotations"]["grid_mode"] == "off"


@pytest.mark.unit
def test_run_module_passes_openai_storyboard_image_size_override(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seeded = seed_storyboard_project(tmp_path, scene_count=1)
    calls: list[dict[str, object]] = []

    def fake_generate_image(
        prompt: str,
        entity_type: str = "character",
        model: str = "gpt-image-1",
        aspect_ratio: str | None = None,
        quality: str = "auto",
        reference_image_paths: list[str] | None = None,
        size: str | None = None,
    ) -> tuple[bytes, str]:
        calls.append(
            {
                "model": model,
                "size": size,
                "reference_image_paths": list(reference_image_paths or []),
            }
        )
        return b"storyboard-bytes", model

    monkeypatch.setattr(storyboard_generation, "generate_image", fake_generate_image)

    result = run_module(
        inputs=seeded["inputs"],
        params={"identity_model": "mock", "style": "clean_line"},
        context={
            "project_dir": str(seeded["project_dir"]),
            "run_id": "storyboard-openai-size",
            "stage_id": "storyboards",
            "runtime_params": {"image_size": "1024x1024", "storyboard_grid_mode": "off"},
        },
    )

    storyboard_artifact = next(
        artifact for artifact in result["artifacts"] if artifact["artifact_type"] == "storyboard"
    )
    storyboard = Storyboard.model_validate(storyboard_artifact["data"])

    assert calls
    assert calls[0]["size"] == "1024x1024"
    assert storyboard.frames[0].cost.estimated_cost_usd == pytest.approx(0.00816)
    assert storyboard_artifact["metadata"]["annotations"]["image_size"] == "1024x1024"


@pytest.mark.unit
def test_run_module_template_grid_generates_one_image_and_slices_frames(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seeded = seed_storyboard_project(tmp_path, scene_count=1)
    calls: list[dict[str, object]] = []

    def fake_generate_image(
        prompt: str,
        entity_type: str = "character",
        model: str = "gpt-image-1",
        aspect_ratio: str | None = None,
        quality: str = "auto",
        reference_image_paths: list[str] | None = None,
        size: str | None = None,
    ) -> tuple[bytes, str]:
        calls.append(
            {
                "prompt": prompt,
                "model": model,
                "reference_image_paths": list(reference_image_paths or []),
                "size": size,
            }
        )
        return _jpeg_bytes(str(size or "1536x1024")), model

    monkeypatch.setattr(storyboard_generation, "generate_image", fake_generate_image)

    result = run_module(
        inputs=seeded["inputs"],
        params={"identity_model": "mock", "style": "clean_line", "grid_mode": "template"},
        context={
            "project_dir": str(seeded["project_dir"]),
            "run_id": "storyboard-grid-template",
            "stage_id": "storyboards",
        },
    )

    storyboard_artifact = next(
        artifact for artifact in result["artifacts"] if artifact["artifact_type"] == "storyboard"
    )
    storyboard = Storyboard.model_validate(storyboard_artifact["data"])

    assert len(calls) == 1
    assert "Panel 1" in str(calls[0]["prompt"])
    reference_paths = list(calls[0]["reference_image_paths"])
    assert reference_paths
    assert Path(str(reference_paths[0])).name == "grid_01_template.jpg"
    assert calls[0]["size"] == "1536x1024"
    assert len(storyboard.frames) == 2
    assert all(
        (seeded["project_dir"] / frame.image.relative_path).exists()
        for frame in storyboard.frames
    )
    assert storyboard.frames[0].prompt_sources_used[-2:] == [
        "storyboard_grid",
        "grid_template",
    ]
    assert storyboard_artifact["metadata"]["annotations"]["grid_mode"] == "template"


@pytest.mark.unit
def test_run_module_beat_template_grid_adds_ordered_story_beats(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seeded = seed_storyboard_project(tmp_path, scene_count=1)
    calls: list[dict[str, object]] = []

    def fake_generate_image(
        prompt: str,
        entity_type: str = "character",
        model: str = "gpt-image-1",
        aspect_ratio: str | None = None,
        quality: str = "auto",
        reference_image_paths: list[str] | None = None,
        size: str | None = None,
    ) -> tuple[bytes, str]:
        calls.append(
            {
                "prompt": prompt,
                "model": model,
                "reference_image_paths": list(reference_image_paths or []),
                "size": size,
            }
        )
        return _jpeg_bytes(str(size or "1536x1024")), model

    monkeypatch.setattr(storyboard_generation, "generate_image", fake_generate_image)

    result = run_module(
        inputs=seeded["inputs"],
        params={
            "identity_model": "mock",
            "style": "clean_line",
            "grid_mode": "beat_template",
            "grid_max_panels": 9,
        },
        context={
            "project_dir": str(seeded["project_dir"]),
            "run_id": "storyboard-grid-beats",
            "stage_id": "storyboards",
        },
    )

    storyboard_artifact = next(
        artifact for artifact in result["artifacts"] if artifact["artifact_type"] == "storyboard"
    )
    storyboard = Storyboard.model_validate(storyboard_artifact["data"])
    prompt = str(calls[0]["prompt"])

    assert len(calls) == 1
    assert "Ordered scene beat router:" in prompt
    assert "Beat 1 of 2 / shot SCENE_001_A" in prompt
    assert "opening beat that establishes the scene pressure and geography" in prompt
    assert "Story function: Establish emotional pressure." in prompt
    assert "Recurring identity lock: MARA:" in prompt
    assert "Panel 1 / shot SCENE_001_A:" in prompt
    reference_paths = list(calls[0]["reference_image_paths"])
    assert reference_paths
    assert Path(str(reference_paths[0])).name == "grid_01_template.jpg"
    assert storyboard.frames[0].prompt_sources_used[-3:] == [
        "storyboard_grid",
        "storyboard_grid_beats",
        "grid_template",
    ]
    assert storyboard_artifact["metadata"]["annotations"]["grid_mode"] == "beat_template"
    assert storyboard_artifact["metadata"]["annotations"]["grid_max_panels"] == 9


@pytest.mark.unit
def test_sanitize_visual_text_preserves_apostrophes_and_strips_dialogue() -> None:
    sanitized = _sanitize_visual_text(
        """Brick's entrance as he mutters "Back off." and OWEN: 'Let it run.'"""
    )

    assert sanitized == "Brick's entrance as he mutters the spoken line and the spoken line"


@pytest.mark.unit
def test_sanitize_visual_text_removes_exact_text_display_cues() -> None:
    sanitized = _sanitize_visual_text(
        "MARA studies the ON AIR sign beside the KTRM-FM whiteboard notes."
    )

    assert "ON AIR" not in sanitized
    assert "KTRM" not in sanitized
    assert "whiteboard notes" not in sanitized
    assert "unlettered" in sanitized
    assert "illegible" in sanitized
