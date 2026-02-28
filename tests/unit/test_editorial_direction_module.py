"""Unit tests for the editorial_direction_v1 module (now produces RhythmAndFlow)."""

from __future__ import annotations

from typing import Any

import pytest

from cine_forge.modules.creative_direction.editorial_direction_v1.main import (
    _build_scene_window,
    _mock_direction,
    run_module,
)
from cine_forge.schemas.concern_groups import (
    RhythmAndFlow,
    RhythmAndFlowIndex,
)


def _scene_index_payload() -> dict[str, Any]:
    return {
        "total_scenes": 3,
        "unique_characters": ["ARIA", "NOAH"],
        "unique_locations": ["STUDIO", "ROOF", "OFFICE"],
        "estimated_runtime_minutes": 3.0,
        "scenes_passed_qa": 3,
        "scenes_need_review": 0,
        "entries": [
            {
                "scene_id": "scene_001",
                "scene_number": 1,
                "heading": "INT. STUDIO - DAY",
                "location": "STUDIO",
                "time_of_day": "DAY",
                "characters_present": ["ARIA", "NOAH"],
                "characters_present_ids": ["aria", "noah"],
                "props_mentioned": [],
                "tone_mood": "tense",
                "source_span": {"start_line": 1, "end_line": 4},
            },
            {
                "scene_id": "scene_002",
                "scene_number": 2,
                "heading": "EXT. ROOF - NIGHT",
                "location": "ROOF",
                "time_of_day": "NIGHT",
                "characters_present": ["NOAH"],
                "characters_present_ids": ["noah"],
                "props_mentioned": [],
                "tone_mood": "melancholic",
                "source_span": {"start_line": 5, "end_line": 8},
            },
            {
                "scene_id": "scene_003",
                "scene_number": 3,
                "heading": "INT. OFFICE - DAY",
                "location": "OFFICE",
                "time_of_day": "DAY",
                "characters_present": ["ARIA"],
                "characters_present_ids": ["aria"],
                "props_mentioned": [],
                "tone_mood": "resolute",
                "source_span": {"start_line": 9, "end_line": 12},
            },
        ],
    }


def _canonical_payload() -> dict[str, Any]:
    return {
        "title": "Test Script",
        "script_text": (
            "INT. STUDIO - DAY\n"
            "ARIA\nWe need to talk.\n\n"
            "EXT. ROOF - NIGHT\n"
            "NOAH\nI know.\n\n"
            "INT. OFFICE - DAY\n"
            "ARIA\nIt's decided then.\n"
        ),
        "line_count": 12,
        "scene_count": 3,
        "normalization": {
            "source_format": "screenplay",
            "strategy": "test",
            "rationale": "test",
            "overall_confidence": 1.0,
        },
    }


@pytest.mark.unit
def test_mock_direction_produces_valid_schema() -> None:
    """Mock direction output validates against the RhythmAndFlow schema."""
    direction = _mock_direction("scene_001")
    assert isinstance(direction, RhythmAndFlow)
    assert direction.scene_id == "scene_001"
    assert direction.scope == "scene"
    assert direction.transition_in
    assert direction.transition_out
    assert direction.coverage_priority


@pytest.mark.unit
def test_scene_window_first_scene() -> None:
    """First scene has no previous context."""
    entries = _scene_index_payload()["entries"]
    script_lines = _canonical_payload()["script_text"].splitlines()
    window = _build_scene_window(entries, 0, script_lines)
    assert window["prev_text"] is None
    assert window["prev_heading"] is None
    assert window["current_text"] is not None
    assert "STUDIO" in window["current_text"]
    assert window["next_text"] is not None
    assert window["next_heading"] == "EXT. ROOF - NIGHT"


@pytest.mark.unit
def test_scene_window_middle_scene() -> None:
    """Middle scene has both previous and next context."""
    entries = _scene_index_payload()["entries"]
    script_lines = _canonical_payload()["script_text"].splitlines()
    window = _build_scene_window(entries, 1, script_lines)
    assert window["prev_text"] is not None
    assert window["prev_heading"] == "INT. STUDIO - DAY"
    assert window["current_text"] is not None
    assert "ROOF" in window["current_text"]
    assert window["next_text"] is not None
    assert window["next_heading"] == "INT. OFFICE - DAY"


