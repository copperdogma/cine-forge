"""Schemas for entity relationship graph artifacts."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class EntityEdge(BaseModel):
    """A typed relationship edge between two entities."""

    source_type: Literal["character", "location", "prop"]
    source_id: str
    target_type: Literal["character", "location", "prop"]
    target_id: str
    relationship_type: str
    direction: Literal["symmetric", "source_to_target", "target_to_source"]
    evidence: list[str] = Field(default_factory=list)
    scene_refs: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


class EntityGraph(BaseModel):
    """Master graph artifact connecting all entities."""

    edges: list[EntityEdge] = Field(default_factory=list)
    entity_count: dict[str, int] = Field(default_factory=dict)
    edge_count: int = 0
    extraction_confidence: float = Field(ge=0.0, le=1.0)
