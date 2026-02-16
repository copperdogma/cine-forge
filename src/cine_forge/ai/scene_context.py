"""Extract scene-filtered context for entity-specific LLM calls."""

from __future__ import annotations

from typing import Any


def extract_scenes_for_entity(
    script_text: str,
    scene_index: dict[str, Any],
    entity_type: str,
    entity_name: str,
) -> str:
    """Return only the script text for scenes where an entity appears.

    For characters: matches against characters_present in each scene entry.
    For locations: matches against location field in each scene entry.
    For props: does a case-insensitive text search in each scene's source lines.

    Falls back to the full script if no matching scenes are found (safety net).
    """
    lines = script_text.splitlines()
    matching_scenes: list[str] = []

    entries = scene_index.get("entries", [])
    if not entries:
        return script_text

    name_upper = entity_name.upper().strip()

    for entry in entries:
        span = entry.get("source_span", {})
        start = span.get("start_line", 1) - 1  # 0-indexed
        end = span.get("end_line", len(lines))
        scene_lines = lines[start:end]

        if entity_type == "character":
            chars = [c.upper() for c in entry.get("characters_present", [])]
            if name_upper in chars:
                matching_scenes.append("\n".join(scene_lines))

        elif entity_type == "location":
            loc = entry.get("location", "").upper().strip()
            if loc == name_upper or name_upper in loc or loc in name_upper:
                matching_scenes.append("\n".join(scene_lines))

        elif entity_type == "prop":
            scene_text = "\n".join(scene_lines).upper()
            if name_upper in scene_text:
                matching_scenes.append("\n".join(scene_lines))

    if not matching_scenes:
        # Safety net: if no matches found, return full script
        return script_text

    return "\n\n".join(matching_scenes)
