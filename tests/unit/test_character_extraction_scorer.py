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

scorer = importlib.import_module("character_extraction_scorer")

SCREENPLAY = """INT. LAB - DAY

DR ALICE, Bob's older sister, warns Bob about the reactor and hides the red key
from the gang.

INT. OBSERVATION DECK - NIGHT

Bob says Alice solved the reactor problem.
"""


def _golden() -> dict:
    return {
        "ALICE": {
            "character_id": "alice",
            "name": "ALICE",
            "aliases": ["DR ALICE"],
            "narrative_role": "protagonist",
            "key_traits": ["cautious scientist"],
            "must_have_relationships": [{"target": "BOB", "type": "sibling"}],
            "must_have_evidence": ["Alice warns Bob about the reactor"],
            "key_facts": ["Alice hides the red key from the gang"],
            "must_mention_scenes": ["INT. LAB - DAY"],
        }
    }


def _context(tmp_path: Path, golden: dict | None = None) -> dict:
    path = tmp_path / "golden.json"
    path.write_text(json.dumps(golden or _golden()))
    return {
        "vars": {
            "golden_path": str(path),
            "character_name": "ALICE",
            "screenplay": SCREENPLAY,
        }
    }


def _control(**overrides: object) -> dict:
    result = {
        "character_id": "alice",
        "name": "ALICE",
        "aliases": ["DR ALICE"],
        "description": "A cautious scientist. Alice hides the red key from the gang.",
        "explicit_evidence": [
            {
                "trait": "protective",
                "quote": (
                    "DR ALICE, Bob's older sister, warns Bob about the reactor and hides "
                    "the red key from the gang."
                ),
                "source_scene": "INT. LAB - DAY",
            }
        ],
        "inferred_traits": [
            {
                "trait": "cautious scientist",
                "value": "She warns others about hazards.",
                "confidence": 0.9,
                "rationale": "Her warning is explicit.",
            }
        ],
        "scene_presence": ["INT. LAB - DAY"],
        "dialogue_summary": "She speaks in direct warnings.",
        "narrative_role": "protagonist",
        "relationships": [
            {
                "target_character": "BOB",
                "relationship_type": "sibling",
                "evidence": "DR ALICE is Bob's older sister.",
                "confidence": 0.9,
            }
        ],
        "overall_confidence": 0.95,
    }
    result.update(overrides)
    return result


@pytest.mark.unit
def test_character_scorer_rewards_source_grounded_control(tmp_path: Path) -> None:
    result = scorer.get_assert(json.dumps(_control()), _context(tmp_path))

    assert result["pass"] is True
    assert result["score"] == 1.0


@pytest.mark.unit
def test_character_scorer_rejects_alias_as_canonical_name(tmp_path: Path) -> None:
    result = scorer.get_assert(
        json.dumps(_control(name="DR ALICE")),
        _context(tmp_path),
    )

    assert result["pass"] is False
    assert "identity=0.50" in result["reason"]


@pytest.mark.unit
def test_character_scorer_rejects_wrong_relationship_type(tmp_path: Path) -> None:
    relationship = {**_control()["relationships"][0], "relationship_type": "enemy"}
    result = scorer.get_assert(
        json.dumps(_control(relationships=[relationship])),
        _context(tmp_path),
    )

    assert result["pass"] is False
    assert "relationship_accuracy=0.00" in result["reason"]


@pytest.mark.unit
def test_character_scorer_rejects_relationship_evidence_that_denies_the_claim(
    tmp_path: Path,
) -> None:
    relationship = {
        **_control()["relationships"][0],
        "evidence": "The source never establishes that Alice and Bob are siblings.",
    }

    result = scorer.get_assert(
        json.dumps(_control(relationships=[relationship])),
        _context(tmp_path),
    )

    assert result["pass"] is False
    assert "relationship_accuracy=0.00" in result["reason"]


@pytest.mark.unit
def test_character_scorer_rejects_invented_extra_relationship(tmp_path: Path) -> None:
    invented = {
        "target_character": "EVE",
        "relationship_type": "adversary",
        "evidence": "Invented support.",
        "confidence": 0.8,
    }
    result = scorer.get_assert(
        json.dumps(_control(relationships=[*_control()["relationships"], invented])),
        _context(tmp_path),
    )

    assert result["pass"] is False
    assert "relationship_accuracy=0.67" in result["reason"]


@pytest.mark.unit
def test_character_scorer_rejects_fabricated_quote(tmp_path: Path) -> None:
    evidence = {
        **_control()["explicit_evidence"][0],
        "quote": "Alice pilots a rocket to Mars with Bob.",
    }
    result = scorer.get_assert(
        json.dumps(_control(explicit_evidence=[evidence])),
        _context(tmp_path),
    )

    assert result["pass"] is False
    assert "source_grounding=0.00" in result["reason"]


