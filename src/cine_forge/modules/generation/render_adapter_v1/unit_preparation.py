"""Resolve exact request inputs before spending on prompt compilation."""

from __future__ import annotations

from typing import Any, NamedTuple

from cine_forge.ai.video import VideoGenerationRequest
from cine_forge.ai.video_pricing import resolve_video_price
from cine_forge.artifacts import ArtifactStore
from cine_forge.modules.generation.render_adapter_v1.render_units import (
    clipped_shot_plan,
    render_unit_entity_id,
)
from cine_forge.modules.generation.render_adapter_v1.request_shaping import (
    _shape_generation_request,
)
from cine_forge.modules.generation.render_adapter_v1.resolved_inputs import (
    _collect_resolved_inputs,
    _look_and_feel_aspect_ratio,
    _project_aspect_ratio,
    _resolve_resolution,
)
from cine_forge.modules.generation.render_adapter_v1.support import (
    anticipated_entity_ref,
    latest_entity_ref,
    normalize_aspect_ratio,
    normalize_duration_seconds,
)
from cine_forge.schemas import ArtifactRef, RenderClip, RenderResolvedInput, Scene, ShotPlan


class PreparedRenderUnit(NamedTuple):
    entity_id: str
    plan: ShotPlan
    prompt_ref: ArtifactRef
    video_ref: ArtifactRef
    shot_plan_ref: ArtifactRef
    render_clip_plan_ref: ArtifactRef | None
    requested_duration_seconds: float
    duration_seconds: int
    resolution: str
    aspect_ratio: str
    request: VideoGenerationRequest
    resolved_inputs: list[RenderResolvedInput]
    notes: list[str]
    request_notes: list[str]


def prepare_render_unit(
    *,
    store: ArtifactStore,
    scene: Scene,
    plan: ShotPlan,
    source_maps: dict[str, Any],
    engine_pack: Any,
    requested_duration_seconds: float,
    requested_resolution: str | None,
    requested_aspect_ratio: str | None,
    output_contract: dict[str, Any],
    render_clip: RenderClip | None,
    validate_price: bool = True,
) -> PreparedRenderUnit:
    entity_id = render_unit_entity_id(plan.scene_id, render_clip)
    unit_plan = clipped_shot_plan(plan, render_clip)
    requested_duration = (
        render_clip.target_duration_seconds if render_clip else requested_duration_seconds
    )
    shot_plan_ref = latest_entity_ref(store, "shot_plan", plan.scene_id)
    if shot_plan_ref is None:
        raise ValueError(f"render_adapter_v1 could not resolve shot_plan ref for {plan.scene_id}")
    aspect_ratio, aspect_note = normalize_aspect_ratio(
        requested_aspect_ratio
        or _look_and_feel_aspect_ratio(source_maps["look_and_feel"].get(plan.scene_id))
        or _project_aspect_ratio(source_maps["project_config"]),
        engine_pack.limits.supported_aspect_ratios,
    )
    duration_seconds, duration_note = normalize_duration_seconds(
        requested_duration,
        engine_pack.limits.supported_durations_seconds,
    )
    resolution, resolution_note = _resolve_resolution(
        requested_resolution=requested_resolution,
        engine_pack=engine_pack,
        aspect_ratio=aspect_ratio,
    )
    resolved_inputs = _collect_resolved_inputs(
        store=store,
        scene=scene,
        keyframe_artifact=source_maps["keyframes"].get(plan.scene_id),
        source_maps=source_maps,
    )
    request, resolved_inputs, request_notes = _shape_generation_request(
        engine_pack=engine_pack,
        project_dir=store.project_dir,
        resolved_inputs=resolved_inputs,
        duration_seconds=duration_seconds,
        resolution=resolution,
        aspect_ratio=aspect_ratio,
        allow_prompt_only_required_media=output_contract["prompt_mode"] == "ai_previz",
    )
    # Prices apply to the shaped request, never stale pack benchmarks or requested defaults.
    if validate_price:
        resolve_video_price(
            provider=engine_pack.provider,
            model=engine_pack.target_model,
            resolution=request.resolution,
        )
    return PreparedRenderUnit(
        entity_id=entity_id,
        plan=unit_plan,
        prompt_ref=anticipated_entity_ref(
            store, output_contract["prompt_artifact_type"], entity_id
        ),
        video_ref=anticipated_entity_ref(store, output_contract["video_artifact_type"], entity_id),
        shot_plan_ref=shot_plan_ref,
        render_clip_plan_ref=latest_entity_ref(store, "render_clip_plan", plan.scene_id),
        requested_duration_seconds=float(requested_duration),
        duration_seconds=request.duration_seconds,
        resolution=request.resolution,
        aspect_ratio=request.aspect_ratio,
        request=request,
        resolved_inputs=resolved_inputs,
        notes=[n for n in (aspect_note, duration_note, resolution_note, *request_notes) if n],
        request_notes=request_notes,
    )
