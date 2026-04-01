"""Pydantic models for CineForge API."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from cine_forge.schemas import ArtifactRef, CostRecord, ImpactAssessment
from cine_forge.schemas.models import ProductionFormat


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
    ui_preferences: dict[str, Any] = Field(default_factory=dict)
    human_control_mode: str = "autonomous"
    production_format: ProductionFormat | None = None
    interaction_mode: str = "balanced"
    default_model: str | None = None
    work_model: str | None = None
    verify_model: str | None = None
    escalate_model: str | None = None
    project_budget_limit_usd: float | None = Field(default=None, ge=0.0)
    default_run_budget_limit_usd: float | None = Field(default=None, ge=0.0)
    budget_warning_threshold_ratio: float = Field(default=0.8, ge=0.0, le=1.0)
    preference_learning_enabled: bool = True
    preference_learning_cleared_at: str | None = None


class RecentProjectSummary(ProjectSummary):
    """Project summary plus filesystem path for sidebar listing."""

    project_path: str
    last_modified: float | None = None


class RunSummary(BaseModel):
    """Thin run metadata from run_state.json."""

    run_id: str
    status: str
    recipe_id: str = "mvp_ingest"
    started_at: float | None = None
    finished_at: float | None = None
    total_cost_usd: float = Field(default=0.0, ge=0.0)


class ArtifactHealthDetailsResponse(BaseModel):
    """Live graph health details plus provenance for one artifact."""

    health: str
    source_kind: str | None = None
    reason: str | None = None
    trigger_ref: ArtifactRef | None = None
    source_artifact_ref: ArtifactRef | None = None
    upstream_change_summary: str | None = None
    suggested_revision: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    assessing_role: str | None = None
    decided_by: str | None = None
    updated_at: str | None = None


class ArtifactGroupSummary(BaseModel):
    """Latest version summary for one artifact type/entity group."""

    artifact_type: str
    entity_id: str | None = None
    latest_version: int = Field(ge=1)
    health: str | None = None
    health_details: ArtifactHealthDetailsResponse | None = None


class ArtifactVersionSummary(BaseModel):
    """Version-level summary for one artifact group."""

    artifact_type: str
    entity_id: str | None = None
    version: int = Field(ge=1)
    health: str | None = None
    health_details: ArtifactHealthDetailsResponse | None = None
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
    human_control_mode: Literal["autonomous", "checkpoint", "advisory"] | None = None
    accept_config: bool = False
    config_file: str | None = None
    config_overrides: dict[str, Any] | None = None
    run_id: str | None = None
    force: bool = False
    start_from: str | None = None
    end_at: str | None = None
    skip_qa: bool = False
    project_budget_limit_usd: float | None = Field(default=None, ge=0.0)
    run_budget_limit_usd: float | None = Field(default=None, ge=0.0)
    budget_warning_threshold_ratio: float | None = Field(default=None, ge=0.0, le=1.0)
    retry_failed_stage_for_run_id: str | None = None


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
    health: str | None = None
    health_details: ArtifactHealthDetailsResponse | None = None
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


class ImpactPreviewTargetResponse(BaseModel):
    """One stale artifact included in an impact preview."""

    artifact_ref: ArtifactRef
    artifact_type: str
    entity_id: str | None = None
    current_health: str


class ImpactPreviewRequest(BaseModel):
    """Request payload for previewing semantic impact scope."""

    artifact_ref: ArtifactRef
    selected_artifact_refs: list[ArtifactRef] | None = None
    model: str | None = None
    budget_cap_usd: float | None = Field(default=None, ge=0.0)


class ImpactPreviewResponse(BaseModel):
    """Scope preview for a semantic impact assessment run."""

    trigger_artifact_ref: ArtifactRef
    requested_artifact_ref: ArtifactRef
    total_stale: int = Field(ge=0)
    affected_types: list[str] = Field(default_factory=list)
    estimated_cost: CostRecord
    budget_cap_usd: float | None = Field(default=None, ge=0.0)
    within_budget: bool = True
    targets: list[ImpactPreviewTargetResponse] = Field(default_factory=list)


class ImpactAssessmentRequest(BaseModel):
    """Request payload for running semantic impact assessment."""

    artifact_ref: ArtifactRef
    selected_artifact_refs: list[ArtifactRef] | None = None
    model: str | None = None
    role_id: str | None = None
    budget_cap_usd: float | None = Field(default=None, ge=0.0)


class ImpactAssessmentResponse(BaseModel):
    """Assessment artifact and payload returned to the UI."""

    assessment_ref: ArtifactRef
    assessment: ImpactAssessment


class ArtifactHealthOverrideRequest(BaseModel):
    """Manual resolution of a live artifact health state."""

    artifact_ref: ArtifactRef
    target_health: Literal["valid", "needs_revision", "confirmed_valid"]
    rationale: str = Field(min_length=1)
    decided_by: str = Field(default="human", min_length=1)


class ArtifactHealthOverrideResponse(BaseModel):
    """Result payload after a manual health override."""

    decision_ref: ArtifactRef
    artifact_ref: ArtifactRef
    health: str
    health_details: ArtifactHealthDetailsResponse | None = None


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
    """Create a project using a slug and display name, or an explicit path."""

    slug: str | None = None
    display_name: str | None = None
    project_path: str | None = None


class ProjectSettingsUpdate(BaseModel):
    """Partial update for project settings (display name, etc.)."""

    display_name: str | None = None
    human_control_mode: Literal["autonomous", "checkpoint", "advisory"] | None = None
    production_format: ProductionFormat | None = None
    interaction_mode: Literal["guided", "balanced", "expert"] | None = None
    default_model: str | None = None
    work_model: str | None = None
    verify_model: str | None = None
    escalate_model: str | None = None
    project_budget_limit_usd: float | None = Field(default=None, ge=0.0)
    default_run_budget_limit_usd: float | None = Field(default=None, ge=0.0)
    budget_warning_threshold_ratio: float | None = Field(default=None, ge=0.0, le=1.0)
    preference_learning_enabled: bool | None = None
    preference_learning_cleared_at: str | None = None
    style_packs: dict[str, str] | None = None
    ui_preferences: dict[str, Any] | None = None


class ResumeRunRequest(BaseModel):
    """Optional per-run budget override when resuming a paused run."""

    run_budget_limit_usd: float | None = Field(default=None, ge=0.0)


class ChatMessagePayload(BaseModel):
    """A single chat message for the project journal."""

    id: str = Field(min_length=1)
    type: str = Field(min_length=1)
    content: str
    timestamp: float
    speaker: str | None = None
    model: str | None = None
    actions: list[dict[str, Any]] | None = None
    needsAction: bool | None = None
    route: str | None = None
    pageContext: str | None = None
    toolCalls: list[dict[str, Any]] | None = None
    injectedContent: str | None = None
    relatedArtifacts: list[ArtifactRef] | None = None
    decisionIds: list[str] | None = None
    suggestionIds: list[str] | None = None


# --- Search ---


class SearchResultScene(BaseModel):
    """Scene match in search results."""

    scene_id: str
    scene_number: int = 0
    heading: str
    location: str
    time_of_day: str
    int_ext: str


class SearchResultEntity(BaseModel):
    """Bible entity match in search results."""

    entity_id: str
    display_name: str
    entity_type: str  # character, location, prop
    artifact_type: str  # character_bible, location_bible, prop_bible


class SearchResponse(BaseModel):
    """Unified search results across project entities."""

    query: str
    scenes: list[SearchResultScene] = []
    characters: list[SearchResultEntity] = []
    locations: list[SearchResultEntity] = []
    props: list[SearchResultEntity] = []


# --- Streaming Chat ---


class ChatStreamRequest(BaseModel):
    """Request payload for the streaming chat endpoint."""

    message: str = Field(min_length=1)
    chat_history: list[dict[str, Any]] = []
    page_context: str | None = None
    active_role: str | None = None


class InsightRequest(BaseModel):
    """Request payload for auto-generated AI insights."""

    trigger: str = Field(min_length=1)
    context: dict[str, Any] = {}


# --- Intent / Mood ---


class IntentMoodInput(BaseModel):
    """Request payload for saving intent/mood."""

    mood_descriptors: list[str] = []
    reference_films: list[str] = []
    filmmaker_anchors: list[str] = []
    style_preset_id: str | None = None
    natural_language_intent: str | None = None
    look_notes: str | None = None
    scope: str = "project"
    scene_id: str | None = None


class IntentMoodResponse(BaseModel):
    """Saved intent/mood artifact data."""

    scope: str
    scene_id: str | None = None
    mood_descriptors: list[str] = []
    reference_films: list[str] = []
    filmmaker_anchors: list[str] = []
    style_preset_id: str | None = None
    natural_language_intent: str | None = None
    look_notes: str | None = None
    user_approved: bool = False
    version: int = 1


class PropagateRequest(BaseModel):
    """Request payload for triggering mood propagation."""

    scope: str = "project"
    scene_id: str | None = None
    model: str | None = None


class PropagatedGroupResponse(BaseModel):
    """A single concern group's propagated suggestions."""

    fields: dict[str, Any]
    rationale: str


