"""Schemas for semantic impact assessment artifacts."""

from __future__ import annotations

from pydantic import BaseModel, Field

from .models import ArtifactRef, CostRecord


class ArtifactImpact(BaseModel):
    """Assessment result for one downstream artifact."""

    artifact_ref: ArtifactRef
    previous_health: str = Field(default="stale")
    assessed_health: str = Field(pattern="^(needs_revision|confirmed_valid)$")
    rationale: str = Field(min_length=1)
    upstream_change_summary: str = Field(min_length=1)
    suggested_revision: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    assessing_role: str = Field(min_length=1)


class ImpactAssessment(BaseModel):
    """Immutable record of a semantic impact assessment run."""

    trigger_artifact_ref: ArtifactRef
    trigger_diff_summary: str = Field(min_length=1)
    assessments: list[ArtifactImpact] = Field(default_factory=list)
    total_stale: int = Field(ge=0)
    total_needs_revision: int = Field(ge=0)
    total_confirmed_valid: int = Field(ge=0)
    assessment_cost: CostRecord
