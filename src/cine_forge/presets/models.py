"""Style preset schema — a named vibe package that sets coherent defaults
across all five concern groups simultaneously (Spec §12.1, ADR-003 Decision #9).

These are NOT the same as per-role style packs (in src/cine_forge/roles/style_packs/).
Vibe presets are higher-level: they map mood → concern group hints for ALL groups,
whereas style packs inject personality into a single role's system prompt.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class StylePreset(BaseModel):
    """A named starting point that populates IntentMood fields and seeds
    concern group defaults for propagation."""

    preset_id: str = Field(description="Unique kebab-case identifier")
    display_name: str = Field(description="Human-readable title")
    description: str = Field(description="1-2 sentence creative summary")
    mood_descriptors: list[str] = Field(
        description="Default mood tags when this preset is selected"
    )
    reference_films: list[str] = Field(
        default_factory=list,
        description="Canonical film references for this vibe",
    )
    thumbnail_emoji: str = Field(
        description="Emoji for UI card display (single character)"
    )
    concern_group_hints: dict[str, dict[str, str]] = Field(
        description=(
            "Per-concern-group suggested defaults. Keys are concern group IDs "
            "(look_and_feel, sound_and_music, rhythm_and_flow, "
            "character_and_performance, story_world). Values are dicts mapping "
            "field names to suggested string values."
        ),
    )
