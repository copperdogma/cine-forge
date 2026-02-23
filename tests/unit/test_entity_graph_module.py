from __future__ import annotations

from typing import Any

import pytest

from cine_forge.modules.world_building.entity_graph_v1.main import run_module


@pytest.fixture
def mock_inputs() -> dict[str, Any]:
    return {
        "breakdown_scenes": {
            "entries": [
                {
                    "scene_id": "scene_001",
                    "location": "STUDIO",
                    "characters_present": ["ARIA", "NOAH"],
                },
                {
                    "scene_id": "scene_002",
                    "location": "PARK",
                    "characters_present": ["ARIA"],
                }
            ],
            "unique_locations": ["STUDIO", "PARK"],
        },
        "character_bible": [
            {
                "character_id": "aria",
                "name": "ARIA",
                "relationships": [
                    {
                        "target_character": "NOAH",
                        "relationship_type": "friend",
                        "evidence": "They grew up together.",
                        "confidence": 0.9,
                    }
                ]
            },
            {
                "character_id": "noah",
                "name": "NOAH",
                "relationships": []
            }
        ],
        "location_bible": [
            {
                "location_id": "studio",
                "name": "STUDIO",
            }
        ],
        "prop_bible": []
    }


@pytest.mark.unit
def test_entity_graph_module_builds_mock(mock_inputs: dict[str, Any]) -> None:
    params = {"model": "mock"}
    result = run_module(inputs=mock_inputs, params=params, context={})

    assert "artifacts" in result
    artifacts = result["artifacts"]
    assert len(artifacts) == 1
    
    graph_data = artifacts[0]["data"]
    edges = graph_data["edges"]
    
    # Co-occurrence: Aria & Noah in scene_001
    assert any(
        e["source_id"] == "aria"
        and e["target_id"] == "noah"
        and e["relationship_type"] == "co-occurrence"
        for e in edges
    )
    
    # Presence: Aria in Studio
    assert any(
        e["source_id"] == "aria"
        and e["target_id"] == "studio"
        and e["relationship_type"] == "presence"
        for e in edges
    )
    
    # Relationship Stub: Aria friend of Noah
    assert any(
        e["source_id"] == "aria"
        and e["target_id"] == "noah"
        and e["relationship_type"] == "friend"
        for e in edges
    )
    
    assert graph_data["entity_count"]["character"] == 2
    assert graph_data["entity_count"]["location"] == 1
