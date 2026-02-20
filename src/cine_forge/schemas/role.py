"""Role-system schemas for hierarchy, runtime responses, and style packs."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field

from .models import CostRecord


class RoleTier(StrEnum):
    """Hierarchy tier used for role authority and gating."""

    CANON_AUTHORITY = "canon_authority"
    CANON_GUARDIAN = "canon_guardian"
    STRUCTURAL_ADVISOR = "structural_advisor"
    PERFORMANCE = "performance"


class PerceptionCapability(StrEnum):
    """Media modalities a role can reason over."""

    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO_VIDEO = "audio+video"


class StylePackSlot(StrEnum):
    """Whether a role accepts a style pack selection."""

    ACCEPTS = "accepts"
    FORBIDDEN = "forbidden"


class RoleDefinition(BaseModel):
    """Structured definition for an AI role persona."""

    role_id: str = Field(min_length=2)
    display_name: str = Field(min_length=2)
    tier: RoleTier
    description: str = Field(min_length=8)
    system_prompt: str = Field(min_length=20)
    capabilities: list[PerceptionCapability] = Field(min_length=1)
    style_pack_slot: StylePackSlot
    permissions: list[str] = Field(default_factory=list)


class StylePackFileRef(BaseModel):
    """Manifest entry for a style-pack file."""

    kind: Literal["description", "reference_image", "frame_grab", "palette", "notes"]
    path: str = Field(min_length=1)
    caption: str | None = None


class StylePack(BaseModel):
    """Folder-based style pack manifest plus prompt material."""

    style_pack_id: str = Field(min_length=1)
    role_id: str = Field(min_length=2)
    display_name: str = Field(min_length=2)
    summary: str = Field(min_length=8)
    prompt_injection: str = Field(min_length=8)
    files: list[StylePackFileRef] = Field(default_factory=list)


class RoleResponse(BaseModel):
    """Standardized role invocation response envelope."""

    role_id: str
    content: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str = Field(min_length=1)
    cost_data: CostRecord | None = None
