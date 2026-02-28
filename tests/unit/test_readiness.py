"""Unit tests for scene readiness computation (Story 094, Spec §12.7)."""

from __future__ import annotations

import pytest

from cine_forge.schemas.readiness import (
    ReadinessState,
    SceneReadiness,
    compute_scene_readiness,
)


@pytest.mark.unit
def test_all_red_when_no_artifacts() -> None:
    """All groups are red when no artifacts exist."""
    result = compute_scene_readiness("scene_001", {})
    assert result.scene_id == "scene_001"
    assert result.intent_mood == ReadinessState.RED
    assert result.look_and_feel == ReadinessState.RED
    assert result.sound_and_music == ReadinessState.RED
    assert result.rhythm_and_flow == ReadinessState.RED
    assert result.character_and_performance == ReadinessState.RED
    assert result.story_world == ReadinessState.RED


@pytest.mark.unit
def test_all_red_when_artifacts_are_none() -> None:
    """Explicitly None artifacts are treated as missing."""
    result = compute_scene_readiness("scene_001", {
        "intent_mood": None,
        "look_and_feel": None,
        "sound_and_music": None,
        "rhythm_and_flow": None,
        "character_and_performance": None,
        "story_world": None,
    })
    assert result.intent_mood == ReadinessState.RED
    assert result.rhythm_and_flow == ReadinessState.RED


@pytest.mark.unit
def test_all_red_when_artifacts_empty() -> None:
    """Empty artifacts (no yellow-trigger fields set) are red."""
    result = compute_scene_readiness("scene_001", {
        "intent_mood": {"scope": "scene"},
        "look_and_feel": {"scope": "scene"},
        "sound_and_music": {"scope": "scene"},
        "rhythm_and_flow": {"scope": "scene"},
        "character_and_performance": {},
        "story_world": {},
    })
    assert result.intent_mood == ReadinessState.RED
    assert result.look_and_feel == ReadinessState.RED


@pytest.mark.unit
def test_yellow_intent_mood_with_descriptors() -> None:
    result = compute_scene_readiness("scene_001", {
        "intent_mood": {"mood_descriptors": ["tense", "intimate"]},
    })
    assert result.intent_mood == ReadinessState.YELLOW


@pytest.mark.unit
def test_yellow_intent_mood_with_preset() -> None:
    result = compute_scene_readiness("scene_001", {
        "intent_mood": {"style_preset_id": "neo-noir"},
    })
    assert result.intent_mood == ReadinessState.YELLOW


@pytest.mark.unit
def test_yellow_look_and_feel() -> None:
    result = compute_scene_readiness("scene_001", {
        "look_and_feel": {"lighting_concept": "Low-key chiaroscuro"},
    })
    assert result.look_and_feel == ReadinessState.YELLOW


@pytest.mark.unit
def test_yellow_sound_and_music() -> None:
    result = compute_scene_readiness("scene_001", {
        "sound_and_music": {"ambient_environment": "Rain on tin roof"},
    })
    assert result.sound_and_music == ReadinessState.YELLOW


@pytest.mark.unit
def test_yellow_rhythm_and_flow() -> None:
    result = compute_scene_readiness("scene_001", {
        "rhythm_and_flow": {
            "scene_function": "climax",
            "pacing_intent": "fast",
        },
    })
    assert result.rhythm_and_flow == ReadinessState.YELLOW


@pytest.mark.unit
def test_yellow_character_and_performance() -> None:
    """Character group is yellow when entries list is non-empty."""
    result = compute_scene_readiness("scene_001", {
        "character_and_performance": {
            "entries": [
                {"character_id": "mariner", "emotional_state_entering": "resigned"},
            ],
        },
    })
    assert result.character_and_performance == ReadinessState.YELLOW


@pytest.mark.unit
def test_yellow_story_world() -> None:
    result = compute_scene_readiness("scene_001", {
        "story_world": {
            "character_design_baselines": ["mariner", "helen"],
        },
    })
    assert result.story_world == ReadinessState.YELLOW


@pytest.mark.unit
def test_green_when_user_approved() -> None:
    """All groups go green when user_approved is True."""
    result = compute_scene_readiness("scene_001", {
        "intent_mood": {"mood_descriptors": ["tense"], "user_approved": True},
        "look_and_feel": {"lighting_concept": "Hard light", "user_approved": True},
        "sound_and_music": {"ambient_environment": "Silence", "user_approved": True},
        "rhythm_and_flow": {"scene_function": "climax", "user_approved": True},
        "character_and_performance": {"entries": [{"character_id": "a"}], "user_approved": True},
        "story_world": {"character_design_baselines": ["a"], "user_approved": True},
    })
    assert result.intent_mood == ReadinessState.GREEN
    assert result.look_and_feel == ReadinessState.GREEN
    assert result.sound_and_music == ReadinessState.GREEN
    assert result.rhythm_and_flow == ReadinessState.GREEN
    assert result.character_and_performance == ReadinessState.GREEN
    assert result.story_world == ReadinessState.GREEN


@pytest.mark.unit
def test_mixed_readiness() -> None:
    """Realistic scenario with mixed readiness states."""
    result = compute_scene_readiness("scene_007", {
        "intent_mood": {"mood_descriptors": ["dark"], "user_approved": True},
        "look_and_feel": {"color_palette": "Desaturated"},
        "sound_and_music": None,
        "rhythm_and_flow": {
            "scene_function": "escalation",
            "pacing_intent": "building",
            "user_approved": True,
        },
    })
    assert result.intent_mood == ReadinessState.GREEN
    assert result.look_and_feel == ReadinessState.YELLOW
    assert result.sound_and_music == ReadinessState.RED
    assert result.rhythm_and_flow == ReadinessState.GREEN
    assert result.character_and_performance == ReadinessState.RED
    assert result.story_world == ReadinessState.RED


@pytest.mark.unit
def test_scene_readiness_model() -> None:
    """SceneReadiness can be constructed and serialized."""
    sr = SceneReadiness(
        scene_id="scene_001",
        intent_mood=ReadinessState.GREEN,
        look_and_feel=ReadinessState.YELLOW,
    )
    data = sr.model_dump()
    assert data["intent_mood"] == "green"
    assert data["look_and_feel"] == "yellow"
    assert data["sound_and_music"] == "red"  # default
