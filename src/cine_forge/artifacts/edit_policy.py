"""Shared artifact edit policy helpers."""

from __future__ import annotations

from typing import TypeAlias

EditRestriction: TypeAlias = tuple[str, str]  # noqa: UP040 - FastAPI CLI here still runs on Python 3.11

_ARTIFACT_EDIT_RESTRICTIONS: dict[str, EditRestriction] = {
    "render_prompt": (
        "Render prompts are review-only compiled artifacts. Update upstream artifacts instead.",
        "Change the creative inputs or other upstream artifacts so CineForge recompiles "
        "the prompt.",
    ),
    "media_validation": (
        "Validation artifacts are runtime evidence snapshots and cannot be edited directly.",
        "Re-run validation or update the validated media source instead of editing the report.",
    ),
}


def get_artifact_edit_restriction(artifact_type: str) -> EditRestriction | None:
    """Return the edit restriction for *artifact_type*, if one exists."""
    return _ARTIFACT_EDIT_RESTRICTIONS.get(artifact_type)
