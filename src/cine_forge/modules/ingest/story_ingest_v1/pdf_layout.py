"""Screenplay-aware cleanup for text extracted from PDF layout."""

from __future__ import annotations

import re
from typing import Any

TOKENIZED_TIME_WORDS = {
    "DAY",
    "NIGHT",
    "MORNING",
    "EVENING",
    "AFTERNOON",
    "DAWN",
    "DUSK",
    "LATER",
    "CONTINUOUS",
}
SCENE_HEAD_TOKENS = {"INT.", "EXT.", "INT/EXT.", "I/E.", "EST."}
SCENE_HEADING_LINE_RE = re.compile(
    r"^(INT\.|EXT\.|INT/EXT\.|I/E\.|EST\.)\s*[A-Z0-9]", flags=re.IGNORECASE
)
_LAYOUT_CHUNK_RE = re.compile(r"\S(?:.*?\S)?(?=\s{2,}|$)")
_CUE_RE = re.compile(r"^[A-Z0-9 .\-'()]+$")
_TABLE_HEADER_TOKENS = {
    "DATE",
    "DESCRIPTION",
    "ITEM",
    "LOCATION",
    "NAME",
    "OWNER",
    "REQUIREMENT",
    "ROLE",
    "STATUS",
    "VALUE",
}


def normalize_pdf_layout_text(text: str) -> str:
    normalized, _diagnostics = normalize_pdf_layout_text_with_diagnostics(text)
    return normalized


def normalize_pdf_layout_text_with_diagnostics(
    text: str,
) -> tuple[str, dict[str, Any]]:
    if not text:
        return "", {"dual_dialogue_reflow_count": 0}

    raw_lines, dual_dialogue_reflow_count = _reflow_dual_dialogue(text.splitlines())
    normalized_lines: list[str] = []
    blank_pending = False
    for raw_line in raw_lines:
        line = re.sub(r"\s+", " ", raw_line).strip()
        if not line:
            if normalized_lines:
                blank_pending = True
            continue
        if blank_pending:
            normalized_lines.append("")
            blank_pending = False
        normalized_lines.append(line)
    return "\n".join(normalized_lines).strip(), {
        "dual_dialogue_reflow_count": dual_dialogue_reflow_count,
    }


def repair_pdf_tokenized_layout(extracted: str) -> tuple[str, dict[str, Any]]:
    lines = [line.strip() for line in extracted.splitlines() if line.strip()]
    if not lines:
        return extracted, {"tokenized_layout_detected": False}

    single_word = sum(1 for line in lines if len(line.split()) == 1)
    avg_words = sum(len(line.split()) for line in lines) / max(len(lines), 1)
    tokenized_ratio = single_word / max(len(lines), 1)
    tokenized_layout = len(lines) >= 80 and tokenized_ratio >= 0.55 and avg_words <= 2.2
    diagnostics: dict[str, Any] = {
        "tokenized_layout_detected": tokenized_layout,
        "line_count": len(lines),
        "single_word_line_count": single_word,
        "single_word_line_ratio": round(tokenized_ratio, 3),
        "average_words_per_line": round(avg_words, 3),
    }
    if not tokenized_layout:
        return extracted, diagnostics

    merged = re.sub(r"\s+", " ", " ".join(lines)).strip()
    merged = re.sub(
        r"\s+(?=(?:FADE IN:|FADE OUT:|CUT TO:|DISSOLVE TO:|SMASH CUT TO:))",
        "\n",
        merged,
    )
    merged = re.sub(r"\s+(?=(?:INT\.|EXT\.|INT/EXT\.|I/E\.|EST\.)\s)", "\n", merged)
    merged = re.sub(
        (
            r"((?:INT\.|EXT\.|INT/EXT\.|I/E\.|EST\.)[^\n]{0,140}?"
            r"-\s*(?:DAY|NIGHT|MORNING|EVENING|AFTERNOON|DAWN|DUSK|LATER|CONTINUOUS))\s+"
        ),
        r"\1\n",
        merged,
        flags=re.IGNORECASE,
    )
    normalized = re.sub(r"\n{3,}", "\n\n", merged).strip()
    diagnostics["recovered_scene_heading_count"] = sum(
        1
        for line in normalized.splitlines()
        if line.split() and line.split()[0].upper() in SCENE_HEAD_TOKENS
    )
    return normalized, diagnostics


