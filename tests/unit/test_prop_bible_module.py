from __future__ import annotations

from typing import Any

import pytest

from cine_forge.modules.world_building.prop_bible_v1.main import (
    _find_scene_presence,
    run_module,
)
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


@pytest.mark.unit
def test_find_scene_presence_matches_span() -> None:
    """_find_scene_presence returns scene IDs where prop name appears in the scene span."""
    canonical_script = {
        "script_text": (
            "INT. OFFICE - DAY\n"           # line 1 (scene_001 span: 1-3)
            "John sits at his desk.\n"       # line 2
            "He picks up the BANDOLIER.\n"  # line 3 — prop mention
            "EXT. STREET - NIGHT\n"         # line 4 (scene_002 span: 4-6)
            "Mary walks alone.\n"            # line 5
            "No props here.\n"               # line 6
        )
    }
    scene_index = {
        "entries": [
            {
                "scene_id": "scene_001",
                "source_span": {"start_line": 1, "end_line": 3},
            },
            {
                "scene_id": "scene_002",
                "source_span": {"start_line": 4, "end_line": 6},
            },
        ]
    }
    result = _find_scene_presence("Bandolier", canonical_script, scene_index)
    assert result == ["scene_001"]
    assert "scene_002" not in result


@pytest.mark.unit
def test_find_scene_presence_no_match() -> None:
    """Returns empty list when prop name doesn't appear in any scene span."""
    canonical_script = {"script_text": "INT. OFFICE - DAY\nNothing here.\n"}
    scene_index = {
        "entries": [
            {"scene_id": "scene_001", "source_span": {"start_line": 1, "end_line": 2}}
        ]
    }
    assert _find_scene_presence("Flare Gun", canonical_script, scene_index) == []


@pytest.mark.unit
def test_mock_extract_scene_presence_overwritten_to_empty() -> None:
    """Mock extraction returns scene_001 but _find_scene_presence overrides it.
    With a script that doesn't mention the prop, scene_presence should be [].
    """
    canonical_script = {
        "script_text": "INT. OFFICE - DAY\nNothing here.\n",
    }
    scene_index = {
        "entries": [
            {
                "scene_id": "scene_001",
                "location": "OFFICE",
                "characters_present": [],
                "source_span": {"start_line": 1, "end_line": 2},
            }
        ],
        "unique_locations": ["OFFICE"],
    }
    inputs = {
        "canonical_script": canonical_script,
        "enriched_scene_index": scene_index,
    }
    result = run_module(inputs=inputs, params={"model": "mock"}, context={})
    prop_bibles = [a for a in result["artifacts"] if a["artifact_type"] == "prop_bible"]
    for bible in prop_bibles:
        # Mock script doesn't mention "Hero Sword" or "Secret Map" literally,
        # so overwrite should produce [].
        assert bible["data"]["scene_presence"] == [], (
            f"Expected empty scene_presence for {bible['entity_id']} "
            f"but got {bible['data']['scene_presence']}"
        )

