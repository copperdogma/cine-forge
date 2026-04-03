"""Schemas for animatic, keyframe, and previz reel artifacts."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .models import ArtifactRef


class MediaFile(BaseModel):
    """Persisted media file referenced by an artifact."""

    relative_path: str
    media_type: str
    duration_seconds: float | None = Field(default=None, ge=0.0)


class AudioReference(BaseModel):
    """Audio source used during animatic or previz assembly."""

    relative_path: str
    media_type: str = "audio/wav"
    source_kind: Literal["scene_injected", "project_injected", "sound_and_music"] = (
        "scene_injected"
    )
    label: str | None = None
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
    estimated_cost_usd: float | None = Field(default=None, ge=0.0)
    generation_latency_ms: int | None = Field(default=None, ge=0)


class AnimaticSegment(BaseModel):
    """Single shot-aligned animatic segment."""

    segment_id: str
    shot_id: str
    storyboard_frame_id: str | None = None
    source_kind: Literal["storyboard", "placeholder"] = "storyboard"
    source_image_path: str | None = None
    video: MediaFile
    duration_seconds: float = Field(ge=0.0)
    shot_size: str
    camera_angle: str
    camera_movement: str
    characters_in_frame: list[str] = Field(default_factory=list)
    edit_intent: str
    notes: str | None = None


class Animatic(BaseModel):
    """Per-scene animatic artifact with ordered segments and a scene render."""

    scene_id: str
    scene_number: int = Field(ge=1)
    scene_heading: str
    scene_ref: ArtifactRef
    shot_plan_ref: ArtifactRef
    storyboard_ref: ArtifactRef | None = None
    sound_and_music_ref: ArtifactRef | None = None
    video: MediaFile
    segments: list[AnimaticSegment] = Field(default_factory=list, min_length=1)
    audio_refs: list[AudioReference] = Field(default_factory=list)
    total_duration_seconds: float = Field(ge=0.0)
    source_mix: list[str] = Field(default_factory=list)
    preview_provenance: PreviewProvenance = Field(default_factory=PreviewProvenance)

    @model_validator(mode="after")
    def _validate_total_duration(self) -> Animatic:
        if self.total_duration_seconds <= 0 and self.segments:
            raise ValueError("total_duration_seconds must be positive when segments exist")
        return self


class Keyframe(BaseModel):
    """Single keyframe extracted for a shot position."""

    keyframe_id: str
    shot_id: str
    position: Literal["start", "mid", "end"]
    timestamp_seconds: float = Field(ge=0.0)
    image: MediaFile
    source_kind: Literal["storyboard", "animatic", "placeholder"] = "storyboard"
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
    animatic_ref: ArtifactRef | None = None
    storyboard_ref: ArtifactRef | None = None
    keyframes: list[Keyframe] = Field(default_factory=list, min_length=1)


class PrevizSceneSegment(BaseModel):
    """Scene-level item inside the project previz reel."""

    scene_id: str
    scene_number: int = Field(ge=1)
    scene_heading: str
    source_track_type: Literal["animatics", "storyboards", "script"]
    artifact_ref: ArtifactRef
    video: MediaFile
    audio_refs: list[AudioReference] = Field(default_factory=list)
    duration_seconds: float = Field(ge=0.0)
    notes: str | None = None
    preview_provenance: PreviewProvenance = Field(default_factory=PreviewProvenance)


class PrevizReel(BaseModel):
    """Project-level mixed-fidelity previz reel."""

    timeline_ref: ArtifactRef
    track_manifest_ref: ArtifactRef
    reel_video: MediaFile
    scenes: list[PrevizSceneSegment] = Field(default_factory=list, min_length=1)
    total_duration_seconds: float = Field(ge=0.0)
