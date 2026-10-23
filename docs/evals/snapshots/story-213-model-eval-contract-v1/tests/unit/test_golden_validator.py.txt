from __future__ import annotations

import importlib.util
import json
import re
import sys
from copy import deepcopy
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
GOLDEN_ROOT = REPO_ROOT / "benchmarks" / "golden"
if str(GOLDEN_ROOT) not in sys.path:
    sys.path.insert(0, str(GOLDEN_ROOT))

spec = importlib.util.spec_from_file_location(
    "cine_forge_golden_validator",
    GOLDEN_ROOT / "validate-golden.py",
)
assert spec and spec.loader
validator = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = validator
spec.loader.exec_module(validator)

EXPECTED_FIXTURES = {
    "the-mariner-characters.json",
    "the-mariner-scenes.json",
    "the-mariner-locations.json",
    "the-mariner-props.json",
    "the-mariner-relationships.json",
    "the-mariner-entity-discovery.json",
    "the-mariner-script-bible.json",
    "the_mariner_scene_entities.json",
    "the-mariner-config.json",
    "normalize-signal-golden.json",
    "enrich-scenes-golden.json",
    "qa-pass-golden.json",
    "continuity-extraction-golden.json",
    "open-frequency-maya-character.json",
    "open-frequency-scenes.json",
    "open-frequency-entity-discovery.json",
    "open-frequency-config.json",
    "open-frequency-script-bible.json",
    "normalize-open-frequency-corrupted-golden.json",
}


@pytest.mark.unit
def test_validator_covers_every_semantic_golden() -> None:
    assert set(validator.GOLDEN_SPECS) == EXPECTED_FIXTURES


@pytest.mark.unit
@pytest.mark.parametrize("filename", sorted(EXPECTED_FIXTURES))
def test_each_semantic_golden_is_structurally_valid(filename: str) -> None:
    result, data = validator.validate_file(filename, validator.GOLDEN_SPECS[filename])

    assert data is not None
    assert result.errors == []


@pytest.mark.unit
def test_config_validator_rejects_malformed_grounding_contracts() -> None:
    data = json.loads((GOLDEN_ROOT / "the-mariner-config.json").read_text())
    data["fields"]["genre"]["allowed_values"] = "action"
    result = validator.ValidationResult("config.json", "Config")

    validator.validate_config(
        data,
        validator.GOLDEN_SPECS["the-mariner-config.json"],
        result,
    )

    assert "fields.genre: allowed_values must be a list, got str" in result.errors


@pytest.mark.unit
def test_config_validator_rejects_unknown_or_repeated_equivalent_values() -> None:
    data = json.loads((GOLDEN_ROOT / "open-frequency-config.json").read_text())
    data["fields"]["tone"]["equivalent_value_groups"] = [
        ["hopeful", "invented"],
        ["hopeful", "uplifting"],
    ]
    result = validator.ValidationResult("config.json", "Config")

    validator.validate_config(
        data,
        validator.GOLDEN_SPECS["open-frequency-config.json"],
        result,
    )

    assert "fields.tone: equivalent values not in allowed_values: invented" in result.errors
    assert (
        "fields.tone: equivalent values appear in multiple groups: hopeful"
        in result.errors
    )


@pytest.mark.unit
def test_qa_golden_exercises_both_verdicts() -> None:
    data = json.loads((GOLDEN_ROOT / "qa-pass-golden.json").read_text())

    assert {case["expected_passed"] for case in data.values()} == {True, False}


def _qa_errors(data: dict) -> list[str]:
    result = validator.ValidationResult("qa.json", "QA Pass")
    validator.validate_qa_pass(
        data,
        validator.GOLDEN_SPECS["qa-pass-golden.json"],
        result,
    )
    return result.errors


