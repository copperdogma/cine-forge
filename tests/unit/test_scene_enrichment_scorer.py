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

scorer = importlib.import_module("scene_enrichment_scorer")


def _context(tmp_path: Path) -> dict:
    golden = {
        "elevator": {
            "heading": "INT. ELEVATOR - CONTINUOUS",
            "location": "ELEVATOR",
            "time_of_day": "UNSPECIFIED",
            "int_ext": "INT",
            "characters_present": ["ALICE", "THUG 1", "THUG 2", "THUG 3"],
            "expected_tone": ["tense", "violent"],
            "expected_beat_types": ["conflict", "revelation"],
            "key_details": [
                "Alice fights three thugs",
                "Alice discovers a bloody scrap",
            ],
        }
    }
    path = tmp_path / "golden.json"
    path.write_text(json.dumps(golden))
    return {
        "vars": {
            "golden_path": str(path),
            "scene_key": "elevator",
            "scene_text": (
                "INT. ELEVATOR - CONTINUOUS\n\n"
                "Alice fights three thugs inside the elevator. After the fight, "
                "Alice discovers a bloody, hairy scrap on the floor."
            ),
        }
    }


def _control() -> dict:
    return {
        "heading": "INT. ELEVATOR - CONTINUOUS",
        "location": "ELEVATOR",
        "time_of_day": "UNSPECIFIED",
        "int_ext": "INT",
        "characters_present": ["ALICE", "THUG 1", "THUG 2", "THUG 3"],
        "narrative_beats": [
            {
                "beat_type": "conflict",
                "description": "Alice fights three thugs inside the elevator.",
                "confidence": 0.98,
            },
            {
                "beat_type": "revelation",
                "description": "Alice discovers a bloody, hairy scrap on the floor.",
                "confidence": 0.95,
            },
        ],
        "tone_mood": "tense",
        "tone_shifts": ["violent"],
    }


@pytest.mark.unit
def test_scene_enrichment_scorer_rewards_grounded_control(tmp_path: Path) -> None:
    result = scorer.get_assert(json.dumps(_control()), _context(tmp_path))

    assert result["pass"] is True
    assert result["score"] == 1.0


@pytest.mark.unit
def test_scene_enrichment_scorer_rejects_invented_time(tmp_path: Path) -> None:
    result = scorer.get_assert(
        json.dumps({**_control(), "time_of_day": "NIGHT"}),
        _context(tmp_path),
    )

    assert result["pass"] is False
    assert "time_accuracy=0.00" in result["reason"]


@pytest.mark.unit
def test_scene_enrichment_scorer_rejects_generic_group_for_numbered_thugs(
    tmp_path: Path,
) -> None:
    output = {**_control(), "characters_present": ["ALICE", "THUG"]}
    result = scorer.get_assert(json.dumps(output), _context(tmp_path))

    assert result["pass"] is False
    assert "character_accuracy=" in result["reason"]


@pytest.mark.unit
def test_scene_enrichment_scorer_rejects_wrong_heading(tmp_path: Path) -> None:
    result = scorer.get_assert(
        json.dumps({**_control(), "heading": "EXT. BEACH - DAY"}),
        _context(tmp_path),
    )

    assert result["pass"] is False
    assert "heading_accuracy=0.00" in result["reason"]


@pytest.mark.unit
def test_scene_enrichment_scorer_dominated_detail_scores_lower(tmp_path: Path) -> None:
    context = _context(tmp_path)
    complete = scorer.get_assert(json.dumps(_control()), context)
    output = _control()
    output["narrative_beats"] = [
        {"beat_type": "conflict", "description": "Alice is present.", "confidence": 0.9},
        {"beat_type": "revelation", "description": "A scrap appears.", "confidence": 0.9},
    ]
    dominated = scorer.get_assert(json.dumps(output), context)

    assert dominated["score"] < complete["score"]


@pytest.mark.unit
def test_scene_enrichment_rejects_invented_dragon_beats_and_romance_tone(
    tmp_path: Path,
) -> None:
    output = _control()
    output["narrative_beats"] = [
        {
            "beat_type": beat["beat_type"],
            "description": (
                "A cheerful dragon celebrates a romantic coronation in a crystal palace."
            ),
            "confidence": beat["confidence"],
        }
        for beat in output["narrative_beats"]
    ]
    output["tone_mood"] = "cheerful romance"
    output["tone_shifts"] = []

    result = scorer.get_assert(json.dumps(output), _context(tmp_path))

    assert result["pass"] is False
    assert "beat_detail_grounding=0.00" in result["reason"]
    assert "tone_accuracy=0.00" in result["reason"]


@pytest.mark.unit
def test_scene_enrichment_hard_gates_wrong_metadata_and_extra_cast(tmp_path: Path) -> None:
    output = {
        **_control(),
        "location": "MOON PALACE",
        "int_ext": "EXT",
        "characters_present": [
            "ALICE",
            "THUG 1",
            "THUG 2",
            "THUG 3",
            "INVENTED DRAGON",
        ],
    }

    result = scorer.get_assert(json.dumps(output), _context(tmp_path))

    assert result["pass"] is False
    assert "location_accuracy=" in result["reason"]


@pytest.mark.unit
@pytest.mark.parametrize(
    "mutation",
    [
        {"extra": "forbidden"},
        {"tone_shifts": "violent"},
        {
            "narrative_beats": [
                {"beat_type": "conflict", "description": "Alice fights three thugs."}
            ]
        },
        {
            "narrative_beats": [
                {
                    "beat_type": "conflict",
                    "description": "Alice fights three thugs.",
                    "confidence": 1.5,
                }
            ]
        },
    ],
)
def test_scene_enrichment_rejects_invalid_exact_schema(
    tmp_path: Path, mutation: dict
) -> None:
    result = scorer.get_assert(json.dumps({**_control(), **mutation}), _context(tmp_path))

    assert result["pass"] is False
    assert "schema_errors=" in result["reason"]
