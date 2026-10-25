"""Validation consumes only outputs persisted by the approved generation stage."""

from __future__ import annotations

from typing import Any

from cine_forge.artifacts import ArtifactStore
from cine_forge.driver.recipe import RecipeStage
from cine_forge.schemas import ArtifactRef
from cine_forge.schemas.media_execution_plan import MediaExecutionPlan


def approved_validation_inputs(
    *,
    store: ArtifactStore,
    stage: RecipeStage,
    stage_outputs: dict[str, list[dict[str, Any]]],
    runtime_params: dict[str, Any],
) -> tuple[dict[str, Any], list[ArtifactRef]]:
    """Never fall back to old or unselected project media when this run has no output."""
    ref = ArtifactRef.model_validate(runtime_params["media_execution_plan_ref"])
    plan = MediaExecutionPlan.model_validate(store.load_artifact(ref).data)
    generation_stage = "render" if plan.recipe_id == "render_generation" else "ai_previz"
    video_type = stage.params.get("target_artifact_type") or "generated_video"
    outputs = [
        output
        for output in stage_outputs.get(generation_stage, [])
        if output["ref"].artifact_type == video_type
    ]
    expected = {unit.entity_id for unit in plan.units}
    actual = [output["ref"].entity_id for output in outputs]
    if len(actual) != len(expected) or set(actual) != expected:
        raise ValueError("Approved validation requires exactly this run's selected media outputs")
    # These refs/data are the artifact persister's returned versions, not latest-store queries.
    return {"generated_video": [output["data"] for output in outputs]}, [
        output["ref"] for output in outputs
    ]
