"""Schemas for provider-bounded scene render clip planning."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .models import ArtifactRef

RenderClipDerivation = Literal["shot_plan", "ai_fallback", "code_default", "hybrid"]
RenderClipPlanSource = Literal["ai", "code", "hybrid"]
RenderClipPlanMode = Literal[
    "shot_plan_ai",
    "shot_plan_code",
    "fallback_ai",
    "fallback_code",
]


class RenderClip(BaseModel):
    """One provider-bounded generation unit inside a scene render plan."""

    clip_id: str = Field(min_length=1)
    scene_id: str = Field(min_length=1)
    source_shot_ids: list[str] = Field(default_factory=list)
    fallback_beat_ids: list[str] = Field(default_factory=list)
    start_time_seconds: float = Field(ge=0.0)
    end_time_seconds: float = Field(ge=0.0)
    target_duration_seconds: float = Field(gt=0.0)
    dialogue_lines: list[str] = Field(default_factory=list)
    action_beats: list[str] = Field(default_factory=list)
    continuity_start_notes: list[str] = Field(default_factory=list)
    continuity_end_notes: list[str] = Field(default_factory=list)
    reference_intent: list[str] = Field(default_factory=list)
    keyframe_intent: str | None = None
    derivation: RenderClipDerivation
    rationale: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="after")
    def _validate_timing(self) -> RenderClip:
        if self.end_time_seconds < self.start_time_seconds:
            raise ValueError("end_time_seconds must be >= start_time_seconds")
        window_duration = self.end_time_seconds - self.start_time_seconds
        if abs(window_duration - self.target_duration_seconds) > 0.05:
            raise ValueError(
                "clip timing window must match target_duration_seconds within 0.05s"
            )
        return self


class RenderClipPlan(BaseModel):
    """Scene-level dramatic-duration estimate and provider clip plan."""

    scene_id: str = Field(min_length=1)
    scene_number: int = Field(ge=1)
    scene_heading: str = Field(min_length=1)
    scene_ref: ArtifactRef
    shot_plan_ref: ArtifactRef | None = None
    timeline_ref: ArtifactRef | None = None
    track_manifest_ref: ArtifactRef | None = None
    selected_engine_pack_id: str = Field(min_length=1)
    engine_max_clip_duration_seconds: float = Field(gt=0.0)
    target_dramatic_duration_seconds: float = Field(gt=0.0)
    duration_rationale: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    source: RenderClipPlanSource
    provenance_mode: RenderClipPlanMode
    planner_model: str | None = None
    missing_upstream_categories: list[str] = Field(default_factory=list)
    deterministic_lower_bound_seconds: float = Field(ge=0.0)
    clips: list[RenderClip] = Field(default_factory=list, min_length=1)
    notes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_clips(self) -> RenderClipPlan:
        seen_ids: set[str] = set()
        previous_end = 0.0
        for clip in self.clips:
            if clip.scene_id != self.scene_id:
                raise ValueError("all render clips must share the parent scene_id")
            if clip.clip_id in seen_ids:
                raise ValueError("clip_id values must be unique within a RenderClipPlan")
            if clip.target_duration_seconds > self.engine_max_clip_duration_seconds + 0.05:
                raise ValueError("render clip exceeds engine_max_clip_duration_seconds")
            if clip.start_time_seconds + 0.05 < previous_end:
                raise ValueError("render clips must be ordered by non-overlapping time")
            seen_ids.add(clip.clip_id)
            previous_end = max(previous_end, clip.end_time_seconds)

        if self.target_dramatic_duration_seconds + 0.05 < self.deterministic_lower_bound_seconds:
            raise ValueError("target duration cannot be below deterministic lower bound")
        summed_duration = sum(clip.target_duration_seconds for clip in self.clips)
        if abs(summed_duration - self.target_dramatic_duration_seconds) > 0.25:
            raise ValueError("clip durations must sum to target_dramatic_duration_seconds")
        return self
