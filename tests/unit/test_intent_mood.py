"""Unit tests for the intent/mood layer: presets, propagation, pipeline module."""

from __future__ import annotations

from typing import Any

import pytest

from cine_forge.presets import StylePreset, list_presets, load_preset
from cine_forge.schemas.concern_groups import IntentMood
from cine_forge.services.intent_mood import PropagatedGroup, PropagationResult

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _scene_index_payload() -> dict[str, Any]:
    return {
        "total_scenes": 2,
        "unique_characters": ["ALICE", "BOB"],
        "unique_locations": ["STUDIO", "PARK"],
        "estimated_runtime_minutes": 2.0,
        "scenes_passed_qa": 2,
        "scenes_need_review": 0,
        "entries": [
            {
                "scene_id": "scene_001",
                "scene_number": 1,
                "heading": "INT. STUDIO - DAY",
                "location": "STUDIO",
                "time_of_day": "DAY",
                "characters_present": ["ALICE"],
                "characters_present_ids": ["alice"],
                "props_mentioned": [],
                "tone_mood": "warm",
                "source_span": {"start_line": 1, "end_line": 4},
            },
            {
                "scene_id": "scene_002",
                "scene_number": 2,
                "heading": "EXT. PARK - NIGHT",
                "location": "PARK",
                "time_of_day": "NIGHT",
                "characters_present": ["BOB"],
                "characters_present_ids": ["bob"],
                "props_mentioned": [],
                "tone_mood": "tense",
                "source_span": {"start_line": 5, "end_line": 8},
            },
        ],
    }


def _canonical_script_payload() -> dict[str, Any]:
    return {
        "format": "fountain",
        "script_text": (
            "INT. STUDIO - DAY\n\nALICE sits at a desk.\n\n"
            "EXT. PARK - NIGHT\n\nBOB walks alone.\n"
        ),
        "metadata": {},
    }


# ---------------------------------------------------------------------------
# T1: Style preset catalog
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestStylePresets:
    """Verify the built-in style preset catalog loads correctly."""

    def test_list_presets_returns_all_six(self) -> None:
        presets = list_presets()
        assert len(presets) == 6

    def test_preset_ids_are_unique(self) -> None:
        presets = list_presets()
        ids = [p.preset_id for p in presets]
        assert len(ids) == len(set(ids))

    def test_each_preset_has_required_fields(self) -> None:
        for preset in list_presets():
            assert preset.display_name
            assert preset.description
            assert len(preset.mood_descriptors) > 0
            assert preset.thumbnail_emoji
            assert len(preset.concern_group_hints) > 0

    def test_load_preset_by_id(self) -> None:
        preset = load_preset("neo-noir")
        assert preset is not None
        assert preset.preset_id == "neo-noir"
        assert preset.display_name == "Neo-Noir"

    def test_load_preset_missing_returns_none(self) -> None:
        preset = load_preset("nonexistent-preset")
        assert preset is None

    def test_preset_concern_group_hints_have_valid_keys(self) -> None:
        valid_groups = {
            "look_and_feel",
            "sound_and_music",
            "rhythm_and_flow",
            "character_and_performance",
            "story_world",
        }
        for preset in list_presets():
            for group_key in preset.concern_group_hints:
                assert group_key in valid_groups, (
                    f"Preset {preset.preset_id} has invalid concern group "
                    f"key: {group_key}"
                )

    def test_preset_model_validation(self) -> None:
        """StylePreset Pydantic model validates correctly."""
        data = {
            "preset_id": "test",
            "display_name": "Test",
            "description": "A test preset",
            "mood_descriptors": ["calm"],
            "reference_films": [],
            "thumbnail_emoji": "🎬",
            "concern_group_hints": {
                "look_and_feel": {"palette": "warm tones"},
            },
        }
        preset = StylePreset(**data)
        assert preset.preset_id == "test"


