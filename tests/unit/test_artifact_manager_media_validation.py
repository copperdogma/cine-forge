from __future__ import annotations

from pathlib import Path

import pytest

from cine_forge.api.artifact_manager import ArtifactManager
from cine_forge.artifacts import ArtifactStore
from cine_forge.schemas import (
    ArtifactHealth,
    ArtifactMetadata,
    ArtifactRef,
    FinalOutputArtifact,
    MediaValidationArtifact,
    MediaValidationTarget,
)
from tests.render_fixtures import seed_final_output_project, seed_generated_video_project


def _manager(project_path: Path) -> ArtifactManager:
    return ArtifactManager(
        project_path_resolver=lambda _project_id: project_path,
        role_context_factory=lambda _project_id: None,
        role_catalog=object(),
    )


def _seed_validation(
    store: ArtifactStore,
    *,
    target,
    target_ref,
    prompt_ref,
    validated_media,
    entity_id: str,
    declared_duration_seconds: float,
    recommended_health: ArtifactHealth,
) -> None:
    validation = MediaValidationArtifact(
        target=target,
        target_ref=target_ref,
        prompt_ref=prompt_ref,
        validated_media=validated_media,
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
            "duration_seconds": declared_duration_seconds,
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
        entity_id=entity_id,
        data=validation.model_dump(mode="json"),
        metadata=ArtifactMetadata(
            lineage=[target_ref, *([prompt_ref] if prompt_ref else [])],
            intent="seed media validation",
            rationale="seed overlay path",
            confidence=0.84,
            source="code",
            producing_module="tests.unit",
        ),
    )


def _scene_target(seeded: dict) -> MediaValidationTarget:
    generated_video = seeded["generated_video"]
    return MediaValidationTarget(
        scope_kind="scene",
        entity_id=seeded["scene_id"],
        label=(
            f"Scene {generated_video.scene_number}: "
            f"{generated_video.scene_heading}"
        ),
        scene_id=seeded["scene_id"],
        scene_number=generated_video.scene_number,
        scene_heading=generated_video.scene_heading,
    )


