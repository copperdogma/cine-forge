from __future__ import annotations

from typing import Any

import pytest

from cine_forge.modules.world_building.location_bible_v1.main import run_module


@pytest.fixture
def mock_inputs() -> dict[str, Any]:
    return {
        "normalize": {
            "script_text": "INT. STUDIO - DAY\nARIA is here.",
        },
        "extract_scenes": {
            "unique_locations": ["STUDIO"],
            "entries": [
                {
                    "scene_id": "scene_001",
                    "location": "STUDIO",
                }
            ],
        },
    }


@pytest.mark.unit
def test_location_bible_module_extracts_mock(mock_inputs: dict[str, Any]) -> None:
    params = {"model": "mock"}
    result = run_module(inputs=mock_inputs, params=params, context={})

    assert "artifacts" in result
    artifacts = result["artifacts"]
    
    # We expect 1 bible_manifest for STUDIO
    manifests = [a for a in artifacts if a["artifact_type"] == "bible_manifest"]
    assert len(manifests) == 1
    assert manifests[0]["entity_id"] == "location_studio"
    assert manifests[0]["data"]["display_name"] == "STUDIO"
    assert "master_v1.json" in manifests[0]["bible_files"]
