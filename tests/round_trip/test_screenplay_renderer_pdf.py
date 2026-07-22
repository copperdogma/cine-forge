from __future__ import annotations

import pytest

from cine_forge.export.screenplay import ScreenplayRenderer
from cine_forge.modules.ingest.story_ingest_v1.main import read_source_text_with_diagnostics


@pytest.mark.round_trip
def test_screenplay_renderer_writes_semantically_readable_pdf(tmp_path) -> None:
    scenes = [
        {
            "scene_number": 1,
            "heading": "EXT. BEACH - DAY",
            "elements": [
                {"element_type": "scene_heading", "content": "EXT. BEACH - DAY"},
                {"element_type": "character", "content": "THE MARINER"},
                {"element_type": "dialogue", "content": "The sea is angry today."},
            ],
        }
    ]
    output_path = tmp_path / "screenplay-renderer.pdf"

    ScreenplayRenderer().render_pdf(
        scenes,
        str(output_path),
        project_title="THE MARINER",
    )

    assert output_path.read_bytes().startswith(b"%PDF")

    extracted_text, _diagnostics = read_source_text_with_diagnostics(output_path)
    normalized_text = " ".join(extracted_text.split()).upper()
    assert "THE MARINER" in normalized_text
    assert "EXT. BEACH - DAY" in normalized_text
    assert "THE SEA IS ANGRY TODAY." in normalized_text
