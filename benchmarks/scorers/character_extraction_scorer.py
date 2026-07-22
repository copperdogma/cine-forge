"""Deterministic source-grounded scorer for character extraction."""

from __future__ import annotations

import json
import os
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

SCORER_ROOT = Path(__file__).resolve().parent
if str(SCORER_ROOT) not in sys.path:
    sys.path.insert(0, str(SCORER_ROOT))

from score_semantics import finalize_score  # noqa: E402

STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "by",
    "for",
    "from",
    "in",
    "is",
    "of",
    "on",
    "the",
    "to",
    "with",
}
TOP_LEVEL_FIELDS = {
    "character_id",
    "name",
    "aliases",
    "description",
    "explicit_evidence",
    "inferred_traits",
    "scene_presence",
    "dialogue_summary",
    "narrative_role",
    "relationships",
    "overall_confidence",
}
EVIDENCE_FIELDS = {"trait", "quote", "source_scene"}
TRAIT_FIELDS = {"trait", "value", "confidence", "rationale"}
RELATIONSHIP_FIELDS = {
    "target_character",
    "relationship_type",
    "evidence",
    "confidence",
}
NARRATIVE_ROLES = {"protagonist", "supporting"}
SCENE_HEADING = re.compile(r"^(?:BEGIN FLASHBACK:\s*)?(?:INT|EXT)\.\s+\S", re.IGNORECASE)
RELATIONSHIP_SIGNALS = {
    "sibling": {"sibling", "siblings", "sister", "brother", "sis"},
    "parent": {"parent", "parents", "father", "mother", "dad", "mom", "ma", "pa"},
    "adversary": {
        "adversary",
        "enemy",
        "fight",
        "fights",
        "attack",
        "attacks",
        "kidnap",
        "kidnapped",
        "kill",
        "threat",
        "gunpoint",
        "gang",
    },
    "romantic_ex": {"ex", "former", "boyfriend", "girlfriend", "romantic"},
    "family": {"family", "relative", "kin"},
}
RELATIONSHIP_DENIAL_RE = re.compile(
    r"(?:\b(?:never|not)\s+(?:establishes?|shows?|states?|supports?|confirms?)\b|"
    r"\bno\s+(?:evidence|support|basis)\b|"
    r"\b(?:is|are|was|were)\s+not\s+"
    r"(?:siblings?|family|related|parent|father|mother|adversaries|enemies|romantic)\b|"
    r"\bunrelated\b)",
    flags=re.IGNORECASE,
)
PASS_THRESHOLD = 0.65


def _resolve_golden_path(context: dict) -> str:
    golden_path = context.get("vars", {}).get("golden_path", "")
    if golden_path and not os.path.isabs(golden_path):
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for candidate in (os.path.join(base, golden_path), os.path.join(os.getcwd(), golden_path)):
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


def _normalize(value: object) -> str:
    return " ".join(re.findall(r"[A-Z0-9]+", str(value or "").upper()))


def _canonical_heading(value: object) -> str:
    unescaped = re.sub(r"\\([\\-])", r"\1", str(value or "").strip())
    return " ".join(unescaped.upper().split())


def _tokens(value: object) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", str(value or "").lower())
        if len(token) > 2 and token not in STOP_WORDS
    }


def _concept_matches(text: object, concept: object, threshold: float = 0.5) -> bool:
    expected = _tokens(concept)
    return bool(expected) and len(expected & _tokens(text)) / len(expected) >= threshold


def _concept_recall(text: object, concepts: list[str], threshold: float = 0.5) -> float:
    if not concepts:
        return 1.0
    return sum(_concept_matches(text, concept, threshold) for concept in concepts) / len(concepts)


def _find_golden(all_golden: dict, character_name: str) -> dict | None:
    normalized = _normalize(character_name)
    return next(
        (value for key, value in all_golden.items() if _normalize(key) == normalized),
        None,
    )


