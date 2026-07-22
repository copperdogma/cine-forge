import re
from xml.etree import ElementTree as ET

import pytest

from cine_forge.ai.fdx import detect_and_convert_fdx, export_screenplay_text
from tests.round_trip.fidelity_contract import (
    assert_dialogue_anchors,
    assert_heading_fidelity,
    assert_source_contract,
    fixture_paths,
    load_contract,
)


def _normalize_char(name: str) -> str:
    # Remove (CONT'D), (O.S.), (V.O.) and whitespace
    n = name.split("(")[0].strip().upper()
    return " ".join(n.split())


def _normalize_text(text: str) -> str:
    return " ".join(
        text.replace("\u2018", "'")
        .replace("\u2019", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .upper()
        .split()
    )


def _extract_structure(fdx_xml: str) -> list[tuple[str, str]]:
    root = ET.fromstring(fdx_xml)
    paras = []
    for p in root.iter():
        if p.tag.endswith("Paragraph"):
            ptype = p.attrib.get("Type", "Action")
            text = _normalize_text("".join(p.itertext()))
            if text:
                paras.append((ptype, text))
    return paras


def _ordered_tokens(fdx_xml: str) -> list[str]:
    """Canonical text stream, insensitive only to typography and XML runs."""
    root = ET.fromstring(fdx_xml)
    text = " ".join(
        "".join(paragraph.itertext())
        for paragraph in root.iter()
        if paragraph.tag.endswith("Paragraph")
    )
    return re.findall(
        r"[A-Z0-9]+(?:'[A-Z0-9]+)?",
        text.replace("\u2019", "'").upper(),
    )


@pytest.mark.round_trip
@pytest.mark.parametrize(
    "script_folder", ["big-fish", "brick-and-steel", "the-last-birthday-card"]
)
def test_fdx_fountain_fdx_fidelity(script_folder: str) -> None:
    fountain_file, fdx_file, _pdf_file = fixture_paths(script_folder)
    contract = load_contract(script_folder)
    fountain_source = fountain_file.read_text(encoding="utf-8")
    assert_source_contract(fountain_source, contract)

    content = fdx_file.read_text(encoding="utf-8")

    # 1. FDX -> Fountain
    result = detect_and_convert_fdx(content)
    assert result.is_fdx
    fountain_text = result.fountain_text
    assert_heading_fidelity(fountain_source, fountain_text, contract)
    assert_dialogue_anchors(fountain_text, contract["dialogue_anchors"])

    # 2. Fountain -> FDX
    export_result = export_screenplay_text(fountain_text, "fdx")
    assert export_result.success
    new_fdx_content = export_result.content.decode("utf-8")

    # 3. Compare Structure
    old_struct = _extract_structure(content)
    new_struct = _extract_structure(new_fdx_content)

    old_headings = [p[1] for p in old_struct if p[0] in ("Scene Heading", "Heading")]
    new_headings = [p[1] for p in new_struct if p[0] == "Scene Heading"]

    old_chars = [_normalize_char(p[1]) for p in old_struct if p[0] == "Character"]
    new_chars = [_normalize_char(p[1]) for p in new_struct if p[0] == "Character"]

    # Core screenplay order and text are exact contracts. Count/set-only checks
    # previously allowed reordered headings, duplicated cues, and deleted prose.
    assert new_headings == old_headings
    assert new_chars == old_chars
    assert _ordered_tokens(new_fdx_content) == _ordered_tokens(content)
