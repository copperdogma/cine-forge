from __future__ import annotations

from typing import Any

import pytest

from cine_forge.modules.world_building.location_bible_v1.main import (
    _extract_location_definition,
    run_module,
)
from cine_forge.modules.world_building.location_bible_v1.main import (
    _mock_extract as _mock_location_extract,
)
from cine_forge.schemas import EntityAdjudicationDecision


@pytest.fixture
def mock_inputs() -> dict[str, Any]:
    return {
        "normalize": {
            "script_text": "INT. STUDIO - DAY\nARIA is here.",
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


@pytest.mark.unit
def test_location_bible_module_skips_discovery_backed_adjudication(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _unexpected_adjudication(
        **_: Any,
    ) -> tuple[list[EntityAdjudicationDecision], dict[str, Any]]:
        raise AssertionError("discovery-backed locations should not be re-adjudicated")

    monkeypatch.setattr(
        "cine_forge.modules.world_building.location_bible_v1.main.adjudicate_entity_candidates",
        _unexpected_adjudication,
    )

    result = run_module(
        inputs={
            "canonical_script": {"script_text": "EXT. CITY CENTRE - NIGHT\nARIA runs."},
            "scene_index": {
                "unique_locations": ["CITY CENTRE"],
                "entries": [{"scene_id": "scene_001", "location": "CITY CENTRE"}],
            },
            "discovery_results": {
                "characters": [],
                "locations": ["EXT. CITY CENTRE - NIGHT"],
                "props": [],
                "script_title": "Test",
                "processing_metadata": {},
            },
        },
        params={"model": "mock"},
        context={},
    )

    location_ids = {
        artifact["entity_id"]
        for artifact in result["artifacts"]
        if artifact["artifact_type"] == "location_bible"
    }
    assert "city_centre" in location_ids


@pytest.mark.unit
def test_location_bible_module_discovery_fallback_still_adjudicates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called = False

    def _fake_adjudication(**_: Any) -> tuple[list[EntityAdjudicationDecision], dict[str, Any]]:
        nonlocal called
        called = True
        return [
            EntityAdjudicationDecision(
                candidate="STUDIO",
                verdict="valid",
                canonical_name="STUDIO",
                rationale="fallback should still validate scene-index candidates",
                confidence=0.94,
            )
        ], {
            "model": "mock",
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": 0.0,
        }

    monkeypatch.setattr(
        "cine_forge.modules.world_building.location_bible_v1.main.adjudicate_entity_candidates",
        _fake_adjudication,
    )

    result = run_module(
        inputs={
            "canonical_script": {"script_text": "INT. STUDIO - DAY\nARIA is here."},
            "scene_index": {
                "unique_locations": ["STUDIO"],
                "entries": [{"scene_id": "scene_001", "location": "STUDIO"}],
            },
            "discovery_results": {
                "characters": [],
                "locations": ["EXT. BEACH - NIGHT"],
                "props": [],
                "script_title": "Test",
                "processing_metadata": {},
            },
        },
        params={"model": "mock"},
        context={},
    )

    assert called is True
    location_ids = {
        artifact["entity_id"]
        for artifact in result["artifacts"]
        if artifact["artifact_type"] == "location_bible"
    }
    assert "studio" in location_ids


@pytest.mark.unit
def test_location_extraction_helper_forwards_output_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, Any]] = []
    entry = {"name": "STUDIO", "scene_count": 1, "scene_presence": ["scene_001"]}

    def _fake_call_llm(**kwargs: Any) -> tuple[Any, dict[str, Any]]:
        calls.append(kwargs)
        return _mock_location_extract("STUDIO", entry), {
            "model": "fixture",
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": 0.0,
        }

    monkeypatch.setattr(
        "cine_forge.modules.world_building.location_bible_v1.main._build_extraction_prompt",
        lambda *args, **kwargs: "location-prompt",
    )
    monkeypatch.setattr(
        "cine_forge.modules.world_building.location_bible_v1.main.call_llm",
        _fake_call_llm,
    )

    _extract_location_definition(
        loc_name="STUDIO",
        entry=entry,
        canonical_script={"script_text": "INT. STUDIO - DAY"},
        scene_index={"entries": [{"scene_id": "scene_001", "location": "STUDIO"}]},
        model="claude-sonnet-4-6",
        max_tokens=3333,
    )

    assert calls[0]["max_tokens"] == 3333
    assert calls[0]["fail_on_truncation"] is True
