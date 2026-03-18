"""Schemas for scene-level storyboard artifacts."""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from .models import ArtifactRef, CostRecord, StoryboardStyleValue


class StoryboardImageFile(BaseModel):
    """Persisted image file referenced by a storyboard frame."""

    relative_path: str
    media_type: str = "image/jpeg"


class StoryboardOverlay(BaseModel):
    """Deterministic metadata rendered alongside a storyboard frame."""

    shot_ids: list[str] = Field(default_factory=list, min_length=1)
    shot_size: str
    camera_angle: str
    camera_movement: str
    character_labels: list[str] = Field(default_factory=list)
    blocking_indicator: str
    camera_indicator: str
    edit_intent: str | None = None


class StoryboardFrame(BaseModel):
    """Single generated storyboard frame tied to one or more shots."""

    frame_id: str
    shot_ids: list[str] = Field(default_factory=list, min_length=1)
    primary_shot_id: str
    image: StoryboardImageFile
    prompt_used: str
    prompt_sources_used: list[str] = Field(default_factory=list)
    visual_reference_images: list[str] = Field(default_factory=list)
    overlay: StoryboardOverlay
    duration_estimate_seconds: float = Field(ge=0.0)
    cost: CostRecord
    notes: str | None = None

    @model_validator(mode="after")
    def _validate_primary_shot(self) -> StoryboardFrame:
        if self.primary_shot_id not in self.shot_ids:
            raise ValueError("primary_shot_id must appear in shot_ids")
        return self


class Storyboard(BaseModel):
    """Per-scene storyboard artifact containing ordered frames and file refs."""

    scene_id: str
    scene_number: int = Field(ge=1)
    scene_heading: str
    scene_ref: ArtifactRef
    shot_plan_ref: ArtifactRef
    style: StoryboardStyleValue
    aspect_ratio: str
    frames: list[StoryboardFrame] = Field(default_factory=list, min_length=1)
    total_estimated_cost_usd: float = Field(ge=0.0)

