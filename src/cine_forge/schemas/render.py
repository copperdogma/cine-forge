"""Schemas for render prompts, generated video artifacts, and engine packs."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .creative_brief import VisualCreativeBrief
from .models import ArtifactRef, CostRecord
from .preview import MediaFile, PreviewProvenance

RenderProvider = Literal["openai", "google", "xai"]
PrevizAdoptionState = Literal["default", "recommended_optional", "experimental_manual"]
PrevizCostStatus = Literal["verified", "estimated", "blocked"]
PrevizLaneId = Literal["ai_previz"]
PrevizLatencyClass = Literal["fast", "slow"]
PrevizConsistencyStrategy = Literal[
    "deterministic",
    "prompt_only",
    "optional_references",
    "reference_guided",
]
PrevizPromptProfile = Literal["standard", "compact"]
RenderPromptUsage = Literal[
    "input_reference",
    "reference_image",
    "last_frame",
    "prompt_context",
    "unsupported",
]
RenderInputKind = Literal[
    "keyframe",
    "scene_injected_image",
    "scene_injected_audio",
    "project_injected_image",
    "project_injected_audio",
    "character_injected_image",
    "location_injected_image",
]


class RenderPromptSection(BaseModel):
    """One attributed section inside the compiled render prompt."""

    section_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    body: str = Field(min_length=1)
    source_role_id: str | None = None
    source_artifact_types: list[str] = Field(default_factory=list)


class RenderResolvedInput(BaseModel):
    """Resolved upstream image/audio/keyframe input and how the adapter used it."""

    input_id: str = Field(min_length=1)
    kind: RenderInputKind
    label: str = Field(min_length=1)
    relative_path: str | None = None
    media_type: str | None = None
    source_ref: ArtifactRef | None = None
    lock_status: str | None = None
    required: bool = False
    used_as: RenderPromptUsage = "prompt_context"
    notes: str | None = None


class RenderCompletenessCheck(BaseModel):
    """Deterministic summary of which prompt-input categories were covered."""

    included_categories: list[str] = Field(default_factory=list)
    missing_categories: list[str] = Field(default_factory=list)
    blocking_missing_categories: list[str] = Field(default_factory=list)
    advisory_missing_categories: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class PrevizStyleProfile(BaseModel):
    """Named low-fidelity visual contract for AI-generated previz."""

    profile_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    identity_strategy: str = Field(min_length=1)
    location_strategy: str = Field(min_length=1)
    motion_priority: str = Field(min_length=1)
    detail_suppression: list[str] = Field(default_factory=list)
    prompt_guidance: list[str] = Field(default_factory=list)


class PrevizPromptContract(BaseModel):
    """Compiled prompt contract for low-fidelity AI previz experiments."""

    target_engine_pack_id: str = Field(min_length=1)
    consistency_strategy: PrevizConsistencyStrategy = "prompt_only"
    prompt_profile: PrevizPromptProfile = "standard"
    style_profile: PrevizStyleProfile
    prompt_text: str = Field(min_length=1)
    negative_prompt_terms: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class PrevizCostEvidence(BaseModel):
    """Cost evidence or blocker behind the current AI-previz lane."""

    status: PrevizCostStatus = "blocked"
    estimated_cost_usd: float | None = Field(default=None, ge=0.0)
    reason: str | None = None


class PrevizLaneStatus(BaseModel):
    """Shared operator-facing status for one previz lane."""

    lane_id: PrevizLaneId
    label: str = Field(min_length=1)
    candidate_label: str | None = None
    latency_class: PrevizLatencyClass = "slow"
    adoption_state: PrevizAdoptionState = "experimental_manual"
    reason: str = Field(min_length=1)
    intended_use: str = Field(min_length=1)
    fidelity_disclosure: str = Field(min_length=1)
    blocker_reasons: list[str] = Field(default_factory=list)
    overall_score: float | None = Field(default=None, ge=0.0, le=1.0)
    baseline_score: float | None = Field(default=None, ge=0.0, le=1.0)
    score_margin: float | None = None
    measured_at: str | None = None
    latency_ms: int | None = Field(default=None, ge=0)
    latency_budget_ms: int | None = Field(default=None, ge=0)
    regenerate_reuse_latency_ms: int | None = Field(default=None, ge=0)
    regenerate_full_latency_ms: int | None = Field(default=None, ge=0)
    engine_pack_id: str | None = None
    target_model: str | None = None
    resolution: str | None = None
    duration_seconds: float | None = Field(default=None, ge=0.0)
    consistency_strategy: PrevizConsistencyStrategy | None = None
    cost: PrevizCostEvidence = Field(default_factory=PrevizCostEvidence)
    validation_stage_enabled: bool = False


class PrevizAdoptionStatus(BaseModel):
    """Shared backend policy object for shipped AI-previz truth."""

    policy_summary: str = Field(min_length=1)
    ai_previz: PrevizLaneStatus


class CompiledRenderPrompt(BaseModel):
    """Persisted prompt artifact used to create a generated-video artifact."""

    scene_id: str = Field(min_length=1)
    scene_number: int = Field(ge=1)
    scene_heading: str = Field(min_length=1)
    render_unit: Literal["scene"] = "scene"
    scene_ref: ArtifactRef
    shot_plan_ref: ArtifactRef
    render_clip_plan_ref: ArtifactRef | None = None
    keyframe_ref: ArtifactRef | None = None
    target_provider: RenderProvider
    target_model: str = Field(min_length=1)
    engine_pack_id: str = Field(min_length=1)
    compiler_model: str = Field(min_length=1)
    requested_duration_seconds: float = Field(ge=0.0)
    resolved_duration_seconds: float = Field(ge=0.0)
    resolution: str = Field(min_length=1)
    aspect_ratio: str = Field(min_length=1)
    provider_params: dict[str, Any] = Field(default_factory=dict)
    prompt_text: str = Field(min_length=1)
    sections: list[RenderPromptSection] = Field(default_factory=list, min_length=1)
    completeness: RenderCompletenessCheck
    prompt_sources_used: list[str] = Field(default_factory=list)
    creative_brief_preview: VisualCreativeBrief | None = None
    resolved_inputs: list[RenderResolvedInput] = Field(default_factory=list)
    preview_provenance: PreviewProvenance | None = None

    @model_validator(mode="after")
    def _validate_duration(self) -> CompiledRenderPrompt:
        if self.resolved_duration_seconds <= 0:
            raise ValueError("resolved_duration_seconds must be positive")
        if self.requested_duration_seconds <= 0:
            raise ValueError("requested_duration_seconds must be positive")
        return self


class GeneratedVideoArtifact(BaseModel):
    """Persisted scene-level generated-video artifact."""

    scene_id: str = Field(min_length=1)
    scene_number: int = Field(ge=1)
    scene_heading: str = Field(min_length=1)
    render_unit: Literal["scene"] = "scene"
    scene_ref: ArtifactRef
    shot_plan_ref: ArtifactRef
    render_clip_plan_ref: ArtifactRef | None = None
    prompt_ref: ArtifactRef
    keyframe_ref: ArtifactRef | None = None
    video: MediaFile
    duration_seconds: float = Field(ge=0.0)
    resolution: str = Field(min_length=1)
    aspect_ratio: str = Field(min_length=1)
    generation_params: dict[str, Any] = Field(default_factory=dict)
    target_provider: RenderProvider
    target_model: str = Field(min_length=1)
    engine_pack_id: str = Field(min_length=1)
    request_id: str | None = None
    cost: CostRecord
    resolved_inputs: list[RenderResolvedInput] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    preview_provenance: PreviewProvenance | None = None


class EnginePackLimits(BaseModel):
    """Capability envelope for one video-generation engine pack."""

    supported_durations_seconds: list[int] = Field(default_factory=list)
    supported_resolutions: list[str] = Field(default_factory=list)
    supported_aspect_ratios: list[str] = Field(default_factory=list)
    max_reference_images: int = Field(default=0, ge=0)
    supports_first_frame: bool = False
    supports_last_frame: bool = False
    supports_audio_upload: bool = False
    supports_audio_cues: bool = True

    @model_validator(mode="after")
    def _validate_values(self) -> EnginePackLimits:
        if not self.supported_durations_seconds:
            raise ValueError("supported_durations_seconds must not be empty")
        if not self.supported_resolutions:
            raise ValueError("supported_resolutions must not be empty")
        return self


class EnginePackRetryPolicy(BaseModel):
    """Retry guidance attached to an engine pack."""

    max_attempts: int = Field(default=2, ge=1)
    poll_interval_seconds: float = Field(default=10.0, ge=1.0)
    retryable_http_statuses: list[int] = Field(default_factory=list)
    retryable_error_substrings: list[str] = Field(default_factory=list)


class EnginePack(BaseModel):
    """Validated engine-pack configuration loaded from YAML."""

    pack_id: str = Field(min_length=1)
    provider: RenderProvider
    target_model: str = Field(min_length=1)
    description: str = Field(min_length=1)
    preferred_prompt_style: str = Field(min_length=1)
    known_strengths: list[str] = Field(default_factory=list)
    known_limitations: list[str] = Field(default_factory=list)
    limits: EnginePackLimits
    request_defaults: dict[str, Any] = Field(default_factory=dict)
    retry_policy: EnginePackRetryPolicy = Field(default_factory=EnginePackRetryPolicy)
