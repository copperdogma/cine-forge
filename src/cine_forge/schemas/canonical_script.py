"""Schema for canonical screenplay artifact output."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Invention(BaseModel):
    """Something the AI added that was not explicit in the source."""

    description: str
    location: str
    rationale: str


class Assumption(BaseModel):
    """Interpretive choice made during normalization."""

    description: str
    rationale: str
    alternatives_considered: list[str] = Field(default_factory=list)


class NormalizationMetadata(BaseModel):
    """Transparency envelope for normalization behavior."""

    source_format: str
    strategy: str
    inventions: list[Invention] = Field(default_factory=list)
    assumptions: list[Assumption] = Field(default_factory=list)
    overall_confidence: float = Field(ge=0.0, le=1.0)
    rationale: str


class CanonicalScript(BaseModel):
    """Human-readable canonical screenplay text."""

    title: str
    script_text: str
    line_count: int = Field(ge=0)
    scene_count: int = Field(ge=0)
    normalization: NormalizationMetadata
