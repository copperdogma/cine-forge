import os
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

# Add src to path
sys.path.append(os.path.abspath("src"))

from cine_forge.ai.fdx import detect_and_convert_fdx, export_screenplay_text


def normalize_char(name):
    # Remove (CONT'D), (O.S.), (V.O.) and whitespace
    n = name.split("(")[0].strip().upper()
    return " ".join(n.split())


def extract_structure(fdx_xml):
    root = ET.fromstring(fdx_xml)
    paras = []
    for p in root.iter():
        if p.tag.endswith("Paragraph"):
            ptype = p.attrib.get("Type", "Action")
            text = "".join(p.itertext()).strip().upper()
            if text:
                paras.append((ptype, text))
    return paras


@pytest.mark.round_trip
@pytest.mark.parametrize(
    "script_folder", ["big-fish", "brick-and-steel", "the-last-birthday-card"]
)
def test_fdx_fountain_fdx_fidelity(script_folder):
    fixture_dir = Path("tests/fixtures/round_trip") / script_folder
    fdx_file = next(fixture_dir.glob("*.fdx"))

    content = fdx_file.read_text(encoding="utf-8")

    # 1. FDX -> Fountain
    result = detect_and_convert_fdx(content)
    assert result.is_fdx
    fountain_text = result.fountain_text

    # 2. Fountain -> FDX
    export_result = export_screenplay_text(fountain_text, "fdx")
    assert export_result.success
    new_fdx_content = export_result.content.decode("utf-8")

    # 3. Compare Structure
    old_struct = extract_structure(content)
    new_struct = extract_structure(new_fdx_content)

    old_headings = [p[1] for p in old_struct if p[0] in ("Scene Heading", "Heading")]
    new_headings = [p[1] for p in new_struct if p[0] == "Scene Heading"]

    old_chars = set(normalize_char(p[1]) for p in old_struct if p[0] == "Character")
    new_chars = set(normalize_char(p[1]) for p in new_struct if p[0] == "Character")

    print(f"\\nFidelity Report for {script_folder}:")
    print(f"  Headings: {len(new_headings)} vs {len(old_headings)}")
    print(f"  Characters: {len(new_chars)} vs {len(old_chars)}")

    # FDX round-trip must be 100% lossless on core structure
    msg_head = f"Heading count mismatch: {len(new_headings)} vs {len(old_headings)}"
    assert len(new_headings) == len(old_headings), msg_head

    msg_char = (
        f"Character set mismatch. Missing: {old_chars - new_chars}, "
        f"Extra: {new_chars - old_chars}"
    )
    assert new_chars == old_chars, msg_char
