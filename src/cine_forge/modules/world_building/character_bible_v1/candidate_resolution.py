"""Candidate preparation and adjudication for character bible extraction."""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

from cine_forge.ai import adjudicate_entity_candidates
from cine_forge.schemas import EntityAdjudicationDecision

Adjudicator = Callable[..., tuple[list[EntityAdjudicationDecision], dict[str, Any]]]

CHARACTER_STOPWORDS = {
    "A",
    "AN",
    "AND",
    "AS",
    "AT",
    "BACK",
    "BLACK",
    "BEGIN",
    "CONTINUOUS",
    "CUT",
    "DAY",
    "END",
    "ENDFLASHBACK",
    "EXT",
    "FADE",
    "FOR",
    "FROM",
    "GO",
    "HE",
    "HER",
    "HIS",
    "I",
    "IN",
    "INT",
    "IT",
    "LATER",
    "NIGHT",
    "NO",
    "NOBODY",
    "NOW",
    "OF",
    "ON",
    "OUT",
    "PRESENT",
    "SHE",
    "THE",
    "THEY",
    "THWACK",
    "TO",
    "UNKNOWN",
    "UNSPECIFIED",
    "WE",
    "YOU",
    "LUXURIOUS",
    "CLEAN",
    "DIMLY",
    "LIT",
    "DISCARDED",
    "BOTTLES",
    "RUG",
    "RUSTY",
    "WEIGHTS",
    "WEEDS",
    "OPENING",
    "TITLE",
}


def prepare_character_candidates(
    canonical_script: dict[str, Any],
    scene_index: dict[str, Any],
    discovery_results: dict[str, Any] | None,
    min_appearances: int,
    model: str,
    *,
    adjudicator: Adjudicator | None = None,
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, Any],
]:
    discovery_backed = bool(discovery_results and discovery_results.get("characters"))
    if discovery_backed:
        ranked, candidates = _build_discovery_character_candidates(
            canonical_script=canonical_script,
            scene_index=scene_index,
            discovery_results=discovery_results,
        )
    else:
        characters = _aggregate_characters(scene_index)
        ranked = _rank_characters(characters, canonical_script, scene_index)
        candidates = [
            candidate
            for candidate in ranked
            if (candidate["scene_count"] >= min_appearances)
            or (candidate["dialogue_count"] >= 1)
        ]

    if not discovery_backed:
        candidates = [c for c in candidates if _is_plausible_character_name(c["name"])]
    candidates, rejected, decisions, cost = _adjudicate_candidates(
        candidates=candidates,
        script_text=canonical_script["script_text"],
        model=model,
        adjudicator=adjudicator or adjudicate_entity_candidates,
    )
    return ranked, candidates, rejected, decisions, cost


