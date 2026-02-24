"""LLM-first adjudication helpers for candidate entities."""

from __future__ import annotations

import json
from typing import Any

from cine_forge.ai.llm import call_llm
from cine_forge.schemas import (
    EntityAdjudicationBatch,
    EntityAdjudicationDecision,
    EntityType,
)


def adjudicate_entity_candidates(
    *,
    entity_type: EntityType,
    candidates: list[dict[str, Any]],
    script_text: str,
    model: str,
) -> tuple[list[EntityAdjudicationDecision], dict[str, Any]]:
    """Adjudicate candidate entities before bible emission.

    `candidates` should include at least `candidate` and optional evidence fields.
    Returns one resolved decision per input candidate (defaults to invalid when missing).
    """
    if not candidates:
        return [], {
            "model": "code",
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": 0.0,
        }

    if model == "mock":
        return _mock_decisions(candidates), {
            "model": "mock",
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": 0.0,
        }

    prompt = _build_prompt(entity_type=entity_type, candidates=candidates, script_text=script_text)
    batch, cost = call_llm(
        prompt=prompt,
        model=model,
        response_schema=EntityAdjudicationBatch,
        max_tokens=2400,
    )
    return _resolve_decisions(entity_type=entity_type, candidates=candidates, raw=batch), cost


def _mock_decisions(candidates: list[dict[str, Any]]) -> list[EntityAdjudicationDecision]:
    decisions: list[EntityAdjudicationDecision] = []
    for candidate in candidates:
        name = str(candidate.get("candidate") or "").strip()
        if not name:
            continue
        decisions.append(
            EntityAdjudicationDecision(
                candidate=name,
                verdict="valid",
                canonical_name=name,
                rationale="mock mode accepts candidate",
                confidence=1.0,
            )
        )
    return decisions


def _build_prompt(
    entity_type: EntityType, candidates: list[dict[str, Any]], script_text: str
) -> str:
    compact_candidates = []
    for item in candidates:
        compact_candidates.append(
            {
                "candidate": item.get("candidate"),
                "scene_count": item.get("scene_count"),
                "dialogue_count": item.get("dialogue_count"),
                "scene_presence": item.get("scene_presence"),
                "mention_count": item.get("mention_count"),
                "source_hint": item.get("source_hint"),
            }
        )

    return (
        "You are an entity adjudicator for screenplay world-building.\n"
        "Classify each candidate for the requested target type.\n"
        "Return JSON matching EntityAdjudicationBatch exactly.\n\n"
        f"Target type: {entity_type}\n"
        "For each candidate, set verdict:\n"
        "- valid: is a real entity of target type\n"
        "- invalid: not a real entity (formatting token, dialogue fragment, noise)\n"
        "- retype: real entity but different type (set target_entity_type)\n"
        "Rules:\n"
        "- Do NOT invent entities not present in candidates.\n"
        "- Keep candidate string exact in decision.candidate.\n"
        "- canonical_name should normalize spelling/casing only when useful.\n"
        "- confidence must be 0..1.\n"
        "- Named minor characters (e.g., THUG 1, GUARD 2, NURSE, COP 3) are VALID,\n"
        "  even if they appear only once. Only reject formatting tokens, sound cues,\n"
        "  and non-character strings (e.g., VOICE ON INTERCOM, THWACK, CUT TO).\n\n"
        f"Candidates JSON:\n{json.dumps(compact_candidates, ensure_ascii=True, indent=2)}\n\n"
        "Script excerpt (truncated):\n"
        f"{script_text[:7000]}"
    )


def _resolve_decisions(
    *, entity_type: EntityType, candidates: list[dict[str, Any]], raw: EntityAdjudicationBatch
) -> list[EntityAdjudicationDecision]:
    by_candidate = {
        str(item.candidate).strip().upper(): item
        for item in (raw.decisions or [])
        if str(item.candidate).strip()
    }

    resolved: list[EntityAdjudicationDecision] = []
    for candidate in candidates:
        original = str(candidate.get("candidate") or "").strip()
        if not original:
            continue
        key = original.upper()
        decision = by_candidate.get(key)
        if not decision:
            resolved.append(
                EntityAdjudicationDecision(
                    candidate=original,
                    verdict="invalid",
                    rationale="missing adjudication decision for candidate",
                    confidence=0.0,
                )
            )
            continue

        if (
            decision.verdict == "valid"
            and decision.target_entity_type
            and decision.target_entity_type != entity_type
        ):
            resolved.append(
                EntityAdjudicationDecision(
                    candidate=original,
                    verdict="retype",
                    target_entity_type=decision.target_entity_type,
                    canonical_name=decision.canonical_name,
                    rationale=decision.rationale,
                    confidence=decision.confidence,
                )
            )
            continue

        if decision.verdict == "retype" and not decision.target_entity_type:
            resolved.append(
                EntityAdjudicationDecision(
                    candidate=original,
                    verdict="invalid",
                    rationale="retype verdict missing target_entity_type",
                    confidence=0.0,
                )
            )
            continue

        resolved.append(
            EntityAdjudicationDecision(
                candidate=original,
                verdict=decision.verdict,
                canonical_name=(
                    (decision.canonical_name or original).strip()
                    if decision.verdict == "valid"
                    else decision.canonical_name
                ),
                target_entity_type=decision.target_entity_type,
                rationale=decision.rationale,
                confidence=decision.confidence,
            )
        )

    return resolved
