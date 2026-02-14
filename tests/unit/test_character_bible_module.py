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
        "total_scenes": 2,
        "unique_characters": ["ARIA", "NOAH", "ARIA (V.O.)", "HE", "INT. STUDIO"],
        "unique_locations": ["STUDIO"],
        "estimated_runtime_minutes": 2.0,
        "entries": [
            {
                "scene_id": "scene_001",
                "characters_present": ["ARIA", "NOAH"],
            },
            {
                "scene_id": "scene_002",
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
Hi.""",
        "line_count": 10,
        "scene_count": 2,
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
    assert ranked[0]["scene_count"] == 2
    assert ranked[1]["name"] == "NOAH"
    assert ranked[1]["scene_count"] == 1


@pytest.mark.unit
def test_run_module_emits_bible_manifests() -> None:
    result = run_module(
        inputs={
            "scene_index": _scene_index_payload(),
            "canonical_script": _canonical_payload(),
        },
        params={"model": "mock", "min_scene_appearances": 1},
        context={"run_id": "unit", "stage_id": "world_building"},
    )
    
    artifacts = result["artifacts"]
    assert len(artifacts) == 2
    assert artifacts[0]["artifact_type"] == "bible_manifest"
    assert artifacts[0]["entity_id"].startswith("character_")
    assert "master_v1.json" in artifacts[0]["bible_files"]
