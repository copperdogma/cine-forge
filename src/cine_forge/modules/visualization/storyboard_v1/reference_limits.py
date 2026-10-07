"""Model limits shared by storyboard prompts, requests, and reference provenance."""

from __future__ import annotations

NANO_BANANA_MODEL = "gemini-nano-banana-2.1"
NANO_BANANA_MAX_REFERENCE_IMAGES = 14


def select_direct_references(
    model: str, reference_images: list[str], *, uses_template: bool = False
) -> list[str]:
    """Keep existing reference priority, reserving the first slot for a grid template."""
    if model != NANO_BANANA_MODEL:
        return list(reference_images)
    budget = NANO_BANANA_MAX_REFERENCE_IMAGES - int(uses_template)
    return reference_images[:budget]


def reference_limit_note(
    model: str, available: list[str], direct: list[str], notes: str | None
) -> str | None:
    if model != NANO_BANANA_MODEL:
        return notes
    omitted = [ref for ref in available if ref not in direct]
    if not omitted:
        return notes
    limit_note = "Reference image limit: omitted from direct input: " + ", ".join(omitted)
    return f"{notes}\n{limit_note}" if notes else limit_note
