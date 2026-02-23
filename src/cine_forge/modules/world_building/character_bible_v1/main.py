"""Extract character bibles and manifests from screenplay artifacts."""

from __future__ import annotations

import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from typing import Any

from cine_forge.ai import adjudicate_entity_candidates
from cine_forge.ai.llm import call_llm
from cine_forge.schemas import (
    CharacterBible,
    EntityAdjudicationDecision,
    QAResult,
)

logger = logging.getLogger(__name__)

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
    "THUG",
}


def run_module(
    inputs: dict[str, Any], params: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    """Execute character bible extraction."""
    canonical_script, scene_index, discovery_results = _extract_inputs(inputs)
    runtime_params = context.get("runtime_params", {}) if isinstance(context, dict) else {}
    if not isinstance(runtime_params, dict):
        runtime_params = {}

    # Tiered Model Strategy (Subsumption)
    work_model = (
        params.get("work_model")
        or params.get("model")
        or params.get("default_model")
        or runtime_params.get("work_model")
        or runtime_params.get("default_model")
        or runtime_params.get("model")
        or "claude-sonnet-4-6"
    )
    verify_model = (
        params.get("verify_model")
        or params.get("qa_model")
        or params.get("utility_model")
        or runtime_params.get("verify_model")
        or runtime_params.get("qa_model")
        or runtime_params.get("utility_model")
        or "claude-haiku-4-5-20251001"
    )
    escalate_model = (
        params.get("escalate_model")
        or params.get("sota_model")
        or runtime_params.get("escalate_model")
        or runtime_params.get("sota_model")
        or "claude-opus-4-6"
    )
    skip_qa = bool(params.get("skip_qa", False))
    concurrency = int(
        params.get("concurrency")
        or runtime_params.get("concurrency")
        or 5
    )

    # Higher default for bibles to avoid noise pollution
    min_appearances = int(params.get("min_scene_appearances", 3))

    # 1. Aggregate and Filter
    if discovery_results and discovery_results.get("characters"):
        approved_names = {n.upper() for n in discovery_results["characters"]}
        print(f"[character_bible] Using {len(approved_names)} characters from discovery results.")
        all_chars = _aggregate_characters(scene_index)
        ranked = _rank_characters(all_chars, canonical_script, scene_index)
        candidates = [c for c in ranked if c["name"].upper() in approved_names]
    else:
        characters = _aggregate_characters(scene_index)
        ranked = _rank_characters(characters, canonical_script, scene_index)

        # Filter by minimum appearances OR presence of dialogue
        candidates = [
            c
            for c in ranked
            if (c["scene_count"] >= min_appearances) or (c["dialogue_count"] >= 1)
        ]
    # Final sanity check: skip anything that is JUST stopwords after filtering
    candidates = [c for c in candidates if _is_plausible_character_name(c["name"])]
    (
        candidates,
        adjudication_rejections,
        adjudication_decisions,
        adjudication_cost,
    ) = _adjudicate_candidates(
        candidates=candidates,
        script_text=canonical_script["script_text"],
        model=work_model,
    )

    models_seen: set[str] = set()
    total_cost = {
        "input_tokens": 0,
        "output_tokens": 0,
        "estimated_cost_usd": 0.0,
    }
    _update_total_cost(total_cost, adjudication_cost)
    if adjudication_cost.get("model") and adjudication_cost["model"] != "code":
        models_seen.add(str(adjudication_cost["model"]))

    # 2. Extract for each candidate in parallel; announce each entity as it completes
    # so the engine can save mid-stage and the sidebar count ticks up live (story-072).
    print(f"[character_bible] Extracting {len(candidates)} characters (concurrency={concurrency}).")
    announce = context.get("announce_artifact")
    artifacts: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        future_to_entry = {
            executor.submit(
                _process_character,
                entry=entry,
                canonical_script=canonical_script,
                scene_index=scene_index,
                ranked=ranked,
                candidates=candidates,
                adjudication_rejections=adjudication_rejections,
                adjudication_decisions=adjudication_decisions,
                work_model=work_model,
                verify_model=verify_model,
                escalate_model=escalate_model,
                skip_qa=skip_qa,
            ): entry
            for entry in candidates
        }
        for future in as_completed(future_to_entry):
            entry = future_to_entry[future]
            try:
                entity_artifacts, entity_cost = future.result()
                if announce:
                    for a in entity_artifacts:
                        if a.get("artifact_type") == "character_bible":
                            announce(a)
                artifacts.extend(entity_artifacts)
                _update_total_cost(total_cost, entity_cost)
                m = entity_cost.get("model", "code")
                if m and m != "code":
                    models_seen.update(m.split("+"))
            except Exception as exc:
                logger.warning(
                    "[character_bible] Failed to extract '%s': %s", entry["name"], exc
                )

    # Stable output order
    artifacts.sort(key=lambda a: a["entity_id"])

    model_label = "+".join(sorted(models_seen)) if models_seen else "code"
    total_cost["model"] = model_label

    return {
        "artifacts": artifacts,
        "cost": total_cost,
    }


def _process_character(
    entry: dict[str, Any],
    canonical_script: dict[str, Any],
    scene_index: dict[str, Any],
    ranked: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    adjudication_rejections: list[dict[str, Any]],
    adjudication_decisions: list[dict[str, Any]],
    work_model: str,
    verify_model: str,
    escalate_model: str,
    skip_qa: bool,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Extract bible for a single character; returns (artifacts, cost)."""
    char_name = entry["name"]
    slug = _slugify(char_name)
    entity_cost: dict[str, Any] = {"input_tokens": 0, "output_tokens": 0, "estimated_cost_usd": 0.0}
    models_in_entity: set[str] = set()

    # Pass 1: Work
    definition, cost = _extract_character_definition(
        char_name=char_name,
        entry=entry,
        canonical_script=canonical_script,
        scene_index=scene_index,
        model=work_model,
    )
    # Override AI-generated character_id with canonical slug so the data field
    # always matches the artifact entity_id (AI often writes "mariner_001" etc.)
    definition = definition.model_copy(update={"character_id": slug})
    _update_total_cost(entity_cost, cost)
    if cost.get("model") and cost["model"] != "code":
        models_in_entity.add(cost["model"])

    if not skip_qa and work_model != "mock":
        # Pass 2: Verify
        qa_result, qa_cost = _run_character_qa(
            char_name=char_name,
            definition=definition,
            script_text=canonical_script["script_text"],
            model=verify_model,
        )
        _update_total_cost(entity_cost, qa_cost)
        if qa_cost.get("model") and qa_cost["model"] != "code":
            models_in_entity.add(qa_cost["model"])

        if not qa_result.passed:
            # Pass 3: Escalate
            definition, esc_cost = _extract_character_definition(
                char_name=char_name,
                entry=entry,
                canonical_script=canonical_script,
                scene_index=scene_index,
                model=escalate_model,
                feedback=qa_result.summary,
            )
            _update_total_cost(entity_cost, esc_cost)
            if esc_cost.get("model") and esc_cost["model"] != "code":
                models_in_entity.add(esc_cost["model"])

    entity_cost["model"] = "+".join(sorted(models_in_entity)) if models_in_entity else "code"

    # Build artifacts
    version = 1
    master_filename = f"master_v{version}.json"
    manifest_data = {
        "entity_type": "character",
        "entity_id": slug,
        "display_name": char_name,
        "files": [
            {
                "filename": master_filename,
                "purpose": "master_definition",
                "version": version,
                "provenance": "ai_extracted",
                "created_at": datetime.now(UTC).isoformat(),
            }
        ],
        "version": version,
        "created_at": datetime.now(UTC).isoformat(),
    }
    annotation = _adjudication_annotation(
        input_count=len(ranked),
        approved_count=len(candidates),
        rejected=adjudication_rejections,
        decisions=adjudication_decisions,
    )

    return [
        {
            "artifact_type": "character_bible",
            "entity_id": slug,
            "data": definition.model_dump(mode="json"),
            "metadata": {
                "intent": f"Establish master definition for character '{char_name}'",
                "rationale": "Extracted from canonical script and scene co-occurrence data.",
                "confidence": definition.overall_confidence,
                "source": "ai",
                "annotations": annotation,
            },
        },
        {
            "artifact_type": "bible_manifest",
            "entity_id": f"character_{slug}",
            "data": manifest_data,
            "metadata": {
                "intent": f"Establish master bible for character '{char_name}'",
                "rationale": (
                    "Consolidate character traits, evidence, and relationships from script."
                ),
                "confidence": definition.overall_confidence,
                "source": "ai",
                "annotations": annotation,
            },
            "bible_files": {master_filename: definition.model_dump_json(indent=2)},
        },
    ], entity_cost


def _update_total_cost(total: dict[str, Any], call_cost: dict[str, Any]) -> None:
    total["input_tokens"] += call_cost.get("input_tokens", 0)
    total["output_tokens"] += call_cost.get("output_tokens", 0)
    total["estimated_cost_usd"] += call_cost.get("estimated_cost_usd", 0.0)


def _extract_inputs(
    inputs: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any] | None]:
    canonical_script = None
    scene_index = None
    discovery_results = None
    for payload in inputs.values():
        if isinstance(payload, dict) and "script_text" in payload:
            canonical_script = payload
        if isinstance(payload, dict) and "unique_characters" in payload and "entries" in payload:
            scene_index = payload
        if isinstance(payload, dict) and "props" in payload and "characters" in payload:
            discovery_results = payload

    if not canonical_script or not scene_index:
        raise ValueError("character_bible_v1 requires canonical_script and scene_index inputs")
    return canonical_script, scene_index, discovery_results


def _aggregate_characters(scene_index: dict[str, Any]) -> list[str]:
    raw_names = scene_index.get("unique_characters", [])
    normalized = [_normalize_character_name(n) for n in raw_names]
    # Filter noise
    plausible = [n for n in normalized if _is_plausible_character_name(n)]
    # Filter derivative
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

    # Dialogue counts
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


def _extract_character_definition(
    char_name: str,
    entry: dict[str, Any],
    canonical_script: dict[str, Any],
    scene_index: dict[str, Any],
    model: str,
    feedback: str = "",
) -> tuple[CharacterBible, dict[str, Any]]:
    if model == "mock":
        return _mock_extract(char_name, entry), {
            "model": "mock",
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": 0.0,
        }

    prompt = _build_extraction_prompt(char_name, entry, canonical_script, scene_index, feedback)
    definition, cost = call_llm(
        prompt=prompt,
        model=model,
        response_schema=CharacterBible,
    )
    return definition, cost


def _adjudicate_candidates(
    candidates: list[dict[str, Any]],
    script_text: str,
    model: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    if not candidates:
        return [], [], [], _empty_cost(model)

    adjudication_input = [
        {
            "candidate": item["name"],
            "scene_count": item["scene_count"],
            "dialogue_count": item["dialogue_count"],
            "scene_presence": item["scene_presence"][:8],
            "source_hint": "scene_index.unique_characters",
        }
        for item in candidates
    ]
    decisions, cost = adjudicate_entity_candidates(
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

        existing = merged.get(canonical)
        if not existing:
            merged[canonical] = {
                "name": canonical,
                "scene_count": source["scene_count"],
                "dialogue_count": source["dialogue_count"],
                "scene_presence": list(source["scene_presence"]),
                "score": (source["scene_count"] * 2) + source["dialogue_count"],
            }
            continue
        existing["scene_count"] += source["scene_count"]
        existing["dialogue_count"] += source["dialogue_count"]
        existing["scene_presence"] = sorted(
            list(set(existing["scene_presence"] + list(source["scene_presence"])))
        )
        existing["score"] = (existing["scene_count"] * 2) + existing["dialogue_count"]

    approved = sorted(merged.values(), key=lambda item: item["score"], reverse=True)
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


def _adjudication_annotation(
    *,
    input_count: int,
    approved_count: int,
    rejected: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "entity_adjudication": {
            "input_candidate_count": input_count,
            "approved_candidate_count": approved_count,
            "rejected_candidate_count": len(rejected),
            "rejected_candidates": rejected[:50],
            "decision_trace_count": len(decisions),
            "decision_trace": decisions[:100],
        }
    }


def _empty_cost(model: str) -> dict[str, Any]:
    return {
        "model": model if model == "mock" else "code",
        "input_tokens": 0,
        "output_tokens": 0,
        "estimated_cost_usd": 0.0,
    }


def _run_character_qa(
    char_name: str,
    definition: CharacterBible,
    script_text: str,
    model: str,
) -> tuple[QAResult, dict[str, Any]]:
    from cine_forge.ai import qa_check

    return qa_check(
        original_input=script_text[:5000],  # Give enough for context
        prompt_used="Character extraction prompt",
        output_produced=definition.model_dump_json(),
        model=model,
        criteria=["accuracy", "depth", "vividness"],
    )


def _build_extraction_prompt(
    char_name: str,
    entry: dict[str, Any],
    script: dict[str, Any],
    index: dict[str, Any],
    feedback: str = "",
) -> str:
    from cine_forge.ai import extract_scenes_for_entity

    relevant_text = extract_scenes_for_entity(
        script_text=script["script_text"],
        scene_index=index,
        entity_type="character",
        entity_name=char_name,
    )
    feedback_block = f"\nQA Feedback to address: {feedback}\n" if feedback else ""
    return f"""You are a character analyst. Extract a master definition for character: {char_name}.

    Return JSON matching CharacterBible schema.
    {feedback_block}
    Character Context:
    - Name: {char_name}
    - Scene Count: {entry['scene_count']}
    - Dialogue Count: {entry['dialogue_count']}

    Relevant Script Scenes (containing {char_name}):
    {relevant_text}
    """


def _mock_extract(char_name: str, entry: dict[str, Any]) -> CharacterBible:
    return CharacterBible(
        character_id=_slugify(char_name),
        name=char_name,
        aliases=[],
        description=f"A character named {char_name}.",
        explicit_evidence=[],
        inferred_traits=[],
        scene_presence=entry["scene_presence"],
        dialogue_summary=f"Speaking in {entry['dialogue_count']} lines.",
        narrative_role="supporting",
        narrative_role_confidence=0.8,
        relationships=[],
        overall_confidence=0.9,
    )


def _normalize_character_name(value: Any) -> str:
    text = str(value or "").strip().upper()
    text = re.sub(r"\s*\((V\.O\.|O\.S\.|CONT'D|CONT'D|OFF|ON RADIO)\)\s*$", "", text)

    # Strip non-alphanumeric except spaces and apostrophes (e.g. MR. SALVATORI -> MR SALVATORI)
    text = re.sub(r"[^A-Z0-9' ]+", "", text)

    # Strip leading "THE " prefix if it's followed by 4+ letters
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
    if any(not re.match(r"^[A-Z']+$", token) for token in tokens):
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
