"""Schemas for assembled project-level final output artifacts."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .models import ArtifactRef
from .preview import MediaFile

FinalOutputCoverageState = Literal["partial", "complete"]
FinalOutputOmissionReason = Literal[
    "missing_generated_video_track",
    "missing_generated_video_artifact",
]


class FinalOutputIncludedClip(BaseModel):
    """One generated-video clip included inside a rendered timeline scene."""

    render_clip_id: str | None = None
    generated_video_ref: ArtifactRef
    clip_relative_path: str = Field(min_length=1)
    duration_seconds: float = Field(ge=0.0)
    scene_start_seconds: float | None = Field(default=None, ge=0.0)
    scene_end_seconds: float | None = Field(default=None, ge=0.0)
    output_start_seconds: float = Field(ge=0.0)
    output_end_seconds: float = Field(ge=0.0)

    @model_validator(mode="after")
    def _validate_time_bounds(self) -> FinalOutputIncludedClip:
        if self.output_end_seconds < self.output_start_seconds:
            raise ValueError("output_end_seconds must be >= output_start_seconds")
        if (
            self.scene_start_seconds is not None
            and self.scene_end_seconds is not None
            and self.scene_end_seconds < self.scene_start_seconds
        ):
            raise ValueError("scene_end_seconds must be >= scene_start_seconds")
        return self


class FinalOutputIncludedScene(BaseModel):
    """One timeline scene included in the assembled project output."""

    scene_id: str = Field(min_length=1)
    scene_number: int = Field(ge=1)
    scene_heading: str = Field(min_length=1)
    generated_video_ref: ArtifactRef
    clip_relative_path: str = Field(min_length=1)
    duration_seconds: float = Field(ge=0.0)
    output_start_seconds: float = Field(ge=0.0)
    output_end_seconds: float = Field(ge=0.0)
    clips: list[FinalOutputIncludedClip] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_time_bounds(self) -> FinalOutputIncludedScene:
        if self.output_end_seconds < self.output_start_seconds:
            raise ValueError("output_end_seconds must be >= output_start_seconds")
        for clip in self.clips:
            if clip.output_start_seconds < self.output_start_seconds:
                raise ValueError("clip output_start_seconds must be within scene bounds")
            if clip.output_end_seconds > self.output_end_seconds:
                raise ValueError("clip output_end_seconds must be within scene bounds")
        return self


class FinalOutputOmittedScene(BaseModel):
    """One timeline scene omitted from the assembled project output."""

    scene_id: str = Field(min_length=1)
    scene_number: int = Field(ge=1)
    scene_heading: str = Field(min_length=1)
    reason: FinalOutputOmissionReason
    detail: str | None = None


class FinalOutputArtifact(BaseModel):
    """Persisted project-level assembled cut built from generated scene renders."""

    timeline_ref: ArtifactRef
    track_manifest_ref: ArtifactRef
    video: MediaFile
    coverage_state: FinalOutputCoverageState = "partial"
    total_scene_count: int = Field(ge=0)
    included_scene_ids: list[str] = Field(default_factory=list)
    omitted_scene_ids: list[str] = Field(default_factory=list)
    included_scenes: list[FinalOutputIncludedScene] = Field(default_factory=list)
    omitted_scenes: list[FinalOutputOmittedScene] = Field(default_factory=list)
    normalization_applied: bool = False
    normalization_notes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_consistency(self) -> FinalOutputArtifact:
        included_ids = [item.scene_id for item in self.included_scenes]
        omitted_ids = [item.scene_id for item in self.omitted_scenes]

        if self.included_scene_ids != included_ids:
            raise ValueError("included_scene_ids must match included_scenes ordering")
        if self.omitted_scene_ids != omitted_ids:
            raise ValueError("omitted_scene_ids must match omitted_scenes ordering")
        if self.total_scene_count != len(self.included_scenes) + len(self.omitted_scenes):
            raise ValueError("total_scene_count must equal included + omitted scenes")
        if self.coverage_state == "complete" and self.omitted_scenes:
            raise ValueError("complete coverage cannot include omitted scenes")
        if self.coverage_state == "partial" and not self.omitted_scenes:
            raise ValueError("partial coverage must include at least one omitted scene")
        return self
