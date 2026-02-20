"""Schemas for inter-role conversations and transcripts."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field

from .models import ArtifactRef


class ConversationTurn(BaseModel):
    """A single turn in a multi-role conversation."""

    role_id: str = Field(min_length=1)
    content: str = Field(min_length=1)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    references: list[ArtifactRef] = Field(default_factory=list)


class Conversation(BaseModel):
    """Immutable inter-role conversation artifact."""

    conversation_id: str = Field(min_length=1)
    participants: list[str] = Field(default_factory=list, min_length=1)
    topic: str = Field(min_length=1)
    related_artifacts: list[ArtifactRef] = Field(default_factory=list)
    turns: list[ConversationTurn] = Field(default_factory=list)
    outcome_decisions: list[str] = Field(default_factory=list)  # Decision artifact IDs
    outcome_suggestions: list[str] = Field(default_factory=list)  # Suggestion artifact IDs
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class DisagreementArtifact(BaseModel):
    """Detailed record of a specific disagreement and its resolution."""

    disagreement_id: str = Field(min_length=1)
    conversation_id: str | None = None
    objecting_role_id: str = Field(min_length=1)
    objection_summary: str = Field(min_length=1)
    objection_rationale: str = Field(min_length=1)
    overriding_role_id: str | None = None
    override_rationale: str | None = None
    status: Literal[
        "open", "resolved_with_override", "resolved_with_concession", "withdrawn"
    ] = "open"
    affected_artifacts: list[ArtifactRef] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    resolved_at: datetime | None = None
