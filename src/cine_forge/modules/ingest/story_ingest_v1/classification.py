"""Deterministic structural classification for ingested creative text."""

from __future__ import annotations

import re
from typing import Any

from cine_forge.modules.ingest.story_ingest_v1.pdf_layout import (
    SCENE_HEADING_LINE_RE,
    count_tokenized_scene_headings,
)

_TRANSITION_RE = re.compile(r"^[A-Z][A-Z0-9 '\-]+TO:$")
_PARENTHETICAL_RE = re.compile(r"^\([^)]+\)$")
_BULLET_RE = re.compile(r"^(\-|\*|\+)\s+\S+")
_NUMBERED_RE = re.compile(r"^\d+[.)]\s+\S+")
_COLON_HEADING_RE = re.compile(r"^[A-Za-z][^:]{1,40}:\s+\S+")
_ALL_CAPS_RE = re.compile(r"^[A-Z0-9 .'\-()]+$")
_SENTENCE_RE = re.compile(r"[A-Za-z][^.!?]*[.!?]")


def classify_format(content: str, file_format: str) -> dict[str, Any]:
    classification, _ = classify_format_with_diagnostics(content, file_format)
    return classification


def classify_format_with_diagnostics(
    content: str, file_format: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Classify ingested content from observable structure and conservative priors."""
    if file_format == "fdx":
        return _fdx_classification()

    lines = [line.rstrip() for line in content.splitlines()]
    non_empty = [line for line in lines if line.strip()]
    paragraphs = _paragraph_blocks(lines)
    signals = _measure_signals(non_empty, paragraphs)
    scores = _score_formats(signals, file_format)
    label, confidence = _select_label(scores)
    evidence = _build_evidence(signals, file_format)

    return {
        "detected_format": label,
        "confidence": round(confidence, 3),
        "evidence": evidence or ["No strong structural signals were detected"],
    }, {
        "line_counts": {
            "total_lines": len(lines),
            "non_empty_lines": len(non_empty),
            "single_word_lines": signals["single_word_lines"],
            "paragraph_blocks": len(paragraphs),
        },
        "signals": {
            "scene_headings": signals["scene_headings"],
            "character_cues": signals["character_cues"],
            "transitions": signals["transitions"],
            "parentheticals": signals["parentheticals"],
            "prose_paragraphs": signals["prose_paragraphs"],
            "tokenized_heading_sequences": signals["tokenized_heading_sequences"],
        },
        "score_breakdown": {name: round(score, 3) for name, score in scores.items()},
    }


def _fdx_classification() -> tuple[dict[str, Any], dict[str, Any]]:
    return {
        "detected_format": "screenplay",
        "confidence": 0.99,
        "evidence": ["File extension is .fdx, a screenplay-oriented XML format"],
    }, {"score_breakdown": {"screenplay": 0.99, "prose": 0.0, "notes": 0.0}}


def _measure_signals(non_empty: list[str], paragraphs: list[str]) -> dict[str, int]:
    scene_headings = sum(
        1 for line in non_empty if SCENE_HEADING_LINE_RE.match(line.strip())
    )
    transitions = sum(1 for line in non_empty if _TRANSITION_RE.match(line.strip()))
    character_cues = sum(1 for line in non_empty if _looks_like_character_cue(line))
    bullets = sum(1 for line in non_empty if _BULLET_RE.match(line.strip()))
    numbered = sum(1 for line in non_empty if _NUMBERED_RE.match(line.strip()))
    prose_paragraphs = sum(
        1
        for block in paragraphs
        if len(block.split()) >= 16 and not _ALL_CAPS_RE.match(block.strip())
    )
    prose_lines = sum(
        1
        for line in non_empty
        if len(line.split()) >= 8
        and re.search(r"[a-z]", line)
        and not _BULLET_RE.match(line.strip())
        and not _NUMBERED_RE.match(line.strip())
        and not _ALL_CAPS_RE.match(line.strip())
    )
    return {
        "non_empty_lines": max(len(non_empty), 1),
        "paragraph_blocks": max(len(paragraphs), 1),
        "scene_headings": scene_headings,
        "transitions": transitions,
        "parentheticals": sum(
            1 for line in non_empty if _PARENTHETICAL_RE.match(line.strip())
        ),
        "character_cues": character_cues,
        "bullets": bullets,
        "numbered": numbered,
        "colon_headings": sum(
            1 for line in non_empty if _COLON_HEADING_RE.match(line.strip())
        ),
        "short_fragments": sum(1 for line in non_empty if len(line.split()) <= 6),
        "single_word_lines": sum(1 for line in non_empty if len(line.split()) == 1),
        "prose_paragraphs": prose_paragraphs,
        "sentence_like_paragraphs": sum(
            1 for block in paragraphs if len(_SENTENCE_RE.findall(block)) >= 2
        ),
        "prose_lines": prose_lines,
        "tokenized_heading_sequences": count_tokenized_scene_headings(non_empty),
    }


def _score_formats(signals: dict[str, int], file_format: str) -> dict[str, float]:
    line_count = signals["non_empty_lines"]
    paragraph_count = signals["paragraph_blocks"]
    single_word_ratio = _ratio(signals["single_word_lines"], line_count)
    cue_weight = max(0.1, 1.0 - (single_word_ratio * 0.85))
    has_screenplay_structure = any(
        signals[name]
        for name in (
            "scene_headings",
            "transitions",
            "parentheticals",
            "tokenized_heading_sequences",
        )
    )
    screenplay_prior = 0.35 if file_format == "fountain" else 0.0
    if file_format in {"docx", "pdf"} and has_screenplay_structure:
        screenplay_prior = 0.35

    screenplay = min(
        1.0,
        0.45 * _ratio(signals["scene_headings"], line_count)
        + 0.2 * _ratio(signals["character_cues"], line_count) * cue_weight
        + 0.2 * _ratio(signals["transitions"], line_count)
        + 0.1 * _ratio(signals["parentheticals"], line_count)
        + min(0.6, signals["scene_headings"] * 0.06)
        + min(0.25, signals["transitions"] * 0.05)
        + min(0.5, signals["tokenized_heading_sequences"] * 0.18)
        + screenplay_prior,
    )
    notes = min(
        1.0,
        0.45 * _ratio(signals["bullets"] + signals["numbered"], line_count)
        + 0.15 * _ratio(signals["colon_headings"], line_count)
        + 0.2 * _ratio(signals["short_fragments"], line_count),
    )
    prose = min(
        1.0,
        0.65 * _ratio(signals["prose_paragraphs"], paragraph_count)
        + 0.25 * _ratio(signals["sentence_like_paragraphs"], paragraph_count)
        + 0.2 * _ratio(signals["prose_lines"], line_count)
        - 0.3
        * _ratio(signals["scene_headings"] + signals["character_cues"], line_count)
        - min(0.7, signals["scene_headings"] * 0.07)
        - min(0.3, signals["transitions"] * 0.05)
        - 0.5 * _ratio(signals["bullets"] + signals["numbered"], line_count)
        - 0.6 * single_word_ratio
        - min(0.45, signals["tokenized_heading_sequences"] * 0.16),
    )
    return {"screenplay": screenplay, "prose": max(0.0, prose), "notes": notes}


def _select_label(scores: dict[str, float]) -> tuple[str, float]:
    if scores["screenplay"] >= 0.45 and scores["prose"] >= 0.35:
        return "hybrid", min(0.95, (scores["screenplay"] + scores["prose"]) / 2)

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    top_label, top_score = ranked[0]
    margin = max(0.0, top_score - ranked[1][1])
    confidence = min(0.99, max(0.2, top_score + (margin * 0.4)))
    return (top_label if top_score >= 0.3 else "unknown"), confidence


def _build_evidence(signals: dict[str, int], file_format: str) -> list[str]:
    evidence: list[str] = []
    if signals["scene_headings"]:
        evidence.append(
            f"Detected {signals['scene_headings']} scene headings (INT./EXT./EST.)"
        )
    if signals["character_cues"]:
        evidence.append(
            f"Detected {signals['character_cues']} uppercase character cue candidates"
        )
    if signals["transitions"]:
        evidence.append(
            f"Detected {signals['transitions']} screenplay transition lines ending with TO:"
        )
    if signals["bullets"] or signals["numbered"]:
        evidence.append(
            "Detected note-style list structure "
            f"({signals['bullets']} bullets, {signals['numbered']} numbered items)"
        )
    if signals["prose_paragraphs"]:
        evidence.append(
            f"Detected {signals['prose_paragraphs']} long narrative-style paragraphs"
        )
    if signals["tokenized_heading_sequences"]:
        evidence.append(
            "Detected tokenized screenplay heading patterns "
            f"({signals['tokenized_heading_sequences']} heading sequences)"
        )
    line_count = signals["non_empty_lines"]
    if _ratio(signals["single_word_lines"], line_count) >= 0.45:
        evidence.append(
            "Detected extraction noise with many single-word lines "
            f"({signals['single_word_lines']}/{line_count})"
        )
    if file_format in {"fountain", "fdx"}:
        evidence.append(f"File extension is .{file_format}, a screenplay-oriented format")
    return evidence


def _looks_like_character_cue(line: str) -> bool:
    text = line.strip()
    if not text or len(text) > 35 or not _ALL_CAPS_RE.match(text):
        return False
    words = [word for word in text.split() if word]
    return bool(words) and len(words) <= 4 and all(
        any(char.isalpha() for char in word) for word in words
    )


def _ratio(count: int, total: int) -> float:
    return count / total if total > 0 else 0.0


def _paragraph_blocks(lines: list[str]) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped:
            current.append(stripped)
        elif current:
            blocks.append(" ".join(current))
            current = []
    if current:
        blocks.append(" ".join(current))
    return blocks
