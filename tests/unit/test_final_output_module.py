from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from cine_forge.modules.timeline.final_output_v1.main import run_module
from cine_forge.schemas import (
    ArtifactMetadata,
    FinalOutputArtifact,
    GeneratedVideoArtifact,
    MediaFile,
    TrackEntry,
    TrackManifest,
)
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
    probed_durations = iter([4.0, 4.0, 8.0])
    monkeypatch.setattr(
        "cine_forge.modules.timeline.final_output_v1.main._probe_duration_seconds",
        lambda _path: next(probed_durations),
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
def test_run_module_normalizes_when_copy_concat_output_is_too_short(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seeded = seed_final_output_project(tmp_path, rendered_scene_ids=["scene_001", "scene_002"])
    expected_duration = round(float(seeded["clip_meta"]["duration_seconds"]) * 2, 3)

    def _fake_concat_copy(_clip_paths, output_path):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"short-stream-copy-mp4")
        return None

    def _fake_concat_normalized(_clip_paths, output_path):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"normalized-mp4")
        return ["Normalized after stream-copy concat produced a short output."]

    clip_duration = float(seeded["clip_meta"]["duration_seconds"])
    probed_durations = iter([clip_duration, clip_duration, clip_duration, expected_duration])

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
        lambda _path: next(probed_durations),
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

    assert final_output.normalization_applied is True
    assert final_output.video.duration_seconds == pytest.approx(expected_duration)
    assert any("stream-copy concat produced" in note for note in final_output.normalization_notes)


@pytest.mark.unit
def test_run_module_assembles_ordered_render_clips_for_one_scene(tmp_path: Path) -> None:
    seeded = seed_final_output_project(tmp_path, rendered_scene_ids=["scene_001", "scene_002"])
    store = seeded["store"]
    project_dir = seeded["project_dir"]
    base_ref = seeded["generated_video_refs"]["scene_001"]
    base_artifact = store.load_artifact(base_ref)
    base_video = GeneratedVideoArtifact.model_validate(base_artifact.data)
    source_path = project_dir / base_video.video.relative_path

    clip_refs = []
    for index, (start, end) in enumerate(((0.0, 4.0), (4.0, 8.0)), start=1):
        clip_id = f"scene_001_clip_{index:03d}"
        media_dir = project_dir / "artifacts" / "generated_video_media" / clip_id / "v1"
        media_dir.mkdir(parents=True, exist_ok=True)
        output_path = media_dir / "scene_render.mp4"
        shutil.copyfile(source_path, output_path)
        clip_video = base_video.model_copy(
            update={
                "render_unit": "render_clip",
                "render_clip_id": clip_id,
                "render_clip_start_time_seconds": start,
                "render_clip_end_time_seconds": end,
                "video": MediaFile(
                    relative_path=str(output_path.relative_to(project_dir)),
                    media_type="video/mp4",
                    duration_seconds=4.0,
                ),
                "duration_seconds": 4.0,
            }
        )
        clip_ref = store.save_artifact(
            artifact_type="generated_video",
            entity_id=clip_id,
            data=clip_video.model_dump(mode="json"),
            metadata=ArtifactMetadata(
                lineage=[base_ref],
                intent="seed render clip",
                rationale="unit test multi-clip final output assembly",
                confidence=1.0,
                source="code",
            ),
        )
        clip_refs.append((clip_id, clip_ref, start, end))

    track_manifest_ref = store.latest_ref("track_manifest", "project")
    assert track_manifest_ref is not None
    manifest = TrackManifest.model_validate(store.load_artifact(track_manifest_ref).data)
    entries = list(manifest.entries)
    for clip_id, clip_ref, start, end in clip_refs:
        entries.append(
            TrackEntry(
                track_type="generated_video",
                scene_id="scene_001",
                render_clip_id=clip_id,
                artifact_ref=clip_ref,
                start_time_seconds=start,
                end_time_seconds=end,
                priority=100,
                status="available",
                notes="Seeded render clip fixture track.",
            )
        )
    updated_manifest = manifest.model_copy(update={"entries": entries})
    store.save_artifact(
        artifact_type="track_manifest",
        entity_id="project",
        data=updated_manifest.model_dump(mode="json"),
        metadata=ArtifactMetadata(
            lineage=[track_manifest_ref, *[ref for _, ref, _, _ in clip_refs]],
            intent="seed clip track manifest",
            rationale="unit test multi-clip final output assembly",
            confidence=1.0,
            source="code",
        ),
    )

    result = run_module(
        inputs=seeded["inputs"],
        params={},
        context={"project_dir": str(project_dir)},
    )

    artifact_payload = next(
        artifact["data"]
        for artifact in result["artifacts"]
        if artifact["artifact_type"] == "final_output"
    )
    final_output = FinalOutputArtifact.model_validate(artifact_payload)
    scene_001 = final_output.included_scenes[0]

    assert scene_001.scene_id == "scene_001"
    assert [clip.render_clip_id for clip in scene_001.clips] == [
        "scene_001_clip_001",
        "scene_001_clip_002",
    ]
    assert scene_001.duration_seconds == 8.0


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
