"""Tests for fountain_validate lint false positive fixes."""

from __future__ import annotations

import pytest

from cine_forge.ai.fountain_validate import lint_fountain_text, normalize_fountain_text


@pytest.mark.unit
def test_parenthetical_not_flagged_as_orphan() -> None:
    """Parentheticals like (V.O.) or (beat) should not trigger orphan cue warnings."""
    text = (
        "INT. ROOM - DAY\n\n"
        "ALICE\n"
        "(whispering)\n"
        "Hello there.\n\n"
        "BOB (V.O.)\n"
        "Hi back.\n"
    )
    lint = lint_fountain_text(text)
    orphan_issues = [i for i in lint.issues if "Character cue without dialogue" in i]
    assert orphan_issues == [], f"False positive orphan cues: {orphan_issues}"


@pytest.mark.unit
def test_title_page_not_flagged_as_transition() -> None:
    """Title/Author lines should not be flagged as malformed transitions."""
    text = (
        "Title: My Screenplay\n"
        "Author: Jane Doe\n"
        "Draft date: 2026-01-15\n\n"
        "INT. ROOM - DAY\n\n"
        "ALICE\n"
        "Hello.\n"
    )
    lint = lint_fountain_text(text)
    transition_issues = [i for i in lint.issues if "Malformed transition" in i]
    assert transition_issues == [], f"False positive transitions: {transition_issues}"


@pytest.mark.unit
def test_real_malformed_transition_still_flagged() -> None:
    """All-caps non-standard transitions should still be caught."""
    text = (
        "INT. ROOM - DAY\n\n"
        "ALICE\n"
        "Hello.\n\n"
        "WIPE ACROSS:\n\n"
        "EXT. STREET - NIGHT\n\n"
        "BOB\n"
        "Hi.\n"
    )
    lint = lint_fountain_text(text)
    assert any("Malformed transition" in i for i in lint.issues)


@pytest.mark.unit
def test_valid_transition_not_flagged() -> None:
    """Standard transitions like CUT TO: and FADE TO: should be fine."""
    text = (
        "INT. ROOM - DAY\n\n"
        "ALICE\n"
        "Hello.\n\n"
        "CUT TO:\n\n"
        "EXT. STREET - NIGHT\n\n"
        "BOB\n"
        "Hi.\n"
    )
    lint = lint_fountain_text(text)
    transition_issues = [i for i in lint.issues if "Malformed transition" in i]
    assert transition_issues == []


@pytest.mark.unit
def test_normalize_preserves_parentheticals() -> None:
    """Parentheticals should not be uppercased by normalize."""
    text = (
        "INT. ROOM - DAY\n\n"
        "ALICE\n"
        "(softly)\n"
        "Hello.\n"
    )
    normalized = normalize_fountain_text(text)
    assert "(softly)" in normalized


@pytest.mark.unit
def test_opening_title_not_flagged_as_character_cue() -> None:
    """OPENING TITLE should not trigger character cue without dialogue."""
    text = (
        "INT. ROOM - DAY\n\n"
        "OPENING TITLE\n\n"
        "In 2020 the pandemic swept the globe.\n\n"
        "ALICE\n"
        "Hello.\n"
    )
    lint = lint_fountain_text(text)
    cue_issues = [i for i in lint.issues if "Character cue" in i or "Orphaned" in i]
    assert cue_issues == [], f"False positive character cues: {cue_issues}"


@pytest.mark.unit
def test_begin_end_flashback_not_flagged() -> None:
    """BEGIN FLASHBACK: and END FLASHBACK. should not trigger lint issues."""
    text = (
        "INT. ROOM - DAY\n\n"
        "ALICE\n"
        "Look at this.\n\n"
        "BEGIN FLASHBACK:\n\n"
        "EXT. BEACH - DAY\n\n"
        "BOB\n"
        "Remember?\n\n"
        "END FLASHBACK.\n\n"
        "INT. ROOM - DAY\n\n"
        "ALICE\n"
        "Wow.\n"
    )
    lint = lint_fountain_text(text)
    issues = [i for i in lint.issues if "Malformed" in i or "Character cue" in i]
    assert issues == [], f"False positive issues: {issues}"


@pytest.mark.unit
def test_cut_to_black_period_not_flagged() -> None:
    """CUT TO BLACK. (with period) should not be flagged."""
    text = (
        "INT. ROOM - DAY\n\n"
        "ALICE\n"
        "Goodbye.\n\n"
        "CUT TO BLACK.\n"
    )
    lint = lint_fountain_text(text)
    issues = [i for i in lint.issues if "Orphaned" in i or "Character cue" in i]
    assert issues == [], f"False positive issues: {issues}"


@pytest.mark.unit
def test_clean_screenplay_passes_lint() -> None:
    """A well-formatted screenplay should pass lint with zero issues."""
    text = (
        "INT. KITCHEN - MORNING\n\n"
        "SARAH\n"
        "Good morning.\n\n"
        "MIKE\n"
        "Coffee?\n\n"
        "EXT. GARDEN - DAY\n\n"
        "SARAH\n"
        "Beautiful day.\n"
    )
    lint = lint_fountain_text(text)
    assert lint.valid is True, f"Unexpected issues: {lint.issues}"
