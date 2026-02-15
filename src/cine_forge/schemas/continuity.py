"""Schemas for asset state tracking and continuity artifacts."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class StateProperty(BaseModel):
    """A single property snapshot for an entity's state."""

    key: str
    value: str
    confidence: float = Field(ge=0.0, le=1.0)


class ContinuityEvent(BaseModel):
    """An event describing a change in an entity's state."""

    property_key: str
    previous_value: str | None = None
    new_value: str
    reason: str
    evidence: str
    is_explicit: bool
    confidence: float = Field(ge=0.0, le=1.0)


class ContinuityState(BaseModel):
    """Snapshot of an entity's state at a specific point in time/scene."""

    entity_type: Literal["character", "location", "prop"]
    entity_id: str
    scene_id: str
    story_time_position: int
    properties: list[StateProperty] = Field(default_factory=list)
    change_events: list[ContinuityEvent] = Field(default_factory=list)
    overall_confidence: float = Field(ge=0.0, le=1.0)


class EntityTimeline(BaseModel):
    """Ordered sequence of states for a single entity."""

    entity_type: Literal["character", "location", "prop"]
    entity_id: str
    states: list[str] = Field(default_factory=list)  # list of state artifact paths or IDs
    gaps: list[str] = Field(default_factory=list)  # list of scene IDs with missing/ambiguous state


class ContinuityIndex(BaseModel):
    """Master index of all entity state timelines."""

    # entity_type:entity_id -> timeline
    timelines: dict[str, EntityTimeline] = Field(default_factory=dict)
    total_gaps: int = 0
    overall_continuity_score: float = Field(ge=0.0, le=1.0)
