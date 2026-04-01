"""Typed project-level creative-brief contracts for visual taste compilation."""

from __future__ import annotations

from pydantic import BaseModel, Field

from .injected_asset import AssetLockStatus


class CreativeBriefProjectReference(BaseModel):
    """One active project reference contributing to the compiled taste stack."""

    asset_id: str = Field(min_length=1)
    filename: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    lock_status: AssetLockStatus
    transparency_note: str = Field(min_length=1)


class VisualCreativeBrief(BaseModel):
    """Read-only, typed summary of project-level visual taste inputs."""

    visual_medium: str | None = None
    mood_descriptors: list[str] = Field(default_factory=list)
    reference_films: list[str] = Field(default_factory=list)
    filmmaker_anchors: list[str] = Field(default_factory=list)
    style_preset_id: str | None = None
    natural_language_intent: str | None = None
    look_notes: str | None = None
    active_project_references: list[CreativeBriefProjectReference] = Field(default_factory=list)
    summary_lines: list[str] = Field(default_factory=list)
    operator_preview: str = ""
    sources_used: list[str] = Field(default_factory=list)