@pytest.mark.unit
def test_scene_window_last_scene() -> None:
    """Last scene has no next context."""
    entries = _scene_index_payload()["entries"]
    script_lines = _canonical_payload()["script_text"].splitlines()
    window = _build_scene_window(entries, 2, script_lines)
    assert window["prev_text"] is not None
    assert window["prev_heading"] == "EXT. ROOF - NIGHT"
    assert window["current_text"] is not None
    assert "OFFICE" in window["current_text"]
    assert window["next_text"] is None
    assert window["next_heading"] is None


@pytest.mark.unit
def test_run_module_mock_mode() -> None:
    """Full module run with mock model produces valid artifacts."""
    inputs = {
        "normalize": _canonical_payload(),
        "enriched_scene_index": _scene_index_payload(),
    }
    params = {"work_model": "mock", "skip_qa": True}
    context = {"runtime_params": {}, "run_id": "test-001", "stage_id": "rhythm_and_flow"}

    result = run_module(inputs, params, context)

    assert "artifacts" in result
    assert "cost" in result

    artifacts = result["artifacts"]
    # 3 scene directions + 1 index
    assert len(artifacts) == 4

    # Verify per-scene artifacts
    scene_artifacts = [a for a in artifacts if a["artifact_type"] == "rhythm_and_flow"]
    assert len(scene_artifacts) == 3

    for a in scene_artifacts:
        data = a["data"]
        # Validate against schema
        direction = RhythmAndFlow.model_validate(data)
        assert direction.scene_id is not None
        assert direction.scene_id.startswith("scene_")
        assert a["metadata"]["source"] == "ai"

    # Verify index artifact
    index_artifacts = [a for a in artifacts if a["artifact_type"] == "rhythm_and_flow_index"]
    assert len(index_artifacts) == 1
    index_data = index_artifacts[0]["data"]
    index = RhythmAndFlowIndex.model_validate(index_data)
    assert index.total_scenes == 3
    assert index.scenes_with_direction == 3


@pytest.mark.unit
def test_run_module_missing_inputs_raises() -> None:
    """Module raises ValueError when required inputs are missing."""
    with pytest.raises(ValueError, match="requires canonical_script and scene_index"):
        run_module(
            inputs={"normalize": _canonical_payload()},
            params={"work_model": "mock"},
            context={"runtime_params": {}},
        )


@pytest.mark.unit
def test_run_module_empty_scenes() -> None:
    """Module handles empty scene list gracefully."""
    empty_index = {
        "total_scenes": 0,
        "unique_characters": [],
        "unique_locations": [],
        "estimated_runtime_minutes": 0.0,
        "scenes_passed_qa": 0,
        "scenes_need_review": 0,
        "entries": [],
    }
    inputs = {
        "normalize": _canonical_payload(),
        "enriched_scene_index": empty_index,
    }
    params = {"work_model": "mock", "skip_qa": True}
    context = {"runtime_params": {}}

    result = run_module(inputs, params, context)
    artifacts = result["artifacts"]
    # Only the index artifact (0 scene directions)
    assert len(artifacts) == 1
    assert artifacts[0]["artifact_type"] == "rhythm_and_flow_index"
    index = RhythmAndFlowIndex.model_validate(artifacts[0]["data"])
    assert index.total_scenes == 0
    assert index.scenes_with_direction == 0


@pytest.mark.unit
def test_rhythm_and_flow_all_fields_optional() -> None:
    """RhythmAndFlow supports progressive disclosure — all fields optional."""
    # Minimal: just scope
    minimal = RhythmAndFlow()
    assert minimal.scope == "scene"
    assert minimal.scene_function is None
    assert minimal.pacing_intent is None
    assert minimal.montage_candidates == []


@pytest.mark.unit
def test_announce_artifact_called() -> None:
    """Streaming progress callback is invoked for each scene."""
    announced: list[dict] = []

    def mock_announce(artifact: dict) -> None:
        announced.append(artifact)

    inputs = {
        "normalize": _canonical_payload(),
        "enriched_scene_index": _scene_index_payload(),
    }
    params = {"work_model": "mock", "skip_qa": True}
    context = {"runtime_params": {}, "announce_artifact": mock_announce}

    run_module(inputs, params, context)
    # Should announce each scene direction (not the index)
    assert len(announced) == 3
    for a in announced:
        assert a["artifact_type"] == "rhythm_and_flow"