@pytest.mark.unit
def test_artifact_manager_overlays_generated_video_health_from_validation(tmp_path: Path) -> None:
    seeded = seed_generated_video_project(tmp_path)
    project_path = seeded["project_dir"]
    store = ArtifactStore(project_dir=project_path)
    _seed_validation(
        store,
        target=_scene_target(seeded),
        target_ref=seeded["generated_video_ref"],
        prompt_ref=seeded["prompt_ref"],
        validated_media=seeded["generated_video"].video,
        entity_id=seeded["scene_id"],
        declared_duration_seconds=seeded["generated_video"].duration_seconds,
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
def test_artifact_manager_overlays_ai_previz_video_health_from_validation(tmp_path: Path) -> None:
    seeded = seed_generated_video_project(tmp_path)
    project_path = seeded["project_dir"]
    store = ArtifactStore(project_dir=project_path)
    ai_previz_ref = store.save_artifact(
        artifact_type="ai_previz_video",
        entity_id=seeded["scene_id"],
        data=seeded["generated_video"].model_dump(mode="json"),
        metadata=ArtifactMetadata(
            lineage=[seeded["generated_video_ref"], seeded["prompt_ref"]],
            intent="seed ai previz video",
            rationale="seed overlay path",
            confidence=1.0,
            source="code",
            producing_module="tests.unit",
        ),
    )
    _seed_validation(
        store,
        target=_scene_target(seeded),
        target_ref=ai_previz_ref,
        prompt_ref=seeded["prompt_ref"],
        validated_media=seeded["generated_video"].video,
        entity_id=seeded["scene_id"],
        declared_duration_seconds=seeded["generated_video"].duration_seconds,
        recommended_health=ArtifactHealth.NEEDS_REVIEW,
    )

    detail = _manager(project_path).read_artifact(
        "project-id",
        "ai_previz_video",
        seeded["scene_id"],
        ai_previz_ref.version,
    )

    assert detail["health"] == ArtifactHealth.NEEDS_REVIEW.value
    assert detail["health_details"]["source_kind"] == "media_validation"
    assert detail["health_details"]["source_artifact_ref"]["artifact_type"] == "media_validation"


@pytest.mark.unit
def test_artifact_manager_marks_ai_previz_missing_validation_as_pending(
    tmp_path: Path,
) -> None:
    seeded = seed_generated_video_project(tmp_path)
    project_path = seeded["project_dir"]
    store = ArtifactStore(project_dir=project_path)
    ai_previz_ref = store.save_artifact(
        artifact_type="ai_previz_video",
        entity_id=seeded["scene_id"],
        data=seeded["generated_video"].model_dump(mode="json"),
        metadata=ArtifactMetadata(
            lineage=[seeded["generated_video_ref"], seeded["prompt_ref"]],
            intent="seed ai previz video",
            rationale="seed pending overlay path",
            confidence=1.0,
            source="code",
            producing_module="tests.unit",
        ),
    )

    detail = _manager(project_path).read_artifact(
        "project-id",
        "ai_previz_video",
        seeded["scene_id"],
        ai_previz_ref.version,
    )

    assert detail["health"] == ArtifactHealth.NEEDS_REVIEW.value
    assert detail["health_details"]["source_kind"] == "media_validation_missing"
    assert "playable" in detail["health_details"]["reason"]


@pytest.mark.unit
def test_artifact_manager_marks_ai_previz_with_older_validation_as_pending_latest(
    tmp_path: Path,
) -> None:
    seeded = seed_generated_video_project(tmp_path)
    project_path = seeded["project_dir"]
    store = ArtifactStore(project_dir=project_path)
    first_ref = store.save_artifact(
        artifact_type="ai_previz_video",
        entity_id=seeded["scene_id"],
        data=seeded["generated_video"].model_dump(mode="json"),
        metadata=ArtifactMetadata(
            lineage=[seeded["generated_video_ref"], seeded["prompt_ref"]],
            intent="seed ai previz video v1",
            rationale="seed stale overlay path",
            confidence=1.0,
            source="code",
            producing_module="tests.unit",
        ),
    )
    _seed_validation(
        store,
        target=_scene_target(seeded),
        target_ref=first_ref,
        prompt_ref=seeded["prompt_ref"],
        validated_media=seeded["generated_video"].video,
        entity_id=seeded["scene_id"],
        declared_duration_seconds=seeded["generated_video"].duration_seconds,
        recommended_health=ArtifactHealth.VALID,
    )
    second_ref = store.save_artifact(
        artifact_type="ai_previz_video",
        entity_id=seeded["scene_id"],
        data=seeded["generated_video"].model_dump(mode="json"),
        metadata=ArtifactMetadata(
            lineage=[first_ref, seeded["prompt_ref"]],
            intent="seed ai previz video v2",
            rationale="seed stale overlay path",
            confidence=1.0,
            source="code",
            producing_module="tests.unit",
        ),
    )

    detail = _manager(project_path).read_artifact(
        "project-id",
        "ai_previz_video",
        seeded["scene_id"],
        second_ref.version,
    )

    assert detail["health"] == ArtifactHealth.NEEDS_REVIEW.value
    assert detail["health_details"]["source_kind"] == "media_validation_stale"
    assert detail["health_details"]["source_artifact_ref"]["artifact_type"] == "media_validation"
    assert "older clip" in detail["health_details"]["reason"]


@pytest.mark.unit
def test_artifact_manager_keeps_structural_stale_over_validation_overlay(tmp_path: Path) -> None:
    seeded = seed_generated_video_project(tmp_path)
    project_path = seeded["project_dir"]
    store = ArtifactStore(project_dir=project_path)
    _seed_validation(
        store,
        target=_scene_target(seeded),
        target_ref=seeded["generated_video_ref"],
        prompt_ref=seeded["prompt_ref"],
        validated_media=seeded["generated_video"].video,
        entity_id=seeded["scene_id"],
        declared_duration_seconds=seeded["generated_video"].duration_seconds,
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
        target=_scene_target(seeded),
        target_ref=seeded["generated_video_ref"],
        prompt_ref=seeded["prompt_ref"],
        validated_media=seeded["generated_video"].video,
        entity_id=seeded["scene_id"],
        declared_duration_seconds=seeded["generated_video"].duration_seconds,
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


@pytest.mark.unit
def test_artifact_manager_marks_final_output_missing_validation_as_unvalidated(
    tmp_path: Path,
) -> None:
    workspace_root = Path(__file__).resolve().parents[2]
    seeded = seed_final_output_project(tmp_path, rendered_scene_ids=["scene_001"])
    project_path = seeded["project_dir"]
    from cine_forge.driver.engine import DriverEngine

    engine = DriverEngine(workspace_root=workspace_root, project_dir=project_path)
    run_state = engine.run(
        recipe_path=workspace_root / "configs" / "recipes" / "recipe-final-output.yaml",
        run_id="artifact-manager-final-output-missing-validation",
        end_at="final_output",
        force=True,
    )
    final_output_ref = ArtifactRef.model_validate(
        run_state["stages"]["final_output"]["artifact_refs"][0]
    )

    detail = _manager(project_path).read_artifact(
        "project-id",
        "final_output",
        "project",
        final_output_ref.version,
    )

    assert detail["health"] == ArtifactHealth.NEEDS_REVIEW.value
    assert detail["health_details"]["source_kind"] == "media_validation_missing"
    assert "not been validated" in detail["health_details"]["reason"]


@pytest.mark.unit
def test_artifact_manager_uses_matching_final_output_validation_and_ignores_old_one(
    tmp_path: Path,
) -> None:
    workspace_root = Path(__file__).resolve().parents[2]
    seeded = seed_final_output_project(tmp_path, rendered_scene_ids=["scene_001"])
    from cine_forge.driver.engine import DriverEngine

    engine = DriverEngine(workspace_root=workspace_root, project_dir=seeded["project_dir"])
    first_run = engine.run(
        recipe_path=workspace_root / "configs" / "recipes" / "recipe-final-output.yaml",
        run_id="artifact-manager-final-output-overlay",
        end_at="final_output",
        force=True,
    )
    first_ref = ArtifactRef.model_validate(first_run["stages"]["final_output"]["artifact_refs"][0])
    first_artifact = FinalOutputArtifact.model_validate(engine.store.load_artifact(first_ref).data)

    _seed_validation(
        engine.store,
        target=MediaValidationTarget(
            scope_kind="project",
            entity_id="project",
            label="Project final output",
            coverage_state="partial",
            included_scene_count=1,
            omitted_scene_count=1,
        ),
        target_ref=first_ref,
        prompt_ref=None,
        validated_media=first_artifact.video,
        entity_id="project",
        declared_duration_seconds=float(first_artifact.video.duration_seconds or 0.0),
        recommended_health=ArtifactHealth.NEEDS_REVISION,
    )

    second_run = engine.run(
        recipe_path=workspace_root / "configs" / "recipes" / "recipe-final-output.yaml",
        run_id="artifact-manager-final-output-overlay-refresh",
        end_at="final_output",
        force=True,
    )
    second_ref = ArtifactRef.model_validate(
        second_run["stages"]["final_output"]["artifact_refs"][0]
    )
    second_artifact = FinalOutputArtifact.model_validate(
        engine.store.load_artifact(second_ref).data
    )

    stale_detail = _manager(seeded["project_dir"]).read_artifact(
        "project-id",
        "final_output",
        "project",
        second_ref.version,
    )

    assert stale_detail["health"] == ArtifactHealth.NEEDS_REVIEW.value
    assert stale_detail["health_details"]["source_kind"] == "media_validation_stale"
    assert (
        stale_detail["health_details"]["source_artifact_ref"]["artifact_type"]
        == "media_validation"
    )

    _seed_validation(
        engine.store,
        target=MediaValidationTarget(
            scope_kind="project",
            entity_id="project",
            label="Project final output",
            coverage_state="partial",
            included_scene_count=1,
            omitted_scene_count=1,
        ),
        target_ref=second_ref,
        prompt_ref=None,
        validated_media=second_artifact.video,
        entity_id="project",
        declared_duration_seconds=float(second_artifact.video.duration_seconds or 0.0),
        recommended_health=ArtifactHealth.NEEDS_REVIEW,
    )

    detail = _manager(seeded["project_dir"]).read_artifact(
        "project-id",
        "final_output",
        "project",
        second_ref.version,
    )

    assert detail["health"] == ArtifactHealth.NEEDS_REVIEW.value
    assert detail["health_details"]["source_kind"] == "media_validation"
    assert detail["health_details"]["source_artifact_ref"]["artifact_type"] == "media_validation"
