from __future__ import annotations

import json
from copy import deepcopy

import pytest
import yaml

from tests.unit.continuity_scorer_test_support import (
    ROOT,
    change,
    day_control,
    maintained_context,
    night_control,
    prop,
    scorer,
)


def _score(output: dict, scene_key: str = "dock_night") -> dict:
    return scorer.get_assert(json.dumps(output), maintained_context(scene_key))


def _property(output: dict, entity_key: str, property_key: str) -> dict:
    entity = next(
        state for state in output["entity_states"] if state["entity_key"] == entity_key
    )
    return next(item for item in entity["properties"] if item["key"] == property_key)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("scene_key", "factory"),
    [("dock_day", day_control), ("dock_night", night_control)],
)
def test_maintained_faithful_outputs_score_one(scene_key: str, factory) -> None:
    result = _score(factory(), scene_key)

    assert result["pass"] is True
    assert result["score"] == 1.0


@pytest.mark.unit
@pytest.mark.parametrize(
    ("entity_key", "property_key", "contradictory_value"),
    [
        (
            "character:billy",
            "costume",
            "leather jacket torn at the left sleeve, gold fabric",
        ),
        (
            "character:billy",
            "physical_condition",
            "soaked through; dried blood and fresh blood visible on his knuckles",
        ),
        (
            "character:billy",
            "physical_condition",
            "soaked through but dry; dried blood visible on his knuckles",
        ),
        ("character:billy", "emotional_state", "hollow but cheerful"),
        ("location:harbor_dock", "weather", "rain plus snow"),
        ("location:harbor_dock", "lighting", "blazing daylight at night"),
        (
            "prop:oar",
            "condition",
            "broken in two pieces, repaired on the moon and owned by Jane",
        ),
        ("prop:envelope", "condition", "open but sealed; contents scattered in puddles"),
    ],
)
def test_contradictory_or_unsupported_qualifier_fails(
    entity_key: str,
    property_key: str,
    contradictory_value: str,
) -> None:
    output = night_control()
    _property(output, entity_key, property_key)["value"] = contradictory_value

    result = _score(output)

    assert result["pass"] is False
    assert "property_accuracy=" in result["reason"]
    assert result["score"] < 1.0


@pytest.mark.unit
def test_all_verifier_contradictions_cannot_repeat_the_previous_perfect_score() -> None:
    output = night_control()
    replacements = {
        ("character:billy", "costume"): "leather jacket torn at the left sleeve, gold fabric",
        (
            "character:billy",
            "physical_condition",
        ): "soaked through but dry; dried blood and fresh blood visible on his knuckles",
        ("character:billy", "emotional_state"): "hollow but cheerful",
        ("location:harbor_dock", "weather"): "rain plus snow",
        ("location:harbor_dock", "lighting"): "blazing daylight at night",
        (
            "prop:oar",
            "condition",
        ): "broken in two pieces, repaired on the moon and owned by Jane",
        (
            "prop:envelope",
            "condition",
        ): "open but sealed; contents scattered in puddles",
    }
    for (entity_key, property_key), value in replacements.items():
        _property(output, entity_key, property_key)["value"] = value

    result = _score(output)

    assert result["pass"] is False
    assert result["score"] < 1.0


@pytest.mark.unit
def test_partial_property_value_is_not_accepted() -> None:
    output = night_control()
    _property(output, "character:billy", "physical_condition")["value"] = (
        "dried blood visible on his knuckles"
    )

    result = _score(output)

    assert result["pass"] is False
    assert "property_accuracy=" in result["reason"]


@pytest.mark.unit
@pytest.mark.parametrize("extra_kind", ["entity", "property", "change"])
def test_each_unsupported_extra_fails_independently(extra_kind: str) -> None:
    output = night_control()
    if extra_kind == "entity":
        output["entity_states"].append(
            {
                "entity_key": "location:moon",
                "properties": [prop("weather", "snow")],
                "change_events": [],
                "confidence": 0.9,
            }
        )
    elif extra_kind == "property":
        output["entity_states"][0]["properties"].append(prop("hat", "gold crown"))
    else:
        output["entity_states"][0]["change_events"].append(
            change("costume", "gold fabric", "silver fabric", "Rain hammers the dock.")
        )

    assert _score(output)["pass"] is False


@pytest.mark.unit
@pytest.mark.parametrize(
    ("field", "value"),
    [("previous_value", "flat and resigned"), ("new_value", "hollow and cheerful")],
)
def test_change_values_require_exact_normalized_truth(field: str, value: str) -> None:
    output = night_control()
    event = output["entity_states"][0]["change_events"][3]
    event[field] = value
    event["reason"] = f"changed from {event['previous_value']} to {event['new_value']}"

    result = _score(output)

    assert result["pass"] is False
    assert "change_accuracy=" in result["reason"]


@pytest.mark.unit
def test_task_contains_only_source_supported_prior_state() -> None:
    task = yaml.safe_load(
        (ROOT / "benchmarks" / "tasks" / "continuity-extraction.yaml").read_text()
    )
    day_prior = task["tests"][0]["vars"]["entities_block"].lower()
    night_prior = task["tests"][1]["vars"]["entities_block"].lower()

    for invented in ("flannel", "jeans", "tense", "jaw tight"):
        assert invented not in day_prior
    assert "no verified prior state" in day_prior
    assert "compare for change events: none (no verified prior state)" in day_prior
    assert "emotional_state: flat" in night_prior
    assert "resigned" not in night_prior
    assert "weather: wind" in night_prior


@pytest.mark.unit
def test_subject_prompt_forbids_partial_and_contradictory_value_padding() -> None:
    prompt = (
        ROOT / "benchmarks" / "prompts" / "continuity-extraction.txt"
    ).read_text().lower()

    assert "no unsupported, contradictory, alternative, or cross-property qualifier" in prompt
    assert "no verified prior state" in prompt
    assert "reject partial values" in prompt


@pytest.mark.unit
def test_mutating_a_control_does_not_mutate_the_fixture_factory() -> None:
    first = night_control()
    second = deepcopy(first)
    _property(second, "location:harbor_dock", "weather")["value"] = "snow"

    assert _score(first)["score"] == 1.0
    assert _score(second)["pass"] is False
