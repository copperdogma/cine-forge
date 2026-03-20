"""CineForge API backend package."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def create_app(workspace_root: Path | None = None) -> Any:
    """Lazy app export to avoid importing the FastAPI stack during service imports."""
    from .app import create_app as _create_app

    return _create_app(workspace_root=workspace_root)


__all__ = ["create_app"]
