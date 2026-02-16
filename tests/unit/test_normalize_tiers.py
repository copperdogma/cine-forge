"""Tests for 3-tier normalize routing."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from cine_forge.modules.ingest.script_normalize_v1.main import run_module

VALID_FOUNTAIN = (
    "INT. KITCHEN - MORNING\n\n"
    "SARAH\n"
    "Good morning.\n\n"
    "MIKE\n"
    "Coffee?\n\n"
    "EXT. GARDEN - DAY\n\n"
    "SARAH\n"
    "Beautiful day.\n"
)

PROSE_INPUT = (
    "Once upon a time there was a dog who wanted to go to the moon. "
    "He trained very hard and eventually built a rocket ship. "
    "The end."
)


def _make_raw_input(content: str, detected_format: str = "screenplay", confidence: float = 0.95):
    return {
        "content": content,
        "classification": {
            "detected_format": detected_format,
            "confidence": confidence,
        },
        "source_info": {
            "original_filename": "test_script.fountain",
        },
    }


@pytest.mark.unit
def test_tier1_valid_fountain_zero_llm_calls() -> None:
    """Valid Fountain input should complete with zero LLM calls."""
    inputs = {"raw_input": _make_raw_input(VALID_FOUNTAIN)}
    params: dict = {}
    context: dict = {}

    with patch("cine_forge.modules.ingest.script_normalize_v1.main.call_llm") as mock_llm:
        result = run_module(inputs, params, context)

    mock_llm.assert_not_called()
    assert len(result["artifacts"]) == 1
    artifact = result["artifacts"][0]
    assert artifact["metadata"]["health"] == "valid"
    assert artifact["metadata"]["source"] == "code"
    assert artifact["metadata"]["annotations"]["normalization_tier"] == 1
    assert result["cost"]["estimated_cost_usd"] == 0.0


@pytest.mark.unit
def test_tier1_passthrough_preserves_content() -> None:
    """Tier 1 should produce script_text that's essentially the same content."""
    inputs = {"raw_input": _make_raw_input(VALID_FOUNTAIN)}
    result = run_module(inputs, {}, {})
    script_text = result["artifacts"][0]["data"]["script_text"]
    # Key content should survive
    assert "INT. KITCHEN - MORNING" in script_text
    assert "SARAH" in script_text
    assert "Good morning." in script_text
    assert "MIKE" in script_text


@pytest.mark.unit
def test_tier1_hardcodes_metadata() -> None:
    """Tier 1 metadata should be hardcoded, not LLM-generated."""
    inputs = {"raw_input": _make_raw_input(VALID_FOUNTAIN)}
    result = run_module(inputs, {}, {})
    meta = result["artifacts"][0]["data"]["normalization"]
    assert meta["strategy"] == "code_passthrough"
    assert meta["overall_confidence"] == 0.95
    assert meta["inventions"] == []
    assert meta["assumptions"] == []


@pytest.mark.unit
def test_tier3_rejects_prose_input() -> None:
    """Non-screenplay input should be rejected with INVALID health."""
    inputs = {"raw_input": _make_raw_input(PROSE_INPUT, detected_format="prose", confidence=0.9)}
    result = run_module(inputs, {}, {})
    artifact = result["artifacts"][0]
    assert artifact["metadata"]["health"] == "needs_revision"
    assert artifact["metadata"]["annotations"]["normalization_tier"] == 3
    assert artifact["data"]["script_text"] == ""


@pytest.mark.unit
def test_tier2_falls_through_from_tier1_on_lint_failure() -> None:
    """If Tier 1 lint fails, should fall through to Tier 2."""
    # Screenplay with an orphaned character cue — will fail lint
    broken = (
        "INT. ROOM - DAY\n\n"
        "ALICE\n"
        "Hello.\n\n"
        "CHARLIE\n\n"  # orphaned — no dialogue follows, just blank line
        "EXT. STREET - NIGHT\n\n"
        "BOB\n"
        "Hi.\n"
    )
    inputs = {"raw_input": _make_raw_input(broken)}
    params = {"work_model": "mock", "qa_model": "mock"}

    result = run_module(inputs, params, {})
    tier = result["artifacts"][0]["metadata"]["annotations"]["normalization_tier"]
    assert tier == 2, f"Expected Tier 2 fallthrough, got Tier {tier}"


@pytest.mark.unit
def test_tier2_smart_chunks_only_fixes_broken_scenes() -> None:
    """Smart chunk-skip should only send failing scenes to LLM."""
    # Build a screenplay with multiple scenes, one broken
    good_scene1 = "INT. KITCHEN - DAY\n\nALICE\nHello.\n"
    good_scene2 = "EXT. GARDEN - DAY\n\nBOB\nHi.\n"
    # Scene with orphaned cue — will fail lint
    bad_scene = "INT. OFFICE - NIGHT\n\nCHARLIE\n\nDAVE\nYo.\n"
    content = f"{good_scene1}\n{good_scene2}\n{bad_scene}"

    inputs = {"raw_input": _make_raw_input(content)}
    params = {"work_model": "mock"}

    with patch("cine_forge.modules.ingest.script_normalize_v1.main.call_llm") as mock_llm:
        # Mock returns a fixed version of the scene
        mock_llm.return_value = (
            "INT. OFFICE - NIGHT\n\nCHARLIE\nHey there.\n\nDAVE\nYo.\n",
            {"model": "mock", "input_tokens": 0, "output_tokens": 0, "estimated_cost_usd": 0.0},
        )
        result = run_module(inputs, params, {})

    # Should have called LLM only for the broken scene(s), not all scenes
    assert mock_llm.call_count <= 2  # at most the broken scene(s)
    tier = result["artifacts"][0]["metadata"]["annotations"]["normalization_tier"]
    assert tier == 2
