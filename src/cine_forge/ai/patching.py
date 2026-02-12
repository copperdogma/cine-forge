"""Search/replace patch parsing and robust application helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher


@dataclass(frozen=True)
class SearchReplacePatch:
    """Single SEARCH/REPLACE patch block."""

    search: str
    replace: str


def parse_search_replace_blocks(text: str) -> list[SearchReplacePatch]:
    """Parse Aider-style SEARCH/REPLACE patch blocks from plain text."""
    pattern = re.compile(
        r"<<<<<<<\s*SEARCH\s*\n(.*?)\n=======\n(.*?)\n>>>>>>>\s*REPLACE",
        flags=re.DOTALL,
    )
    patches: list[SearchReplacePatch] = []
    for match in pattern.finditer(text):
        search = match.group(1)
        replace = match.group(2)
        patches.append(SearchReplacePatch(search=search, replace=replace))
    return patches


def apply_search_replace_patches(
    original: str,
    patches: list[SearchReplacePatch],
    fuzzy_threshold: float = 0.85,
) -> tuple[str, list[str]]:
    """Apply patches with exact, whitespace-normalized, then fuzzy matching."""
    updated = original
    failures: list[str] = []
    for idx, patch in enumerate(patches, start=1):
        if not patch.search:
            failures.append(f"patch_{idx}: empty SEARCH block")
            continue

        applied, new_text = _apply_exact(updated, patch)
        if applied:
            updated = new_text
            continue

        applied, new_text = _apply_whitespace_normalized(updated, patch)
        if applied:
            updated = new_text
            continue

        applied, new_text = _apply_fuzzy(updated, patch, threshold=fuzzy_threshold)
        if applied:
            updated = new_text
            continue

        failures.append(f"patch_{idx}: no match found")
    return updated, failures


def _apply_exact(text: str, patch: SearchReplacePatch) -> tuple[bool, str]:
    index = text.find(patch.search)
    if index < 0:
        return False, text
    return True, text[:index] + patch.replace + text[index + len(patch.search) :]


def _apply_whitespace_normalized(text: str, patch: SearchReplacePatch) -> tuple[bool, str]:
    def normalize(value: str) -> str:
        return re.sub(r"\s+", " ", value).strip()

    normalized_search = normalize(patch.search)
    lines = text.splitlines(keepends=True)
    for start in range(len(lines)):
        for end in range(start + 1, min(len(lines), start + 20) + 1):
            window = "".join(lines[start:end])
            if normalize(window) == normalized_search:
                start_offset = sum(len(line) for line in lines[:start])
                end_offset = start_offset + len(window)
                return True, text[:start_offset] + patch.replace + text[end_offset:]
    return False, text


def _apply_fuzzy(text: str, patch: SearchReplacePatch, threshold: float) -> tuple[bool, str]:
    lines = text.splitlines(keepends=True)
    best_ratio = 0.0
    best_bounds: tuple[int, int] | None = None
    for start in range(len(lines)):
        for end in range(start + 1, min(len(lines), start + 30) + 1):
            window = "".join(lines[start:end])
            ratio = SequenceMatcher(a=window.strip(), b=patch.search.strip()).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_bounds = (start, end)
    if not best_bounds or best_ratio < threshold:
        return False, text

    start, end = best_bounds
    start_offset = sum(len(line) for line in lines[:start])
    end_offset = start_offset + len("".join(lines[start:end]))
    return True, text[:start_offset] + patch.replace + text[end_offset:]
