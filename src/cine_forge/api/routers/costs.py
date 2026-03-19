"""Cost summary router — run and project cost transparency surfaces."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter

from cine_forge.api.exceptions import ServiceError
from cine_forge.schemas import ProjectCostSummary, RunCostSummary
from cine_forge.services.cost_tracking import CostTrackingService

if TYPE_CHECKING:
    from cine_forge.api.service import OperatorConsoleService

router = APIRouter(tags=["costs"])

_service: OperatorConsoleService | None = None


def set_service(svc: OperatorConsoleService) -> None:
    global _service  # noqa: PLW0603
    _service = svc


def _require_service() -> OperatorConsoleService:
    if _service is None:
        raise ServiceError(
            code="cost_router_uninitialized",
            message="Cost router not initialized.",
            status_code=500,
        )
    return _service


@router.get("/projects/{project_id}/costs", response_model=ProjectCostSummary)
async def get_project_cost_summary(project_id: str) -> ProjectCostSummary:
    service = _require_service()
    project_path = service.require_project_path(project_id)
    return CostTrackingService(service.workspace_root).build_project_summary(
        project_id=project_id,
        project_path=project_path,
    )


@router.get("/runs/{run_id}/costs", response_model=RunCostSummary)
async def get_run_cost_summary(run_id: str) -> RunCostSummary:
    service = _require_service()
    return CostTrackingService(service.workspace_root).build_run_summary(run_id=run_id)
