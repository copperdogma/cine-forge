"""Source-fidelity contracts shared by the Fountain normalization scorer."""

from __future__ import annotations

import re
from collections import Counter

SCENE_HEADING_PATTERN = re.compile(r"^\s*(INT\.|EXT\.|INT\./EXT\.)\s+.+", re.IGNORECASE)
CHARACTER_CUE_PATTERN = re.compile(r"^[A-Z][A-Z\s.'()]+$")
TITLE_PAGE_FIELDS = {
    "author",
    "contact",
    "copyright",
    "credit",
    "draft date",
    "notes",
    "source",
    "title",
}
TRANSITION_PATTERN = re.compile(
    r"^(?:CUT TO|SMASH CUT TO|MATCH CUT TO|DISSOLVE TO|WIPE TO|FADE IN|FADE OUT):$",
    re.IGNORECASE,
)


def _base_character(value: str) -> str:
    return re.sub(r"\s*\(.*?\)\s*$", "", value.strip()).strip()


def _contract_text(value: str) -> str:
    value = re.sub(r"\\([!#*_:\-])", r"\1", value)
    return " ".join(
        value.replace("’", "'")
        .replace("‘", "'")
        .replace("“", '"')
        .replace("”", '"')
        .split()
    )


def _presentation_clean_line(line: str) -> str:
    cleaned = re.sub(r"^\s*#{1,6}\s*", "", line.strip())
    cleaned = re.sub(r"^\s*-\s+", "", cleaned)
    cleaned = re.sub(r"^\s*>\s*", "", cleaned)
    cleaned = cleaned.replace("**", "").replace("__", "")
    return _contract_text(cleaned)


def _known_cue(line: str, expected_characters: list[str]) -> str | None:
    base = _base_character(_presentation_clean_line(line))
    return next(
        (
            character.upper()
            for character in expected_characters
            if base.casefold() == character.strip().casefold()
        ),
        None,
    )


def _title_metadata(text: str) -> Counter[tuple[str, str]]:
    metadata: Counter[tuple[str, str]] = Counter()
    for line in text.splitlines():
        match = re.match(r"^\s*([A-Za-z ]+):\s*(.+?)\s*$", line)
        if not match:
            continue
        key = " ".join(match.group(1).lower().split())
        if key in TITLE_PAGE_FIELDS:
            metadata[(key, _contract_text(match.group(2)).casefold())] += 1
    return metadata


def _parenthetical_value(line: str) -> str | None:
    cleaned = _presentation_clean_line(line)
    match = re.fullmatch(r"\(([^()]*)\)", cleaned)
    return _contract_text(match.group(1)) if match else None


def _source_parentheticals(text: str) -> Counter[str]:
    return Counter(
        value
        for line in text.splitlines()
        if (value := _parenthetical_value(line)) is not None
    )


def _merge_dialogue(turns: list[tuple[str, str]]) -> list[tuple[str, str]]:
    merged: list[tuple[str, str]] = []
    for speaker, dialogue in turns:
        if speaker and merged and merged[-1][0] == speaker:
            merged[-1] = (speaker, f"{merged[-1][1]} {dialogue}")
        else:
            merged.append((speaker, dialogue))
    return merged


def _fountain_dialogue(text: str, expected_characters: list[str]) -> list[tuple[str, str]]:
    lines = text.splitlines()
    turns: list[tuple[str, str]] = []
    index = 0
    while index < len(lines):
        speaker = _known_cue(lines[index], expected_characters)
        if not speaker:
            index += 1
            continue
        cursor = index + 1
        while cursor < len(lines) and not lines[cursor].strip():
            cursor += 1
        while cursor < len(lines) and _parenthetical_value(lines[cursor]) is not None:
            cursor += 1
        while cursor < len(lines) and not lines[cursor].strip():
            cursor += 1
        dialogue: list[str] = []
        while cursor < len(lines) and lines[cursor].strip():
            if _known_cue(lines[cursor], expected_characters):
                break
            dialogue.append(_contract_text(lines[cursor].strip()))
            cursor += 1
        if dialogue:
            turns.append((speaker, " ".join(dialogue)))
        index = max(cursor, index + 1)
    return _merge_dialogue(turns)


def _source_dialogue(text: str, golden: dict) -> list[tuple[str, str]]:
    expected_characters = golden.get("expected_characters", [])
    fountain = _fountain_dialogue(text, expected_characters)
    if fountain:
        return fountain
    quotes = [
        _contract_text(value[:-1] + "." if value.endswith(",") else value)
        for value in re.findall(r'["“]([^"”]+)["”]', text)
    ]
    requirements = golden.get("required_dialogue", [])
    speakers = [
        str(item.get("character", item.get("speaker", ""))).upper()
        for item in requirements
    ]
    if len(speakers) != len(quotes):
        speakers = [""] * len(quotes)
    return _merge_dialogue(list(zip(speakers, quotes, strict=True)))


