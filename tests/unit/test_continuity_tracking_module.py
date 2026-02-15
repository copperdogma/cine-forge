from __future__ import annotations

from typing import Any

import pytest

from cine_forge.modules.world_building.continuity_tracking_v1.main import run_module


@pytest.fixture
def mock_inputs() -> dict[str, Any]:
    return {
        "extract_scenes": {
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
        "prop_bible": []
    }


@pytest.mark.unit
def test_continuity_tracking_module_mock(mock_inputs: dict[str, Any]) -> None:
    params = {"model": "mock"}
    result = run_module(inputs=mock_inputs, params=params, context={})

    assert "artifacts" in result
    artifacts = result["artifacts"]
    
    # We expect 1 continuity_state for ARIA in scene_001 + 1 continuity_index
    assert len(artifacts) >= 2
    
    states = [a for a in artifacts if a["artifact_type"] == "continuity_state"]
    assert len(states) == 1
    assert states[0]["entity_id"] == "character_aria_scene_001"
    
    index = [a for a in artifacts if a["artifact_type"] == "continuity_index"][0]
    assert "character:aria" in index["data"]["timelines"]
    assert index["data"]["timelines"]["character:aria"]["states"] == ["character_aria_scene_001"]
