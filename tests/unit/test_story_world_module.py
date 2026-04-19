"""Unit tests for the story_world_v1 module."""

from __future__ import annotations

from typing import Any

import pytest

from cine_forge.modules.creative_direction.story_world_v1.main import (
    _StoryWorldAuthoringResponse,
    run_module,
)
from cine_forge.schemas.concern_groups import StoryWorld


def _canonical_payload() -> dict[str, Any]:
    return {
        "title": "Pressure Test",
        "script_text": (
            "INT. LAB - NIGHT\n"
            "MARA studies the console.\n"
            "MARA\nWe can still stop this.\n\n"
            "EXT. ROOF - DAWN\n"
            "Wind tears at Mara's coat.\n"
            "MARA\nThen tell me what it cost.\n"
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
                "tone_mood": "tense",
                "characters_present": ["MARA", "OWEN"],
            },
            {
                "scene_id": "scene_002",
                "scene_number": 2,
                "heading": "EXT. ROOF - DAWN",
                "location": "ROOF",
                "tone_mood": "bleak",
                "characters_present": ["MARA"],
            },
        ],
        "unique_characters": ["MARA", "OWEN"],
        "unique_locations": ["LAB", "ROOF"],
    }


def _intent_mood_payload() -> dict[str, Any]:
    return {
        "mood_descriptors": ["tense", "bleak"],
        "reference_films": ["Sicario (2015)", "Michael Clayton (2007)"],
        "natural_language_intent": (
            "Pressure should collapse inward until the outside world exposes the cost."
        ),
    }


@pytest.mark.unit
def test_run_module_mock_mode_produces_story_world_artifact() -> None:
    inputs = {
        "normalize": _canonical_payload(),
        "enriched_scene_index": _scene_index_payload(),
        "intent_mood": _intent_mood_payload(),
        "character_bible": [
            {"character_id": "mara", "name": "MARA", "description": "Exhausted engineer."},
            {"character_id": "owen", "name": "OWEN", "description": "Cold pragmatist."},
        ],
        "location_bible": [
            {"location_id": "lab", "name": "LAB", "description": "Sealed and fluorescent."},
            {"location_id": "roof", "name": "ROOF", "description": "Open, wind-battered."},
        ],
        "prop_bible": [
            {"prop_id": "console", "name": "CONSOLE", "description": "The irreversible switch."},
        ],
    }

    result = run_module(
        inputs=inputs,
        params={"work_model": "mock"},
        context={"runtime_params": {}, "run_id": "test-001", "stage_id": "story_world"},
    )

    assert result["cost"]["model"] == "mock"
    assert len(result["artifacts"]) == 1

    artifact = result["artifacts"][0]
    assert artifact["artifact_type"] == "story_world"
    assert artifact["entity_id"] == "project"

    story_world = StoryWorld.model_validate(artifact["data"])
    assert story_world.character_design_baselines == ["mara", "owen"]
    assert story_world.location_design_baselines == ["lab", "roof"]
    assert story_world.prop_design_baselines == ["console"]
    assert story_world.visual_motif_annotations
    assert story_world.audio_motif_annotations
    assert artifact["metadata"]["annotations"]["visual_motif_count"] == len(
        story_world.visual_motif_annotations
    )


@pytest.mark.unit
def test_story_world_response_schema_is_fully_defined() -> None:
    schema = _StoryWorldAuthoringResponse.model_json_schema()

    visual_items = schema["properties"]["visual_motif_annotations"]["items"]
    assert visual_items["$ref"] == "#/$defs/MotifAnnotation"
    assert "MotifAnnotation" in schema["$defs"]


@pytest.mark.unit
def test_run_module_missing_inputs_raises() -> None:
    with pytest.raises(ValueError, match="requires canonical_script and scene_index"):
        run_module(
            inputs={"normalize": _canonical_payload()},
            params={"work_model": "mock"},
            context={"runtime_params": {}},
        )
