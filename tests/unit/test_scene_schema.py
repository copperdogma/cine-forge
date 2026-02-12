from __future__ import annotations

import pytest
from pydantic import ValidationError

from cine_forge.schemas import Scene, SceneIndex


def _scene_payload() -> dict[str, object]:
    return {
        "scene_id": "scene_001",
        "scene_number": 1,
        "heading": "INT. LAB - NIGHT",
        "location": "Lab",
        "time_of_day": "NIGHT",
        "int_ext": "INT",
        "characters_present": ["MARA"],
        "elements": [
            {"element_type": "scene_heading", "content": "INT. LAB - NIGHT"},
            {"element_type": "character", "content": "MARA"},
            {"element_type": "dialogue", "content": "We begin."},
        ],
        "narrative_beats": [
            {
                "beat_type": "decision",
                "description": "Mara commits to testing the device.",
                "approximate_location": "mid-scene",
                "confidence": 0.84,
            }
        ],
        "tone_mood": "tense",
        "tone_shifts": ["resolve"],
        "source_span": {"start_line": 1, "end_line": 12},
        "inferences": [
            {
                "field_name": "location",
                "value": "Lab",
                "rationale": "Derived from slug line descriptor",
                "confidence": 0.91,
            }
        ],
        "provenance": [
            {
                "field_name": "heading",
                "method": "parser",
                "evidence": "Slug line token match",
                "confidence": 0.99,
            }
        ],
        "confidence": 0.93,
    }


@pytest.mark.unit
def test_scene_schema_accepts_valid_payload() -> None:
    scene = Scene.model_validate(_scene_payload())
    assert scene.scene_id == "scene_001"
    assert scene.elements[0].element_type == "scene_heading"
    assert scene.source_span.end_line == 12


@pytest.mark.unit
def test_scene_schema_rejects_invalid_element_type() -> None:
    payload = _scene_payload()
    payload["elements"] = [{"element_type": "monologue", "content": "invalid"}]
    with pytest.raises(ValidationError):
        Scene.model_validate(payload)


@pytest.mark.unit
def test_scene_schema_rejects_invalid_span_order() -> None:
    payload = _scene_payload()
    payload["source_span"] = {"start_line": 10, "end_line": 2}
    with pytest.raises(ValidationError):
        Scene.model_validate(payload)


@pytest.mark.unit
def test_scene_schema_rejects_out_of_range_confidence() -> None:
    payload = _scene_payload()
    payload["confidence"] = 1.2
    with pytest.raises(ValidationError):
        Scene.model_validate(payload)


@pytest.mark.unit
def test_scene_index_rejects_negative_counts() -> None:
    with pytest.raises(ValidationError):
        SceneIndex.model_validate(
            {
                "total_scenes": -1,
                "unique_locations": [],
                "unique_characters": [],
                "estimated_runtime_minutes": 0.0,
                "scenes_passed_qa": 0,
                "scenes_need_review": 0,
                "entries": [],
            }
        )
