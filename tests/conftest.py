"""Shared pytest config and fixtures."""

from pathlib import Path

import pytest

_MARKER_OWNED_DIRS = {
    "unit": (Path(__file__).parent / "unit").resolve(),
    "integration": (Path(__file__).parent / "integration").resolve(),
    "smoke": (Path(__file__).parent / "smoke").resolve(),
    "acceptance": (Path(__file__).parent / "acceptance").resolve(),
    "round_trip": (Path(__file__).parent / "round_trip").resolve(),
}


def pytest_collection_modifyitems(
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    """Reject tests in marker-owned suites that their advertised gate would skip.

    Marker declarations live in ``pyproject.toml``. Keeping this as a failing
    contract instead of auto-marking by path makes accidental omissions visible
    at collection time, including for focused test commands.
    """

    del config
    unmarked = [
        f"{item.nodeid} (missing {marker})"
        for item in items
        for marker, owner_dir in _MARKER_OWNED_DIRS.items()
        if Path(item.path).resolve().is_relative_to(owner_dir)
        and item.get_closest_marker(marker) is None
    ]
    if unmarked:
        formatted = "\n  - ".join(unmarked)
        raise pytest.UsageError(
            "Every test in a marker-owned suite must carry its suite marker. "
            f"Unmarked tests:\n  - {formatted}"
        )
