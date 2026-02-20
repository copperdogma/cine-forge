"""Schemas for track manifests and scene-level representation entries."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .models import ArtifactRef

TrackStatus = Literal["available", "pending", "failed"]


class TrackEntry(BaseModel):
    """A single representation entry anchored to a scene and optional time/shot."""

    track_type: str
    scene_id: str
    shot_id: str | None = None
    artifact_ref: ArtifactRef
    start_time_seconds: float | None = Field(default=None, ge=0.0)
    end_time_seconds: float | None = Field(default=None, ge=0.0)
    priority: int = Field(default=100, ge=0)
    status: TrackStatus = "available"
    notes: str | None = None

    @model_validator(mode="after")
    def _validate_time_bounds(self) -> TrackEntry:
        if (
            self.start_time_seconds is not None
            and self.end_time_seconds is not None
            and self.end_time_seconds < self.start_time_seconds
        ):
            raise ValueError("end_time_seconds must be >= start_time_seconds")
        return self


class TrackManifest(BaseModel):
    """Project-level track state aligned to a specific timeline version."""

    timeline_ref: ArtifactRef
    entries: list[TrackEntry] = Field(default_factory=list)
    fallback_order: list[str] = Field(
        default_factory=lambda: [
            "generated_video",
            "animatics",
            "storyboards",
            "script",
        ]
    )
    track_fill_counts: dict[str, int] = Field(default_factory=dict)
