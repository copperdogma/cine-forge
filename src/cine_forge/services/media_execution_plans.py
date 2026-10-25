"""Build no-call scene execution plans using the actual renderer's unit preparation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from cine_forge.ai.video import _validate_priced_request
from cine_forge.ai.video_pricing import resolve_video_price
from cine_forge.artifacts import ArtifactStore
from cine_forge.driver.input_collection import collect_inputs
from cine_forge.driver.recipe import load_recipe, resolve_runtime_params
from cine_forge.modules.generation.render_adapter_v1 import source_inputs as source
from cine_forge.modules.generation.render_adapter_v1.orchestration import _render_clips_for_scene
from cine_forge.modules.generation.render_adapter_v1.support import (
    load_engine_pack,
    optional_string,
)
from cine_forge.modules.generation.render_adapter_v1.unit_preparation import prepare_render_unit
from cine_forge.schemas import ArtifactMetadata, Scene
from cine_forge.schemas.media_execution_plan import (
    MediaExecutionPlan,
    MediaExecutionPlanRequest,
    MediaExecutionPlanResponse,
    MediaExecutionUnit,
    MediaSourceBinding,
)
from cine_forge.services.design_study_backfill import DefaultDesignStudyBackfillService
from cine_forge.services.media_plan_sources import MediaSourceSnapshot, digest
from cine_forge.services.run_parameters import build_runtime_params


class PreparedMediaExecution:
    """In-process execution state; no mutable source is reloaded after validation."""

    def __init__(self, store: MediaSourceSnapshot):
        self.store = store
        self.units: dict[str, Any] = {}
        self.scenes: list[Scene] = []
        self.plans: list[Any] = []
        self.inputs: dict[str, Any] = {}
        self.source_maps: dict[str, Any] = {}
        self.params: dict[str, Any] = {}
        self.runtime: dict[str, Any] = {}
        self.request: dict[str, Any] = {}
        self.recipe: Any = None
        self.stage: Any = None
        self.engine_pack: Any = None
        self.contract: dict[str, Any] = {}
        self.compiler_model = ""
        self.backfill_model = ""
        self.plan: MediaExecutionPlan | None = None


def media_run_request(
    project_dir: Path, request: MediaExecutionPlanRequest, pj: dict[str, Any]
) -> dict[str, Any]:
    stage = "render" if request.recipe_id == "render_generation" else "ai_previz"
    inputs = sorted((project_dir / "inputs").glob("*"))
    result = {
        key: pj[key]
        for key in (
            "work_model",
            "verify_model",
            "qa_model",
            "escalate_model",
            "human_control_mode",
            "project_budget_limit_usd",
            "default_run_budget_limit_usd",
            "budget_warning_threshold_ratio",
            "style_packs",
        )
        if key in pj
    }
    result.update(
        {
            "input_file": str(inputs[0]) if inputs else str(project_dir / "inputs"),
            "default_model": pj.get("default_model") or "claude-sonnet-4-6",
            "recipe_id": request.recipe_id,
            "start_from": stage,
            "end_at": "validate_media",
            "scene_scope": {"mode": "current_scene", "scene_ids": [request.scene_id]},
            "render_clip_ids": request.render_clip_ids,
        }
    )
    return result


def prepare_media_execution(
    *,
    workspace_root: Path,
    project_dir: Path,
    project_id: str,
    request: MediaExecutionPlanRequest,
    actual_inputs: dict[str, Any] | None = None,
) -> PreparedMediaExecution:
    snapshot = PreparedMediaExecution(MediaSourceSnapshot(project_dir))
    raw_pj = snapshot.store.bind_file("project.json")
    pj = json.loads(raw_pj) if raw_pj else {}
    snapshot.request = media_run_request(project_dir, request, pj)
    snapshot.runtime = build_runtime_params(snapshot.request, pj)
    path = workspace_root / "configs/recipes" / f"recipe-{request.recipe_id.replace('_', '-')}.yaml"
    recipe = resolve_runtime_params(load_recipe(path), snapshot.runtime)
    snapshot.recipe = recipe
    snapshot.stage = next(s for s in recipe.stages if s.id == snapshot.request["start_from"])
    snapshot.params = snapshot.stage.params
    snapshot.contract = source._output_contract(
        params=snapshot.params, runtime_params=snapshot.runtime
    )
    contract = snapshot.contract
    snapshot.engine_pack = load_engine_pack(
        str(
            snapshot.params.get("engine_pack_id")
            or snapshot.runtime.get("engine_pack_id")
            or contract["default_engine_pack_id"]
        )
    )
    snapshot.compiler_model = str(
        snapshot.params.get("compiler_model")
        or snapshot.runtime.get("compiler_model")
        or contract["default_compiler_model"]
    )
    snapshot.backfill_model = source._default_design_study_backfill_model(
        params=snapshot.params,
        runtime_params=snapshot.runtime,
        compiler_model=snapshot.compiler_model,
    )
    blockers: list[str] = []
    rows: list[MediaExecutionUnit] = []
    try:
        inputs, _ = collect_inputs(
            store=snapshot.store,
            recipe=recipe,
            stage_id=snapshot.stage.id,
            stage_outputs={},
            runtime_params=snapshot.runtime,
        )
        if actual_inputs is not None and inputs != actual_inputs:
            raise ValueError("Actual renderer inputs differ from the inspected sources")
        snapshot.inputs = inputs
        snapshot.source_maps = source._build_source_maps(inputs)
        snapshot.plans = source._shot_plans(inputs, runtime_params=snapshot.runtime)
        if len(snapshot.plans) != 1 or snapshot.plans[0].scene_id != request.scene_id:
            raise ValueError("Prepare a healthy shot plan for the selected scene first")
        if request.scene_id not in snapshot.source_maps["render_clip_plan"]:
            raise ValueError("Prepare the selected scene through render_clip_planning first")
        _prepare_units(snapshot, request, rows, blockers)
    except (ValueError, OSError, KeyError) as exc:
        blockers.append(str(exc))
    snapshot.store.verify_files()
    bindings = snapshot.store.source_bindings()
    bindings.extend(
        [
            MediaSourceBinding(
                key="effective_recipe", sha256=digest(recipe.model_dump(mode="json"))
            ),
            MediaSourceBinding(
                key="engine_pack", sha256=digest(snapshot.engine_pack.model_dump(mode="json"))
            ),
        ]
    )
    return _finish_plan(snapshot, request, project_id, rows, blockers, bindings)


def _finish_plan(
    snapshot: PreparedMediaExecution,
    request: MediaExecutionPlanRequest,
    project_id: str,
    rows: list[MediaExecutionUnit],
    blockers: list[str],
    bindings: list[MediaSourceBinding],
) -> PreparedMediaExecution:
    prices_known = bool(rows) and all(r.video_estimate_usd is not None for r in rows)
    plan = MediaExecutionPlan(
        project_id=project_id,
        recipe_id=request.recipe_id,
        scene_id=request.scene_id,
        render_clip_ids=request.render_clip_ids,
        binding_sha256="",
        status="blocked" if blockers else "ready",
        blockers=list(dict.fromkeys(blockers)),
        units=rows,
        source_bindings=bindings,
        video_estimate_usd=round(sum(r.video_estimate_usd or 0 for r in rows), 8)
        if prices_known
        else None,
    )
    plan.binding_sha256 = digest(
        {
            "plan": plan.model_dump(mode="json"),
            "runtime": snapshot.runtime,
            "effective_settings": {
                "contract": snapshot.contract,
                "compiler_model": snapshot.compiler_model,
                "backfill_model": snapshot.backfill_model,
            },
            "inputs": snapshot.inputs,
            "units": [_unit_binding(u) for u in snapshot.units.values()],
        }
    )
    snapshot.plan = plan
    return snapshot


def _prepare_units(
    snapshot: PreparedMediaExecution,
    request: MediaExecutionPlanRequest,
    rows: list[MediaExecutionUnit],
    blockers: list[str],
) -> None:
    store, pack, maps = snapshot.store, snapshot.engine_pack, snapshot.source_maps
    plan = snapshot.plans[0]
    scene = Scene.model_validate(store.load_artifact(plan.scene_ref).data)
    snapshot.scenes = [scene]
    # Freeze optional provenance even if no locked keyframe is selected.
    store.list_versions("keyframe", scene.scene_id)
    _bind_reference_state(store, scene)
    if source._default_design_study_backfill_enabled(
        params=snapshot.params, runtime_params=snapshot.runtime
    ):
        if DefaultDesignStudyBackfillService(
            store.project_dir, image_model=snapshot.backfill_model
        ).generation_required(scene):
            blockers.append(
                "Reference images are missing. Prepare or select them before confirming; "
                "automatic image generation is not authorized by this plan."
            )
    clips = _render_clips_for_scene(
        scene_id=scene.scene_id,
        render_clip_plan=maps["render_clip_plan"].get(scene.scene_id),
        output_contract=snapshot.contract,
        selected_render_clip_ids=set(request.render_clip_ids) if request.render_clip_ids else None,
    )
    for clip in clips:
        unit = prepare_render_unit(
            store=store,
            scene=scene,
            plan=plan,
            source_maps=maps,
            engine_pack=pack,
            requested_duration_seconds=float(snapshot.params.get("duration_seconds") or 8),
            requested_resolution=optional_string(snapshot.params.get("resolution")),
            requested_aspect_ratio=optional_string(snapshot.params.get("aspect_ratio")),
            output_contract=snapshot.contract,
            render_clip=clip,
            validate_price=False,
        )
        snapshot.units[unit.entity_id] = unit
        for item in unit.resolved_inputs:
            store.bind_file(item.relative_path)
        price = None
        try:
            price = resolve_video_price(
                provider=pack.provider, model=pack.target_model, resolution=unit.resolution
            )
            _validate_priced_request(unit.request)
        except ValueError as exc:
            price = None
            blockers.append(str(exc))
        rows.append(
            MediaExecutionUnit(
                entity_id=unit.entity_id,
                clip_id=clip.clip_id if clip else None,
                title=f"{plan.scene_heading} — {clip.clip_id}" if clip else plan.scene_heading,
                planned_duration_seconds=unit.requested_duration_seconds,
                duration_seconds=unit.duration_seconds,
                resolution=unit.resolution,
                aspect_ratio=unit.aspect_ratio,
                provider=pack.provider,
                model=pack.target_model,
                price=price,
                video_estimate_usd=round(price.unit_price_usd * unit.duration_seconds, 8)
                if price
                else None,
            )
        )


def _bind_reference_state(store: MediaSourceSnapshot, scene: Scene) -> None:
    from cine_forge.modules.generation.render_adapter_v1.support import slugify

    targets = [
        *(f"character_{c}" for c in scene.characters_present_ids),
        f"location_{slugify(scene.location)}",
        *(f"prop_{slugify(p)}" for p in scene.props_mentioned),
    ]
    for target in targets:
        ref = store.latest_ref("bible_manifest", target)
        if ref:
            artifact = store.load_artifact(ref)
            folder = Path(ref.path).parent
            # Design-study selection is mutable beside the immutable manifest.
            store.bind_file(str(folder / "design_study_state.json"))
            filename = artifact.data.get("visual_reference_image")
            if filename:
                store.bind_file(str(folder / filename))


def _unit_binding(unit: Any) -> dict[str, Any]:
    return {
        "entity_id": unit.entity_id,
        "plan": unit.plan.model_dump(mode="json"),
        "resolved_inputs": [r.model_dump(mode="json") for r in unit.resolved_inputs],
        "duration": unit.duration_seconds,
        "resolution": unit.resolution,
        "aspect_ratio": unit.aspect_ratio,
        "provider_params": unit.request.provider_params,
    }


def save_media_execution_plan(**kwargs: Any) -> MediaExecutionPlanResponse:
    prepared = prepare_media_execution(**kwargs)
    assert prepared.plan is not None
    plan = prepared.plan
    # A unique entity avoids concurrent inspectors racing over a shared version counter.
    ref = ArtifactStore(kwargs["project_dir"]).save_artifact(
        "media_execution_plan",
        f"plan-{uuid4().hex}",
        plan.model_dump(mode="json"),
        ArtifactMetadata(
            intent="Inspect selected scene media before execution",
            rationale="Bind normalized provider work to source bytes without provider calls",
            confidence=1,
            source="code",
            producing_module="media_execution_plans",
            lineage=[b.ref for b in plan.source_bindings if b.ref is not None],
        ),
    )
    return MediaExecutionPlanResponse(plan_ref=ref, plan=plan)
