"""Schemas for editorial direction artifacts (Spec 12.1)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class EditorialDirection(BaseModel):
    """Per-scene editorial direction produced by the Editorial Architect.

    Consumed by shot planning to determine coverage strategy and transition design.
    """

    scene_id: str
    scene_number: int = Field(ge=1)
    heading: str = Field(description="Scene heading for reference (e.g. 'INT. OFFICE - DAY')")

    # Spec 12.1 fields
    scene_function: str = Field(
        description=(
            "Role this scene plays in the narrative arc: inciting incident, "
            "escalation, climax, resolution, transition, exposition, etc."
        )
    )
    pacing_intent: str = Field(
        description=(
            "Intended pace and rhythm — fast/slow, building/releasing tension, "
            "breathing room. Describes internal tempo."
        )
    )
    transition_in: str = Field(
        description=(
            "How to enter this scene: hard cut, dissolve, match cut, "
            "sound bridge, smash cut, fade in, etc."
        )
    )
    transition_in_rationale: str = Field(
        description="Why this entry transition serves the story."
    )
    transition_out: str = Field(
        description=(
            "How to exit this scene: hard cut, dissolve, match cut, "
            "sound bridge, smash cut, fade out, etc."
        )
    )
    transition_out_rationale: str = Field(
        description="Why this exit transition serves the story."
    )
    coverage_priority: str = Field(
        description=(
            "What shot types the editor needs to assemble this scene — "
            "masters, close-ups, inserts, reaction shots, cutaways — and why."
        )
    )
    montage_candidates: list[str] = Field(
        default_factory=list,
        description="Montage sequence candidates within or involving this scene.",
    )
    parallel_editing_notes: str | None = Field(
        default=None,
        description="Cross-cutting or parallel editing opportunities with other scenes.",
    )
    act_level_notes: str | None = Field(
        default=None,
        description=(
            "When scoped to an act: pacing arc, turning points, "
            "and rhythm across scenes."
        ),
    )
    confidence: float = Field(ge=0.0, le=1.0)


class EditorialDirectionIndex(BaseModel):
    """Aggregate index of all per-scene editorial directions for a project."""

    total_scenes: int = Field(ge=0)
    scenes_with_direction: int = Field(ge=0)
    overall_pacing_arc: str = Field(
        description="High-level pacing arc across the entire screenplay."
    )
    act_structure: list[str] = Field(
        default_factory=list,
        description="Identified act boundaries and their editorial character.",
    )
    key_transition_moments: list[str] = Field(
        default_factory=list,
        description="Most significant transitions that define the film's editorial rhythm.",
    )
    montage_sequences: list[str] = Field(
        default_factory=list,
        description="All identified montage sequence candidates across the film.",
    )
    editorial_concerns: list[str] = Field(
        default_factory=list,
        description="Scenes or sequences that may be difficult to edit as written.",
    )
    confidence: float = Field(ge=0.0, le=1.0)
