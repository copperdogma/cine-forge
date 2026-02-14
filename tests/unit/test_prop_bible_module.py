from __future__ import annotations

from typing import Any

import pytest

from cine_forge.modules.world_building.prop_bible_v1.main import run_module


@pytest.fixture
def mock_inputs() -> dict[str, Any]:
    return {
        "normalize": {
            "script_text": "INT. STUDIO - DAY\nARIA holds a CAMERA.",
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
def test_prop_bible_module_extracts_mock(mock_inputs: dict[str, Any]) -> None:
    params = {"model": "mock"}
    result = run_module(inputs=mock_inputs, params=params, context={})

    assert "artifacts" in result
    artifacts = result["artifacts"]
    
    # We expect 2 bible_manifests + 2 prop_bibles for discovered props
    assert len(artifacts) == 4
    # Mock returns ["Hero Sword", "Secret Map"]
    manifests = [a for a in artifacts if a["artifact_type"] == "bible_manifest"]
    assert len(manifests) == 2
    assert any(m["entity_id"] == "prop_hero_sword" for m in manifests)
    assert any(m["entity_id"] == "prop_secret_map" for m in manifests)
    assert "master_v1.json" in manifests[0]["bible_files"]