class PropagationResponse(BaseModel):
    """Full propagation result — suggested defaults per concern group."""

    look_and_feel: PropagatedGroupResponse | None = None
    sound_and_music: PropagatedGroupResponse | None = None
    rhythm_and_flow: PropagatedGroupResponse | None = None
    character_and_performance: PropagatedGroupResponse | None = None
    story_world: PropagatedGroupResponse | None = None
    overall_rationale: str = ""
    confidence: float = 0.0
    artifacts_created: list[str] = []


class ScriptContextResponse(BaseModel):
    """Script bible context surfaced on the Intent page."""

    title: str
    logline: str
    genre: str
    tone: str
    themes: list[str] = []


class IntentMoodSuggestion(BaseModel):
    """AI-suggested IntentMood from script analysis (unsaved)."""

    mood_descriptors: list[str]
    reference_films: list[str] = []
    filmmaker_anchors: list[str] = []
    style_preset_id: str | None = None
    natural_language_intent: str | None = None
    look_notes: str | None = None
    rationale: str = ""


class StylePresetResponse(BaseModel):
    """Style preset summary for the UI."""

    preset_id: str
    display_name: str
    description: str
    mood_descriptors: list[str]
    reference_films: list[str]
    thumbnail_emoji: str
    concern_group_ids: list[str] = []
