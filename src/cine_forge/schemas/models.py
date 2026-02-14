"""Core artifact and metadata schemas for the pipeline foundation."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


class ArtifactHealth(StrEnum):
    """Structural health state for an artifact in the dependency graph."""

    VALID = "valid"
    STALE = "stale"
    NEEDS_REVISION = "needs_revision"
    NEEDS_REVIEW = "needs_review"
    CONFIRMED_VALID = "confirmed_valid"


class CostRecord(BaseModel):
    """Per-call cost envelope for module execution."""

    model: str
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    estimated_cost_usd: float = Field(ge=0.0)
    latency_seconds: float | None = Field(default=None, ge=0.0)
    request_id: str | None = None


class ArtifactRef(BaseModel):
    """Reference to a specific immutable artifact version."""

    artifact_type: str
    entity_id: str | None = None
    version: int = Field(ge=1)
    path: str

    def key(self) -> str:
        entity_key = self.entity_id or "__project__"
        return f"{self.artifact_type}:{entity_key}:v{self.version}"


class ArtifactMetadata(BaseModel):
    """Audit and lineage metadata attached to every artifact snapshot."""

    ref: ArtifactRef | None = None
    lineage: list[ArtifactRef] = Field(default_factory=list)
    intent: str
    rationale: str
    alternatives_considered: list[str] | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    source: Literal["ai", "human", "hybrid"]
    producing_module: str | None = None
    producing_role: str | None = None
    cost_data: CostRecord | None = None
    annotations: dict[str, Any] = Field(default_factory=dict)
    health: ArtifactHealth = ArtifactHealth.VALID
    schema_version: str = "1.0.0"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Artifact(BaseModel):
    """Persisted artifact snapshot payload."""

    metadata: ArtifactMetadata
    data: dict[str, Any]


class SourceFileInfo(BaseModel):
    """Metadata describing the ingested source file."""

    original_filename: str
    file_size_bytes: int = Field(ge=0)
    character_count: int = Field(ge=0)
    line_count: int = Field(ge=0)
    file_format: Literal["txt", "md", "fountain", "pdf", "fdx", "docx"]


class FormatClassification(BaseModel):
    """Heuristic classification for the ingested input format."""

    detected_format: Literal["screenplay", "prose", "hybrid", "notes", "unknown"]
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)


class RawInput(BaseModel):
    """First immutable artifact preserving source text and format signals."""

    content: str
    source_info: SourceFileInfo
    classification: FormatClassification


class DetectedValue(BaseModel):
    """An auto-detected or defaulted project configuration field."""

    value: Any
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str
    source: Literal["auto_detected", "user_specified", "default"]


class ProjectConfig(BaseModel):
    """Project-level configuration used by all downstream modules and roles."""

    title: str
    format: str
    genre: list[str] = Field(default_factory=list)
    tone: list[str] = Field(default_factory=list)
    estimated_duration_minutes: float | None = Field(default=None, ge=0.0)
    primary_characters: list[str] = Field(default_factory=list)
    supporting_characters: list[str] = Field(default_factory=list)
    location_count: int = Field(ge=0)
    locations_summary: list[str] = Field(default_factory=list)
    target_audience: str | None = None
    aspect_ratio: str
    production_mode: Literal["ai_generated", "irl", "hybrid"]
    human_control_mode: Literal["autonomous", "checkpoint", "advisory"]
    style_packs: dict[str, str] = Field(default_factory=dict)
    budget_cap_usd: float | None = Field(default=None, ge=0.0)
    default_model: str
    detection_details: dict[str, DetectedValue] = Field(default_factory=dict)
    confirmed: bool
    confirmed_at: str | None = None
