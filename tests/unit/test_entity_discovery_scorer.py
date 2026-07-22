from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCORER_ROOT = REPO_ROOT / "benchmarks" / "scorers"
if str(SCORER_ROOT) not in sys.path:
    sys.path.insert(0, str(SCORER_ROOT))

scorer = importlib.import_module("entity_discovery_scorer")
OPEN_FREQUENCY_GOLDEN = REPO_ROOT / "benchmarks" / "golden" / (
    "open-frequency-entity-discovery.json"
)
MARINER_GOLDEN = REPO_ROOT / "benchmarks" / "golden" / (
    "the-mariner-entity-discovery.json"
)


def _context(tmp_path: Path) -> dict:
    golden = {
        "characters": {
            "required": ["ALICE"],
            "acceptable_aliases": {"ALICE": ["DR. ALICE"]},
            "optional": [],
        },
        "locations": {
            "required": ["LAB"],
            "acceptable_aliases": {},
            "optional": [],
        },
        "props": {
            "required": ["KEY"],
            "acceptable_aliases": {},
            "optional": [],
        },
    }
    path = tmp_path / "golden.json"
    path.write_text(json.dumps(golden))
    return {"vars": {"golden_path": str(path)}}


@pytest.mark.unit
def test_entity_discovery_scorer_rewards_grounded_control(tmp_path: Path) -> None:
    result = scorer.get_assert(
        json.dumps({"characters": ["ALICE"], "locations": ["LAB"], "props": ["KEY"]}),
        _context(tmp_path),
    )

    assert result["pass"] is True
    assert result["score"] == 1.0


@pytest.mark.unit
def test_entity_discovery_scorer_rejects_empty_entity_names(tmp_path: Path) -> None:
    result = scorer.get_assert(
        json.dumps({"characters": [""], "locations": ["  "], "props": [""]}),
        _context(tmp_path),
    )

    assert result["pass"] is False
    assert result["score"] < 0.3
    assert "Missing characters: ALICE" in result["reason"]


@pytest.mark.unit
def test_entity_discovery_scorer_dominated_mutation_scores_lower(tmp_path: Path) -> None:
    context = _context(tmp_path)
    complete = scorer.get_assert(
        json.dumps({"characters": ["DR. ALICE"], "locations": ["LAB"], "props": ["KEY"]}),
        context,
    )
    missing_prop = scorer.get_assert(
        json.dumps({"characters": ["DR. ALICE"], "locations": ["LAB"], "props": []}),
        context,
    )

    assert missing_prop["score"] < complete["score"]


@pytest.mark.unit
def test_entity_discovery_scorer_rejects_any_unrecognized_entity(tmp_path: Path) -> None:
    result = scorer.get_assert(
        json.dumps(
            {
                "characters": ["ALICE", "INVENTED DRAGON"],
                "locations": ["LAB"],
                "props": ["KEY"],
            }
        ),
        _context(tmp_path),
    )

    assert result["pass"] is False
    assert "Unrecognized entities: 1" in result["reason"]


@pytest.mark.unit
def test_entity_discovery_scorer_rejects_extra_root_keys(tmp_path: Path) -> None:
    result = scorer.get_assert(
        json.dumps(
            {
                "characters": ["ALICE"],
                "locations": ["LAB"],
                "props": ["KEY"],
                "bonus": ["INVENTED DRAGON"],
            }
        ),
        _context(tmp_path),
    )

    assert result["pass"] is False
    assert "Schema errors: extra:bonus" in result["reason"]


@pytest.mark.unit
@pytest.mark.parametrize(
    "characters",
    [["ALICE", "alice"], ["ALICE", ""], ["ALICE", 7], "ALICE"],
)
def test_entity_discovery_scorer_rejects_invalid_entity_arrays(
    tmp_path: Path, characters: object
) -> None:
    result = scorer.get_assert(
        json.dumps(
            {"characters": characters, "locations": ["LAB"], "props": ["KEY"]}
        ),
        _context(tmp_path),
    )

    assert result["pass"] is False
    assert "Schema errors:" in result["reason"]


def _open_frequency_context() -> tuple[dict, dict, dict]:
    golden = json.loads(OPEN_FREQUENCY_GOLDEN.read_text())
    candidate = {
        category: list(config["required"])
        for category, config in golden.items()
        if category in {"characters", "locations", "props"}
    }
    return golden, candidate, {"vars": {"golden_path": str(OPEN_FREQUENCY_GOLDEN)}}


@pytest.mark.unit
def test_entity_discovery_requires_every_required_prop() -> None:
    _, candidate, context = _open_frequency_context()
    candidate["props"] = []
    result = scorer.get_assert(json.dumps(candidate), context)

    assert result["pass"] is False
    assert "Missing props:" in result["reason"]


@pytest.mark.unit
def test_entity_discovery_rejects_named_animal_in_people_only_category() -> None:
    _, candidate, context = _open_frequency_context()
    candidate["characters"].append("COMET")
    result = scorer.get_assert(json.dumps(candidate), context)

    assert result["pass"] is False
    assert "Explicitly excluded entities: characters:COMET" in result["reason"]


@pytest.mark.unit
def test_entity_discovery_rejects_explicit_minor_prop_noun_dump() -> None:
    _, candidate, context = _open_frequency_context()
    candidate["props"].extend(["TOOL BAG", "CASSETTE", "NOTEBOOK", "MAP", "BREAD"])
    result = scorer.get_assert(json.dumps(candidate), context)

    assert result["pass"] is False
    assert "Explicitly excluded entities:" in result["reason"]


@pytest.mark.unit
def test_entity_discovery_does_not_credit_undeclared_name_fragments() -> None:
    _, candidate, context = _open_frequency_context()
    candidate["props"].remove("ON AIR SIGN")
    candidate["props"].append("SIGN")
    result = scorer.get_assert(json.dumps(candidate), context)

    assert result["pass"] is False
    assert "Missing props: ON AIR SIGN" in result["reason"]


@pytest.mark.unit
def test_entity_discovery_accepts_documented_optional_classifications() -> None:
    golden, candidate, context = _open_frequency_context()
    candidate["locations"].append("NORTH SHELTER")
    candidate["props"].append("OPEN FREQUENCY SIGN")
    result = scorer.get_assert(json.dumps(candidate), context)

    assert "NORTH SHELTER" in golden["locations"]["optional"]
    assert "OPEN FREQUENCY SIGN" in golden["props"]["optional"]
    assert result["pass"] is True


@pytest.mark.unit
def test_entity_discovery_accepts_separately_staged_mariner_building_faces() -> None:
    golden = json.loads(MARINER_GOLDEN.read_text())
    candidate = {
        category: config["required"] + config["optional"]
        for category, config in golden.items()
        if category in {"characters", "locations", "props"}
    }
    context = {"vars": {"golden_path": str(MARINER_GOLDEN)}}

    result = scorer.get_assert(json.dumps(candidate), context)

    assert "RUDDY & GREENE BUILDING - FRONT" in golden["locations"]["optional"]
    assert "RUDDY & GREENE BUILDING - REAR" in golden["locations"]["optional"]
    assert result["pass"] is True
    assert "Unrecognized entities" not in result["reason"]
