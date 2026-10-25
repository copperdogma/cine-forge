"""Batch rendering, partial-output preservation, and terminal cost evidence."""

from __future__ import annotations

from typing import Any

from cine_forge.artifacts import ArtifactStore
from cine_forge.execution_errors import ModuleCostError
from cine_forge.modules.generation.render_adapter_v1.accounting import aggregate_receipts
from cine_forge.modules.generation.render_adapter_v1.orchestration import (
    _planned_render_unit_count,
    _render_failure_summary,
    _render_scene_outputs,
)
from cine_forge.modules.generation.render_adapter_v1.outputs import (
    GeneratedVideoTrackRef,
    _track_manifest_artifact_dict,
    _update_track_manifest_with_video_track,
)
from cine_forge.modules.generation.render_adapter_v1.render_unit import _render_scene
from cine_forge.modules.generation.render_adapter_v1.support import (
    anticipated_entity_ref,
    latest_project_ref,
)
from cine_forge.schemas import ArtifactRef, GeneratedVideoArtifact, Scene, ShotPlan, TrackManifest
from cine_forge.schemas.media_cost import CostReceipt
from cine_forge.schemas.scene_scope import SceneActionPreflight


def execute_render(
    *,
    store: ArtifactStore,
    scenes: list[Scene],
    shot_plans: list[ShotPlan],
    track_manifest: TrackManifest,
    source_maps: dict[str, Any],
    engine_pack: Any,
    compiler_model: str,
    requested_duration_seconds: float,
    requested_resolution: str | None,
    requested_aspect_ratio: str | None,
    output_contract: dict[str, Any],
    scene_action_preflight: SceneActionPreflight | None,
    selected_render_clip_ids: set[str] | None,
    default_design_study_backfill: bool,
    default_design_study_backfill_model: str,
    announce_artifact: Any,
    cost_receipts: list[CostReceipt],
    prepared_units: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifacts: list[dict[str, Any]] = []
    generated_refs: list[GeneratedVideoTrackRef] = []
    failures: list[dict[str, Any]] = []
    planned_count = 0
    for scene, plan in zip(scenes, shot_plans, strict=True):
        planned_count += _planned_render_unit_count(
            plan=plan,
            source_maps=source_maps,
            output_contract=output_contract,
            selected_render_clip_ids=selected_render_clip_ids,
        )
        outputs, scene_failures = _render_scene_outputs(
            render_scene=_render_scene,
            store=store,
            scene=scene,
            plan=plan,
            source_maps=source_maps,
            engine_pack=engine_pack,
            compiler_model=compiler_model,
            requested_duration_seconds=requested_duration_seconds,
            requested_resolution=requested_resolution,
            requested_aspect_ratio=requested_aspect_ratio,
            output_contract=output_contract,
            scene_action_preflight=scene_action_preflight,
            selected_render_clip_ids=selected_render_clip_ids,
            default_design_study_backfill=default_design_study_backfill,
            default_design_study_backfill_model=default_design_study_backfill_model,
            cost_receipts=cost_receipts,
            prepared_units=prepared_units,
        )
        failures.extend(scene_failures)
        _preserve_outputs(
            store=store,
            outputs=outputs,
            artifacts=artifacts,
            generated_refs=generated_refs,
            announce_artifact=announce_artifact,
            output_contract=output_contract,
        )
        if any(receipt.status == "uncertain" for receipt in cost_receipts):
            break
    if generated_refs:
        artifacts.append(
            _finalize_track(
                store=store,
                track_manifest=track_manifest,
                generated_refs=generated_refs,
                output_contract=output_contract,
                announce_artifact=announce_artifact,
            )
        )
    if any(receipt.status == "uncertain" for receipt in cost_receipts):
        raise ModuleCostError(
            "Render cost is unresolved; preserved available media and stopped further paid work.",
            cost_receipts=cost_receipts,
        )
    if failures:
        message = (
            failures[0]["error"]
            if len(failures) == 1 and not generated_refs
            else _render_failure_summary(
                failures=failures,
                success_count=len(generated_refs),
                total_count=planned_count or len(shot_plans),
            )
        )
        if cost_receipts:
            raise ModuleCostError(message, cost_receipts=cost_receipts)
        raise failures[0]["exception"] if len(failures) == 1 else RuntimeError(message)
    return {
        "artifacts": artifacts,
        "cost": aggregate_receipts(cost_receipts),
        "cost_receipts": [r.model_dump(mode="json") for r in cost_receipts],
    }


def _preserve_outputs(
    *,
    store: ArtifactStore,
    outputs: list[tuple[dict[str, Any], dict[str, Any], dict[str, Any]]],
    artifacts: list[dict[str, Any]],
    generated_refs: list[GeneratedVideoTrackRef],
    announce_artifact: Any,
    output_contract: dict[str, Any],
) -> None:
    for prompt_artifact, video_artifact, _cost in outputs:
        _announce_artifact(announce_artifact, prompt_artifact)
        video_ref = _announce_artifact(announce_artifact, video_artifact)
        if video_ref is None:
            video_ref = anticipated_entity_ref(
                store,
                output_contract["video_artifact_type"],
                str(video_artifact["entity_id"]),
            )
        video = GeneratedVideoArtifact.model_validate(video_artifact["data"])
        generated_refs.append(
            GeneratedVideoTrackRef(
                scene_id=video.scene_id,
                artifact_ref=video_ref,
                render_clip_id=video.render_clip_id,
                start_time_seconds=video.render_clip_start_time_seconds,
                end_time_seconds=video.render_clip_end_time_seconds,
            )
        )
        artifacts.extend([prompt_artifact, video_artifact])


def _finalize_track(
    *,
    store: ArtifactStore,
    track_manifest: TrackManifest,
    generated_refs: list[GeneratedVideoTrackRef],
    output_contract: dict[str, Any],
    announce_artifact: Any,
) -> dict[str, Any]:
    ref = latest_project_ref(store, "track_manifest")
    if ref is None:
        raise ValueError("render_adapter_v1 could not resolve latest track_manifest artifact")
    updated = _update_track_manifest_with_video_track(
        manifest=track_manifest,
        generated_video_refs=generated_refs,
        track_type=output_contract["track_type"],
        priority=output_contract["track_priority"],
        notes=output_contract["track_note"],
    )
    artifact = _track_manifest_artifact_dict(
        updated_manifest=updated,
        track_manifest_ref=ref,
        generated_video_refs=generated_refs,
    )
    _announce_artifact(announce_artifact, artifact)
    return artifact


def _announce_artifact(announce: Any, artifact: dict[str, Any]) -> ArtifactRef | None:
    if not callable(announce):
        return None
    announce(artifact)
    raw = artifact.get("pre_saved_ref")
    return ArtifactRef.model_validate(raw) if isinstance(raw, dict) else None