def _build_discovery_character_candidates(
    canonical_script: dict[str, Any],
    scene_index: dict[str, Any],
    discovery_results: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    approved_names: set[str] = set()
    for name in discovery_results["characters"]:
        normalized = _normalize_character_name(name)
        if normalized:
            approved_names.add(normalized)

    print(f"[character_bible] Using {len(approved_names)} characters from discovery results.")
    all_chars = _aggregate_characters(scene_index)
    ranked = _rank_characters(all_chars, canonical_script, scene_index)
    candidates = [
        {
            **candidate,
            "source_hint": "entity_discovery+scene_index.unique_characters",
        }
        for candidate in ranked
        if candidate["name"] in approved_names
    ]

    # Discovery may contain characters the scene parser normalized differently
    # (e.g. "THUG 1"/"THUG 2" collapsed to "THUG", "YOUNG MARINER" to "MARINER").
    # Create stub entries so they still get extracted.
    matched_names = {candidate["name"] for candidate in candidates}
    for name in sorted(approved_names - matched_names):
        candidates.append(
            {
                "name": name,
                "scene_count": 0,
                "dialogue_count": 0,
                "score": 0,
                "scene_presence": [],
                "source_hint": "entity_discovery",
            }
        )

    candidates.sort(key=lambda item: item["score"], reverse=True)
    return ranked, candidates


def _aggregate_characters(scene_index: dict[str, Any]) -> list[str]:
    raw_names = scene_index.get("unique_characters", [])
    normalized = [_normalize_character_name(n) for n in raw_names]
    plausible = [n for n in normalized if _is_plausible_character_name(n)]
    base_tokens = {n for n in plausible if " " not in n and len(n) >= 4}
    unique = [n for n in plausible if not _looks_like_derivative_noise(n, base_tokens)]
    return sorted(list(set(unique)))


def _rank_characters(
    names: list[str], script: dict[str, Any], index: dict[str, Any]
) -> list[dict[str, Any]]:
    scene_counts = {name: 0 for name in names}
    scene_presence = {name: [] for name in names}
    for entry in index.get("entries", []):
        for raw_char in entry.get("characters_present", []):
            norm = _normalize_character_name(raw_char)
            if norm in scene_counts:
                scene_counts[norm] += 1
                if entry["scene_id"] not in scene_presence[norm]:
                    scene_presence[norm].append(entry["scene_id"])

    script_text = script.get("script_text", "")
    dialogue_counts = {name: 0 for name in names}
    for line in script_text.splitlines():
        norm = _normalize_character_name(line)
        if norm in dialogue_counts:
            dialogue_counts[norm] += 1

    results = []
    for name in names:
        results.append(
            {
                "name": name,
                "scene_count": scene_counts[name],
                "scene_presence": scene_presence[name],
                "dialogue_count": dialogue_counts[name],
                "score": (scene_counts[name] * 2) + dialogue_counts[name],
            }
        )

    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def _adjudicate_candidates(
    candidates: list[dict[str, Any]],
    script_text: str,
    model: str,
    *,
    adjudicator: Adjudicator = adjudicate_entity_candidates,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    if not candidates:
        return [], [], [], _empty_cost(model)

    adjudication_input = [
        {
            "candidate": item["name"],
            "scene_count": item["scene_count"],
            "dialogue_count": item["dialogue_count"],
            "scene_presence": item["scene_presence"][:8],
            "source_hint": item.get("source_hint", "scene_index.unique_characters"),
        }
        for item in candidates
    ]
    decisions, cost = adjudicator(
        entity_type="character",
        candidates=adjudication_input,
        script_text=script_text,
        model=model,
    )

    source_by_name = {item["name"]: item for item in candidates}
    merged: dict[str, dict[str, Any]] = {}
    rejected: list[dict[str, Any]] = []
    decision_log: list[dict[str, Any]] = []
    for decision in decisions:
        source = source_by_name.get(decision.candidate)
        if not source:
            decision_log.append(
                {
                    "candidate": decision.candidate,
                    "decision_verdict": decision.verdict,
                    "target_entity_type": decision.target_entity_type,
                    "canonical_name": decision.canonical_name,
                    "llm_rationale": decision.rationale,
                    "llm_confidence": decision.confidence,
                    "outcome": "ignored_unknown_candidate",
                }
            )
            continue
        if decision.verdict != "valid":
            entry = _decision_to_rejection(decision)
            rejected.append(entry)
            decision_log.append({**entry, "outcome": "rejected_by_verdict"})
            continue
        canonical, resolution_mode = _resolve_character_name(
            decision=decision,
            original_candidate=source["name"],
        )
        if not _is_plausible_character_name(canonical):
            entry = {
                **_decision_to_rejection(decision),
                "resolution_mode": resolution_mode,
                "outcome": "rejected_after_resolution",
                "rationale": "resolved candidate failed plausibility checks",
            }
            rejected.append(entry)
            decision_log.append(entry)
            continue
        if resolution_mode == "fallback_to_original_candidate":
            decision_log.append(
                {
                    **_decision_to_rejection(decision),
                    "resolved_name": canonical,
                    "resolution_mode": resolution_mode,
                    "outcome": "accepted_after_fallback",
                }
            )
        else:
            decision_log.append(
                {
                    **_decision_to_rejection(decision),
                    "resolved_name": canonical,
                    "resolution_mode": resolution_mode,
                    "outcome": "accepted",
                }
            )

        _merge_valid_candidate(
            merged=merged,
            canonical=canonical,
            source=source,
            canonical_is_candidate=canonical in source_by_name,
        )

    _annotate_surviving_names(decision_log=decision_log, merged=merged)
    approved = sorted(
        [_public_candidate(candidate) for candidate in merged.values()],
        key=lambda item: item["score"],
        reverse=True,
    )
    return approved, rejected, decision_log, cost


def _resolve_character_name(
    decision: EntityAdjudicationDecision, original_candidate: str
) -> tuple[str, str]:
    canonical_candidate = _normalize_character_name(
        decision.canonical_name or decision.candidate
    )
    if _is_plausible_character_name(canonical_candidate):
        return canonical_candidate, "canonical_or_candidate"

    fallback = _normalize_character_name(original_candidate)
    if _is_plausible_character_name(fallback):
        return fallback, "fallback_to_original_candidate"

    return canonical_candidate, "canonical_invalid_and_fallback_invalid"


def _decision_to_rejection(decision: EntityAdjudicationDecision) -> dict[str, Any]:
    return {
        "candidate": decision.candidate,
        "decision_verdict": decision.verdict,
        "target_entity_type": decision.target_entity_type,
        "canonical_name": decision.canonical_name,
        "llm_rationale": decision.rationale,
        "llm_confidence": decision.confidence,
    }


def _merge_valid_candidate(
    *,
    merged: dict[str, dict[str, Any]],
    canonical: str,
    source: dict[str, Any],
    canonical_is_candidate: bool,
) -> None:
    existing = merged.get(canonical)
    if not existing:
        merged[canonical] = _new_candidate_group(
            canonical=canonical,
            source=source,
            canonical_is_candidate=canonical_is_candidate,
        )
        return

    source_scene_presence = list(source["scene_presence"])
    combined_scene_presence = sorted(
        list(set(existing["scene_presence"] + source_scene_presence))
    )
    if combined_scene_presence:
        existing["scene_count"] = len(combined_scene_presence)
    else:
        existing["scene_count"] += source["scene_count"]
    existing["dialogue_count"] += source["dialogue_count"]
    existing["scene_presence"] = combined_scene_presence
    _update_representative_name(existing, source)
    _add_aliases(existing, canonical, source["name"])
    existing["score"] = (existing["scene_count"] * 2) + existing["dialogue_count"]


def _new_candidate_group(
    *,
    canonical: str,
    source: dict[str, Any],
    canonical_is_candidate: bool,
) -> dict[str, Any]:
    scene_presence = list(source["scene_presence"])
    scene_count = len(scene_presence) if scene_presence else source["scene_count"]
    name = source["name"] if canonical_is_candidate else canonical
    group = {
        "name": name,
        "aliases": [],
        "scene_count": scene_count,
        "dialogue_count": source["dialogue_count"],
        "scene_presence": scene_presence,
        "score": (scene_count * 2) + source["dialogue_count"],
        "_representative_key": (
            _candidate_representative_key(source) if canonical_is_candidate else None
        ),
    }
    _add_aliases(group, canonical, source["name"])
    return group


def _update_representative_name(existing: dict[str, Any], source: dict[str, Any]) -> None:
    existing_key = existing.get("_representative_key")
    if existing_key is None:
        return
    source_key = _candidate_representative_key(source)
    if source_key <= existing_key:
        return
    previous_name = existing["name"]
    existing["name"] = source["name"]
    existing["_representative_key"] = source_key
    _add_aliases(existing, previous_name)


def _candidate_representative_key(source: dict[str, Any]) -> tuple[int, int, int]:
    return (
        int(source.get("score") or 0),
        int(source.get("dialogue_count") or 0),
        int(source.get("scene_count") or 0),
    )


def _add_aliases(candidate: dict[str, Any], *aliases: str) -> None:
    current_aliases = set(candidate.get("aliases", []))
    current_aliases.update(
        alias for alias in aliases if alias and alias != candidate["name"]
    )
    candidate["aliases"] = sorted(current_aliases)


def _public_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": candidate["name"],
        "aliases": [
            alias for alias in candidate.get("aliases", []) if alias != candidate["name"]
        ],
        "scene_count": candidate["scene_count"],
        "dialogue_count": candidate["dialogue_count"],
        "scene_presence": candidate["scene_presence"],
        "score": candidate["score"],
    }


def _annotate_surviving_names(
    *,
    decision_log: list[dict[str, Any]],
    merged: dict[str, dict[str, Any]],
) -> None:
    surviving_by_resolved = {
        resolved_name: candidate["name"] for resolved_name, candidate in merged.items()
    }
    for entry in decision_log:
        resolved_name = entry.get("resolved_name")
        if resolved_name in surviving_by_resolved:
            entry["surviving_name"] = surviving_by_resolved[resolved_name]


def _empty_cost(model: str) -> dict[str, Any]:
    return {
        "model": model if model == "mock" else "code",
        "input_tokens": 0,
        "output_tokens": 0,
        "estimated_cost_usd": 0.0,
    }


def _normalize_character_name(value: Any) -> str:
    text = str(value or "").strip().upper()
    text = re.sub(r"\s*\((V\.O\.|O\.S\.|CONT'D|CONT'D|OFF|ON RADIO)\)\s*$", "", text)

    text = re.sub(r"[^A-Z0-9' ]+", "", text)

    if text.startswith("THE "):
        remainder = text[4:].strip()
        if len(remainder) >= 4:
            text = remainder

    text = re.sub(r"\s+", " ", text).strip()
    return text


def _is_plausible_character_name(name: str) -> bool:
    if not name:
        return False
    if len(name) < 2 or len(name) > 28:
        return False
    tokens = name.split()
    if len(tokens) > 3:
        return False
    if any(not re.match(r"^[A-Z0-9']+$", token) for token in tokens):
        return False
    if any(len(token) > 12 for token in tokens):
        return False
    if any(token in CHARACTER_STOPWORDS for token in tokens):
        return False
    if not any(char.isalpha() for char in name):
        return False
    if re.match(r"^\d+$", name):
        return False
    return True


def _looks_like_derivative_noise(name: str, base_tokens: set[str]) -> bool:
    for token in name.split():
        for base in base_tokens:
            if token == base:
                continue
            if token.startswith(base) and len(token) >= len(base) + 3:
                return True
    return False


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
