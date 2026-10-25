"""Inspect current-scene media work without executing provider calls."""

from fastapi import APIRouter, Request

from cine_forge.api.exceptions import ServiceError
from cine_forge.schemas.media_execution_plan import (
    MediaExecutionPlanRequest,
    MediaExecutionPlanResponse,
)
from cine_forge.services.media_execution_plans import save_media_execution_plan

router = APIRouter(tags=["media-execution-plans"])


@router.post(
    "/projects/{project_id}/media-execution-plans", response_model=MediaExecutionPlanResponse
)
def create_media_execution_plan(
    project_id: str, body: MediaExecutionPlanRequest, request: Request
) -> MediaExecutionPlanResponse:
    service = request.app.state.console_service
    try:
        return save_media_execution_plan(
            workspace_root=service.workspace_root,
            project_dir=service.require_project_path(project_id),
            project_id=project_id,
            request=body,
        )
    except (ValueError, OSError) as exc:
        raise ServiceError(
            code="media_inspection_failed", message=str(exc), status_code=422
        ) from exc
