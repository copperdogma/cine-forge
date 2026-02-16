from __future__ import annotations

import pytest

from cine_forge.ai.long_doc import (
    estimate_token_count,
    group_scenes_into_chunks,
    initialize_running_metadata,
    select_strategy,
    split_screenplay_by_scene,
    split_text_into_chunks,
    update_running_metadata,
)


@pytest.mark.unit
def test_select_strategy_short_doc_uses_single_pass() -> None:
    strategy = select_strategy(source_format="prose", confidence=0.6, text="short text")
    assert strategy.name == "single_pass"


@pytest.mark.unit
def test_select_strategy_long_screenplay_prefers_chunked_conversion() -> None:
    long_text = "word " * 6000
    strategy = select_strategy(source_format="screenplay", confidence=0.9, text=long_text)
    assert strategy.name == "chunked_conversion"


@pytest.mark.unit
def test_split_text_into_chunks_respects_overlap() -> None:
    text = " ".join(f"w{i}" for i in range(12))
    chunks = split_text_into_chunks(text=text, chunk_size_tokens=5, overlap_tokens=2)
    assert len(chunks) == 4
    assert chunks[0].split()[-2:] == chunks[1].split()[:2]


@pytest.mark.unit
def test_estimate_token_count_handles_empty() -> None:
    assert estimate_token_count("   ") == 0


@pytest.mark.unit
def test_split_screenplay_by_scene_splits_headings() -> None:
    text = "INT. ROOM - DAY\nA\n\nEXT. STREET - NIGHT\nB"
    scenes = split_screenplay_by_scene(text)
    assert len(scenes) == 2
    assert scenes[0].startswith("INT. ROOM")


@pytest.mark.unit
def test_group_scenes_into_chunks_adds_previous_context_marker() -> None:
    scenes = [
        "INT. ROOM - DAY\nA " * 200,
        "EXT. STREET - NIGHT\nB " * 200,
    ]
    chunks = group_scenes_into_chunks(scenes, target_chunk_tokens=300, overlap_tokens=50)
    assert len(chunks) >= 2
    assert "[PREVIOUS CONTEXT — DO NOT MODIFY]" in chunks[1]


@pytest.mark.unit
def test_running_metadata_updates_characters_and_locations() -> None:
    metadata = initialize_running_metadata("INT. LAB - DAY\nMARA\nHello.")
    updated = update_running_metadata(metadata, "EXT. STREET - NIGHT\nKIAN\nRun!")
    assert "MARA" in updated.characters
    assert "KIAN" in updated.characters
    assert "EXT. STREET - NIGHT" in updated.locations
