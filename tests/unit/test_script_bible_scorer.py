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

scorer = importlib.import_module("script_bible_scorer")
OPEN_FREQUENCY_GOLDEN = REPO_ROOT / "benchmarks" / "golden" / (
    "open-frequency-script-bible.json"
)
OPEN_FREQUENCY_SOURCE = REPO_ROOT / "tests" / "fixtures" / "ingest_inputs" / (
    "open_frequency_short.fountain"
)
QWEN38_RESULT = REPO_ROOT / "benchmarks" / "results" / (
    "script-bible-qwen38-openrouter-open-frequency-2026-08-03.json"
)

REQUIRED_FIELDS = [
    "title",
    "logline",
    "synopsis",
    "act_structure",
    "themes",
    "narrative_arc",
    "genre",
    "tone",
    "protagonist_journey",
    "central_conflict",
    "setting_overview",
    "confidence",
]


def _context(tmp_path: Path) -> dict:
    golden = {
        "must_include_title": "Test Film",
        "act_count_min": 2,
        "act_count_max": 4,
        "required_fields": REQUIRED_FIELDS,
        "genre_keywords": ["action", "thriller"],
        "tone_keywords": ["dark comedy", "gritty"],
        "logline_keywords": ["gang", "tower", "rescue"],
        "protagonist_keywords": ["alice"],
        "must_include_conflict_keywords": ["gang", "stolen key", "father truth"],
        "setting_keywords": ["ruined city", "tower", "roof"],
        "protagonist_journey_keywords": ["truth", "hero", "identity"],
        "must_include_themes": [
            {"description": "Truth", "keywords": ["truth", "lies"]},
            {"description": "Family", "keywords": ["family", "sibling"]},
        ],
        "synopsis_min_length": 200,
        "logline_max_length": 300,
    }
    path = tmp_path / "golden.json"
    path.write_text(json.dumps(golden))
    return {"vars": {"golden_path": str(path)}}


def _act(number: int, title: str) -> dict:
    return {
        "act_number": number,
        "title": title,
        "start_scene": f"Scene {number}A",
        "end_scene": f"Scene {number}B",
        "summary": f"Alice advances through the gang conflict in act {number}.",
        "turning_points": [f"Turning point {number}"],
    }


def _theme(name: str, keyword: str) -> dict:
    return {
        "theme": name,
        "description": f"The screenplay explores {keyword} through Alice's choices.",
        "evidence": [f"Scene evidence for {keyword} one", f"Scene evidence for {keyword} two"],
    }


def _control() -> dict:
    synopsis = (
        "Alice crosses a ruined city and enters the tower to rescue her sibling from a gang. "
        "The gang wants a stolen key, while Alice confronts the father truth that shaped her "
        "identity. On the roof she chooses to become a hero grounded in truth rather than lies. "
        "Her family survives the tower confrontation, but the cost changes how she sees herself."
    )
    return {
        "title": "Test Film",
        "logline": "Alice must rescue her sibling from a gang controlling a ruined tower.",
        "synopsis": synopsis,
        "act_structure": [_act(1, "Setup"), _act(2, "Confrontation")],
        "themes": [_theme("Truth", "truth"), _theme("Family", "family")],
        "narrative_arc": (
            "Alice moves from comforting lies toward the father truth and hero identity."
        ),
        "genre": "Action thriller",
        "tone": "Gritty dark comedy",
        "protagonist_journey": "Alice accepts the truth and defines her own hero identity.",
        "central_conflict": "Alice battles the gang over the stolen key and father truth.",
        "setting_overview": "A ruined city, its tower, and the final roof confrontation.",
        "confidence": 0.9,
    }


@pytest.mark.unit
def test_script_bible_scorer_rewards_grounded_control(tmp_path: Path) -> None:
    result = scorer.get_assert(json.dumps(_control()), _context(tmp_path))

    assert result["pass"] is True
    assert result["score"] == 1.0


@pytest.mark.unit
def test_script_bible_scorer_rejects_hollow_keyword_payload(tmp_path: Path) -> None:
    hollow = {
        **_control(),
        "title": "Test Film Extended",
        "act_structure": [_act(1, "Setup"), {"act_number": 2, "summary": "thin"}],
        "themes": ["truth", "family"],
        "genre": "Pure comedy",
        "tone": "Cheerful",
        "synopsis": "padding " * 40,
        "confidence": 7,
    }
    result = scorer.get_assert(json.dumps(hollow), _context(tmp_path))

    assert result["pass"] is False
    assert result["score"] < 0.7


@pytest.mark.unit
def test_script_bible_scorer_rejects_unsupported_genre_and_tone(tmp_path: Path) -> None:
    output = {**_control(), "genre": "Pure comedy", "tone": "Cheerful"}
    result = scorer.get_assert(json.dumps(output), _context(tmp_path))

    assert result["pass"] is False
    assert "genre_tone_grounding=0.00" in result["reason"]


