from __future__ import annotations

from typing import Any

import pytest

from cine_forge.modules.world_building.character_bible_v1.main import (
    _aggregate_characters,
    _rank_characters,
    run_module,
)


def _scene_index_payload() -> dict[str, Any]:
    return {
        "total_scenes": 3,
        "unique_characters": ["ARIA", "NOAH", "ARIA (V.O.)", "HE", "INT. STUDIO"],
        "unique_locations": ["STUDIO"],
        "estimated_runtime_minutes": 3.0,
        "entries": [
            {
                "scene_id": "scene_001",
                "characters_present": ["ARIA", "NOAH"],
            },
            {
                "scene_id": "scene_002",
                "characters_present": ["ARIA"],
            },
            {
                "scene_id": "scene_003",
                "characters_present": ["ARIA"],
            },
        ],
    }


def _canonical_payload() -> dict[str, Any]:
    return {
        "title": "Test",
        "script_text": """INT. STUDIO - DAY
ARIA
Hello.

EXT. ROOF - NIGHT
NOAH
Hi.

INT. OFFICE - DAY
ARIA
Listen.""",
        "line_count": 15,
        "scene_count": 3,
        "normalization": {
            "source_format": "screenplay",
            "strategy": "test",
            "rationale": "test",
            "overall_confidence": 1.0,
        },
    }


@pytest.mark.unit
def test_character_aggregation_filters_noise() -> None:
    index = _scene_index_payload()
    chars = _aggregate_characters(index)
    # ARIA, NOAH are plausible.
    # ARIA (V.O.) normalizes to ARIA.
    # HE is a stopword.
    # INT. STUDIO is not a plausible name.
    assert sorted(chars) == ["ARIA", "NOAH"]


@pytest.mark.unit
def test_character_ranking() -> None:
    chars = ["ARIA", "NOAH"]
    script = _canonical_payload()
    index = _scene_index_payload()
    ranked = _rank_characters(chars, script, index)
    
    assert ranked[0]["name"] == "ARIA"
    assert ranked[0]["scene_count"] == 3
    assert ranked[1]["name"] == "NOAH"
    assert ranked[1]["scene_count"] == 1


@pytest.mark.unit
def test_run_module_emits_bible_manifests() -> None:
    # Aria has 3 scenes, Noah has 1. Both have dialogue.
    result = run_module(
        inputs={
            "scene_index": _scene_index_payload(),
            "canonical_script": _canonical_payload(),
        },
        params={"model": "mock"},
        context={"run_id": "unit", "stage_id": "world_building"},
    )
    
    artifacts = result["artifacts"]
    # Both should remain because both have dialogue_count >= 1
    assert len(artifacts) == 2
    ids = {a["entity_id"] for name, a in zip(["ARIA", "NOAH"], artifacts, strict=False)}
    assert "character_aria" in ids
    assert "character_noah" in ids