# ---------------------------------------------------------------------------
# T2: Propagation service schemas
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestPropagationSchemas:
    """Verify PropagationResult and PropagatedGroup schemas."""

    def test_propagated_group_roundtrip(self) -> None:
        group = PropagatedGroup(
            fields={"palette": "desaturated neon", "lighting": "high contrast"},
            rationale="Neo-noir demands stark lighting contrasts.",
        )
        data = group.model_dump()
        restored = PropagatedGroup(**data)
        assert restored.fields["palette"] == "desaturated neon"
        assert restored.rationale == group.rationale

    def test_propagation_result_with_some_groups(self) -> None:
        result = PropagationResult(
            look_and_feel=PropagatedGroup(
                fields={"palette": "cool"},
                rationale="Dark mood calls for cool palette.",
            ),
            sound_and_music=None,
            rhythm_and_flow=None,
            character_and_performance=None,
            story_world=None,
            overall_rationale="Overall dark and moody.",
            confidence=0.85,
        )
        assert result.look_and_feel is not None
        assert result.sound_and_music is None
        assert result.confidence == 0.85

    def test_propagation_result_full(self) -> None:
        groups = {}
        for name in [
            "look_and_feel", "sound_and_music", "rhythm_and_flow",
            "character_and_performance", "story_world",
        ]:
            groups[name] = PropagatedGroup(
                fields={"key": f"{name}_value"},
                rationale=f"Rationale for {name}",
            )
        result = PropagationResult(
            **groups,
            overall_rationale="Full propagation.",
            confidence=0.92,
        )
        assert result.look_and_feel is not None
        assert result.story_world is not None


# ---------------------------------------------------------------------------
# T3: IntentMood schema
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestIntentMoodSchema:
    """Verify IntentMood concern group schema."""

    def test_minimal_intent_mood(self) -> None:
        """All fields are optional — empty IntentMood is valid."""
        intent = IntentMood()
        assert intent.mood_descriptors == []
        assert intent.reference_films == []
        assert intent.style_preset_id is None
        assert intent.user_approved is False

    def test_populated_intent_mood(self) -> None:
        intent = IntentMood(
            scope="project",
            mood_descriptors=["tense", "dark"],
            reference_films=["Blade Runner", "Se7en"],
            style_preset_id="neo-noir",
            natural_language_intent="Make it feel claustrophobic.",
            user_approved=True,
        )
        assert len(intent.mood_descriptors) == 2
        assert intent.style_preset_id == "neo-noir"
        assert intent.user_approved is True

    def test_scene_scoped_intent_mood(self) -> None:
        intent = IntentMood(
            scope="scene",
            scene_id="scene_003",
            mood_descriptors=["warm", "nostalgic"],
        )
        assert intent.scope == "scene"
        assert intent.scene_id == "scene_003"


# ---------------------------------------------------------------------------
# T4: Pipeline module (mock mode)
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestIntentMoodModule:
    """Test the intent_mood_v1 pipeline module in mock mode."""

    def test_mock_run(self) -> None:
        from cine_forge.modules.creative_direction.intent_mood_v1.main import (
            run_module,
        )

        inputs = {
            "normalize": _canonical_script_payload(),
            "enriched_scene_index": _scene_index_payload(),
        }
        params = {"work_model": "mock", "concurrency": 1}
        announced: list[dict[str, Any]] = []
        context = {
            "run_id": "test-intent-001",
            "project_id": "test-project",
            "announce_artifact": lambda a: announced.append(a),
        }

        result = run_module(inputs, params, context)

        assert "artifacts" in result
        assert len(result["artifacts"]) >= 1

        # Verify the artifact data validates as IntentMood
        art = result["artifacts"][0]
        intent = IntentMood(**art["data"])
        assert len(intent.mood_descriptors) > 0

        # Verify announce was called
        assert len(announced) >= 1

    def test_mock_run_with_script_bible(self) -> None:
        from cine_forge.modules.creative_direction.intent_mood_v1.main import (
            run_module,
        )

        inputs = {
            "normalize": _canonical_script_payload(),
            "enriched_scene_index": _scene_index_payload(),
            "script_bible": {
                "title": "Test Film",
                "logline": "A short test story.",
                "genre": "drama",
                "setting_period": "contemporary",
                "narrative_pov": "third person",
                "tone_and_mood": "warm and intimate",
                "themes": ["friendship"],
                "screenplay_format": "feature",
                "estimated_runtime_minutes": 2,
            },
        }
        params = {"work_model": "mock", "concurrency": 1}
        context = {
            "run_id": "test-intent-002",
            "project_id": "test-project",
            "announce_artifact": lambda a: None,
        }

        result = run_module(inputs, params, context)
        assert len(result["artifacts"]) >= 1