@pytest.mark.unit
def test_script_bible_scorer_rejects_out_of_range_confidence(tmp_path: Path) -> None:
    result = scorer.get_assert(
        json.dumps({**_control(), "confidence": 7}),
        _context(tmp_path),
    )

    assert result["pass"] is False
    assert "confidence_quality=0.00" in result["reason"]


@pytest.mark.unit
def test_script_bible_scorer_dominated_mutation_scores_lower(tmp_path: Path) -> None:
    context = _context(tmp_path)
    complete = scorer.get_assert(json.dumps(_control()), context)
    output = _control()
    output["themes"][1]["evidence"] = []
    dominated = scorer.get_assert(json.dumps(output), context)

    assert dominated["score"] < complete["score"]


def _open_act(number: int, start: str, end: str) -> dict:
    return {
        "act_number": number,
        "title": f"Act {number}",
        "start_scene": start,
        "end_scene": end,
        "summary": f"The radio team advances the Red Creek broadcast in act {number}.",
        "turning_points": [f"The team reaches turning point {number}."],
    }


def _open_frequency_control() -> dict:
    headings = json.loads(OPEN_FREQUENCY_GOLDEN.read_text())["source_headings"]
    return {
        "title": "Open Frequency",
        "logline": (
            "A community radio team battles a storm and failing signal to broadcast urgent "
            "shelter information across Red Creek."
        ),
        "synopsis": (
            "During a storm in Red Creek, Aria, Noah, June, and Kell struggle to restore the "
            "community radio signal from a studio running on emergency power. Aria and Noah "
            "carry the portable antenna to the water tower, where they hear that the north "
            "shelter needs insulin and dry blankets and reconnect with June. At the high "
            "school gym shelter, Maya asks them to broadcast a plea for her missing dog, "
            "Comet. By morning Comet is found, the ON AIR sign is steady, and the radio team "
            "returns to work."
        ),
        "act_structure": [
            _open_act(1, headings[0], headings[0]),
            _open_act(2, headings[1], headings[2]),
            _open_act(3, headings[3], headings[3]),
        ],
        "themes": [
            {
                "theme": "Community service",
                "description": "The broadcasters turn local information into mutual aid.",
                "evidence": ["north shelter needs insulin", "East road is open one lane"],
            },
            {
                "theme": "Communication and connection",
                "description": "A fragile radio signal reconnects isolated people.",
                "evidence": ["if anyone hears this", "Loud enough to make me useful"],
            },
            {
                "theme": "Resilience and hope",
                "description": "The team keeps working through the storm until morning.",
                "evidence": ["one miracle", "ON AIR sign steadies"],
            },
        ],
        "narrative_arc": (
            "A powerless radio studio becomes a working community lifeline; Maya's missing "
            "dog Comet is recovered and the morning broadcast returns the team to work."
        ),
        "genre": "Hopeful disaster drama",
        "tone": "Tense, resilient, warm, and wry",
        "protagonist_journey": (
            "The radio team turns a failing signal into a useful broadcast that reconnects "
            "the community, then settles back to work."
        ),
        "central_conflict": (
            "The team must overcome the storm, emergency power, and a failing signal so the "
            "broadcast can deliver insulin and shelter information."
        ),
        "setting_overview": (
            "Storm-struck Red Creek from night through morning: a community radio studio, "
            "water tower catwalk, and high school gym shelter."
        ),
        "confidence": 0.98,
    }


def _open_frequency_context() -> dict:
    return {
        "vars": {
            "golden_path": str(OPEN_FREQUENCY_GOLDEN),
            "screenplay": OPEN_FREQUENCY_SOURCE.read_text(),
        }
    }


@pytest.mark.unit
def test_script_bible_requires_full_source_ending_concepts() -> None:
    candidate = _open_frequency_control()
    first_half = (
        "During a storm in Red Creek, Aria, Noah, June, and Kell operate the community radio "
        "studio on emergency power. Aria and Noah carry the antenna to the water tower and "
        "restore a thin signal. They hear that the north shelter needs insulin and dry "
        "blankets, and June answers the broadcast. The radio team becomes useful to its "
        "community, but this account stops at the tower before the later shelter and morning "
        "scenes."
    )
    candidate.update(
        synopsis=first_half,
        narrative_arc=first_half,
        protagonist_journey="Aria restores the signal and connects with June.",
        central_conflict="The storm, power failure, and antenna threaten the broadcast.",
        setting_overview="Red Creek radio studio and water tower at night during a storm.",
        act_structure=[
            _open_act(
                1,
                "INT. COMMUNITY RADIO STUDIO - NIGHT",
                "INT. COMMUNITY RADIO STUDIO - NIGHT",
            ),
            _open_act(
                2,
                "EXT. WATER TOWER CATWALK - NIGHT",
                "EXT. WATER TOWER CATWALK - NIGHT",
            ),
        ],
    )
    result = scorer.get_assert(json.dumps(candidate), _open_frequency_context())

    assert result["pass"] is False
    assert "Required story events missing" in result["reason"]


