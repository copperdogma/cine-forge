from __future__ import annotations

from pathlib import Path

import pytest

from cine_forge.artifacts import ArtifactStore
from cine_forge.modules.visualization.animatic_v1.main import run_module as run_animatic_module
from cine_forge.modules.visualization.keyframe_v1.main import run_module as run_keyframe_module
from cine_forge.schemas import Animatic, ArtifactMetadata, KeyframeArtifact, PrevizReel
from tests.animatic_fixtures import seed_animatic_project
from tests.storyboard_fixtures import metadata


def _ffmpeg_missing() -> bool:
    import shutil

    return shutil.which("ffmpeg") is None


def _persist_outputs(store: ArtifactStore, artifacts: list[dict[str, object]]) -> None:
    for artifact in artifacts:
        artifact_type = str(artifact["artifact_type"])
        entity_id = str(artifact["entity_id"]) if artifact.get("entity_id") is not None else None
        raw_metadata = artifact.get("metadata") or {}
        metadata_obj = ArtifactMetadata.model_validate(raw_metadata or metadata("persist output"))
        store.save_artifact(
            artifact_type=artifact_type,
            entity_id=entity_id,
            data=artifact["data"],  # type: ignore[arg-type]
            metadata=metadata_obj,
        )


@pytest.mark.unit
def test_animatic_module_uses_placeholder_when_storyboards_missing(tmp_path: Path) -> None:
    if _ffmpeg_missing():
        pytest.skip("ffmpeg is required for animatic module tests")

    seeded = seed_animatic_project(
        tmp_path,
        scene_count=1,
        include_storyboards=False,
        include_audio=False,
    )
    result = run_animatic_module(
        inputs=seeded["inputs"],
        params={},
        context={"project_dir": str(seeded["project_dir"])},
    )

    animatic_payload = next(
        artifact["data"]
        for artifact in result["artifacts"]
        if artifact["artifact_type"] == "animatic"
    )
    animatic = Animatic.model_validate(animatic_payload)

    assert animatic.segments[0].source_kind == "placeholder"
    assert (seeded["project_dir"] / animatic.video.relative_path).exists()
    assert animatic.audio_refs == []


@pytest.mark.unit
def test_animatic_module_includes_project_audio_refs(tmp_path: Path) -> None:
    if _ffmpeg_missing():
        pytest.skip("ffmpeg is required for animatic module tests")

    seeded = seed_animatic_project(
        tmp_path,
        scene_count=1,
        include_storyboards=True,
        include_audio=True,
    )
    result = run_animatic_module(
        inputs=seeded["inputs"],
        params={},
        context={"project_dir": str(seeded["project_dir"])},
    )

    animatic_payload = next(
        artifact["data"]
        for artifact in result["artifacts"]
        if artifact["artifact_type"] == "animatic"
    )
    animatic = Animatic.model_validate(animatic_payload)

    assert any(item.source_kind == "project_injected" for item in animatic.audio_refs)
    assert (seeded["project_dir"] / animatic.video.relative_path).exists()


@pytest.mark.unit
def test_animatic_module_emits_previz_reel_with_scene_animatics(tmp_path: Path) -> None:
    if _ffmpeg_missing():
        pytest.skip("ffmpeg is required for animatic module tests")

    seeded = seed_animatic_project(
        tmp_path,
        scene_count=2,
        include_storyboards=False,
        include_audio=False,
    )
    result = run_animatic_module(
        inputs=seeded["inputs"],
        params={},
        context={"project_dir": str(seeded["project_dir"])},
    )

    previz_payload = next(
        artifact["data"]
        for artifact in result["artifacts"]
        if artifact["artifact_type"] == "previz_reel"
    )
    previz = PrevizReel.model_validate(previz_payload)

    assert len(previz.scenes) == 2
    assert all(item.source_track_type == "animatics" for item in previz.scenes)
    assert (seeded["project_dir"] / previz.reel_video.relative_path).exists()


