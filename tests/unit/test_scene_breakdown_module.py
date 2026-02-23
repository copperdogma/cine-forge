from __future__ import annotations

from typing import Any

import pytest

from cine_forge.modules.ingest.scene_breakdown_v1.main import (
    _extract_elements,
    _is_plausible_character_name,
    _normalize_character_name,
    _parse_heading,
    _split_into_scene_chunks,
    run_module,
)

# ---------------------------------------------------------------------------
# Heading parsing
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_parse_heading_basic_int() -> None:
    result = _parse_heading("INT. OFFICE - NIGHT")
    assert result["int_ext"] == "INT"
    assert result["location"] == "Office"
    assert result["time_of_day"] == "NIGHT"


@pytest.mark.unit
def test_parse_heading_basic_ext() -> None:
    result = _parse_heading("EXT. PARKING LOT - DAY")
    assert result["int_ext"] == "EXT"
    assert result["location"] == "Parking Lot"
    assert result["time_of_day"] == "DAY"


@pytest.mark.unit
def test_parse_heading_int_ext_combo() -> None:
    result = _parse_heading("INT/EXT. CAR - DAWN")
    assert result["int_ext"] == "INT/EXT"
    assert result["location"] == "Car"
    assert result["time_of_day"] == "DAWN"


@pytest.mark.unit
def test_parse_heading_no_time_of_day() -> None:
    result = _parse_heading("INT. HALLWAY")
    assert result["location"] == "Hallway"
    assert result["time_of_day"] == "UNSPECIFIED"


@pytest.mark.unit
def test_parse_heading_empty() -> None:
    result = _parse_heading("")
    assert result["int_ext"] == "INT/EXT"
    assert result["location"] == "UNKNOWN"
    assert result["time_of_day"] == "UNSPECIFIED"


@pytest.mark.unit
def test_parse_heading_strips_narrative_modifiers() -> None:
    result = _parse_heading("INT. LIVING ROOM - DAY - FLASHBACK")
    assert result["location"] == "Living Room"
    assert result["time_of_day"] == "DAY"


@pytest.mark.unit
def test_parse_heading_multi_segment_location() -> None:
    result = _parse_heading("INT. RUDDY & GREENE BUILDING - ELEVATOR - NIGHT")
    assert result["time_of_day"] == "NIGHT"
    assert "Ruddy" in result["location"]


# ---------------------------------------------------------------------------
# Scene splitting
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_split_into_scene_chunks_basic() -> None:
    script = (
        "FADE IN:\n\n"
        "INT. ROOM - NIGHT\n\n"
        "MARA\nHello.\n\n"
        "EXT. GARDEN - DAY\n\n"
        "Birds sing.\n"
    )
    chunks = _split_into_scene_chunks(script)
    assert len(chunks) == 2
    assert chunks[0].scene_number == 1
    assert chunks[1].scene_number == 2
    assert "MARA" in chunks[0].raw_text
    assert "Birds" in chunks[1].raw_text


@pytest.mark.unit
def test_split_into_scene_chunks_no_headings_returns_single_chunk() -> None:
    script = "Some random text\nwith no scene headings\n"
    chunks = _split_into_scene_chunks(script)
    assert len(chunks) == 1
    assert chunks[0].boundary_uncertain is True


@pytest.mark.unit
def test_split_into_scene_chunks_empty() -> None:
    assert _split_into_scene_chunks("") == []


# ---------------------------------------------------------------------------
# Element extraction
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_extract_elements_identifies_character_and_dialogue() -> None:
    lines = [
        "INT. ROOM - NIGHT",
        "",
        "MARA",
        "Where are we?",
        "",
        "JACK",
        "(whispering)",
        "I don't know.",
    ]
    elements, characters = _extract_elements(lines)
    element_types = [e.element_type for e in elements]
    assert "scene_heading" in element_types
    assert "character" in element_types
    assert "dialogue" in element_types
    assert "parenthetical" in element_types
    assert "MARA" in characters
    assert "JACK" in characters


@pytest.mark.unit
def test_extract_elements_identifies_transition() -> None:
    lines = [
        "INT. ROOM - DAY",
        "",
        "CUT TO:",
    ]
    elements, _chars = _extract_elements(lines)
    assert any(e.element_type == "transition" for e in elements)


@pytest.mark.unit
def test_extract_elements_identifies_action() -> None:
    lines = [
        "INT. ROOM - DAY",
        "",
        "Mara slowly opens the door.",
    ]
    elements, _chars = _extract_elements(lines)
    assert any(e.element_type == "action" for e in elements)


# ---------------------------------------------------------------------------
# Character name validation
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_normalize_character_name_strips_extensions() -> None:
    assert _normalize_character_name("MARA (V.O.)") == "MARA"
    assert _normalize_character_name("JACK (CONT'D)") == "JACK"


@pytest.mark.unit
def test_is_plausible_character_name_accepts_valid() -> None:
    assert _is_plausible_character_name("MARA") is True
    assert _is_plausible_character_name("MARINER") is True
    assert _is_plausible_character_name("DR CHEN") is True


@pytest.mark.unit
def test_is_plausible_character_name_rejects_stopwords() -> None:
    assert _is_plausible_character_name("CUT") is False
    assert _is_plausible_character_name("FADE") is False
    assert _is_plausible_character_name("NIGHT") is False


