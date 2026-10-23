"""Deterministic source-grounding and structure scorer for script bibles."""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

SCORER_ROOT = Path(__file__).resolve().parent
if str(SCORER_ROOT) not in sys.path:
    sys.path.insert(0, str(SCORER_ROOT))

from score_semantics import finalize_score  # noqa: E402
from script_bible_polarity import (  # noqa: E402
    contains_affirmed_phrase,
    regex_has_affirmed_match,
)

PASS_THRESHOLD = 0.70


ACT_FIELDS = {
    "act_number",
    "title",
    "start_scene",
    "end_scene",
    "summary",
    "turning_points",
}
THEME_FIELDS = {"theme", "description", "evidence"}


def _resolve_golden_path(context: dict) -> str:
    golden_path = context.get("vars", {}).get("golden_path", "")
    if golden_path and not os.path.isabs(golden_path):
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidate = os.path.join(base, golden_path)
        if os.path.exists(candidate):
            return candidate
    return golden_path


def _parse_output(output: str) -> tuple[dict | None, float]:
    try:
        parsed = json.loads(output)
        return (parsed if isinstance(parsed, dict) else None), 1.0
    except json.JSONDecodeError:
        match = re.search(r"```(?:json)?\s*([\s\S]*?)```", output)
        if not match:
            return None, 0.0
        try:
            parsed = json.loads(match.group(1))
        except json.JSONDecodeError:
            return None, 0.0
        return (parsed if isinstance(parsed, dict) else None), 0.9


def _tokens(value: object) -> list[str]:
    return re.findall(r"[a-z0-9]+", str(value or "").lower())


def _grounding_tokens(value: object) -> list[str]:
    normalized = []
    for token in _tokens(value):
        if token in {"died", "dies", "dying"}:
            normalized.append("die")
        elif len(token) > 4 and token.endswith("ies"):
            normalized.append(f"{token[:-3]}y")
        elif len(token) > 5 and token.endswith("ing"):
            normalized.append(token[:-3])
        elif len(token) > 4 and token.endswith("s"):
            normalized.append(token[:-1])
        else:
            normalized.append(token)
    return normalized


def _contains_token_run(haystack: list[str], needle: list[str], minimum: int = 3) -> bool:
    maximum = min(len(needle), len(haystack))
    for length in range(maximum, minimum - 1, -1):
        for index in range(len(needle) - length + 1):
            candidate = needle[index : index + length]
            if any(
                haystack[offset : offset + length] == candidate
                for offset in range(len(haystack) - length + 1)
            ):
                return True
    return False


def _source_fragment_grounded(value: object, source: str) -> bool:
    fragment = _grounding_tokens(value)
    source_tokens = _grounding_tokens(source)
    if len(fragment) < 4 or not source_tokens:
        return False
    source_vocabulary = set(source_tokens)
    coverage = sum(token in source_vocabulary for token in fragment) / len(fragment)
    return coverage >= 0.8 and _contains_token_run(source_tokens, fragment)


def _contains_phrase(value: object, phrase: object) -> bool:
    haystack = _tokens(value)
    needle = _tokens(phrase)
    return bool(needle) and any(
        haystack[index : index + len(needle)] == needle
        for index in range(len(haystack) - len(needle) + 1)
    )


def _keyword_score(value: object, keywords: list[str], minimum: int) -> float:
    if not keywords:
        return 1.0
    matches = sum(_contains_phrase(value, keyword) for keyword in keywords)
    return min(1.0, matches / max(1, minimum))


def _required_field_score(result: dict, required: list[str]) -> tuple[float, bool]:
    present = [
        field
        for field in required
        if field in result and result[field] not in (None, "", [])
    ]
    extra = set(result) - set(required)
    denominator = len(required) + len(extra)
    score = len(present) / denominator if denominator else 1.0
    return score, len(present) == len(required) and not extra


def _act_structure_score(result: dict, golden: dict) -> tuple[float, bool]:
    acts = result.get("act_structure")
    minimum = golden.get("act_count_min", 2)
    maximum = golden.get("act_count_max", 4)
    if not isinstance(acts, list) or not minimum <= len(acts) <= maximum:
        return 0.0, False
    scores = []
    for index, act in enumerate(acts, start=1):
        if not isinstance(act, dict):
            scores.append(0.0)
            continue
        fields = len(ACT_FIELDS & set(act)) / len(ACT_FIELDS | set(act))
        number = 1.0 if act.get("act_number") == index else 0.0
        substantive = 1.0 if len(str(act.get("summary", ""))) >= 20 else 0.0
        turning_points = act.get("turning_points")
        turns = 1.0 if isinstance(turning_points, list) and turning_points else 0.0
        scores.append((fields + number + substantive + turns) / 4)
    score = sum(scores) / len(scores)
    return score, all(value == 1.0 for value in scores)


