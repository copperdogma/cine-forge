"""Typed narrative export contracts shared by interchange emitters."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .models import ArtifactRef

NarrativeAnnotationKind = Literal[
    "scene_boundary",
    "beat",
    "character_entrance",
    "character_exit",
    "emotional_note",
]


class NarrativeSceneSegment(BaseModel):
    """Timeline-aligned scene segment used by export emitters."""

    scene_id: str
    scene_number: int = Field(ge=1)
    scene_ref: ArtifactRef
    edit_position: int = Field(ge=1)
    story_position: int = Field(ge=1)
    heading: str
    location: str
    time_of_day: str
    int_ext: str
    characters_present: list[str] = Field(default_factory=list)
    start_seconds: float = Field(ge=0.0)
    duration_seconds: float = Field(ge=0.0)
    end_seconds: float = Field(ge=0.0)

    @model_validator(mode="after")
    def _validate_end_time(self) -> NarrativeSceneSegment:
        if self.end_seconds < self.start_seconds:
            raise ValueError("end_seconds must be >= start_seconds")
        return self


class NarrativeAnnotation(BaseModel):
    """Format-independent narrative annotation anchored to the timeline."""

    annotation_id: str
    kind: NarrativeAnnotationKind
    scene_id: str
    scene_ref: ArtifactRef
    start_seconds: float = Field(ge=0.0)
    duration_seconds: float = Field(default=0.0, ge=0.0)
    end_seconds: float = Field(ge=0.0)
    label: str
    note: str | None = None
    color_label: str | None = None
    character_name: str | None = None

    @model_validator(mode="after")
    def _validate_end_time(self) -> NarrativeAnnotation:
        if self.end_seconds < self.start_seconds:
            raise ValueError("end_seconds must be >= start_seconds")
        return self


class NarrativeInterchangeExport(BaseModel):
    """Canonical narrative timeline export payload consumed by file emitters."""

    project_id: str
    project_title: str
    timeline_ref: ArtifactRef
    track_manifest_ref: ArtifactRef | None = None
    total_duration_seconds: float = Field(ge=0.0)
    scenes: list[NarrativeSceneSegment] = Field(default_factory=list)
    annotations: list[NarrativeAnnotation] = Field(default_factory=list)
