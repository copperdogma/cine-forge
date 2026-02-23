from __future__ import annotations

from typing import Any

import pytest

from cine_forge.modules.world_building.prop_bible_v1.main import run_module
from cine_forge.schemas import EntityAdjudicationDecision


@pytest.fixture
def mock_inputs() -> dict[str, Any]:
    return {
        "normalize": {
            "script_text": "INT. STUDIO - DAY\nARIA holds a CAMERA.",
        },
        "breakdown_scenes": {
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


@pytest.mark.unit
def test_prop_bible_module_rejects_non_prop_candidate(
    mock_inputs: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    def _fake_adjudication(**_: Any) -> tuple[list[EntityAdjudicationDecision], dict[str, Any]]:
        decisions = [
            EntityAdjudicationDecision(
                candidate="Hero Sword",
                verdict="valid",
                canonical_name="Hero Sword",
                rationale="actual prop",
                confidence=0.95,
            ),
            EntityAdjudicationDecision(
                candidate="Secret Map",
                verdict="invalid",
                rationale="not treated as prop in this fixture",
                confidence=0.9,
            ),
        ]
        return decisions, {
            "model": "mock",
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": 0.0,
        }

    monkeypatch.setattr(
        "cine_forge.modules.world_building.prop_bible_v1.main.adjudicate_entity_candidates",
        _fake_adjudication,
    )

    result = run_module(inputs=mock_inputs, params={"model": "mock"}, context={})
    artifacts = result["artifacts"]
    ids = {a["entity_id"] for a in artifacts}
    assert "hero_sword" in ids
    assert "prop_hero_sword" in ids
    assert "secret_map" not in ids
    assert "prop_secret_map" not in ids
