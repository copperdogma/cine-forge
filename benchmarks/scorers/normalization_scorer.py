"""Deterministic Fountain-normalization scorer for promptfoo."""

from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

SCORER_ROOT = Path(__file__).resolve().parent
if str(SCORER_ROOT) not in sys.path:
    sys.path.insert(0, str(SCORER_ROOT))

from normalization_fidelity import (  # noqa: E402
    CHARACTER_CUE_PATTERN,
    SCENE_HEADING_PATTERN,
    _base_character,
    _known_cue,
    _source_contracts,
    _source_fidelity,
)
from score_semantics import finalize_score  # noqa: E402

PASS_THRESHOLD = 0.65


def _resolve_golden_path(context: dict) -> str:
    golden_path = context.get("vars", {}).get("golden_path", "")
    if golden_path and not os.path.isabs(golden_path):
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for candidate in (os.path.join(base, golden_path), os.path.join(os.getcwd(), golden_path)):
            if os.path.exists(candidate):
                return candidate
    return golden_path


def _unwrap_fence(output: str) -> tuple[str, bool]:
    raw = output.strip()
    match = re.fullmatch(r"```(?:\w+)?\s*([\s\S]*?)```", raw)
    return (match.group(1).strip(), True) if match else (raw, False)


def _is_character_cue(lines: list[str], index: int) -> bool:
    stripped = lines[index].strip()
    return bool(stripped and len(stripped) < 60
                and CHARACTER_CUE_PATTERN.fullmatch(stripped)
                and not SCENE_HEADING_PATTERN.match(stripped))


def _scene_heading_score(lines: list[str], expected_scenes: list[str]) -> tuple[float, list[str]]:
    headings = [line.strip() for line in lines if SCENE_HEADING_PATTERN.match(line.strip())]
    uppercase_ratio = (sum(heading == heading.upper() for heading in headings) / len(headings)
                       if headings else 0.0)
    if not expected_scenes:
        return (1.0 if headings else 0.0), headings
    expected = Counter(" ".join(value.upper().split()) for value in expected_scenes)
    actual = Counter(" ".join(value.upper().split()) for value in headings)
    matched = sum((expected & actual).values())
    identity_ratio = matched / max(len(expected_scenes), len(headings))
    return (identity_ratio * 0.6 + uppercase_ratio * 0.4), headings


def _character_cue_score(lines: list[str], expected_characters: list[str]
                         ) -> tuple[float, list[int], set[str]]:
    indices = [index for index in range(len(lines)) if _is_character_cue(lines, index)]
    found = {_base_character(lines[index].strip()) for index in indices}
    if not expected_characters:
        return (1.0 if found else 0.0), indices, found
    expected = {character.upper() for character in expected_characters}
    return len(expected & found) / len(expected), indices, found


def _speaker_before(lines: list[str], line_index: int) -> str | None:
    for index in range(line_index - 1, -1, -1):
        if SCENE_HEADING_PATTERN.match(lines[index].strip()):
            return None
        if _is_character_cue(lines, index):
            return _base_character(lines[index].strip())
    return None


def _dialogue_score(lines: list[str], requirements: list[dict]) -> tuple[float, bool]:
    if not requirements:
        return 1.0, True
    scores: list[float] = []
    for requirement in requirements:
        fragment = str(requirement.get("fragment", "")).strip().lower()
        expected_speaker = str(
            requirement.get("character", requirement.get("speaker", ""))
        ).upper()
        candidates = [
            index
            for index, line in enumerate(lines)
            if fragment and fragment in line.lower()
        ]
        if not candidates:
            scores.append(0.0)
            continue
        if not expected_speaker:
            scores.append(1.0)
            continue
        attributed = any(_speaker_before(lines, index) == expected_speaker for index in candidates)
        scores.append(1.0 if attributed else 0.5)
    return sum(scores) / len(scores), all(score == 1.0 for score in scores)


def _markdown_score(raw_output: str, forbidden: list[str], had_fence: bool) -> tuple[float, int]:
    violations = int(had_fence)
    for pattern in forbidden:
        try:
            violations += bool(re.search(pattern, raw_output, re.MULTILINE))
        except re.error:
            violations += 1
    denominator = max(1, len(forbidden) + 1)
    return max(0.0, 1.0 - violations / denominator), violations


def _structure_score(lines: list[str], cue_indices: list[int]) -> float:
    blank_ratio = (sum(index > 0 and not lines[index - 1].strip()
                       for index in cue_indices) / len(cue_indices) if cue_indices else 0.0)
    parentheses_valid = all(not line.strip().startswith("(") or line.strip().endswith(")")
                            for line in lines)
    return (blank_ratio + float(parentheses_valid)) / 2


