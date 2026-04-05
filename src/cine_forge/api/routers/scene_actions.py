"""Scene-action preflight router."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter

from cine_forge.api.exceptions import ServiceError
from cine_forge.api.models import SceneActionPreflightRequest, SceneActionPreflightResponse

if TYPE_CHECKING:
    from cine_forge.api.service import OperatorConsoleService

router = APIRouter(prefix="/projects/{project_id}/scene-actions", tags=["scene-actions"])

_service: OperatorConsoleService | None = None


def set_service(svc: OperatorConsoleService) -> None:
    global _service  # noqa: PLW0603
    _service = svc


def _require_service() -> OperatorConsoleService:
    if _service is None:
        raise ServiceError(
            code="scene_actions_router_uninitialized",
            message="Scene actions router not initialized.",
            status_code=500,
        )
    return _service


@router.post("/preflight", response_model=SceneActionPreflightResponse)
async def preview_scene_action(
    project_id: str,
    request: SceneActionPreflightRequest,
) -> SceneActionPreflightResponse:
    service = _require_service()
    preflight = service.preview_scene_action(
        project_id,
        recipe_id=request.recipe_id,
        scene_scope=request.scene_scope,
        start_from=request.start_from,
        end_at=request.end_at,
    )
    return SceneActionPreflightResponse.model_validate(preflight.model_dump(mode="json"))
