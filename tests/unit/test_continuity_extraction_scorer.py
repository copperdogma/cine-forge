from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from tests.unit.continuity_scorer_test_support import (
    change as _change,
)
from tests.unit.continuity_scorer_test_support import (
    prop as _property,
)
from tests.unit.continuity_scorer_test_support import (
    scorer,
)
from tests.unit.continuity_scorer_test_support import (
    synthetic_context as _context,
)
from tests.unit.continuity_scorer_test_support import (
    synthetic_control as _control,
)
from tests.unit.continuity_scorer_test_support import (
    synthetic_golden as _golden,
)


@pytest.mark.unit
def test_continuity_scorer_rewards_grounded_control(tmp_path: Path) -> None:
    result = scorer.get_assert(json.dumps(_control()), _context(tmp_path))

    assert result["pass"] is True
    assert result["score"] == 1.0


@pytest.mark.unit
def test_continuity_scorer_rejects_wrong_scene_id(tmp_path: Path) -> None:
    output = _control()
    output["scene_id"] = "scene_999"
    result = scorer.get_assert(json.dumps(output), _context(tmp_path))

    assert result["pass"] is False
    assert "scene_identity=0.00" in result["reason"]


@pytest.mark.unit
def test_continuity_scorer_rejects_suffix_only_entity_match(tmp_path: Path) -> None:
    output = _control()
    output["entity_states"][0]["entity_key"] = "prop:alice"
    result = scorer.get_assert(json.dumps(output), _context(tmp_path))

    assert result["pass"] is False
    assert "entity_accuracy=" in result["reason"]


@pytest.mark.unit
def test_continuity_scorer_rejects_extra_entity_property_and_change(tmp_path: Path) -> None:
    output = _control()
    output["entity_states"].append(
        {
            "entity_key": "location:moon",
            "properties": [_property("weather", "snowing")],
            "change_events": [],
            "confidence": 0.9,
        }
    )
    output["entity_states"][0]["properties"].append(_property("hat", "gold crown"))
    output["entity_states"][0]["change_events"].append(
        _change("hat", "none", "gold crown", "Alice enters in a red coat, afraid.")
    )
    result = scorer.get_assert(json.dumps(output), _context(tmp_path))

    assert result["pass"] is False


@pytest.mark.unit
def test_continuity_scorer_rejects_wrong_change_values(tmp_path: Path) -> None:
    output = _control()
    output["entity_states"][0]["change_events"][0]["previous_value"] = "green dress"
    output["entity_states"][0]["change_events"][0]["new_value"] = "black armor"
    result = scorer.get_assert(json.dumps(output), _context(tmp_path))

    assert result["pass"] is False
    assert "change_accuracy=" in result["reason"]


@pytest.mark.unit
def test_continuity_scorer_rejects_fabricated_evidence(tmp_path: Path) -> None:
    output = _control()
    output["entity_states"][1]["change_events"][0]["evidence"] = (
        "The key becomes a dragon and flies to Mars."
    )
    result = scorer.get_assert(json.dumps(output), _context(tmp_path))

    assert result["pass"] is False
    assert "change_accuracy=" in result["reason"]


@pytest.mark.unit
def test_continuity_scorer_rejects_average_hiding_bad_confidence(tmp_path: Path) -> None:
    output = _control()
    output["entity_states"][0]["confidence"] = 0.4
    output["entity_states"][1]["confidence"] = 1.0
    result = scorer.get_assert(json.dumps(output), _context(tmp_path))

    assert result["pass"] is False
    assert "confidence_calibration=0.00" in result["reason"]


@pytest.mark.unit
def test_continuity_scorer_rejects_boolean_nested_confidence(tmp_path: Path) -> None:
    output = _control()
    output["entity_states"][0]["properties"][0]["confidence"] = True
    result = scorer.get_assert(json.dumps(output), _context(tmp_path))

    assert result == {"pass": False, "score": 0.0, "reason": "Invalid entity-state schema"}


@pytest.mark.unit
def test_continuity_scorer_dominated_mutation_scores_lower(tmp_path: Path) -> None:
    context = _context(tmp_path)
    complete = scorer.get_assert(json.dumps(_control()), context)
    output = deepcopy(_control())
    output["entity_states"][0]["properties"][1]["value"] = "cheerful"
    dominated = scorer.get_assert(json.dumps(output), context)

    assert dominated["score"] < complete["score"]
    assert dominated["pass"] is False


@pytest.mark.unit
def test_continuity_scorer_rejects_extra_top_level_field(tmp_path: Path) -> None:
    output = _control()
    output["analysis"] = "padded"

    result = scorer.get_assert(json.dumps(output), _context(tmp_path))

    assert result == {"pass": False, "score": 0.0, "reason": "Invalid result schema"}


@pytest.mark.unit
@pytest.mark.parametrize("level", ["entity", "property", "change"])
def test_continuity_scorer_rejects_extra_nested_fields(
    tmp_path: Path,
    level: str,
) -> None:
    output = _control()
    target = {
        "entity": output["entity_states"][0],
        "property": output["entity_states"][0]["properties"][0],
        "change": output["entity_states"][0]["change_events"][0],
    }[level]
    target["padding"] = "not in contract"

    result = scorer.get_assert(json.dumps(output), _context(tmp_path))

    assert result == {
        "pass": False,
        "score": 0.0,
        "reason": "Invalid entity-state schema",
    }


