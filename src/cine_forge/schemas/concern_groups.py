"""Concern group artifact schemas (Spec §12.1–12.6, ADR-003).

Six concern groups replace the old role-based direction types:
- IntentMood (§12.1) — global tone/mood, propagates defaults to all groups
- LookAndFeel (§12.2) — visual direction: lighting, color, composition, camera
- SoundAndMusic (§12.3) — audio direction: ambient, score, silence, motifs
- RhythmAndFlow (§12.4) — editorial direction: pacing, transitions, coverage
- CharacterAndPerformance (§12.5) — per-character emotional/physical direction
- StoryWorld (§12.6) — entity baselines, continuity overrides, motif annotations

All fields are optional (progressive disclosure). AI fills what user doesn't specify.
Readiness computation (§12.7) lives in readiness.py.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Shared types
# ---------------------------------------------------------------------------

ConcernScope = Literal["project", "scene"]


class MotifAnnotation(BaseModel):
    """A recurring visual or audio motif with thematic meaning (§12.6)."""

    motif_name: str = Field(description="Short name, e.g. 'Red Door', 'Clock Ticking'")
    description: str = Field(description="What this motif represents thematically")
    scope: Literal["world", "character", "location"] = Field(
        default="world",
        description="Whether this motif is global or tied to a specific entity",
    )
    entity_id: str | None = Field(
        default=None,
        description="Entity this motif is attached to (when scope is character/location)",
    )
    scene_refs: list[str] = Field(
        default_factory=list,
        description="Scene IDs where this motif appears",
    )


# ---------------------------------------------------------------------------
# §12.1 — Intent / Mood
# ---------------------------------------------------------------------------

class IntentMood(BaseModel):
    """Global tone and mood — the primary interaction surface for beginners (§12.1).

    Changes auto-propagate suggested defaults to all five concern groups.
    Scoped project-wide or per-scene override.
    """

    scope: ConcernScope = Field(default="project")
    scene_id: str | None = Field(default=None, description="Set when scope='scene'")

    mood_descriptors: list[str] = Field(
        default_factory=list,
        description="Emotional tags: tense, warm, chaotic, dreamy, epic, intimate, raw, unsettling",
    )
    reference_films: list[str] = Field(
        default_factory=list,
        description="Titles, directors, aesthetic references (e.g. 'like Blade Runner')",
    )
    style_preset_id: str | None = Field(
        default=None,
        description="Named style package that sets coherent defaults across all groups",
    )
    natural_language_intent: str | None = Field(
        default=None,
        description="Free-text direction (e.g. 'make this scene darker and tenser')",
    )
    user_approved: bool = Field(
        default=False,
        description="Whether a user has explicitly reviewed and approved this",
    )


# ---------------------------------------------------------------------------
# §12.2 — Look & Feel
# ---------------------------------------------------------------------------

class LookAndFeel(BaseModel):
    """Visual direction — lighting, color, composition, camera, design (§12.2).

    Primary contributor: Visual Architect role.
    Scoped project-wide or per-scene.
    """

    scope: ConcernScope = Field(default="scene")
    scene_id: str | None = Field(default=None)

    lighting_concept: str | None = Field(
        default=None,
        description=(
            "Key light direction, quality (hard/soft), "
            "motivated vs. stylized, practical sources"
        ),
    )
    color_palette: str | None = Field(
        default=None,
        description="Dominant colors, temperature, saturation, contrast",
    )
    composition_philosophy: str | None = Field(
        default=None,
        description="Symmetry, negative space, depth of field, framing style",
    )
    camera_personality: str | None = Field(
        default=None,
        description="Static/controlled vs. handheld/chaotic, observational vs. intimate",
    )
    reference_imagery: list[str] = Field(
        default_factory=list,
        description="Style pack refs, user-injected images, or AI-suggested references",
    )
    costume_notes: str | None = Field(
        default=None,
        description="Character appearance and wardrobe, referencing bible states",
    )
    production_design_notes: str | None = Field(
        default=None,
        description="Set design and environment details",
    )
    visual_motifs: list[MotifAnnotation] = Field(
        default_factory=list,
        description="Recurring visual elements connecting to larger themes",
    )
    aspect_ratio_override: str | None = Field(
        default=None,
        description="Only set when overriding project-wide aspect ratio",
    )
    user_approved: bool = Field(default=False)


# ---------------------------------------------------------------------------
# §12.3 — Sound & Music
# ---------------------------------------------------------------------------

class SoundAndMusic(BaseModel):
    """Audio direction — ambient, emotional soundscape, silence, score (§12.3).

    Primary contributor: Sound Designer role.
    Silence is a first-class element, not the absence of direction.
    """

    scope: ConcernScope = Field(default="scene")
    scene_id: str | None = Field(default=None)

    ambient_environment: str | None = Field(
        default=None,
        description="Baseline soundscape: city noise, wind, silence, machinery hum",
    )
    emotional_soundscape: str | None = Field(
        default=None,
        description="How sound supports the scene's emotional arc",
    )
    silence_placement: str | None = Field(
        default=None,
        description="Intentional absence of sound — where and why",
    )
    offscreen_audio_cues: list[str] = Field(
        default_factory=list,
        description="Sounds from outside frame that expand world or foreshadow",
    )
    sound_driven_transitions: str | None = Field(
        default=None,
        description="Audio bridges, stingers, or motifs connecting to adjacent scenes",
    )
    music_intent: str | None = Field(
        default=None,
        description="Score direction: tension, release, theme, absence of score",
    )
    diegetic_non_diegetic_notes: str | None = Field(
        default=None,
        description="What sounds exist in story world vs. for audience only",
    )
    audio_motifs: list[MotifAnnotation] = Field(
        default_factory=list,
        description="Recurring sound elements with thematic meaning",
    )
    user_approved: bool = Field(default=False)


# ---------------------------------------------------------------------------
# §12.4 — Rhythm & Flow (replaces EditorialDirection)
# ---------------------------------------------------------------------------

class RhythmAndFlow(BaseModel):
    """Editorial direction — pacing, transitions, coverage, montage (§12.4).

    Primary contributor: Editorial Architect role.
    UI label for non-filmmakers: 'Pace & Energy'.

    This schema replaces EditorialDirection (Story 020). All fields from
    EditorialDirection are preserved here; scene_number and heading are dropped
    (they live in Scene/SceneIndex).
    """

    scope: Literal["project", "scene", "act"] = Field(default="scene")
    scene_id: str | None = Field(default=None)
    act_number: int | None = Field(default=None, description="Set when scope='act'")

    scene_function: str | None = Field(
        default=None,
        description=(
            "Role this scene plays in the narrative arc: inciting incident, "
            "escalation, climax, resolution, transition, exposition"
        ),
    )
    pacing_intent: str | None = Field(
        default=None,
        description="Intended pace — fast/slow, building/releasing tension, breathing room",
    )
    transition_in: str | None = Field(
        default=None,
        description="How to enter this scene: hard cut, dissolve, match cut, sound bridge",
    )
    transition_in_rationale: str | None = Field(
        default=None,
        description="Why this entry transition serves the story",
    )
    transition_out: str | None = Field(
        default=None,
        description="How to exit this scene: hard cut, dissolve, match cut, fade out",
    )
    transition_out_rationale: str | None = Field(
        default=None,
        description="Why this exit transition serves the story",
    )
    coverage_priority: str | None = Field(
        default=None,
        description=(
            "What shot types the editor needs — "
            "masters, close-ups, inserts, reaction shots"
        ),
    )
    camera_movement_dynamics: str | None = Field(
        default=None,
        description="Speed, energy, type of movement (distinct from composition in LookAndFeel)",
    )
    montage_candidates: list[str] = Field(
        default_factory=list,
        description="Montage sequence candidates within or involving this scene",
    )
    parallel_editing_notes: str | None = Field(
        default=None,
        description="Cross-cutting or parallel editing opportunities with other scenes",
    )
    act_level_notes: str | None = Field(
        default=None,
        description="When scoped to an act: pacing arc, turning points, rhythm across scenes",
    )
    user_approved: bool = Field(default=False)


class RhythmAndFlowIndex(BaseModel):
    """Aggregate index of all per-scene rhythm & flow direction for a project.

    Replaces EditorialDirectionIndex.
    """

    total_scenes: int = Field(ge=0)
    scenes_with_direction: int = Field(ge=0)
    overall_pacing_arc: str = Field(
        description="High-level pacing arc across the entire screenplay"
    )
    act_structure: list[str] = Field(
        default_factory=list,
        description="Identified act boundaries and their editorial character",
    )
    key_transition_moments: list[str] = Field(
        default_factory=list,
        description="Most significant transitions that define the film's editorial rhythm",
    )
    montage_sequences: list[str] = Field(
        default_factory=list,
        description="All identified montage sequence candidates across the film",
    )
    editorial_concerns: list[str] = Field(
        default_factory=list,
        description="Scenes or sequences that may be difficult to edit as written",
    )
    confidence: float = Field(ge=0.0, le=1.0)


# ---------------------------------------------------------------------------
# §12.5 — Character & Performance
# ---------------------------------------------------------------------------

class CharacterAndPerformance(BaseModel):
    """Per-character emotional and physical direction for a scene (§12.5).

    Contributors: Actor Agents (per character), reviewed by Director.
    Contingent on Story 023 — may close if character bibles + chat suffice.
    """

    character_id: str = Field(description="Which character this entry covers")
    scene_id: str = Field(description="Scene this direction applies to")

    emotional_state_entering: str | None = Field(
        default=None,
        description="Emotional state at scene start",
    )
    emotional_arc: str | None = Field(
        default=None,
        description="How emotional state changes through the scene",
    )
    motivation: str | None = Field(
        default=None,
        description="What the character wants in this scene",
    )
    subtext: str | None = Field(
        default=None,
        description="What they are not saying",
    )
    physical_notes: str | None = Field(
        default=None,
        description="Posture, energy level, gestures, habits",
    )
    key_beats: list[str] = Field(
        default_factory=list,
        description="Moments of change, realization, decision",
    )
    relationship_dynamics: str | None = Field(
        default=None,
        description="How this character relates to others present",
    )
    dialogue_delivery_notes: str | None = Field(
        default=None,
        description="Tone, pace, emphasis for specific lines",
    )
    blocking_notes: str | None = Field(
        default=None,
        description="Character positions and movement within the scene",
    )
    user_approved: bool = Field(default=False)


class SceneCharacterPerformance(BaseModel):
    """Container for all character performance directions in a single scene."""

    scene_id: str
    entries: list[CharacterAndPerformance] = Field(
        default_factory=list,
        description="One entry per character in the scene",
    )


# ---------------------------------------------------------------------------
# §12.6 — Story World
# ---------------------------------------------------------------------------

class StoryWorld(BaseModel):
    """Cross-scene continuity and entity design baselines (§12.6).

    Project-wide scope. CineForge's primary differentiator — consistency
    of character appearance, location design, and thematic motifs across scenes.
    """

    character_design_baselines: list[str] = Field(
        default_factory=list,
        description="Character bible entity IDs serving as design references",
    )
    location_design_baselines: list[str] = Field(
        default_factory=list,
        description="Location bible entity IDs serving as design references",
    )
    prop_design_baselines: list[str] = Field(
        default_factory=list,
        description="Prop bible entity IDs serving as design references",
    )
    continuity_override_notes: str | None = Field(
        default=None,
        description="Deliberate creative breaks: dream sequences, surreal transitions",
    )
    character_behavioral_consistency_notes: str | None = Field(
        default=None,
        description="Cross-scene behavioral rules for characters",
    )
    narrative_rhythm_notes: str | None = Field(
        default=None,
        description="Rhythm across acts — pacing of world revelation",
    )
    visual_motif_annotations: list[MotifAnnotation] = Field(
        default_factory=list,
        description="Visual motifs at world, character, or location scope",
    )
    audio_motif_annotations: list[MotifAnnotation] = Field(
        default_factory=list,
        description="Audio motifs at world, character, or location scope",
    )
    user_approved: bool = Field(default=False)
