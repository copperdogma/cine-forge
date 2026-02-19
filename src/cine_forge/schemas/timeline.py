"""Schemas for project timeline and ordering artifacts."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from .models import ArtifactRef


class TimelineEntry(BaseModel):
    """A single scene slot in script/edit/story orderings."""

    scene_id: str
    scene_ref: ArtifactRef
    script_position: int = Field(ge=1)
    edit_position: int = Field(ge=1)
    story_position: int = Field(ge=1)
    estimated_duration_seconds: float = Field(ge=0.0)
    shot_count: int = Field(default=0, ge=0)
    shot_ids: list[str] = Field(default_factory=list)
    story_order_confidence: Literal["high", "medium", "low"] = "low"
    story_order_rationale: str | None = None
    notes: str | None = None


class Timeline(BaseModel):
    """Project-level temporal structure artifact."""

    entries: list[TimelineEntry] = Field(default_factory=list)
    total_scenes: int = Field(ge=0)
    estimated_runtime_seconds: float = Field(ge=0.0)
    edit_order_locked: bool = False
    story_order_locked: bool = False
    chronology_source: Literal["continuity_index", "scene_index_fallback"] = "scene_index_fallback"