@pytest.mark.unit
def test_script_bible_requires_exact_source_act_boundaries() -> None:
    candidate = _open_frequency_control()
    for index, act in enumerate(candidate["act_structure"], start=1):
        act["start_scene"] = f"Fabricated scene {index}A"
        act["end_scene"] = f"Fabricated scene {index}B"
    result = scorer.get_assert(json.dumps(candidate), _open_frequency_context())

    assert result["pass"] is False
    assert "exact source headings" in result["reason"]


@pytest.mark.unit
def test_script_bible_accepts_source_grounded_descriptive_act_boundaries() -> None:
    candidate = _open_frequency_control()
    headings = json.loads(OPEN_FREQUENCY_GOLDEN.read_text())["source_headings"]
    candidate["act_structure"] = [
        _open_act(
            1,
            headings[0],
            "The ON AIR sign flickers, then dies again. Aria asks for ten minutes and one miracle.",
        ),
        _open_act(
            2,
            headings[1],
            "Aria smiles for the first time all night and tightens the last bolt.",
        ),
        _open_act(
            3,
            headings[2],
            "The ON AIR sign steadies into a solid red glow as the four settle back to work.",
        ),
    ]

    result = scorer.get_assert(json.dumps(candidate), _open_frequency_context())

    assert result["pass"] is True
    assert "act_boundary_grounding=1.00" in result["reason"]


@pytest.mark.unit
def test_script_bible_requires_source_grounded_theme_evidence() -> None:
    candidate = _open_frequency_control()
    for index, theme in enumerate(candidate["themes"], start=1):
        theme["evidence"] = [
            f"A dragon receives a jeweled crown in invented kingdom {index}",
            f"Royal armies celebrate an unrelated victory in invented kingdom {index}",
        ]
    result = scorer.get_assert(json.dumps(candidate), _open_frequency_context())

    assert result["pass"] is False
    assert "Theme evidence is not grounded" in result["reason"]


@pytest.mark.unit
def test_script_bible_accepts_source_grounded_annotated_theme_evidence() -> None:
    candidate = _open_frequency_control()
    candidate["themes"][0]["evidence"] = [
        "'north shelter needs insulin and dry blankets' — the radio carries urgent aid requests",
        "June tapes 'OPEN FREQUENCY' over the door — the station becomes a public commons",
    ]
    candidate["themes"][1]["evidence"] = [
        "'It only tried to kill me once' — Kell makes do with the damaged antenna",
        (
            "Aria braces the lantern with her boot while Noah clamps the portable "
            "antenna — improvisation under pressure"
        ),
    ]
    candidate["themes"][2]["evidence"] = [
        "The ON AIR sign flickers, then dies again — the team initially loses its voice",
        "The ON AIR sign steadies into a solid red glow — the broadcast is restored",
    ]

    result = scorer.get_assert(json.dumps(candidate), _open_frequency_context())

    assert result["pass"] is True
    assert "theme_evidence_grounding=1.00" in result["reason"]


@pytest.mark.unit
def test_script_bible_does_not_treat_dead_cell_towers_as_kells_death() -> None:
    candidate = _open_frequency_control()
    candidate["act_structure"][0]["summary"] += (
        " Kell reports the bridge closed; cell towers are dead."
    )

    result = scorer.get_assert(json.dumps(candidate), _open_frequency_context())

    assert result["pass"] is True
    assert "unsupported_claims=1.00" in result["reason"]


@pytest.mark.unit
def test_script_bible_repaired_contract_regrades_frozen_qwen_output() -> None:
    retained = json.loads(QWEN38_RESULT.read_text())
    outputs = [
        row["response"]["output"]
        for row in retained["results"]["results"]
        if row.get("response", {}).get("output")
    ]

    assert len(outputs) == 1
    result = scorer.get_assert(outputs[0], _open_frequency_context())

    assert result["pass"] is True
    assert result["score"] == 0.9533
    assert "act_boundary_grounding=1.00" in result["reason"]
    assert "theme_evidence_grounding=1.00" in result["reason"]
    assert "unsupported_claims=1.00" in result["reason"]


@pytest.mark.unit
@pytest.mark.parametrize(
    "unsupported_claim",
    [
        "Maya dies after the broadcast.",
        "Kell is dead by morning.",
        "Kell was killed during the storm.",
        "Kell lay dead beside the transmitter.",
        "Maya was brutally killed during the storm.",
        "Aria had died before the morning bulletin.",
        "They found dead Noah at the water tower.",
        "Kell's death silences the room.",
        "The death of Kell ends the broadcast.",
        "Aria begins a romantic relationship with Noah.",
        "The storm is revealed to be a tornado.",
        "Red Creek completely recovered by sunrise.",
    ],
)
def test_script_bible_rejects_explicitly_unsupported_claim_classes(
    unsupported_claim: str,
) -> None:
    candidate = _open_frequency_control()
    candidate["narrative_arc"] += f" {unsupported_claim}"
    result = scorer.get_assert(json.dumps(candidate), _open_frequency_context())

    assert result["pass"] is False
    assert "Unsupported claim patterns matched" in result["reason"]
