"""Schemas for transparent project-level preference learning."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field

from .design_study import EntityType as DesignStudyEntityType
from .design_study import ImageDecision

PreferenceSignalSourceKind = Literal["design_study_decision"]
PreferenceSignalPolarity = Literal["positive", "negative", "directional", "neutral"]
PreferenceCueType = Literal["preferred", "avoid", "variation"]


class PreferenceLearningSettings(BaseModel):
    """Project-scoped preference-learning controls stored in project settings."""

    enabled: bool = True
    cleared_at: datetime | None = None


class PreferenceSignal(BaseModel):
    """One immutable preference-learning event derived from a user decision."""

    signal_id: str = Field(min_length=1)
    source_kind: PreferenceSignalSourceKind = "design_study_decision"
    entity_id: str = Field(min_length=1)
    entity_type: DesignStudyEntityType
    round_number: int = Field(ge=1)
    image_filename: str = Field(min_length=1)
    decision: ImageDecision
    polarity: PreferenceSignalPolarity
    guidance: str | None = None
    round_guidance: str | None = None
    prompt_used: str = Field(min_length=1)
    prompt_sources_used: list[str] = Field(default_factory=list)
    model: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class PreferenceCue(BaseModel):
    """One transparent cue derived from one or more active preference signals."""

    cue_type: PreferenceCueType
    entity_id: str = Field(min_length=1)
    entity_type: DesignStudyEntityType
    text: str = Field(min_length=1)
    weight: float = Field(default=1.0, ge=0.0)
    signal_count: int = Field(default=1, ge=1)
    source_signal_ids: list[str] = Field(default_factory=list)
    source_image_filenames: list[str] = Field(default_factory=list)


class PreferenceProfile(BaseModel):
    """Project-level transparent summary of active learned preferences."""

    enabled: bool = True
    last_cleared_at: datetime | None = None
    active_signal_count: int = Field(default=0, ge=0)
    entity_count: int = Field(default=0, ge=0)
    summary_lines: list[str] = Field(default_factory=list)
    preferred_cues: list[PreferenceCue] = Field(default_factory=list)
    avoid_cues: list[PreferenceCue] = Field(default_factory=list)
    variation_cues: list[PreferenceCue] = Field(default_factory=list)
    recent_signals: list[PreferenceSignal] = Field(default_factory=list)
