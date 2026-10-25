"""Typed preflight gate applied before any run worker or paid prerequisite starts."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from cine_forge.api.exceptions import ServiceError
from cine_forge.pipeline.media_readiness import recipe_has_media_stage
from cine_forge.schemas.scene_scope import SceneActionPreflight, SceneExecutionScope


def apply_run_start_preflight(
    *,
    project_id: str,
    request: dict[str, Any],
    preview: Callable[..., SceneActionPreflight],
) -> None:
    scope = SceneExecutionScope.model_validate(request.get("scene_scope") or {})
    request["scene_scope"] = scope.model_dump(mode="json")
    if request.get("render_clip_ids") and not (
        scope.mode == "current_scene" and len(scope.scene_ids) == 1
    ):
        raise ServiceError(
            code="render_clip_scope_required",
            message="Render clip regeneration requires a single current scene scope.",
            hint="Select the scene that owns the clip, then regenerate that one render clip.",
            status_code=422,
        )
    recipe_id = str(request.get("recipe_id") or "mvp_ingest")
    end_at = request.get("end_at")
    if not scope.is_scene_scoped and not recipe_has_media_stage(
        recipe_id,
        request.get("start_from"),
        end_at,
    ):
        return
    preflight = preview(
        project_id,
        recipe_id=recipe_id,
        scene_scope=scope,
        start_from=request.get("start_from"),
        end_at=end_at,
    )
    if preflight.status == "soft_block":
        blocker = next((item for item in preflight.items if item.kind == "soft_block"), None)
        raise ServiceError(
            code="scene_action_blocked",
            message=preflight.summary or "Scene action is blocked.",
            hint=blocker.detail if blocker else None,
            status_code=422,
        )
    if preflight.start_from:
        request["start_from"] = preflight.start_from
    else:
        request.pop("start_from", None)
    if preflight.end_at:
        request["end_at"] = preflight.end_at
    else:
        request.pop("end_at", None)
    request["scene_action_preflight"] = preflight.model_dump(mode="json")


def require_confirmed_media_preflight(
    *,
    project_id: str,
    request: dict[str, Any],
    preview: Callable[..., SceneActionPreflight],
) -> None:
    """Retain readiness guards without rewriting the approved slice or parameters."""
    scope = SceneExecutionScope.model_validate(request["scene_scope"])
    result = preview(
        project_id,
        recipe_id=request["recipe_id"],
        scene_scope=scope,
        start_from=request["start_from"],
        end_at=request["end_at"],
    )
    if result.status == "soft_block":
        blocker = next((item for item in result.items if item.kind == "soft_block"), None)
        raise ServiceError(
            code="scene_action_blocked",
            message=result.summary,
            hint=blocker.detail if blocker else None,
            status_code=422,
        )
    if result.start_from != request["start_from"] or result.end_at != request["end_at"]:
        raise ServiceError(
            code="media_execution_plan_conflict",
            message="Preparation changed; inspect again before executing media.",
            status_code=409,
        )
