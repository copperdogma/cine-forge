"""One render unit's paid calls and immutable output assembly."""

from __future__ import annotations

import time
from typing import Any
from uuid import uuid4

from cine_forge.ai.video import VideoGenerationRequest, generate_video
from cine_forge.artifacts import ArtifactStore
from cine_forge.modules.generation.render_adapter_v1.accounting import (
    aggregate_receipts,
    record_media_receipts,
)
from cine_forge.modules.generation.render_adapter_v1.outputs import (
    _prompt_artifact_dict,
    _video_artifact_dict,
)
from cine_forge.modules.generation.render_adapter_v1.support import render_media_dir
from cine_forge.modules.generation.render_adapter_v1.unit_artifacts import build_video_artifact
from cine_forge.modules.generation.render_adapter_v1.unit_preparation import (
    PreparedRenderUnit,
    prepare_render_unit,
)
from cine_forge.modules.generation.render_adapter_v1.unit_prompt import compile_unit_prompt
from cine_forge.schemas import CompiledRenderPrompt, RenderClip, Scene, ShotPlan
from cine_forge.schemas.media_cost import CostReceipt
from cine_forge.schemas.scene_scope import SceneActionPreflight


def _render_scene(
    *,
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
    cost_receipts: list[CostReceipt],
    render_clip: RenderClip | None = None,
    prepared_unit: PreparedRenderUnit | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    started = time.perf_counter()
    receipt_start = len(cost_receipts)
    unit = prepared_unit or prepare_render_unit(
        store=store,
        scene=scene,
        plan=plan,
        source_maps=source_maps,
        engine_pack=engine_pack,
        requested_duration_seconds=requested_duration_seconds,
        requested_resolution=requested_resolution,
        requested_aspect_ratio=requested_aspect_ratio,
        output_contract=output_contract,
        render_clip=render_clip,
    )
    prompt = compile_unit_prompt(
        store=store,
        scene=scene,
        plan=plan,
        source_maps=source_maps,
        engine_pack=engine_pack,
        compiler_model=compiler_model,
        output_contract=output_contract,
        scene_action_preflight=scene_action_preflight,
        render_clip=render_clip,
        unit=unit,
        cost_receipts=cost_receipts,
    )
    result = _generate_with_receipts(
        unit=unit,
        prompt=prompt,
        engine_pack=engine_pack,
        cost_receipts=cost_receipts,
    )
    unit_receipts = cost_receipts[receipt_start:]
    scene_cost = aggregate_receipts(unit_receipts, model=result.model_used)
    scene_cost["request_id"] = result.request_id or result.provider_job_id
    media_dir = render_media_dir(
        store.project_dir,
        unit.entity_id,
        unit.video_ref.version,
        media_root=output_contract["media_root"],
    )
    media_dir.mkdir(parents=True, exist_ok=True)
    output_path = media_dir / output_contract["media_filename"]
    output_path.write_bytes(result.video_bytes)
    generated = build_video_artifact(
        store=store,
        plan=plan,
        unit=unit,
        render_clip=render_clip,
        engine_pack=engine_pack,
        output_contract=output_contract,
        scene_action_preflight=scene_action_preflight,
        result=result,
        scene_cost=scene_cost,
        cost_receipts=unit_receipts,
        output_path=output_path,
        latency_ms=round((time.perf_counter() - started) * 1000),
        prompt=prompt,
    )
    video_artifact = _video_artifact_dict(
        generated_video=generated,
        prompt_artifact=prompt,
        compile_cost=scene_cost,
        request_notes=unit.request_notes,
        output_contract=output_contract,
    )
    return (
        _prompt_artifact_dict(prompt, output_contract=output_contract),
        video_artifact,
        scene_cost,
    )


def _generate_with_receipts(
    *,
    unit: PreparedRenderUnit,
    prompt: CompiledRenderPrompt,
    engine_pack: Any,
    cost_receipts: list[CostReceipt],
) -> Any:
    request = VideoGenerationRequest(
        prompt=prompt.prompt_text,
        duration_seconds=unit.request.duration_seconds,
        resolution=unit.request.resolution,
        aspect_ratio=unit.request.aspect_ratio,
        first_frame=unit.request.first_frame,
        last_frame=unit.request.last_frame,
        reference_images=unit.request.reference_images,
        provider_params=unit.request.provider_params,
    )
    try:
        result = generate_video(request=request, engine_pack=engine_pack)
    except Exception as exc:
        record_media_receipts(
            cost_receipts,
            getattr(exc, "cost_receipts", []),
            scene_id=unit.plan.scene_id,
            entity_id=unit.entity_id,
        )
        raise
    if not result.cost_receipts:
        cost_receipts.append(
            CostReceipt(
                receipt_id=f"unaccounted-video:{uuid4()}",
                component="video",
                model=result.model_used,
                status="uncertain",
                provider=engine_pack.provider,
                provider_job_id=result.provider_job_id or result.request_id,
                scene_id=unit.plan.scene_id,
                entity_id=unit.entity_id,
                reason="Video generation returned media without any cost receipt.",
            )
        )
        raise ValueError("Video generation returned no cost receipts; media cost is unknown")
    record_media_receipts(
        cost_receipts,
        result.cost_receipts,
        scene_id=unit.plan.scene_id,
        entity_id=unit.entity_id,
    )
    return result
