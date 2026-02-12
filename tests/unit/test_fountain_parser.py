from __future__ import annotations

import pytest

from cine_forge.ai.fountain_parser import validate_fountain_structure


@pytest.mark.unit
def test_validate_fountain_structure_fallback_detects_parseable_script() -> None:
    text = "INT. LAB - NIGHT\n\nMARA\nWe move now.\n"
    result = validate_fountain_structure(text)
    assert result.parseable is True
    assert result.element_count >= 2


@pytest.mark.unit
def test_validate_fountain_structure_reports_empty_script() -> None:
    result = validate_fountain_structure("   ")
    assert result.parseable is False
    assert "Script is empty" in result.issues
