"""Guardrail tests for long-form continuity stall recovery."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest

from cine_forge.modules.world_building.continuity_tracking_v1.main import run_module
from cine_forge.modules.world_building.continuity_tracking_v1.prompting import (
    SCENE_CONTINUITY_MAX_ATTEMPTS,
    SCENE_CONTINUITY_REQUEST_TIMEOUT_SECONDS,
    EntityStateExtraction,
    SceneContinuityExtraction,
    _extract_scene_continuity,
)
from cine_forge.schemas import StateProperty


@pytest.fixture
def single_scene_inputs() -> dict[str, Any]:
    return {
        "normalize": {
            "script_text": (
                "INT. DOCK - DAY\n"
                "\n"
                "BILLY stands at the edge of the dock.\n"
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
                    "props_mentioned": [],
                    "source_span": {"start_line": 1, "end_line": 3},
                }
            ],
            "unique_locations": ["DOCK"],
        },
        "character_bible": [{"character_id": "billy", "name": "BILLY"}],
        "location_bible": [{"location_id": "dock", "name": "DOCK"}],
        "prop_bible": [],
    }


@pytest.fixture
def two_scene_inputs() -> dict[str, Any]:
    return {
        "normalize": {
            "script_text": (
                "INT. DOCK - DAY\n"
                "\n"
                "BILLY grips the oar in a torn blue jacket.\n"
                "\n"
                "INT. DOCK - NIGHT\n"
                "\n"
                "BILLY returns to the same dock.\n"
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
                    "props_mentioned": [],
                    "source_span": {"start_line": 1, "end_line": 3},
                },
                {
                    "scene_id": "scene_002",
                    "scene_number": 2,
                    "heading": "INT. DOCK - NIGHT",
                    "location": "DOCK",
                    "characters_present": ["BILLY"],
                    "props_mentioned": [],
                    "source_span": {"start_line": 5, "end_line": 7},
                },
            ],
            "unique_locations": ["DOCK"],
        },
        "character_bible": [{"character_id": "billy", "name": "BILLY"}],
        "location_bible": [{"location_id": "dock", "name": "DOCK"}],
        "prop_bible": [],
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
                        value="torn blue jacket",
                        confidence=0.95,
                    )
                ],
                change_events=[],
                confidence=0.9,
            ),
            EntityStateExtraction(
                entity_key="location:dock",
                properties=[
                    StateProperty(
                        key="time_of_day",
                        value="day",
                        confidence=1.0,
                    )
                ],
                change_events=[],
                confidence=0.95,
            ),
        ],
    )


@pytest.mark.unit
def test_extract_scene_continuity_uses_bounded_scene_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(
        "cine_forge.modules.world_building.continuity_tracking_v1.prompting.time.sleep",
        lambda _seconds: None,
    )

    def failing_llm(**kwargs: Any) -> tuple[Any, dict[str, Any]]:
        calls.append(kwargs)
        raise RuntimeError("request timed out")

    extraction, metadata = _extract_scene_continuity(
        scene_entry={
            "scene_id": "scene_001",
            "scene_number": 1,
            "heading": "INT. DOCK - DAY",
        },
        scene_text="BILLY stands at the edge of the dock.",
        present_entities=["character:billy"],
        entities={"character:billy": {"type": "character", "data": {"name": "BILLY"}}},
        current_states={},
        model="claude-haiku-4-5-20251001",
        llm_callable=failing_llm,
    )

    assert extraction.scene_id == "scene_001"
    assert extraction.entity_states == []
    assert len(calls) == SCENE_CONTINUITY_MAX_ATTEMPTS
    assert all(call["max_retries"] == 0 for call in calls)
    assert all(
        call["request_timeout_seconds"] == SCENE_CONTINUITY_REQUEST_TIMEOUT_SECONDS
        for call in calls
    )
    assert metadata["scene_result_status"] == "failed"
    assert metadata["scene_result_reason"] == "timeout"
    assert metadata["attempt_count"] == SCENE_CONTINUITY_MAX_ATTEMPTS
    assert metadata["retry_count"] == SCENE_CONTINUITY_MAX_ATTEMPTS - 1


@pytest.mark.unit
def test_run_module_announces_continuity_states_incrementally(
    single_scene_inputs: dict[str, Any],
) -> None:
    announced: list[dict[str, Any]] = []

    def fake_call_llm(**kwargs: Any) -> tuple[Any, dict[str, Any]]:
        return _scene_001_response(), {
            "model": "claude-haiku-4-5-20251001",
            "input_tokens": 120,
            "output_tokens": 80,
            "estimated_cost_usd": 0.001,
        }

    with patch(
        "cine_forge.modules.world_building.continuity_tracking_v1.main.call_llm",
        side_effect=fake_call_llm,
    ):
        result = run_module(
            inputs=single_scene_inputs,
            params={"work_model": "claude-haiku-4-5-20251001"},
            context={"announce_artifact": lambda artifact: announced.append(artifact)},
        )

    states = [
        artifact
        for artifact in result["artifacts"]
        if artifact["artifact_type"] == "continuity_state"
    ]
    index = next(
        artifact
        for artifact in result["artifacts"]
        if artifact["artifact_type"] == "continuity_index"
    )

    assert len(announced) == len(states)
    assert len(states) == 2
    assert all(artifact["artifact_type"] == "continuity_state" for artifact in announced)
    assert index["metadata"]["throughput"]["announced_states"] == len(states)
    assert index["metadata"]["throughput"]["scene_successes"] == 1


@pytest.mark.unit
def test_timeout_fallback_is_explicit_and_carries_forward_state(
    monkeypatch: pytest.MonkeyPatch,
    two_scene_inputs: dict[str, Any],
) -> None:
    monkeypatch.setattr(
        "cine_forge.modules.world_building.continuity_tracking_v1.prompting.time.sleep",
        lambda _seconds: None,
    )
    call_count = 0

    def fake_call_llm(**kwargs: Any) -> tuple[Any, dict[str, Any]]:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return _scene_001_response(), {
                "model": "claude-haiku-4-5-20251001",
                "input_tokens": 120,
                "output_tokens": 80,
                "estimated_cost_usd": 0.001,
            }
        raise RuntimeError("request timed out")

    with patch(
        "cine_forge.modules.world_building.continuity_tracking_v1.main.call_llm",
        side_effect=fake_call_llm,
    ):
        result = run_module(
            inputs=two_scene_inputs,
            params={"work_model": "claude-haiku-4-5-20251001"},
            context={},
        )

    billy_scene_2 = next(
        artifact
        for artifact in result["artifacts"]
        if artifact["entity_id"] == "character_billy_scene_002"
    )
    props = {prop["key"]: prop["value"] for prop in billy_scene_2["data"]["properties"]}
    throughput = next(
        artifact["metadata"]["throughput"]
        for artifact in result["artifacts"]
        if artifact["artifact_type"] == "continuity_index"
    )

    assert props["costume"] == "torn blue jacket"
    assert billy_scene_2["metadata"]["health"] == "needs_review"
    assert billy_scene_2["metadata"]["annotations"]["scene_result_reason"] == "timeout"
    assert (
        billy_scene_2["metadata"]["annotations"]["scene_result_attempt_count"]
        == SCENE_CONTINUITY_MAX_ATTEMPTS
    )
    assert throughput["scene_calls"] == 2
    assert throughput["scene_successes"] == 1
    assert throughput["scene_failures"] == 1
    assert throughput["timeout_failures"] == 1
    assert throughput["scene_retry_attempts"] == 1
