"""Preference-learning router — inspect and clear project-level learned taste signals."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import APIRouter

from cine_forge.api.exceptions import ServiceError
from cine_forge.schemas import PreferenceProfile
from cine_forge.services import PreferenceService

if TYPE_CHECKING:
    from cine_forge.api.service import OperatorConsoleService

router = APIRouter(prefix="/projects/{project_id}/preferences", tags=["preferences"])

_service: OperatorConsoleService | None = None


def set_service(svc: OperatorConsoleService) -> None:
    global _service  # noqa: PLW0603
    _service = svc


def _get_project_path(project_id: str) -> Path:
    if _service is None:
        raise ServiceError(
            code="preferences_router_uninitialized",
            message="Preference router not initialized.",
            status_code=500,
        )
    return _service.require_project_path(project_id)


def _preference_service(project_id: str) -> PreferenceService:
    return PreferenceService(project_dir=_get_project_path(project_id))


@router.get("/profile", response_model=PreferenceProfile)
async def get_preference_profile(project_id: str) -> PreferenceProfile:
    return _preference_service(project_id).build_profile()


@router.post("/clear", response_model=PreferenceProfile)
async def clear_preference_profile(project_id: str) -> PreferenceProfile:
    if _service is None:
        raise ServiceError(
            code="preferences_router_uninitialized",
            message="Preference router not initialized.",
            status_code=500,
        )
    _service.update_project_settings(
        project_id,
        {"preference_learning_cleared_at": datetime.now(UTC).isoformat()},
    )
    return _preference_service(project_id).build_profile()
