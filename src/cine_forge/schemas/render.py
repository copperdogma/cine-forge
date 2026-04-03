"""Schemas for render prompts, generated video artifacts, and engine packs."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .animatic import MediaFile, PreviewProvenance
from .creative_brief import VisualCreativeBrief
from .models import ArtifactRef, CostRecord

RenderProvider = Literal["openai", "google"]
PrevizConsistencyStrategy = Literal[
    "prompt_only",
    "optional_references",
    "reference_guided",
]
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
    style_profile: PrevizStyleProfile
    prompt_text: str = Field(min_length=1)
    negative_prompt_terms: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class CompiledRenderPrompt(BaseModel):
    """Persisted prompt artifact used to create a generated-video artifact."""

    scene_id: str = Field(min_length=1)
    scene_number: int = Field(ge=1)
    scene_heading: str = Field(min_length=1)
    render_unit: Literal["scene"] = "scene"
    scene_ref: ArtifactRef
    shot_plan_ref: ArtifactRef
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
    prompt_ref: ArtifactRef
    keyframe_ref: ArtifactRef | None = None
    previz_baseline_ref: ArtifactRef | None = None
    previz_reel_ref: ArtifactRef | None = None
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