def get_assert(output: str, context: dict) -> dict:
    golden_path = _resolve_golden_path(context)
    if not golden_path or not os.path.exists(golden_path):
        return {"pass": False, "score": 0.0, "reason": f"Golden file not found: {golden_path}"}
    with open(golden_path) as handle:
        golden = json.load(handle)

    text, had_fence = _unwrap_fence(output)
    lines = text.splitlines()
    expected_scenes = golden.get("expected_scenes", [])
    expected_characters = golden.get("expected_characters", [])
    scene_score, headings = _scene_heading_score(lines, expected_scenes)
    cue_score, _, _ = _character_cue_score(lines, expected_characters)
    known_cue_indices = [
        index for index, line in enumerate(lines) if _known_cue(line, expected_characters)
    ]
    dialogue_score, dialogue_grounded = _dialogue_score(
        lines,
        golden.get("required_dialogue", []),
    )
    markdown_score, markdown_violations = _markdown_score(
        output,
        golden.get("forbidden_patterns", []),
        had_fence,
    )
    text_upper = text.upper()
    content_score = (
        sum(character.upper() in text_upper for character in expected_characters)
        / len(expected_characters)
        if expected_characters
        else 1.0
    )
    source_text = str(context.get("vars", {}).get("source_text", ""))
    fidelity_score, fidelity_gate, fidelity_reason = _source_fidelity(source_text, text, golden)
    contract_score, contract_gate, failed_contracts = _source_contracts(
        source_text, text, golden
    )
    structure_score = _structure_score(lines, known_cue_indices)
    scores = {
        "scene_headings": scene_score,
        "character_cues": cue_score,
        "dialogue_preserved": dialogue_score,
        "no_markdown": markdown_score,
        "structure_quality": structure_score,
        "content_completeness": content_score,
        "source_fidelity": fidelity_score,
        "source_contracts": contract_score,
    }
    weights = {
        "scene_headings": 0.15,
        "character_cues": 0.15,
        "dialogue_preserved": 0.20,
        "no_markdown": 0.10,
        "structure_quality": 0.15,
        "content_completeness": 0.05,
        "source_fidelity": 0.10,
        "source_contracts": 0.10,
    }
    total = sum(scores[key] * weight for key, weight in weights.items())
    reasons = [f"{key}={value:.2f}" for key, value in sorted(scores.items())]
    if len(headings) < len(expected_scenes):
        reasons.append(f"Headings: {len(headings)}/{len(expected_scenes)}")
    if markdown_violations:
        reasons.append(f"Markdown violations: {markdown_violations}")
    if not dialogue_grounded:
        reasons.append("Required dialogue missing or attributed to the wrong character")
    if failed_contracts:
        reasons.append(f"Source contract violations: {', '.join(failed_contracts)}")
    if fidelity_reason:
        reasons.append(fidelity_reason)
    rules = golden.get("structural_rules", {})
    expected_heading_counts = Counter(" ".join(value.upper().split()) for value in expected_scenes)
    actual_heading_counts = Counter(" ".join(value.upper().split()) for value in headings)
    heading_identity_gate = not expected_scenes or expected_heading_counts == actual_heading_counts
    headings_uppercase = bool(headings) and all(heading == heading.upper() for heading in headings)
    cues_uppercase = bool(known_cue_indices) and all(
        lines[index].strip() == lines[index].strip().upper() for index in known_cue_indices
    )
    blank_lines_valid = bool(known_cue_indices) and all(
        index > 0 and not lines[index - 1].strip() for index in known_cue_indices
    )
    parentheticals_valid = all(
        not line.strip().startswith("(") or re.fullmatch(r"\([^()]+\)", line.strip())
        for line in lines
    )
    markdown_gate = not rules.get("no_markdown_formatting") or markdown_violations == 0
    scene_case_gate = not rules.get("scene_headings_uppercase") or headings_uppercase
    cue_case_gate = not rules.get("character_cues_uppercase") or cues_uppercase
    parenthetical_gate = not rules.get("parentheticals_in_parens") or parentheticals_valid
    blank_line_gate = not rules.get("blank_line_before_character_cue") or blank_lines_valid
    if not heading_identity_gate:
        reasons.append("Scene heading set differs from the golden contract")
    if not scene_case_gate:
        reasons.append("scene_headings_uppercase rule violated")
    if not cue_case_gate:
        reasons.append("character_cues_uppercase rule violated")
    if not parenthetical_gate:
        reasons.append("parentheticals_in_parens rule violated")
    if not blank_line_gate:
        reasons.append("blank_line_before_character_cue rule violated")
    hard_gates = all(
        (
            dialogue_grounded,
            markdown_gate,
            heading_identity_gate,
            scene_case_gate,
            cue_case_gate,
            parenthetical_gate,
            blank_line_gate,
            fidelity_gate,
            contract_gate,
        )
    )
    return finalize_score(
        total,
        pass_threshold=PASS_THRESHOLD,
        hard_gates=hard_gates,
        reason=" | ".join(reasons),
    )
