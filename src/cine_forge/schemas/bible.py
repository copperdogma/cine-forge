"""Schemas for bible artifacts and manifests."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from cine_forge.schemas.scene import SourceSpan


class BibleFileEntry(BaseModel):
    """Reference to a specific file within a bible folder."""

    filename: str
    purpose: Literal[
        "master_definition",
        "evidence",
        "reference_image",
        "continuity_state",
        "role_notes",
        "user_injected",
    ]
    version: int
    provenance: Literal["ai_extracted", "ai_inferred", "user_injected", "system"]
    created_at: datetime = Field(default_factory=datetime.now)


class BibleManifest(BaseModel):
    """Manifest tracking files and versions within an entity's bible folder."""

    entity_type: Literal["character", "location", "prop"]
    entity_id: str
    display_name: str
    files: list[BibleFileEntry] = Field(default_factory=list)
    version: int = Field(ge=1)
    created_at: datetime = Field(default_factory=datetime.now)


class CharacterEvidence(BaseModel):
    """Direct quote and location establishing a character trait."""

    trait: str
    quote: str
    source_scene: str
    source_span: SourceSpan


class InferredTrait(BaseModel):
    """AI-inferred characteristic with rationale and confidence."""

    trait: str
    value: str
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str


class CharacterRelationshipStub(BaseModel):
    """Basic relationship edge between characters (stub for Story 010)."""

    target_character: str
    relationship_type: str
    evidence: str
    confidence: float = Field(ge=0.0, le=1.0)


class CharacterBible(BaseModel):
    """Master definition for a character entity."""

    character_id: str
    name: str
    aliases: list[str] = Field(default_factory=list)
    description: str
    prominence: Literal["primary", "secondary", "minor"] = Field(
        default="secondary",
        description=(
            "Production importance tier. primary = drives the plot (protagonist, "
            "antagonist, key relationships). secondary = recurring supporting with "
            "named role and meaningful dialogue. minor = walk-on, one-scene, "
            "functional (thug, guard, cop)."
        ),
    )
    explicit_evidence: list[CharacterEvidence] = Field(default_factory=list)
    inferred_traits: list[InferredTrait] = Field(default_factory=list)
    scene_presence: list[str] = Field(default_factory=list)
    dialogue_summary: str
    narrative_role: Literal["protagonist", "antagonist", "supporting", "minor"]
    narrative_role_confidence: float = Field(ge=0.0, le=1.0)
    relationships: list[CharacterRelationshipStub] = Field(default_factory=list)
    overall_confidence: float = Field(ge=0.0, le=1.0)


class LocationBible(BaseModel):
    """Master definition for a location entity."""

    location_id: str
    name: str
    aliases: list[str] = Field(default_factory=list)
    description: str
    physical_traits: list[str] = Field(default_factory=list)
    scene_presence: list[str] = Field(default_factory=list)
    narrative_significance: str
    overall_confidence: float = Field(ge=0.0, le=1.0)


class PropBible(BaseModel):
    """Master definition for a prop entity."""

    prop_id: str
    name: str
    description: str
    scene_presence: list[str] = Field(default_factory=list)
    associated_characters: list[str] = Field(
        default_factory=list,
        description=(
            "Slugified entity IDs of characters who primarily own or wield this prop "
            "(signature relationship). Distinct from scene_presence — only characters "
            "with a persistent, continuity-critical association."
        ),
    )
    narrative_significance: str
    overall_confidence: float = Field(ge=0.0, le=1.0)


class EntityDiscoveryResults(BaseModel):
    """Consolidated lists of discovered entity candidates."""

    characters: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    props: list[str] = Field(default_factory=list)
    script_title: str
    processing_metadata: dict[str, Any] = Field(default_factory=dict)