@pytest.mark.unit
def test_keyframe_module_extracts_start_mid_end_frames(tmp_path: Path) -> None:
    if _ffmpeg_missing():
        pytest.skip("ffmpeg is required for animatic module tests")

    seeded = seed_animatic_project(
        tmp_path,
        scene_count=1,
        include_storyboards=True,
        include_audio=False,
    )
    store = ArtifactStore(project_dir=seeded["project_dir"])

    animatic_result = run_animatic_module(
        inputs=seeded["inputs"],
        params={},
        context={"project_dir": str(seeded["project_dir"])},
    )
    _persist_outputs(store, animatic_result["artifacts"])

    animatic_payloads = [
        artifact["data"]
        for artifact in animatic_result["artifacts"]
        if artifact["artifact_type"] == "animatic"
    ]
    track_manifest_payload = next(
        artifact["data"]
        for artifact in animatic_result["artifacts"]
        if artifact["artifact_type"] == "track_manifest"
    )
    keyframe_result = run_keyframe_module(
        inputs={
            "track_manifest": track_manifest_payload,
            "shot_plan": seeded["inputs"]["shot_plan"],
            "storyboard": seeded["inputs"]["storyboard"],
            "animatic": animatic_payloads,
        },
        params={},
        context={"project_dir": str(seeded["project_dir"])},
    )

    keyframe_payload = next(
        artifact["data"]
        for artifact in keyframe_result["artifacts"]
        if artifact["artifact_type"] == "keyframe"
    )
    keyframe_artifact = KeyframeArtifact.model_validate(keyframe_payload)

    assert len(keyframe_artifact.keyframes) == 6
    assert {item.position for item in keyframe_artifact.keyframes} == {"start", "mid", "end"}
    assert all(
        (seeded["project_dir"] / item.image.relative_path).exists()
        for item in keyframe_artifact.keyframes
    )


@pytest.mark.unit
def test_keyframe_lock_versions_remain_immutable(tmp_path: Path) -> None:
    seeded = seed_animatic_project(
        tmp_path,
        scene_count=1,
        include_storyboards=True,
        include_audio=False,
    )
    store = ArtifactStore(project_dir=seeded["project_dir"])

    base_payload = {
        "scene_id": "scene_001",
        "scene_number": 1,
        "scene_heading": "INT. LAB - NIGHT",
        "shot_plan_ref": store.list_versions("shot_plan", "scene_001")[-1].model_dump(mode="json"),
        "animatic_ref": None,
        "storyboard_ref": None,
        "keyframes": [
            {
                "keyframe_id": "scene_001_scene_001_a_start",
                "shot_id": "SCENE_001_A",
                "position": "start",
                "timestamp_seconds": 0.0,
                "image": {
                    "relative_path": "artifacts/keyframe_media/scene_001/v1/example.jpg",
                    "media_type": "image/jpeg",
                },
                "source_kind": "storyboard",
                "source_segment_id": None,
                "is_locked": False,
                "locked_by": None,
                "lock_reason": None,
                "shot_size": "Medium Single",
                "camera_angle": "Eye level",
                "camera_movement": "Slow push",
                "notes": "seed",
            }
        ],
    }

    v1_ref = store.save_artifact(
        artifact_type="keyframe",
        entity_id="scene_001",
        data=base_payload,
        metadata=metadata("seed keyframe"),
    )
    locked_payload = dict(base_payload)
    locked_payload["keyframes"] = [
        {
            **base_payload["keyframes"][0],
            "is_locked": True,
            "locked_by": "director",
            "lock_reason": "Approved visual beat.",
        }
    ]
    store.save_artifact(
        artifact_type="keyframe",
        entity_id="scene_001",
        data=locked_payload,
        metadata=metadata("lock keyframe").model_copy(update={"lineage": [v1_ref]}),
    )

    v1 = KeyframeArtifact.model_validate(store.load_artifact(v1_ref).data)
    latest_ref = store.list_versions("keyframe", "scene_001")[-1]
    v2 = KeyframeArtifact.model_validate(store.load_artifact(latest_ref).data)

    assert v1.keyframes[0].is_locked is False
    assert v2.keyframes[0].is_locked is True
    assert v2.keyframes[0].locked_by == "director"
