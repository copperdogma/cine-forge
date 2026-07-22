"""Acceptance test: Entity discovery verification loop (Story 124).

Tests the recall verification loop by running entity discovery on The Mariner
with an independently source-annotated scene index, then checking both recall
and precision against the separately verified entity-discovery golden.

Requires: CINE_FORGE_GEMINI_API_KEY or GEMINI_API_KEY (uses
gemini-2.5-flash-lite, the production default).
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import pytest

from cine_forge.env import resolve_env

BENCHMARKS = Path(__file__).resolve().parents[2] / "benchmarks"
SCREENPLAY = BENCHMARKS / "input" / "the-mariner.md"
GOLDEN = BENCHMARKS / "golden" / "the-mariner-entity-discovery.json"
SCENE_TRUTH = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "golden"
    / "the_mariner_scene_entities.json"
)

pytestmark = [
    pytest.mark.acceptance,
    pytest.mark.skipif(
        os.getenv("CINE_FORGE_LIVE_TESTS") != "1" or not resolve_env("GEMINI_API_KEY"),
        reason=(
            "Set CINE_FORGE_LIVE_TESTS=1 and configure "
            "CINE_FORGE_GEMINI_API_KEY or GEMINI_API_KEY"
        ),
    ),
]


def _load_golden() -> dict:
    return json.loads(GOLDEN.read_text())


def _build_breakdown_scenes(scene_truth: dict) -> dict:
    """Build normal upstream-shaped signals without consulting the eval golden."""
    scenes = scene_truth["scenes"]
    characters = {
        name
        for scene in scenes
        for field in ("characters_in_action", "characters_in_dialogue")
        for name in scene[field]
    }
    return {
        "unique_characters": sorted(characters),
        "unique_locations": [scene["heading"] for scene in scenes],
        "entries": [{"props_mentioned": scene["props"]} for scene in scenes],
    }


def _normalize(value: str) -> str:
    return " ".join(re.findall(r"[A-Z0-9]+", value.upper()))


def _matches(found: str, target: str, aliases: list[str]) -> bool:
    normalized_found = _normalize(found)
    candidates = {_normalize(target), *(_normalize(alias) for alias in aliases)}
    candidates.discard("")
    return bool(normalized_found) and normalized_found in candidates


def _compute_recall(
    found: list[str], golden_section: dict
) -> tuple[float, list[str]]:
    """Compute recall against golden required entities with alias support."""
    required = golden_section["required"]
    aliases = golden_section.get("acceptable_aliases", {})
    missing = []

    for req in required:
        if not any(_matches(value, req, aliases.get(req, [])) for value in found):
            missing.append(req)

    recall = (len(required) - len(missing)) / len(required) if required else 1.0
    return recall, missing


def _compute_precision(found: list[str], golden_section: dict) -> tuple[float, list[str]]:
    """Measure whether outputs belong to independently verified required/optional truth."""
    aliases = golden_section.get("acceptable_aliases", {})
    expected = golden_section["required"] + golden_section.get("optional", [])
    unexpected = [
        value
        for value in found
        if not any(_matches(value, target, aliases.get(target, [])) for target in expected)
    ]
    precision = (len(found) - len(unexpected)) / len(found) if found else 0.0
    return precision, unexpected


def test_verification_improves_location_recall():
    """Run discovery from independent source annotations and gate precision/recall.

    The verification loop should catch any locations that chunked discovery
    misses by cross-referencing against scene_index.unique_locations.
    """
    from cine_forge.modules.world_building.entity_discovery_v1.main import (
        run_module,
    )

    golden = _load_golden()
    script_text = SCREENPLAY.read_text()
    breakdown_scenes = _build_breakdown_scenes(json.loads(SCENE_TRUTH.read_text()))

    inputs = {
        "canonical_script": {
            "script_text": script_text,
            "title": "The Mariner",
        },
        "breakdown_scenes": breakdown_scenes,
    }
    params = {
        "discovery_model": "gemini-2.5-flash-lite",
        "chunk_size": 12000,
    }

    result = run_module(inputs, params, {})
    data = result["artifacts"][0]["data"]
    meta = data["processing_metadata"]

    char_recall, char_missing = _compute_recall(
        data["characters"], golden["characters"]
    )
    loc_recall, loc_missing = _compute_recall(
        data["locations"], golden["locations"]
    )
    prop_recall, prop_missing = _compute_recall(
        data["props"], golden["props"]
    )
    char_precision, char_unexpected = _compute_precision(
        data["characters"], golden["characters"]
    )
    loc_precision, loc_unexpected = _compute_precision(
        data["locations"], golden["locations"]
    )
    prop_precision, prop_unexpected = _compute_precision(
        data["props"], golden["props"]
    )

    print(f"\n{'='*60}")
    print("Entity Discovery Verification Results (Story 124)")
    print(f"{'='*60}")
    print(
        f"Characters: {len(data['characters'])} "
        f"(recall: {char_recall:.0%}, precision: {char_precision:.0%}, "
        f"missing: {char_missing}, unexpected: {char_unexpected})"
    )
    print(f"Locations:  {len(data['locations'])} "
          f"(recall: {loc_recall:.0%}, precision: {loc_precision:.0%}, "
          f"missing: {loc_missing}, unexpected: {loc_unexpected})")
    print(f"Props:      {len(data['props'])} "
          f"(recall: {prop_recall:.0%}, precision: {prop_precision:.0%}, "
          f"missing: {prop_missing}, unexpected: {prop_unexpected})")
    print(f"Verification ran: {meta['verification_ran']}")
    print(f"Location gaps found: {meta['locations_gap_count']}")
    print(f"Prop gaps found: {meta['props_gap_count']}")
    print(f"Verification cost: ${meta['verification_cost_usd']:.4f}")
    print(f"Total cost: ${result['cost']['estimated_cost_usd']:.4f}")
    print(f"{'='*60}")

    assert char_recall == 1.0, (
        f"Character recall {char_recall:.0%}, missing: {char_missing}"
    )
    assert loc_recall == 1.0, (
        f"Location recall {loc_recall:.0%}, missing: {loc_missing}"
    )
    assert prop_recall == 1.0, (
        f"Prop recall {prop_recall:.0%}, missing: {prop_missing}"
    )
    assert char_precision >= 0.8, (
        f"Character precision {char_precision:.0%}, unexpected: {char_unexpected}"
    )
    assert loc_precision >= 0.8, (
        f"Location precision {loc_precision:.0%}, unexpected: {loc_unexpected}"
    )
    assert prop_precision >= 0.8, (
        f"Prop precision {prop_precision:.0%}, unexpected: {prop_unexpected}"
    )
    assert meta["character_source"] == "scene_index"
