"""Helper utilities for design-study router state mutation and composition context."""

from __future__ import annotations

from textwrap import shorten
from typing import NamedTuple

from fastapi import HTTPException

from cine_forge.schemas.design_study import (
    DesignStudyImage,
    DesignStudyRound,
    DesignStudyState,
    ImageDecision,
)

_PROMPT_EXCERPT_WIDTH = 180


class CompositionContext(NamedTuple):
    positive_refs: list[str]
    negative_refs: list[str]
    positive_reference_lines: list[str]
    negative_reference_lines: list[str]


def find_round_image(
    state: DesignStudyState,
    filename: str,
) -> tuple[DesignStudyRound, DesignStudyImage]:
    for round_ in state.rounds:
        for image in round_.images:
            if image.filename == filename:
                return round_, image
    raise HTTPException(
        status_code=404,
        detail=f"Image '{filename}' not found in design study state.",
    )


def resolve_composition_context(
    state: DesignStudyState,
    *,
    positive_refs: list[str] | None,
    negative_refs: list[str] | None,
) -> CompositionContext:
    normalized_positive = _normalize_reference_filenames(positive_refs)
    normalized_negative = _normalize_reference_filenames(negative_refs)
    overlap = sorted(set(normalized_positive).intersection(normalized_negative))
    if overlap:
        joined = ", ".join(overlap)
        raise HTTPException(
            status_code=400,
            detail=f"Composition references cannot be both positive and negative: {joined}",
        )

    return CompositionContext(
        positive_refs=normalized_positive,
        negative_refs=normalized_negative,
        positive_reference_lines=_reference_prompt_lines(state, normalized_positive),
        negative_reference_lines=_reference_prompt_lines(state, normalized_negative),
    )


def apply_image_decision(
    state: DesignStudyState,
    *,
    filename: str,
    decision: ImageDecision,
    guidance: str | None,
) -> tuple[DesignStudyRound, DesignStudyImage, str | None]:
    auto_cleared_final_filename: str | None = None
    if decision == "selected_final":
        for round_ in state.rounds:
            for image in round_.images:
                if image.filename != filename and image.decision == "selected_final":
                    image.decision = "pending"
                    image.guidance = None
                    auto_cleared_final_filename = image.filename

    round_, image = find_round_image(state, filename)
    image.decision = decision
    if decision == "pending":
        image.guidance = None
    elif guidance is not None:
        image.guidance = guidance

    if decision == "selected_final":
        state.selected_final_filename = filename
    elif state.selected_final_filename == filename:
        state.selected_final_filename = None

    return round_, image, auto_cleared_final_filename


def _normalize_reference_filenames(filenames: list[str] | None) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for filename in filenames or []:
        cleaned = filename.strip()
        if not cleaned or cleaned in seen:
            continue
        normalized.append(cleaned)
        seen.add(cleaned)
    return normalized


def _reference_prompt_lines(
    state: DesignStudyState,
    filenames: list[str],
) -> list[str]:
    lines: list[str] = []
    seen: set[str] = set()
    for filename in filenames:
        round_, image = find_round_image(state, filename)
        line = _reference_context_line(round_, image)
        if line in seen:
            continue
        lines.append(line)
        seen.add(line)
    return lines


def _reference_context_line(
    round_: DesignStudyRound,
    image: DesignStudyImage,
) -> str:
    parts: list[str] = []
    if round_.directive:
        parts.append(f"Round directive: {_ensure_sentence(round_.directive)}")
    if image.guidance:
        parts.append(f"Image note: {_ensure_sentence(image.guidance)}")
    prompt_excerpt = _prompt_excerpt(image.prompt_used)
    if prompt_excerpt:
        parts.append(f"Prompt anchor: {_ensure_sentence(prompt_excerpt)}")
    return " ".join(_dedupe(parts))


def _prompt_excerpt(prompt_used: str) -> str:
    normalized = " ".join(prompt_used.split())
    if not normalized:
        return ""
    return shorten(normalized, width=_PROMPT_EXCERPT_WIDTH, placeholder="…")


def _ensure_sentence(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        return ""
    if cleaned.endswith((".", "!", "?")):
        return cleaned
    return f"{cleaned}."


def _dedupe(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = " ".join(value.strip().lower().split())
        if not normalized or normalized in seen:
            continue
        deduped.append(value)
        seen.add(normalized)
    return deduped
