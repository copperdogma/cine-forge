from __future__ import annotations

import pytest

from tests.round_trip.fidelity_contract import (
    assert_complete_token_retention,
    assert_dialogue_anchors,
    assert_heading_fidelity,
    assert_only_allowed_extra_tokens,
    assert_ordered_token_retention,
    assert_source_contract,
    fixture_paths,
    load_contract,
)

pytestmark = pytest.mark.round_trip


@pytest.mark.parametrize(
    "script_folder", ["big-fish", "brick-and-steel", "the-last-birthday-card"]
)
def test_reviewed_contract_matches_human_authored_source(script_folder: str) -> None:
    fountain_file, _fdx_file, _pdf_file = fixture_paths(script_folder)
    source = fountain_file.read_text(encoding="utf-8")
    assert_source_contract(source, load_contract(script_folder))


def test_heading_contract_rejects_reordering_and_deletion() -> None:
    contract = {
        "scene_count": 3,
        "ordered_scene_anchors": ["INT. A - DAY", "EXT. C - NIGHT"],
    }
    source = "INT. A - DAY\n\nEXT. B - DAY\n\nEXT. C - NIGHT"

    with pytest.raises(AssertionError):
        assert_heading_fidelity(
            source,
            "EXT. B - DAY\n\nINT. A - DAY\n\nEXT. C - NIGHT",
            contract,
        )
    with pytest.raises(AssertionError):
        assert_heading_fidelity(source, "INT. A - DAY\n\nEXT. C - NIGHT", contract)


def test_token_contract_rejects_deletion_and_excess_invention() -> None:
    source = "ALPHA BRAVO CHARLIE DELTA"

    with pytest.raises(AssertionError, match="lost source tokens"):
        assert_complete_token_retention(source, "ALPHA BRAVO DELTA")
    with pytest.raises(AssertionError, match="added too much"):
        assert_complete_token_retention(source, source + " " + "NOISE " * 20)


def test_ordered_token_contract_rejects_reordering() -> None:
    with pytest.raises(AssertionError, match="deleted or reordered"):
        assert_ordered_token_retention("ALPHA BRAVO CHARLIE", "BRAVO ALPHA CHARLIE")


def test_extra_token_contract_rejects_non_pagination_noise() -> None:
    assert_only_allowed_extra_tokens(
        "ALPHA BRAVO",
        "ALPHA 2 BRAVO MORE",
        ["MORE"],
        max_page_number=2,
    )
    with pytest.raises(AssertionError, match="unsupported tokens"):
        assert_only_allowed_extra_tokens(
            "ALPHA BRAVO",
            "ALPHA INVENTED BRAVO",
            ["MORE"],
            max_page_number=2,
        )
    with pytest.raises(AssertionError, match="unsupported tokens"):
        assert_only_allowed_extra_tokens(
            "ALPHA BRAVO",
            "ALPHA 9999 BRAVO",
            ["MORE"],
            max_page_number=2,
        )
    with pytest.raises(AssertionError, match="overproduced"):
        assert_only_allowed_extra_tokens(
            "ALPHA BRAVO",
            "ALPHA BRAVO MORE MORE MORE",
            ["MORE"],
            max_page_number=2,
        )


def test_dialogue_contract_rejects_character_or_dialogue_loss() -> None:
    anchors = [{"speaker": "MARA", "dialogue": "Keep the blue door locked"}]
    original = "MARA\nKeep the blue door locked."
    assert_dialogue_anchors(original, anchors)

    with pytest.raises(AssertionError, match="speaker-detached"):
        assert_dialogue_anchors("ELI\nKeep the blue door locked.", anchors)
    with pytest.raises(AssertionError, match="speaker-detached"):
        assert_dialogue_anchors("MARA\nLeave the blue door open.", anchors)
    with pytest.raises(AssertionError, match="speaker-detached"):
        assert_dialogue_anchors(
            "MARA\nWrong line.\n\nELI\nKeep the blue door locked.",
            anchors,
        )