@pytest.mark.unit
@pytest.mark.parametrize(
    "mutation",
    [
        "missing_families",
        "unknown_family",
        "duplicate_family",
        "missing_family_mapping",
        "empty_summary_anchors",
        "missing_claim_family",
        "empty_claim_alternatives",
        "missing_claim_field",
        "defect_source_overlap",
        "legacy_min_errors",
    ],
)
def test_qa_validator_fails_closed_on_family_contract_drift(mutation: str) -> None:
    data = json.loads((GOLDEN_ROOT / "qa-pass-golden.json").read_text())
    bad = data["bad_scene"]
    if mutation == "missing_families":
        bad.pop("required_families")
    elif mutation == "unknown_family":
        bad["required_families"][-1] = "unknown"
    elif mutation == "duplicate_family":
        bad["critical_error_families"].append(bad["critical_error_families"][0])
    elif mutation == "missing_family_mapping":
        bad["required_issues"] = [
            issue for issue in bad["required_issues"] if issue["field"] != "confidence"
        ]
    elif mutation == "empty_summary_anchors":
        bad["required_in_summary_any"] = []
    elif mutation == "missing_claim_family":
        bad["family_claim_contracts"].pop("tone")
    elif mutation == "empty_claim_alternatives":
        bad["family_claim_contracts"]["tone"]["defect_relations"] = []
    elif mutation == "missing_claim_field":
        bad["family_claim_contracts"]["tone"].pop("source_corrections")
    elif mutation == "defect_source_overlap":
        bad["family_claim_contracts"]["cast_identity"]["source_relations"].append(
            "omits"
        )
    elif mutation == "legacy_min_errors":
        bad["min_errors"] = 6

    assert _qa_errors(data)


def _continuity_errors(data: dict) -> list[str]:
    result = validator.ValidationResult("continuity.json", "Continuity")
    validator.validate_continuity(
        data,
        validator.GOLDEN_SPECS["continuity-extraction-golden.json"],
        result,
    )
    return result.errors


@pytest.mark.unit
def test_continuity_validator_requires_change_evidence_and_explicitness_contract() -> None:
    data = json.loads((GOLDEN_ROOT / "continuity-extraction-golden.json").read_text())
    change = data["dock_night"]["expected_changes"]["character:billy"][0]
    change.pop("evidence_patterns")
    change.pop("is_explicit")

    errors = _continuity_errors(data)

    assert any("missing 'evidence_patterns'" in error for error in errors)
    assert any("missing 'is_explicit'" in error for error in errors)


@pytest.mark.unit
def test_continuity_validator_rejects_unknown_fields_and_change_keys() -> None:
    data = json.loads((GOLDEN_ROOT / "continuity-extraction-golden.json").read_text())
    mutation = deepcopy(data)
    mutation["dock_day"]["answer_hint"] = "do not allow"
    change = mutation["dock_night"]["expected_changes"]["character:billy"][0]
    change["unscored_note"] = "padding"
    change["property_key"] = "unrequested_state"

    errors = _continuity_errors(mutation)

    assert any("unexpected fields ['answer_hint']" in error for error in errors)
    assert any("unexpected fields ['unscored_note']" in error for error in errors)
    assert any("absent from expected_properties" in error for error in errors)


@pytest.mark.unit
def test_entity_validator_rejects_required_excluded_overlap() -> None:
    data = json.loads(
        (GOLDEN_ROOT / "open-frequency-entity-discovery.json").read_text()
    )
    data["characters"]["excluded"].append("ARIA")
    result = validator.ValidationResult("entity.json", "Entity")
    validator.validate_entity_discovery(
        data,
        validator.GOLDEN_SPECS["open-frequency-entity-discovery.json"],
        result,
    )

    assert any("also declared required/optional" in error for error in result.errors)


def _prop_errors(data: dict) -> list[str]:
    result = validator.ValidationResult("props.json", "Props")
    validator.validate_keyed_object(
        data,
        validator.GOLDEN_SPECS["the-mariner-props.json"],
        result,
    )
    return result.errors


@pytest.mark.unit
def test_mariner_prop_validator_enforces_runtime_ids_and_exact_associations() -> None:
    data = json.loads((GOLDEN_ROOT / "the-mariner-props.json").read_text())

    missing = deepcopy(data)
    missing["OAR"].pop("associated_characters")
    assert any(
        "missing required field 'associated_characters'" in error
        for error in _prop_errors(missing)
    )

    malformed = deepcopy(data)
    malformed["OAR"]["associated_characters"] = ["the-mariner"]
    assert any("not a lowercase_underscore ID" in error for error in _prop_errors(malformed))

    wrong_owner = deepcopy(data)
    wrong_owner["OAR"]["associated_characters"] = ["rose"]
    assert any(
        "source-verified list ['the_mariner']" in error
        for error in _prop_errors(wrong_owner)
    )


