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

scorer = importlib.import_module("scene_extraction_scorer")
OPEN_FREQUENCY_GOLDEN = REPO_ROOT / "benchmarks" / "golden" / (
    "open-frequency-scenes.json"
)
OPEN_FREQUENCY_SOURCE = REPO_ROOT / "tests" / "fixtures" / "ingest_inputs" / (
    "open_frequency_short.fountain"
)


def _scenes() -> list[dict]:
    return [
        {
            "scene_number": 1,
            "heading": "INT. LAB - DAY",
            "int_ext": "INT",
            "location": "LAB",
            "time_of_day": "DAY",
            "summary": "Alice unlocks the red vault.",
            "characters": ["ALICE"],
        },
        {
            "scene_number": 2,
            "heading": "EXT. ROOF - NIGHT",
            "int_ext": "EXT",
            "location": "ROOF",
            "time_of_day": "NIGHT",
            "summary": "Bob signals the helicopter.",
            "characters": ["BOB"],
        },
    ]


def _context(tmp_path: Path) -> dict:
    path = tmp_path / "golden.json"
    path.write_text(json.dumps({"title": "Test", "scene_count": 2, "scenes": _scenes()}))
    return {"vars": {"golden_path": str(path)}}


def _payload(scenes: list[dict] | None = None, **overrides: object) -> dict:
    value = {
        "title": "Test",
        "scene_count": len(scenes if scenes is not None else _scenes()),
        "scenes": scenes if scenes is not None else _scenes(),
    }
    value.update(overrides)
    return value


@pytest.mark.unit
def test_scene_extraction_scorer_rewards_per_scene_grounded_control(tmp_path: Path) -> None:
    result = scorer.get_assert(json.dumps(_payload()), _context(tmp_path))

    assert result["pass"] is True
    assert result["score"] == 1.0


@pytest.mark.unit
def test_scene_extraction_scorer_rejects_fabricated_per_scene_facts(tmp_path: Path) -> None:
    fabricated = [
        {
            **scene,
            "scene_number": 3 - scene["scene_number"],
            "int_ext": "EXT" if scene["int_ext"] == "INT" else "INT",
            "location": "MOON BASE",
            "time_of_day": "DAWN",
            "summary": "Invented dragons celebrate an unrelated coronation.",
            "characters": ["BOB"] if scene["characters"] == ["ALICE"] else ["ALICE"],
        }
        for scene in _scenes()
    ]
    result = scorer.get_assert(json.dumps(_payload(fabricated)), _context(tmp_path))

    assert result["pass"] is False
    assert result["score"] < 0.7
    assert "scene_field_accuracy" in result["reason"]


@pytest.mark.unit
def test_scene_extraction_scorer_dominated_mutation_scores_lower(tmp_path: Path) -> None:
    context = _context(tmp_path)
    complete = scorer.get_assert(json.dumps(_payload()), context)
    mutated = _scenes()
    mutated[1] = {
        **mutated[1],
        "location": "INVENTED PALACE",
        "characters": ["ALICE"],
        "summary": "An unrelated banquet begins.",
    }
    dominated = scorer.get_assert(json.dumps(_payload(mutated)), context)

    assert dominated["score"] < complete["score"]


def _open_frequency_context() -> tuple[dict, dict]:
    golden = json.loads(OPEN_FREQUENCY_GOLDEN.read_text())
    context = {
        "vars": {
            "golden_path": str(OPEN_FREQUENCY_GOLDEN),
            "screenplay": OPEN_FREQUENCY_SOURCE.read_text(),
        }
    }
    return golden, context


@pytest.mark.unit
def test_scene_extraction_requires_every_exact_scene_boundary() -> None:
    golden, context = _open_frequency_context()
    result = scorer.get_assert(
        json.dumps({"scenes": golden["scenes"][:1]}),
        context,
    )

    assert result["pass"] is False
    assert "Required scene headings/boundaries differ" in result["reason"]


@pytest.mark.unit
def test_scene_extraction_requires_expected_cast_in_every_scene() -> None:
    golden, context = _open_frequency_context()
    scenes = [{**scene, "characters": []} for scene in golden["scenes"]]
    result = scorer.get_assert(json.dumps({"scenes": scenes}), context)

    assert result["pass"] is False
    assert "missing or invented cast members" in result["reason"]


@pytest.mark.unit
def test_scene_extraction_rejects_fabricated_but_substantive_summaries() -> None:
    golden, context = _open_frequency_context()
    scenes = [
        {
            **scene,
            "summary": (
                "Invented dragons hold an elaborate coronation in a distant crystal palace "
                "while royal armies celebrate an unrelated victory."
            ),
        }
        for scene in golden["scenes"]
    ]
    result = scorer.get_assert(json.dumps({"scenes": scenes}), context)

    assert result["pass"] is False
    assert "Source-grounding failed for scene summaries" in result["reason"]


@pytest.mark.unit
def test_scene_extraction_rejects_open_frequency_summaries_that_deny_the_source() -> None:
    golden, context = _open_frequency_context()
    control = scorer.get_assert(json.dumps(golden), context)
    scenes = [
        {
            **scene,
            "summary": f"The screenplay says this never happens: {scene['summary']}",
        }
        for scene in golden["scenes"]
    ]

    result = scorer.get_assert(json.dumps({**golden, "scenes": scenes}), context)

    assert control["pass"] is True
    assert control["score"] == 1.0
    assert result["pass"] is False
    assert result["score"] < control["score"]
    assert "Source-grounding failed for scene summaries" in result["reason"]


@pytest.mark.unit
@pytest.mark.parametrize(
    "payload",
    [
        {"scenes": _scenes()},
        _payload(title="Wrong Title"),
        _payload(scene_count=999),
        _payload(extra="forbidden"),
    ],
)
def test_scene_extraction_rejects_invalid_top_level_contract(
    tmp_path: Path, payload: dict
) -> None:
    result = scorer.get_assert(json.dumps(payload), _context(tmp_path))

    assert result["pass"] is False
    assert "Schema errors:" in result["reason"]


@pytest.mark.unit
def test_scene_extraction_rejects_invented_extra_cast(tmp_path: Path) -> None:
    scenes = [
        {**scene, "characters": [*scene["characters"], "INVENTED DRAGON"]}
        for scene in _scenes()
    ]

    result = scorer.get_assert(json.dumps(_payload(scenes)), _context(tmp_path))

    assert result["pass"] is False
    assert "missing or invented cast members" in result["reason"]


@pytest.mark.unit
def test_scene_extraction_rejects_nonconsecutive_scene_numbers(tmp_path: Path) -> None:
    scenes = [dict(scene) for scene in _scenes()]
    scenes[1]["scene_number"] = 7

    result = scorer.get_assert(json.dumps(_payload(scenes)), _context(tmp_path))

    assert result["pass"] is False
    assert "scene_number:not-consecutive" in result["reason"]
