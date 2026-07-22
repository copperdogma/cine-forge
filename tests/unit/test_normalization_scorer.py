from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest

from tests.unit.open_frequency_eval_test_support import NORMALIZED_OPEN_FREQUENCY

REPO_ROOT = Path(__file__).resolve().parents[2]
SCORER_ROOT = REPO_ROOT / "benchmarks" / "scorers"
if str(SCORER_ROOT) not in sys.path:
    sys.path.insert(0, str(SCORER_ROOT))

scorer = importlib.import_module("normalization_scorer")
OPEN_FREQUENCY_GOLDEN = REPO_ROOT / "benchmarks" / "golden" / (
    "normalize-open-frequency-corrupted-golden.json"
)
OPEN_FREQUENCY_SOURCE = REPO_ROOT / "benchmarks" / "input" / (
    "normalize-open-frequency-corrupted.fountain"
)
SIGNAL_GOLDEN = REPO_ROOT / "benchmarks" / "golden" / "normalize-signal-golden.json"
BROKEN_FOUNTAIN_SOURCE = REPO_ROOT / "benchmarks" / "input" / (
    "normalize-broken-fountain.txt"
)

FOUNTAIN = """INT. LAB - DAY

ALICE
I know the code.

BOB
Open the vault.
"""

ACTION = (
    "A silver generator hums beneath amber warning lights while rain rattles the "
    "laboratory windows and old copper relays click in sequence."
)
CONTRACT_SOURCE = f"""Title: Signal in the Rain

int. lab - day

{ACTION}

alice
(quietly)
I know the code.

bob
Open the vault.
"""
CONTRACT_FOUNTAIN = f"""TITLE: SIGNAL IN THE RAIN

INT. LAB - DAY

{ACTION}

ALICE
(quietly)
I know the code.

BOB
Open the vault.
"""


def _context(tmp_path: Path, source_text: str = "") -> dict:
    golden = {
        "expected_scenes": ["INT. LAB - DAY"],
        "expected_characters": ["ALICE", "BOB"],
        "required_dialogue": [
            {"character": "ALICE", "fragment": "I know the code"},
            {"character": "BOB", "fragment": "Open the vault"},
        ],
        "forbidden_patterns": [r"```"],
        "structural_rules": {
            "scene_headings_uppercase": True,
            "character_cues_uppercase": True,
            "parentheticals_in_parens": True,
            "no_markdown_formatting": True,
            "blank_line_before_character_cue": True,
        },
    }
    path = tmp_path / "golden.json"
    path.write_text(json.dumps(golden))
    return {"vars": {"golden_path": str(path), "source_text": source_text}}


@pytest.mark.unit
def test_normalization_scorer_rewards_grounded_fountain(tmp_path: Path) -> None:
    result = scorer.get_assert(FOUNTAIN, _context(tmp_path))

    assert result["pass"] is True
    assert result["score"] == 1.0


@pytest.mark.unit
def test_normalization_scorer_rejects_markdown_fences(tmp_path: Path) -> None:
    result = scorer.get_assert(f"```fountain\n{FOUNTAIN}```", _context(tmp_path))

    assert result["pass"] is False
    assert "Markdown violations" in result["reason"]


@pytest.mark.unit
def test_normalization_scorer_rejects_misattributed_dialogue(tmp_path: Path) -> None:
    misattributed = """INT. LAB - DAY

ALICE
Open the vault.

BOB
I know the code.
"""
    result = scorer.get_assert(misattributed, _context(tmp_path))

    assert result["pass"] is False
    assert "wrong character" in result["reason"]


@pytest.mark.unit
def test_normalization_scorer_dominated_mutation_scores_lower(tmp_path: Path) -> None:
    context = _context(tmp_path)
    complete = scorer.get_assert(FOUNTAIN, context)
    missing_dialogue = scorer.get_assert(FOUNTAIN.replace("Open the vault.", ""), context)

    assert missing_dialogue["score"] < complete["score"]


@pytest.mark.unit
def test_normalization_scorer_requires_each_exact_scene_heading(tmp_path: Path) -> None:
    wrong_heading = FOUNTAIN.replace("INT. LAB - DAY", "INT. LAB - CONTINUOUS")
    result = scorer.get_assert(wrong_heading, _context(tmp_path))

    assert result["pass"] is False
    assert "scene_headings=0.40" in result["reason"]


@pytest.mark.unit
def test_normalization_scorer_rejects_source_action_omission(tmp_path: Path) -> None:
    source = FOUNTAIN.replace(
        "\nALICE\n",
        "\nThe generator hums beneath amber warning lights.\n\nALICE\n",
    )
    result = scorer.get_assert(FOUNTAIN, _context(tmp_path, source))

    assert result["pass"] is False
    assert "source_recall=" in result["reason"]


@pytest.mark.unit
def test_normalization_scorer_rejects_invented_content(tmp_path: Path) -> None:
    invented = FOUNTAIN + "\nCrimson dragons devour the silver moon palace.\n"
    result = scorer.get_assert(invented, _context(tmp_path, FOUNTAIN))

    assert result["pass"] is False
    assert "novel_tokens=" in result["reason"]


@pytest.mark.unit
def test_normalization_scorer_accepts_vo_character_cue_structure() -> None:
    lines = ["", "NOAH (V.O.)", "A voice arrives."]

    assert scorer._structure_score(lines, [1]) == 1.0


@pytest.mark.unit
def test_normalization_scorer_perfect_source_contract_scores_one(tmp_path: Path) -> None:
    result = scorer.get_assert(CONTRACT_FOUNTAIN, _context(tmp_path, CONTRACT_SOURCE))

    assert result["pass"] is True
    assert result["score"] == 1.0


