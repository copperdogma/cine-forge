"""Scene readiness computation per concern group (Spec §12.7).

Given a scene and its concern group artifacts, compute red/yellow/green
readiness state per group. This is creative completeness — distinct from
pipeline node status (NodeStatus in pipeline/graph.py).

Red    = no user input for this group in this scene
Yellow = some guidance exists (partial fields, or AI-propagated defaults)
Green  = user has explicitly reviewed and approved
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ReadinessState(StrEnum):
    """Creative readiness level for a concern group on a specific scene."""

    RED = "red"
    YELLOW = "yellow"
    GREEN = "green"


class SceneReadiness(BaseModel):
    """Readiness state for all concern groups on a single scene."""

    scene_id: str
    intent_mood: ReadinessState = Field(default=ReadinessState.RED)
    look_and_feel: ReadinessState = Field(default=ReadinessState.RED)
    sound_and_music: ReadinessState = Field(default=ReadinessState.RED)
    rhythm_and_flow: ReadinessState = Field(default=ReadinessState.RED)
    character_and_performance: ReadinessState = Field(default=ReadinessState.RED)
    story_world: ReadinessState = Field(default=ReadinessState.RED)


def _compute_group_readiness(
    data: dict[str, Any] | None,
    yellow_fields: list[str],
) -> ReadinessState:
    """Compute readiness for a single concern group.

    Args:
        data: The artifact's data dict (None if no artifact exists).
        yellow_fields: Field names — if ANY are non-empty, the group is yellow.

    Returns:
        GREEN if user_approved is True, YELLOW if any yellow_field has content,
        RED otherwise.
    """
    if data is None:
        return ReadinessState.RED

    if data.get("user_approved"):
        return ReadinessState.GREEN

    for field_name in yellow_fields:
        value = data.get(field_name)
        if value is not None and value != "" and value != []:
            return ReadinessState.YELLOW

    return ReadinessState.RED


def compute_scene_readiness(
    scene_id: str,
    artifacts: dict[str, dict[str, Any] | None],
) -> SceneReadiness:
    """Compute creative readiness for all concern groups on a scene.

    Args:
        scene_id: The scene to compute readiness for.
        artifacts: Map of concern group name to artifact data dict (or None).
            Expected keys: 'intent_mood', 'look_and_feel', 'sound_and_music',
            'rhythm_and_flow', 'character_and_performance', 'story_world'.

    Returns:
        SceneReadiness with per-group red/yellow/green states.
    """
    return SceneReadiness(
        scene_id=scene_id,
        intent_mood=_compute_group_readiness(
            artifacts.get("intent_mood"),
            ["mood_descriptors", "style_preset_id", "natural_language_intent"],
        ),
        look_and_feel=_compute_group_readiness(
            artifacts.get("look_and_feel"),
            ["lighting_concept", "color_palette", "camera_personality"],
        ),
        sound_and_music=_compute_group_readiness(
            artifacts.get("sound_and_music"),
            ["ambient_environment", "music_intent", "emotional_soundscape"],
        ),
        rhythm_and_flow=_compute_group_readiness(
            artifacts.get("rhythm_and_flow"),
            ["scene_function", "pacing_intent", "transition_in", "coverage_priority"],
        ),
        character_and_performance=_compute_group_readiness(
            artifacts.get("character_and_performance"),
            ["entries"],
        ),
        story_world=_compute_group_readiness(
            artifacts.get("story_world"),
            ["character_design_baselines", "location_design_baselines", "visual_motif_annotations"],
        ),
    )
