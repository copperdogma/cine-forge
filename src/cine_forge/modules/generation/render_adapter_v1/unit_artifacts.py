"""Build immutable render unit artifacts from prepared inputs and receipts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cine_forge.artifacts import ArtifactStore
from cine_forge.modules.generation.render_adapter_v1.outputs import (
    _build_preview_provenance,
    _scene_cost,
)
from cine_forge.modules.generation.render_adapter_v1.render_units import render_unit_kind
from cine_forge.modules.generation.render_adapter_v1.support import latest_entity_ref, relative_path
from cine_forge.modules.generation.render_adapter_v1.unit_preparation import PreparedRenderUnit
from cine_forge.schemas import (
    CompiledRenderPrompt,
    CostRecord,
    GeneratedVideoArtifact,
    MediaFile,
    RenderClip,
    Scene,
    ShotPlan,
)
from cine_forge.schemas.media_cost import CostReceipt
from cine_forge.schemas.scene_scope import SceneActionPreflight


def build_prompt_artifact(
    *,
    store: ArtifactStore,
    scene: Scene,
    plan: ShotPlan,
    unit: PreparedRenderUnit,
    render_clip: RenderClip | None,
    source_maps: dict[str, Any],
    engine_pack: Any,
    compiler_model: str,
    output_contract: dict[str, Any],
    scene_action_preflight: SceneActionPreflight | None,
    compile_cost: dict[str, Any],
    prompt_text: str,
    sections: Any,
    completeness: Any,
    prompt_sources: list[str],
) -> CompiledRenderPrompt:
    scene_cost = _scene_cost(
        compile_cost=compile_cost,
        generation_model=engine_pack.target_model,
        request_id=None,
    )
    preview_provenance = _build_preview_provenance(
        output_contract=output_contract,
        scene_cost=scene_cost,
        prompt_sources=prompt_sources,
        resolved_inputs=unit.resolved_inputs,
        generation_latency_ms=None,
        scene_action_preflight=scene_action_preflight,
    )
    return CompiledRenderPrompt(
        scene_id=plan.scene_id,
        scene_number=plan.scene_number,
        scene_heading=plan.scene_heading,
        render_unit=render_unit_kind(render_clip),
        render_clip_id=render_clip.clip_id if render_clip else None,
        render_clip_start_time_seconds=render_clip.start_time_seconds if render_clip else None,
        render_clip_end_time_seconds=render_clip.end_time_seconds if render_clip else None,
        source_shot_ids=list(render_clip.source_shot_ids) if render_clip else [],
        fallback_beat_ids=list(render_clip.fallback_beat_ids) if render_clip else [],
        scene_ref=plan.scene_ref,
        shot_plan_ref=unit.shot_plan_ref,
        render_clip_plan_ref=unit.render_clip_plan_ref,
        keyframe_ref=latest_entity_ref(store, "keyframe", plan.scene_id),
        target_provider=engine_pack.provider,
        target_model=engine_pack.target_model,
        engine_pack_id=engine_pack.pack_id,
        compiler_model=compiler_model,
        requested_duration_seconds=float(unit.requested_duration_seconds),
        resolved_duration_seconds=float(unit.duration_seconds),
        resolution=unit.resolution,
        aspect_ratio=unit.aspect_ratio,
        provider_params=unit.request.provider_params,
        prompt_text=prompt_text,
        sections=sections,
        completeness=completeness,
        prompt_sources_used=prompt_sources,
        creative_brief_preview=source_maps["creative_brief"],
        resolved_inputs=unit.resolved_inputs,
        preview_provenance=preview_provenance,
    )


def build_video_artifact(
    *,
    store: ArtifactStore,
    plan: ShotPlan,
    unit: PreparedRenderUnit,
    render_clip: RenderClip | None,
    engine_pack: Any,
    output_contract: dict[str, Any],
    scene_action_preflight: SceneActionPreflight | None,
    result: Any,
    scene_cost: dict[str, Any],
    cost_receipts: list[CostReceipt],
    output_path: Path,
    latency_ms: int,
    prompt: CompiledRenderPrompt,
) -> GeneratedVideoArtifact:
    cost_is_complete = any(r.component == "video" for r in cost_receipts) and all(
        r.status == "estimated" for r in cost_receipts
    )
    provenance = _build_preview_provenance(
        output_contract=output_contract,
        scene_cost=scene_cost,
        prompt_sources=prompt.prompt_sources_used,
        resolved_inputs=unit.resolved_inputs,
        generation_latency_ms=latency_ms,
        scene_action_preflight=scene_action_preflight,
    )
    notes = list(prompt.completeness.notes)
    if not cost_is_complete:
        provenance = provenance.model_copy(update={"estimated_cost_usd": None})
        notes.append(
            "Media cost is incomplete; an unresolved provider charge remains. "
            "The recorded cost contains only known estimates."
        )
    return GeneratedVideoArtifact(
        scene_id=plan.scene_id,
        scene_number=plan.scene_number,
        scene_heading=plan.scene_heading,
        render_unit=render_unit_kind(render_clip),
        render_clip_id=render_clip.clip_id if render_clip else None,
        render_clip_start_time_seconds=render_clip.start_time_seconds if render_clip else None,
        render_clip_end_time_seconds=render_clip.end_time_seconds if render_clip else None,
        source_shot_ids=list(render_clip.source_shot_ids) if render_clip else [],
        fallback_beat_ids=list(render_clip.fallback_beat_ids) if render_clip else [],
        scene_ref=plan.scene_ref,
        shot_plan_ref=unit.shot_plan_ref,
        render_clip_plan_ref=unit.render_clip_plan_ref,
        prompt_ref=unit.prompt_ref,
        keyframe_ref=latest_entity_ref(store, "keyframe", plan.scene_id),
        video=MediaFile(
            relative_path=relative_path(store.project_dir, output_path),
            media_type=result.media_type,
            duration_seconds=float(unit.duration_seconds),
        ),
        duration_seconds=float(unit.duration_seconds),
        resolution=unit.resolution,
        aspect_ratio=unit.aspect_ratio,
        generation_params={
            "duration_seconds": unit.duration_seconds,
            "resolution": unit.resolution,
            "aspect_ratio": unit.aspect_ratio,
            "provider_params": unit.request.provider_params,
        },
        target_provider=engine_pack.provider,
        target_model=result.model_used,
        engine_pack_id=engine_pack.pack_id,
        request_id=result.request_id or result.provider_job_id,
        cost=CostRecord.model_validate(scene_cost),
        cost_is_complete=cost_is_complete,
        cost_receipts=cost_receipts,
        resolved_inputs=unit.resolved_inputs,
        notes=notes,
        preview_provenance=provenance,
    )
