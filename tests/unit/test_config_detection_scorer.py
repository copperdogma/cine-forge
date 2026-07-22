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

scorer = importlib.import_module("config_detection_scorer")

SOURCE_TEXT = """Title: Test Film

FADE IN:

INT. LAB - DAY

ALICE fights armed intruders in the LAB during a tense rescue.

EXT. ROOF - NIGHT

BOB helps Alice from the ROOF before the rescue ends.

CUT TO BLACK.
"""


def _field(importance: str, **values: object) -> dict:
    return {"importance": importance, "min_confidence": 0.8, **values}


def _context(tmp_path: Path) -> dict:
    golden = {
        "fields": {
            "title": _field("critical", expected_value="Test Film"),
            "format": _field(
                "critical",
                expected_values=["short film"],
                allowed_values=["short film"],
                rationale_must_mention_any=["FADE IN", "CUT TO BLACK"],
            ),
            "genre": _field(
                "important",
                expected_keywords=["action", "thriller", "adventure"],
                must_include_at_least=1,
                allowed_values=["action", "thriller", "adventure"],
                rationale_must_mention_any=["fights", "armed intruders"],
            ),
            "tone": _field(
                "important",
                expected_keywords=["dark comedy", "irreverent", "tense"],
                must_include_at_least=1,
                allowed_values=["dark comedy", "irreverent", "tense"],
                rationale_must_mention_any=["tense rescue"],
            ),
            "estimated_duration_minutes": _field(
                "critical",
                expected_range=[10, 25],
                rationale_must_mention_any=["FADE IN", "CUT TO BLACK"],
            ),
            "primary_characters": _field(
                "critical",
                must_include=["ALICE"],
                allowed_values=["ALICE"],
                rationale_must_mention_any=["ALICE"],
            ),
            "supporting_characters": _field(
                "important",
                should_include_any=["BOB", "CARA"],
                min_count=1,
                allowed_values=["BOB", "CARA"],
                rationale_must_mention_any=["BOB"],
            ),
            "location_count": _field(
                "important",
                expected_range=[2, 4],
                rationale_must_mention_any=["LAB", "ROOF"],
            ),
            "locations_summary": _field(
                "important",
                must_mention=["LAB", "ROOF"],
                forbidden_keywords=["palace", "Mars"],
                rationale_must_mention_any=["LAB", "ROOF"],
            ),
            "target_audience": _field(
                "critical",
                expected_keywords=["mature audiences", "adults"],
                allow_null=False,
                rationale_must_mention_any=["armed intruders", "fights"],
            ),
        }
    }
    golden["fields"]["title"].update(
        allowed_values=["Test Film"],
        rationale_must_mention_any=["Test Film"],
    )
    path = tmp_path / "golden.json"
    path.write_text(json.dumps(golden))
    return {"vars": {"golden_path": str(path), "screenplay": SOURCE_TEXT}}


def _wrapped(value: object, rationale: str, confidence: object = 0.9) -> dict:
    return {"value": value, "confidence": confidence, "rationale": rationale}


def _control() -> dict:
    return {
        "title": _wrapped("Test Film", "The title page names Test Film."),
        "format": _wrapped(
            "short film",
            "The complete story runs from FADE IN through CUT TO BLACK.",
        ),
        "genre": _wrapped(
            ["action"],
            "ALICE fights armed intruders, which supports action.",
        ),
        "tone": _wrapped(
            ["tense"],
            "The tense rescue on the ROOF supports this tone.",
        ),
        "estimated_duration_minutes": _wrapped(
            18,
            "The compact action from FADE IN to CUT TO BLACK supports this estimate.",
        ),
        "primary_characters": _wrapped(
            ["ALICE"],
            "ALICE drives the LAB rescue.",
        ),
        "supporting_characters": _wrapped(
            ["BOB"],
            "BOB helps Alice from the ROOF.",
        ),
        "location_count": _wrapped(
            2,
            "The screenplay stages the LAB and ROOF.",
        ),
        "locations_summary": _wrapped(
            "The LAB and ROOF are the main locations.",
            "The action moves from the LAB to the ROOF.",
        ),
        "target_audience": _wrapped(
            "mature audiences",
            "The armed intruders and fighting support mature audiences.",
        ),
    }


@pytest.mark.unit
def test_config_scorer_rewards_source_grounded_control(tmp_path: Path) -> None:
    result = scorer.get_assert(json.dumps(_control()), _context(tmp_path))

    assert result["pass"] is True
    assert result["score"] == 1.0


@pytest.mark.unit
def test_config_scorer_treats_keywords_as_alternatives(tmp_path: Path) -> None:
    result = scorer.get_assert(json.dumps(_control()), _context(tmp_path))

    assert "genre_accuracy=1.00" in result["reason"]
    assert "tone_accuracy=1.00" in result["reason"]


