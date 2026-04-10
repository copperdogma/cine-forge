"""Scene readiness router."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter

from cine_forge.api.exceptions import ServiceError
from cine_forge.artifacts import ArtifactStore
from cine_forge.schemas import SceneReadiness
from cine_forge.services.scene_readiness import build_scene_readiness

if TYPE_CHECKING:
    from cine_forge.api.service import OperatorConsoleService

router = APIRouter(prefix="/projects/{project_id}", tags=["readiness"])

_service: OperatorConsoleService | None = None


def set_service(svc: OperatorConsoleService) -> None:
    global _service  # noqa: PLW0603
    _service = svc


def _require_store(project_id: str) -> ArtifactStore:
    if _service is None:
        raise ServiceError(
            code="readiness_router_uninitialized",
            message="Readiness router not initialized.",
            status_code=500,
        )
    project_path = _service.require_project_path(project_id)
    return ArtifactStore(project_dir=project_path)


@router.get("/scenes/{scene_id}/readiness", response_model=SceneReadiness)
async def get_scene_readiness(project_id: str, scene_id: str) -> SceneReadiness:
    store = _require_store(project_id)
    if store.latest_ref("scene", scene_id) is None:
        raise ServiceError(
            code="scene_not_found",
            message=f"Scene '{scene_id}' was not found.",
            status_code=404,
        )
    return build_scene_readiness(store, scene_id)