@pytest.mark.unit
def test_character_scorer_rejects_real_quote_bound_to_wrong_heading(tmp_path: Path) -> None:
    evidence = {
        **_control()["explicit_evidence"][0],
        "source_scene": "INT. OBSERVATION DECK - NIGHT",
    }
    result = scorer.get_assert(
        json.dumps(_control(explicit_evidence=[evidence])),
        _context(tmp_path),
    )

    assert result["pass"] is False
    assert "source_grounding=0.00" in result["reason"]


@pytest.mark.unit
def test_character_scorer_allows_evidence_from_scene_where_target_is_absent(
    tmp_path: Path,
) -> None:
    golden = _golden()
    golden["ALICE"]["must_have_evidence"] = ["Bob says Alice solved the reactor problem"]
    evidence = {
        "trait": "capable",
        "quote": "Bob says Alice solved the reactor problem.",
        "source_scene": "INT. OBSERVATION DECK - NIGHT",
    }
    result = scorer.get_assert(
        json.dumps(_control(explicit_evidence=[evidence])),
        _context(tmp_path, golden),
    )

    assert result["pass"] is True
    assert result["score"] == 1.0


@pytest.mark.unit
def test_character_scorer_requires_evidence_inside_grounded_quotes(tmp_path: Path) -> None:
    evidence = {
        **_control()["explicit_evidence"][0],
        "quote": "Alice hides the red key from the gang.",
    }
    result = scorer.get_assert(
        json.dumps(
            _control(
                description=(
                    "A cautious scientist. Alice warns Bob about the reactor and hides the red "
                    "key from the gang."
                ),
                explicit_evidence=[evidence],
            )
        ),
        _context(tmp_path),
    )

    assert result["pass"] is False
    assert "evidence_recall=0.00" in result["reason"]


@pytest.mark.unit
def test_character_scorer_rejects_invalid_confidence(tmp_path: Path) -> None:
    result = scorer.get_assert(
        json.dumps(_control(overall_confidence=True)),
        _context(tmp_path),
    )

    assert result["pass"] is False
    assert "schema_quality=" in result["reason"]


@pytest.mark.unit
@pytest.mark.parametrize("mutation", ["top_level", "evidence", "trait", "relationship"])
def test_character_scorer_rejects_additional_schema_fields(
    tmp_path: Path,
    mutation: str,
) -> None:
    payload = _control()
    if mutation == "top_level":
        payload["prominence"] = "primary"
    else:
        field = {
            "evidence": "explicit_evidence",
            "trait": "inferred_traits",
            "relationship": "relationships",
        }[mutation]
        payload[field][0]["unexpected"] = "answer-bearing extra"

    result = scorer.get_assert(json.dumps(payload), _context(tmp_path))

    assert result["pass"] is False
    assert "schema_quality=" in result["reason"]


@pytest.mark.unit
def test_character_scorer_rejects_role_outside_maintained_vocabulary(
    tmp_path: Path,
) -> None:
    golden = _golden()
    golden["ALICE"]["narrative_role"] = "antagonist"
    result = scorer.get_assert(
        json.dumps(_control(narrative_role="antagonist")),
        _context(tmp_path, golden),
    )

    assert result["pass"] is False
    assert "narrative_role=1.00" in result["reason"]
    assert "schema_quality=" in result["reason"]


@pytest.mark.unit
def test_character_scorer_rejects_extra_scene_and_alias(tmp_path: Path) -> None:
    result = scorer.get_assert(
        json.dumps(
            _control(
                aliases=["DR ALICE", "THE EMPRESS"],
                scene_presence=["INT. LAB - DAY", "EXT. MOON - NIGHT"],
            )
        ),
        _context(tmp_path),
    )

    assert result["pass"] is False
    assert "alias_accuracy=" in result["reason"]
    assert "scene_accuracy=" in result["reason"]


@pytest.mark.unit
def test_character_scorer_allows_source_honest_empty_alias_list(tmp_path: Path) -> None:
    golden = _golden()
    golden["ALICE"]["aliases"] = []
    result = scorer.get_assert(
        json.dumps(_control(aliases=[])),
        _context(tmp_path, golden),
    )

    assert result["pass"] is True
    assert result["score"] == 1.0


@pytest.mark.unit
def test_character_scorer_dominated_mutation_scores_lower(tmp_path: Path) -> None:
    context = _context(tmp_path)
    complete = scorer.get_assert(json.dumps(_control()), context)
    mutated = scorer.get_assert(
        json.dumps(
            _control(
                relationships=[],
                description="A cautious scientist.",
            )
        ),
        context,
    )

    assert mutated["score"] < complete["score"]
    assert mutated["pass"] is False
