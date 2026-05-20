"""Dialogue timing and exact-line prompt contracts for render adapter generation."""

from __future__ import annotations

import re
from typing import Any

from cine_forge.modules.generation.render_adapter_v1.render_units import (
    render_clip_dialogue_lines,
)
from cine_forge.schemas import RenderClip, ShotPlan


def _exact_dialogue_lines_for_shot(shot: Any) -> list[str]:
    return [
        line.strip()
        for line in getattr(shot, "dialogue_lines", [])
        if isinstance(line, str) and line.strip()
    ]


def _exact_dialogue_lines_for_plan(plan: ShotPlan) -> list[str]:
    seen: set[str] = set()
    lines: list[str] = []
    for shot in plan.shots:
        for line in _exact_dialogue_lines_for_shot(shot):
            if line in seen:
                continue
            seen.add(line)
            lines.append(line)
    return lines


def _ensure_dialogue_prompt_contract(
    prompt_text: str,
    plan: ShotPlan,
    *,
    duration_seconds: float,
    render_clip: RenderClip | None = None,
) -> tuple[str, list[str]]:
    dialogue_lines = _exact_dialogue_lines_for_render_unit(plan, render_clip)
    if not dialogue_lines:
        return prompt_text, []

    notes: list[str] = []
    normalized_prompt = _normalize_dialogue_text(prompt_text)
    missing = [
        line
        for line in dialogue_lines
        if _normalize_dialogue_text(line) not in normalized_prompt
    ]
    updated_prompt = prompt_text.rstrip()
    if missing:
        updated_prompt += "\n\n" + _dialogue_timing_contract(
            plan,
            duration_seconds=duration_seconds,
            render_clip=render_clip,
        )
        sample = "; ".join(missing[:3])
        if len(missing) > 3:
            sample += f"; +{len(missing) - 3} more"
        punctuation = "" if sample.endswith((".", "!", "?")) else "."
        notes.append(
            "Adapter appended a dialogue timing contract from the shot plan because "
            f"the compiler omitted: {sample}{punctuation}"
        )

    cadence_guidance, cadence_note = _dialogue_cadence_guidance(
        dialogue_lines=dialogue_lines,
        duration_seconds=duration_seconds,
    )
    normalized_updated = _normalize_dialogue_text(updated_prompt)
    normalized_cadence = _normalize_dialogue_text(cadence_guidance)
    if cadence_guidance and normalized_cadence not in normalized_updated:
        updated_prompt += "\n\n" + cadence_guidance
        notes.append(cadence_note)

    return updated_prompt, notes


def _exact_dialogue_lines_for_render_unit(
    plan: ShotPlan,
    render_clip: RenderClip | None,
) -> list[str]:
    if render_clip is not None:
        return render_clip_dialogue_lines(render_clip)
    return _exact_dialogue_lines_for_plan(plan)


def _dialogue_timing_contract(
    plan: ShotPlan,
    *,
    duration_seconds: float | None,
    render_clip: RenderClip | None = None,
) -> str:
    dialogue_lines = _exact_dialogue_lines_for_render_unit(plan, render_clip)
    if not dialogue_lines:
        return ""
    lines = [
        "Dialogue timing / exact lines:",
        (
            "- Single dialogue pass: include each line once, in this order, "
            "with one speaker at a time."
        ),
        (
            "- Cadence: leave a visible breath or reaction beat after each line; "
            "honor any planned silence or stillness cues from the shot action."
        ),
    ]
    density_guidance, _ = _dialogue_cadence_guidance(
        dialogue_lines=dialogue_lines,
        duration_seconds=duration_seconds,
    )
    if density_guidance:
        lines.append("- " + density_guidance.removeprefix("Dialogue cadence: "))
    if render_clip is not None:
        lines.append(
            f"- {render_clip.clip_id} "
            f"(render clip, about {render_clip.target_duration_seconds:.1f}s):"
        )
        for line in dialogue_lines:
            lines.append(f"  - {line}")
        return "\n".join(lines)

    for shot in plan.shots:
        dialogue = _exact_dialogue_lines_for_shot(shot)
        if not dialogue:
            continue
        lines.append(
            f"- {shot.shot_id} ({shot.shot_size}, about {shot.duration_estimate_seconds:.1f}s):"
        )
        for line in dialogue:
            lines.append(f"  - {line}")
    return "\n".join(lines)


def _dialogue_cadence_guidance(
    *,
    dialogue_lines: list[str],
    duration_seconds: float | None,
) -> tuple[str, str]:
    if not dialogue_lines:
        return "", ""
    estimated_spoken_seconds = _estimated_dialogue_seconds(dialogue_lines)
    if duration_seconds and estimated_spoken_seconds > (duration_seconds * 0.8):
        return (
            "Dialogue cadence: This is dialogue-dense for the requested "
            f"{duration_seconds:g}s clip; keep delivery terse but distinct, with clear "
            "breaths and reaction beats instead of back-to-back rapid-fire speech.",
            "Adapter added dialogue cadence guidance because the exact line count is dense "
            f"for the requested {duration_seconds:g}s render.",
        )
    return (
        "Dialogue cadence: Deliver the exact lines with distinct breaths and reaction beats, "
        "one speaker at a time.",
        "Adapter added dialogue cadence guidance for exact scripted lines.",
    )


def _estimated_dialogue_seconds(dialogue_lines: list[str]) -> float:
    word_count = 0
    for line in dialogue_lines:
        utterance = line.split(":", 1)[1] if ":" in line else line
        word_count += len(re.findall(r"[A-Za-z0-9']+", utterance))
    spoken_seconds = word_count / 2.7
    reaction_beats = max(len(dialogue_lines) - 1, 0) * 0.35
    return spoken_seconds + reaction_beats


def _normalize_dialogue_text(text: str) -> str:
    normalized = (
        text.replace("\u2018", "'")
        .replace("\u2019", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace('"', "")
        .replace("`", "")
    )
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = re.sub(r"\s+([:;,.!?])", r"\1", normalized)
    normalized = re.sub(r":\s*", ": ", normalized)
    return normalized.strip().casefold()
