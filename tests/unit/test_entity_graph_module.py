from __future__ import annotations

from typing import Any

import pytest

import cine_forge.modules.world_building.entity_graph_v1.main as entity_graph_main
from cine_forge.modules.world_building.entity_graph_v1.main import (
    _build_char_resolver,
    _generate_co_occurrence_edges,
    _generate_signature_edges,
    run_module,
)
from cine_forge.schemas import EntityEdge


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


@pytest.mark.unit
def test_runtime_work_model_overrides_default_graph_model(
    mock_inputs: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def _fake_extract_new_relationships(
        character_bibles: list[dict[str, Any]],
        location_bibles: list[dict[str, Any]],
        prop_bibles: list[dict[str, Any]],
        scene_index: dict[str, Any],
        work_model: str,
    ):
        captured["model"] = work_model
        return [], {
            "model": work_model,
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": 0.0,
        }

    monkeypatch.setattr(
        entity_graph_main,
        "_extract_new_relationships",
        _fake_extract_new_relationships,
    )

    result = run_module(
        inputs=mock_inputs,
        params={},
        context={"runtime_params": {"work_model": "claude-sonnet-4-6"}},
    )

    assert captured["model"] == "claude-sonnet-4-6"
    assert result["cost"]["model"] == "claude-sonnet-4-6"


@pytest.mark.unit
def test_co_occurrence_uses_slugified_char_ids() -> None:
    """Bug fix: character IDs in co-occurrence edges must use _slugify, not .lower().
    'THE MARINER' → 'the_mariner', not 'the mariner' (spaces matter for entity lookups).
    """
    scene_index = {
        "entries": [
            {
                "scene_id": "scene_001",
                "location": "OPEN OCEAN",
                "characters_present": ["THE MARINER", "ROSE"],
            }
        ],
        "unique_locations": ["OPEN OCEAN"],
    }
    edges = _generate_co_occurrence_edges(scene_index)
    char_ids = {e.source_id for e in edges} | {e.target_id for e in edges}
    # Slugified: no spaces, underscores instead
    assert "the_mariner" in char_ids
    assert "rose" in char_ids
    # The old broken form (space-separated) should NOT appear
    assert "the mariner" not in char_ids


@pytest.mark.unit
def test_co_occurrence_uses_characters_present_ids_when_available() -> None:
    """If scene index entries carry pre-slugified IDs, use them directly."""
    scene_index = {
        "entries": [
            {
                "scene_id": "scene_001",
                "location": "BRIDGE",
                "characters_present": ["COMMANDER JACKS"],
                "characters_present_ids": ["commander_jacks"],
            }
        ],
        "unique_locations": ["BRIDGE"],
    }
    edges = _generate_co_occurrence_edges(scene_index)
    char_ids = {e.source_id for e in edges} | {e.target_id for e in edges}
    assert "commander_jacks" in char_ids


@pytest.mark.unit
def test_prop_cooccurrence_edges_generated() -> None:
    """Prop bibles with scene_presence produce prop<->character and prop<->location edges."""
    scene_index = {
        "entries": [
            {
                "scene_id": "scene_001",
                "location": "ARMORY",
                "characters_present": ["ARCHER"],
                "characters_present_ids": ["archer"],
            }
        ],
        "unique_locations": ["ARMORY"],
    }
    prop_bibles = [
        {
            "prop_id": "crossbow",
            "name": "Crossbow",
            "scene_presence": ["scene_001"],
            "associated_characters": [],
        }
    ]
    edges = _generate_co_occurrence_edges(scene_index, prop_bibles)
    prop_char_edge = next(
        (
            e for e in edges
            if e.source_type == "prop" and e.source_id == "crossbow"
            and e.target_type == "character" and e.target_id == "archer"
        ),
        None,
    )
    assert prop_char_edge is not None
    assert prop_char_edge.relationship_type == "co-occurrence"

    prop_loc_edge = next(
        (
            e for e in edges
            if e.source_type == "prop" and e.source_id == "crossbow"
            and e.target_type == "location"
        ),
        None,
    )
    assert prop_loc_edge is not None
    assert prop_loc_edge.target_id == "armory"


@pytest.mark.unit
def test_signature_prop_edges_generated() -> None:
    """Prop bibles with associated_characters produce signature_prop_of edges."""
    prop_bibles = [
        {
            "prop_id": "bandolier",
            "name": "Bandolier",
            "scene_presence": [],
            "associated_characters": ["the_mariner"],
        }
    ]
    edges = _generate_signature_edges(prop_bibles)
    assert len(edges) == 1
    e = edges[0]
    assert e.source_type == "prop"
    assert e.source_id == "bandolier"
    assert e.target_type == "character"
    assert e.target_id == "the_mariner"
    assert e.relationship_type == "signature_prop_of"
    assert e.confidence == 0.95


@pytest.mark.unit
def test_signature_edges_resolve_canonical_char_id() -> None:
    """AI writes 'the_mariner' in associated_characters but character_id is 'mariner'.
    The resolver must map the_mariner → mariner so the edge uses the canonical ID.
    """
    char_bibles = [{"character_id": "mariner", "name": "THE MARINER"}]
    prop_bibles = [
        {
            "prop_id": "bandolier",
            "name": "Bandolier",
            "scene_presence": [],
            "associated_characters": ["the_mariner"],
        }
    ]
    resolver = _build_char_resolver(char_bibles)
    edges = _generate_signature_edges(prop_bibles, resolver)
    assert len(edges) == 1
    assert edges[0].target_id == "mariner", (
        "Expected canonical ID 'mariner', got AI-written 'the_mariner'"
    )


@pytest.mark.unit
def test_char_resolver_maps_canonical_name_alias_and_article_variants() -> None:
    resolver = _build_char_resolver(
        [
            {
                "character_id": "brick",
                "name": "BRICK BRADDOCK",
                "aliases": ["THE CHAMP"],
            }
        ]
    )

    assert resolver["brick"] == "brick"
    assert resolver["the_brick"] == "brick"
    assert resolver["BRICK BRADDOCK"] == "brick"
    assert resolver["brick_braddock"] == "brick"
    assert resolver["the_brick_braddock"] == "brick"
    assert resolver["THE CHAMP"] == "brick"
    assert resolver["the_champ"] == "brick"
    assert resolver["champ"] == "brick"


@pytest.mark.unit
def test_signature_edges_resolve_display_alias_char_id() -> None:
    resolver = _build_char_resolver(
        [{"character_id": "brick", "name": "BRICK", "aliases": ["BRICK BRADDOCK"]}]
    )
    prop_bibles = [
        {
            "prop_id": "badge",
            "name": "Badge",
            "scene_presence": [],
            "associated_characters": ["BRICK BRADDOCK"],
        }
    ]

    edges = _generate_signature_edges(prop_bibles, resolver)

    assert len(edges) == 1
    assert edges[0].target_id == "brick"


@pytest.mark.unit
def test_entity_graph_resolves_scene_aliases_to_canonical_character() -> None:
    inputs = {
        "breakdown_scenes": {
            "entries": [
                {
                    "scene_id": "scene_001",
                    "location": "PATIO",
                    "characters_present": ["BRICK", "BRICK BRADDOCK"],
                },
                {
                    "scene_id": "scene_002",
                    "location": "GARAGE",
                    "characters_present": ["BRICK"],
                },
            ],
            "unique_locations": ["PATIO", "GARAGE"],
        },
        "character_bible": [
            {
                "character_id": "brick",
                "name": "BRICK",
                "aliases": ["BRICK BRADDOCK"],
                "relationships": [],
            }
        ],
        "location_bible": [],
        "prop_bible": [
            {
                "prop_id": "badge",
                "name": "Badge",
                "scene_presence": ["scene_001"],
                "associated_characters": ["brick_braddock"],
            }
        ],
    }

    result = run_module(inputs=inputs, params={"model": "mock"}, context={})
    graph_data = result["artifacts"][0]["data"]
    edges = graph_data["edges"]
    character_ids = {
        edge[key]
        for edge in edges
        for key in ("source_id", "target_id")
        if edge[key.replace("_id", "_type")] == "character"
    }

    assert graph_data["entity_count"]["character"] == 1
    assert "brick" in character_ids
    assert "brick_braddock" not in character_ids
    assert not any(
        edge["source_type"] == "character"
        and edge["target_type"] == "character"
        and edge["source_id"] == edge["target_id"]
        for edge in edges
    )
    assert any(
        edge["source_type"] == "prop"
        and edge["source_id"] == "badge"
        and edge["target_type"] == "character"
        and edge["target_id"] == "brick"
        for edge in edges
    )


@pytest.mark.unit
def test_scene_pre_slugged_alias_ids_dedupe_to_canonical_character() -> None:
    resolver = _build_char_resolver(
        [{"character_id": "brick", "name": "BRICK", "aliases": ["BRICK BRADDOCK"]}]
    )
    scene_index = {
        "entries": [
            {
                "scene_id": "scene_001",
                "location": "PATIO",
                "characters_present": ["BRICK", "BRICK BRADDOCK"],
                "characters_present_ids": ["brick", "brick_braddock"],
            }
        ],
        "unique_locations": ["PATIO"],
    }

    edges = _generate_co_occurrence_edges(scene_index, char_resolver=resolver)

    assert sum(edge.source_id == "brick" for edge in edges) == 1
    assert not any(
        edge.source_type == "character"
        and edge.target_type == "character"
        and edge.source_id == edge.target_id
        for edge in edges
    )
    assert "brick_braddock" not in {
        entity_id
        for edge in edges
        for entity_type, entity_id in (
            (edge.source_type, edge.source_id),
            (edge.target_type, edge.target_id),
        )
        if entity_type == "character"
    }


@pytest.mark.unit
def test_relationship_stub_alias_target_resolves_and_drops_self_edge() -> None:
    inputs = {
        "breakdown_scenes": {
            "entries": [
                {
                    "scene_id": "scene_001",
                    "location": "PATIO",
                    "characters_present": ["BRICK"],
                }
            ],
            "unique_locations": ["PATIO"],
        },
        "character_bible": [
            {
                "character_id": "brick",
                "name": "BRICK",
                "aliases": ["BRICK BRADDOCK"],
                "relationships": [
                    {
                        "target_character": "BRICK BRADDOCK",
                        "relationship_type": "same_person",
                        "evidence": "Brick Braddock is Brick's full name.",
                        "confidence": 0.95,
                    }
                ],
            }
        ],
        "location_bible": [],
        "prop_bible": [],
    }

    result = run_module(inputs=inputs, params={"model": "mock"}, context={})
    edges = result["artifacts"][0]["data"]["edges"]

    assert not any(edge["relationship_type"] == "same_person" for edge in edges)
    assert not any(
        edge["source_type"] == "character"
        and edge["target_type"] == "character"
        and edge["source_id"] == edge["target_id"]
        for edge in edges
    )
    assert "brick_braddock" not in {
        edge[key]
        for edge in edges
        for key in ("source_id", "target_id")
        if edge[key.replace("_id", "_type")] == "character"
    }


@pytest.mark.unit
def test_ai_relationship_edges_resolve_display_alias_and_drop_self_edge(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _fake_extract_new_relationships(
        character_bibles: list[dict[str, Any]],
        location_bibles: list[dict[str, Any]],
        prop_bibles: list[dict[str, Any]],
        scene_index: dict[str, Any],
        work_model: str,
    ):
        return [
            EntityEdge(
                source_type="character",
                source_id="BRICK BRADDOCK",
                target_type="character",
                target_id="BRICK",
                relationship_type="same_person",
                direction="symmetric",
                evidence=["AI emitted an alias edge."],
                confidence=0.8,
            ),
            EntityEdge(
                source_type="prop",
                source_id="badge",
                target_type="character",
                target_id="BRICK BRADDOCK",
                relationship_type="signature_prop_of",
                direction="source_to_target",
                evidence=["AI emitted display text for the target character."],
                confidence=0.8,
            ),
        ], {
            "model": work_model,
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": 0.0,
        }

    monkeypatch.setattr(
        entity_graph_main,
        "_extract_new_relationships",
        _fake_extract_new_relationships,
    )
    inputs = {
        "breakdown_scenes": {
            "entries": [
                {
                    "scene_id": "scene_001",
                    "location": "PATIO",
                    "characters_present": ["BRICK"],
                }
            ],
            "unique_locations": ["PATIO"],
        },
        "character_bible": [
            {
                "character_id": "brick",
                "name": "BRICK",
                "aliases": ["BRICK BRADDOCK"],
                "relationships": [],
            }
        ],
        "location_bible": [],
        "prop_bible": [
            {
                "prop_id": "badge",
                "name": "Badge",
                "scene_presence": [],
                "associated_characters": [],
            }
        ],
    }

    result = run_module(inputs=inputs, params={"model": "test-model"}, context={})
    edges = result["artifacts"][0]["data"]["edges"]
    character_ids = {
        edge[key]
        for edge in edges
        for key in ("source_id", "target_id")
        if edge[key.replace("_id", "_type")] == "character"
    }

    assert "brick" in character_ids
    assert "brick_braddock" not in character_ids
    assert "BRICK BRADDOCK" not in character_ids
    assert not any(
        edge["source_type"] == "character"
        and edge["target_type"] == "character"
        and edge["source_id"] == edge["target_id"]
        for edge in edges
    )
    assert any(
        edge["source_type"] == "prop"
        and edge["source_id"] == "badge"
        and edge["target_type"] == "character"
        and edge["target_id"] == "brick"
        and edge["relationship_type"] == "signature_prop_of"
        for edge in edges
    )


@pytest.mark.unit
def test_prop_list_in_ai_prompt_uses_prop_names(mock_inputs: dict[str, Any]) -> None:
    """Bug fix: prop_list in AI prompt must come from prop['name'], not prop.get('files', []).
    The old code always produced an empty string since PropBible dicts have no 'files' key.
    """
    # Add a prop bible to the fixture and verify the integration doesn't crash
    mock_inputs_with_prop = dict(mock_inputs)
    mock_inputs_with_prop["prop_bible"] = [
        {
            "prop_id": "laser_gun",
            "name": "Laser Gun",
            "scene_presence": [],
            "associated_characters": [],
        }
    ]
    # With model="mock" the AI pass is skipped, but we verify the module runs without
    # TypeError on the list comprehension (regression guard).
    result = run_module(inputs=mock_inputs_with_prop, params={"model": "mock"}, context={})
    assert "artifacts" in result
    assert result["artifacts"][0]["data"]["entity_count"]["prop"] == 1
