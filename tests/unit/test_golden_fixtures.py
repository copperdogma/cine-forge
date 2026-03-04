"""Structural integrity tests for CineForge golden fixture files.

These tests verify that the hand-curated golden references in
``tests/fixtures/golden/`` remain internally consistent and match the
expectations registered in :data:`golden_fixture_helpers.GOLDEN_SPECS`.

They do NOT test extraction quality — that lives in the promptfoo eval suite
under ``benchmarks/tasks/``.  These tests exist to catch accidental corruption
during editing (truncated scenes, duplicate numbers, malformed fields, etc.).
"""

from __future__ import annotations

import pytest

from tests.unit.golden_fixture_helpers import (
    GOLDEN_SPECS,
    GoldenFixtureSpec,
    assert_characters_are_strings,
    assert_metadata_present,
    assert_no_duplicate_scene_numbers,
    assert_no_empty_headings,
    assert_scene_count,
    assert_source_lines_valid,
    load_golden,
)


@pytest.mark.unit
class TestMarinerSceneEntitiesStructure:
    """Structural integrity checks for ``the_mariner_scene_entities.json``.

    Each test method checks one invariant in isolation so failures pinpoint
    the exact structural problem without noise from unrelated checks.
    """

    def setup_method(self) -> None:
        self.spec: GoldenFixtureSpec = next(
            s for s in GOLDEN_SPECS if s.slug == "the_mariner_scene_entities"
        )
        self.data = load_golden(self.spec)

    def test_metadata_present(self) -> None:
        """All required metadata keys exist and are non-empty strings."""
        assert_metadata_present(self.data)

    def test_scene_count(self) -> None:
        """Scene list length matches the registered spec (15 scenes)."""
        assert_scene_count(self.data, self.spec)

    def test_no_empty_headings(self) -> None:
        """Every scene has a non-empty heading string."""
        assert_no_empty_headings(self.data)

    def test_no_duplicate_scene_numbers(self) -> None:
        """scene_number values are unique across all 15 scenes."""
        assert_no_duplicate_scene_numbers(self.data)

    def test_source_lines_valid(self) -> None:
        """Every scene's source_lines is [start, end] with end >= start >= 0."""
        assert_source_lines_valid(self.data)

    def test_characters_are_strings(self) -> None:
        """All character entries in action and dialogue lists are non-empty strings."""
        assert_characters_are_strings(self.data)
