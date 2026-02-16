"""Tests for fountain-tools parser integration and structural quality scoring."""

from __future__ import annotations

import pytest

from cine_forge.ai.fountain_parser import (
    FountainParseResult,
    compute_structural_quality,
    validate_fountain_structure,
)

VALID_SCREENPLAY = """\
INT. ROOM - DAY

ALICE
Hello there.

(beat)

BOB
Hi back.

EXT. STREET - NIGHT

ALICE
Let's go.
"""

MINIMAL_SCREENPLAY = """\
INT. ROOM - DAY

ALICE
Hello.
"""

GARBAGE_TEXT = """\
This is just some random text that has nothing to do with screenplays.
It doesn't have scene headings or character cues or dialogue.
Just paragraphs of prose about various topics.
"""


@pytest.mark.unit
def test_parser_uses_fountain_tools_backend() -> None:
    result = validate_fountain_structure(VALID_SCREENPLAY)
    assert result.parser_backend == "fountain-tools"


@pytest.mark.unit
def test_element_counts_populated() -> None:
    result = validate_fountain_structure(VALID_SCREENPLAY)
    assert result.scene_heading_count == 2
    assert result.character_count >= 2
    assert result.dialogue_count >= 2
    assert result.parseable is True


@pytest.mark.unit
def test_action_elements_counted() -> None:
    text = "INT. ROOM - DAY\n\nThe room is dark.\n\nALICE\nHello.\n"
    result = validate_fountain_structure(text)
    assert result.action_count >= 1


@pytest.mark.unit
def test_structural_quality_valid_screenplay() -> None:
    result = validate_fountain_structure(VALID_SCREENPLAY)
    score = compute_structural_quality(result)
    assert score >= 0.6


@pytest.mark.unit
def test_structural_quality_minimal_screenplay() -> None:
    result = validate_fountain_structure(MINIMAL_SCREENPLAY)
    score = compute_structural_quality(result)
    assert score >= 0.6


@pytest.mark.unit
def test_structural_quality_garbage_text() -> None:
    result = validate_fountain_structure(GARBAGE_TEXT)
    score = compute_structural_quality(result)
    assert score < 0.3


@pytest.mark.unit
def test_structural_quality_no_dialogue() -> None:
    text = "INT. ROOM - DAY\n\nSomething happens.\n\nEXT. STREET - NIGHT\n\nMore action.\n"
    result = validate_fountain_structure(text)
    score = compute_structural_quality(result)
    # Has scene headings (0.4) but no characters or dialogue (0.0)
    assert score < 0.6


@pytest.mark.unit
def test_empty_result_quality_is_zero() -> None:
    result = FountainParseResult(
        parseable=False,
        element_count=0,
        coverage=0.0,
        issues=[],
        parser_backend="none",
    )
    assert compute_structural_quality(result) == 0.0


@pytest.mark.unit
def test_coverage_is_reasonable() -> None:
    result = validate_fountain_structure(VALID_SCREENPLAY)
    assert 0.0 < result.coverage <= 1.0
