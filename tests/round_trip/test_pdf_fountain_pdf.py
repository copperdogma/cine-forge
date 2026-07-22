from pathlib import Path

import pdfplumber
import pytest

from cine_forge.ai.fdx import export_screenplay_text
from cine_forge.modules.ingest.story_ingest_v1.main import read_source_text_with_diagnostics
from tests.round_trip.fidelity_contract import (
    assert_complete_token_retention,
    assert_dialogue_anchors,
    assert_heading_fidelity,
    assert_only_allowed_extra_tokens,
    assert_ordered_text_anchors,
    assert_ordered_token_retention,
    assert_source_contract,
    fixture_paths,
    load_contract,
    renderable_fountain_text,
)

pytestmark = pytest.mark.round_trip


@pytest.mark.parametrize(
    "script_folder", ["big-fish", "brick-and-steel", "the-last-birthday-card"]
)
def test_pdf_fountain_pdf_fidelity(script_folder: str, tmp_path: Path) -> None:
    fountain_file, _fdx_file, pdf_file = fixture_paths(script_folder)
    contract = load_contract(script_folder)
    fountain_text = fountain_file.read_text(encoding="utf-8")
    assert_source_contract(fountain_text, contract)

    extracted_text, diagnostics = read_source_text_with_diagnostics(pdf_file)
    assert diagnostics.get("pdf_extractor_selected") == "pdfplumber"
    assert_heading_fidelity(fountain_text, extracted_text, contract)
    assert_ordered_text_anchors(extracted_text, contract["identity_anchors"])
    assert_dialogue_anchors(extracted_text, contract["dialogue_anchors"])
    assert_complete_token_retention(
        renderable_fountain_text(fountain_text),
        extracted_text,
        minimum_precision=contract["pdf_source_minimum_precision"],
        converted_token_aliases=contract.get("pdf_source_token_aliases"),
    )
    assert_ordered_token_retention(
        renderable_fountain_text(fountain_text),
        extracted_text,
        converted_token_aliases=contract.get("pdf_source_token_aliases"),
    )
    with pdfplumber.open(pdf_file) as source_pdf:
        source_page_count = len(source_pdf.pages)
    assert_only_allowed_extra_tokens(
        renderable_fountain_text(fountain_text),
        extracted_text,
        contract["allowed_pdf_extra_tokens"],
        converted_token_aliases=contract.get("pdf_source_token_aliases"),
        max_page_number=source_page_count,
    )

    export_result = export_screenplay_text(extracted_text, "pdf")
    assert export_result.success
    assert export_result.content
    assert export_result.content.startswith(b"%PDF")

    second_pdf = tmp_path / f"{script_folder}-second-generation.pdf"
    second_pdf.write_bytes(export_result.content)
    second_text, second_diagnostics = read_source_text_with_diagnostics(second_pdf)
    assert second_diagnostics.get("pdf_extractor_selected") == "pdfplumber"

    assert_heading_fidelity(extracted_text, second_text, contract)
    assert_ordered_text_anchors(second_text, contract["identity_anchors"])
    assert_dialogue_anchors(second_text, contract["dialogue_anchors"])
    assert_complete_token_retention(extracted_text, second_text)
    assert_ordered_token_retention(extracted_text, second_text)
    with pdfplumber.open(second_pdf) as generated_pdf:
        generated_page_count = len(generated_pdf.pages)
    assert_only_allowed_extra_tokens(
        extracted_text,
        second_text,
        contract["allowed_pdf_extra_tokens"],
        max_page_number=generated_page_count,
    )
