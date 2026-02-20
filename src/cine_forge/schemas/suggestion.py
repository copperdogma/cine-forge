"""Schemas for creative suggestions and editorial decisions."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from .models import ArtifactRef


class SuggestionStatus(StrEnum):
    """Lifecycle status for a creative suggestion."""

    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    DEFERRED = "deferred"
    SUPERSEDED = "superseded"


class Suggestion(BaseModel):
    """Immutable creative suggestion artifact."""

    suggestion_id: str = Field(min_length=1)
    source_role: str = Field(min_length=1)
    related_artifact_ref: ArtifactRef | None = None
    related_scene_id: str | None = None
    related_entity_id: str | None = None
    proposal: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    status: SuggestionStatus = SuggestionStatus.PROPOSED
    status_reason: str | None = None
    decided_by: str | None = None  # Role ID or "human"
    decided_at: datetime | None = None
    superseded_by: str | None = None  # suggestion_id of replacement
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Decision(BaseModel):
    """Immutable editorial decision artifact."""

    decision_id: str = Field(min_length=1)
    decided_by: str = Field(min_length=1)  # Role ID or "human"
    summary: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    alternatives_considered: list[str] = Field(default_factory=list)
    informed_by_suggestions: list[str] = Field(default_factory=list)  # suggestion_ids
    affected_artifacts: list[ArtifactRef] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
