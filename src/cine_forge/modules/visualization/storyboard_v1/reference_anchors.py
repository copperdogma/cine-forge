"""Reference-anchor prompt helpers for storyboard grid generation."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from cine_forge.modules.visualization.storyboard_v1.support import (
    resolve_character_bible,
    slugify,
)


def build_reference_anchor_lines(
    *,
    shots: list[Any],
    character_bibles: dict[str, dict[str, Any]],
    location_bible: dict[str, Any] | None,
    character_identity_locks: dict[str, Any],
    reference_images_by_shot: list[list[str]],
) -> list[str]:
    """Describe how direct reference images map to grid subjects and panels."""
    panel_refs = _panel_refs(reference_images_by_shot)
    all_refs = list(panel_refs)
    if not all_refs:
        return []

    lines: list[str] = []
    claimed_refs: set[str] = set()

    for character_id in _ordered_character_ids(shots):
        character_bible = resolve_character_bible(character_bibles, character_id)
        if character_bible is None:
            continue
        refs = [
            ref
            for ref in all_refs
            if _matches_entity_ref(ref, "character", [character_id, character_bible.get("name")])
        ]
        if not refs:
            continue
        claimed_refs.update(refs)
        name = str(character_bible.get("name") or character_id).strip()
        lock = character_identity_locks.get(slugify(character_id))
        detail = _identity_detail(lock)
        lines.append(
            (
                f"- {name}: use {', '.join(_basename(ref) for ref in refs)} as the "
                f"canonical off-canvas character reference for panels "
                f"{_format_panel_list(panel_refs[refs[0]])}. Preserve face, hair, build, "
                f"wardrobe silhouette, and recurring identity across every panel where "
                f"{name} appears. {detail} Do not draw the reference card or portrait "
                "as an object inside the scene."
            ).strip()
        )

    if location_bible is not None:
        location_names = [
            location_bible.get("location_id"),
            location_bible.get("name"),
            *(
                location_bible.get("aliases")
                if isinstance(location_bible.get("aliases"), list)
                else []
            ),
        ]
        refs = [
            ref for ref in all_refs if _matches_entity_ref(ref, "location", location_names)
        ]
        if refs:
            claimed_refs.update(refs)
            location_name = str(
                location_bible.get("name") or location_bible.get("location_id") or "location"
            ).strip()
            traits = _location_traits(location_bible)
            lines.append(
                (
                    f"- {location_name}: use {', '.join(_basename(ref) for ref in refs)} "
                    f"as the canonical off-canvas location reference for panels "
                    f"{_format_panel_list(panel_refs[refs[0]])}. Preserve recognizable "
                    f"layout, architectural cues, scale, weather, and practical objects. "
                    f"{traits} Do not draw the reference card itself inside the panel."
                ).strip()
            )

    unclaimed = [ref for ref in all_refs if ref not in claimed_refs]
    if unclaimed:
        lines.append(
            "- Other attached references: use "
            f"{', '.join(_basename(ref) for ref in unclaimed)} only as off-canvas "
            "visual anchors for relevant panels; never depict the reference cards "
            "themselves as props, posters, screens, or overlays."
        )

    return [_compact(line, 650) for line in lines]


def _panel_refs(reference_images_by_shot: list[list[str]]) -> dict[str, list[int]]:
    panel_refs: dict[str, list[int]] = {}
    for panel_index, refs in enumerate(reference_images_by_shot, start=1):
        for ref in refs:
            text = str(ref or "").strip()
            if not text:
                continue
            panel_refs.setdefault(text, []).append(panel_index)
    return panel_refs


def _ordered_character_ids(shots: Iterable[Any]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for shot in shots:
        for raw_character_id in getattr(shot, "characters_in_frame", []):
            character_id = str(raw_character_id or "").strip()
            key = slugify(character_id)
            if not character_id or key in seen:
                continue
            seen.add(key)
            ordered.append(character_id)
    return ordered


def _matches_entity_ref(ref: str, entity_type: str, names: Iterable[Any]) -> bool:
    ref_slug = slugify(ref.replace("/", " "))
    for name in names:
        text = str(name or "").strip()
        if not text:
            continue
        entity_fragment = f"{entity_type}_{slugify(text)}"
        if entity_fragment and entity_fragment in ref_slug:
            return True
    return False


def _identity_detail(lock: Any) -> str:
    if lock is None:
        return ""
    parts: list[str] = []
    appearance = str(getattr(lock, "appearance_summary", "") or "").strip()
    wardrobe = str(getattr(lock, "wardrobe_summary", "") or "").strip()
    features = [
        str(feature).strip()
        for feature in getattr(lock, "distinguishing_features", []) or []
        if str(feature).strip()
    ]
    if appearance:
        parts.append(_compact(appearance, 170))
    if wardrobe:
        parts.append(f"Wardrobe: {_compact(wardrobe, 120)}")
    if features:
        parts.append(f"Distinguishing cues: {_compact('; '.join(features[:3]), 150)}")
    return " ".join(parts)


def _location_traits(location_bible: dict[str, Any]) -> str:
    traits = [
        str(item).strip()
        for item in location_bible.get("physical_traits", []) or []
        if str(item).strip()
    ]
    description = str(location_bible.get("description") or "").strip()
    if traits:
        return f"Location cues: {_compact('; '.join(traits[:4]), 180)}."
    if description:
        return f"Location cues: {_compact(description, 180)}."
    return ""


def _format_panel_list(panels: list[int]) -> str:
    values = sorted(set(panels))
    if not values:
        return "the relevant panels"
    if len(values) == 1:
        return str(values[0])
    if values == list(range(values[0], values[-1] + 1)):
        return f"{values[0]}-{values[-1]}"
    return ", ".join(str(value) for value in values)


def _basename(ref: str) -> str:
    return ref.rsplit("/", maxsplit=1)[-1]


def _compact(value: str, max_chars: int) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= max_chars:
        return text
    cutoff = max(
        text.rfind(". ", 0, max_chars),
        text.rfind("; ", 0, max_chars),
        text.rfind(", ", 0, max_chars),
    )
    if cutoff < max_chars // 2:
        cutoff = max_chars
    return text[:cutoff].rstrip(" ,;.") + "."
