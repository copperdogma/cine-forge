"""Schemas for LLM-first entity adjudication decisions."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

EntityType = Literal["character", "location", "prop"]
EntityVerdict = Literal["valid", "invalid", "retype"]


class EntityAdjudicationDecision(BaseModel):
    """Decision for one candidate entity."""

    candidate: str = Field(min_length=1)
    verdict: EntityVerdict
    canonical_name: str | None = None
    target_entity_type: EntityType | None = None
    rationale: str
    confidence: float = Field(ge=0.0, le=1.0)


class EntityAdjudicationBatch(BaseModel):
    """Batched adjudication payload returned by the LLM."""

    decisions: list[EntityAdjudicationDecision] = Field(default_factory=list)
