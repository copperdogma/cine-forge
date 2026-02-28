"""Schema for the script bible artifact (Spec §4.5).

The script bible is the first story-lane artifact derived from the script.
It captures the macro-level story understanding: logline, synopsis, act structure,
themes, narrative arc, and genre/tone. Every downstream role and concern group
references this as "what is this story about?"
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ActStructure(BaseModel):
    """One act within the screenplay's dramatic structure."""

    act_number: int = Field(ge=1)
    title: str = Field(description="Short label, e.g. 'Setup', 'Confrontation', 'Resolution'")
    start_scene: str = Field(description="Scene heading or description marking act start")
    end_scene: str = Field(description="Scene heading or description marking act end")
    summary: str = Field(description="1-2 sentence summary of what happens in this act")
    turning_points: list[str] = Field(
        default_factory=list,
        description="Key turning points / plot beats within this act",
    )


class ThematicElement(BaseModel):
    """A theme identified in the screenplay."""

    theme: str = Field(description="Theme name, e.g. 'Redemption', 'Loss of innocence'")
    description: str = Field(description="How this theme manifests in the story")
    evidence: list[str] = Field(
        default_factory=list,
        description="Scene references or quotes supporting this theme",
    )


class ScriptBible(BaseModel):
    """High-level story understanding derived from the canonical script.

    Project-scoped (entity_id='project'). Produced by script_bible_v1 module.
    """

    title: str = Field(description="Title of the screenplay")
    logline: str = Field(description="One-sentence summary of the story")
    synopsis: str = Field(description="1-3 paragraph synopsis")
    act_structure: list[ActStructure] = Field(
        description="Dramatic structure broken into acts with turning points"
    )
    themes: list[ThematicElement] = Field(
        description="Major thematic concerns identified in the script"
    )
    narrative_arc: str = Field(
        description="Overall story shape — setup, confrontation, resolution pattern"
    )
    genre: str = Field(description="Primary genre, e.g. 'Action-Thriller', 'Drama'")
    tone: str = Field(
        description="Dominant tone, e.g. 'Gritty and intense', 'Darkly comedic'"
    )
    protagonist_journey: str = Field(
        description="The protagonist's transformation arc across the story"
    )
    central_conflict: str = Field(
        description="The core dramatic conflict driving the narrative"
    )
    setting_overview: str = Field(
        description="Time period, location context, and world-building essentials"
    )
    confidence: float = Field(ge=0.0, le=1.0, description="Overall extraction confidence")
