"""Unit tests for the character_and_performance_v1 module."""

from __future__ import annotations

from typing import Any

import pytest

from cine_forge.modules.creative_direction.character_and_performance_v1.main import run_module
from cine_forge.schemas.concern_groups import SceneCharacterPerformance


def _canonical_payload() -> dict[str, Any]:
    return {
        "title": "Pressure Test",
        "script_text": (
            "INT. LAB - NIGHT\n"
            "MARA studies the console.\n"
            "OWEN does not look away.\n"
            "MARA\nWe can still stop this.\n"
            "OWEN\nNo. We let it run.\n"
        ),
    }


def _scene_index_payload() -> dict[str, Any]:
    return {
        "entries": [
            {
                "scene_id": "scene_001",
                "scene_number": 1,
                "heading": "INT. LAB - NIGHT",
                "location": "LAB",
                "time_of_day": "NIGHT",
                "tone_mood": "tense",
                "characters_present": ["MARA", "OWEN"],
                "characters_present_ids": ["mara", "owen"],
                "source_span": {"start_line": 1, "end_line": 5},
            }
        ],
        "unique_characters": ["MARA", "OWEN"],
        "unique_locations": ["LAB"],
    }


def _intent_mood_payload() -> dict[str, Any]:
    return {
        "mood_descriptors": ["tense", "claustrophobic"],
        "natural_language_intent": "Pressure should feel tightly contained until someone breaks.",
    }


@pytest.mark.unit
def test_run_module_mock_mode_produces_scene_character_performance_artifact() -> None:
    inputs = {
        "normalize": _canonical_payload(),
        "enriched_scene_index": _scene_index_payload(),
        "intent_mood": _intent_mood_payload(),
        "character_bible": [
            {"character_id": "mara", "name": "MARA", "description": "Exhausted engineer."},
            {"character_id": "owen", "name": "OWEN", "description": "Cold pragmatist."},
        ],
    }

    result = run_module(
        inputs=inputs,
        params={"work_model": "mock", "concurrency": 1},
        context={
            "runtime_params": {},
            "run_id": "test-001",
            "stage_id": "character_and_performance",
        },
    )

    assert result["cost"]["model"] == "mock"
    assert len(result["artifacts"]) == 1

    artifact = result["artifacts"][0]
    assert artifact["artifact_type"] == "character_and_performance"
    assert artifact["entity_id"] == "scene_001"
    assert artifact["schema_name"] == "character_and_performance"

    scene_performance = SceneCharacterPerformance.model_validate(artifact["data"])
    assert scene_performance.scene_id == "scene_001"
    assert scene_performance.user_approved is False
    assert [entry.character_id for entry in scene_performance.entries] == ["mara", "owen"]
    assert artifact["metadata"]["annotations"]["entry_count"] == 2


@pytest.mark.unit
def test_run_module_missing_inputs_raises() -> None:
    with pytest.raises(ValueError, match="requires canonical_script and scene_index"):
        run_module(
            inputs={"normalize": _canonical_payload()},
            params={"work_model": "mock"},
            context={"runtime_params": {}},
        )


@pytest.mark.unit
def test_runtime_work_model_overrides_module_defaults() -> None:
    inputs = {
        "normalize": _canonical_payload(),
        "enriched_scene_index": _scene_index_payload(),
    }

    result = run_module(
        inputs=inputs,
        params={"work_model": "claude-sonnet-4-6", "concurrency": 1},
        context={"runtime_params": {"work_model": "mock"}},
    )

    assert result["cost"]["model"] == "mock"
    assert len(result["artifacts"]) == 1