@pytest.mark.unit
def test_config_scorer_rejects_negated_critical_format(tmp_path: Path) -> None:
    output = {
        **_control(),
        "format": _wrapped(
            "not a short film",
            "The story runs from FADE IN to CUT TO BLACK.",
        ),
    }
    result = scorer.get_assert(json.dumps(output), _context(tmp_path))

    assert result["pass"] is False
    assert "format_accuracy=0.00" in result["reason"]


@pytest.mark.unit
def test_config_scorer_rejects_missing_declared_field(tmp_path: Path) -> None:
    output = _control()
    del output["target_audience"]
    result = scorer.get_assert(json.dumps(output), _context(tmp_path))

    assert result["pass"] is False
    assert "Missing fields: target_audience" in result["reason"]


@pytest.mark.unit
def test_config_scorer_dominated_mutation_scores_lower(tmp_path: Path) -> None:
    context = _context(tmp_path)
    complete = scorer.get_assert(json.dumps(_control()), context)
    output = {
        **_control(),
        "estimated_duration_minutes": _wrapped(
            40,
            "The story runs from FADE IN to CUT TO BLACK.",
        ),
    }
    wrong_duration = scorer.get_assert(json.dumps(output), context)

    assert wrong_duration["score"] < complete["score"]


@pytest.mark.unit
def test_config_scorer_rejects_boolean_confidence_as_numeric(tmp_path: Path) -> None:
    output = {key: {**value, "confidence": True} for key, value in _control().items()}
    result = scorer.get_assert(json.dumps(output), _context(tmp_path))

    assert "confidence_quality=0.00" in result["reason"]
    assert result["score"] < 1.0
    assert result["pass"] is False


@pytest.mark.unit
def test_config_scorer_hard_gates_materially_wrong_important_fields(tmp_path: Path) -> None:
    output = {
        **_control(),
        "estimated_duration_minutes": _wrapped(
            80,
            "The story runs from FADE IN to CUT TO BLACK.",
        ),
        "location_count": _wrapped(20, "The source stages the LAB and ROOF."),
        "locations_summary": _wrapped(
            "An unrelated desert and submarine.",
            "The source stages the LAB and ROOF.",
        ),
    }
    result = scorer.get_assert(json.dumps(output), _context(tmp_path))

    assert result["pass"] is False
    assert "duration_accuracy=0.00" in result["reason"]
    assert "location_accuracy=0.00" in result["reason"]


@pytest.mark.unit
def test_config_scorer_normalizes_audience_singular_and_plural(tmp_path: Path) -> None:
    context = _context(tmp_path)
    path = Path(context["vars"]["golden_path"])
    golden = json.loads(path.read_text())
    golden["fields"]["target_audience"]["expected_keywords"] = ["adult"]
    path.write_text(json.dumps(golden))
    output = {
        **_control(),
        "target_audience": _wrapped(
            "Adults (Rated R)",
            "The armed intruders and fighting support an adult rating.",
        ),
    }

    result = scorer.get_assert(json.dumps(output), context)

    assert result["pass"] is True
    assert "audience_accuracy=1.00" in result["reason"]


@pytest.mark.unit
def test_config_scorer_rejects_flat_or_extra_schema(tmp_path: Path) -> None:
    flat = {key: value["value"] for key, value in _control().items()}
    flat["invented_field"] = "padding"

    result = scorer.get_assert(json.dumps(flat), _context(tmp_path))

    assert result["pass"] is False
    assert "Unexpected fields: invented_field" in result["reason"]
    assert "title: expected exactly value/confidence/rationale" in result["reason"]


@pytest.mark.unit
def test_config_scorer_rejects_missing_or_generic_rationale(tmp_path: Path) -> None:
    output = _control()
    output["format"] = {**output["format"], "rationale": "Typical"}

    result = scorer.get_assert(json.dumps(output), _context(tmp_path))

    assert result["pass"] is False
    assert "format: rationale must be substantive" in result["reason"]


@pytest.mark.unit
def test_config_scorer_rejects_unsupported_padding_and_generic_rationales(
    tmp_path: Path,
) -> None:
    output = _control()
    output["genre"]["value"].append("romance")
    output["tone"]["value"].append("sunny")
    output["primary_characters"]["value"].append("INVENTED DRAGON")
    output["supporting_characters"]["value"].append("INVENTED QUEEN")
    output["locations_summary"]["value"] += " plus a palace on Mars."
    for field in output.values():
        field["rationale"] = "Source evidence."

    result = scorer.get_assert(json.dumps(output), _context(tmp_path))

    assert result["pass"] is False
    assert result["score"] < 1.0
    assert "genre: unsupported values: romance" in result["reason"]
    assert "tone: unsupported values: sunny" in result["reason"]
    assert "primary_characters: unsupported values: INVENTED DRAGON" in result["reason"]
    assert "supporting_characters: unsupported values: INVENTED QUEEN" in result["reason"]
    assert "locations_summary: forbidden unsupported claims: palace, Mars" in result["reason"]
    assert "rationale_grounding=0.00" in result["reason"]
