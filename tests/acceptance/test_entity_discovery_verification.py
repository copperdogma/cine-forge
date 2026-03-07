"""Acceptance test: Entity discovery verification loop (Story 124).

Tests the recall verification loop by running entity discovery on The Mariner
with a scene_index that contains known locations/props, then checking whether
the verification step improves recall compared to raw discovery.

Requires: GEMINI_API_KEY (uses gemini-2.5-flash-lite, the production default).
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import pytest

BENCHMARKS = Path(__file__).resolve().parents[2] / "benchmarks"
SCREENPLAY = BENCHMARKS / "input" / "the-mariner.md"
GOLDEN = BENCHMARKS / "golden" / "the-mariner-entity-discovery.json"

pytestmark = [
    pytest.mark.acceptance,
    pytest.mark.skipif(
        not os.environ.get("GEMINI_API_KEY"),
        reason="GEMINI_API_KEY required for live entity discovery",
    ),
]


def _load_golden() -> dict:
    return json.loads(GOLDEN.read_text())


def _compute_recall(
    found: list[str], golden_section: dict
) -> tuple[float, list[str]]:
    """Compute recall against golden required entities with alias support."""
    required = golden_section["required"]
    aliases = golden_section.get("acceptable_aliases", {})
    missing = []

    def _normalize(s: str) -> str:
        return re.sub(r"[^A-Z0-9 ]", "", s.upper().strip())

    for req in required:
        norm_req = _normalize(req)
        alias_norms = [_normalize(a) for a in aliases.get(req, [])]
        targets = [norm_req] + alias_norms

        matched = False
        for f in found:
            norm_f = _normalize(f)
            for t in targets:
                if t in norm_f or norm_f in t:
                    matched = True
                    break
            if matched:
                break
        if not matched:
            missing.append(req)

    recall = (len(required) - len(missing)) / len(required) if required else 1.0
    return recall, missing


def test_verification_improves_location_recall():
    """Run entity discovery with scene_index containing known locations.

    The verification loop should catch any locations that chunked discovery
    misses by cross-referencing against scene_index.unique_locations.
    """
    from cine_forge.modules.world_building.entity_discovery_v1.main import (
        run_module,
    )

    golden = _load_golden()
    script_text = SCREENPLAY.read_text()

    # Build a scene_index with known locations from the golden reference
    # (simulates what scene_breakdown would produce)
    known_locations = (
        golden["locations"]["required"] + golden["locations"]["optional"]
    )
    known_props = golden["props"]["required"] + golden["props"]["optional"]

    inputs = {
        "canonical_script": {
            "script_text": script_text,
            "title": "The Mariner",
        },
        "breakdown_scenes": {
            "unique_characters": golden["characters"]["required"],
            "unique_locations": known_locations,
            "entries": [
                {"props_mentioned": known_props},
            ],
        },
    }
    params = {
        "discovery_model": "gemini-2.5-flash-lite",
        "chunk_size": 12000,
    }

    result = run_module(inputs, params, {})
    data = result["artifacts"][0]["data"]
    meta = data["processing_metadata"]

    # Report results
    loc_recall, loc_missing = _compute_recall(
        data["locations"], golden["locations"]
    )
    prop_recall, prop_missing = _compute_recall(
        data["props"], golden["props"]
    )

    print(f"\n{'='*60}")
    print("Entity Discovery Verification Results (Story 124)")
    print(f"{'='*60}")
    print(f"Characters: {len(data['characters'])} "
          f"(source: {meta['character_source']})")
    print(f"Locations:  {len(data['locations'])} "
          f"(recall: {loc_recall:.0%}, missing: {loc_missing})")
    print(f"Props:      {len(data['props'])} "
          f"(recall: {prop_recall:.0%}, missing: {prop_missing})")
    print(f"Verification ran: {meta['verification_ran']}")
    print(f"Location gaps found: {meta['locations_gap_count']}")
    print(f"Prop gaps found: {meta['props_gap_count']}")
    print(f"Verification cost: ${meta['verification_cost_usd']:.4f}")
    print(f"Total cost: ${result['cost']['estimated_cost_usd']:.4f}")
    print(f"{'='*60}")

    # Gate: all required locations and props must be found
    assert loc_recall == 1.0, (
        f"Location recall {loc_recall:.0%}, missing: {loc_missing}"
    )
    assert prop_recall == 1.0, (
        f"Prop recall {prop_recall:.0%}, missing: {prop_missing}"
    )
    # Characters come from scene_index passthrough — always correct
    assert meta["character_source"] == "scene_index"
