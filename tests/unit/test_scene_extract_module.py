from __future__ import annotations

from typing import Any

import pytest

from cine_forge.modules.ingest.scene_extract_v1.main import (
    _EnrichmentEnvelope,
    _extract_elements,
    _normalize_character_name,
    _parse_heading,
    _split_into_scene_chunks,
    run_module,
)
from cine_forge.schemas import QAResult


def _canonical_payload(script_text: str) -> dict[str, Any]:
    return {
        "title": "Test Script",
        "script_text": script_text,
        "line_count": script_text.count("\n") + 1,
        "scene_count": 2,
        "normalization": {
            "source_format": "screenplay",
            "strategy": "passthrough_cleanup",
            "inventions": [],
            "assumptions": [],
            "overall_confidence": 0.9,
            "rationale": "fixture",
        },
    }


@pytest.mark.unit
def test_split_into_scene_chunks_detects_int_ext_boundaries() -> None:
    text = "INT. LAB - NIGHT\nMARA\nReady.\n\nEXT. STREET - DAY\nJON\nGo."
    chunks = _split_into_scene_chunks(text)
    assert len(chunks) == 2
    assert chunks[0].source_span.start_line == 1
    assert chunks[1].source_span.start_line == 5


@pytest.mark.unit
def test_split_into_scene_chunks_handles_compact_headings_without_space() -> None:
    text = "EXT.CITY - NIGHT\nMARA\nReady.\n\nINT.LAB - DAY\nJON\nGo."
    chunks = _split_into_scene_chunks(text)
    assert len(chunks) == 2
    assert chunks[0].raw_text.splitlines()[0] == "EXT.CITY - NIGHT"
    assert chunks[1].raw_text.splitlines()[0] == "INT.LAB - DAY"


@pytest.mark.unit
def test_split_into_scene_chunks_handles_missing_headings() -> None:
    chunks = _split_into_scene_chunks("MARA walks through rain.\nShe stops.")
    assert len(chunks) == 1
    assert chunks[0].scene_number == 1


@pytest.mark.unit
def test_character_normalization_removes_voice_modifiers() -> None:
    assert _normalize_character_name("JOHN (V.O.)") == "JOHN"
    assert _normalize_character_name("MARA (CONT'D)") == "MARA"


@pytest.mark.unit
def test_parse_heading_multi_segment_location() -> None:
    """INT. BUILDING - HALLWAY - NIGHT should keep full location."""
    result = _parse_heading("INT. BUILDING - HALLWAY - NIGHT")
    assert result["int_ext"] == "INT"
    assert result["location"] == "Building - Hallway"
    assert result["time_of_day"] == "NIGHT"


@pytest.mark.unit
def test_parse_heading_three_segment_location_with_time() -> None:
    """INT. HOTEL - LOBBY - ELEVATOR BANK - DAY should keep all location parts."""
    result = _parse_heading("INT. HOTEL - LOBBY - ELEVATOR BANK - DAY")
    assert result["int_ext"] == "INT"
    assert result["location"] == "Hotel - Lobby - Elevator Bank"
    assert result["time_of_day"] == "DAY"


@pytest.mark.unit
def test_parse_heading_no_time_keeps_all_as_location() -> None:
    """INT. BUILDING - ROOFTOP should treat last segment as location if not a time."""
    result = _parse_heading("INT. BUILDING - ROOFTOP")
    assert result["location"] == "Building - Rooftop"
    assert result["time_of_day"] == "UNSPECIFIED"


@pytest.mark.unit
def test_parse_heading_strips_narrative_modifiers() -> None:
    """EXT. COASTLINE - DAY - PAST should strip PAST and use DAY as time."""
    result = _parse_heading("EXT. COASTLINE - DAY - PAST")
    assert result["location"] == "Coastline"
    assert result["time_of_day"] == "DAY"


@pytest.mark.unit
def test_parse_heading_strips_flashback_modifier() -> None:
    """EXT. BACKYARD - DAY - (FLASHBACK) should strip the modifier."""
    result = _parse_heading("EXT. BACKYARD - DAY - (FLASHBACK)")
    assert result["location"] == "Backyard"
    assert result["time_of_day"] == "DAY"


@pytest.mark.unit
def test_extract_elements_classifies_fade_in_as_transition() -> None:
    lines = ["INT. LAB - NIGHT", "FADE IN:", "MARA", "Hello."]
    elements, _ = _extract_elements(lines)
    fade = next(e for e in elements if "FADE" in e.content)
    assert fade.element_type == "transition"


@pytest.mark.unit
def test_extract_elements_classifies_end_flashback_as_transition() -> None:
    lines = ["INT. LAB - NIGHT", "Some action.", "", "END FLASHBACK"]
    elements, _ = _extract_elements(lines)
    fb = next(e for e in elements if "FLASHBACK" in e.content)
    assert fb.element_type == "transition"


