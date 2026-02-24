from unittest.mock import MagicMock

import pytest

import cine_forge.modules.world_building.entity_discovery_v1.main as discovery_main
from cine_forge.modules.world_building.entity_discovery_v1.main import (
    _normalize_character_name,
    run_module,
)

_SCRIPT = {
    "script_text": "INT. OFFICE - DAY\n\nAbe enters. He carries a RARE COIN.",
    "title": "Test",
}


@pytest.fixture(autouse=True)
def _mock_llm(monkeypatch):
    """Default mock that returns empty items — tests override via side_effect."""
    mock = MagicMock(
        return_value=(MagicMock(items=[]), {"estimated_cost_usd": 0.0})
    )
    monkeypatch.setattr(discovery_main, "call_llm", mock)
    return mock


# ── Scene-index passthrough (Story 081) ─────────────────────────────


class TestSceneIndexCharacterSource:
    """Characters come from scene_index when available, no LLM calls for characters."""

    def test_scene_index_characters_passthrough(self, _mock_llm):
        """Scene_index unique_characters become the character list with no LLM character scan."""
        inputs = {
            "canonical_script": _SCRIPT,
            "breakdown_scenes": {
                "unique_characters": ["ALICE", "BOB", "THE DETECTIVE"],
                "entries": [],
            },
        }
        params = {"discovery_model": "mock", "enable_locations": False, "enable_props": False}
        result = run_module(inputs, params, {})

        data = result["artifacts"][0]["data"]
        assert "ALICE" in data["characters"]
        assert "BOB" in data["characters"]
        assert "DETECTIVE" in data["characters"]  # THE stripped
        assert _mock_llm.call_count == 0  # no LLM calls at all

    def test_scene_index_normalization_deduplication(self, _mock_llm):
        """Duplicate names after normalization are collapsed."""
        inputs = {
            "canonical_script": _SCRIPT,
            "breakdown_scenes": {
                "unique_characters": [
                    "THE MARINER",
                    "MARINER",
                    "THUG 1",
                    "THUG 2",
                    "THUG 3",
                    "YOUNG MARINER'S DAD",
                    "DAD",
                ],
                "entries": [],
            },
        }
        params = {"discovery_model": "mock", "enable_locations": False, "enable_props": False}
        result = run_module(inputs, params, {})

        chars = result["artifacts"][0]["data"]["characters"]
        # THE MARINER and MARINER both normalize to MARINER — only one instance
        assert chars.count("MARINER") == 1
        assert "THUG 1" in chars
        assert "THUG 2" in chars
        assert "THUG 3" in chars
        # YOUNG MARINER'S DAD normalizes to YOUNG MARINERS DAD (apostrophe kept)
        assert "DAD" in chars

    def test_scene_index_metadata_shows_source(self, _mock_llm):
        """Processing metadata records character_source=scene_index."""
        inputs = {
            "canonical_script": _SCRIPT,
            "breakdown_scenes": {
                "unique_characters": ["ALICE"],
                "entries": [],
            },
        }
        params = {"discovery_model": "mock", "enable_locations": False, "enable_props": False}
        result = run_module(inputs, params, {})

        meta = result["artifacts"][0]["data"]["processing_metadata"]
        assert meta["character_source"] == "scene_index"

    def test_location_prop_scanning_still_uses_llm(self, _mock_llm):
        """Even with scene_index characters, locations/props still go through LLM scanning."""
        _mock_llm.side_effect = [
            (MagicMock(items=["OFFICE"]), {"estimated_cost_usd": 0.01}),
            (MagicMock(items=["RARE COIN"]), {"estimated_cost_usd": 0.01}),
        ]
        inputs = {
            "canonical_script": _SCRIPT,
            "breakdown_scenes": {
                "unique_characters": ["ALICE"],
                "entries": [],
            },
        }
        params = {"discovery_model": "mock"}
        result = run_module(inputs, params, {})

        data = result["artifacts"][0]["data"]
        assert "ALICE" in data["characters"]
        assert "OFFICE" in data["locations"]
        assert "RARE COIN" in data["props"]
        # LLM called for locations (1 chunk) + props (1 chunk) = 2 calls, NOT for characters
        assert _mock_llm.call_count == 2


# ── Fallback: no scene_index → LLM character scanning ───────────────


class TestLLMFallback:
    """Without scene_index, characters are discovered via LLM (original behavior)."""

    def test_llm_character_scanning_without_scene_index(self, _mock_llm):
        """When no scene_index is provided, characters come from LLM scanning."""
        _mock_llm.side_effect = [
            (MagicMock(items=["ABE"]), {"estimated_cost_usd": 0.01}),
        ]
        inputs = {"canonical_script": _SCRIPT}
        params = {
            "discovery_model": "mock",
            "enable_locations": False,
            "enable_props": False,
        }
        result = run_module(inputs, params, {})

        data = result["artifacts"][0]["data"]
        assert "ABE" in data["characters"]
        assert data["processing_metadata"]["character_source"] == "llm"
        assert _mock_llm.call_count == 1

    def test_refine_mode_bootstraps(self, _mock_llm):
        """Verify that discovery bootstraps from existing bibles (no scene_index)."""
        _mock_llm.side_effect = [
            (MagicMock(items=["ABE"]), {"estimated_cost_usd": 0.01}),
            (MagicMock(items=["GOLD COIN"]), {"estimated_cost_usd": 0.01}),
        ]
        inputs = {
            "canonical_script": _SCRIPT,
            "character_bible": [{"name": "ABE"}],
            "prop_bible": [{"canonical_name": "GOLD COIN"}],
        }
        params = {"discovery_model": "mock", "enable_locations": False}
        result = run_module(inputs, params, {})

        data = result["artifacts"][0]["data"]
        assert "ABE" in data["characters"]
        assert "GOLD COIN" in data["props"]

        # Verify bootstrap names appear in prompts
        char_prompt = _mock_llm.call_args_list[0][1]["prompt"]
        assert "ABE" in char_prompt
        prop_prompt = _mock_llm.call_args_list[1][1]["prompt"]
        assert "GOLD COIN" in prop_prompt


# ── Normalization unit tests ─────────────────────────────────────────


class TestNormalizeCharacterName:
    def test_the_prefix_stripped(self):
        assert _normalize_character_name("THE MARINER") == "MARINER"

    def test_short_name_keeps_the(self):
        assert _normalize_character_name("THE DOC") == "THE DOC"

    def test_parenthetical_stripped(self):
        assert _normalize_character_name("ROSE (V.O.)") == "ROSE"

    def test_whitespace_collapsed(self):
        assert _normalize_character_name("  THUG   3  ") == "THUG 3"

    def test_empty_string(self):
        assert _normalize_character_name("") == ""
