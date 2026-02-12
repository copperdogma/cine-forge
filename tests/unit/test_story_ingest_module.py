from __future__ import annotations

from pathlib import Path

import pytest

from cine_forge.modules.ingest.story_ingest_v1.main import (
    classify_format,
    detect_file_format,
    read_source_text,
    run_module,
)


@pytest.mark.unit
def test_detect_file_format_supports_expected_extensions() -> None:
    assert detect_file_format(Path("a.txt")) == "txt"
    assert detect_file_format(Path("a.md")) == "md"
    assert detect_file_format(Path("a.fountain")) == "fountain"
    assert detect_file_format(Path("a.pdf")) == "pdf"


@pytest.mark.unit
def test_detect_file_format_rejects_unknown_extension() -> None:
    with pytest.raises(ValueError, match="Unsupported input format"):
        detect_file_format(Path("a.docx"))


@pytest.mark.unit
def test_read_source_text_preserves_plain_text_exactly(tmp_path: Path) -> None:
    source = tmp_path / "sample.txt"
    payload = "Line one\nLine two\n"
    source.write_text(payload, encoding="utf-8")

    assert read_source_text(source) == payload


@pytest.mark.unit
def test_read_source_text_extracts_pdf_via_reader(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    source = tmp_path / "sample.pdf"
    source.write_bytes(b"%PDF-1.4 mock")

    monkeypatch.setattr(
        "cine_forge.modules.ingest.story_ingest_v1.main._extract_pdf_text",
        lambda _: "INT. ROOM - NIGHT\nMARA\nHello there.",
    )

    assert read_source_text(source) == "INT. ROOM - NIGHT\nMARA\nHello there."


@pytest.mark.unit
def test_classify_screenplay_detects_structural_signals() -> None:
    content = "\n".join(
        [
            "INT. CONTROL ROOM - NIGHT",
            "",
            "MARA",
            "(whispering)",
            "We still have one chance.",
            "CUT TO:",
            "EXT. RIDGE - NIGHT",
        ]
    )
    result = classify_format(content=content, file_format="fountain")
    assert result["detected_format"] == "screenplay"
    assert result["confidence"] >= 0.6
    assert result["evidence"]


@pytest.mark.unit
def test_classify_prose_detects_narrative_paragraphs() -> None:
    content = (
        "She crossed the market square before sunrise and watched the mist pull away from "
        "the river. The letter in her pocket felt heavier with each step, as if it could "
        "choose her future for her."
    )
    result = classify_format(content=content, file_format="txt")
    assert result["detected_format"] == "prose"
    assert result["confidence"] >= 0.3


@pytest.mark.unit
def test_classify_notes_detects_list_patterns() -> None:
    content = "\n".join(
        [
            "- Hero: Mara",
            "- Objective: restore comms",
            "1. Enter tower",
            "2. Trigger beacon",
            "3. Escape storm",
        ]
    )
    result = classify_format(content=content, file_format="md")
    assert result["detected_format"] == "notes"
    assert result["confidence"] >= 0.3


@pytest.mark.unit
def test_classification_confidence_higher_for_clear_signals() -> None:
    strong_screenplay = "\n".join(
        [
            "INT. ROOM - NIGHT",
            "MARA",
            "(quietly)",
            "We have to move.",
            "CUT TO:",
            "EXT. HILL - NIGHT",
        ]
    )
    ambiguous = "Fragments and ideas without clear scene structure or full narrative lines"

    strong = classify_format(content=strong_screenplay, file_format="fountain")
    weak = classify_format(content=ambiguous, file_format="txt")
    assert strong["confidence"] > weak["confidence"]


@pytest.mark.unit
def test_run_module_builds_raw_input_payload(tmp_path: Path) -> None:
    source = tmp_path / "notes.md"
    source_text = "- beat one\n- beat two\n"
    source.write_text(source_text, encoding="utf-8")

    result = run_module(
        inputs={},
        params={"input_file": str(source)},
        context={"run_id": "unit", "stage_id": "ingest", "runtime_params": {}},
    )

    artifact = result["artifacts"][0]
    assert artifact["artifact_type"] == "raw_input"
    assert artifact["data"]["content"] == source_text
    assert artifact["data"]["source_info"]["original_filename"] == "notes.md"
    assert artifact["data"]["classification"]["detected_format"] in {
        "notes",
        "unknown",
        "hybrid",
        "prose",
        "screenplay",
    }
