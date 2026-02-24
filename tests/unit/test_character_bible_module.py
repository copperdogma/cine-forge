from __future__ import annotations

from typing import Any

import pytest

from cine_forge.modules.world_building.character_bible_v1.main import (
    _aggregate_characters,
    _is_plausible_character_name,
    _rank_characters,
    run_module,
)
from cine_forge.schemas import EntityAdjudicationDecision


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
    # 2 characters, each produces a character_bible AND a bible_manifest
    assert len(artifacts) == 4
    ids = {a["entity_id"] for a in artifacts}
    assert "aria" in ids
    assert "character_aria" in ids
    assert "noah" in ids
    assert "character_noah" in ids


@pytest.mark.unit
def test_run_module_skips_invalid_candidates_via_adjudication(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _fake_adjudication(**_: Any) -> tuple[list[EntityAdjudicationDecision], dict[str, Any]]:
        decisions = [
            EntityAdjudicationDecision(
                candidate="ARIA",
                verdict="valid",
                canonical_name="ARIA",
                rationale="principal character",
                confidence=0.95,
            ),
            EntityAdjudicationDecision(
                candidate="NOAH",
                verdict="invalid",
                rationale="dialogue fragment in this fixture",
                confidence=0.91,
            ),
        ]
        return decisions, {
            "model": "mock",
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": 0.0,
        }

    monkeypatch.setattr(
        "cine_forge.modules.world_building.character_bible_v1.main.adjudicate_entity_candidates",
        _fake_adjudication,
    )

    result = run_module(
        inputs={
            "scene_index": _scene_index_payload(),
            "canonical_script": _canonical_payload(),
        },
        params={"model": "mock"},
        context={"run_id": "unit", "stage_id": "world_building"},
    )

    artifacts = result["artifacts"]
    ids = {a["entity_id"] for a in artifacts}
    assert "aria" in ids
    assert "character_aria" in ids
    assert "noah" not in ids
    assert "character_noah" not in ids


@pytest.mark.unit
def test_run_module_skips_retyped_candidates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _fake_adjudication(**_: Any) -> tuple[list[EntityAdjudicationDecision], dict[str, Any]]:
        decisions = [
            EntityAdjudicationDecision(
                candidate="ARIA",
                verdict="retype",
                target_entity_type="location",
                canonical_name="ARIA'S OFFICE",
                rationale="candidate is a place reference, not a person",
                confidence=0.93,
            ),
            EntityAdjudicationDecision(
                candidate="NOAH",
                verdict="valid",
                canonical_name="NOAH",
                rationale="actual character",
                confidence=0.95,
            ),
        ]
        return decisions, {
            "model": "mock",
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": 0.0,
        }

    monkeypatch.setattr(
        "cine_forge.modules.world_building.character_bible_v1.main.adjudicate_entity_candidates",
        _fake_adjudication,
    )

    result = run_module(
        inputs={
            "scene_index": _scene_index_payload(),
            "canonical_script": _canonical_payload(),
        },
        params={"model": "mock"},
        context={"run_id": "unit", "stage_id": "world_building"},
    )

    artifacts = result["artifacts"]
    ids = {a["entity_id"] for a in artifacts}
    assert "aria" not in ids
    assert "character_aria" not in ids
    assert "noah" in ids
    assert "character_noah" in ids


@pytest.mark.unit
def test_run_module_keeps_valid_candidate_when_llm_canonical_name_is_not_plausible(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _fake_adjudication(**_: Any) -> tuple[list[EntityAdjudicationDecision], dict[str, Any]]:
        decisions = [
            EntityAdjudicationDecision(
                candidate="ARIA",
                verdict="valid",
                canonical_name="THE ARIA",
                rationale="attempted canonicalization with article prefix",
                confidence=0.9,
            ),
            EntityAdjudicationDecision(
                candidate="NOAH",
                verdict="valid",
                canonical_name="NOAH",
                rationale="valid character",
                confidence=0.95,
            ),
        ]
        return decisions, {
            "model": "mock",
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": 0.0,
        }

    monkeypatch.setattr(
        "cine_forge.modules.world_building.character_bible_v1.main.adjudicate_entity_candidates",
        _fake_adjudication,
    )

    result = run_module(
        inputs={
            "scene_index": _scene_index_payload(),
            "canonical_script": _canonical_payload(),
        },
        params={"model": "mock"},
        context={"run_id": "unit", "stage_id": "world_building"},
    )

    artifacts = result["artifacts"]
    ids = {a["entity_id"] for a in artifacts}
    assert "aria" in ids
    assert "character_aria" in ids
    assert "noah" in ids


# --- Story 077: Prominence tier and minor character tests ---


@pytest.mark.unit
def test_thug_1_passes_plausibility_check() -> None:
    """THUG 1 is a named character and should pass plausibility."""
    assert _is_plausible_character_name("THUG 1") is True
    assert _is_plausible_character_name("GUARD 2") is True
    assert _is_plausible_character_name("COP 3") is True


@pytest.mark.unit
def test_non_character_strings_still_rejected() -> None:
    """Sound cues, formatting tokens, and single stopwords should still fail."""
    assert _is_plausible_character_name("HE") is False
    assert _is_plausible_character_name("CUT") is False
    assert _is_plausible_character_name("INT") is False
    # Pure digits
    assert _is_plausible_character_name("123") is False
    # Too many tokens
    assert _is_plausible_character_name("A B C D") is False


@pytest.mark.unit
def test_prominence_field_present_in_mock_output() -> None:
    """All character_bible artifacts should include a prominence field."""
    result = run_module(
        inputs={
            "scene_index": _scene_index_payload(),
            "canonical_script": _canonical_payload(),
        },
        params={"model": "mock"},
        context={"run_id": "unit", "stage_id": "world_building"},
    )
    for artifact in result["artifacts"]:
        if artifact["artifact_type"] == "character_bible":
            assert "prominence" in artifact["data"], (
                f"character_bible for {artifact['entity_id']} missing prominence field"
            )
            assert artifact["data"]["prominence"] in ("primary", "secondary", "minor")


def _scene_index_with_minor_characters() -> dict[str, Any]:
    """Fixture with both major and minor (numbered functional) characters."""
    return {
        "total_scenes": 3,
        "unique_characters": ["ARIA", "NOAH", "THUG 1", "THUG 2"],
        "unique_locations": ["STUDIO"],
        "estimated_runtime_minutes": 3.0,
        "entries": [
            {
                "scene_id": "scene_001",
                "characters_present": ["ARIA", "NOAH", "THUG 1"],
            },
            {
                "scene_id": "scene_002",
                "characters_present": ["ARIA", "THUG 2"],
            },
            {
                "scene_id": "scene_003",
                "characters_present": ["ARIA"],
            },
        ],
    }


def _canonical_payload_with_thugs() -> dict[str, Any]:
    return {
        "title": "Test",
        "script_text": """INT. STUDIO - DAY
ARIA
Hello.

NOAH
Stay back!

THUG 1
(menacing)
Give me the money.

EXT. ROOF - NIGHT
ARIA
We need to run.

THUG 2
Not so fast.

INT. OFFICE - DAY
ARIA
Listen.""",
        "line_count": 20,
        "scene_count": 3,
        "normalization": {
            "source_format": "screenplay",
            "strategy": "test",
            "rationale": "test",
            "overall_confidence": 1.0,
        },
    }


@pytest.mark.unit
def test_minor_characters_retained_via_discovery_results() -> None:
    """When discovery_results include minor characters, they should get bibles."""
    result = run_module(
        inputs={
            "scene_index": _scene_index_with_minor_characters(),
            "canonical_script": _canonical_payload_with_thugs(),
            "discovery_results": {
                "characters": ["ARIA", "NOAH", "THUG 1", "THUG 2"],
                "locations": [],
                "props": [],
                "script_title": "Test",
                "processing_metadata": {},
            },
        },
        params={"model": "mock"},
        context={"run_id": "unit", "stage_id": "world_building"},
    )
    bible_ids = {
        a["entity_id"]
        for a in result["artifacts"]
        if a["artifact_type"] == "character_bible"
    }
    assert "aria" in bible_ids
    assert "noah" in bible_ids
    assert "thug_1" in bible_ids
    assert "thug_2" in bible_ids


@pytest.mark.unit
def test_minor_characters_get_minor_prominence() -> None:
    """Low-score characters routed to lightweight extraction should have prominence='minor'."""
    result = run_module(
        inputs={
            "scene_index": _scene_index_with_minor_characters(),
            "canonical_script": _canonical_payload_with_thugs(),
            "discovery_results": {
                "characters": ["ARIA", "NOAH", "THUG 1", "THUG 2"],
                "locations": [],
                "props": [],
                "script_title": "Test",
                "processing_metadata": {},
            },
        },
        params={"model": "mock"},
        context={"run_id": "unit", "stage_id": "world_building"},
    )
    for artifact in result["artifacts"]:
        if artifact["artifact_type"] != "character_bible":
            continue
        eid = artifact["entity_id"]
        prominence = artifact["data"]["prominence"]
        if eid in ("thug_1", "thug_2"):
            # Minor characters (score < 4) should get minor prominence
            assert prominence == "minor", f"{eid} expected minor, got {prominence}"
        elif eid in ("aria",):
            # Major character: full extraction mock defaults to secondary
            assert prominence == "secondary", f"{eid} expected secondary, got {prominence}"


@pytest.mark.unit
def test_discovery_only_characters_still_extracted() -> None:
    """Characters in discovery_results but NOT in scene_index should still get bibles.

    Regression: scene extraction may normalize 'THUG 1'/'THUG 2' into a single 'THUG'
    entry, but entity discovery (LLM-driven) preserves the numbered variants. The bible
    module must create stub candidates for discovery-only names so they don't silently
    vanish.
    """
    # Scene index only has "THUG" (collapsed), not "THUG 1"/"THUG 2"
    scene_index: dict[str, Any] = {
        "total_scenes": 2,
        "unique_characters": ["ARIA", "THUG"],
        "unique_locations": ["STUDIO"],
        "estimated_runtime_minutes": 2.0,
        "entries": [
            {"scene_id": "scene_001", "characters_present": ["ARIA", "THUG"]},
            {"scene_id": "scene_002", "characters_present": ["ARIA"]},
        ],
    }
    canonical = {
        "title": "Test",
        "script_text": "INT. STUDIO - DAY\nARIA\nHello.\n\nTHUG 1\nStop!\n\nTHUG 2\nGet them!",
        "line_count": 8,
        "scene_count": 2,
        "normalization": {
            "source_format": "screenplay",
            "strategy": "test",
            "rationale": "test",
            "overall_confidence": 1.0,
        },
    }
    result = run_module(
        inputs={
            "scene_index": scene_index,
            "canonical_script": canonical,
            "discovery_results": {
                "characters": ["ARIA", "THUG 1", "THUG 2"],
                "locations": [],
                "props": [],
                "script_title": "Test",
                "processing_metadata": {},
            },
        },
        params={"model": "mock"},
        context={"run_id": "unit", "stage_id": "world_building"},
    )
    bible_ids = {
        a["entity_id"]
        for a in result["artifacts"]
        if a["artifact_type"] == "character_bible"
    }
    assert "aria" in bible_ids
    assert "thug_1" in bible_ids, f"THUG 1 missing from bibles: {bible_ids}"
    assert "thug_2" in bible_ids, f"THUG 2 missing from bibles: {bible_ids}"
