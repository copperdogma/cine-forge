"""Focused throughput/compaction tests for continuity_tracking_v1."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest

from cine_forge.modules.world_building.continuity_tracking_v1.main import (
    EntityStateExtraction,
    SceneContinuityExtraction,
    _build_continuity_prompt,
    _merge_state_properties,
    run_module,
)
from cine_forge.schemas import ContinuityEvent, StateProperty


@pytest.fixture
def multi_scene_inputs() -> dict[str, Any]:
    return {
        "normalize": {
            "script_text": (
                "INT. DOCK - DAY\n"
                "\n"
                "BILLY stands at the edge, gripping a weathered OAR.\n"
                "He wears a torn blue jacket and oil-stained jeans.\n"
                "\n"
                "INT. DOCK - NIGHT\n"
                "\n"
                "BILLY sits on a crate, blood on his lip from the fight.\n"
                "The OAR leans against the wall, cracked.\n"
            ),
        },
        "breakdown_scenes": {
            "entries": [
                {
                    "scene_id": "scene_001",
                    "scene_number": 1,
                    "heading": "INT. DOCK - DAY",
                    "location": "DOCK",
                    "characters_present": ["BILLY"],
                    "props_mentioned": ["OAR"],
                    "source_span": {"start_line": 1, "end_line": 5},
                },
                {
                    "scene_id": "scene_002",
                    "scene_number": 2,
                    "heading": "INT. DOCK - NIGHT",
                    "location": "DOCK",
                    "characters_present": ["BILLY"],
                    "props_mentioned": ["OAR"],
                    "source_span": {"start_line": 6, "end_line": 9},
                },
            ],
            "unique_locations": ["DOCK"],
        },
        "character_bible": [{"character_id": "billy", "name": "BILLY"}],
        "location_bible": [{"location_id": "dock", "name": "DOCK"}],
        "prop_bible": [{"prop_id": "oar", "name": "OAR"}],
    }


def _scene_001_response() -> SceneContinuityExtraction:
    return SceneContinuityExtraction(
        scene_id="scene_001",
        entity_states=[
            EntityStateExtraction(
                entity_key="character:billy",
                properties=[
                    StateProperty(
                        key="costume",
                        value="torn blue jacket, oil-stained jeans",
                        confidence=0.95,
                    ),
                    StateProperty(
                        key="physical_condition",
                        value="healthy",
                        confidence=0.9,
                    ),
                ],
                change_events=[],
                confidence=0.85,
            ),
            EntityStateExtraction(
                entity_key="location:dock",
                properties=[
                    StateProperty(key="time_of_day", value="day", confidence=1.0),
                ],
                change_events=[],
                confidence=0.9,
            ),
            EntityStateExtraction(
                entity_key="prop:oar",
                properties=[
                    StateProperty(
                        key="condition",
                        value="weathered but intact",
                        confidence=0.9,
                    ),
                    StateProperty(
                        key="position",
                        value="in Billy's hands",
                        confidence=0.95,
                    ),
                ],
                change_events=[],
                confidence=0.9,
            ),
        ],
    )


def _scene_002_sparse_response() -> SceneContinuityExtraction:
    return SceneContinuityExtraction(
        scene_id="scene_002",
        entity_states=[
            EntityStateExtraction(
                entity_key="character:billy",
                properties=[
                    StateProperty(
                        key="physical_condition",
                        value="blood on lip from fight",
                        confidence=0.95,
                    ),
                ],
                change_events=[
                    ContinuityEvent(
                        property_key="physical_condition",
                        previous_value="healthy",
                        new_value="blood on lip from fight",
                        reason="Injured in fight",
                        evidence="blood on his lip from the fight",
                        is_explicit=True,
                        confidence=0.95,
                    )
                ],
                confidence=0.9,
            ),
            EntityStateExtraction(
                entity_key="location:dock",
                properties=[
                    StateProperty(key="time_of_day", value="night", confidence=1.0),
                ],
                change_events=[
                    ContinuityEvent(
                        property_key="time_of_day",
                        previous_value="day",
                        new_value="night",
                        reason="Time has passed",
                        evidence="INT. DOCK - NIGHT",
                        is_explicit=True,
                        confidence=1.0,
                    )
                ],
                confidence=0.9,
            ),
            EntityStateExtraction(
                entity_key="prop:oar",
                properties=[
                    StateProperty(key="condition", value="cracked", confidence=0.95),
                ],
                change_events=[
                    ContinuityEvent(
                        property_key="condition",
                        previous_value="weathered but intact",
                        new_value="cracked",
                        reason="Damaged in fight",
                        evidence="The OAR leans against the wall, cracked.",
                        is_explicit=True,
                        confidence=0.9,
                    )
                ],
                confidence=0.9,
            ),
        ],
    )


@pytest.mark.unit
def test_sparse_scene_response_carries_forward_previous_state(
    multi_scene_inputs: dict[str, Any],
) -> None:
    call_count = 0

    def fake_call_llm(**kwargs: Any) -> tuple[Any, dict[str, Any]]:
        nonlocal call_count
        call_count += 1
        metadata = {
            "model": "claude-haiku-4-5-20251001",
            "input_tokens": 200,
            "output_tokens": 120,
            "estimated_cost_usd": 0.002,
        }
        if call_count == 1:
            return _scene_001_response(), metadata
        return _scene_002_sparse_response(), metadata

    with patch(
        "cine_forge.modules.world_building.continuity_tracking_v1.main.call_llm",
        side_effect=fake_call_llm,
    ):
        result = run_module(
            inputs=multi_scene_inputs,
            params={"work_model": "claude-haiku-4-5-20251001"},
            context={},
        )

    states = [
        artifact
        for artifact in result["artifacts"]
        if artifact["artifact_type"] == "continuity_state"
    ]
    billy_scene_2 = next(
        artifact for artifact in states if artifact["entity_id"] == "character_billy_scene_002"
    )
    properties = {prop["key"]: prop["value"] for prop in billy_scene_2["data"]["properties"]}
    assert properties["physical_condition"] == "blood on lip from fight"
    assert properties["costume"] == "torn blue jacket, oil-stained jeans"

    oar_scene_2 = next(
        artifact for artifact in states if artifact["entity_id"] == "prop_oar_scene_002"
    )
    prop_state = {prop["key"]: prop["value"] for prop in oar_scene_2["data"]["properties"]}
    assert prop_state["condition"] == "cracked"
    assert prop_state["position"] == "in Billy's hands"

    continuity_index = next(
        artifact
        for artifact in result["artifacts"]
        if artifact["artifact_type"] == "continuity_index"
    )
    throughput = continuity_index["metadata"]["throughput"]
    assert throughput["scene_calls"] == 2
    assert throughput["observed_properties"] == 8
    assert throughput["carried_forward_properties"] >= 2
    assert throughput["change_event_count"] == 3


@pytest.mark.unit
def test_prompt_contract_requests_sparse_properties_and_clips_previous_state() -> None:
    previous_state = {
        "costume": StateProperty(
            key="costume",
            value=(
                "heavy wool peacoat with salt-caked shoulders, torn cuffs, brass toggles, "
                "and a frayed red lining hanging loose at the hem"
            ),
            confidence=0.9,
        ),
    }
    prompt = _build_continuity_prompt(
        scene_entry={
            "scene_id": "scene_002",
            "scene_number": 2,
            "heading": "INT. DOCK - NIGHT",
        },
        scene_text="BILLY sits on a crate, blood on his lip from the fight.",
        present_entities=["character:billy"],
        entities={"character:billy": {"type": "character", "data": {"name": "BILLY"}}},
        current_states={"character:billy": previous_state},
    )

    assert "Do not repeat unchanged carried-forward state" in prompt
    assert "new_value`: what it is now, or null if the property no longer applies" in prompt
    assert "heavy wool peacoat with salt-caked shoulders" in prompt
    assert "frayed red lining hanging loose at the hem" not in prompt
    assert "…" in prompt


@pytest.mark.unit
def test_merge_state_properties_removes_cleared_values() -> None:
    previous_state = {
        "props_carried": StateProperty(
            key="props_carried",
            value="sealed envelope",
            confidence=0.9,
        ),
        "physical_condition": StateProperty(
            key="physical_condition",
            value="healthy",
            confidence=0.9,
        ),
    }
    merged, carried_forward = _merge_state_properties(
        previous_state=previous_state,
        extracted_properties=[
            StateProperty(
                key="physical_condition",
                value="blood on lip from fight",
                confidence=0.95,
            )
        ],
        change_events=[
            ContinuityEvent(
                property_key="props_carried",
                previous_value="sealed envelope",
                new_value=None,
                reason="Dropped envelope",
                evidence="The ENVELOPE is open, contents scattered in puddles.",
                is_explicit=True,
                confidence=0.9,
            )
        ],
    )

    merged_map = {prop.key: prop.value for prop in merged}
    assert merged_map == {"physical_condition": "blood on lip from fight"}
    assert carried_forward == 0