@pytest.mark.unit
def test_is_plausible_character_name_rejects_empty_and_short() -> None:
    assert _is_plausible_character_name("") is False
    assert _is_plausible_character_name("A") is False


# ---------------------------------------------------------------------------
# run_module (mock model)
# ---------------------------------------------------------------------------

SAMPLE_FOUNTAIN = (
    "INT. OFFICE - DAY\n\n"
    "MARA\nWe need to leave.\n\n"
    "JACK\nNot yet.\n\n"
    "EXT. PARKING LOT - NIGHT\n\n"
    "Rain pours down.\n\n"
    "ROSE\nIt's time.\n\n"
    "INT. ELEVATOR - NIGHT\n\n"
    "The doors close slowly.\n"
)


def _canonical_input(script_text: str = SAMPLE_FOUNTAIN) -> dict[str, Any]:
    return {
        "canonical_script": {
            "script_text": script_text,
            "source_format": "fountain",
            "normalization_model": "mock",
        }
    }


@pytest.mark.unit
def test_run_module_produces_scenes_and_index(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "cine_forge.modules.ingest.scene_breakdown_v1.main.validate_fountain_structure",
        lambda _: type("R", (), {"parseable": True, "coverage": 0.8, "parser_backend": "test"})(),
    )
    result = run_module(
        inputs=_canonical_input(),
        params={"work_model": "mock", "max_workers": 2},
        context={},
    )
    artifacts = result["artifacts"]
    scene_artifacts = [a for a in artifacts if a["artifact_type"] == "scene"]
    index_artifacts = [a for a in artifacts if a["artifact_type"] == "scene_index"]

    assert len(scene_artifacts) == 3
    assert len(index_artifacts) == 1

    # Scenes should have empty narrative fields (Tier 1 structural only)
    for scene in scene_artifacts:
        assert scene["data"]["narrative_beats"] == []
        assert scene["data"]["tone_mood"] == "neutral"
        assert scene["data"]["tone_shifts"] == []
        assert scene["metadata"]["annotations"]["discovery_tier"] == "structural"
        assert scene["metadata"]["annotations"]["ai_enrichment_used"] is False

    # Index should list all scenes
    index_data = index_artifacts[0]["data"]
    assert index_data["total_scenes"] == 3
    assert index_artifacts[0]["metadata"]["annotations"]["discovery_tier"] == "structural"


@pytest.mark.unit
def test_run_module_extracts_characters_structurally(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "cine_forge.modules.ingest.scene_breakdown_v1.main.validate_fountain_structure",
        lambda _: type("R", (), {"parseable": True, "coverage": 0.8, "parser_backend": "test"})(),
    )
    result = run_module(
        inputs=_canonical_input(),
        params={"work_model": "mock", "max_workers": 1},
        context={},
    )
    all_characters: set[str] = set()
    for a in result["artifacts"]:
        if a["artifact_type"] == "scene":
            all_characters.update(a["data"]["characters_present"])

    assert "MARA" in all_characters
    assert "JACK" in all_characters
    assert "ROSE" in all_characters


@pytest.mark.unit
def test_run_module_rejects_empty_script(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "cine_forge.modules.ingest.scene_breakdown_v1.main.validate_fountain_structure",
        lambda _: type("R", (), {"parseable": False, "coverage": 0.0, "parser_backend": "test"})(),
    )
    with pytest.raises(ValueError, match="non-empty canonical script"):
        run_module(
            inputs=_canonical_input(""),
            params={"work_model": "mock"},
            context={},
        )


@pytest.mark.unit
def test_run_module_rejects_missing_input() -> None:
    with pytest.raises(ValueError, match="requires upstream canonical_script"):
        run_module(inputs={}, params={"work_model": "mock"}, context={})


@pytest.mark.unit
def test_run_module_scene_order_is_deterministic(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "cine_forge.modules.ingest.scene_breakdown_v1.main.validate_fountain_structure",
        lambda _: type("R", (), {"parseable": True, "coverage": 0.8, "parser_backend": "test"})(),
    )
    result = run_module(
        inputs=_canonical_input(),
        params={"work_model": "mock", "max_workers": 4},
        context={},
    )
    scenes = [a for a in result["artifacts"] if a["artifact_type"] == "scene"]
    numbers = [s["data"]["scene_number"] for s in scenes]
    assert numbers == sorted(numbers)


@pytest.mark.unit
def test_run_module_cost_is_present(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "cine_forge.modules.ingest.scene_breakdown_v1.main.validate_fountain_structure",
        lambda _: type("R", (), {"parseable": True, "coverage": 0.8, "parser_backend": "test"})(),
    )
    result = run_module(
        inputs=_canonical_input(),
        params={"work_model": "mock"},
        context={},
    )
    assert "cost" in result
    assert "estimated_cost_usd" in result["cost"]


@pytest.mark.unit
def test_run_module_includes_provenance(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "cine_forge.modules.ingest.scene_breakdown_v1.main.validate_fountain_structure",
        lambda _: type("R", (), {"parseable": True, "coverage": 0.8, "parser_backend": "test"})(),
    )
    result = run_module(
        inputs=_canonical_input(),
        params={"work_model": "mock"},
        context={},
    )
    scene = next(a for a in result["artifacts"] if a["artifact_type"] == "scene")
    assert scene["data"]["provenance"]
    field_names = {p["field_name"] for p in scene["data"]["provenance"]}
    assert "heading" in field_names
    assert "characters_present" in field_names
