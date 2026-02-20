from __future__ import annotations

from typing import Any

import pytest

from cine_forge.modules.world_building.location_bible_v1.main import run_module
from cine_forge.schemas import EntityAdjudicationDecision


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
    
    # We expect 1 location_bible and 1 bible_manifest for STUDIO
    assert len(artifacts) == 2
    manifests = [a for a in artifacts if a["artifact_type"] == "bible_manifest"]
    assert len(manifests) == 1
    assert manifests[0]["entity_id"] == "location_studio"
    assert manifests[0]["data"]["display_name"] == "STUDIO"
    assert "master_v1.json" in manifests[0]["bible_files"]


@pytest.mark.unit
def test_location_bible_module_rejects_invalid_candidate(
    mock_inputs: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    def _fake_adjudication(**_: Any) -> tuple[list[EntityAdjudicationDecision], dict[str, Any]]:
        decisions = [
            EntityAdjudicationDecision(
                candidate="STUDIO",
                verdict="invalid",
                rationale="not an actual location in this synthetic fixture",
                confidence=0.9,
            )
        ]
        return decisions, {
            "model": "mock",
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": 0.0,
        }

    monkeypatch.setattr(
        "cine_forge.modules.world_building.location_bible_v1.main.adjudicate_entity_candidates",
        _fake_adjudication,
    )

    result = run_module(inputs=mock_inputs, params={"model": "mock"}, context={})
    assert result["artifacts"] == []