@pytest.mark.unit
def test_extract_elements_classifies_smash_cut_as_transition() -> None:
    lines = ["INT. LAB - NIGHT", "MARA", "Hello.", "", "SMASH CUT:"]
    elements, _ = _extract_elements(lines)
    cut = next(e for e in elements if "SMASH" in e.content)
    assert cut.element_type == "transition"


@pytest.mark.unit
def test_extract_elements_contd_is_character_cue() -> None:
    """MARA (CONT'D) should be classified as a character cue, not action."""
    lines = ["INT. LAB - NIGHT", "", "MARA (CONT'D)", "I'm back."]
    elements, chars = _extract_elements(lines)
    mara = next(e for e in elements if "MARA" in e.content)
    assert mara.element_type == "character"
    assert "MARA" in chars


@pytest.mark.unit
def test_run_module_emits_scene_and_scene_index_artifacts() -> None:
    script = (
        "INT. LAB - NIGHT\n"
        "MARA\n"
        "We're live.\n\n"
        "EXT. STREET - DAY\n"
        "JON (O.S.)\n"
        "Move!\n"
    )
    result = run_module(
        inputs={"normalize": _canonical_payload(script)},
        params={"model": "mock", "qa_model": "mock", "skip_qa": False},
        context={"run_id": "unit", "stage_id": "extract"},
    )
    scenes = [item for item in result["artifacts"] if item["artifact_type"] == "scene"]
    scene_index = next(
        item for item in result["artifacts"] if item["artifact_type"] == "scene_index"
    )

    assert len(scenes) == 2
    assert scenes[0]["data"]["scene_id"] == "scene_001"
    assert scenes[0]["data"]["source_span"]["start_line"] == 1
    assert "MARA" in scenes[0]["data"]["characters_present"]
    assert scene_index["data"]["total_scenes"] == 2
    assert scene_index["data"]["estimated_runtime_minutes"] == 2.0


@pytest.mark.unit
def test_run_module_filters_pronoun_character_noise() -> None:
    script = (
        "INT. LAB - NIGHT\n"
        "HE moves to the door.\n"
        "IT falls.\n"
        "MARINER\n"
        "Move.\n\n"
        "EXT. STREET - DAY\n"
        "ROSE\n"
        "Now.\n"
    )
    result = run_module(
        inputs={"normalize": _canonical_payload(script)},
        params={"model": "mock", "qa_model": "mock", "skip_qa": False},
        context={"run_id": "unit", "stage_id": "extract"},
    )
    scene_index = next(
        item for item in result["artifacts"] if item["artifact_type"] == "scene_index"
    )
    unique = set(scene_index["data"]["unique_characters"])
    assert "MARINER" in unique
    assert "ROSE" in unique
    assert "HE" not in unique
    assert "IT" not in unique


@pytest.mark.unit
def test_run_module_retries_scene_when_qa_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    qa_calls = {"count": 0}

    def fake_run_scene_qa(**_: Any):
        qa_calls["count"] += 1
        if qa_calls["count"] == 1:
            return (
                QAResult(
                    passed=False,
                    confidence=0.4,
                    issues=[
                        {
                            "severity": "error",
                            "description": "Missing character",
                            "location": "line 2",
                        }
                    ],
                    summary="retry",
                ),
                {"model": "mock", "input_tokens": 0, "output_tokens": 0, "estimated_cost_usd": 0.0},
            )
        return (
            QAResult(passed=True, confidence=0.9, issues=[], summary="ok"),
            {"model": "mock", "input_tokens": 0, "output_tokens": 0, "estimated_cost_usd": 0.0},
        )

    monkeypatch.setattr(
        "cine_forge.modules.ingest.scene_extract_v1.main._run_scene_qa",
        fake_run_scene_qa,
    )

    # Use a scene with unresolved time_of_day so QA triggers
    result = run_module(
        inputs={"normalize": _canonical_payload("INT. LAB\nMARA\nHi.")},
        params={"model": "mock", "qa_model": "gpt-4o-mini", "skip_qa": False, "max_retries": 2},
        context={"run_id": "unit", "stage_id": "extract"},
    )
    scene = next(item for item in result["artifacts"] if item["artifact_type"] == "scene")
    assert qa_calls["count"] == 2
    assert scene["metadata"]["health"] == "valid"


@pytest.mark.unit
def test_run_module_marks_needs_review_after_qa_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    def always_fail_qa(**_: Any):
        return (
            QAResult(
                passed=False,
                confidence=0.35,
                issues=[{"severity": "error", "description": "Bad mapping", "location": "scene"}],
                summary="failed",
            ),
            {"model": "mock", "input_tokens": 0, "output_tokens": 0, "estimated_cost_usd": 0.0},
        )

    monkeypatch.setattr(
        "cine_forge.modules.ingest.scene_extract_v1.main._run_scene_qa",
        always_fail_qa,
    )

    # Use a scene with unresolved time_of_day so QA actually triggers
    result = run_module(
        inputs={"normalize": _canonical_payload("INT. LAB\nMARA\nHi.")},
        params={"model": "mock", "qa_model": "gpt-4o-mini", "skip_qa": False, "max_retries": 1},
        context={"run_id": "unit", "stage_id": "extract"},
    )
    scene = next(item for item in result["artifacts"] if item["artifact_type"] == "scene")
    index = next(item for item in result["artifacts"] if item["artifact_type"] == "scene_index")
    assert scene["metadata"]["health"] == "needs_review"
    assert index["metadata"]["health"] == "needs_review"
    assert index["data"]["scenes_need_review"] == 1


