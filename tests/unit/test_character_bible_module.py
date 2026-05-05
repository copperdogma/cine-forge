from __future__ import annotations

from typing import Any

import pytest

from cine_forge.ai.entity_adjudication import _build_prompt as _build_entity_adjudication_prompt
from cine_forge.modules.world_building.character_bible_v1.candidate_resolution import (
    _aggregate_characters,
    _is_plausible_character_name,
    _rank_characters,
    prepare_character_candidates,
)
from cine_forge.modules.world_building.character_bible_v1.main import (
    _build_extraction_prompt,
    _extract_character_definition,
    _extract_minor_character_definition,
    _mock_minor_extract,
    run_module,
)
from cine_forge.modules.world_building.character_bible_v1.main import (
    _mock_extract as _mock_character_extract,
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
        "cine_forge.modules.world_building.character_bible_v1.candidate_resolution.adjudicate_entity_candidates",
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
        "cine_forge.modules.world_building.character_bible_v1.candidate_resolution.adjudicate_entity_candidates",
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
        "cine_forge.modules.world_building.character_bible_v1.candidate_resolution.adjudicate_entity_candidates",
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
    for artifact in result["artifacts"]:
        if artifact["artifact_type"] != "character_bible":
            continue
        adjudication = artifact["metadata"]["annotations"]["entity_adjudication"]
        assert adjudication["input_candidate_count"] == 3
        assert adjudication["approved_candidate_count"] == 3
        assert adjudication["decision_trace_count"] == 3


def _scene_index_with_brick_aliases() -> dict[str, Any]:
    return {
        "total_scenes": 2,
        "unique_characters": ["BRICK", "BRICK BRADDOCK"],
        "unique_locations": ["PATIO", "GARAGE"],
        "estimated_runtime_minutes": 2.0,
        "entries": [
            {
                "scene_id": "scene_001",
                "characters_present": ["BRICK", "BRICK BRADDOCK"],
            },
            {
                "scene_id": "scene_002",
                "characters_present": ["BRICK"],
            },
        ],
    }


def _canonical_payload_with_brick_aliases() -> dict[str, Any]:
    return {
        "title": "Brick Alias Test",
        "script_text": """EXT. BRICK'S PATIO - DAY
Brick Braddock sits beside the pool.

BRICK
Retirement is killing me.

INT. GARAGE - DAY
BRICK
Let's go.""",
        "line_count": 9,
        "scene_count": 2,
        "normalization": {
            "source_format": "screenplay",
            "strategy": "test",
            "rationale": "test",
            "overall_confidence": 1.0,
        },
    }


@pytest.mark.unit
def test_discovery_backed_aliases_are_adjudicated_and_collapsed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen_candidates: list[str] = []
    seen_source_hints: list[str] = []

    def _fake_adjudication(
        **kwargs: Any,
    ) -> tuple[list[EntityAdjudicationDecision], dict[str, Any]]:
        seen_candidates.extend(item["candidate"] for item in kwargs["candidates"])
        seen_source_hints.extend(str(item.get("source_hint")) for item in kwargs["candidates"])
        decisions = [
            EntityAdjudicationDecision(
                candidate="BRICK",
                verdict="valid",
                canonical_name="BRICK",
                rationale="dialogue cue for Brick Braddock",
                confidence=0.97,
            ),
            EntityAdjudicationDecision(
                candidate="BRICK BRADDOCK",
                verdict="valid",
                canonical_name="BRICK",
                rationale="full name for the same character",
                confidence=0.97,
            ),
        ]
        return decisions, {
            "model": "fixture-adjudicator",
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": 0.0,
        }

    monkeypatch.setattr(
        "cine_forge.modules.world_building.character_bible_v1.candidate_resolution.adjudicate_entity_candidates",
        _fake_adjudication,
    )

    result = run_module(
        inputs={
            "scene_index": _scene_index_with_brick_aliases(),
            "canonical_script": _canonical_payload_with_brick_aliases(),
            "discovery_results": {
                "characters": ["BRICK", "BRICK BRADDOCK"],
                "locations": [],
                "props": [],
                "script_title": "Brick Alias Test",
                "processing_metadata": {},
            },
        },
        params={"model": "mock"},
        context={"run_id": "unit", "stage_id": "world_building"},
    )

    bible_ids = {
        artifact["entity_id"]
        for artifact in result["artifacts"]
        if artifact["artifact_type"] == "character_bible"
    }
    assert seen_candidates == ["BRICK", "BRICK BRADDOCK"]
    assert seen_source_hints == [
        "entity_discovery+scene_index.unique_characters",
        "entity_discovery+scene_index.unique_characters",
    ]
    assert "brick" in bible_ids
    assert "brick_braddock" not in bible_ids

    brick_bible = next(
        artifact
        for artifact in result["artifacts"]
        if artifact["artifact_type"] == "character_bible" and artifact["entity_id"] == "brick"
    )
    assert brick_bible["data"]["scene_presence"] == ["scene_001", "scene_002"]
    assert brick_bible["data"]["aliases"] == ["BRICK BRADDOCK"]
    adjudication = brick_bible["metadata"]["annotations"]["entity_adjudication"]
    assert adjudication["input_candidate_count"] == 2
    assert adjudication["approved_candidate_count"] == 1
    assert adjudication["decision_trace_count"] == 2


@pytest.mark.unit
def test_discovery_backed_candidates_reach_adjudication_before_plausibility_filter() -> None:
    seen_candidates: list[str] = []

    def _fake_adjudication(
        **kwargs: Any,
    ) -> tuple[list[EntityAdjudicationDecision], dict[str, Any]]:
        seen_candidates.extend(item["candidate"] for item in kwargs["candidates"])
        return [
            EntityAdjudicationDecision(
                candidate="VOICE ON INTERCOM",
                verdict="invalid",
                rationale="sound cue, not a character",
                confidence=0.98,
            )
        ], {
            "model": "fixture-adjudicator",
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": 0.0,
        }

    _, candidates, rejected, decisions, _ = prepare_character_candidates(
        canonical_script={"script_text": "VOICE ON INTERCOM\nStay alert."},
        scene_index={
            "unique_characters": ["VOICE ON INTERCOM"],
            "entries": [
                {
                    "scene_id": "scene_001",
                    "characters_present": ["VOICE ON INTERCOM"],
                }
            ],
        },
        discovery_results={
            "characters": ["VOICE ON INTERCOM"],
            "locations": [],
            "props": [],
            "script_title": "Adjudication Trace Test",
            "processing_metadata": {},
        },
        min_appearances=3,
        model="mock",
        adjudicator=_fake_adjudication,
    )

    assert seen_candidates == ["VOICE ON INTERCOM"]
    assert candidates == []
    assert rejected[0]["candidate"] == "VOICE ON INTERCOM"
    assert decisions[0]["outcome"] == "rejected_by_verdict"


@pytest.mark.unit
def test_alias_merge_deduplicates_shared_scene_counts() -> None:
    def _fake_adjudication(
        **_: Any,
    ) -> tuple[list[EntityAdjudicationDecision], dict[str, Any]]:
        return [
            EntityAdjudicationDecision(
                candidate="BRICK",
                verdict="valid",
                canonical_name="BRICK",
                rationale="dialogue cue for Brick Braddock",
                confidence=0.97,
            ),
            EntityAdjudicationDecision(
                candidate="BRICK BRADDOCK",
                verdict="valid",
                canonical_name="BRICK",
                rationale="full name for the same character",
                confidence=0.97,
            ),
        ], {
            "model": "fixture-adjudicator",
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": 0.0,
        }

    _, candidates, rejected, decisions, _ = prepare_character_candidates(
        canonical_script=_canonical_payload_with_brick_aliases(),
        scene_index=_scene_index_with_brick_aliases(),
        discovery_results={
            "characters": ["BRICK", "BRICK BRADDOCK"],
            "locations": [],
            "props": [],
            "script_title": "Brick Alias Test",
            "processing_metadata": {},
        },
        min_appearances=3,
        model="mock",
        adjudicator=_fake_adjudication,
    )

    assert rejected == []
    assert len(decisions) == 2
    assert candidates == [
        {
            "name": "BRICK",
            "aliases": ["BRICK BRADDOCK"],
            "scene_count": 2,
            "dialogue_count": 2,
            "scene_presence": ["scene_001", "scene_002"],
            "score": 6,
        }
    ]


@pytest.mark.unit
def test_alias_merge_keeps_strongest_source_candidate_as_surviving_identity() -> None:
    def _fake_adjudication(
        **_: Any,
    ) -> tuple[list[EntityAdjudicationDecision], dict[str, Any]]:
        return [
            EntityAdjudicationDecision(
                candidate="BRICK",
                verdict="valid",
                canonical_name="BRICK BRADDOCK",
                rationale="dialogue cue and full name refer to one character",
                confidence=0.97,
            ),
            EntityAdjudicationDecision(
                candidate="BRICK BRADDOCK",
                verdict="valid",
                canonical_name="BRICK BRADDOCK",
                rationale="full name for the same character",
                confidence=0.97,
            ),
        ], {
            "model": "fixture-adjudicator",
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": 0.0,
        }

    _, candidates, rejected, decisions, _ = prepare_character_candidates(
        canonical_script=_canonical_payload_with_brick_aliases(),
        scene_index=_scene_index_with_brick_aliases(),
        discovery_results={
            "characters": ["BRICK", "BRICK BRADDOCK"],
            "locations": [],
            "props": [],
            "script_title": "Brick Alias Test",
            "processing_metadata": {},
        },
        min_appearances=3,
        model="mock",
        adjudicator=_fake_adjudication,
    )

    assert rejected == []
    assert len(decisions) == 2
    assert {decision["resolved_name"] for decision in decisions} == {"BRICK BRADDOCK"}
    assert {decision["surviving_name"] for decision in decisions} == {"BRICK"}
    assert candidates == [
        {
            "name": "BRICK",
            "aliases": ["BRICK BRADDOCK"],
            "scene_count": 2,
            "dialogue_count": 2,
            "scene_presence": ["scene_001", "scene_002"],
            "score": 6,
        }
    ]


@pytest.mark.unit
def test_character_extraction_prompt_uses_alias_scene_presence_context() -> None:
    script = {
        "script_text": "\n".join(
            [
                "EXT. PATIO - DAY",
                "Brick Braddock watches the empty pool.",
                "",
                "INT. GARAGE - DAY",
                "BRICK",
                "Let's go.",
            ]
        )
    }
    scene_index = {
        "entries": [
            {
                "scene_id": "scene_001",
                "characters_present": ["BRICK BRADDOCK"],
                "source_span": {"start_line": 1, "end_line": 3},
            },
            {
                "scene_id": "scene_002",
                "characters_present": ["BRICK"],
                "source_span": {"start_line": 4, "end_line": 6},
            },
        ]
    }
    entry = {
        "name": "BRICK",
        "aliases": ["BRICK BRADDOCK"],
        "scene_count": 2,
        "dialogue_count": 1,
        "scene_presence": ["scene_001", "scene_002"],
    }

    prompt = _build_extraction_prompt(
        char_name="BRICK",
        entry=entry,
        script=script,
        index=scene_index,
    )

    assert "Known aliases: BRICK BRADDOCK" in prompt
    assert "Brick Braddock watches the empty pool." in prompt
    assert "BRICK\nLet's go." in prompt


@pytest.mark.unit
def test_character_extraction_preserves_entry_aliases_when_model_omits_them(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entry = {
        "name": "BRICK",
        "aliases": ["BRICK BRADDOCK"],
        "scene_count": 2,
        "dialogue_count": 1,
        "scene_presence": ["scene_001", "scene_002"],
        "score": 5,
    }

    def _fake_call_llm(**_: Any) -> tuple[Any, dict[str, Any]]:
        definition = _mock_character_extract("BRICK", {**entry, "aliases": []})
        return definition, {
            "model": "fixture",
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": 0.0,
        }

    monkeypatch.setattr(
        "cine_forge.modules.world_building.character_bible_v1.main.call_llm",
        _fake_call_llm,
    )

    definition, _ = _extract_character_definition(
        char_name="BRICK",
        entry=entry,
        canonical_script=_canonical_payload_with_brick_aliases(),
        scene_index=_scene_index_with_brick_aliases(),
        model="fixture-model",
    )

    assert definition.aliases == ["BRICK BRADDOCK"]


@pytest.mark.unit
def test_entity_adjudication_prompt_allows_safe_aliases_without_numbered_role_merges() -> None:
    prompt = _build_entity_adjudication_prompt(
        entity_type="character",
        candidates=[
            {"candidate": "BRICK", "scene_count": 2, "dialogue_count": 2},
            {"candidate": "BRICK BRADDOCK", "scene_count": 1, "dialogue_count": 0},
            {"candidate": "THUG 1", "scene_count": 1, "dialogue_count": 1},
            {"candidate": "THUG 2", "scene_count": 1, "dialogue_count": 1},
        ],
        script_text="Brick Braddock is called BRICK. THUG 1 and THUG 2 are different men.",
    )

    assert "may collapse aliases" in prompt
    assert "Do NOT collapse candidates only because one string contains another" in prompt
    assert "THUG 1 and THUG 2 separate" in prompt


@pytest.mark.unit
def test_entity_adjudication_prompt_keeps_character_specific_alias_rules_out_of_locations() -> None:
    prompt = _build_entity_adjudication_prompt(
        entity_type="location",
        candidates=[
            {"candidate": "BRICK'S HOUSE", "scene_count": 2},
            {"candidate": "BRADDOCK HOME", "scene_count": 1},
        ],
        script_text="Brick's house is not necessarily every Braddock home.",
    )

    assert "target entity" in prompt
    assert "canonical character" not in prompt
    assert "THUG 1" not in prompt


@pytest.mark.unit
def test_character_extraction_helpers_forward_output_budgets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, Any]] = []
    entry = {
        "name": "ARIA",
        "scene_count": 3,
        "dialogue_count": 2,
        "scene_presence": ["scene_001"],
        "score": 8,
    }

    def _fake_call_llm(**kwargs: Any) -> tuple[Any, dict[str, Any]]:
        calls.append(kwargs)
        if len(calls) == 1:
            return _mock_character_extract("ARIA", entry), {
                "model": "fixture",
                "input_tokens": 0,
                "output_tokens": 0,
                "estimated_cost_usd": 0.0,
            }
        return _mock_minor_extract("ARIA", entry), {
            "model": "fixture",
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": 0.0,
        }

    monkeypatch.setattr(
        "cine_forge.modules.world_building.character_bible_v1.main._build_extraction_prompt",
        lambda *args, **kwargs: "full-prompt",
    )
    monkeypatch.setattr(
        "cine_forge.modules.world_building.character_bible_v1.main._build_lightweight_prompt",
        lambda *args, **kwargs: "minor-prompt",
    )
    monkeypatch.setattr(
        "cine_forge.modules.world_building.character_bible_v1.main.call_llm",
        _fake_call_llm,
    )

    _extract_character_definition(
        char_name="ARIA",
        entry=entry,
        canonical_script=_canonical_payload(),
        scene_index=_scene_index_payload(),
        model="claude-sonnet-4-6",
        max_tokens=5555,
    )
    _extract_minor_character_definition(
        char_name="ARIA",
        entry=entry,
        canonical_script=_canonical_payload(),
        scene_index=_scene_index_payload(),
        model="claude-sonnet-4-6",
        max_tokens=2222,
    )

    assert calls[0]["max_tokens"] == 5555
    assert calls[0]["fail_on_truncation"] is True
    assert calls[1]["max_tokens"] == 2222
    assert calls[1]["fail_on_truncation"] is True
