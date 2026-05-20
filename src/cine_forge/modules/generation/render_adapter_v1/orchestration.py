"""Render-unit orchestration and failure helpers for render adapter generation."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from cine_forge.ai.video import VideoGenerationError
from cine_forge.artifacts import ArtifactStore
from cine_forge.schemas import RenderClip, RenderClipPlan, Scene, ShotPlan
from cine_forge.schemas.scene_scope import SceneActionPreflight
from cine_forge.services.design_study_backfill import DefaultDesignStudyBackfillService


def _render_scene_outputs(
    *,
    render_scene: Callable[..., tuple[dict[str, Any], dict[str, Any], dict[str, Any]]],
    store: ArtifactStore,
    scene: Scene,
    plan: ShotPlan,
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
) -> tuple[list[tuple[dict[str, Any], dict[str, Any], dict[str, Any]]], list[dict[str, Any]]]:
    render_clip_plan = source_maps["render_clip_plan"].get(plan.scene_id)
    render_clips = _render_clips_for_scene(
        scene_id=plan.scene_id,
        render_clip_plan=render_clip_plan,
        output_contract=output_contract,
        selected_render_clip_ids=selected_render_clip_ids,
    )
    outputs: list[tuple[dict[str, Any], dict[str, Any], dict[str, Any]]] = []
    failures: list[dict[str, Any]] = []
    if default_design_study_backfill:
        _backfill_default_design_studies(
            store=store,
            scene=scene,
            image_model=default_design_study_backfill_model,
        )
    for render_clip in render_clips:
        try:
            outputs.append(
                render_scene(
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
                    render_clip=render_clip,
                )
            )
        except Exception as exc:  # noqa: BLE001
            failures.append(_scene_failure(plan=plan, exc=exc, render_clip=render_clip))
            if _should_abort_remaining_render_units(exc):
                break
    return outputs, failures


def _backfill_default_design_studies(
    *,
    store: ArtifactStore,
    scene: Scene,
    image_model: str,
) -> None:
    result = DefaultDesignStudyBackfillService(
        store.project_dir,
        image_model=image_model,
    ).backfill_scene(scene)
    failures = [item for item in result.items if item.status == "failed"]
    if failures:
        details = "; ".join(
            f"{item.entity_id}: {item.reason or 'unknown failure'}" for item in failures
        )
        raise ValueError(f"Default design-study backfill failed before render: {details}")
    if result.generated_count:
        print(
            "[render_adapter] Backfilled "
            f"{result.generated_count} default design-study reference(s) "
            f"for {scene.scene_id} with {image_model}."
        )


def _should_abort_remaining_render_units(exc: Exception) -> bool:
    if not isinstance(exc, VideoGenerationError):
        return False
    message = str(exc).lower()
    return "timed out after" in message and "waiting for completion" in message


def _render_clips_for_scene(
    *,
    scene_id: str,
    render_clip_plan: RenderClipPlan | None,
    output_contract: dict[str, Any],
    selected_render_clip_ids: set[str] | None = None,
) -> list[RenderClip | None]:
    if render_clip_plan is not None and len(render_clip_plan.clips) > 1:
        clips = list(render_clip_plan.clips)
        if selected_render_clip_ids is None:
            return clips
        selected_clips = [
            clip for clip in clips if clip.clip_id in selected_render_clip_ids
        ]
        matched_clip_ids = {clip.clip_id for clip in selected_clips}
        missing_clip_ids = selected_render_clip_ids - matched_clip_ids
        if missing_clip_ids:
            requested = ", ".join(sorted(missing_clip_ids))
            available = ", ".join(clip.clip_id for clip in clips)
            raise ValueError(
                "render_adapter_v1 could not find requested render clip(s) "
                f"for {scene_id}: {requested}. Available clips: {available}."
            )
        return selected_clips
    if selected_render_clip_ids is not None:
        requested = ", ".join(sorted(selected_render_clip_ids))
        raise ValueError(
            "render_adapter_v1 received render_clip_ids for a scene without a "
            f"multi-clip render_clip_plan: {scene_id} ({requested})."
        )
    return [None]


def _ensure_required_render_clip_plans(
    *,
    params: dict[str, Any],
    context: dict[str, Any],
    shot_plans: list[ShotPlan],
    source_maps: dict[str, Any],
) -> None:
    if not bool(params.get("require_render_clip_plan")):
        return
    missing_scene_ids = [
        plan.scene_id
        for plan in shot_plans
        if plan.scene_id not in source_maps["render_clip_plan"]
    ]
    if not missing_scene_ids:
        return
    stage_id = context.get("stage_id", "render") if isinstance(context, dict) else "render"
    missing = ", ".join(sorted(missing_scene_ids))
    raise ValueError(
        f"Stage '{stage_id}' requires render_clip_plan artifacts for {missing}. "
        "Run render_clip_planning before this stage."
    )


def _planned_render_unit_count(
    *,
    plan: ShotPlan,
    source_maps: dict[str, Any],
    output_contract: dict[str, Any],
    selected_render_clip_ids: set[str] | None = None,
) -> int:
    return len(
        _render_clips_for_scene(
            scene_id=plan.scene_id,
            render_clip_plan=source_maps["render_clip_plan"].get(plan.scene_id),
            output_contract=output_contract,
            selected_render_clip_ids=selected_render_clip_ids,
        )
    )


def _scene_failure(
    *,
    plan: ShotPlan,
    exc: Exception,
    render_clip: RenderClip | None = None,
) -> dict[str, Any]:
    return {
        "scene_id": plan.scene_id,
        "scene_number": plan.scene_number,
        "scene_heading": plan.scene_heading,
        "render_clip_id": render_clip.clip_id if render_clip else None,
        "error_class": exc.__class__.__name__,
        "error": _clean_error_detail(str(exc)),
        "exception": exc,
    }


def _clean_error_detail(message: str) -> str:
    compact = " ".join(message.split())
    return compact if compact else "Unknown render failure"


def _render_failure_summary(
    *,
    failures: list[dict[str, Any]],
    success_count: int,
    total_count: int,
) -> str:
    failure_count = len(failures)
    details = ", ".join(
        (
            f"{failure['scene_id']}:{failure['render_clip_id']}"
            if failure.get("render_clip_id")
            else failure["scene_id"]
        )
        + f" ({failure['error_class']}: {failure['error']})"
        for failure in failures[:5]
    )
    if failure_count > 5:
        details += f", +{failure_count - 5} more"
    if success_count > 0:
        return (
            "Render generation preserved "
            f"{success_count} successful render unit(s) but failed for "
            f"{failure_count}/{total_count} render unit(s): {details}."
        )
    return (
        "Render generation failed before any render units were preserved: "
        f"{details}."
    )