def repair_compact_screenplay_headings(text: str) -> tuple[str, dict[str, Any]]:
    if not text:
        return text, {"compact_heading_repairs": 0, "flashback_heading_breaks": 0}

    normalized, compact_repairs = _normalize_compact_lines(text)
    flashback_breaks = 0
    for anchor in ("BEGINFLASHBACK:", "ENDFLASHBACK.", "BACKTO PRESENT:"):
        updated = re.sub(
            rf"({re.escape(anchor)})\s*(INT\.|EXT\.|INT/EXT\.|I/E\.|EST\.)",
            r"\1\n\2",
            normalized,
            flags=re.IGNORECASE,
        )
        if updated != normalized:
            flashback_breaks += 1
            normalized = updated
    normalized, post_break_repairs = _normalize_compact_lines(normalized)
    return normalized, {
        "compact_heading_repairs": compact_repairs + post_break_repairs,
        "flashback_heading_breaks": flashback_breaks,
    }


def count_tokenized_scene_headings(lines: list[str]) -> int:
    tokens = [line.strip().upper() for line in lines if line.strip()]
    count = 0
    idx = 0
    while idx < len(tokens):
        if tokens[idx] in SCENE_HEAD_TOKENS:
            window = tokens[idx + 1 : idx + 14]
            if "-" in window and any(word in TOKENIZED_TIME_WORDS for word in window):
                count += 1
        idx += 1
    return count


def _reflow_dual_dialogue(lines: list[str]) -> tuple[list[str], int]:
    """Turn two visual dialogue columns into sequential Fountain dual dialogue."""
    output: list[str] = []
    reflow_count = 0
    index = 0
    known_cues = _known_single_column_cues(lines)
    while index < len(lines):
        cue_chunks = _layout_chunks(lines[index])
        if not _is_dual_cue_row(cue_chunks) or not _has_screenplay_context(
            lines, index
        ):
            output.append(lines[index])
            index += 1
            continue

        block_end = index + 1
        dialogue_rows: list[list[tuple[int, str]]] = []
        while (
            block_end < len(lines)
            and lines[block_end].strip()
            and not _is_screenplay_boundary(lines[block_end])
        ):
            dialogue_rows.append(_layout_chunks(lines[block_end]))
            block_end += 1
        left, right = _split_column_dialogue(cue_chunks, dialogue_rows)
        if not _looks_like_dual_dialogue(
            left,
            right,
            cue_chunks=cue_chunks,
            known_cues=known_cues,
        ):
            output.append(lines[index])
            index += 1
            continue

        output.extend([cue_chunks[0][1], *left, "", f"{cue_chunks[1][1]} ^", *right])
        reflow_count += 1
        index = block_end
    return output, reflow_count


def _layout_chunks(line: str) -> list[tuple[int, str]]:
    return [(match.start(), match.group()) for match in _LAYOUT_CHUNK_RE.finditer(line)]


def _is_dual_cue_row(chunks: list[tuple[int, str]]) -> bool:
    if len(chunks) != 2 or chunks[1][0] - chunks[0][0] < 15:
        return False
    return all(
        _looks_like_character_cue(text)
        and not set(text.split()) <= _TABLE_HEADER_TOKENS
        for _position, text in chunks
    )


