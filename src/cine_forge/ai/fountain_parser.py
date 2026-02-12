"""Optional parser-backed Fountain validation helpers."""

from __future__ import annotations

import importlib
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

    element_count = _estimate_element_count(parsed)
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
    )


def _try_fountain_tools_parse(text: str) -> Any | None:
    """Try known fountain-tools parser module/function combinations."""
    candidates = [
        ("fountain_tools.parser", "parse"),
        ("fountain_tools.parser", "parse_string"),
        ("fountain_tools.fountain_parser", "parse"),
        ("fountain_tools.fountain_parser", "parse_string"),
    ]
    for module_name, func_name in candidates:
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError:
            continue
        parser_fn = getattr(module, func_name, None)
        if not callable(parser_fn):
            continue
        try:
            return parser_fn(text)
        except Exception:  # noqa: BLE001
            continue
    return None


def _estimate_element_count(parsed: Any) -> int:
    if parsed is None:
        return 0
    if isinstance(parsed, list):
        return len(parsed)
    if isinstance(parsed, dict):
        for key in ("elements", "tokens", "body"):
            value = parsed.get(key)
            if isinstance(value, list):
                return len(value)
        return len(parsed)
    if hasattr(parsed, "__len__"):
        try:
            return len(parsed)  # type: ignore[arg-type]
        except TypeError:
            return 0
    return 0


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
    )


def _is_upper_cue(line: str) -> bool:
    if not line or len(line) > 35:
        return False
    return (
        line.upper() == line
        and any(ch.isalpha() for ch in line)
        and not line.startswith(("INT.", "EXT."))
    )
