from __future__ import annotations

import pytest

from cine_forge.ai.patching import apply_search_replace_patches, parse_search_replace_blocks


@pytest.mark.unit
def test_parse_search_replace_blocks_extracts_multiple_patches() -> None:
    raw = (
        "<<<<<<< SEARCH\nOLD ONE\n=======\nNEW ONE\n>>>>>>> REPLACE\n\n"
        "<<<<<<< SEARCH\nOLD TWO\n=======\nNEW TWO\n>>>>>>> REPLACE"
    )
    patches = parse_search_replace_blocks(raw)
    assert len(patches) == 2
    assert patches[0].search == "OLD ONE"
    assert patches[1].replace == "NEW TWO"


@pytest.mark.unit
def test_apply_search_replace_patches_supports_fuzzy_match() -> None:
    original = "INT. LAB - NIGHT\nMARA\nWe still have one chance.\n"
    raw = (
        "<<<<<<< SEARCH\nMARA\nWe still have one chance!\n=======\n"
        "MARA\nWe have one chance.\n>>>>>>> REPLACE"
    )
    patches = parse_search_replace_blocks(raw)
    updated, failures = apply_search_replace_patches(original, patches, fuzzy_threshold=0.8)
    assert not failures
    assert "We have one chance." in updated