# ---------------------------------------------------------------------------
# Pipeline graph
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestPipelineGraphIntentMood:
    """Verify intent_mood node is properly configured in graph."""

    def test_intent_mood_node_is_implemented(self) -> None:
        from cine_forge.pipeline.graph import _NODE_MAP

        node = _NODE_MAP["intent_mood"]
        assert node.implemented is True
        assert node.nav_route == "/intent"

    def test_intent_mood_in_fix_recipes(self) -> None:
        from cine_forge.pipeline.graph import NODE_FIX_RECIPES

        assert "intent_mood" in NODE_FIX_RECIPES
        assert NODE_FIX_RECIPES["intent_mood"] == "creative_direction"


# ---------------------------------------------------------------------------
# T12: Suggest flow — response models and suggestion logic
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestSuggestModels:
    """Verify ScriptContextResponse and IntentMoodSuggestion models."""

    def test_script_context_response_roundtrip(self) -> None:
        from cine_forge.api.models import ScriptContextResponse

        ctx = ScriptContextResponse(
            title="The Mariner",
            logline="A fisherman faces a storm.",
            genre="Drama",
            tone="Gritty and intense",
            themes=["survival", "isolation"],
        )
        data = ctx.model_dump()
        restored = ScriptContextResponse(**data)
        assert restored.title == "The Mariner"
        assert restored.themes == ["survival", "isolation"]

    def test_script_context_response_empty_themes(self) -> None:
        from cine_forge.api.models import ScriptContextResponse

        ctx = ScriptContextResponse(
            title="Untitled",
            logline="",
            genre="",
            tone="",
        )
        assert ctx.themes == []

    def test_intent_mood_suggestion_roundtrip(self) -> None:
        from cine_forge.api.models import IntentMoodSuggestion

        suggestion = IntentMoodSuggestion(
            mood_descriptors=["dark", "tense", "atmospheric"],
            style_preset_id="neo-noir",
            natural_language_intent="A noir thriller.",
            rationale="Based on genre and tone.",
        )
        data = suggestion.model_dump()
        restored = IntentMoodSuggestion(**data)
        assert restored.mood_descriptors == ["dark", "tense", "atmospheric"]
        assert restored.style_preset_id == "neo-noir"

    def test_intent_mood_suggestion_defaults(self) -> None:
        from cine_forge.api.models import IntentMoodSuggestion

        suggestion = IntentMoodSuggestion(
            mood_descriptors=["warm"],
        )
        assert suggestion.reference_films == []
        assert suggestion.style_preset_id is None
        assert suggestion.rationale == ""


@pytest.mark.unit
class TestSuggestLogic:
    """Test the mood-word extraction and preset-matching logic."""

    def test_mood_extraction_from_tone_string(self) -> None:
        """Verify words are extracted, deduped, and cleaned."""
        tone = "Dark, intense and moody"
        mood_words = [
            w.strip().rstrip(",.")
            for w in tone.lower().replace(" and ", ", ").split()
            if len(w.strip().rstrip(",.")) > 2
        ]
        seen: set[str] = set()
        deduped: list[str] = []
        for w in mood_words:
            if w not in seen:
                seen.add(w)
                deduped.append(w)
        assert "dark" in deduped
        assert "intense" in deduped
        assert "moody" in deduped
        # "and" should be eliminated (replaced by ", " then split)
        assert "and" not in deduped

    def test_preset_matching_by_keyword_overlap(self) -> None:
        """Neo-noir preset should match 'dark' and 'atmospheric' mood words."""
        from cine_forge.presets import list_presets

        search_terms = {"dark", "atmospheric", "cynical"}
        best_preset_id: str | None = None
        best_score = 0
        for preset in list_presets():
            preset_terms = set(
                w.lower() for w in preset.mood_descriptors
            ) | {preset.preset_id.replace("-", " ")}
            score = len(search_terms & preset_terms)
            if score > best_score:
                best_score = score
                best_preset_id = preset.preset_id
        # Neo-noir has "dark", "cynical", "atmospheric" in its mood_descriptors
        assert best_preset_id == "neo-noir"
        assert best_score >= 2

    def test_no_preset_match_returns_none(self) -> None:
        """Completely unrelated terms should yield no match."""
        from cine_forge.presets import list_presets

        search_terms = {"zzz_nonexistent_term"}
        best_preset_id: str | None = None
        best_score = 0
        for preset in list_presets():
            preset_terms = set(
                w.lower() for w in preset.mood_descriptors
            ) | {preset.preset_id.replace("-", " ")}
            score = len(search_terms & preset_terms)
            if score > best_score:
                best_score = score
                best_preset_id = preset.preset_id
        assert best_score == 0
        assert best_preset_id is None
