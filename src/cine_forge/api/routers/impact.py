"""Impact assessment router — semantic change propagation actions."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter

from cine_forge.api.exceptions import ServiceError
from cine_forge.api.models import (
    ArtifactHealthOverrideRequest,
    ArtifactHealthOverrideResponse,
    ImpactAssessmentRequest,
    ImpactAssessmentResponse,
    ImpactPreviewRequest,
    ImpactPreviewResponse,
)
from cine_forge.schemas import ArtifactHealth

if TYPE_CHECKING:
    from cine_forge.api.service import OperatorConsoleService

router = APIRouter(prefix="/projects/{project_id}/impact", tags=["impact"])

_service: OperatorConsoleService | None = None


def set_service(svc: OperatorConsoleService) -> None:
    global _service  # noqa: PLW0603
    _service = svc


def _require_service() -> OperatorConsoleService:
    if _service is None:
        raise ServiceError(
            code="impact_router_uninitialized",
            message="Impact router not initialized.",
            status_code=500,
        )
    return _service


@router.post("/preview", response_model=ImpactPreviewResponse)
async def preview_impact_scope(
    project_id: str,
    body: ImpactPreviewRequest,
) -> ImpactPreviewResponse:
    service = _require_service()
    return ImpactPreviewResponse.model_validate(
        service.preview_impact_scope(
            project_id,
            body.artifact_ref,
            selected_refs=body.selected_artifact_refs,
            model=body.model,
            budget_cap_usd=body.budget_cap_usd,
        )
    )


@router.post("/assess", response_model=ImpactAssessmentResponse)
async def run_impact_assessment(
    project_id: str,
    body: ImpactAssessmentRequest,
) -> ImpactAssessmentResponse:
    service = _require_service()
    return ImpactAssessmentResponse.model_validate(
        service.run_impact_assessment(
            project_id,
            body.artifact_ref,
            selected_refs=body.selected_artifact_refs,
            model=body.model,
            role_id=body.role_id,
            budget_cap_usd=body.budget_cap_usd,
        )
    )


@router.post("/override", response_model=ArtifactHealthOverrideResponse)
async def override_artifact_health(
    project_id: str,
    body: ArtifactHealthOverrideRequest,
) -> ArtifactHealthOverrideResponse:
    service = _require_service()
    return ArtifactHealthOverrideResponse.model_validate(
        service.override_artifact_health(
            project_id,
            body.artifact_ref,
            target_health=ArtifactHealth(body.target_health),
            rationale=body.rationale,
            decided_by=body.decided_by,
        )
    )
