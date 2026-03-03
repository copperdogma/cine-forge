"""Factory for the artifact schema registry used by DriverEngine."""

from __future__ import annotations

from cine_forge.schemas import (
    BibleManifest,
    CanonicalScript,
    CharacterAndPerformance,
    CharacterBible,
    ContinuityIndex,
    ContinuityState,
    Conversation,
    Decision,
    DisagreementArtifact,
    EntityDiscoveryResults,
    EntityEdge,
    EntityGraph,
    IntentMood,
    LocationBible,
    LookAndFeel,
    LookAndFeelIndex,
    ProjectConfig,
    PropBible,
    QAResult,
    RawInput,
    RhythmAndFlow,
    RhythmAndFlowIndex,
    RoleDefinition,
    RoleResponse,
    Scene,
    SceneCharacterPerformance,
    SceneIndex,
    SchemaRegistry,
    ScriptBible,
    SoundAndMusic,
    SoundAndMusicIndex,
    StageReviewArtifact,
    StoryWorld,
    StylePack,
    Suggestion,
    Timeline,
    TrackManifest,
)


def build_schema_registry() -> SchemaRegistry:
    """Create and populate the artifact schema registry with all known types."""
    registry = SchemaRegistry()
    registry.register("dict", dict)
    registry.register("raw_input", RawInput)
    registry.register("canonical_script", CanonicalScript)
    registry.register("scene", Scene)
    registry.register("scene_index", SceneIndex)
    registry.register("timeline", Timeline)
    registry.register("track_manifest", TrackManifest)
    registry.register("project_config", ProjectConfig)
    registry.register("bible_manifest", BibleManifest)
    registry.register("character_bible", CharacterBible)
    registry.register("location_bible", LocationBible)
    registry.register("prop_bible", PropBible)
    registry.register("entity_discovery_results", EntityDiscoveryResults)
    registry.register("entity_edge", EntityEdge)
    registry.register("entity_graph", EntityGraph)
    registry.register("continuity_state", ContinuityState)
    registry.register("continuity_index", ContinuityIndex)
    registry.register("qa_result", QAResult)
    registry.register("role_definition", RoleDefinition)
    registry.register("role_response", RoleResponse)
    registry.register("style_pack", StylePack)
    registry.register("stage_review", StageReviewArtifact)
    registry.register("suggestion", Suggestion)
    registry.register("decision", Decision)
    registry.register("conversation", Conversation)
    registry.register("disagreement", DisagreementArtifact)
    registry.register("intent_mood", IntentMood)
    registry.register("look_and_feel", LookAndFeel)
    registry.register("look_and_feel_index", LookAndFeelIndex)
    registry.register("sound_and_music", SoundAndMusic)
    registry.register("sound_and_music_index", SoundAndMusicIndex)
    registry.register("rhythm_and_flow", RhythmAndFlow)
    registry.register("rhythm_and_flow_index", RhythmAndFlowIndex)
    registry.register("character_and_performance", CharacterAndPerformance)
    registry.register("scene_character_performance", SceneCharacterPerformance)
    registry.register("story_world", StoryWorld)
    registry.register("script_bible", ScriptBible)
    return registry
