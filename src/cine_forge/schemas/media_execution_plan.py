"""Immutable inspected scene work and the exact sources authorizing execution."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from cine_forge.schemas.media_cost import VideoPrice
from cine_forge.schemas.models import ArtifactRef


class MediaExecutionPlanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    recipe_id: Literal["render_generation", "ai_previz_generation"]
    scene_id: str = Field(min_length=1)
    render_clip_ids: list[str] | None = Field(default=None, min_length=1)

    @field_validator("render_clip_ids")
    @classmethod
    def validate_selection(cls, value: list[str] | None) -> list[str] | None:
        if value is not None and (
            len(value) != len(set(value)) or any(not x.strip() for x in value)
        ):
            raise ValueError("Clip selection must contain unique non-empty IDs")
        return value


class MediaSourceBinding(BaseModel):
    """A source artifact, mutable file, or explicit absence in the inspected scope."""

    key: str
    ref: ArtifactRef | None = None
    sha256: str | None = None


class MediaExecutionUnit(BaseModel):
    entity_id: str
    clip_id: str | None = None
    title: str
    planned_duration_seconds: float
    duration_seconds: int
    resolution: str
    aspect_ratio: str
    provider: str
    model: str
    video_estimate_usd: float | None = None
    price: VideoPrice | None = None


class MediaExecutionPlan(BaseModel):
    project_id: str
    recipe_id: Literal["render_generation", "ai_previz_generation"]
    scene_id: str
    render_clip_ids: list[str] | None = None
    binding_sha256: str
    status: Literal["ready", "blocked"]
    blockers: list[str] = Field(default_factory=list)
    units: list[MediaExecutionUnit] = Field(default_factory=list)
    video_estimate_usd: float | None = None
    total_estimate_usd: None = None
    excluded_costs: list[str] = Field(
        default_factory=lambda: [
            "Prompt compilation",
            "Preparation already incurred",
            "Validation and retries",
        ]
    )
    source_bindings: list[MediaSourceBinding] = Field(default_factory=list)


class MediaExecutionPlanResponse(BaseModel):
    plan_ref: ArtifactRef
    plan: MediaExecutionPlan
