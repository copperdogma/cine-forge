"""Source-backed contracts for screenplay round-trip tests."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

FIXTURE_ROOT = Path("tests/fixtures/round_trip")
CONTRACT_PATH = FIXTURE_ROOT / "contracts.json"
_SCENE_PREFIXES = ("INT.", "EXT.", "INT/EXT.", "I/E.", "EST.")
_TOKEN_RE = re.compile(r"[A-Z0-9]+(?:'[A-Z0-9]+)?")
_TITLE_FIELD_RE = re.compile(r"^[A-Za-z][A-Za-z ]*:\s*(.*)$")


def load_contract(script_folder: str) -> dict[str, Any]:
    contracts = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    return contracts[script_folder]


def fixture_paths(script_folder: str) -> tuple[Path, Path, Path]:
    contract = load_contract(script_folder)
    fixture_dir = FIXTURE_ROOT / script_folder
    stem = contract["file_stem"]
    return (
        fixture_dir / f"{stem}.fountain",
        fixture_dir / f"{stem}.fdx",
        fixture_dir / f"{stem}.pdf",
    )


def normalized_tokens(
    text: str,
    token_aliases: dict[str, str] | None = None,
) -> list[str]:
    normalized = (
        re.sub(r"(?i)\(c\)", " COPYRIGHT ", text)
        .replace("©", " COPYRIGHT ")
        .replace("&", " AND ")
        .replace("\u2018", "'")
        .replace("\u2019", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .upper()
    )
    tokens = _TOKEN_RE.findall(normalized)
    if token_aliases:
        return [token_aliases.get(token, token) for token in tokens]
    return tokens


def scene_headings(text: str) -> list[str]:
    return [
        " ".join(line.strip().upper().split())
        for line in text.splitlines()
        if line.strip().upper().startswith(_SCENE_PREFIXES)
    ]


def renderable_fountain_text(source: str) -> str:
    """Remove Fountain-only metadata labels and non-rendered outline markup."""
    rendered: list[str] = []
    in_title_page = True
    for line in source.splitlines():
        stripped = line.strip()
        if in_title_page:
            if stripped == "====":
                in_title_page = False
                continue
            title_field = _TITLE_FIELD_RE.match(line)
            if title_field:
                if value := title_field.group(1):
                    rendered.append(value)
                continue
            if line.startswith((" ", "\t")) and stripped:
                rendered.append(stripped)
                continue
            if not stripped:
                continue
            if stripped.upper().startswith((*_SCENE_PREFIXES, "#", ">", ".")):
                in_title_page = False
            else:
                rendered.append(stripped)
                continue

        if not stripped or stripped.startswith(("#", "=")):
            continue
        rendered.append(stripped)
    return "\n".join(rendered)


def assert_source_contract(source: str, contract: dict[str, Any]) -> None:
    headings = scene_headings(source)
    assert len(headings) == contract["scene_count"]
    _assert_ordered_values(headings, contract["ordered_scene_anchors"])
    assert_ordered_text_anchors(source, contract["identity_anchors"])
    assert_dialogue_anchors(source, contract["dialogue_anchors"])


def assert_heading_fidelity(
    source: str,
    converted: str,
    contract: dict[str, Any],
) -> None:
    source_headings = scene_headings(source)
    assert len(source_headings) == contract["scene_count"]
    _assert_ordered_values(source_headings, contract["ordered_scene_anchors"])
    converted_headings = scene_headings(converted)
    assert len(converted_headings) == len(source_headings)
    # PDF extraction can wrap a long heading onto a second line and can insert
    # spaces around dashes. Requiring every complete heading token sequence in
    # screenplay order preserves semantics without pretending layout is text.
    assert_ordered_text_anchors(converted, source_headings)


def assert_ordered_text_anchors(text: str, anchors: list[str]) -> None:
    haystack = normalized_tokens(text)
    cursor = 0
    for anchor in anchors:
        needle = normalized_tokens(anchor)
        position = _find_contiguous(haystack, needle, cursor)
        assert position is not None, f"Missing or reordered text anchor: {anchor!r}"
        cursor = position + len(needle)


def assert_dialogue_anchors(text: str, anchors: list[dict[str, str]]) -> None:
    lines = text.splitlines()
    cursor = 0
    for anchor in anchors:
        speaker = normalized_tokens(anchor["speaker"])
        dialogue = normalized_tokens(anchor["dialogue"])
        match_line = _find_dialogue_anchor(lines, speaker, dialogue, cursor)
        assert match_line is not None, (
            "Missing, reordered, or speaker-detached dialogue anchor: "
            f"{anchor['speaker']}: {anchor['dialogue']}"
        )
        cursor = match_line + 1


def assert_complete_token_retention(
    source: str,
    converted: str,
    *,
    minimum_precision: float = 0.99,
    converted_token_aliases: dict[str, str] | None = None,
) -> None:
    source_tokens = normalized_tokens(source)
    converted_tokens = normalized_tokens(converted, converted_token_aliases)
    missing = Counter(source_tokens) - Counter(converted_tokens)
    assert not missing, f"Conversion lost source tokens: {missing.most_common(10)}"
    precision = len(source_tokens) / max(len(converted_tokens), 1)
    assert precision >= minimum_precision, (
        f"Conversion added too much non-source text: precision={precision:.4f}, "
        f"required={minimum_precision:.4f}"
    )


def assert_ordered_token_retention(
    source: str,
    converted: str,
    *,
    converted_token_aliases: dict[str, str] | None = None,
) -> None:
    source_tokens = normalized_tokens(source)
    converted_tokens = normalized_tokens(converted, converted_token_aliases)
    cursor = 0
    for token in converted_tokens:
        if cursor < len(source_tokens) and token == source_tokens[cursor]:
            cursor += 1
    assert cursor == len(source_tokens), (
        "Converted text deleted or reordered source tokens near "
        f"source token index {cursor}"
    )


def assert_only_allowed_extra_tokens(
    source: str,
    converted: str,
    allowed_tokens: list[str],
    *,
    converted_token_aliases: dict[str, str] | None = None,
    max_page_number: int | None = None,
) -> None:
    source_counter = Counter(normalized_tokens(source))
    converted_counter = Counter(normalized_tokens(converted, converted_token_aliases))
    extras = converted_counter - source_counter
    allowed = set(allowed_tokens)
    unexpected = {
        token: count
        for token, count in extras.items()
        if (
            token not in allowed
            and not (
                max_page_number is not None
                and token.isdigit()
                and 1 <= int(token) <= max_page_number
            )
        )
    }
    assert not unexpected, f"Conversion added unsupported tokens: {unexpected}"
    overproduced = {
        token: count
        for token, count in extras.items()
        if token in allowed and max_page_number is not None and count > max_page_number
    }
    assert not overproduced, f"Conversion overproduced pagination tokens: {overproduced}"


def _find_dialogue_anchor(
    lines: list[str],
    speaker: list[str],
    dialogue: list[str],
    start: int,
) -> int | None:
    for index in range(start, len(lines)):
        if normalized_tokens(lines[index]) != speaker:
            continue
        window_lines: list[str] = []
        for line in lines[index + 1 : index + 21]:
            if _is_pagination_line(line, speaker):
                continue
            if _is_dialogue_boundary(line):
                break
            window_lines.append(line)
        window = normalized_tokens("\n".join(window_lines))
        if _find_contiguous(window, dialogue, 0) is not None:
            return index
    return None


def _is_pagination_line(line: str, speaker: list[str]) -> bool:
    tokens = normalized_tokens(line)
    if not tokens:
        return False
    if tokens == ["MORE"] or all(token.isdigit() for token in tokens):
        return True
    return tokens[: len(speaker)] == speaker and "CONT'D" in tokens


def _is_dialogue_boundary(line: str) -> bool:
    """Stop attachment at the next cue, scene heading, or transition."""
    stripped = line.strip()
    if not stripped:
        return False
    upper = stripped.upper().rstrip("^").strip()
    if upper.startswith(_SCENE_PREFIXES) or upper.endswith(" TO:"):
        return True
    if upper.startswith("("):
        return False
    tokens = normalized_tokens(upper)
    return (
        1 <= len(tokens) <= 5
        and stripped == stripped.upper()
        and not any(character in stripped for character in "!?;:")
        and tokens != ["MORE"]
        and not all(token.isdigit() for token in tokens)
    )


def _assert_ordered_values(values: list[str], anchors: list[str]) -> None:
    cursor = 0
    for anchor in anchors:
        anchor_tokens = normalized_tokens(anchor)
        position = next(
            (
                index
                for index in range(cursor, len(values))
                if normalized_tokens(values[index]) == anchor_tokens
            ),
            None,
        )
        if position is None:
            raise AssertionError(f"Missing or reordered scene anchor: {anchor!r}")
        cursor = position + 1


def _find_contiguous(
    values: list[str],
    needle: list[str],
    start: int,
) -> int | None:
    if not needle:
        return start
    stop = len(values) - len(needle) + 1
    for index in range(start, stop):
        if values[index : index + len(needle)] == needle:
            return index
    return None
