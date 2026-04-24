"""Ordered storyboard beat helpers for grid generation."""

from __future__ import annotations

from typing import Any

from cine_forge.modules.visualization.storyboard_v1.prompting import _sanitize_visual_text
from cine_forge.modules.visualization.storyboard_v1.support import slugify


def build_ordered_grid_beats(
    *,
    scene: Any,
    shots: list[Any],
    character_identity_locks: dict[str, Any],
) -> list[str]:
    """Build a left-to-right story spine from existing scene and shot-plan truth."""
    scene_anchors = _scene_anchors(scene)
    total = len(shots)
    beats: list[str] = []
    for index, shot in enumerate(shots, start=1):
        action = _clean(shot.action_description) or _clean(shot.blocking)
        blocking = _clean(shot.blocking)
        edit_intent = _clean(shot.edit_intent)
        character_note = _character_note(shot.characters_in_frame, character_identity_locks)
        role = _beat_role(index=index, total=total)
        parts = [
            f"Beat {index} of {total} / shot {shot.shot_id}: {role}.",
            f"Visual story action: {action or 'hold the planned shot action visually'}.",
        ]
        if blocking and blocking != action:
            parts.append(f"Blocking continuity: {blocking}.")
        if character_note:
            parts.append(f"Recurring identity lock: {character_note}.")
        if edit_intent:
            parts.append(f"Story function: {edit_intent}.")
        if scene_anchors:
            parts.append(f"Scene-specific anchors to keep visible: {scene_anchors}.")
        beats.append(" ".join(parts))
    return beats


def _scene_anchors(scene: Any) -> str:
    anchors: list[str] = []
    for value in (
        getattr(scene, "heading", ""),
        getattr(scene, "location", ""),
        getattr(scene, "time_of_day", ""),
        getattr(scene, "tone_mood", ""),
    ):
        text = _clean(value)
        if text:
            anchors.append(text)
    props = getattr(scene, "props_mentioned", [])
    if isinstance(props, list):
        anchors.extend(_clean(prop) for prop in props if _clean(prop))
    return "; ".join(dict.fromkeys(anchors))


def _character_note(
    character_ids: list[str],
    character_identity_locks: dict[str, Any],
) -> str:
    notes: list[str] = []
    for character_id in character_ids:
        lock = character_identity_locks.get(slugify(str(character_id)))
        if lock is None:
            continue
        details = [f"{lock.name}: {lock.appearance_summary}"]
        wardrobe = getattr(lock, "wardrobe_summary", None)
        if wardrobe:
            details.append(f"wardrobe {wardrobe}")
        notes.append("; ".join(details))
    return " | ".join(notes)


def _beat_role(*, index: int, total: int) -> str:
    if index == 1:
        return "opening beat that establishes the scene pressure and geography"
    if index == total:
        return "closing beat that preserves the scene turn or final visual emphasis"
    return "middle beat that advances the scene from the prior panel"


def _clean(value: Any) -> str:
    return _sanitize_visual_text(value).strip()
