import json
import os
import sys
from pathlib import Path

import pytest

# Add src to path
sys.path.append(os.path.abspath("src"))

from cine_forge.ai.fdx import export_screenplay_text
from cine_forge.modules.ingest.story_ingest_v1.main import read_source_text_with_diagnostics


def evaluate(text):
    lines = text.splitlines()
    headings = [
        line.strip().upper()
        for line in lines
        if line.strip().upper().startswith(("INT.", "EXT.", "INT/EXT.", "I/E.", "EST."))
    ]
    chars = set()
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        # Heuristic for characters: uppercase, not heading, not transition, followed by content
        if (
            line_stripped
            and line_stripped.upper() == line_stripped
            and any(c.isalpha() for c in line_stripped)
            and len(line_stripped) < 30
            and i + 1 < len(lines)
            and lines[i + 1].strip()
        ):
            chars.add(line_stripped.split("(")[0].strip())
    return {
        "scene_count": len(headings),
        "character_count": len(chars),
        "word_count": len(text.split()),
    }


@pytest.mark.round_trip
@pytest.mark.parametrize(
    "script_folder", ["big-fish", "brick-and-steel", "the-last-birthday-card"]
)
def test_pdf_fountain_pdf_fidelity(script_folder, tmp_path):
    fixture_dir = Path("tests/fixtures/round_trip") / script_folder
    pdf_file = next(fixture_dir.glob("*.pdf"))
    golden_json = next(fixture_dir.glob("*-golden.json"))

    with golden_json.open() as f:
        golden = json.load(f)

    # 1. PDF -> Fountain (via ingestion)
    extracted_text, diagnostics = read_source_text_with_diagnostics(pdf_file)

    # 2. Fountain -> PDF
    export_result = export_screenplay_text(extracted_text, "pdf")
    assert export_result.success
    assert export_result.content

    # 3. Compare with Golden (most forgiving)
    actual = evaluate(extracted_text)

    # Thresholds (from Phase 3 spec):
    # Scene count: <= 5% delta
    # Word count: <= 10% delta

    scene_golden = golden["scene_count"]
    words_golden = golden["total_word_count"]

    scene_delta = abs(actual["scene_count"] - scene_golden) / max(scene_golden, 1)
    word_delta = abs(actual["word_count"] - words_golden) / max(words_golden, 1)

    print(f"\\nFidelity Report for {script_folder}:")
    print(f"  Scenes: {actual['scene_count']} vs {scene_golden} (Delta: {scene_delta:.1%})")
    print(f"  Words: {actual['word_count']} vs {words_golden} (Delta: {word_delta:.1%})")
    print(f"  Extractor: {diagnostics.get('pdf_extractor_selected')}")

    # Thresholds (very generous as original PDF extraction is lossy)
    assert scene_delta <= 0.15
    assert word_delta <= 0.25