@pytest.mark.unit
def test_continuity_scorer_rejects_synonymous_property_keys(tmp_path: Path) -> None:
    output = _control()
    output["entity_states"][0]["properties"][0]["key"] = "wardrobe"
    output["entity_states"][0]["change_events"][0]["property_key"] = "wardrobe"

    result = scorer.get_assert(json.dumps(output), _context(tmp_path))

    assert result["pass"] is False
    assert "property_accuracy=" in result["reason"]


@pytest.mark.unit
def test_continuity_scorer_rejects_synonymous_change_key(tmp_path: Path) -> None:
    output = _control()
    output["entity_states"][0]["change_events"][0]["property_key"] = "wardrobe"

    result = scorer.get_assert(json.dumps(output), _context(tmp_path))

    assert result["pass"] is False
    assert "change_accuracy=" in result["reason"]


@pytest.mark.unit
def test_continuity_scorer_rejects_duplicate_change_events(tmp_path: Path) -> None:
    output = _control()
    output["entity_states"][0]["change_events"].append(
        deepcopy(output["entity_states"][0]["change_events"][0])
    )

    result = scorer.get_assert(json.dumps(output), _context(tmp_path))

    assert result["pass"] is False
    assert "change_accuracy=" in result["reason"]


@pytest.mark.unit
def test_continuity_scorer_does_not_reuse_one_event_for_two_specs(tmp_path: Path) -> None:
    golden = _golden()
    second_spec = deepcopy(golden["lab"]["expected_changes"]["character:alice"][0])
    golden["lab"]["expected_changes"]["character:alice"].append(second_spec)
    output = _control()

    result = scorer.get_assert(json.dumps(output), _context(tmp_path, golden))

    assert result["pass"] is False
    assert "change_accuracy=0.75" in result["reason"]


@pytest.mark.unit
def test_continuity_scorer_requires_literal_null_for_absent_previous_state(
    tmp_path: Path,
) -> None:
    golden = _golden()
    golden["lab"]["expected_changes"]["prop:key"][0]["previous_patterns"] = []
    output = _control()
    change = output["entity_states"][1]["change_events"][0]
    change["previous_value"] = None
    change["reason"] = "new state now broken in two"
    control = scorer.get_assert(json.dumps(output), _context(tmp_path, golden))
    change["previous_value"] = "null"
    mutation = scorer.get_assert(json.dumps(output), _context(tmp_path, golden))

    assert control["pass"] is True
    assert mutation["pass"] is False


@pytest.mark.unit
@pytest.mark.parametrize("level", ["property", "change"])
def test_continuity_scorer_enforces_nested_confidence_range(
    tmp_path: Path,
    level: str,
) -> None:
    output = _control()
    nested = {
        "property": output["entity_states"][0]["properties"][0],
        "change": output["entity_states"][0]["change_events"][0],
    }[level]
    nested["confidence"] = 0.6

    result = scorer.get_assert(json.dumps(output), _context(tmp_path))

    assert result["pass"] is False
    assert "confidence_calibration=0.00" in result["reason"]


@pytest.mark.unit
def test_continuity_scorer_binds_real_evidence_to_its_change(tmp_path: Path) -> None:
    output = _control()
    alice_change = output["entity_states"][0]["change_events"][0]
    key_change = output["entity_states"][1]["change_events"][0]
    alice_change["evidence"], key_change["evidence"] = (
        key_change["evidence"],
        alice_change["evidence"],
    )

    result = scorer.get_assert(json.dumps(output), _context(tmp_path))

    assert result["pass"] is False
    assert "evidence_coverage=1.00" in result["reason"]
    assert "change_accuracy=0.00" in result["reason"]


@pytest.mark.unit
def test_continuity_scorer_rejects_near_quote_with_changed_subject(tmp_path: Path) -> None:
    output = _control()
    output["entity_states"][0]["change_events"][0]["evidence"] = (
        "Bob enters in a red coat, afraid."
    )

    result = scorer.get_assert(json.dumps(output), _context(tmp_path))

    assert result["pass"] is False
    assert "change_accuracy=" in result["reason"]


@pytest.mark.unit
def test_continuity_scorer_rejects_unbound_generic_reason(tmp_path: Path) -> None:
    output = _control()
    output["entity_states"][0]["change_events"][0]["reason"] = (
        "The observable state changed."
    )

    result = scorer.get_assert(json.dumps(output), _context(tmp_path))

    assert result["pass"] is False
    assert "change_accuracy=" in result["reason"]


@pytest.mark.unit
def test_continuity_scorer_rejects_reason_with_reversed_state_direction(
    tmp_path: Path,
) -> None:
    output = _control()
    output["entity_states"][0]["change_events"][0]["reason"] = (
        "changed from red coat to blue shirt"
    )

    result = scorer.get_assert(json.dumps(output), _context(tmp_path))

    assert result["pass"] is False
    assert "change_accuracy=" in result["reason"]


@pytest.mark.unit
def test_continuity_scorer_enforces_expected_explicitness(tmp_path: Path) -> None:
    output = _control()
    output["entity_states"][0]["change_events"][0]["is_explicit"] = False

    result = scorer.get_assert(json.dumps(output), _context(tmp_path))

    assert result["pass"] is False
    assert "change_accuracy=" in result["reason"]


@pytest.mark.unit
def test_continuity_scorer_rejects_negated_expected_property(tmp_path: Path) -> None:
    output = _control()
    output["entity_states"][0]["properties"][0]["value"] = "not wearing a red coat"

    result = scorer.get_assert(json.dumps(output), _context(tmp_path))

    assert result["pass"] is False
    assert "property_accuracy=" in result["reason"]
