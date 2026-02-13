"""Pydantic models for Operator Console Lite API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ErrorPayload(BaseModel):
    """Structured API error envelope."""

    code: str
    message: str
    hint: str | None = None


class ProjectPathRequest(BaseModel):
    """Request envelope that targets a project path."""

    project_path: str = Field(min_length=1)


class ProjectSummary(BaseModel):
    """Project snapshot for list/open/new responses."""

    project_id: str
    display_name: str
    artifact_groups: int = Field(ge=0)
    run_count: int = Field(ge=0)


class RecentProjectSummary(ProjectSummary):
    """Project summary plus filesystem path for sidebar listing."""

    project_path: str


class RunSummary(BaseModel):
    """Thin run metadata from run_state.json."""

    run_id: str
    status: str
    started_at: float | None = None
    finished_at: float | None = None


class ArtifactGroupSummary(BaseModel):
    """Latest version summary for one artifact type/entity group."""

    artifact_type: str
    entity_id: str | None = None
    latest_version: int = Field(ge=1)
    health: str | None = None


class ArtifactVersionSummary(BaseModel):
    """Version-level summary for one artifact group."""

    artifact_type: str
    entity_id: str | None = None
    version: int = Field(ge=1)
    health: str | None = None
    path: str
    created_at: str | None = None
    intent: str | None = None
    producing_module: str | None = None


class RunStartRequest(BaseModel):
    """Start-run request from GUI runtime form."""

    project_id: str = Field(min_length=1)
    input_file: str = Field(min_length=1)
    default_model: str = Field(min_length=1)
    qa_model: str | None = None
    accept_config: bool = False
    config_file: str | None = None
    config_overrides: dict[str, Any] | None = None
    run_id: str | None = None
    force: bool = False


class RunStartResponse(BaseModel):
    """Run start acknowledgment."""

    run_id: str
    state_url: str
    events_url: str


class UploadedInputResponse(BaseModel):
    """Response payload for uploaded script/story input files."""

    original_name: str
    stored_path: str
    size_bytes: int = Field(ge=0)


class RunStateResponse(BaseModel):
    """Run state payload wrapper."""

    run_id: str
    state: dict[str, Any]
    background_error: str | None = None


class RunEventsResponse(BaseModel):
    """Chronological run event list."""

    run_id: str
    events: list[dict[str, Any]]


class ArtifactDetailResponse(BaseModel):
    """Raw artifact payload view."""

    artifact_type: str
    entity_id: str | None = None
    version: int = Field(ge=1)
    payload: dict[str, Any]
