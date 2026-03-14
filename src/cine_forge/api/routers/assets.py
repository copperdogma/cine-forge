"""Injected asset router — upload, browse, and negotiate asset locks."""

from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Literal

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from cine_forge.api.exceptions import ServiceError
from cine_forge.schemas import AssetLockStatus, AssetTargetKind, InjectedAssetManifest
from cine_forge.services import InjectedAssetError, InjectedAssetService

if TYPE_CHECKING:
    from cine_forge.api.service import OperatorConsoleService

router = APIRouter(prefix="/projects/{project_id}/assets", tags=["assets"])
UPLOAD_FILE_PARAM = File(...)

_service: OperatorConsoleService | None = None


def set_service(svc: OperatorConsoleService) -> None:
    global _service  # noqa: PLW0603
    _service = svc


def _get_project_path(project_id: str) -> Path:
    if _service is None:
        raise ServiceError(
            code="asset_router_uninitialized",
            message="Asset router not initialized.",
            status_code=500,
        )
    return _service.require_project_path(project_id)


def _asset_service(project_id: str) -> InjectedAssetService:
    return InjectedAssetService(project_dir=_get_project_path(project_id))


class LockUpdateRequest(BaseModel):
    lock_status: AssetLockStatus
    rationale: str = Field(default="Operator updated the asset lock.")


class LockProposalRequest(BaseModel):
    source_role: str = Field(min_length=1)
    proposed_lock_status: AssetLockStatus
    rationale: str = Field(min_length=1)
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)


class LockProposalResponseRequest(BaseModel):
    decision: Literal["accept", "reject"]
    decided_by: str = Field(default="human", min_length=1)
    reason: str = Field(min_length=1)


@router.post("/inject", response_model=InjectedAssetManifest)
async def inject_asset(
    project_id: str,
    target_kind: Annotated[AssetTargetKind, Form(...)],
    target_id: Annotated[str, Form(...)],
    purpose: Annotated[str, Form(...)],
    lock_status: Annotated[AssetLockStatus, Form()] = "soft_locked",
    file: UploadFile = UPLOAD_FILE_PARAM,
) -> InjectedAssetManifest:
    if not file.filename:
        raise ServiceError(
            code="missing_filename",
            message="Uploaded file must include a filename.",
            status_code=422,
        )
    content = await file.read()
    try:
        return _asset_service(project_id).inject_asset(
            target_kind=target_kind,
            target_id=target_id,
            purpose=purpose,
            filename=file.filename,
            content=content,
            lock_status=lock_status,
            content_type=file.content_type or mimetypes.guess_type(file.filename)[0],
        )
    except InjectedAssetError as exc:
        raise ServiceError(
            code="asset_injection_failed",
            message=str(exc),
            status_code=422,
        ) from exc


@router.get("/{target_kind}/{target_id}", response_model=InjectedAssetManifest)
async def get_assets(
    project_id: str, target_kind: AssetTargetKind, target_id: str
) -> InjectedAssetManifest:
    return _asset_service(project_id).get_manifest(
        target_kind=target_kind,
        target_id=target_id,
    )


@router.get("/file/{relative_path:path}")
async def get_asset_file(project_id: str, relative_path: str) -> FileResponse:
    project_path = _get_project_path(project_id)
    file_path = (project_path / relative_path).resolve()
    if not file_path.is_relative_to(project_path.resolve()):
        raise ServiceError(
            code="invalid_asset_path",
            message="Asset path escapes the project directory.",
            status_code=400,
        )
    if not file_path.exists():
        raise ServiceError(
            code="asset_file_not_found",
            message=f"Asset file '{relative_path}' does not exist.",
            status_code=404,
        )
    media_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    return FileResponse(path=str(file_path), media_type=media_type)


@router.post("/{target_kind}/{target_id}/{asset_id}/lock", response_model=InjectedAssetManifest)
async def update_asset_lock(
    project_id: str,
    target_kind: AssetTargetKind,
    target_id: str,
    asset_id: str,
    body: LockUpdateRequest,
) -> InjectedAssetManifest:
    try:
        return _asset_service(project_id).update_lock_status(
            target_kind=target_kind,
            target_id=target_id,
            asset_id=asset_id,
            lock_status=body.lock_status,
            rationale=body.rationale,
        )
    except InjectedAssetError as exc:
        raise ServiceError(
            code="asset_lock_update_failed",
            message=str(exc),
            status_code=422,
        ) from exc


@router.post("/{target_kind}/{target_id}/{asset_id}/propose-lock-change")
async def propose_lock_change(
    project_id: str,
    target_kind: AssetTargetKind,
    target_id: str,
    asset_id: str,
    body: LockProposalRequest,
) -> dict[str, str]:
    try:
        suggestion = _asset_service(project_id).create_lock_change_proposal(
            target_kind=target_kind,
            target_id=target_id,
            asset_id=asset_id,
            proposed_lock_status=body.proposed_lock_status,
            source_role=body.source_role,
            rationale=body.rationale,
            confidence=body.confidence,
        )
    except InjectedAssetError as exc:
        raise ServiceError(
            code="asset_lock_proposal_failed",
            message=str(exc),
            status_code=422,
        ) from exc
    return {"suggestion_id": suggestion.suggestion_id}


@router.post("/lock-proposals/{suggestion_id}/respond")
async def respond_to_lock_proposal(
    project_id: str,
    suggestion_id: str,
    body: LockProposalResponseRequest,
) -> dict[str, str]:
    try:
        manifest = _asset_service(project_id).respond_to_lock_change_proposal(
            suggestion_id=suggestion_id,
            decision=body.decision,
            decided_by=body.decided_by,
            reason=body.reason,
        )
    except InjectedAssetError as exc:
        raise ServiceError(
            code="asset_lock_response_failed",
            message=str(exc),
            status_code=422,
        ) from exc
    return {
        "suggestion_id": suggestion_id,
        "decision": body.decision,
        "target_version": str(manifest.version) if manifest is not None else "",
    }
