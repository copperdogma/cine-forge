"""Shared helpers for loading and asserting on CineForge golden fixture files.

Golden fixtures are hand-curated reference outputs stored under
``tests/fixtures/golden/``.  Each fixture is a JSON file with a well-known
schema.  This module provides:

- :class:`GoldenFixtureSpec` — typed registry entry for one golden file.
- :data:`GOLDEN_SPECS` — tuple of all known golden fixtures.
- :func:`load_golden` — loads and validates a golden fixture JSON.
- Assertion helpers that check structural invariants shared across fixtures.

Modelled after the ``dossier`` project's ``golden_fixture_helpers.py`` pattern.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

GOLDEN_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "golden"
EXPECTED_VERSION = "1.0.0"

# ---------------------------------------------------------------------------
# Spec registry
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GoldenFixtureSpec:
    """Registry entry for one golden fixture JSON file.

    Attributes:
        slug: Filename stem (without ``.json``), used to locate the file.
        scene_count: Expected number of scenes in the ``scenes`` list.
    """

    slug: str
    scene_count: int

    @property
    def json_path(self) -> Path:
        """Absolute path to the golden JSON file."""
        return GOLDEN_DIR / f"{self.slug}.json"


GOLDEN_SPECS: tuple[GoldenFixtureSpec, ...] = (
    GoldenFixtureSpec("the_mariner_scene_entities", scene_count=15),
)

# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

_REQUIRED_METADATA_KEYS = {"_description", "_version", "_created", "_source_script"}
_REQUIRED_TOP_LEVEL_KEYS = _REQUIRED_METADATA_KEYS | {"scenes"}


def load_golden(spec: GoldenFixtureSpec | str) -> dict[str, Any]:
    """Load and validate the top-level structure of a golden fixture JSON.

    If *spec* is a string, it is looked up in :data:`GOLDEN_SPECS` by slug.
    The file must exist and contain all required top-level keys.  The raw
    parsed ``dict`` is returned — callers apply domain-specific assertions via
    the helper functions below.

    Args:
        spec: A :class:`GoldenFixtureSpec` or a slug string.

    Returns:
        Parsed JSON as ``dict[str, Any]``.

    Raises:
        KeyError: If a slug string does not match any entry in
            :data:`GOLDEN_SPECS`.
        FileNotFoundError: If the JSON file does not exist on disk.
        ValueError: If required top-level keys are missing.
    """
    if isinstance(spec, str):
        slug = spec
        matches = [s for s in GOLDEN_SPECS if s.slug == slug]
        if not matches:
            raise KeyError(f"No GoldenFixtureSpec found for slug {slug!r}")
        spec = matches[0]

    path = spec.json_path
    if not path.exists():
        raise FileNotFoundError(f"Golden fixture not found: {path}")

    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))

    missing = _REQUIRED_TOP_LEVEL_KEYS - data.keys()
    if missing:
        raise ValueError(
            f"Golden fixture {spec.slug!r} is missing required keys: {sorted(missing)}"
        )

    return data


# ---------------------------------------------------------------------------
# Assertion helpers
# ---------------------------------------------------------------------------


def assert_metadata_present(data: dict[str, Any]) -> None:
    """Verify all required metadata keys are present.

    Required keys: ``_description``, ``_version``, ``_created``,
    ``_source_script``.  Each must be a non-empty string.

    Why: Metadata is how humans understand what a golden fixture covers and
    when it was last reviewed.  Missing or blank metadata makes the fixture
    opaque.
    """
    for key in sorted(_REQUIRED_METADATA_KEYS):
        assert key in data, f"Missing metadata key: {key!r}"
        assert isinstance(data[key], str), (
            f"Metadata key {key!r} must be a string, got {type(data[key]).__name__}"
        )
        assert data[key].strip(), f"Metadata key {key!r} must not be empty"


def assert_scene_count(data: dict[str, Any], spec: GoldenFixtureSpec) -> None:
    """Verify the number of scenes matches the spec.

    Why: An accidental truncation or off-by-one during editing would silently
    produce a fixture with fewer scenes, causing evals to test against
    incomplete data.
    """
    scenes = data.get("scenes", [])
    actual = len(scenes)
    assert actual == spec.scene_count, (
        f"Expected {spec.scene_count} scenes in {spec.slug!r}, found {actual}"
    )


def assert_no_empty_headings(data: dict[str, Any]) -> None:
    """Verify every scene has a non-empty ``heading`` string.

    Why: An empty or missing heading means the scene cannot be matched to a
    screenplay location, making the golden reference unusable for heading-based
    lookups or display.
    """
    for scene in data.get("scenes", []):
        scene_number = scene.get("scene_number", "?")
        heading = scene.get("heading", "")
        assert isinstance(heading, str), (
            f"Scene {scene_number}: 'heading' must be a string"
        )
        assert heading.strip(), f"Scene {scene_number}: 'heading' must not be empty"


def assert_no_duplicate_scene_numbers(data: dict[str, Any]) -> None:
    """Verify ``scene_number`` values are unique across all scenes.

    Why: Duplicate scene numbers would cause ambiguous lookups and hide data
    integrity problems introduced during manual editing of the golden file.
    """
    seen: set[int] = set()
    duplicates: list[int] = []
    for scene in data.get("scenes", []):
        num = scene.get("scene_number")
        if num in seen:
            duplicates.append(num)
        seen.add(num)
    assert not duplicates, f"Duplicate scene_number values found: {duplicates}"


def assert_source_lines_valid(data: dict[str, Any]) -> None:
    """Verify every scene's ``source_lines`` is ``[start, end]`` with ``end >= start >= 0``.

    Why: Invalid source_lines (negative indices, inverted ranges, wrong length)
    signal a hand-editing error and would break any code that maps scenes back
    to screenplay line ranges.
    """
    for scene in data.get("scenes", []):
        scene_number = scene.get("scene_number", "?")
        source_lines = scene.get("source_lines")
        assert isinstance(source_lines, list), (
            f"Scene {scene_number}: 'source_lines' must be a list"
        )
        assert len(source_lines) == 2, (
            f"Scene {scene_number}: 'source_lines' must have exactly 2 elements, "
            f"got {len(source_lines)}"
        )
        start, end = source_lines
        assert isinstance(start, int) and isinstance(end, int), (
            f"Scene {scene_number}: 'source_lines' elements must be ints"
        )
        assert start >= 0, (
            f"Scene {scene_number}: source_lines start ({start}) must be >= 0"
        )
        assert end >= start, (
            f"Scene {scene_number}: source_lines end ({end}) must be >= start ({start})"
        )


def assert_characters_are_strings(data: dict[str, Any]) -> None:
    """Verify all character list entries are non-empty strings.

    Checks both ``characters_in_action`` and ``characters_in_dialogue`` on
    every scene.

    Why: A blank string or non-string entry in a character list means the
    extraction produced garbage data and will silently pollute character-level
    aggregation queries.
    """
    for scene in data.get("scenes", []):
        scene_number = scene.get("scene_number", "?")
        for field in ("characters_in_action", "characters_in_dialogue"):
            entries = scene.get(field, [])
            assert isinstance(entries, list), (
                f"Scene {scene_number}: {field!r} must be a list"
            )
            for i, entry in enumerate(entries):
                assert isinstance(entry, str), (
                    f"Scene {scene_number}: {field}[{i}] must be a string, "
                    f"got {type(entry).__name__}"
                )
                assert entry.strip(), (
                    f"Scene {scene_number}: {field}[{i}] must not be empty"
                )