@pytest.mark.unit
def test_mariner_prop_golden_preserves_exact_qualified_source_headings() -> None:
    data = json.loads((GOLDEN_ROOT / "the-mariner-props.json").read_text())

    assert data["PURSE"]["must_mention_scenes"] == [
        "INT. RUDDY & GREEN BUILDING - ELEVATOR",
        "INT. STAIRWELL - CONTINUOUS",
        "INT. 15TH FLOOR",
    ]
    assert data["AIRTAG"]["must_mention_scenes"] == [
        "INT. RUDDY & GREEN BUILDING - ELEVATOR",
        "INT. 12TH FLOOR STAIRWELL - CONTINUOUS",
    ]
    assert data["BEER BOTTLES"]["must_mention_scenes"] == [
        "BEGIN FLASHBACK: EXT. COASTLINE - DAY - PAST",
        "EXT. BACKYARD - DAY - (FLASHBACK)",
        "EXT. COASTLINE - DAY - (FLASHBACK)",
    ]
    assert data["BENCH PRESS"]["must_mention_scenes"] == [
        "BEGIN FLASHBACK: EXT. BACKYARD - DAY - PAST",
        "EXT. BACKYARD - DAY - (FLASHBACK)",
    ]


@pytest.mark.unit
def test_mariner_script_bible_encodes_exact_source_and_exclusion_contracts() -> None:
    data = json.loads((GOLDEN_ROOT / "the-mariner-script-bible.json").read_text())

    headings = data["source_headings"]
    assert len(headings) == 15
    assert headings.count("EXT. BACKYARD - DAY - (FLASHBACK)") == 2
    event_descriptions = {
        event["description"] for event in data["required_story_events"]
    }
    assert {
        "Rose affirms that Mariner became a real hero",
        "Rose says Mariner never backs down from a fight",
        "Mariner smiles at Rose's affirmation",
        "Mariner clenches his hands into fists",
        "The screenplay cuts to black",
        "The final confrontation remains unresolved",
    } <= event_descriptions

    patterns = [re.compile(pattern) for pattern in data["forbidden_claim_patterns"]]
    unsupported = [
        "Mariner waits at a dock in Newfoundland.",
        "Mariner defeats Salvatori in the final fight.",
        "Mariner overpowered Salvatori.",
        "Mariner wins the final fight.",
        "The final confrontation is won by Salvatori.",
        "Salvatori defeated Mariner after demanding the password.",
        "Salvatori shot Rose after demanding the password.",
        "Rose kills Salvatori.",
        "Mariner captures Salvatori.",
        "Mariner triumphs over Salvatori.",
        "Salvatori escapes.",
    ]
    assert all(any(pattern.search(claim) for pattern in patterns) for claim in unsupported)

    supported = [
        "Salvatori fires a shot into the bookcase behind Rose.",
        "Mariner defeats Vinnie before reaching the fifteenth floor.",
    ]
    assert all(not any(pattern.search(claim) for pattern in patterns) for claim in supported)


@pytest.mark.unit
def test_script_bible_validator_rejects_unusable_story_contracts() -> None:
    data = json.loads((GOLDEN_ROOT / "open-frequency-script-bible.json").read_text())
    data["required_story_events"][0]["minimum_matches"] = 99
    data["forbidden_claim_patterns"][0] = "["
    result = validator.ValidationResult("bible.json", "Bible")
    validator.validate_script_bible(
        data,
        validator.GOLDEN_SPECS["open-frequency-script-bible.json"],
        result,
    )

    assert any("minimum_matches exceeds keyword count" in error for error in result.errors)
    assert any("invalid regex" in error for error in result.errors)


@pytest.mark.unit
def test_normalization_validator_requires_boolean_fidelity_rules() -> None:
    data = json.loads(
        (GOLDEN_ROOT / "normalize-open-frequency-corrupted-golden.json").read_text()
    )
    data["structural_rules"]["preserve_source_action_order"] = "yes"
    result = validator.ValidationResult("normalization.json", "Normalization")
    validator.validate_normalization(
        data,
        validator.GOLDEN_SPECS["normalize-open-frequency-corrupted-golden.json"],
        result,
    )

    assert "structural_rules.preserve_source_action_order must be a boolean" in result.errors