@pytest.mark.unit
def test_run_module_uses_skip_qa_without_calling_qa(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_if_called(**_: Any):
        raise AssertionError("QA should not run when skip_qa=true")

    monkeypatch.setattr(
        "cine_forge.modules.ingest.scene_extract_v1.main._run_scene_qa",
        fail_if_called,
    )

    result = run_module(
        inputs={"normalize": _canonical_payload("INT. LAB - NIGHT\nMARA\nHi.")},
        params={"model": "mock", "qa_model": "mock", "skip_qa": True},
        context={"run_id": "unit", "stage_id": "extract"},
    )
    scene = next(item for item in result["artifacts"] if item["artifact_type"] == "scene")
    assert scene["metadata"]["health"] == "valid"
    assert "qa_result" not in scene["metadata"]["annotations"]


@pytest.mark.unit
def test_run_module_marks_disagreement_as_needs_review(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_enrich_scene(**_: Any):
        return (
            _EnrichmentEnvelope(heading="EXT. SOMEWHERE - DAY"),
            {"model": "mock", "input_tokens": 0, "output_tokens": 0, "estimated_cost_usd": 0.0},
            "prompt",
        )

    monkeypatch.setattr(
        "cine_forge.modules.ingest.scene_extract_v1.main._enrich_scene",
        fake_enrich_scene,
    )

    result = run_module(
        inputs={"normalize": _canonical_payload("MARA walks in.\nShe sits.")},
        params={"model": "mock", "qa_model": "mock", "skip_qa": False},
        context={"run_id": "unit", "stage_id": "extract"},
    )
    scene = next(item for item in result["artifacts"] if item["artifact_type"] == "scene")
    assert scene["metadata"]["health"] == "needs_review"
    assert scene["metadata"]["annotations"]["disagreements"]


@pytest.mark.unit
def test_run_module_skips_ai_enrichment_when_fields_resolved(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_enrich_called(**_: Any):
        raise AssertionError(
            "AI enrichment should be skipped for fully resolved deterministic scene"
        )

    monkeypatch.setattr(
        "cine_forge.modules.ingest.scene_extract_v1.main._enrich_scene",
        fail_if_enrich_called,
    )

    result = run_module(
        inputs={"normalize": _canonical_payload("INT. LAB - NIGHT\nMARA\nGo.")},
        params={"model": "gpt-4o", "qa_model": "mock", "skip_qa": False},
        context={"run_id": "unit", "stage_id": "extract"},
    )
    scene = next(item for item in result["artifacts"] if item["artifact_type"] == "scene")
    assert scene["metadata"]["annotations"]["ai_enrichment_used"] is False


@pytest.mark.unit
def test_run_module_cost_is_lower_when_skip_qa(monkeypatch: pytest.MonkeyPatch) -> None:
    def priced_enrich_scene(**_: Any):
        return (
            _EnrichmentEnvelope(),
            {"model": "mock", "input_tokens": 10, "output_tokens": 5, "estimated_cost_usd": 0.02},
            "prompt",
        )

    def priced_qa(**_: Any):
        return (
            QAResult(passed=True, confidence=0.9, issues=[], summary="ok"),
            {"model": "mock", "input_tokens": 8, "output_tokens": 4, "estimated_cost_usd": 0.03},
        )

    monkeypatch.setattr(
        "cine_forge.modules.ingest.scene_extract_v1.main._enrich_scene",
        priced_enrich_scene,
    )
    monkeypatch.setattr(
        "cine_forge.modules.ingest.scene_extract_v1.main._run_scene_qa",
        priced_qa,
    )

    # Use a scene with unresolved time_of_day so QA actually triggers
    script = "INT. LAB\nMARA\nGo."
    with_qa = run_module(
        inputs={"normalize": _canonical_payload(script)},
        params={"model": "gpt-4o", "qa_model": "gpt-4o-mini", "skip_qa": False},
        context={"run_id": "unit", "stage_id": "extract"},
    )
    no_qa = run_module(
        inputs={"normalize": _canonical_payload(script)},
        params={"model": "gpt-4o", "qa_model": "gpt-4o-mini", "skip_qa": True},
        context={"run_id": "unit", "stage_id": "extract"},
    )
    assert with_qa["cost"]["estimated_cost_usd"] > no_qa["cost"]["estimated_cost_usd"]
