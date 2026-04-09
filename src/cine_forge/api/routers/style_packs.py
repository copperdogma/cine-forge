"""Project style-pack library and generation endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool

from cine_forge.api.exceptions import ServiceError
from cine_forge.api.models import (
    StylePackDraftResponse,
    StylePackGenerateRequest,
    StylePackLibraryResponse,
    StylePackManualImportRequest,
    StylePackManualPromptRequest,
    StylePackManualPromptResponse,
    StylePackSaveRequest,
    StylePackSaveResponse,
)

if TYPE_CHECKING:
    from cine_forge.api.service import OperatorConsoleService

router = APIRouter(prefix="/projects/{project_id}/style-packs", tags=["style-packs"])

_service: OperatorConsoleService | None = None


def set_service(svc: OperatorConsoleService) -> None:
    global _service  # noqa: PLW0603
    _service = svc


def _require_service() -> OperatorConsoleService:
    if _service is None:
        raise ServiceError(
            code="style_pack_router_uninitialized",
            message="Style-pack router not initialized.",
            status_code=500,
        )
    return _service


@router.get("", response_model=StylePackLibraryResponse)
async def list_style_packs(project_id: str) -> StylePackLibraryResponse:
    payload = _require_service().list_project_style_pack_library(project_id)
    return StylePackLibraryResponse.model_validate(payload)


@router.post("/generate", response_model=StylePackDraftResponse)
async def generate_style_pack(
    project_id: str,
    request: StylePackGenerateRequest,
) -> StylePackDraftResponse:
    payload = await run_in_threadpool(
        _require_service().generate_style_pack_draft,
        project_id,
        role_id=request.role_id,
        subject=request.subject,
        provider=request.provider,
    )
    return StylePackDraftResponse.model_validate(payload)


@router.post("/manual-prompt", response_model=StylePackManualPromptResponse)
async def build_manual_style_pack_prompt(
    project_id: str,
    request: StylePackManualPromptRequest,
) -> StylePackManualPromptResponse:
    payload = _require_service().build_manual_style_pack_prompt(
        project_id,
        role_id=request.role_id,
        subject=request.subject,
    )
    return StylePackManualPromptResponse.model_validate(payload)


@router.post("/manual-import", response_model=StylePackDraftResponse)
async def import_manual_style_pack_draft(
    project_id: str,
    request: StylePackManualImportRequest,
) -> StylePackDraftResponse:
    payload = _require_service().import_manual_style_pack_draft(
        project_id,
        role_id=request.role_id,
        subject=request.subject,
        raw_output=request.raw_output,
    )
    return StylePackDraftResponse.model_validate(payload)


@router.post("/save", response_model=StylePackSaveResponse)
async def save_style_pack(
    project_id: str,
    request: StylePackSaveRequest,
) -> StylePackSaveResponse:
    payload = _require_service().save_project_style_pack(
        project_id,
        role_id=request.role_id,
        style_pack_id=request.style_pack_id,
        display_name=request.display_name,
        summary=request.summary,
        prompt_injection=request.prompt_injection,
        style_markdown=request.style_markdown,
        additional_files=[item.model_dump(mode="json") for item in request.additional_files],
        assign_to_role=request.assign_to_role,
    )
    return StylePackSaveResponse.model_validate(payload)
