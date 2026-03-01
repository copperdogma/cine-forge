"""Integration test for continuity AI detection (Story 092).

Uses a real LLM model to verify the continuity extraction produces
semantically meaningful output. Marked with `integration` so it doesn't
run in CI — invoke with:

    .venv/bin/python -m pytest tests/integration/test_continuity_ai_integration.py -v
"""

from __future__ import annotations

import os
from typing import Any

import pytest

from cine_forge.modules.world_building.continuity_tracking_v1.main import (
    run_module,
)

# Short script excerpt — 3 scenes with deliberate continuity changes
SCRIPT_TEXT = """\
INT. BILLY'S APARTMENT - MORNING

BILLY (50s, weathered face) sits at his kitchen table in a faded
flannel shirt and worn jeans. He holds a chipped coffee mug. A
PHOTOGRAPH of a younger woman sits propped against the salt shaker.

He stares at the photo, jaw tight. Then he stands, grabs his
old leather jacket from the hook by the door, and heads out.

EXT. HARBOR DOCK - DAY

BILLY walks along the dock, leather jacket zipped against the wind.
The OAR — his father's, weathered oak with a rope-wrapped grip —
rests in his right hand like a walking stick.

He spots JANE (30s, sharp eyes, rain jacket) waiting by the boat.
She holds a sealed ENVELOPE.

JANE
You're late.

BILLY
(flat)
I'm always late.

He sets the OAR against a piling and reaches for the envelope.

EXT. HARBOR DOCK - NIGHT

Rain hammers the dock. BILLY sits on a coiled rope, soaked through.
His leather jacket is torn at the left sleeve — dried blood visible
on his knuckles. The OAR lies broken in two pieces at his feet.

JANE is gone. The ENVELOPE is open, contents scattered in puddles.

BILLY stares at the dark water, expression hollow.
"""

SCENE_ENTRIES = [
    {
        "scene_id": "scene_001",
        "scene_number": 1,
        "heading": "INT. BILLY'S APARTMENT - MORNING",
        "location": "BILLY'S APARTMENT",
        "characters_present": ["BILLY"],
        "props_mentioned": ["PHOTOGRAPH", "COFFEE MUG"],
        "source_span": {"start_line": 1, "end_line": 9},
    },
    {
        "scene_id": "scene_002",
        "scene_number": 2,
        "heading": "EXT. HARBOR DOCK - DAY",
        "location": "HARBOR DOCK",
        "characters_present": ["BILLY", "JANE"],
        "props_mentioned": ["OAR", "ENVELOPE"],
        "source_span": {"start_line": 10, "end_line": 24},
    },
    {
        "scene_id": "scene_003",
        "scene_number": 3,
        "heading": "EXT. HARBOR DOCK - NIGHT",
        "location": "HARBOR DOCK",
        "characters_present": ["BILLY"],
        "props_mentioned": ["OAR", "ENVELOPE"],
        "source_span": {"start_line": 25, "end_line": 33},
    },
]


def _build_inputs() -> dict[str, Any]:
    return {
        "normalize": {"script_text": SCRIPT_TEXT},
        "breakdown_scenes": {
            "entries": SCENE_ENTRIES,
            "unique_locations": ["BILLY'S APARTMENT", "HARBOR DOCK"],
        },
        "character_bible": [
            {"character_id": "billy", "name": "BILLY"},
            {"character_id": "jane", "name": "JANE"},
        ],
        "location_bible": [
            {"location_id": "billy_s_apartment", "name": "BILLY'S APARTMENT"},
            {"location_id": "harbor_dock", "name": "HARBOR DOCK"},
        ],
        "prop_bible": [
            {"prop_id": "oar", "name": "OAR"},
            {"prop_id": "envelope", "name": "ENVELOPE"},
        ],
    }


@pytest.mark.integration
def test_continuity_ai_produces_meaningful_output() -> None:
    """Run continuity extraction with a real model and verify output quality."""
    # Skip if no API key is available
    if not os.environ.get("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set")

    inputs = _build_inputs()
    result = run_module(
        inputs=inputs,
        params={"work_model": "claude-haiku-4-5-20251001"},
        context={},
    )

    artifacts = result["artifacts"]
    states = [a for a in artifacts if a["artifact_type"] == "continuity_state"]
    index_list = [
        a for a in artifacts if a["artifact_type"] == "continuity_index"
    ]

    # Basic structural checks
    assert len(states) > 0, "Expected at least some continuity states"
    assert len(index_list) == 1, "Expected exactly one continuity index"

    # At least some states should have non-empty properties
    states_with_props = [
        s for s in states if len(s["data"]["properties"]) > 0
    ]
    assert len(states_with_props) >= 3, (
        f"Expected at least 3 states with properties, got {len(states_with_props)}"
    )

    # Scene 3 should detect changes (Billy's jacket torn, OAR broken)
    billy_s3 = [
        s for s in states
        if s["entity_id"] == "character_billy_scene_003"
    ]
    if billy_s3:
        events = billy_s3[0]["data"]["change_events"]
        # The model should detect at least one change (injury, jacket damage)
        # Being lenient — different models may detect different changes
        assert len(events) >= 1 or len(billy_s3[0]["data"]["properties"]) >= 2, (
            "Billy in scene 3 should have change events or rich properties"
        )

    # Cost should be non-zero
    cost = result["cost"]
    assert cost["estimated_cost_usd"] > 0, "Expected non-zero cost"
    assert cost["input_tokens"] > 0, "Expected non-zero input tokens"

    # Index should have real computed scores
    index_data = index_list[0]["data"]
    assert index_data["overall_continuity_score"] > 0, (
        "Expected non-zero continuity score"
    )
    # Score should not be the old hardcoded 0.9
    assert index_data["overall_continuity_score"] != 0.9 or len(states) < 3

    print(f"\n[integration] Produced {len(states)} state artifacts")
    print(f"[integration] {len(states_with_props)} with properties")
    print(f"[integration] Cost: ${cost['estimated_cost_usd']:.4f}")
    print(
        f"[integration] Continuity score: "
        f"{index_data['overall_continuity_score']:.3f}"
    )
    print(f"[integration] Total gaps: {index_data['total_gaps']}")
