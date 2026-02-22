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
    """Normalize line endings, heading/cue casing, and screenplay spacing.
    
    Strictly enforces:
    - Metadata at top
    - 1 blank line before scene headings
    - 1 blank line before character cues
    - 0 blank lines within a dialogue block (char -> paren -> dialogue)
    - 1 blank line after dialogue block
    """
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    raw_lines = [line.rstrip() for line in normalized.split("\n")]

    # 1. Strip markdown artifacts
    raw_lines = [
        line.lstrip("> ").lstrip(">") if line.lstrip().startswith(">") else line
        for line in raw_lines
    ]
    raw_lines = [
        line.replace("\\-", "-").replace("\\!", "!") for line in raw_lines
    ]

    # 2. Clean/Heal metadata block
    processed_lines = clean_fountain_metadata(raw_lines)

    # 3. Identify and tag elements
    elements: list[tuple[str, str]] = []
    in_metadata = True
    
    for idx, line in enumerate(processed_lines):
        # Metadata check must happen BEFORE stripping to catch indentation
        if in_metadata:
            # Metadata is 'Key: Value' or an indented line following a key
            # Or loose text at the very top that isn't a screenplay element
            is_key_value = re.match(r"^[A-Za-z][A-Za-z ]{1,20}:\s*", line.lstrip())
            is_indented = line.startswith("    ")
            
            if is_key_value or is_indented:
                elements.append(("metadata", line.rstrip()))
                continue
            elif not line.strip():
                # End of metadata block on first blank line
                in_metadata = False
                continue
            else:
                # If we are at the very top and it's not a screenplay element,
                # keep it in metadata.
                stripped_tmp = line.strip()
                if not (
                    _is_scene_heading(stripped_tmp) 
                    or _looks_like_character_candidate(stripped_tmp, processed_lines, idx)
                ):
                    elements.append(("metadata", line.rstrip()))
                    continue
                in_metadata = False
                
        stripped = line.strip()
        if not stripped:
            continue
                
        # Body elements
        if _is_scene_heading(stripped):
            elements.append(("heading", stripped.upper()))
        elif _looks_like_character_cue(stripped) or _looks_like_character_candidate(
            stripped, processed_lines, idx
        ):
            elements.append(("character", stripped.upper()))
        elif stripped.startswith("(") and stripped.endswith(")"):
            # Check if this is a valid parenthetical (preceded by char or paren)
            prev_type = elements[-1][0] if elements else None
            if prev_type in ("character", "parenthetical", "dialogue"):
                elements.append(("parenthetical", stripped))
            else:
                elements.append(("action", stripped))
        elif _is_valid_transition(stripped) or _is_valid_transition(stripped.rstrip(".")):
            elements.append(("transition", stripped.upper()))
        else:
            # Check if this is dialogue (preceded by char or paren)
            prev_type = elements[-1][0] if elements else None
            if prev_type in ("character", "parenthetical", "dialogue"):
                elements.append(("dialogue", stripped))
            else:
                elements.append(("action", stripped))

    # 4. Reconstruct with correct spacing
    final_lines: list[str] = []
    for i, (etype, content) in enumerate(elements):
        if etype == "metadata":
            final_lines.append(content)
            continue
            
        # Add spacing before body elements
        if i > 0:
            prev_type = elements[i-1][0]
            
            # Rule: No blank lines within a dialogue block
            # (Character -> Parenthetical -> Dialogue -> Parenthetical -> ...)
            is_dialogue_flow = (
                prev_type in ("character", "parenthetical", "dialogue")
                and etype in ("parenthetical", "dialogue")
            )
            
            # Rule: No blank lines between metadata lines
            is_metadata_flow = (
                prev_type == "metadata" and etype == "metadata"
            )
            
            if etype != "metadata" and prev_type == "metadata":
                # 1 blank line after the entire metadata block
                final_lines.append("")
            elif not is_dialogue_flow and not is_metadata_flow:
                final_lines.append("")
                
        final_lines.append(content)

    return "\n".join(final_lines).strip() + ("\n" if final_lines else "")


def clean_fountain_metadata(lines: list[str]) -> list[str]:
    """Capture all non-screenplay text at the start of the file as metadata.
    
    Continues until the first definitive screenplay element (Heading, Character, 
    or common start-of-script marker like TEASER/FADE IN) is encountered.
    """
    if not lines:
        return []
        
    metadata_map: dict[str, list[str]] = {}
    # Strict whitelist of standard Fountain keys supported by renderers
    standard_keys = {
        "Title", "Author", "Authors", "Source", "Credit", "Draft date", 
        "Contact", "Notes"
    }
    
    # definitive body markers (usually on their own line)
    body_markers = {"TEASER", "FADE IN", "ACT ONE"}
    
    collected_metadata_lines: list[str] = []
    body_start_idx = 0
    
    # 1. Identify definitive script body start
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
            
        upper = stripped.upper().rstrip(":")
        # It's a body element if it's a heading, a character cue, or a standalone marker
        is_body = (
            _is_scene_heading(stripped) 
            or _looks_like_character_candidate(stripped, lines, idx)
            or upper in body_markers
        )
        
        if is_body:
            body_start_idx = idx
            break
        else:
            collected_metadata_lines.append(line)
            body_start_idx = idx + 1
            
    if not collected_metadata_lines:
        return lines
        
    # 2. Parse collected lines into keys
    current_key: str | None = None
    for line in collected_metadata_lines:
        stripped = line.strip()
        if not stripped:
            continue
            
        # Match 'Key: Value'. Only accept standard keys to avoid misidentifying titles.
        match = re.match(r"^([A-Za-z ]{1,25}):\s*(.*)", stripped)
        if match and match.group(1).strip().title() in standard_keys:
            key = match.group(1).strip().title()
            value = match.group(2).strip()
            if key not in metadata_map:
                metadata_map[key] = []
            if value:
                metadata_map[key].append(value)
            current_key = key
        else:
            # Not a standard Key: Value line. 
            # If we are at the top, it's the Title.
            if not metadata_map and not current_key:
                metadata_map["Title"] = [stripped]
                current_key = "Title"
            elif current_key:
                metadata_map[current_key].append(stripped)
            else:
                metadata_map["Title"] = [stripped]
                current_key = "Title"

    # 3. Reconstruct block
    output_lines: list[str] = []
    
    # Output standard keys in order
    order = ["Title", "Author", "Authors", "Source", "Credit", "Draft date", "Contact", "Notes"]
    for k in order:
        if k in metadata_map:
            vals = metadata_map[k]
            if len(vals) == 1:
                output_lines.append(f"{k}: {vals[0]}")
            else:
                # Put first value on same line as key, subsequent lines indented
                output_lines.append(f"{k}: {vals[0]}")
                for v in vals[1:]:
                    output_lines.append(f"    {v}")
                    
    # Return contiguous metadata + 1 blank line + rest of script
    return output_lines + [""] + lines[body_start_idx:]


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
    if len(line) > 35 or len(line.split()) > 5:
        return False
    # Parentheticals are NOT character cues
    if line.startswith("("):
        return False
    # Support smart quotes, standard extensions, commas, slashes, ampersands
    if not re.match(r"^[A-Za-z0-9 .'\-()’,/&]+$", line):
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
    if not stripped or len(stripped) > 35 or len(stripped.split()) > 5:
        return False
    if stripped.startswith("("):
        return False
    if _is_scene_heading(stripped):
        return False
    # Support smart quotes, commas, etc.
    if not re.match(r"^[A-Za-z0-9 .'\-()’,/&]+$", stripped):
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
