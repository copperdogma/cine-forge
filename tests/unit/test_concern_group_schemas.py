"""Unit tests for concern group artifact schemas (Story 094)."""

from __future__ import annotations

import pytest

from cine_forge.schemas.concern_groups import (
    CharacterAndPerformance,
    IntentMood,
    LookAndFeel,
    MotifAnnotation,
    RhythmAndFlow,
    RhythmAndFlowIndex,
    SceneCharacterPerformance,
    SoundAndMusic,
    StoryWorld,
)

# ---------------------------------------------------------------------------
# Progressive disclosure: all schemas accept empty construction
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_intent_mood_empty() -> None:
    m = IntentMood()
    assert m.scope == "project"
    assert m.mood_descriptors == []
    assert m.style_preset_id is None
    assert m.user_approved is False


@pytest.mark.unit
def test_look_and_feel_empty() -> None:
    lf = LookAndFeel()
    assert lf.scope == "scene"
    assert lf.lighting_concept is None
    assert lf.visual_motifs == []


@pytest.mark.unit
def test_sound_and_music_empty() -> None:
    sm = SoundAndMusic()
    assert sm.scope == "scene"
    assert sm.silence_placement is None
    assert sm.audio_motifs == []


@pytest.mark.unit
def test_rhythm_and_flow_empty() -> None:
    rf = RhythmAndFlow()
    assert rf.scope == "scene"
    assert rf.scene_function is None
    assert rf.montage_candidates == []


@pytest.mark.unit
def test_character_and_performance_minimal() -> None:
    cp = CharacterAndPerformance(character_id="mariner", scene_id="scene_001")
    assert cp.emotional_state_entering is None
    assert cp.key_beats == []


@pytest.mark.unit
def test_story_world_empty() -> None:
    sw = StoryWorld()
    assert sw.character_design_baselines == []
    assert sw.visual_motif_annotations == []
    assert sw.user_approved is False


# ---------------------------------------------------------------------------
# Full construction with all fields
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_intent_mood_full() -> None:
    m = IntentMood(
        scope="scene",
        scene_id="scene_005",
        mood_descriptors=["tense", "claustrophobic"],
        reference_films=["Das Boot", "Alien"],
        style_preset_id="neo-noir",
        natural_language_intent="Make it feel like the walls are closing in",
        user_approved=True,
    )
    assert m.scope == "scene"
    assert len(m.mood_descriptors) == 2
    assert m.user_approved is True


@pytest.mark.unit
def test_look_and_feel_with_motifs() -> None:
    motif = MotifAnnotation(
        motif_name="Red Door",
        description="Symbolizes the threshold between safety and danger",
        scope="location",
        entity_id="loc_apartment",
        scene_refs=["scene_003", "scene_012"],
    )
    lf = LookAndFeel(
        lighting_concept="Low-key chiaroscuro with motivated practicals",
        color_palette="Desaturated blues and amber highlights",
        camera_personality="Steady, observational — never draws attention to itself",
        visual_motifs=[motif],
    )
    assert len(lf.visual_motifs) == 1
    assert lf.visual_motifs[0].motif_name == "Red Door"


@pytest.mark.unit
def test_rhythm_and_flow_carries_editorial_fields() -> None:
    """RhythmAndFlow preserves all EditorialDirection fields."""
    rf = RhythmAndFlow(
        scope="scene",
        scene_id="scene_001",
        scene_function="inciting incident",
        pacing_intent="Slow build to sudden escalation",
        transition_in="hard cut",
        transition_in_rationale="Clean break from quiet opening",
        transition_out="match cut",
        transition_out_rationale="Visual rhyme connects to next scene",
        coverage_priority="Close-ups for emotional beats, wide for geography",
        camera_movement_dynamics="Static then sudden handheld for the reveal",
        montage_candidates=["morning routine sequence"],
        parallel_editing_notes="Cross-cut with scene_002",
        act_level_notes="End of Act 1 setup",
    )
    assert rf.scene_function == "inciting incident"
    assert rf.camera_movement_dynamics is not None


@pytest.mark.unit
def test_rhythm_and_flow_index() -> None:
    idx = RhythmAndFlowIndex(
        total_scenes=24,
        scenes_with_direction=20,
        overall_pacing_arc="Rising tension through act 2",
        confidence=0.88,
    )
    assert idx.total_scenes == 24
    assert idx.confidence == 0.88


@pytest.mark.unit
def test_scene_character_performance_container() -> None:
    scp = SceneCharacterPerformance(
        scene_id="scene_001",
        entries=[
            CharacterAndPerformance(
                character_id="mariner",
                scene_id="scene_001",
                emotional_state_entering="resigned",
                motivation="Survive the storm",
            ),
            CharacterAndPerformance(
                character_id="helen",
                scene_id="scene_001",
                emotional_state_entering="determined",
            ),
        ],
    )
    assert len(scp.entries) == 2
    assert scp.entries[0].motivation == "Survive the storm"


@pytest.mark.unit
def test_story_world_with_baselines_and_motifs() -> None:
    sw = StoryWorld(
        character_design_baselines=["mariner", "helen", "deacon"],
        location_design_baselines=["atoll", "smokers_ship"],
        continuity_override_notes="Dream sequence in scene 15 — ignore normal continuity",
        visual_motif_annotations=[
            MotifAnnotation(
                motif_name="Water Level",
                description="Rising water = rising tension",
                scope="world",
            ),
        ],
    )
    assert len(sw.character_design_baselines) == 3
    assert sw.continuity_override_notes is not None


# ---------------------------------------------------------------------------
# Serialization round-trip
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_round_trip_json() -> None:
    """All schemas survive JSON serialization and deserialization."""
    schemas = [
        IntentMood(mood_descriptors=["epic"], natural_language_intent="Go big"),
        LookAndFeel(lighting_concept="High key"),
        SoundAndMusic(ambient_environment="Ocean waves"),
        RhythmAndFlow(scene_function="climax", pacing_intent="Fast"),
        StoryWorld(character_design_baselines=["hero"]),
    ]
    for schema in schemas:
        json_str = schema.model_dump_json()
        restored = type(schema).model_validate_json(json_str)
        assert restored == schema
