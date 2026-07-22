"""Fail-closed JSON loading for retained evaluation evidence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_result_json(path: Path) -> Any:
    """Parse retained JSON while rejecting duplicate keys at any depth."""
    try:
        return json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_unique_object,
        )
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid retained result JSON: {exc}") from exc


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"retained result JSON contains duplicate key {key!r}")
        value[key] = item
    return value