def _theme_score(result: dict, golden: dict) -> tuple[float, bool]:
    themes = result.get("themes")
    if not isinstance(themes, list) or len(themes) < 2:
        return 0.0, False
    structural = []
    for theme in themes:
        if not isinstance(theme, dict):
            structural.append(0.0)
            continue
        has_fields = set(theme) == THEME_FIELDS
        description = len(str(theme.get("description", ""))) >= 20
        evidence = theme.get("evidence")
        has_evidence = isinstance(evidence, list) and len(evidence) >= 2
        structural.append(1.0 if has_fields and description and has_evidence else 0.0)
    theme_text = json.dumps(themes)
    groups = golden.get("must_include_themes", [])
    grounding = (
        sum(
            any(_contains_phrase(theme_text, keyword) for keyword in group.get("keywords", []))
            for group in groups
        )
        / len(groups)
        if groups
        else 1.0
    )
    structure = sum(structural) / len(structural)
    return (structure + grounding) / 2, structure == 1.0 and grounding == 1.0


def _genre_tone_score(result: dict, golden: dict) -> tuple[float, bool]:
    genre = _keyword_score(result.get("genre"), golden.get("genre_keywords", []), 1)
    tone = _keyword_score(result.get("tone"), golden.get("tone_keywords", []), 1)
    return (genre + tone) / 2, genre == 1.0 and tone == 1.0


def _logline_score(result: dict, golden: dict) -> float:
    logline = str(result.get("logline", ""))
    if len(logline) <= 20 or len(logline) > golden.get("logline_max_length", 300):
        return 0.0
    premise = _keyword_score(logline, golden.get("logline_keywords", []), 2)
    protagonist = _keyword_score(logline, golden.get("protagonist_keywords", []), 1)
    conflict = _keyword_score(
        logline,
        golden.get("must_include_conflict_keywords", []),
        1,
    )
    return (premise + protagonist + conflict) / 3


def _synopsis_score(result: dict, golden: dict) -> tuple[float, bool]:
    synopsis = str(result.get("synopsis", ""))
    length_score = min(1.0, len(synopsis) / max(1, golden.get("synopsis_min_length", 200)))
    grounding_scores = [
        _keyword_score(synopsis, golden.get("protagonist_keywords", []), 1),
        _keyword_score(synopsis, golden.get("must_include_conflict_keywords", []), 2),
        _keyword_score(synopsis, golden.get("setting_keywords", []), 1),
        _keyword_score(synopsis, golden.get("protagonist_journey_keywords", []), 1),
    ]
    grounding = sum(grounding_scores) / len(grounding_scores)
    score = 0.3 * length_score + 0.7 * grounding
    return score, length_score == 1.0 and grounding >= 0.75


def _journey_conflict_setting_scores(result: dict, golden: dict) -> dict[str, float]:
    return {
        "journey_grounding": _keyword_score(
            result.get("protagonist_journey"),
            golden.get("protagonist_journey_keywords", []),
            2,
        ),
        "conflict_grounding": _keyword_score(
            result.get("central_conflict"),
            golden.get("must_include_conflict_keywords", []),
            2,
        ),
        "setting_grounding": _keyword_score(
            result.get("setting_overview"),
            golden.get("setting_keywords", []),
            2,
        ),
    }


def _confidence_score(result: dict) -> tuple[float, bool]:
    confidence = result.get("confidence")
    valid = (
        isinstance(confidence, (int, float))
        and not isinstance(confidence, bool)
        and 0.0 <= confidence <= 1.0
    )
    return (1.0 if valid else 0.0), valid


def _narrative_text(result: dict) -> str:
    values = [
        result.get("logline"),
        result.get("synopsis"),
        result.get("narrative_arc"),
        result.get("protagonist_journey"),
        result.get("central_conflict"),
        result.get("setting_overview"),
    ]
    for act in result.get("act_structure", []):
        if isinstance(act, dict):
            values.extend((act.get("summary"), act.get("turning_points")))
    return json.dumps(values)


def _story_event_contract(result: dict, golden: dict) -> tuple[float, bool, list[str]]:
    events = golden.get("required_story_events", [])
    if not events:
        return 1.0, True, []
    narrative = _narrative_text(result)
    valid_events: list[bool] = []
    missing: list[str] = []
    for event in events:
        keywords = event.get("keywords", [])
        minimum = event.get("minimum_matches", len(keywords))
        valid = (
            sum(contains_affirmed_phrase(narrative, keyword) for keyword in keywords)
            >= minimum
        )
        valid_events.append(valid)
        if not valid:
            missing.append(str(event.get("description", "unnamed event")))
    return sum(valid_events) / len(valid_events), all(valid_events), missing


