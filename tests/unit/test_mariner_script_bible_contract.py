from __future__ import annotations

import hashlib
import importlib
import json
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SCORER_ROOT = REPO_ROOT / "benchmarks" / "scorers"
if str(SCORER_ROOT) not in sys.path:
    sys.path.insert(0, str(SCORER_ROOT))

scorer = importlib.import_module("script_bible_scorer")
MARINER_GOLDEN = (
    REPO_ROOT / "benchmarks" / "golden" / "the-mariner-script-bible.json"
)
MARINER_SOURCE = REPO_ROOT / "benchmarks" / "input" / "the-mariner.md"
SCRIPT_BIBLE_TASK = REPO_ROOT / "benchmarks" / "tasks" / "script-bible.yaml"


def _act(number: int, start: str, end: str, summary: str) -> dict:
    return {
        "act_number": number,
        "title": f"Act {number}",
        "start_scene": start,
        "end_scene": end,
        "summary": summary,
        "turning_points": [summary],
    }


def _mariner_synopsis() -> str:
    return (
        "Mariner rescues Rose from the gang-held Ruddy & Greene building. He hid an "
        "AirTag in Rose's purse. The AirTag let him track her. Rose makes them return for "
        "the purse. The purse lining contains a memory stick carrying the blockchain "
        "password, tied to 20 million in gang money. In the elevator Mariner uses his "
        "oar against thugs. Mariner fires a flare gun at Vinnie on the 13th floor. Rose "
        "reveals that Dad is alive in Chimney Bay. The corrected memories expose Dad's "
        "abuse, and Rose says their deadbeat father abandoned Mariner. Salvatori holds "
        "Rose at gunpoint. The thugs take Mariner's oar and force him to his knees. "
        "Salvatori demands the memory stick, then the password from Rose. Rose calls "
        "Mariner a real hero and says he never backs down from a fight. Mariner smiles "
        "and clenches his hands into fists. The screenplay cuts to black, and the "
        "confrontation remains unresolved."
    )


def _mariner_control() -> dict:
    headings = json.loads(MARINER_GOLDEN.read_text())["source_headings"]
    return {
        "title": "The Mariner",
        "logline": (
            "Vigilante Mariner climbs a ruined building to save Rose from Salvatori's gang."
        ),
        "synopsis": _mariner_synopsis(),
        "act_structure": [
            _act(
                1,
                headings[0],
                headings[5],
                "Mariner reaches Rose, but her missing purse sends them back upward.",
            ),
            _act(
                2,
                headings[6],
                headings[9],
                "The siblings fight through the gang and recover the stolen-money key.",
            ),
            _act(
                3,
                headings[10],
                headings[14],
                "Father revelations destabilize Mariner during the final standoff.",
            ),
        ],
        "themes": [
            {
                "theme": "Sibling loyalty",
                "description": "Family loyalty drives the rescue despite dangerous conflict.",
                "evidence": [
                    "I stashed an AirTag in your purse",
                    "It’s all I got, Billy",
                ],
            },
            {
                "theme": "Father and legacy",
                "description": "Billy replaces an invented heroic legacy with painful truth.",
                "evidence": [
                    "he’s living up in Chimney Bay",
                    "kicked the crap out of him",
                ],
            },
            {
                "theme": "Hero identity",
                "description": "Rose defines heroism by present choices instead of mythology.",
                "evidence": [
                    "honesty and bravery and grit",
                    "never backs down from a fight",
                ],
            },
        ],
        "narrative_arc": (
            "A violent rescue becomes a reckoning with family mythology and chosen identity."
        ),
        "genre": "Action thriller with darkly comedic vigilante elements",
        "tone": "Gritty, emotional, intense, and darkly comedic",
        "protagonist_journey": (
            "Mariner faces the truth about his father and redefines his hero identity "
            "through loyalty to his sister."
        ),
        "central_conflict": (
            "Mariner protects his sister Rose from Salvatori and the gang over the crypto "
            "password while confronting the truth about his father."
        ),
        "setting_overview": (
            "A post-collapse ruined city centered on the Ruddy & Greene building and its "
            "15th floor."
        ),
        "confidence": 0.98,
    }


def _context() -> dict:
    return {
        "vars": {
            "golden_path": str(MARINER_GOLDEN),
            "screenplay": MARINER_SOURCE.read_text(),
        }
    }


def _canonical_hash(data: dict) -> str:
    payload = json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode()
    return hashlib.sha256(payload).hexdigest()


@pytest.mark.unit
def test_mariner_faithful_control_passes_every_contract_at_one() -> None:
    result = scorer.get_assert(json.dumps(_mariner_control()), _context())

    assert result["pass"] is True
    assert result["score"] == 1.0


@pytest.mark.unit
@pytest.mark.parametrize("schema_level", ["root", "act", "theme"])
def test_mariner_extra_schema_keys_fail_at_every_structured_level(
    schema_level: str,
) -> None:
    candidate = _mariner_control()
    if schema_level == "root":
        candidate["production_notes"] = []
    elif schema_level == "act":
        candidate["act_structure"][0]["confidence"] = 0.9
    else:
        candidate["themes"][0]["keywords"] = ["family"]

    result = scorer.get_assert(json.dumps(candidate), _context())

    assert result["pass"] is False


