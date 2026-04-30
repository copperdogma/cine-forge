"""Helpers for scene-level and render-clip render units."""

from __future__ import annotations

import re
from collections.abc import Iterable

from cine_forge.schemas import RenderClip, ShotPlan

_PARENTHETICAL_RE = re.compile(r"\([^)]*\)")
_NON_WORD_RE = re.compile(r"[^a-z0-9']+")
_SMART_QUOTES = str.maketrans(
    {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
    }
)


def render_unit_entity_id(scene_id: str, render_clip: RenderClip | None) -> str:
    """Return the artifact entity id for a scene render or one render clip."""

    if render_clip is None:
        return scene_id
    if render_clip.clip_id == scene_id or render_clip.clip_id.startswith(f"{scene_id}_"):
        return render_clip.clip_id
    return f"{scene_id}__{render_clip.clip_id}"


def render_unit_kind(render_clip: RenderClip | None) -> str:
    return "render_clip" if render_clip is not None else "scene"


def clipped_shot_plan(plan: ShotPlan, render_clip: RenderClip | None) -> ShotPlan:
    """Return the shot-plan view that should be visible to one render unit."""

    if render_clip is None:
        return plan

    source_shot_ids = set(render_clip.source_shot_ids)
    shots = [
        shot
        for shot in plan.shots
        if not source_shot_ids or shot.shot_id in source_shot_ids
    ]
    shots = [shot.model_copy(update={"dialogue_lines": []}) for shot in shots]
    return plan.model_copy(
        update={
            "shots": shots,
            "total_estimated_duration_seconds": render_clip.target_duration_seconds,
        }
    )


def render_clip_time_note(render_clip: RenderClip | None) -> str | None:
    if render_clip is None:
        return None
    return (
        f"Render clip {render_clip.clip_id} covers scene time "
        f"{render_clip.start_time_seconds:g}-{render_clip.end_time_seconds:g}s."
    )


def render_clip_dialogue_lines(render_clip: RenderClip | None) -> list[str]:
    if render_clip is None:
        return []
    seen: set[str] = set()
    lines: list[str] = []
    for line in render_clip.dialogue_lines:
        cleaned = line.strip()
        if not cleaned:
            continue
        key = dialogue_line_key(cleaned)
        if key in seen:
            continue
        seen.add(key)
        lines.append(cleaned)
    return lines


def dialogue_line_key(line: str) -> str:
    """Normalize a speaker/dialogue line for duplicate detection."""

    text = line.translate(_SMART_QUOTES).strip()
    speaker = ""
    utterance = text
    if ":" in text:
        speaker, utterance = text.split(":", 1)
    utterance = _PARENTHETICAL_RE.sub(" ", utterance)
    normalized_speaker = _NON_WORD_RE.sub(" ", speaker.casefold()).strip()
    normalized_utterance = _NON_WORD_RE.sub(" ", utterance.casefold()).strip()
    if normalized_speaker:
        return f"{normalized_speaker}:{normalized_utterance}"
    return normalized_utterance


def remove_dialogue_quotes(text: str, dialogue_lines: Iterable[str]) -> str:
    """Remove exact quoted dialogue from action prose when dialogue has its own field."""

    cleaned = text.strip()
    if not cleaned:
        return cleaned
    candidates = sorted(_dialogue_quote_candidates(dialogue_lines), key=len, reverse=True)
    for candidate in candidates:
        if len(candidate) < 3:
            continue
        escaped = re.escape(candidate)
        cleaned = re.sub(
            rf"(['\"\u2018\u2019\u201c\u201d]){escaped}([.!?])?\1",
            "the planned dialogue line",
            cleaned,
            flags=re.I,
        )
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _dialogue_quote_candidates(dialogue_lines: Iterable[str]) -> set[str]:
    candidates: set[str] = set()
    for line in dialogue_lines:
        text = line.translate(_SMART_QUOTES).strip()
        utterance = text.split(":", 1)[1] if ":" in text else text
        utterance = _PARENTHETICAL_RE.sub(" ", utterance)
        utterance = re.sub(r"\s+", " ", utterance).strip()
        if not utterance:
            continue
        candidates.add(utterance)
        stripped = utterance.rstrip(".!?").strip()
        if stripped:
            candidates.add(stripped)
    return candidates