@pytest.mark.unit
@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        (
            lambda value: value.replace("TITLE: SIGNAL IN THE RAIN\n\n", ""),
            "title metadata",
        ),
        (lambda value: value.replace("(quietly)\n", ""), "source parentheticals"),
        (
            lambda value: value.replace("I know the code.", "I know the code!"),
            "source dialogue wording/attribution/punctuation",
        ),
        (
            lambda value: value + "\nEXT. MOON - NIGHT\n",
            "Scene heading set differs from the golden contract",
        ),
    ],
)
def test_normalization_scorer_rejects_source_contract_mutations(
    tmp_path: Path,
    mutation,
    reason: str,
) -> None:
    context = _context(tmp_path, CONTRACT_SOURCE)
    perfect = scorer.get_assert(CONTRACT_FOUNTAIN, context)
    mutated = scorer.get_assert(mutation(CONTRACT_FOUNTAIN), context)

    assert mutated["pass"] is False
    assert mutated["score"] < perfect["score"]
    assert reason in mutated["reason"]


@pytest.mark.unit
@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        (
            lambda value: value.replace("INT. LAB - DAY", "int. lab - day"),
            "scene_headings_uppercase rule violated",
        ),
        (
            lambda value: value.replace("\nALICE\n", "\nalice\n"),
            "character_cues_uppercase rule violated",
        ),
        (
            lambda value: value.replace("(quietly)", "(quietly"),
            "parentheticals_in_parens rule violated",
        ),
        (
            lambda value: value.replace("\n\nALICE\n", "\nALICE\n"),
            "blank_line_before_character_cue rule violated",
        ),
    ],
)
def test_normalization_scorer_enforces_each_named_structural_rule(
    tmp_path: Path,
    mutation,
    reason: str,
) -> None:
    result = scorer.get_assert(
        mutation(CONTRACT_FOUNTAIN),
        _context(tmp_path, CONTRACT_SOURCE),
    )

    assert result["pass"] is False
    assert reason in result["reason"]


def _open_frequency_context() -> dict:
    return {
        "vars": {
            "golden_path": str(OPEN_FREQUENCY_GOLDEN),
            "source_text": OPEN_FREQUENCY_SOURCE.read_text(),
        }
    }


def _mechanically_clean_broken_fountain(source: str) -> str:
    headings = {
        "int. community radio studio": "INT. COMMUNITY RADIO STUDIO",
        "ext. hilltop water tower \\- night": "EXT. HILLTOP WATER TOWER - NIGHT",
        "int. studio hallway \\- night": "INT. STUDIO HALLWAY - NIGHT",
        "int. community radio studio \\- continuous": (
            "INT. COMMUNITY RADIO STUDIO - CONTINUOUS"
        ),
    }
    cleaned: list[str] = []
    for source_line in source.splitlines():
        line = headings.get(source_line, source_line)
        if line == "## CUT TO:":
            line = "CUT TO:"
        if line.startswith("> "):
            line = line[2:]
        line = line.replace("\\-", "-").replace("\\!", "!")
        if line.split(" (", 1)[0] in {"aria", "noah", "june", "kell"}:
            line = line.upper()
        cleaned.append(line)
    return "\n".join(cleaned) + "\n"


@pytest.mark.unit
def test_normalization_rejects_missing_escaped_source_transition() -> None:
    mutation = NORMALIZED_OPEN_FREQUENCY.replace("CUT TO:\n\n", "", 1)
    result = scorer.get_assert(mutation, _open_frequency_context())

    assert result["pass"] is False
    assert "source transitions" in result["reason"]


@pytest.mark.unit
def test_normalization_rejects_missing_final_source_action() -> None:
    mutation = NORMALIZED_OPEN_FREQUENCY.replace(
        "Aria smiles for the first time all night and tightens the last bolt.\n",
        "",
    )
    result = scorer.get_assert(mutation, _open_frequency_context())

    assert result["pass"] is False
    assert "source action wording/order" in result["reason"]


@pytest.mark.unit
def test_normalization_rejects_contradictory_action_rewrite() -> None:
    mutation = NORMALIZED_OPEN_FREQUENCY.replace(
        "The town below is mostly dark",
        "The town below is fully lit",
    )
    result = scorer.get_assert(mutation, _open_frequency_context())

    assert result["pass"] is False
    assert "source action wording/order" in result["reason"]


@pytest.mark.unit
def test_normalization_rejects_reordered_source_action_paragraphs() -> None:
    first = "Aria threads a tape reel while Noah coaxes a signal out of a battered mixer."
    second = "June covers a whiteboard with road closures, shelter names, and call signs."
    mutation = NORMALIZED_OPEN_FREQUENCY.replace(
        f"{first}\n{second}",
        f"{second}\n{first}",
    )
    result = scorer.get_assert(mutation, _open_frequency_context())

    assert result["pass"] is False
    assert "source action wording/order" in result["reason"]


@pytest.mark.unit
def test_normalization_rejects_swapped_broken_fountain_opening_actions() -> None:
    source = BROKEN_FOUNTAIN_SOURCE.read_text()
    control = _mechanically_clean_broken_fountain(source)
    first = (
        "A cramped studio hums with old gear. Rain taps the skylight in steady rhythm."
    )
    second = (
        "aria threads a tape reel while noah checks a cracked mixer. "
        "june balances two mugs of tea on a stack of scripts."
    )
    mutation = control.replace(f"{first}\n{second}", f"{second}\n{first}")
    context = {
        "vars": {
            "golden_path": str(SIGNAL_GOLDEN),
            "source_text": source,
        }
    }

    control_result = scorer.get_assert(control, context)
    result = scorer.get_assert(mutation, context)

    assert mutation != control
    assert control_result["pass"] is True
    assert result["pass"] is False
    assert "source action wording/order" in result["reason"]
