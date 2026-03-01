"""Unit tests for continuity_tracking_v1 module (Story 092)."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest

from cine_forge.modules.world_building.continuity_tracking_v1.main import (
    EntityStateExtraction,
    SceneContinuityExtraction,
    _detect_and_record_gaps,
    _extract_scene_text,
    run_module,
)
from cine_forge.schemas import (
    ContinuityEvent,
    ContinuityState,
    EntityTimeline,
    StateProperty,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_inputs() -> dict[str, Any]:
    """Minimal inputs for mock-model testing (original Story 011 fixture)."""
    return {
        "breakdown_scenes": {
            "entries": [
                {
                    "scene_id": "scene_001",
                    "location": "STUDIO",
                    "characters_present": ["ARIA"],
                }
            ],
            "unique_locations": ["STUDIO"],
        },
        "character_bible": [
            {
                "character_id": "aria",
                "name": "ARIA",
            }
        ],
        "location_bible": [],
        "prop_bible": [],
    }


@pytest.fixture
def multi_scene_inputs() -> dict[str, Any]:
    """Multi-scene inputs with script text for AI-path testing."""
    return {
        "normalize": {
            "script_text": (
                "INT. DOCK - DAY\n"
                "\n"
                "BILLY stands at the edge, gripping a weathered OAR.\n"
                "He wears a torn blue jacket and oil-stained jeans.\n"
                "\n"
                "INT. DOCK - NIGHT\n"
                "\n"
                "BILLY sits on a crate, blood on his lip from the fight.\n"
                "His jacket is ripped at the shoulder now.\n"
                "The OAR leans against the wall, cracked.\n"
            ),
        },
        "breakdown_scenes": {
            "entries": [
                {
                    "scene_id": "scene_001",
                    "scene_number": 1,
                    "heading": "INT. DOCK - DAY",
                    "location": "DOCK",
                    "characters_present": ["BILLY"],
                    "props_mentioned": ["OAR"],
                    "source_span": {"start_line": 1, "end_line": 5},
                },
                {
                    "scene_id": "scene_002",
                    "scene_number": 2,
                    "heading": "INT. DOCK - NIGHT",
                    "location": "DOCK",
                    "characters_present": ["BILLY"],
                    "props_mentioned": ["OAR"],
                    "source_span": {"start_line": 6, "end_line": 11},
                },
            ],
            "unique_locations": ["DOCK"],
        },
        "character_bible": [
            {"character_id": "billy", "name": "BILLY"},
        ],
        "location_bible": [
            {"location_id": "dock", "name": "DOCK"},
        ],
        "prop_bible": [
            {"prop_id": "oar", "name": "OAR"},
        ],
    }


def _make_llm_response_scene1() -> SceneContinuityExtraction:
    """Canned LLM response for scene 001."""
    return SceneContinuityExtraction(
        scene_id="scene_001",
        entity_states=[
            EntityStateExtraction(
                entity_key="character:billy",
                properties=[
                    StateProperty(
                        key="costume",
                        value="torn blue jacket, oil-stained jeans",
                        confidence=0.95,
                    ),
                    StateProperty(
                        key="physical_condition",
                        value="healthy",
                        confidence=0.9,
                    ),
                    StateProperty(
                        key="emotional_state",
                        value="determined",
                        confidence=0.7,
                    ),
                ],
                change_events=[],
                confidence=0.85,
            ),
            EntityStateExtraction(
                entity_key="location:dock",
                properties=[
                    StateProperty(
                        key="time_of_day", value="day", confidence=1.0
                    ),
                    StateProperty(
                        key="lighting", value="natural daylight", confidence=0.9
                    ),
                ],
                change_events=[],
                confidence=0.9,
            ),
            EntityStateExtraction(
                entity_key="prop:oar",
                properties=[
                    StateProperty(
                        key="condition", value="weathered but intact", confidence=0.9
                    ),
                    StateProperty(
                        key="position", value="in Billy's hands", confidence=0.95
                    ),
                ],
                change_events=[],
                confidence=0.9,
            ),
        ],
    )


def _make_llm_response_scene2() -> SceneContinuityExtraction:
    """Canned LLM response for scene 002 — with change events."""
    return SceneContinuityExtraction(
        scene_id="scene_002",
        entity_states=[
            EntityStateExtraction(
                entity_key="character:billy",
                properties=[
                    StateProperty(
                        key="costume",
                        value="torn blue jacket ripped at shoulder, oil-stained jeans",
                        confidence=0.95,
                    ),
                    StateProperty(
                        key="physical_condition",
                        value="blood on lip from fight",
                        confidence=0.95,
                    ),
                    StateProperty(
                        key="emotional_state",
                        value="exhausted",
                        confidence=0.7,
                    ),
                ],
                change_events=[
                    ContinuityEvent(
                        property_key="costume",
                        previous_value="torn blue jacket, oil-stained jeans",
                        new_value=(
                            "torn blue jacket ripped at shoulder, "
                            "oil-stained jeans"
                        ),
                        reason="Jacket damaged in fight",
                        evidence="His jacket is ripped at the shoulder now.",
                        is_explicit=True,
                        confidence=0.95,
                    ),
                    ContinuityEvent(
                        property_key="physical_condition",
                        previous_value="healthy",
                        new_value="blood on lip from fight",
                        reason="Injured in fight between scenes",
                        evidence="blood on his lip from the fight",
                        is_explicit=True,
                        confidence=0.95,
                    ),
                ],
                confidence=0.9,
            ),
            EntityStateExtraction(
                entity_key="location:dock",
                properties=[
                    StateProperty(
                        key="time_of_day", value="night", confidence=1.0
                    ),
                    StateProperty(
                        key="lighting", value="dim/artificial", confidence=0.7
                    ),
                ],
                change_events=[
                    ContinuityEvent(
                        property_key="time_of_day",
                        previous_value="day",
                        new_value="night",
                        reason="Time has passed",
                        evidence="INT. DOCK - NIGHT",
                        is_explicit=True,
                        confidence=1.0,
                    ),
                ],
                confidence=0.9,
            ),
            EntityStateExtraction(
                entity_key="prop:oar",
                properties=[
                    StateProperty(
                        key="condition", value="cracked", confidence=0.95
                    ),
                    StateProperty(
                        key="position",
                        value="leaning against the wall",
                        confidence=0.95,
                    ),
                ],
                change_events=[
                    ContinuityEvent(
                        property_key="condition",
                        previous_value="weathered but intact",
                        new_value="cracked",
                        reason="Damaged (likely in fight)",
                        evidence="The OAR leans against the wall, cracked.",
                        is_explicit=True,
                        confidence=0.9,
                    ),
                ],
                confidence=0.9,
            ),
        ],
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestMockPath:
    """Tests for the mock/deterministic path (preserved from Story 011)."""

    def test_continuity_tracking_module_mock(
        self, mock_inputs: dict[str, Any]
    ) -> None:
        params = {"model": "mock"}
        result = run_module(inputs=mock_inputs, params=params, context={})

        assert "artifacts" in result
        artifacts = result["artifacts"]

        # 1 continuity_state for ARIA in scene_001 + 1 continuity_index
        assert len(artifacts) >= 2

        states = [
            a for a in artifacts if a["artifact_type"] == "continuity_state"
        ]
        assert len(states) == 1
        assert states[0]["entity_id"] == "character_aria_scene_001"

        index = [
            a for a in artifacts if a["artifact_type"] == "continuity_index"
        ][0]
        assert "character:aria" in index["data"]["timelines"]
        assert index["data"]["timelines"]["character:aria"]["states"] == [
            "character_aria_scene_001"
        ]

    def test_mock_path_includes_props(self) -> None:
        """Props in props_mentioned should appear as entities."""
        inputs: dict[str, Any] = {
            "breakdown_scenes": {
                "entries": [
                    {
                        "scene_id": "scene_001",
                        "location": "DOCK",
                        "characters_present": ["BILLY"],
                        "props_mentioned": ["OAR"],
                        "source_span": {"start_line": 1, "end_line": 3},
                    }
                ],
                "unique_locations": ["DOCK"],
            },
            "character_bible": [
                {"character_id": "billy", "name": "BILLY"}
            ],
            "location_bible": [
                {"location_id": "dock", "name": "DOCK"}
            ],
            "prop_bible": [
                {"prop_id": "oar", "name": "OAR"}
            ],
        }
        result = run_module(inputs=inputs, params={"model": "mock"}, context={})
        states = [
            a
            for a in result["artifacts"]
            if a["artifact_type"] == "continuity_state"
        ]
        entity_ids = {s["entity_id"] for s in states}
        assert "character_billy_scene_001" in entity_ids
        assert "location_dock_scene_001" in entity_ids
        # Props with no mock template get empty properties but still tracked


@pytest.mark.unit
class TestSceneTextExtraction:
    """Tests for _extract_scene_text()."""

    def test_basic_extraction(self) -> None:
        lines = [
            "INT. DOCK - DAY",
            "",
            "BILLY stands at the edge.",
            "",
            "INT. DOCK - NIGHT",
            "",
            "BILLY sits on a crate.",
        ]
        scene_entry = {
            "source_span": {"start_line": 1, "end_line": 4},
        }
        text = _extract_scene_text(lines, scene_entry)
        assert "BILLY stands at the edge." in text
        assert "BILLY sits on a crate." not in text

    def test_extraction_with_missing_span(self) -> None:
        """Falls back to full text when source_span is missing."""
        lines = ["Line 1", "Line 2", "Line 3"]
        scene_entry: dict[str, Any] = {}
        text = _extract_scene_text(lines, scene_entry)
        assert text == "Line 1\nLine 2\nLine 3"

    def test_single_line_scene(self) -> None:
        lines = ["INT. ROOM - DAY", "Action.", "INT. HALL - NIGHT"]
        scene_entry = {"source_span": {"start_line": 2, "end_line": 2}}
        text = _extract_scene_text(lines, scene_entry)
        assert text == "Action."


@pytest.mark.unit
class TestAIPath:
    """Tests for the real AI path with mocked LLM calls."""

    def test_ai_path_produces_states_with_properties(
        self, multi_scene_inputs: dict[str, Any]
    ) -> None:
        """LLM extraction populates properties and change_events."""
        call_count = 0

        def fake_call_llm(**kwargs: Any) -> tuple[Any, dict[str, Any]]:
            nonlocal call_count
            call_count += 1
            metadata = {
                "model": "claude-sonnet-4-6",
                "input_tokens": 500,
                "output_tokens": 200,
                "estimated_cost_usd": 0.003,
            }
            if call_count == 1:
                return _make_llm_response_scene1(), metadata
            return _make_llm_response_scene2(), metadata

        with patch(
            "cine_forge.modules.world_building.continuity_tracking_v1"
            ".main.call_llm",
            side_effect=fake_call_llm,
        ):
            result = run_module(
                inputs=multi_scene_inputs,
                params={"work_model": "claude-sonnet-4-6"},
                context={},
            )

        states = [
            a
            for a in result["artifacts"]
            if a["artifact_type"] == "continuity_state"
        ]
        # 3 entities × 2 scenes = 6 states
        assert len(states) == 6

        # Check Billy's scene 2 has change events
        billy_s2 = next(
            a
            for a in states
            if a["entity_id"] == "character_billy_scene_002"
        )
        assert len(billy_s2["data"]["change_events"]) == 2
        assert billy_s2["data"]["change_events"][0]["property_key"] == "costume"

        # Check Billy's scene 1 has properties
        billy_s1 = next(
            a
            for a in states
            if a["entity_id"] == "character_billy_scene_001"
        )
        assert len(billy_s1["data"]["properties"]) == 3
        assert billy_s1["data"]["properties"][0]["key"] == "costume"

    def test_ai_path_tracks_cost(
        self, multi_scene_inputs: dict[str, Any]
    ) -> None:
        """Cost accumulates from LLM calls."""

        def fake_call_llm(**kwargs: Any) -> tuple[Any, dict[str, Any]]:
            metadata = {
                "model": "claude-sonnet-4-6",
                "input_tokens": 1000,
                "output_tokens": 500,
                "estimated_cost_usd": 0.005,
            }
            return SceneContinuityExtraction(
                scene_id="any",
                entity_states=[],
            ), metadata

        with patch(
            "cine_forge.modules.world_building.continuity_tracking_v1"
            ".main.call_llm",
            side_effect=fake_call_llm,
        ):
            result = run_module(
                inputs=multi_scene_inputs,
                params={"work_model": "claude-sonnet-4-6"},
                context={},
            )

        cost = result["cost"]
        # 2 scenes = 2 LLM calls
        assert cost["input_tokens"] == 2000
        assert cost["output_tokens"] == 1000
        assert cost["estimated_cost_usd"] == pytest.approx(0.01)

    def test_ai_path_handles_llm_failure(
        self, multi_scene_inputs: dict[str, Any]
    ) -> None:
        """LLM failure produces low-confidence empty states, not crash."""

        def failing_call_llm(**kwargs: Any) -> None:
            raise RuntimeError("LLM unavailable")

        with patch(
            "cine_forge.modules.world_building.continuity_tracking_v1"
            ".main.call_llm",
            side_effect=failing_call_llm,
        ):
            result = run_module(
                inputs=multi_scene_inputs,
                params={"work_model": "claude-sonnet-4-6"},
                context={},
            )

        # Should still produce an index (no crash)
        index_list = [
            a
            for a in result["artifacts"]
            if a["artifact_type"] == "continuity_index"
        ]
        assert len(index_list) == 1

    def test_ai_path_computes_real_scores(
        self, multi_scene_inputs: dict[str, Any]
    ) -> None:
        """Index has computed continuity score, not hardcoded 0.9."""
        call_count = 0

        def fake_call_llm(**kwargs: Any) -> tuple[Any, dict[str, Any]]:
            nonlocal call_count
            call_count += 1
            metadata = {
                "model": "test",
                "input_tokens": 0,
                "output_tokens": 0,
                "estimated_cost_usd": 0.0,
            }
            if call_count == 1:
                return _make_llm_response_scene1(), metadata
            return _make_llm_response_scene2(), metadata

        with patch(
            "cine_forge.modules.world_building.continuity_tracking_v1"
            ".main.call_llm",
            side_effect=fake_call_llm,
        ):
            result = run_module(
                inputs=multi_scene_inputs,
                params={"work_model": "claude-sonnet-4-6"},
                context={},
            )

        index = next(
            a
            for a in result["artifacts"]
            if a["artifact_type"] == "continuity_index"
        )
        score = index["data"]["overall_continuity_score"]
        # Score is computed from entity confidences, not hardcoded 0.9
        assert 0.0 < score < 1.0
        assert score != 0.9  # not the old hardcoded value


@pytest.mark.unit
class TestGapDetection:
    """Tests for _detect_and_record_gaps()."""

    def test_no_gaps_for_consistent_states(self) -> None:
        """No gaps when all states have good confidence and no contradictions."""
        timelines = {
            "character:billy": EntityTimeline(
                entity_type="character",
                entity_id="billy",
                states=["s1", "s2"],
            )
        }
        all_states = {
            "s1": ContinuityState(
                entity_type="character",
                entity_id="billy",
                scene_id="scene_001",
                story_time_position=0,
                properties=[
                    StateProperty(
                        key="costume", value="blue jacket", confidence=0.9
                    )
                ],
                change_events=[],
                overall_confidence=0.9,
            ),
            "s2": ContinuityState(
                entity_type="character",
                entity_id="billy",
                scene_id="scene_002",
                story_time_position=1,
                properties=[
                    StateProperty(
                        key="costume", value="blue jacket", confidence=0.9
                    )
                ],
                change_events=[],
                overall_confidence=0.9,
            ),
        }
        _detect_and_record_gaps(timelines, all_states)
        assert timelines["character:billy"].gaps == []

    def test_gap_for_empty_properties(self) -> None:
        """Flags gap when an entity has no properties extracted."""
        timelines = {
            "character:billy": EntityTimeline(
                entity_type="character",
                entity_id="billy",
                states=["s1"],
            )
        }
        all_states = {
            "s1": ContinuityState(
                entity_type="character",
                entity_id="billy",
                scene_id="scene_001",
                story_time_position=0,
                properties=[],
                change_events=[],
                overall_confidence=0.3,
            ),
        }
        _detect_and_record_gaps(timelines, all_states)
        assert "scene_001" in timelines["character:billy"].gaps

    def test_gap_for_low_confidence(self) -> None:
        """Flags gap when confidence is below threshold."""
        timelines = {
            "character:billy": EntityTimeline(
                entity_type="character",
                entity_id="billy",
                states=["s1"],
            )
        }
        all_states = {
            "s1": ContinuityState(
                entity_type="character",
                entity_id="billy",
                scene_id="scene_001",
                story_time_position=0,
                properties=[
                    StateProperty(
                        key="costume", value="unknown", confidence=0.2
                    )
                ],
                change_events=[],
                overall_confidence=0.3,
            ),
        }
        _detect_and_record_gaps(timelines, all_states)
        assert "scene_001" in timelines["character:billy"].gaps

    def test_gap_for_unexplained_contradiction(self) -> None:
        """Flags gap when property changes without a change event."""
        timelines = {
            "character:billy": EntityTimeline(
                entity_type="character",
                entity_id="billy",
                states=["s1", "s2"],
            )
        }
        all_states = {
            "s1": ContinuityState(
                entity_type="character",
                entity_id="billy",
                scene_id="scene_001",
                story_time_position=0,
                properties=[
                    StateProperty(
                        key="costume", value="blue jacket", confidence=0.9
                    )
                ],
                change_events=[],
                overall_confidence=0.9,
            ),
            "s2": ContinuityState(
                entity_type="character",
                entity_id="billy",
                scene_id="scene_002",
                story_time_position=1,
                properties=[
                    StateProperty(
                        key="costume", value="red shirt", confidence=0.9
                    )
                ],
                # No change event explains the costume change!
                change_events=[],
                overall_confidence=0.9,
            ),
        }
        _detect_and_record_gaps(timelines, all_states)
        assert "scene_002" in timelines["character:billy"].gaps

    def test_no_gap_when_change_event_explains(self) -> None:
        """No gap when a change event explains the property difference."""
        timelines = {
            "character:billy": EntityTimeline(
                entity_type="character",
                entity_id="billy",
                states=["s1", "s2"],
            )
        }
        all_states = {
            "s1": ContinuityState(
                entity_type="character",
                entity_id="billy",
                scene_id="scene_001",
                story_time_position=0,
                properties=[
                    StateProperty(
                        key="costume", value="blue jacket", confidence=0.9
                    )
                ],
                change_events=[],
                overall_confidence=0.9,
            ),
            "s2": ContinuityState(
                entity_type="character",
                entity_id="billy",
                scene_id="scene_002",
                story_time_position=1,
                properties=[
                    StateProperty(
                        key="costume", value="red shirt", confidence=0.9
                    )
                ],
                change_events=[
                    ContinuityEvent(
                        property_key="costume",
                        previous_value="blue jacket",
                        new_value="red shirt",
                        reason="Changed clothes at home",
                        evidence="Billy enters wearing a red shirt.",
                        is_explicit=True,
                        confidence=0.9,
                    )
                ],
                overall_confidence=0.9,
            ),
        }
        _detect_and_record_gaps(timelines, all_states)
        assert timelines["character:billy"].gaps == []