@pytest.mark.unit
def test_mariner_negated_event_dump_and_invented_triumph_fail() -> None:
    golden = json.loads(MARINER_GOLDEN.read_text())
    negated_claims = " ".join(
        f"It is false that {keyword}."
        for event in golden["required_story_events"]
        for keyword in event["keywords"]
    )
    candidate = _mariner_control()
    candidate["synopsis"] = negated_claims
    candidate["narrative_arc"] = "Mariner triumphs over Salvatori."

    result = scorer.get_assert(json.dumps(candidate), _context())

    assert result["pass"] is False
    assert "Required story events missing" in result["reason"]
    assert "Unsupported claim patterns matched" in result["reason"]


@pytest.mark.unit
@pytest.mark.parametrize(
    "negated_outcome",
    [
        "Mariner does not defeat Salvatori.",
        "Mariner won't win the final fight.",
        "Salvatori does not escape.",
    ],
)
def test_mariner_negated_forbidden_outcome_is_not_a_false_positive(
    negated_outcome: str,
) -> None:
    candidate = _mariner_control()
    candidate["narrative_arc"] += f" {negated_outcome}"

    result = scorer.get_assert(json.dumps(candidate), _context())

    assert result["pass"] is True
    assert result["score"] == 1.0


@pytest.mark.unit
@pytest.mark.parametrize(
    ("source_phrase", "replacement", "missing_event"),
    [
        (
            "Rose calls Mariner a real hero",
            "Rose praises Mariner",
            "Rose affirms that Mariner became a real hero",
        ),
        (
            "never backs down from a fight",
            "shows courage",
            "Rose says Mariner never backs down from a fight",
        ),
        (
            "Mariner smiles",
            "Mariner steadies himself",
            "Mariner smiles at Rose's affirmation",
        ),
        (
            "clenches his hands into fists",
            "sets his stance",
            "Mariner clenches his hands into fists",
        ),
        ("cuts to black", "ends", "The screenplay cuts to black"),
        (
            "confrontation remains unresolved",
            "story stops",
            "The final confrontation remains unresolved",
        ),
    ],
)
def test_mariner_incomplete_terminal_clause_fails(
    source_phrase: str,
    replacement: str,
    missing_event: str,
) -> None:
    candidate = _mariner_control()
    candidate["synopsis"] = candidate["synopsis"].replace(source_phrase, replacement)

    result = scorer.get_assert(json.dumps(candidate), _context())

    assert result["pass"] is False
    assert missing_event in result["reason"]


@pytest.mark.unit
@pytest.mark.parametrize(
    "invented_outcome",
    [
        "Rose kills Salvatori.",
        "Mariner captures Salvatori.",
        "Salvatori escapes.",
    ],
)
def test_mariner_plausible_invented_outcomes_fail(invented_outcome: str) -> None:
    candidate = _mariner_control()
    candidate["narrative_arc"] += f" {invented_outcome}"

    result = scorer.get_assert(json.dumps(candidate), _context())

    assert result["pass"] is False
    assert "Unsupported claim patterns matched" in result["reason"]


@pytest.mark.unit
@pytest.mark.parametrize(
    "truthful_denial",
    [
        "It is false that Rose kills Salvatori.",
        "It is not true that Mariner captures Salvatori.",
        "The screenplay never says that Salvatori escapes.",
    ],
)
def test_mariner_truthful_denials_do_not_trigger_unsupported_outcomes(
    truthful_denial: str,
) -> None:
    candidate = _mariner_control()
    candidate["narrative_arc"] += f" {truthful_denial}"

    result = scorer.get_assert(json.dumps(candidate), _context())

    assert result["pass"] is True, result["reason"]
    assert result["score"] == 1.0


@pytest.mark.unit
@pytest.mark.parametrize(
    "mixed_polarity_invention",
    [
        "Mariner does not hesitate, and Rose kills Salvatori.",
        "Rose does not surrender, but Mariner captures Salvatori.",
        "Mariner does not catch him, and Salvatori escapes.",
        "The screenplay does not show the fight, but Mariner defeats Salvatori.",
    ],
)
def test_mariner_prior_clause_negation_does_not_hide_invented_outcome(
    mixed_polarity_invention: str,
) -> None:
    candidate = _mariner_control()
    candidate["narrative_arc"] += f" {mixed_polarity_invention}"

    result = scorer.get_assert(json.dumps(candidate), _context())

    assert result["pass"] is False
    assert "Unsupported claim patterns matched" in result["reason"]


@pytest.mark.unit
def test_script_bible_task_pins_each_golden_and_terminal_contract() -> None:
    task = yaml.safe_load(SCRIPT_BIBLE_TASK.read_text())
    rubric = task["tests"][0]["assert"][1]["value"]
    assert "{{ending_contract}}" in rubric

    for case in task["tests"]:
        variables = case["vars"]
        golden_path = REPO_ROOT / "benchmarks" / variables["golden_path"]
        golden = json.loads(golden_path.read_text())
        assert variables["golden_sha256"] == _canonical_hash(golden)
        assert variables["ending_contract"].strip()
