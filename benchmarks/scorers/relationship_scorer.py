"""Strict source-grounded relationship-capability scorer for promptfoo.

This scorer deliberately evaluates a richer benchmark-only contract than the
runtime ``entity_graph_v1`` structured-output boundary. It must never accept a
runtime bare-list payload by accident or be treated as runtime-default evidence.
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

SCORER_ROOT = Path(__file__).resolve().parent
if str(SCORER_ROOT) not in sys.path:
    sys.path.insert(0, str(SCORER_ROOT))

from score_semantics import finalize_score  # noqa: E402

PASS_THRESHOLD = 1.0


EDGE_FIELDS = frozenset(
    {
        "source_type",
        "source_id",
        "target_type",
        "target_id",
        "relationship_type",
        "direction",
        "evidence",
        "scene_refs",
        "confidence",
    }
)
EVIDENCE_FIELDS = frozenset({"quote", "scene_ref"})
ENTITY_TYPES = frozenset({"character", "location", "prop"})
DIRECTIONS = frozenset({"symmetric", "source_to_target", "target_to_source"})


class ContractError(ValueError):
    """Raised when model output violates the exact JSON contract."""


@dataclass(frozen=True)
class Match:
    requirement: dict
    edge_index: int | None
    orientation: int = 0


def _resolve_golden_path(context: dict) -> str:
    path = context.get("vars", {}).get("golden_path", "")
    if path and not os.path.isabs(path):
        path = os.path.join(os.path.dirname(__file__), "..", path)
    return path


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    result: dict = {}
    for key, value in pairs:
        if key in result:
            raise ContractError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _parse_output(output: str) -> list[dict]:
    try:
        parsed = json.loads(
            output.strip(),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=lambda value: (_ for _ in ()).throw(
                ContractError(f"invalid JSON number: {value}")
            ),
        )
    except (json.JSONDecodeError, ContractError) as exc:
        raise ContractError(f"invalid strict JSON: {exc}") from exc
    if not isinstance(parsed, dict) or set(parsed) != {"edges"}:
        raise ContractError('top level must be exactly {"edges": [...]}')
    edges = parsed["edges"]
    if not isinstance(edges, list):
        raise ContractError("edges must be a list")
    if any(not isinstance(edge, dict) for edge in edges):
        raise ContractError("every edge must be an object")
    return edges


def _canonical_heading(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "").replace(r"\-", "-").strip())


def _source_tokens(value: object) -> str:
    text = str(value or "")
    text = re.sub(r"\\([^\w\s])", r"\1", text)
    return " ".join(re.findall(r"[a-z0-9]+", text.casefold()))


def _scene_lines(screenplay: object) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    parents: list[str] = []
    for raw_line in str(screenplay or "").splitlines():
        line = _canonical_heading(raw_line)
        if re.match(r"^BEGIN FLASHBACK:\s+(?:INT\.|EXT\.)", line):
            if current is not None:
                parents.append(current)
            current = line
            sections.setdefault(current, []).append(raw_line)
        elif re.match(r"^(?:INT\.|EXT\.)", line):
            parents.clear()
            current = line
            sections.setdefault(current, []).append(raw_line)
        elif current is not None:
            sections[current].append(raw_line)
            if line.rstrip(".") == "END FLASHBACK" and parents:
                current = parents.pop()
    return sections


def _scene_sections(screenplay: object) -> dict[str, str]:
    return {
        heading: "\n".join(lines)
        for heading, lines in _scene_lines(screenplay).items()
    }


def _schema_errors(edge: dict, index: int) -> list[str]:
    prefix = f"edge[{index}]"
    errors: list[str] = []
    if set(edge) != EDGE_FIELDS:
        missing = sorted(EDGE_FIELDS - set(edge))
        extra = sorted(set(edge) - EDGE_FIELDS)
        errors.append(f"{prefix} exact keys failed (missing={missing}, extra={extra})")
    for field in ("source_id", "target_id", "relationship_type"):
        value = edge.get(field)
        if not isinstance(value, str) or not value.strip() or value != value.strip():
            errors.append(f"{prefix}.{field} must be a non-empty trimmed string")
    for field in ("source_type", "target_type"):
        if edge.get(field) not in ENTITY_TYPES:
            errors.append(f"{prefix}.{field} must be one of {sorted(ENTITY_TYPES)}")
    if edge.get("direction") not in DIRECTIONS:
        errors.append(f"{prefix}.direction must be one of {sorted(DIRECTIONS)}")
    confidence = edge.get("confidence")
    if (
        not isinstance(confidence, (int, float))
        or isinstance(confidence, bool)
        or not 0.0 <= confidence <= 1.0
    ):
        errors.append(f"{prefix}.confidence must be a number from 0 to 1")
    scene_refs = edge.get("scene_refs")
    if not isinstance(scene_refs, list) or not scene_refs:
        errors.append(f"{prefix}.scene_refs must be a non-empty list")
    elif (
        any(not isinstance(ref, str) or not ref.strip() or ref != ref.strip() for ref in scene_refs)
        or len(set(scene_refs)) != len(scene_refs)
    ):
        errors.append(f"{prefix}.scene_refs must contain unique, non-empty strings")
    evidence = edge.get("evidence")
    if not isinstance(evidence, list) or not 2 <= len(evidence) <= 4:
        errors.append(f"{prefix}.evidence must contain 2-4 objects")
    else:
        seen_pairs: set[tuple[str, str]] = set()
        for evidence_index, item in enumerate(evidence):
            item_prefix = f"{prefix}.evidence[{evidence_index}]"
            if not isinstance(item, dict) or set(item) != EVIDENCE_FIELDS:
                errors.append(f"{item_prefix} must have exactly quote and scene_ref")
                continue
            quote = item.get("quote")
            ref = item.get("scene_ref")
            quote_length = len(_source_tokens(quote).split())
            if not isinstance(quote, str) or not 2 <= quote_length <= 80:
                errors.append(f"{item_prefix}.quote must be a 2-80 word source excerpt")
            if not isinstance(ref, str) or not ref.strip() or ref != ref.strip():
                errors.append(f"{item_prefix}.scene_ref must be a non-empty trimmed string")
            pair = (str(quote), str(ref))
            if pair in seen_pairs:
                errors.append(f"{item_prefix} duplicates an earlier evidence item")
            seen_pairs.add(pair)
    return errors


def _normalize_label(value: object) -> str:
    return re.sub(r"[\s_/]+", "-", str(value or "").casefold().strip()).strip("-")


def _orientation(edge: dict, requirement: dict) -> int:
    edge_source = (edge.get("source_type"), edge.get("source_id"))
    edge_target = (edge.get("target_type"), edge.get("target_id"))
    expected_source = (requirement.get("source_type"), requirement.get("source_id"))
    expected_target = (requirement.get("target_type"), requirement.get("target_id"))
    if edge_source == expected_source and edge_target == expected_target:
        return 1
    if edge_source == expected_target and edge_target == expected_source:
        return -1
    return 0


def _type_matches(edge: dict, requirement: dict) -> bool:
    actual = _normalize_label(edge.get("relationship_type"))
    allowed = {
        _normalize_label(value)
        for value in requirement.get("relationship_type_keywords", [])
        if _normalize_label(value)
    }
    return bool(actual) and actual in allowed


def _match_edges(edges: list[dict], requirements: list[dict]) -> list[Match]:
    used: set[int] = set()
    matches: list[Match] = []
    for requirement in requirements:
        candidate: tuple[int, int] | None = None
        for index, edge in enumerate(edges):
            orientation = _orientation(edge, requirement)
            if index not in used and orientation and _type_matches(edge, requirement):
                candidate = (index, orientation)
                break
        if candidate is None:
            matches.append(Match(requirement=requirement, edge_index=None))
        else:
            index, orientation = candidate
            used.add(index)
            matches.append(Match(requirement, index, orientation))
    return matches


def _direction_valid(edge: dict, requirement: dict, orientation: int) -> bool:
    expected = requirement.get("direction")
    if orientation == -1:
        expected = {
            "source_to_target": "target_to_source",
            "target_to_source": "source_to_target",
        }.get(expected, expected)
    return edge.get("direction") == expected


def _confidence_valid(edge: dict, requirement: dict) -> bool:
    value = edge.get("confidence")
    minimum = requirement.get("min_confidence", 0.0)
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and isinstance(minimum, (int, float))
        and 0.0 <= minimum <= value <= 1.0
    )


def _scene_refs_valid(edge: dict, requirement: dict) -> bool:
    actual = edge.get("scene_refs")
    expected = requirement.get("scene_refs")
    if not isinstance(actual, list) or not isinstance(expected, list):
        return False
    return {_canonical_heading(value) for value in actual} == {
        _canonical_heading(value) for value in expected
    } and len(actual) == len(expected)


def _evidence_valid(edge: dict, requirement: dict, scenes: dict[str, str]) -> bool:
    evidence = edge.get("evidence")
    refs = edge.get("scene_refs")
    anchors = [_source_tokens(value) for value in requirement.get("must_mention_evidence", [])]
    if not isinstance(evidence, list) or not isinstance(refs, list) or not anchors:
        return False
    canonical_refs = {_canonical_heading(value) for value in refs}
    covered_anchors: set[int] = set()
    for item in evidence:
        if not isinstance(item, dict):
            return False
        quote = _source_tokens(item.get("quote"))
        ref = _canonical_heading(item.get("scene_ref"))
        if ref not in canonical_refs or ref not in scenes:
            return False
        if not quote or quote not in _source_tokens(scenes[ref]):
            return False
        item_anchors = {index for index, anchor in enumerate(anchors) if anchor in quote}
        if not item_anchors:
            return False
        covered_anchors.update(item_anchors)
    return len(covered_anchors) >= min(2, len(anchors))


def get_assert(output: str, context: dict) -> dict:
    """Score exact schema, full edge coverage, and source-bound evidence."""
    try:
        with open(_resolve_golden_path(context)) as handle:
            golden = json.load(handle)
        edges = _parse_output(output)
    except Exception as exc:
        return {"pass": False, "score": 0.0, "reason": f"Contract failure: {exc}"}

    requirements = golden.get("must_find_relationships", [])
    if not isinstance(requirements, list) or not requirements:
        return {"pass": False, "score": 0.0, "reason": "Golden has no relationships"}
    schema_errors = [
        error for index, edge in enumerate(edges) for error in _schema_errors(edge, index)
    ]
    matches = _match_edges(edges, requirements)
    scenes = _scene_sections(context.get("vars", {}).get("screenplay", ""))
    found = [match for match in matches if match.edge_index is not None]
    direction_ok = 0
    confidence_ok = 0
    scene_ok = 0
    evidence_ok = 0
    for match in found:
        edge = edges[match.edge_index]  # type: ignore[index]
        direction_ok += _direction_valid(edge, match.requirement, match.orientation)
        confidence_ok += _confidence_valid(edge, match.requirement)
        scene_ok += _scene_refs_valid(edge, match.requirement)
        evidence_ok += _evidence_valid(edge, match.requirement, scenes)

    requirement_count = len(requirements)
    edge_count = len(edges)
    schema_fraction = max(0.0, 1.0 - len(schema_errors) / max(1, edge_count))
    coverage_fraction = len(found) / requirement_count
    precision_fraction = len(found) / edge_count if edge_count else 0.0
    fractions = {
        "schema": schema_fraction,
        "coverage": coverage_fraction,
        "precision": precision_fraction,
        "direction": direction_ok / requirement_count,
        "confidence": confidence_ok / requirement_count,
        "scene_refs": scene_ok / requirement_count,
        "evidence": evidence_ok / requirement_count,
    }
    weights = {
        "schema": 0.15,
        "coverage": 0.20,
        "precision": 0.10,
        "direction": 0.10,
        "confidence": 0.10,
        "scene_refs": 0.15,
        "evidence": 0.20,
    }
    score = sum(fractions[name] * weights[name] for name in fractions)
    missing = [
        match.requirement.get("relationship_id", "unknown")
        for match in matches
        if match.edge_index is None
    ]
    all_exact = (
        not schema_errors
        and edge_count == requirement_count
        and len(found) == requirement_count
        and precision_fraction == 1.0
        and direction_ok == requirement_count
        and confidence_ok == requirement_count
        and scene_ok == requirement_count
        and evidence_ok == requirement_count
    )
    diagnostics = ", ".join(f"{name}={value:.2f}" for name, value in fractions.items())
    reason = f"Strict relationship contract: {diagnostics}; edges={edge_count}/{requirement_count}"
    if missing:
        reason += f"; missing/wrong-type={missing}"
    if schema_errors:
        reason += f"; schema_errors={schema_errors[:3]}"
    return finalize_score(
        score,
        pass_threshold=PASS_THRESHOLD,
        hard_gates=all_exact,
        reason=reason,
    )
