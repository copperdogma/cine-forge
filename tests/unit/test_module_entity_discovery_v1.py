from unittest.mock import MagicMock

import pytest

import cine_forge.modules.world_building.entity_discovery_v1.main as discovery_main
from cine_forge.modules.world_building.entity_discovery_v1.main import (
    _extract_scene_index_signals,
    _find_recall_gaps,
    _normalize_character_name,
    _normalize_entity_name,
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


# ── Entity name normalization (Story 124) ──────────────────────────


class TestNormalizeEntityName:
    def test_location_strips_int_ext(self):
        assert _normalize_entity_name("INT. OFFICE", "locations") == "OFFICE"
        assert _normalize_entity_name("EXT. DOCK", "locations") == "DOCK"
        assert _normalize_entity_name(
            "INT./EXT. PARKING LOT", "locations"
        ) == "PARKING LOT"

    def test_location_strips_time_of_day(self):
        assert _normalize_entity_name(
            "OFFICE - DAY", "locations"
        ) == "OFFICE"
        assert _normalize_entity_name(
            "DOCK - NIGHT", "locations"
        ) == "DOCK"

    def test_location_strips_both(self):
        assert _normalize_entity_name(
            "INT. OFFICE - DAY", "locations"
        ) == "OFFICE"

    def test_props_normalizes(self):
        assert _normalize_entity_name("rare coin", "props") == "RARE COIN"

    def test_characters_delegates(self):
        assert _normalize_entity_name(
            "THE MARINER", "characters"
        ) == "MARINER"


# ── Scene index signal extraction (Story 124) ─────────────────────


class TestExtractSceneIndexSignals:
    def test_extracts_locations(self):
        si = {
            "unique_locations": ["INT. OFFICE - DAY", "EXT. DOCK - NIGHT"],
            "entries": [],
        }
        signals = _extract_scene_index_signals(si)
        assert "OFFICE" in signals["locations"]
        assert "DOCK" in signals["locations"]

    def test_aggregates_props_from_entries(self):
        si = {
            "unique_locations": [],
            "entries": [
                {"props_mentioned": ["RARE COIN", "GUN"]},
                {"props_mentioned": ["GUN", "LETTER"]},
            ],
        }
        signals = _extract_scene_index_signals(si)
        assert set(signals["props"]) == {"RARE COIN", "GUN", "LETTER"}

    def test_empty_scene_index(self):
        signals = _extract_scene_index_signals({"entries": []})
        assert "locations" not in signals
        assert "props" not in signals


# ── Recall gap detection (Story 124) ──────────────────────────────


class TestFindRecallGaps:
    def test_no_gaps(self):
        gaps = _find_recall_gaps(
            ["OFFICE", "DOCK"], ["OFFICE", "DOCK"], "locations"
        )
        assert gaps == []

    def test_detects_missing(self):
        gaps = _find_recall_gaps(
            ["OFFICE"], ["OFFICE", "DOCK"], "locations"
        )
        assert gaps == ["DOCK"]

    def test_substring_match_handles_aliases(self):
        gaps = _find_recall_gaps(
            ["RUDDY & GREENE BUILDING"],
            ["RUDDY GREENE BUILDING"],
            "locations",
        )
        # "RUDDY GREENE BUILDING" is substring of normalized discovered
        assert gaps == []

    def test_empty_reference(self):
        gaps = _find_recall_gaps(["OFFICE"], [], "locations")
        assert gaps == []


# ── Verification flow integration (Story 124) ─────────────────────


class TestVerificationFlow:
    def test_no_gaps_no_extra_calls(self, _mock_llm):
        """When scene_index locations match discovered, no verification call."""
        _mock_llm.side_effect = [
            # locations chunk
            (MagicMock(items=["OFFICE"]), {"estimated_cost_usd": 0.01}),
            # props chunk
            (MagicMock(items=["COIN"]), {"estimated_cost_usd": 0.01}),
        ]
        inputs = {
            "canonical_script": _SCRIPT,
            "breakdown_scenes": {
                "unique_characters": ["ABE"],
                "unique_locations": ["OFFICE"],
                "entries": [{"props_mentioned": ["COIN"]}],
            },
        }
        params = {"discovery_model": "mock"}
        result = run_module(inputs, params, {})

        meta = result["artifacts"][0]["data"]["processing_metadata"]
        assert meta["verification_ran"] is False
        assert meta["locations_gap_count"] == 0
        assert meta["props_gap_count"] == 0
        # Only 2 calls: locations chunk + props chunk (no verification)
        assert _mock_llm.call_count == 2

    def test_gap_triggers_verification_reprompt(self, _mock_llm):
        """When scene_index has locations not in discovered, re-prompt fires."""
        _mock_llm.side_effect = [
            # locations chunk — misses DOCK
            (MagicMock(items=["OFFICE"]), {"estimated_cost_usd": 0.01}),
            # props chunk
            (MagicMock(items=["COIN"]), {"estimated_cost_usd": 0.01}),
            # verification re-prompt for locations — adds DOCK
            (
                MagicMock(items=["OFFICE", "DOCK"]),
                {"estimated_cost_usd": 0.02},
            ),
        ]
        inputs = {
            "canonical_script": _SCRIPT,
            "breakdown_scenes": {
                "unique_characters": ["ABE"],
                "unique_locations": ["OFFICE", "DOCK"],
                "entries": [{"props_mentioned": ["COIN"]}],
            },
        }
        params = {"discovery_model": "mock"}
        result = run_module(inputs, params, {})

        data = result["artifacts"][0]["data"]
        assert "DOCK" in data["locations"]
        meta = data["processing_metadata"]
        assert meta["verification_ran"] is True
        assert meta["locations_gap_count"] == 1
        assert meta["verification_cost_usd"] == 0.02
        # 3 calls: locations + props + verification
        assert _mock_llm.call_count == 3

    def test_no_scene_index_skips_verification(self, _mock_llm):
        """Without scene_index, verification is skipped entirely."""
        _mock_llm.side_effect = [
            (MagicMock(items=["ABE"]), {"estimated_cost_usd": 0.01}),
            (MagicMock(items=["OFFICE"]), {"estimated_cost_usd": 0.01}),
            (MagicMock(items=["COIN"]), {"estimated_cost_usd": 0.01}),
        ]
        inputs = {"canonical_script": _SCRIPT}
        params = {"discovery_model": "mock"}
        result = run_module(inputs, params, {})

        meta = result["artifacts"][0]["data"]["processing_metadata"]
        assert meta["verification_ran"] is False
