from __future__ import annotations

from pathlib import Path

import pytest

from cine_forge.api.artifact_manager import ArtifactManager
from cine_forge.artifacts import ArtifactStore
from cine_forge.schemas import (
    ArtifactHealth,
    ArtifactMetadata,
    MediaValidationArtifact,
)
from tests.render_fixtures import seed_generated_video_project


def _manager(project_path: Path) -> ArtifactManager:
    return ArtifactManager(
        project_path_resolver=lambda _project_id: project_path,
        role_context_factory=lambda _project_id: None,
        role_catalog=object(),
    )


def _seed_validation(
    store: ArtifactStore,
    *,
    generated_video_ref,
    prompt_ref,
    generated_video,
    recommended_health: ArtifactHealth,
) -> None:
    validation = MediaValidationArtifact(
        scene_id=generated_video.scene_id,
        scene_number=generated_video.scene_number,
        scene_heading=generated_video.scene_heading,
        target_ref=generated_video_ref,
        prompt_ref=prompt_ref,
        validated_media=generated_video.video,
        validator_id="media_validation_v1",
        validation_mode="deterministic_only",
        sampling_policy="2_evenly_spaced_jpegs_v1",
        config_digest="seeded",
        deterministic_probe={
            "file_exists": True,
            "ffprobe_available": True,
            "ffmpeg_available": True,
            "probe_succeeded": True,
            "decode_succeeded": True,
            "duration_seconds": generated_video.duration_seconds,
            "video_stream_present": True,
            "audio_stream_present": False,
            "sample_count_requested": 2,
            "sample_count_extracted": 2,
            "findings": [],
        },
        semantic_review={
            "status": "skipped",
            "mode": "none",
            "reason_skipped": "seeded",
        },
        recommended_health=recommended_health,
        summary="Seeded validation artifact for overlay tests.",
    )
    store.save_artifact(
        artifact_type="media_validation",
        entity_id=generated_video.scene_id,
        data=validation.model_dump(mode="json"),
        metadata=ArtifactMetadata(
            lineage=[generated_video_ref, prompt_ref],
            intent="seed media validation",
            rationale="seed overlay path",
            confidence=0.84,
            source="code",
            producing_module="tests.unit",
        ),
    )


@pytest.mark.unit
def test_artifact_manager_overlays_generated_video_health_from_validation(tmp_path: Path) -> None:
    seeded = seed_generated_video_project(tmp_path)
    project_path = seeded["project_dir"]
    store = ArtifactStore(project_dir=project_path)
    _seed_validation(
        store,
        generated_video_ref=seeded["generated_video_ref"],
        prompt_ref=seeded["prompt_ref"],
        generated_video=seeded["generated_video"],
        recommended_health=ArtifactHealth.NEEDS_REVIEW,
    )

    detail = _manager(project_path).read_artifact(
        "project-id",
        "generated_video",
        seeded["scene_id"],
        seeded["generated_video_ref"].version,
    )

    assert detail["health"] == ArtifactHealth.NEEDS_REVIEW.value
    assert detail["health_details"]["source_kind"] == "media_validation"
    assert detail["health_details"]["source_artifact_ref"]["artifact_type"] == "media_validation"


@pytest.mark.unit
def test_artifact_manager_keeps_structural_stale_over_validation_overlay(tmp_path: Path) -> None:
    seeded = seed_generated_video_project(tmp_path)
    project_path = seeded["project_dir"]
    store = ArtifactStore(project_dir=project_path)
    _seed_validation(
        store,
        generated_video_ref=seeded["generated_video_ref"],
        prompt_ref=seeded["prompt_ref"],
        generated_video=seeded["generated_video"],
        recommended_health=ArtifactHealth.NEEDS_REVISION,
    )
    store.save_artifact(
        artifact_type="render_prompt",
        entity_id=seeded["scene_id"],
        data=store.load_artifact(seeded["prompt_ref"]).data,
        metadata=ArtifactMetadata(
            lineage=[],
            intent="seed render prompt v2",
            rationale="force stale on generated video v1",
            confidence=1.0,
            source="code",
            producing_module="tests.unit",
        ),
    )

    detail = _manager(project_path).read_artifact(
        "project-id",
        "generated_video",
        seeded["scene_id"],
        seeded["generated_video_ref"].version,
    )

    assert detail["health"] == ArtifactHealth.STALE.value
    assert detail["health_details"]["source_kind"] == "structural_invalidation"


@pytest.mark.unit
def test_artifact_manager_uses_validation_verdict_for_media_validation_artifact_health(
    tmp_path: Path,
) -> None:
    seeded = seed_generated_video_project(tmp_path)
    project_path = seeded["project_dir"]
    store = ArtifactStore(project_dir=project_path)
    _seed_validation(
        store,
        generated_video_ref=seeded["generated_video_ref"],
        prompt_ref=seeded["prompt_ref"],
        generated_video=seeded["generated_video"],
        recommended_health=ArtifactHealth.NEEDS_REVIEW,
    )
    validation_ref = store.list_versions("media_validation", seeded["scene_id"])[-1]
    manager = _manager(project_path)

    detail = manager.read_artifact(
        "project-id",
        "media_validation",
        seeded["scene_id"],
        validation_ref.version,
    )
    versions = manager.list_artifact_versions(
        "project-id",
        "media_validation",
        seeded["scene_id"],
    )

    assert detail["health"] == ArtifactHealth.NEEDS_REVIEW.value
    assert detail["health_details"]["source_kind"] == "media_validation"
    assert detail["health_details"]["trigger_ref"]["artifact_type"] == "generated_video"
    assert versions[-1]["health"] == ArtifactHealth.NEEDS_REVIEW.value
