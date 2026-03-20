"""Headless memory router — transcript search, canonical query, and working-memory control."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import APIRouter

from cine_forge.api.exceptions import ServiceError
from cine_forge.schemas import (
    MemoryQueryRequest,
    MemoryQueryResult,
    MemorySettings,
    MemorySettingsUpdate,
    TranscriptSearchRequest,
    TranscriptSearchResponse,
    WorkingMemoryResetRequest,
    WorkingMemoryResetResponse,
)
from cine_forge.services import MemoryService

if TYPE_CHECKING:
    from cine_forge.api.service import OperatorConsoleService

router = APIRouter(prefix="/projects/{project_id}/memory", tags=["memory"])

_service: OperatorConsoleService | None = None


def set_service(svc: OperatorConsoleService) -> None:
    global _service  # noqa: PLW0603
    _service = svc


def _get_project_path(project_id: str) -> Path:
    if _service is None:
        raise ServiceError(
            code="memory_router_uninitialized",
            message="Memory router not initialized.",
            status_code=500,
        )
    return _service.require_project_path(project_id)


def _memory_service(project_id: str) -> MemoryService:
    return MemoryService(project_dir=_get_project_path(project_id))


@router.get("/settings", response_model=MemorySettings)
async def get_memory_settings(project_id: str) -> MemorySettings:
    return _memory_service(project_id).get_settings()


@router.patch("/settings", response_model=MemorySettings)
async def update_memory_settings(
    project_id: str,
    request: MemorySettingsUpdate,
) -> MemorySettings:
    return _memory_service(project_id).update_settings(request)


@router.post("/search", response_model=TranscriptSearchResponse)
async def search_transcripts(
    project_id: str,
    request: TranscriptSearchRequest,
) -> TranscriptSearchResponse:
    return _memory_service(project_id).search_transcripts(request)


@router.post("/query", response_model=MemoryQueryResult)
async def query_memory(
    project_id: str,
    request: MemoryQueryRequest,
) -> MemoryQueryResult:
    return _memory_service(project_id).query_memory(request)


@router.post("/reset", response_model=WorkingMemoryResetResponse)
async def reset_working_memory(
    project_id: str,
    request: WorkingMemoryResetRequest,
) -> WorkingMemoryResetResponse:
    return _memory_service(project_id).reset_working_memory(request)