def _has_screenplay_context(lines: list[str], cue_index: int) -> bool:
    """Require screenplay-shaped context before mutating ambiguous columns."""
    for previous in reversed(lines[:cue_index]):
        stripped = previous.strip()
        if not stripped:
            continue
        return bool(
            SCENE_HEADING_LINE_RE.match(stripped)
            or (re.search(r"[a-z]", stripped) and re.search(r"[.!?]$", stripped))
        )
    return False


def _is_screenplay_boundary(line: str) -> bool:
    stripped = re.sub(r"\s+", " ", line).strip()
    return bool(
        SCENE_HEADING_LINE_RE.match(stripped)
        or re.fullmatch(r"[A-Z][A-Z0-9 '\-]+TO:", stripped)
        or stripped.upper() in {"BEGIN FLASHBACK:", "END FLASHBACK.", "BACK TO PRESENT:"}
    )


def _looks_like_character_cue(text: str) -> bool:
    words = text.split()
    return (
        0 < len(words) <= 5
        and len(text) <= 35
        and bool(_CUE_RE.fullmatch(text))
        and text == text.upper()
        and not text.endswith("TO:")
    )


def _known_single_column_cues(lines: list[str]) -> set[str]:
    """Collect speaker names already proven by an ordinary dialogue block.

    Two arbitrary table headers followed by prose are textually indistinguishable
    from first-use dual dialogue after PDF coordinates are flattened. Requiring a
    prior single-column dialogue use is intentionally conservative: ambiguous
    source stays unchanged instead of being rewritten into false dialogue.
    """
    cues: set[str] = set()
    for index, line in enumerate(lines):
        chunks = _layout_chunks(line)
        if len(chunks) != 1 or not _looks_like_character_cue(chunks[0][1]):
            continue
        for following in lines[index + 1 :]:
            stripped = following.strip()
            if not stripped:
                continue
            if _is_screenplay_boundary(following) or len(_layout_chunks(following)) != 1:
                break
            if re.search(r"[a-z]", stripped):
                cues.add(chunks[0][1])
            break
    return cues


def _split_column_dialogue(
    cue_chunks: list[tuple[int, str]],
    rows: list[list[tuple[int, str]]],
) -> tuple[list[str], list[str]]:
    boundary = (cue_chunks[0][0] + cue_chunks[1][0]) / 2
    left: list[str] = []
    right: list[str] = []
    for chunks in rows:
        for position, text in chunks:
            (left if position < boundary else right).append(text)
    return left, right


def _looks_like_dual_dialogue(
    left: list[str],
    right: list[str],
    *,
    cue_chunks: list[tuple[int, str]],
    known_cues: set[str],
) -> bool:
    """Require prose-like content in both columns before mutating source order.

    Balanced tables often use two uppercase headings followed by two populated
    uppercase columns, which is visually identical to dual dialogue at the
    coordinate level. Requiring lowercase language in each side deliberately
    prefers preserving an unusual all-caps dialogue block over corrupting a
    non-dialogue table.
    """
    return (
        bool(left and right)
        and all(cue in known_cues for _position, cue in cue_chunks)
        and all(
            any(re.search(r"[a-z]", line) for line in column)
            for column in (left, right)
        )
    )


def _normalize_compact_lines(raw_text: str) -> tuple[str, int]:
    repair_count = 0
    updated_lines: list[str] = []
    for line in raw_text.splitlines():
        candidate = line
        spaced = re.sub(
            r"^(INT\.|EXT\.|INT/EXT\.|I/E\.|EST\.)(?=[A-Z0-9])",
            r"\1 ",
            candidate,
            flags=re.IGNORECASE,
        )
        if spaced != candidate:
            repair_count += 1
            candidate = spaced
        if SCENE_HEADING_LINE_RE.match(candidate.strip()):
            dashed = re.sub(r"\s*-\s*", " - ", candidate)
            if dashed != candidate:
                repair_count += 1
                candidate = dashed
        updated_lines.append(candidate)
    return "\n".join(updated_lines), repair_count
