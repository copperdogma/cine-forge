"""Previz adoption/default status router."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter

from cine_forge.api.exceptions import ServiceError
from cine_forge.schemas import PrevizAdoptionStatus
from cine_forge.services.previz_adoption import PrevizAdoptionService

if TYPE_CHECKING:
    from cine_forge.api.service import OperatorConsoleService

router = APIRouter(prefix="/projects/{project_id}/previz", tags=["previz"])

_service: OperatorConsoleService | None = None


def set_service(svc: OperatorConsoleService) -> None:
    global _service  # noqa: PLW0603
    _service = svc


def _require_service() -> OperatorConsoleService:
    if _service is None:
        raise ServiceError(
            code="previz_router_uninitialized",
            message="Previz router not initialized.",
            status_code=500,
        )
    return _service


@router.get("/adoption", response_model=PrevizAdoptionStatus)
async def get_previz_adoption_status(project_id: str) -> PrevizAdoptionStatus:
    service = _require_service()
    project_path = service.require_project_path(project_id)
    return PrevizAdoptionService().build_status(project_path=project_path)