def _source_scene_sections(headings: list[object], screenplay: str) -> list[str] | None:
    lines = screenplay.splitlines(keepends=True)
    starts: list[int] = []
    cursor = 0
    offset = 0
    for heading in headings:
        target = tuple(_tokens(heading))
        match_index = next(
            (
                index
                for index in range(cursor, len(lines))
                if tuple(_tokens(lines[index])) == target
            ),
            None,
        )
        if match_index is None:
            return None
        offset += sum(len(line) for line in lines[cursor:match_index])
        starts.append(offset)
        cursor = match_index
    return [
        screenplay[start : starts[index + 1] if index + 1 < len(starts) else None]
        for index, start in enumerate(starts)
    ]


def _boundary_start_index(
    value: object,
    normalized_headings: list[tuple[str, ...]],
    sections: list[str],
) -> int | None:
    boundary = tuple(_tokens(value))
    if boundary in normalized_headings:
        return normalized_headings.index(boundary)
    matches = [
        index
        for index, section in enumerate(sections)
        if _source_fragment_grounded(value, section)
    ]
    return matches[0] if len(matches) == 1 else None


def _act_boundary_contract(
    result: dict,
    golden: dict,
    screenplay: str,
) -> tuple[float, bool]:
    headings = golden.get("source_headings", [])
    if not headings:
        return 1.0, True
    acts = result.get("act_structure", [])
    sections = _source_scene_sections(headings, screenplay)
    if not isinstance(acts, list) or not acts or sections is None:
        return 0.0, False
    normalized = [tuple(_tokens(heading)) for heading in headings]
    starts = [
        _boundary_start_index(act.get("start_scene"), normalized, sections)
        if isinstance(act, dict)
        else None
        for act in acts
    ]
    if (
        any(start is None for start in starts)
        or starts[0] != 0
        or any(
            current <= previous
            for previous, current in zip(starts, starts[1:], strict=False)
        )
    ):
        return 0.0, False

    boundaries: list[tuple[int, int]] = []
    for index, (act, start) in enumerate(zip(acts, starts, strict=True)):
        assert isinstance(act, dict) and start is not None
        expected_end = starts[index + 1] - 1 if index + 1 < len(starts) else len(headings) - 1
        end_tokens = tuple(_tokens(act.get("end_scene")))
        exact_end = expected_end if end_tokens == normalized[expected_end] else None
        description_grounded = exact_end is None and any(
            _source_fragment_grounded(act.get("end_scene"), sections[scene_index])
            for scene_index in range(start, expected_end + 1)
        )
        if exact_end != expected_end and not description_grounded:
            return 0.0, False
        boundaries.append((start, expected_end))
    valid = (
        boundaries[0][0] == 0
        and boundaries[-1][1] == len(headings) - 1
        and all(
            current[0] == previous[1] + 1
            for previous, current in zip(boundaries, boundaries[1:], strict=False)
        )
    )
    covered = sum(end - start + 1 for start, end in boundaries)
    score = min(1.0, covered / len(headings)) if valid else 0.0
    return score, valid


def _evidence_grounded(evidence: object, screenplay: str) -> bool:
    if _contains_phrase(screenplay, evidence):
        return True
    citation = re.split(r"\s+[—–-]\s+", str(evidence or ""), maxsplit=1)[0]
    if _contains_phrase(screenplay, citation):
        return True
    return _source_fragment_grounded(citation, screenplay)


def _theme_evidence_contract(
    result: dict,
    golden: dict,
    screenplay: str,
) -> tuple[float, bool]:
    if not golden.get("source_headings"):
        return 1.0, True
    if not screenplay:
        return 0.0, False
    evidence = [
        item
        for theme in result.get("themes", [])
        if isinstance(theme, dict) and isinstance(theme.get("evidence"), list)
        for item in theme["evidence"]
    ]
    if not evidence:
        return 0.0, False
    grounded = [_evidence_grounded(item, screenplay) for item in evidence]
    return sum(grounded) / len(grounded), all(grounded)


def _character_death_names(pattern: str) -> list[str]:
    death_terms = {"dead", "death", "died", "dies", "killed"}
    groups = [group.split("|") for group in re.findall(r"\(\?:([a-z|]+)\)", pattern.lower())]
    if not any(death_terms.intersection(group) for group in groups):
        return []
    for terms in groups:
        if terms and not death_terms.intersection(terms):
            return terms
    return []


def _has_grammatical_character_death(value: str, names: list[str]) -> bool:
    if not names:
        return False
    character = rf"(?:{'|'.join(re.escape(name) for name in names)})"
    patterns = (
        rf"(?i)\b{character}\b\s+(?:is|was|gets|got|becomes|became|lies|lay|lays|remains|remained)\s+(?:\w+\s+){{0,2}}(?:dead|killed)\b",
        rf"(?i)\b{character}\b\s+(?:has|had)\s+(?:been\s+)?(?:died|killed)\b",
        rf"(?i)\b{character}\b\s+(?:dies|died)\b",
        rf"(?i)\b{character}(?:'s|’s)\s+(?:death|killing)\b",
        rf"(?i)\b(?:death|killing)\s+of\s+{character}\b",
        rf"(?i)\b(?:dead|killed)\s+{character}\b",
        rf"(?i)\b{character}\b\s*[,—–-]\s*(?:dead|killed)\b",
    )
    return any(regex_has_affirmed_match(pattern, value) for pattern in patterns)


