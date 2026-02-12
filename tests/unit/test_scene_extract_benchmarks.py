from __future__ import annotations

from pathlib import Path

import pytest

from cine_forge.ai import validate_fountain_structure
from cine_forge.modules.ingest.scene_extract_v1.main import _split_into_scene_chunks


@pytest.mark.unit
def test_scene_extract_fixture_coverage_and_fallback_behavior() -> None:
    fixtures_dir = Path(__file__).resolve().parents[1] / "fixtures" / "scene_extract_inputs"
    cases = [
        ("formatted_screenplay.fountain", 2),
        ("prose_converted_screenplay.fountain", 2),
        ("malformed_screenplay.txt", 1),
    ]

    fallback_count = 0
    non_fallback_count = 0
    for name, min_scene_count in cases:
        text = (fixtures_dir / name).read_text(encoding="utf-8")
        chunks = _split_into_scene_chunks(text)
        assert len(chunks) >= min_scene_count
        parse_check = validate_fountain_structure(text)
        assert 0.0 <= parse_check.coverage <= 1.0
        if name != "malformed_screenplay.txt":
            assert parse_check.parseable is True
        if parse_check.parser_backend == "heuristic-fallback":
            fallback_count += 1
        else:
            non_fallback_count += 1

    if non_fallback_count == 0:
        assert fallback_count == len(cases)
    else:
        assert fallback_count < len(cases)
