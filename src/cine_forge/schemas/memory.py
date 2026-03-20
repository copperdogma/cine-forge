"""Schemas for transcript indexing and working-memory state."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field

from .models import ArtifactRef

WorkingMemoryRole = Literal["director", "script_supervisor"]
MemoryQueryType = Literal[
    "decisions",
    "artifact_state",
    "suggestions",
    "conversations",
    "transcript_search",
]
TranscriptSourceKind = Literal["chat_message", "conversation_turn"]


class MemorySettings(BaseModel):
    """Project-scoped controls for optional working-memory behavior."""

    script_supervisor_enabled: bool = False


class MemorySettingsUpdate(BaseModel):
    """Partial update payload for project-scoped memory settings."""

    script_supervisor_enabled: bool | None = None


class TranscriptIndexEntry(BaseModel):
    """One searchable transcript entry sourced from chat or conversation history."""

    entry_id: str = Field(min_length=1)
    source_kind: TranscriptSourceKind
    source_id: str = Field(min_length=1)
    speaker: str = Field(min_length=1)
    text: str = Field(min_length=1)
    timestamp: datetime
    related_artifacts: list[ArtifactRef] = Field(default_factory=list)
    scene_ids: list[str] = Field(default_factory=list)
    entity_ids: list[str] = Field(default_factory=list)


class TranscriptIndex(BaseModel):
    """Immutable searchable index covering the project's transcript sources."""

    index_id: str = Field(min_length=1)
    source_signature: str = Field(min_length=1)
    entry_count: int = Field(ge=0)
    entries: list[TranscriptIndexEntry] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class TranscriptSearchRequest(BaseModel):
    """Filters for transcript search across human and inter-role conversations."""

    query: str | None = None
    participants: list[str] = Field(default_factory=list)
    scene_id: str | None = None
    entity_id: str | None = None
    artifact_type: str | None = None
    artifact_entity_id: str | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    limit: int = Field(default=20, ge=1, le=100)


class TranscriptSearchResponse(BaseModel):
    """Transcript search results plus the backing index artifact ref."""

    index_ref: ArtifactRef | None = None
    total_results: int = Field(ge=0)
    entries: list[TranscriptIndexEntry] = Field(default_factory=list)


class MemoryQueryRequest(BaseModel):
    """Deterministic canonical-memory query request."""

    question: str = Field(min_length=1)
    scene_id: str | None = None
    entity_id: str | None = None
    artifact_type: str | None = None
    participants: list[str] = Field(default_factory=list)
    max_results: int = Field(default=5, ge=1, le=25)


class MemoryQueryEvidence(BaseModel):
    """Structured evidence returned for a memory query answer."""

    source_kind: Literal["artifact", "transcript"]
    summary: str = Field(min_length=1)
    artifact_ref: ArtifactRef | None = None
    timestamp: datetime | None = None


class MemoryQueryResult(BaseModel):
    """Canonical-memory answer with provenance and supporting evidence."""

    query_type: MemoryQueryType
    question: str = Field(min_length=1)
    answer: str = Field(min_length=1)
    evidences: list[MemoryQueryEvidence] = Field(default_factory=list)


class WorkingMemorySummary(BaseModel):
    """Immutable checkpoint for a role's persisted working-memory summary."""

    summary_id: str = Field(min_length=1)
    role_id: WorkingMemoryRole
    summary_text: str = ""
    source_message_count: int = Field(default=0, ge=0)
    covered_through_hash: str = ""
    recent_message_count: int = Field(default=0, ge=0)
    reset_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class WorkingMemoryResetRequest(BaseModel):
    """Request to reset a role's persisted working-memory checkpoint."""

    role_id: WorkingMemoryRole
    reason: str | None = None


class WorkingMemoryResetResponse(BaseModel):
    """Reset result for a role's persisted working-memory checkpoint."""

    summary_ref: ArtifactRef
    summary: WorkingMemorySummary
