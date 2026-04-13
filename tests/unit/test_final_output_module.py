from __future__ import annotations

from pathlib import Path

import pytest

from cine_forge.modules.timeline.final_output_v1.main import run_module
from cine_forge.schemas import FinalOutputArtifact
from tests.render_fixtures import seed_final_output_project


@pytest.mark.unit
def test_run_module_builds_partial_final_output_from_available_scene_renders(
    tmp_path: Path,
) -> None:
    seeded = seed_final_output_project(tmp_path, rendered_scene_ids=["scene_001"])

    result = run_module(
        inputs=seeded["inputs"],
        params={},
        context={"project_dir": str(seeded["project_dir"])},
    )

    artifact_payload = next(
        artifact["data"]
        for artifact in result["artifacts"]
        if artifact["artifact_type"] == "final_output"
    )
    final_output = FinalOutputArtifact.model_validate(artifact_payload)

    assert final_output.coverage_state == "partial"
    assert final_output.included_scene_ids == ["scene_001"]
    assert final_output.omitted_scene_ids == ["scene_002"]
    assert final_output.omitted_scenes[0].reason == "missing_generated_video_track"
    assert final_output.normalization_applied is False
    assert (seeded["project_dir"] / final_output.video.relative_path).exists()


@pytest.mark.unit
def test_run_module_uses_normalization_fallback_when_concat_copy_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seeded = seed_final_output_project(tmp_path, rendered_scene_ids=["scene_001", "scene_002"])

    def _fake_concat_copy(_clip_paths, _output_path):
        return "copy concat failed for fixture"

    def _fake_concat_normalized(_clip_paths, output_path):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"normalized-mp4")
        return ["Source clips had inconsistent audio streams, so the assembled output omits audio."]

    monkeypatch.setattr(
        "cine_forge.modules.timeline.final_output_v1.main._concat_copy",
        _fake_concat_copy,
    )
    monkeypatch.setattr(
        "cine_forge.modules.timeline.final_output_v1.main._concat_normalized",
        _fake_concat_normalized,
    )
    monkeypatch.setattr(
        "cine_forge.modules.timeline.final_output_v1.main._probe_duration_seconds",
        lambda _path: 8.0,
    )

    result = run_module(
        inputs=seeded["inputs"],
        params={},
        context={"project_dir": str(seeded["project_dir"])},
    )

    artifact_payload = next(
        artifact["data"]
        for artifact in result["artifacts"]
        if artifact["artifact_type"] == "final_output"
    )
    final_output = FinalOutputArtifact.model_validate(artifact_payload)

    assert final_output.coverage_state == "complete"
    assert final_output.normalization_applied is True
    assert any(
        "Direct stream-copy concat failed" in note for note in final_output.normalization_notes
    )
    assert any("omits audio" in note for note in final_output.normalization_notes)


@pytest.mark.unit
def test_run_module_rejects_projects_without_any_rendered_scene_media(tmp_path: Path) -> None:
    seeded = seed_final_output_project(tmp_path, rendered_scene_ids=[])

    with pytest.raises(
        ValueError,
        match="requires at least one scene with generated video media",
    ):
        run_module(
            inputs=seeded["inputs"],
            params={},
            context={"project_dir": str(seeded["project_dir"])},
        )