def _identity_score(result: dict, golden: dict) -> tuple[float, bool]:
    name_valid = _normalize(result.get("name")) == _normalize(golden.get("name"))
    identifier_valid = result.get("character_id") == golden.get("character_id")
    score = (float(name_valid) + float(identifier_valid)) / 2
    return score, name_valid and identifier_valid


def _alias_score(result: dict, golden: dict) -> tuple[float, bool]:
    expected = {_normalize(value) for value in golden.get("aliases", []) if _normalize(value)}
    actual_values = result.get("aliases", [])
    actual = (
        {_normalize(value) for value in actual_values if _normalize(value)}
        if isinstance(actual_values, list)
        else set()
    )
    if not expected:
        return (1.0 if not actual else 0.0), not actual
    overlap = len(expected & actual)
    recall = overlap / len(expected)
    precision = overlap / len(actual) if actual else 0.0
    score = 2 * recall * precision / (recall + precision) if recall + precision else 0.0
    return score, actual == expected


def _relationship_type_key(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")


def _relationship_evidence_valid(item: dict, screenplay: str) -> bool:
    evidence = str(item.get("evidence", ""))
    if not evidence.strip() or RELATIONSHIP_DENIAL_RE.search(evidence):
        return False

    relation_key = _relationship_type_key(item.get("relationship_type"))
    relation_signals = RELATIONSHIP_SIGNALS.get(
        relation_key,
        _tokens(item.get("relationship_type")),
    )
    target_tokens = _tokens(item.get("target_character"))
    evidence_tokens = _tokens(evidence)
    source_tokens = _tokens(screenplay)
    target_is_relationship_label = bool(target_tokens) and target_tokens <= relation_signals
    evidence_names_target = bool(target_tokens & evidence_tokens) or (
        target_is_relationship_label and bool(relation_signals & evidence_tokens)
    )
    source_names_target = bool(target_tokens & source_tokens) or (
        target_is_relationship_label and bool(relation_signals & source_tokens)
    )
    return all(
        (
            evidence_names_target,
            source_names_target,
            bool(relation_signals & evidence_tokens),
            bool(relation_signals & source_tokens),
        )
    )


def _relationship_score(
    result: dict,
    golden: dict,
    screenplay: str,
) -> tuple[float, bool]:
    expected = {
        (_normalize(item.get("target")), _normalize(item.get("type")))
        for item in golden.get("must_have_relationships", [])
        if isinstance(item, dict)
    }
    relationships = result.get("relationships", [])
    if not isinstance(relationships, list):
        return 0.0, False
    actual = {
        (
            _normalize(item.get("target_character")),
            _normalize(item.get("relationship_type")),
        )
        for item in relationships
        if isinstance(item, dict)
    }
    no_duplicates = len(actual) == len(relationships)
    if not expected:
        return (1.0 if not actual else 0.0), not actual and no_duplicates
    overlap = len(expected & actual)
    recall = overlap / len(expected)
    precision = overlap / len(actual) if actual else 0.0
    f1 = 2 * recall * precision / (recall + precision) if recall + precision else 0.0
    expected_evidence_validity = [
        _relationship_evidence_valid(item, screenplay)
        for item in relationships
        if isinstance(item, dict)
        and (
            _normalize(item.get("target_character")),
            _normalize(item.get("relationship_type")),
        )
        in expected
    ]
    evidence_score = (
        sum(expected_evidence_validity) / len(expected) if expected else 1.0
    )
    all_evidence_valid = (
        len(expected_evidence_validity) == len(expected)
        and all(expected_evidence_validity)
    )
    return f1 * evidence_score, actual == expected and no_duplicates and all_evidence_valid


def _scene_score(result: dict, golden: dict) -> tuple[float, bool]:
    expected = {_canonical_heading(value) for value in golden.get("must_mention_scenes", [])}
    values = result.get("scene_presence", [])
    actual = (
        {_canonical_heading(value) for value in values if _canonical_heading(value)}
        if isinstance(values, list)
        else set()
    )
    if not expected:
        return 1.0, True
    overlap = len(expected & actual)
    recall = overlap / len(expected)
    precision = overlap / len(actual) if actual else 0.0
    f1 = 2 * recall * precision / (recall + precision) if recall + precision else 0.0
    return f1, actual == expected


def _quote_grounded(quote: str, screenplay: str) -> bool:
    quote_tokens = re.findall(r"[a-z0-9]+", quote.lower())
    source_tokens = re.findall(r"[a-z0-9]+", screenplay.lower())
    if len(quote_tokens) < 3 or not source_tokens:
        return False
    normalized_quote = " ".join(quote_tokens)
    normalized_source = " ".join(source_tokens)
    if normalized_quote in normalized_source:
        return True
    width = len(quote_tokens)
    return any(
        SequenceMatcher(None, quote_tokens, source_tokens[index : index + width]).ratio() >= 0.75
        for index in range(max(1, len(source_tokens) - width + 1))
    )


def _scene_sections(screenplay: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current_heading = ""
    for line in screenplay.splitlines():
        stripped = line.strip()
        if SCENE_HEADING.match(stripped):
            current_heading = _canonical_heading(stripped)
            sections.setdefault(current_heading, []).append(stripped)
        elif current_heading:
            sections[current_heading].append(stripped)
    return {heading: "\n".join(lines) for heading, lines in sections.items()}


def _evidence_is_grounded(item: dict, sections: dict[str, str]) -> bool:
    source_scene = _canonical_heading(item.get("source_scene"))
    governed_text = sections.get(source_scene, "")
    return bool(governed_text) and _quote_grounded(str(item.get("quote", "")), governed_text)


def _evidence_scores(
    result: dict,
    golden: dict,
    screenplay: str,
) -> tuple[float, float, bool]:
    evidence = result.get("explicit_evidence", [])
    if not isinstance(evidence, list) or any(not isinstance(item, dict) for item in evidence):
        return 0.0, 0.0, False
    quotes = [str(item.get("quote", "")) for item in evidence]
    quote_text = " ".join(quotes)
    required_recall = _concept_recall(
        quote_text,
        golden.get("must_have_evidence", []),
        threshold=0.7,
    )
    if not evidence:
        return required_recall, 0.0, False
    sections = _scene_sections(screenplay)
    grounded = sum(
        _evidence_is_grounded(item, sections)
        and bool(str(item.get("trait", "")).strip())
        for item in evidence
    )
    grounding = grounded / len(evidence)
    return required_recall, grounding, required_recall == 1.0 and grounding == 1.0


def _valid_confidence(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and 0.0 <= value <= 1.0
    )


def _nonempty_strings(value: object, *, unique: bool = False) -> bool:
    if not isinstance(value, list) or not all(
        isinstance(item, str) and bool(item.strip()) for item in value
    ):
        return False
    normalized = [_normalize(item) for item in value]
    return not unique or len(normalized) == len(set(normalized))


def _schema_score(result: dict) -> tuple[float, bool]:
    traits = result.get("inferred_traits", [])
    traits_valid = isinstance(traits, list) and all(
        isinstance(item, dict)
        and set(item) == TRAIT_FIELDS
        and all(bool(str(item[field]).strip()) for field in ("trait", "value", "rationale"))
        and _valid_confidence(item.get("confidence"))
        for item in traits
    )
    evidence = result.get("explicit_evidence")
    evidence_valid = isinstance(evidence, list) and all(
        isinstance(item, dict)
        and set(item) == EVIDENCE_FIELDS
        and all(bool(str(item[field]).strip()) for field in EVIDENCE_FIELDS)
        for item in evidence
    )
    relationships = result.get("relationships")
    relationships_valid = isinstance(relationships, list) and all(
        isinstance(item, dict)
        and set(item) == RELATIONSHIP_FIELDS
        and all(
            isinstance(item.get(field), str) and bool(item[field].strip())
            for field in ("target_character", "relationship_type", "evidence")
        )
        and _valid_confidence(item.get("confidence"))
        for item in relationships
    )
    scalar_valid = all(
        isinstance(result.get(field), str) and bool(result[field].strip())
        for field in ("character_id", "name", "description", "dialogue_summary", "narrative_role")
    )
    checks = (
        float(set(result) == TOP_LEVEL_FIELDS),
        float(_valid_confidence(result.get("overall_confidence"))),
        float(traits_valid),
        float(evidence_valid),
        float(relationships_valid),
        float(scalar_valid),
        float(_nonempty_strings(result.get("aliases"), unique=True)),
        float(_nonempty_strings(result.get("scene_presence"), unique=True)),
        float(bool(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", str(result.get("character_id", ""))))),
        float(result.get("narrative_role") in NARRATIVE_ROLES),
    )
    score = sum(checks) / len(checks)
    valid = all(value == 1.0 for value in checks)
    return score, valid


def get_assert(output: str, context: dict) -> dict:
    golden_path = _resolve_golden_path(context)
    character_name = context.get("vars", {}).get("character_name", "")
    if not golden_path or not os.path.exists(golden_path) or not character_name:
        return {"pass": False, "score": 0.0, "reason": "Missing golden or character_name"}
    with open(golden_path) as handle:
        all_golden = json.load(handle)
    golden = _find_golden(all_golden, character_name)
    if golden is None:
        return {"pass": False, "score": 0.0, "reason": f"No golden for {character_name}"}
    result, json_score = _parse_output(output)
    if result is None:
        return {"pass": False, "score": 0.0, "reason": "Invalid JSON object"}
    identity_score, identity_valid = _identity_score(result, golden)
    alias_score, aliases_valid = _alias_score(result, golden)
    screenplay = str(context.get("vars", {}).get("screenplay", ""))
    relationship_score, relationships_valid = _relationship_score(
        result,
        golden,
        screenplay,
    )
    scene_score, scenes_valid = _scene_score(result, golden)
    evidence_recall, source_grounding, evidence_valid = _evidence_scores(
        result,
        golden,
        screenplay,
    )
    schema_score, schema_valid = _schema_score(result)
    trait_text = json.dumps(result.get("inferred_traits", [])) + " " + str(
        result.get("description", "")
    )
    scores = {
        "json_valid": json_score,
        "identity": identity_score,
        "narrative_role": float(result.get("narrative_role") == golden.get("narrative_role")),
        "trait_coverage": _concept_recall(trait_text, golden.get("key_traits", [])),
        "relationship_accuracy": relationship_score,
        "evidence_recall": evidence_recall,
        "source_grounding": source_grounding,
        "fact_recall": _concept_recall(json.dumps(result), golden.get("key_facts", [])),
        "scene_accuracy": scene_score,
        "schema_quality": schema_score,
        "alias_accuracy": alias_score,
    }
    weights = {
        "json_valid": 0.05,
        "identity": 0.10,
        "narrative_role": 0.05,
        "trait_coverage": 0.10,
        "relationship_accuracy": 0.15,
        "evidence_recall": 0.10,
        "source_grounding": 0.15,
        "fact_recall": 0.10,
        "scene_accuracy": 0.10,
        "schema_quality": 0.05,
        "alias_accuracy": 0.05,
    }
    total = sum(scores[key] * weight for key, weight in weights.items())
    hard_gates = all(
        (
            identity_valid,
            aliases_valid,
            relationships_valid,
            scenes_valid,
            evidence_valid,
            schema_valid,
            scores["narrative_role"] == 1.0,
            scores["trait_coverage"] == 1.0,
            scores["fact_recall"] == 1.0,
        )
    )
    details = " | ".join(f"{key}={value:.2f}" for key, value in sorted(scores.items()))
    return finalize_score(
        total,
        pass_threshold=PASS_THRESHOLD,
        hard_gates=hard_gates,
        reason=details,
    )