def _transition_value(line: str) -> str | None:
    cleaned = _presentation_clean_line(line).upper()
    return cleaned if TRANSITION_PATTERN.fullmatch(cleaned) else None


def _source_transitions(text: str) -> list[str]:
    return [
        transition
        for line in text.splitlines()
        if (transition := _transition_value(line)) is not None
    ]


def _content_tokens(value: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", value.lower())


def _source_action_tokens(text: str, expected_characters: list[str]) -> list[str]:
    action_tokens: list[str] = []
    in_dialogue = False
    for raw_line in text.splitlines():
        if not raw_line.strip():
            in_dialogue = False
            continue
        line = _presentation_clean_line(raw_line)
        if not line:
            continue
        if SCENE_HEADING_PATTERN.match(line) or _transition_value(line):
            in_dialogue = False
            continue
        if _title_metadata(line):
            continue
        if _known_cue(line, expected_characters):
            in_dialogue = True
            continue
        if in_dialogue or _parenthetical_value(line) is not None:
            continue
        action_tokens.extend(_content_tokens(line))
    return action_tokens


def _source_contracts(
    source_text: str,
    output_text: str,
    golden: dict,
) -> tuple[float, bool, list[str]]:
    if not source_text:
        return 1.0, True, []
    checks: list[tuple[str, bool]] = []
    source_metadata = _title_metadata(source_text)
    if source_metadata:
        checks.append(("title metadata", not (source_metadata - _title_metadata(output_text))))
    source_parentheticals = _source_parentheticals(source_text)
    if source_parentheticals:
        checks.append(
            (
                "source parentheticals",
                not (source_parentheticals - _source_parentheticals(output_text)),
            )
        )
    expected_dialogue = _source_dialogue(source_text, golden)
    if expected_dialogue:
        actual_dialogue = _fountain_dialogue(
            output_text, golden.get("expected_characters", [])
        )
        dialogue_valid = len(expected_dialogue) == len(actual_dialogue) and all(
            expected_text == actual_text
            and (not expected_speaker or expected_speaker == actual_speaker)
            for (expected_speaker, expected_text), (actual_speaker, actual_text) in zip(
                expected_dialogue, actual_dialogue, strict=True
            )
        )
        checks.append(("source dialogue wording/attribution/punctuation", dialogue_valid))
    rules = golden.get("structural_rules", {})
    if rules.get("preserve_source_action_order"):
        expected_actions = _source_action_tokens(
            source_text, golden.get("expected_characters", [])
        )
        actual_actions = _source_action_tokens(
            output_text, golden.get("expected_characters", [])
        )
        checks.append(("source action wording/order", expected_actions == actual_actions))
    if rules.get("preserve_source_transitions"):
        checks.append(
            (
                "source transitions",
                _source_transitions(source_text) == _source_transitions(output_text),
            )
        )
    if not checks:
        return 1.0, True, []
    failed = [name for name, valid in checks if not valid]
    return sum(valid for _, valid in checks) / len(checks), not failed, failed


def _source_fidelity(
    source_text: str,
    output_text: str,
    golden: dict,
) -> tuple[float, bool, str]:
    if not source_text:
        return 1.0, True, ""
    source_tokens = set(_content_tokens(source_text))
    output_tokens = set(_content_tokens(output_text))
    expected_tokens = set(
        _content_tokens(
            " ".join(golden.get("expected_scenes", []) + golden.get("expected_characters", []))
        )
    )
    structural = {"int", "ext", "day", "night", "continuous", "cut", "to", "vo", "os"}
    recall = len(source_tokens & output_tokens) / len(source_tokens) if source_tokens else 1.0
    novel = output_tokens - source_tokens - expected_tokens - structural
    precision = 1.0 - len(novel) / max(1, len(output_tokens))
    source_contract = _contract_text(source_text).upper()
    output_contract = _contract_text(output_text).upper()
    vo_required = bool(re.search(r"\(\s*V\.O\.\s*\)", source_contract, re.IGNORECASE))
    vo_present = bool(re.search(r"\(\s*V\.O\.\s*\)", output_contract, re.IGNORECASE))
    markers_valid = (
        (not vo_required or vo_present)
        and ("CUT TO:" not in source_contract or "CUT TO:" in output_contract)
    )
    score = 0.7 * recall + 0.3 * precision
    gate = recall >= 0.85 and len(novel) <= 2 and markers_valid
    reason = f"source_recall={recall:.2f}, novel_tokens={len(novel)}, markers={markers_valid}"
    return score, gate, reason
