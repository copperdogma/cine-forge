"""Parser-backed Fountain validation and structural quality scoring."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FountainParseResult:
    """Validation result for parser-backed Fountain checks."""

    parseable: bool
    element_count: int
    coverage: float
    issues: list[str]
    parser_backend: str
    scene_heading_count: int = 0
    character_count: int = 0
    dialogue_count: int = 0
    action_count: int = 0
    transition_count: int = 0
    parenthetical_count: int = 0


def validate_fountain_structure(text: str) -> FountainParseResult:
    """Validate Fountain structure using fountain-tools when available."""
    if not text.strip():
        return FountainParseResult(
            parseable=False,
            element_count=0,
            coverage=0.0,
            issues=["Script is empty"],
            parser_backend="none",
        )

    parsed = _try_fountain_tools_parse(text)
    if parsed is None:
        return _fallback_validation(text)

    counts = _count_elements_by_type(parsed)
    element_count = sum(counts.values())
    line_count = max(len(text.splitlines()), 1)
    coverage = min(1.0, element_count / line_count)
    issues: list[str] = []
    if element_count == 0:
        issues.append("Parser returned no structural elements")
    return FountainParseResult(
        parseable=element_count > 0,
        element_count=element_count,
        coverage=round(coverage, 3),
        issues=issues,
        parser_backend="fountain-tools",
        scene_heading_count=counts.get("HEADING", 0),
        character_count=counts.get("CHARACTER", 0),
        dialogue_count=counts.get("DIALOGUE", 0),
        action_count=counts.get("ACTION", 0),
        transition_count=counts.get("TRANSITION", 0),
        parenthetical_count=counts.get("PARENTHETICAL", 0),
    )


def compute_structural_quality(result: FountainParseResult) -> float:
    """Score 0.0–1.0 indicating how screenplay-like the parsed structure is.

    Weights:
      - scene_headings present: 0.4
      - character cues present:  0.3
      - dialogue present:        0.3

    Each component scores 1.0 if the count meets a minimum threshold,
    scales linearly below it.
    """
    def _score(count: int, minimum: int) -> float:
        if count >= minimum:
            return 1.0
        return count / minimum if minimum > 0 else 0.0

    scene_score = _score(result.scene_heading_count, 1)
    char_score = _score(result.character_count, 1)
    dialogue_score = _score(result.dialogue_count, 1)

    return round(scene_score * 0.4 + char_score * 0.3 + dialogue_score * 0.3, 3)


def _try_fountain_tools_parse(text: str) -> Any | None:
    """Parse text using fountain-tools' Parser builder API."""
    try:
        from fountain_tools.parser import Parser

        p = Parser()
        p.add_text(text)
        p.finalize()
        return p.script
    except Exception:  # noqa: BLE001
        return None


def _count_elements_by_type(script: Any) -> dict[str, int]:
    """Count elements by their ElementType name."""
    counts: dict[str, int] = {}
    elements = getattr(script, "elements", None)
    if not elements:
        return counts
    for elem in elements:
        type_attr = getattr(elem, "type", None)
        if type_attr is not None:
            name = getattr(type_attr, "name", str(type_attr))
            counts[name] = counts.get(name, 0) + 1
    return counts


def _fallback_validation(text: str) -> FountainParseResult:
    scene_like = sum(
        1
        for line in text.splitlines()
        if line.strip().upper().startswith(("INT.", "EXT."))
    )
    cue_like = sum(1 for line in text.splitlines() if _is_upper_cue(line.strip()))
    parseable = scene_like >= 1 and cue_like >= 1
    issues = []
    if not parseable:
        issues.append("fountain-tools not installed or parse failed; fallback heuristic failed")
    return FountainParseResult(
        parseable=parseable,
        element_count=scene_like + cue_like,
        coverage=0.0,
        issues=issues,
        parser_backend="heuristic-fallback",
        scene_heading_count=scene_like,
        character_count=cue_like,
    )


def _is_upper_cue(line: str) -> bool:
    if not line or len(line) > 35:
        return False
    return (
        line.upper() == line
        and any(ch.isalpha() for ch in line)
        and not line.startswith(("INT.", "EXT."))
    )
