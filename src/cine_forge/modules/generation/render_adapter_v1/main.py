"""Scene-level render adapter entrypoint."""

from __future__ import annotations

from typing import Any

from cine_forge.ai.video_pricing import validate_video_target
from cine_forge.artifacts import ArtifactStore
from cine_forge.execution_errors import ModuleCostError
from cine_forge.modules.generation.render_adapter_v1.execution import execute_render
from cine_forge.modules.generation.render_adapter_v1.orchestration import (
    _ensure_required_render_clip_plans,
    ensure_backfill_ready,
)
from cine_forge.modules.generation.render_adapter_v1.source_inputs import (
    _build_source_maps,
    _default_design_study_backfill_enabled,
    _default_design_study_backfill_model,
    _output_contract,
    _project_dir,
    _runtime_params,
    _scene_action_preflight,
    _selected_render_clip_ids,
    _shot_plans,
    _track_manifest,
)
from cine_forge.modules.generation.render_adapter_v1.support import (
    load_engine_pack,
    optional_string,
)
from cine_forge.schemas import Scene
from cine_forge.schemas.media_cost import CostReceipt


def run_module(
    inputs: dict[str, Any],
    params: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    """Validate paid targets, then preserve both outputs and incurred call receipts."""
    if _runtime_params(context).get("media_execution_plan_ref"):
        from cine_forge.services.media_plan_execution import execute_approved_media
        return execute_approved_media(inputs=inputs, params=params, context=context)
    store = ArtifactStore(project_dir=_project_dir(context))
    runtime_params = _runtime_params(context)
    shot_plans = sorted(
        _shot_plans(inputs, runtime_params=runtime_params), key=lambda p: p.scene_number
    )
    contract = _output_contract(params=params, runtime_params=runtime_params)
    engine_pack = load_engine_pack(
        str(
            params.get("engine_pack_id")
            or runtime_params.get("engine_pack_id")
            or contract["default_engine_pack_id"]
        )
    )
    validate_video_target(provider=engine_pack.provider, model=engine_pack.target_model)
    compiler_model = str(
        params.get("compiler_model")
        or runtime_params.get("compiler_model")
        or contract["default_compiler_model"]
    )
    source_maps = _build_source_maps(inputs)
    _ensure_required_render_clip_plans(
        params=params,
        context=context,
        shot_plans=shot_plans,
        source_maps=source_maps,
    )
    scenes = [Scene.model_validate(store.load_artifact(p.scene_ref).data) for p in shot_plans]
    backfill = _default_design_study_backfill_enabled(params=params, runtime_params=runtime_params)
    backfill_model = _default_design_study_backfill_model(
        params=params,
        runtime_params=runtime_params,
        compiler_model=compiler_model,
    )
    if backfill:
        ensure_backfill_ready(store=store, scenes=scenes, image_model=backfill_model)
    cost_receipts: list[CostReceipt] = []
    try:
        return execute_render(
            store=store,
            scenes=scenes,
            shot_plans=shot_plans,
            track_manifest=_track_manifest(inputs),
            source_maps=source_maps,
            engine_pack=engine_pack,
            compiler_model=compiler_model,
            requested_duration_seconds=float(
                params.get("duration_seconds") or runtime_params.get("duration_seconds") or 8.0
            ),
            requested_resolution=optional_string(
                params.get("resolution") or runtime_params.get("resolution")
            ),
            requested_aspect_ratio=optional_string(
                params.get("aspect_ratio") or runtime_params.get("aspect_ratio")
            ),
            output_contract=contract,
            scene_action_preflight=_scene_action_preflight(runtime_params),
            selected_render_clip_ids=_selected_render_clip_ids(runtime_params),
            default_design_study_backfill=backfill,
            default_design_study_backfill_model=backfill_model,
            announce_artifact=context.get("announce_artifact"),
            cost_receipts=cost_receipts,
        )
    except ModuleCostError:
        raise
    except Exception as exc:
        if cost_receipts:
            raise ModuleCostError(str(exc), cost_receipts=cost_receipts) from exc
        raise
