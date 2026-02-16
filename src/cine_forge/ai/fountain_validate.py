"""Deterministic Fountain-style normalization and lint checks."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

SCENE_PREFIXES = ("INT.", "EXT.", "INT/EXT.", "EST.")


@dataclass(frozen=True)
class FountainLintResult:
    """Structural lint output for canonical screenplay text."""

    valid: bool
    issues: list[str] = field(default_factory=list)


def normalize_fountain_text(text: str) -> str:
    """Normalize line endings, heading/cue casing, and screenplay spacing."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    raw_lines = [line.rstrip() for line in normalized.split("\n")]

    # Strip markdown blockquote prefixes that LLMs sometimes add to dialogue
    raw_lines = [
        line.lstrip("> ").lstrip(">") if line.lstrip().startswith(">") else line
        for line in raw_lines
    ]
    # Strip markdown escape sequences (\- \! \\)
    raw_lines = [
        line.replace("\\-", "-").replace("\\!", "!") for line in raw_lines
    ]

    processed: list[str] = []
    previous_blank = True
    for idx, line in enumerate(raw_lines):
        stripped = line.strip()
        if not stripped:
            if not previous_blank:
                processed.append("")
            previous_blank = True
            continue

        line_out = stripped
        if _is_scene_heading(stripped):
            line_out = stripped.upper()
            if processed and processed[-1] != "":
                processed.append("")
        elif _looks_like_character_candidate(stripped, raw_lines, idx):
            line_out = stripped.upper()
            if processed and processed[-1] != "":
                processed.append("")
        processed.append(line_out)
        previous_blank = False

    return "\n".join(processed).strip() + ("\n" if processed else "")


def lint_fountain_text(text: str) -> FountainLintResult:
    """Validate screenplay structure with lightweight deterministic checks."""
    issues: list[str] = []
    lines = text.splitlines()
    if not lines:
        return FountainLintResult(valid=False, issues=["Script is empty"])

    # Skip all lines before the first scene heading — these are title/metadata
    first_scene_idx = _find_first_scene_heading(lines)

    scene_count = 0
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if _is_scene_heading(stripped):
            scene_count += 1
        # Skip character cue checks before the first scene heading
        if idx < first_scene_idx:
            continue
        if _looks_like_character_cue(stripped):
            if idx + 1 >= len(lines):
                issues.append(f"Orphaned character cue at line {idx + 1}")
            else:
                next_line = lines[idx + 1].strip()
                if (
                    not next_line
                    or _is_scene_heading(next_line)
                    or _looks_like_character_cue(next_line)
                ):
                    issues.append(f"Character cue without dialogue at line {idx + 1}")
        if (
            idx >= first_scene_idx
            and (stripped.endswith(":") or stripped.endswith("."))
            and stripped == stripped.upper()
            and any(c.isalpha() for c in stripped)
            and not _is_valid_transition(stripped)
            and not _is_valid_transition(stripped.rstrip("."))
            and not _is_scene_heading(stripped)
        ):
            issues.append(f"Malformed transition line at line {idx + 1}")

    if scene_count == 0:
        issues.append("No scene headings detected (expected INT./EXT. style headings)")

    return FountainLintResult(valid=not issues, issues=issues)


def _is_scene_heading(line: str) -> bool:
    upper = line.upper()
    return upper.startswith(SCENE_PREFIXES)


def _looks_like_character_cue(line: str) -> bool:
    if len(line) > 35 or len(line.split()) > 4:
        return False
    # Parentheticals are NOT character cues
    if line.startswith("("):
        return False
    if not re.match(r"^[A-Za-z0-9 .'\-()]+$", line):
        return False
    letters = [char for char in line if char.isalpha()]
    if not letters:
        return False
    if not (line.upper() == line) or _is_scene_heading(line):
        return False
    # Exclude known transitions and narrative markers
    if _is_valid_transition(line) or _is_valid_transition(line.rstrip(".")):
        return False
    return True


def _looks_like_character_candidate(line: str, lines: list[str], index: int) -> bool:
    stripped = line.strip()
    if not stripped or len(stripped) > 35 or len(stripped.split()) > 4:
        return False
    if stripped.startswith("("):
        return False
    if _is_scene_heading(stripped):
        return False
    if not re.match(r"^[A-Za-z0-9 .'\-()]+$", stripped):
        return False
    if index + 1 >= len(lines):
        return False
    next_line = lines[index + 1].strip()
    if not next_line or _is_scene_heading(next_line):
        return False
    return True


def _find_first_scene_heading(lines: list[str]) -> int:
    """Return the index of the first scene heading line."""
    for idx, line in enumerate(lines):
        if _is_scene_heading(line.strip()):
            return idx
    return len(lines)


# Standard Fountain transitions and narrative markers
_VALID_TRANSITIONS = re.compile(
    r"^("
    r"[A-Z][A-Z0-9 '\-]+TO:[.:]?"
    r"|FADE IN[.:]?"
    r"|FADE OUT[.:]?"
    r"|FADE TO BLACK[.:]?"
    r"|CUT TO BLACK[.:]?"
    r"|SMASH CUT[.:]?"
    r"|MATCH CUT[.:]?"
    r"|INTERCUT[.:]?"
    r"|END CREDITS[.:]?"
    r"|TITLE CARD[.:]?"
    r"|SUPER[.:]?"
    r"|OPENING TITLE[S]?[.:]?"
    r"|CLOSING TITLE[S]?[.:]?"
    r"|THE END[.:]?"
    r"|BEGIN FLASHBACK[.:]?"
    r"|END FLASHBACK[.:]?"
    r"|BACK TO PRESENT[.:]?"
    r"|BACK TO SCENE[.:]?"
    r")$",
    re.IGNORECASE,
)


def _is_valid_transition(line: str) -> bool:
    """Check if a colon-terminated line is a standard screenplay transition."""
    return bool(_VALID_TRANSITIONS.match(line))
