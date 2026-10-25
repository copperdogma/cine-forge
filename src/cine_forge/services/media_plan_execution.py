"""Approval validation, one-use claims, and execution from captured source inputs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from cine_forge.api.exceptions import ServiceError
from cine_forge.artifacts import ArtifactStore
from cine_forge.driver.recipe import load_recipe, resolve_runtime_params
from cine_forge.schemas import ArtifactRef
from cine_forge.schemas.media_execution_plan import MediaExecutionPlan, MediaExecutionPlanRequest
from cine_forge.services.media_execution_plans import prepare_media_execution
from cine_forge.services.media_plan_sources import safe_path


def load_plan(project_dir: Path, project_id: str, ref: ArtifactRef) -> MediaExecutionPlan:
    safe_path(project_dir, ref.path)
    if ref.artifact_type != "media_execution_plan":
        raise ValueError("Confirmation requires a media_execution_plan artifact")
    artifact = ArtifactStore(project_dir).load_artifact(ref)
    if artifact.metadata.ref != ref:
        raise ValueError("Media plan reference does not match its stored artifact")
    plan = MediaExecutionPlan.model_validate(artifact.data)
    if plan.project_id != project_id:
        raise ValueError("Media execution plan belongs to another project")
    if plan.status != "ready":
        raise ValueError("Media execution plan is blocked: " + "; ".join(plan.blockers))
    return plan


def checked_execution(
    *,
    workspace_root: Path,
    project_dir: Path,
    project_id: str,
    ref: ArtifactRef,
    actual_inputs: dict[str, Any] | None = None,
) -> Any:
    plan = load_plan(project_dir, project_id, ref)
    prepared = prepare_media_execution(
        workspace_root=workspace_root,
        project_dir=project_dir,
        project_id=project_id,
        request=MediaExecutionPlanRequest(
            recipe_id=plan.recipe_id, scene_id=plan.scene_id, render_clip_ids=plan.render_clip_ids
        ),
        actual_inputs=actual_inputs,
    )
    if prepared.plan.binding_sha256 != plan.binding_sha256:
        raise ValueError("Media execution plan is stale. Inspect the selected scene again.")
    return prepared


def confirm_media_request(
    *, workspace_root: Path, project_dir: Path, project_id: str, request: dict[str, Any]
) -> dict[str, Any]:
    try:
        if set(request) - {"project_id", "media_execution_plan_ref"}:
            raise ValueError(
                "A media plan confirmation accepts only project_id and media_execution_plan_ref"
            )
        ref = ArtifactRef.model_validate(request["media_execution_plan_ref"])
        prepared = checked_execution(
            workspace_root=workspace_root, project_dir=project_dir, project_id=project_id, ref=ref
        )
        return {**prepared.request, "media_execution_plan_ref": ref.model_dump(mode="json")}
    except (ValueError, OSError, KeyError) as exc:
        raise ServiceError(
            code="media_execution_plan_conflict",
            message=str(exc),
            hint="Inspect the selected scene again before confirming.",
            status_code=409,
        ) from exc


def claim_media_plan(project_dir: Path, ref: ArtifactRef, run_id: str) -> None:
    """Atomically prevent two workers from executing the same approval."""
    folder = project_dir / "media_plan_claims"
    folder.mkdir(exist_ok=True)
    from cine_forge.services.media_plan_sources import digest

    path = folder / f"{digest(ref.model_dump(mode='json'))}.json"
    try:
        with path.open("x", encoding="utf-8") as handle:
            json.dump({"run_id": run_id, "plan_ref": ref.model_dump(mode="json")}, handle)
    except FileExistsError as exc:
        raise ServiceError(
            code="media_execution_plan_already_used",
            message="This media execution plan has already been confirmed.",
            hint="Inspect again only after checking the existing run and any unresolved cost.",
            status_code=409,
        ) from exc


def consume_media_plan(project_dir: Path, ref: ArtifactRef, run_id: str) -> None:
    """Consume the worker boundary once, including direct driver/headless execution."""
    from cine_forge.services.media_plan_sources import digest

    key = digest(ref.model_dump(mode="json"))
    folder = project_dir / "media_plan_claims"
    claim = folder / f"{key}.json"
    if not claim.exists():
        claim_media_plan(project_dir, ref, run_id)
    if json.loads(claim.read_text())["run_id"] != run_id:
        raise ValueError("Media plan is already claimed by another run")
    try:
        with (folder / f"{key}.started").open("x") as handle:
            handle.write(run_id)
    except FileExistsError as exc:
        raise ValueError(
            "Media plan has already started; inspect again after checking its run"
        ) from exc


def validate_media_run_envelope(
    *,
    workspace_root: Path,
    project_dir: Path,
    recipe_path: Path,
    runtime_params: dict[str, Any],
    start_from: str | None,
    end_at: str | None,
    run_id: str,
    consume: bool = True,
) -> dict[str, Any]:
    """Driver boundary: an approval can never turn into paid prerequisite execution."""
    if not runtime_params.get("media_execution_plan_ref"):
        return runtime_params
    ref = ArtifactRef.model_validate(runtime_params["media_execution_plan_ref"])
    safe_path(project_dir, ref.path)
    artifact = ArtifactStore(project_dir).load_artifact(ref)
    plan = MediaExecutionPlan.model_validate(artifact.data)
    prepared = checked_execution(
        workspace_root=workspace_root, project_dir=project_dir, project_id=plan.project_id, ref=ref
    )
    actual = {
        k: v
        for k, v in runtime_params.items()
        if k not in {"media_execution_plan_ref", "__media_plan_workspace_root"}
    }
    recipe = resolve_runtime_params(load_recipe(recipe_path), actual)
    if (
        actual != prepared.runtime
        or recipe != prepared.recipe
        or start_from != prepared.stage.id
        or end_at != prepared.request["end_at"]
    ):
        raise ValueError("Approved media scope, recipe, or runtime parameters changed")
    if consume:
        consume_media_plan(project_dir, ref, run_id)
    return {**runtime_params, "__media_plan_workspace_root": str(workspace_root)}


def execute_approved_media(
    *, inputs: dict[str, Any], params: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    from cine_forge.execution_errors import ModuleCostError
    from cine_forge.modules.generation.render_adapter_v1.execution import execute_render
    from cine_forge.modules.generation.render_adapter_v1.source_inputs import _track_manifest

    runtime = context["runtime_params"]
    project_dir = Path(context["project_dir"])
    root = Path(runtime.get("__media_plan_workspace_root") or Path(__file__).resolve().parents[3])
    ref = ArtifactRef.model_validate(runtime["media_execution_plan_ref"])
    safe_path(project_dir, ref.path)
    artifact = ArtifactStore(project_dir).load_artifact(ref)
    plan = MediaExecutionPlan.model_validate(artifact.data)
    prepared = checked_execution(
        workspace_root=root,
        project_dir=project_dir,
        project_id=plan.project_id,
        ref=ref,
        actual_inputs=inputs,
    )
    actual_runtime = {
        k: v
        for k, v in runtime.items()
        if k not in {"media_execution_plan_ref", "__media_plan_workspace_root"}
    }
    if params != prepared.params or actual_runtime != prepared.runtime:
        raise ValueError("Actual media parameters differ from the inspected plan")
    from cine_forge.ai.video_pricing import validate_video_target
    from cine_forge.modules.generation.render_adapter_v1.orchestration import ensure_backfill_ready
    from cine_forge.modules.generation.render_adapter_v1.source_inputs import (
        _default_design_study_backfill_enabled,
    )
    from cine_forge.services.design_study_backfill import DefaultDesignStudyBackfillService

    validate_video_target(
        provider=prepared.engine_pack.provider, model=prepared.engine_pack.target_model
    )
    if _default_design_study_backfill_enabled(
        params=prepared.params, runtime_params=prepared.runtime
    ):
        ensure_backfill_ready(
            store=prepared.store, scenes=prepared.scenes, image_model=prepared.backfill_model
        )
        backfill = DefaultDesignStudyBackfillService(
            project_dir, image_model=prepared.backfill_model
        )
        if any(backfill.generation_required(scene) for scene in prepared.scenes):
            raise ValueError("Approved execution cannot generate new reference images")
    prepared.store.verify_files()
    receipts: list[Any] = []
    try:
        # Reuse captured maps/scenes/normalized requests. No latest-source lookup or backfill.
        return execute_render(
            store=prepared.store,
            scenes=prepared.scenes,
            shot_plans=prepared.plans,
            track_manifest=_track_manifest(prepared.inputs),
            source_maps=prepared.source_maps,
            engine_pack=prepared.engine_pack,
            compiler_model=prepared.compiler_model,
            requested_duration_seconds=8,
            requested_resolution=None,
            requested_aspect_ratio=None,
            output_contract=prepared.contract,
            scene_action_preflight=None,
            selected_render_clip_ids=set(plan.render_clip_ids) if plan.render_clip_ids else None,
            default_design_study_backfill=False,
            default_design_study_backfill_model=prepared.backfill_model,
            announce_artifact=context.get("announce_artifact"),
            cost_receipts=receipts,
            prepared_units=prepared.units,
        )
    except ModuleCostError:
        raise
    except Exception as exc:
        if receipts:
            raise ModuleCostError(str(exc), cost_receipts=receipts) from exc
        raise
