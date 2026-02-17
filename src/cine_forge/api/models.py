"""Pydantic models for CineForge API."""

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


class InputFileSummary(BaseModel):
    """Metadata for a project input file."""

    filename: str
    original_name: str
    size_bytes: int = Field(ge=0)
    stored_path: str = ""


class ProjectSummary(BaseModel):
    """Project snapshot for list/open/new responses."""

    project_id: str
    display_name: str
    artifact_groups: int = Field(ge=0)
    run_count: int = Field(ge=0)
    has_inputs: bool = False
    input_files: list[str] = []


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
    work_model: str | None = None
    verify_model: str | None = None
    escalate_model: str | None = None
    qa_model: str | None = None
    recipe_id: str | None = "mvp_ingest"
    accept_config: bool = False
    config_file: str | None = None
    config_overrides: dict[str, Any] | None = None
    run_id: str | None = None
    force: bool = False
    start_from: str | None = None
    skip_qa: bool = False


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
    bible_files: dict[str, Any] | None = None


class ArtifactEditRequest(BaseModel):
    """Request payload for editing an artifact (creating a new version)."""

    data: dict[str, Any] = Field(min_length=1)
    rationale: str = Field(min_length=1)


class ArtifactEditResponse(BaseModel):
    """Response payload for artifact edit operation."""

    artifact_type: str
    entity_id: str | None = None
    version: int = Field(ge=1)
    path: str


class RecipeSummary(BaseModel):
    """Recipe metadata for recipe listing endpoint."""

    recipe_id: str
    name: str
    description: str
    stage_count: int = Field(ge=0)


class SlugPreviewRequest(BaseModel):
    """Request to generate a project slug from screenplay content."""

    content_snippet: str = Field(min_length=1)
    original_filename: str = Field(min_length=1)


class SlugPreviewResponse(BaseModel):
    """LLM-generated project name and slug."""

    slug: str
    display_name: str
    alternatives: list[str] = []


class ProjectCreateRequest(BaseModel):
    """Create a project using a slug and display name."""

    slug: str = Field(min_length=1, pattern=r"^[a-z0-9][a-z0-9-]*$")
    display_name: str = Field(min_length=1)


class ProjectSettingsUpdate(BaseModel):
    """Partial update for project settings (display name, etc.)."""

    display_name: str | None = None


class ChatMessagePayload(BaseModel):
    """A single chat message for the project journal."""

    id: str = Field(min_length=1)
    type: str = Field(min_length=1)
    content: str
    timestamp: float
    actions: list[dict[str, Any]] | None = None
    needsAction: bool | None = None


class ChatStreamRequest(BaseModel):
    """Request payload for the streaming chat endpoint."""

    message: str = Field(min_length=1)
    chat_history: list[dict[str, Any]] = []
    page_context: str | None = None


class InsightRequest(BaseModel):
    """Request payload for auto-generated AI insights."""

    trigger: str = Field(min_length=1)
    context: dict[str, Any] = {}