def _exclusion_contract(result: dict, golden: dict) -> tuple[float, bool, list[str]]:
    serialized = json.dumps(result)
    matches = []
    for pattern in golden.get("forbidden_claim_patterns", []):
        if not regex_has_affirmed_match(pattern, serialized):
            continue
        death_names = _character_death_names(pattern)
        if death_names and not _has_grammatical_character_death(serialized, death_names):
            continue
        matches.append(pattern)
    return (0.0 if matches else 1.0), not matches, matches


def get_assert(output: str, context: dict) -> dict:
    golden_path = _resolve_golden_path(context)
    if not golden_path or not os.path.exists(golden_path):
        return {"pass": False, "score": 0.0, "reason": f"Golden not found: {golden_path}"}
    with open(golden_path) as handle:
        golden = json.load(handle)
    result, json_score = _parse_output(output)
    if result is None:
        return {"pass": False, "score": 0.0, "reason": "Invalid JSON object"}
    field_score, fields_valid = _required_field_score(
        result, golden.get("required_fields", [])
    )
    expected_title = _tokens(golden.get("must_include_title", ""))
    title_valid = _tokens(result.get("title", "")) == expected_title
    act_score, acts_valid = _act_structure_score(result, golden)
    theme_score, themes_valid = _theme_score(result, golden)
    genre_tone_score, genre_tone_valid = _genre_tone_score(result, golden)
    synopsis_score, synopsis_valid = _synopsis_score(result, golden)
    confidence_score, confidence_valid = _confidence_score(result)
    event_score, events_valid, missing_events = _story_event_contract(result, golden)
    screenplay = str(context.get("vars", {}).get("screenplay", ""))
    boundary_score, boundaries_valid = _act_boundary_contract(
        result,
        golden,
        screenplay,
    )
    evidence_score, evidence_valid = _theme_evidence_contract(
        result,
        golden,
        screenplay,
    )
    exclusion_score, exclusions_valid, exclusion_matches = _exclusion_contract(
        result, golden
    )
    scores = {
        "json_valid": json_score,
        "field_completeness": field_score,
        "title_correct": 1.0 if title_valid else 0.0,
        "act_structure": act_score,
        "themes": theme_score,
        "genre_tone_grounding": genre_tone_score,
        "logline_grounding": _logline_score(result, golden),
        "synopsis_grounding": synopsis_score,
        **_journey_conflict_setting_scores(result, golden),
        "confidence_quality": confidence_score,
        "full_source_coverage": event_score,
        "act_boundary_grounding": boundary_score,
        "theme_evidence_grounding": evidence_score,
        "unsupported_claims": exclusion_score,
    }
    weights = {
        "json_valid": 0.05,
        "field_completeness": 0.10,
        "title_correct": 0.05,
        "act_structure": 0.15,
        "themes": 0.15,
        "genre_tone_grounding": 0.10,
        "logline_grounding": 0.10,
        "synopsis_grounding": 0.10,
        "journey_grounding": 0.05,
        "conflict_grounding": 0.05,
        "setting_grounding": 0.05,
        "confidence_quality": 0.05,
    }
    base_total = sum(scores[key] * weight for key, weight in weights.items())
    contract_score = sum(
        scores[key]
        for key in (
            "full_source_coverage",
            "act_boundary_grounding",
            "theme_evidence_grounding",
            "unsupported_claims",
        )
    ) / 4
    total = 0.8 * base_total + 0.2 * contract_score
    hard_gates = all(
        (
            fields_valid,
            title_valid,
            acts_valid,
            themes_valid,
            genre_tone_valid,
            synopsis_valid,
            confidence_valid,
            events_valid,
            boundaries_valid,
            evidence_valid,
            exclusions_valid,
        )
    )
    details = " | ".join(f"{key}={value:.2f}" for key, value in sorted(scores.items()))
    if missing_events:
        details += f" | Required story events missing: {', '.join(missing_events)}"
    if not boundaries_valid:
        details += " | Act boundaries do not partition the exact source headings"
    if not evidence_valid:
        details += " | Theme evidence is not grounded in the source screenplay"
    if exclusion_matches:
        details += f" | Unsupported claim patterns matched: {len(exclusion_matches)}"
    return finalize_score(
        total,
        pass_threshold=PASS_THRESHOLD,
        hard_gates=hard_gates,
        reason=details,
    )
