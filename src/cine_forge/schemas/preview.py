"""Schemas for preview media and keyframe artifacts."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from .models import ArtifactRef


class MediaFile(BaseModel):
    """Persisted media file referenced by an artifact."""

    relative_path: str
    media_type: str
    duration_seconds: float | None = Field(default=None, ge=0.0)


PreviewMode = Literal[
    "symbolic",
    "annotated_symbolic",
    "ai_previz",
    "generated_render",
    "final_render",
]
PreviewConsistencyStrategy = Literal[
    "prompt_only",
    "optional_references",
    "reference_guided",
]
PreviewFidelityIntent = Literal[
    "symbolic_baseline",
    "blocking_review",
    "render_preview",
    "final_render",
]
PreviewIntendedUse = Literal["human_review", "ai_conditioning"]


class PreviewProvenance(BaseModel):
    """Operator-facing provenance for preview and render artifacts."""

    mode: PreviewMode = "symbolic"
    fidelity_intent: PreviewFidelityIntent = "symbolic_baseline"
    intended_use: list[PreviewIntendedUse] = Field(default_factory=lambda: ["human_review"])
    upstream_inputs: list[str] = Field(default_factory=list)
    consistency_strategy: PreviewConsistencyStrategy | None = None
    prompt_profile: str | None = None
    estimated_cost_usd: float | None = Field(default=None, ge=0.0)
    generation_latency_ms: int | None = Field(default=None, ge=0)


class Keyframe(BaseModel):
    """Single keyframe extracted for a shot position."""

    keyframe_id: str
    shot_id: str
    position: Literal["start", "mid", "end"]
    timestamp_seconds: float = Field(ge=0.0)
    image: MediaFile
    source_kind: Literal["storyboard", "placeholder"] = "storyboard"
    source_segment_id: str | None = None
    is_locked: bool = False
    locked_by: str | None = None
    lock_reason: str | None = None
    shot_size: str
    camera_angle: str
    camera_movement: str
    notes: str | None = None


class KeyframeArtifact(BaseModel):
    """Per-scene keyframe artifact containing lockable start/mid/end frames."""

    scene_id: str
    scene_number: int = Field(ge=1)
    scene_heading: str
    shot_plan_ref: ArtifactRef
    storyboard_ref: ArtifactRef | None = None
    keyframes: list[Keyframe] = Field(default_factory=list, min_length=1)
