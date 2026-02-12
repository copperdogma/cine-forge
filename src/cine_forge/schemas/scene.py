"""Schemas for per-scene extraction artifacts."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class ScriptElement(BaseModel):
    """A single screenplay element within a scene."""

    element_type: Literal[
        "scene_heading",
        "action",
        "character",
        "dialogue",
        "parenthetical",
        "transition",
        "shot",
        "note",
    ]
    content: str


class SourceSpan(BaseModel):
    """Line range reference into the canonical script."""

    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)

    @model_validator(mode="after")
    def validate_order(self) -> SourceSpan:
        """Ensure span ordering is monotonic."""
        if self.end_line < self.start_line:
            raise ValueError("end_line must be greater than or equal to start_line")
        return self


class NarrativeBeat(BaseModel):
    """AI-identified narrative beat metadata."""

    beat_type: str
    description: str
    approximate_location: str
    confidence: float = Field(ge=0.0, le=1.0)


class InferredField(BaseModel):
    """Marks data that required inference beyond explicit text."""

    field_name: str
    value: str
    rationale: str
    confidence: float = Field(ge=0.0, le=1.0)


class FieldProvenance(BaseModel):
    """Captures which mechanism produced each extracted field."""

    field_name: str
    method: Literal["parser", "rule", "ai"]
    evidence: str
    confidence: float = Field(ge=0.0, le=1.0)


class Scene(BaseModel):
    """Per-scene structured extraction artifact."""

    scene_id: str
    scene_number: int = Field(ge=1)
    heading: str
    location: str
    time_of_day: str
    int_ext: Literal["INT", "EXT", "INT/EXT"]
    characters_present: list[str] = Field(default_factory=list)
    elements: list[ScriptElement] = Field(default_factory=list)
    narrative_beats: list[NarrativeBeat] = Field(default_factory=list)
    tone_mood: str
    tone_shifts: list[str] = Field(default_factory=list)
    source_span: SourceSpan
    inferences: list[InferredField] = Field(default_factory=list)
    provenance: list[FieldProvenance] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


class SceneIndexEntry(BaseModel):
    """Summary row for scene index output."""

    scene_id: str
    scene_number: int = Field(ge=1)
    heading: str
    location: str
    time_of_day: str
    characters_present: list[str] = Field(default_factory=list)
    source_span: SourceSpan
    tone_mood: str


class SceneIndex(BaseModel):
    """Aggregate index artifact for scene list and QA status."""

    total_scenes: int = Field(ge=0)
    unique_locations: list[str] = Field(default_factory=list)
    unique_characters: list[str] = Field(default_factory=list)
    estimated_runtime_minutes: float = Field(ge=0.0)
    scenes_passed_qa: int = Field(ge=0)
    scenes_need_review: int = Field(ge=0)
    entries: list[SceneIndexEntry] = Field(default_factory=list)
