from __future__ import annotations

import pytest

from cine_forge.ai.fountain_validate import lint_fountain_text, normalize_fountain_text


@pytest.mark.unit
def test_normalize_fountain_text_enforces_scene_and_cue_casing() -> None:
    source = "int. kitchen - night\nmara\nhello.\n"
    normalized = normalize_fountain_text(source)
    assert "INT. KITCHEN - NIGHT" in normalized
    assert "MARA" in normalized


@pytest.mark.unit
def test_lint_fountain_text_detects_orphaned_character_cue() -> None:
    text = "INT. LAB - DAY\n\nMARA\n\nEXT. STREET - DAY\n"
    lint = lint_fountain_text(text)
    assert lint.valid is False
    assert any("Character cue without dialogue" in issue for issue in lint.issues)
