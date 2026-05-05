"""Extract character bibles and manifests from screenplay artifacts."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from typing import Any

from cine_forge.ai.llm import call_llm
from cine_forge.modules.world_building.character_bible_v1.candidate_resolution import (
    _slugify,
    prepare_character_candidates,
)
from cine_forge.schemas import (
    CharacterBible,
    QAResult,
)

logger = logging.getLogger(__name__)

DEFAULT_CHARACTER_BIBLE_MAX_TOKENS = 8192
DEFAULT_MINOR_CHARACTER_BIBLE_MAX_TOKENS = 4096


def run_module(
    inputs: dict[str, Any], params: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    """Execute character bible extraction."""
    canonical_script, scene_index, discovery_results = _extract_inputs(inputs)
    options = _resolve_execution_options(params=params, context=context)
    (
        ranked,
        candidates,
        adjudication_rejections,
        adjudication_decisions,
        adjudication_cost,
    ) = prepare_character_candidates(
        canonical_script=canonical_script,
        scene_index=scene_index,
        discovery_results=discovery_results,
        min_appearances=options["min_appearances"],
        model=options["work_model"],
    )

    models_seen: set[str] = set()
    total_cost = {
        "input_tokens": 0,
        "output_tokens": 0,
        "estimated_cost_usd": 0.0,
    }
    _update_total_cost(total_cost, adjudication_cost)
    _record_models(models_seen, adjudication_cost.get("model"))

    # 2. Split candidates into full (primary/secondary) vs lightweight (minor) extraction
    # paths. Characters with score >= 4 (2+ scenes or 1 scene + 2 dialogue) get a deep
    # extraction; lower-scoring candidates get a stripped-down minor-character extraction
    # that's ~80% cheaper per character. Both produce valid CharacterBible artifacts.
    full_candidates = [
        c for c in candidates if c["score"] >= options["minor_score_threshold"]
    ]
    minor_candidates = [
        c for c in candidates if c["score"] < options["minor_score_threshold"]
    ]
    print(
        f"[character_bible] Extracting {len(full_candidates)} full + "
        f"{len(minor_candidates)} minor characters (concurrency={options['concurrency']})."
    )
    artifacts, extraction_cost, extraction_models = _extract_character_artifacts(
        full_candidates=full_candidates,
        minor_candidates=minor_candidates,
        canonical_script=canonical_script,
        scene_index=scene_index,
        ranked=ranked,
        candidates=candidates,
        adjudication_rejections=adjudication_rejections,
        adjudication_decisions=adjudication_decisions,
        work_model=options["work_model"],
        verify_model=options["verify_model"],
        escalate_model=options["escalate_model"],
        skip_qa=options["skip_qa"],
        concurrency=options["concurrency"],
        character_bible_max_tokens=options["character_bible_max_tokens"],
        minor_character_bible_max_tokens=options["minor_character_bible_max_tokens"],
        announce=context.get("announce_artifact") if isinstance(context, dict) else None,
    )
    _update_total_cost(total_cost, extraction_cost)
    models_seen.update(extraction_models)

    # Stable output order
    artifacts.sort(key=lambda a: a["entity_id"])

    model_label = "+".join(sorted(models_seen)) if models_seen else "code"
    total_cost["model"] = model_label

    return {
        "artifacts": artifacts,
        "cost": total_cost,
    }


def _resolve_execution_options(
    params: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    runtime_params = context.get("runtime_params", {}) if isinstance(context, dict) else {}
    if not isinstance(runtime_params, dict):
        runtime_params = {}

    return {
        "work_model": (
            params.get("work_model")
            or params.get("model")
            or params.get("default_model")
            or runtime_params.get("work_model")
            or runtime_params.get("default_model")
            or runtime_params.get("model")
            or "claude-sonnet-4-6"
        ),
        "verify_model": (
            params.get("verify_model")
            or params.get("qa_model")
            or params.get("utility_model")
            or runtime_params.get("verify_model")
            or runtime_params.get("qa_model")
            or runtime_params.get("utility_model")
            or "claude-haiku-4-5-20251001"
        ),
        "escalate_model": (
            params.get("escalate_model")
            or params.get("sota_model")
            or runtime_params.get("escalate_model")
            or runtime_params.get("sota_model")
            or "claude-opus-4-6"
        ),
        "skip_qa": bool(params.get("skip_qa", False)),
        "concurrency": int(params.get("concurrency") or runtime_params.get("concurrency") or 5),
        "min_appearances": int(params.get("min_scene_appearances", 3)),
        "minor_score_threshold": int(
            params.get("minor_score_threshold")
            or runtime_params.get("minor_score_threshold")
            or 4
        ),
        "character_bible_max_tokens": int(
            params.get("character_bible_max_tokens")
            or runtime_params.get("character_bible_max_tokens")
            or DEFAULT_CHARACTER_BIBLE_MAX_TOKENS
        ),
        "minor_character_bible_max_tokens": int(
            params.get("minor_character_bible_max_tokens")
            or runtime_params.get("minor_character_bible_max_tokens")
            or DEFAULT_MINOR_CHARACTER_BIBLE_MAX_TOKENS
        ),
    }


def _extract_character_artifacts(
    *,
    full_candidates: list[dict[str, Any]],
    minor_candidates: list[dict[str, Any]],
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
    concurrency: int,
    character_bible_max_tokens: int,
    minor_character_bible_max_tokens: int,
    announce: Any | None,
) -> tuple[list[dict[str, Any]], dict[str, Any], set[str]]:
    artifacts: list[dict[str, Any]] = []
    total_cost = {
        "input_tokens": 0,
        "output_tokens": 0,
        "estimated_cost_usd": 0.0,
    }
    models_seen: set[str] = set()
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        future_to_entry: dict[Any, dict[str, Any]] = {}
        for entry in full_candidates:
            future_to_entry[
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
                    max_tokens=character_bible_max_tokens,
                )
            ] = entry
        for entry in minor_candidates:
            future_to_entry[
                executor.submit(
                    _process_minor_character,
                    entry=entry,
                    canonical_script=canonical_script,
                    scene_index=scene_index,
                    ranked=ranked,
                    candidates=candidates,
                    adjudication_rejections=adjudication_rejections,
                    adjudication_decisions=adjudication_decisions,
                    model=work_model,
                    max_tokens=minor_character_bible_max_tokens,
                )
            ] = entry
        for future in as_completed(future_to_entry):
            entry = future_to_entry[future]
            try:
                entity_artifacts, entity_cost = future.result()
                if announce:
                    for artifact in entity_artifacts:
                        if artifact.get("artifact_type") == "character_bible":
                            announce(artifact)
                artifacts.extend(entity_artifacts)
                _update_total_cost(total_cost, entity_cost)
                _record_models(models_seen, entity_cost.get("model"))
            except Exception as exc:
                logger.warning(
                    "[character_bible] Failed to extract '%s': %s", entry["name"], exc
                )
    return artifacts, total_cost, models_seen


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
    max_tokens: int,
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
        max_tokens=max_tokens,
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
                max_tokens=max_tokens,
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
        input_count=len(adjudication_decisions) or len(ranked),
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


def _process_minor_character(
    entry: dict[str, Any],
    canonical_script: dict[str, Any],
    scene_index: dict[str, Any],
    ranked: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    adjudication_rejections: list[dict[str, Any]],
    adjudication_decisions: list[dict[str, Any]],
    model: str,
    max_tokens: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Lightweight extraction for minor characters (walk-ons, thugs, guards).

    Produces a valid CharacterBible with minimal fields — skips deep trait
    extraction, evidence, and relationship analysis to keep cost low.
    """
    char_name = entry["name"]
    slug = _slugify(char_name)
    entity_cost: dict[str, Any] = {
        "input_tokens": 0,
        "output_tokens": 0,
        "estimated_cost_usd": 0.0,
    }

    definition, cost = _extract_minor_character_definition(
        char_name=char_name,
        entry=entry,
        canonical_script=canonical_script,
        scene_index=scene_index,
        model=model,
        max_tokens=max_tokens,
    )
    definition = definition.model_copy(update={"character_id": slug})
    _update_total_cost(entity_cost, cost)
    entity_cost["model"] = cost.get("model", "code")

    # Build artifacts — same structure as full extraction
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
        input_count=len(adjudication_decisions) or len(ranked),
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
                "intent": f"Establish minor character definition for '{char_name}'",
                "rationale": "Lightweight extraction for minor/walk-on character.",
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
                "intent": f"Establish minor bible for character '{char_name}'",
                "rationale": "Lightweight extraction for minor/walk-on character.",
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


def _record_models(models_seen: set[str], model_label: Any) -> None:
    if not model_label or model_label == "code":
        return
    models_seen.update(str(model_label).split("+"))


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


def _extract_character_definition(
    char_name: str,
    entry: dict[str, Any],
    canonical_script: dict[str, Any],
    scene_index: dict[str, Any],
    model: str,
    feedback: str = "",
    max_tokens: int = DEFAULT_CHARACTER_BIBLE_MAX_TOKENS,
) -> tuple[CharacterBible, dict[str, Any]]:
    if model == "mock":
        return _definition_with_entry_aliases(_mock_extract(char_name, entry), entry), {
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
        max_tokens=max_tokens,
        fail_on_truncation=True,
        enable_caching=True,
    )
    return _definition_with_entry_aliases(definition, entry), cost


def _extract_minor_character_definition(
    char_name: str,
    entry: dict[str, Any],
    canonical_script: dict[str, Any],
    scene_index: dict[str, Any],
    model: str,
    max_tokens: int = DEFAULT_MINOR_CHARACTER_BIBLE_MAX_TOKENS,
) -> tuple[CharacterBible, dict[str, Any]]:
    """Lightweight extraction for minor characters — cheaper than full extraction."""
    if model == "mock":
        return _definition_with_entry_aliases(_mock_minor_extract(char_name, entry), entry), {
            "model": "mock",
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": 0.0,
        }

    prompt = _build_lightweight_prompt(char_name, entry, canonical_script, scene_index)
    definition, cost = call_llm(
        prompt=prompt,
        model=model,
        response_schema=CharacterBible,
        max_tokens=max_tokens,
        fail_on_truncation=True,
        enable_caching=True,
    )
    return _definition_with_entry_aliases(definition, entry), cost


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


def _extract_entry_script_context(
    script_text: str,
    scene_index: dict[str, Any],
    entry: dict[str, Any],
    fallback_name: str,
) -> str:
    scene_ids = {str(scene_id) for scene_id in entry.get("scene_presence", []) if scene_id}
    if not scene_ids:
        from cine_forge.ai import extract_scenes_for_entity

        return extract_scenes_for_entity(
            script_text=script_text,
            scene_index=scene_index,
            entity_type="character",
            entity_name=fallback_name,
        )

    lines = script_text.splitlines()
    snippets: list[str] = []
    seen: set[str] = set()
    for scene_entry in scene_index.get("entries", []):
        if str(scene_entry.get("scene_id")) not in scene_ids:
            continue
        span = scene_entry.get("source_span") or {}
        if "start_line" in span and "end_line" in span:
            start = max(int(span["start_line"]) - 1, 0)
            end = min(int(span["end_line"]), len(lines))
            snippet = "\n".join(lines[start:end])
        else:
            snippet = script_text
        if snippet and snippet not in seen:
            snippets.append(snippet)
            seen.add(snippet)

    if snippets:
        return "\n\n".join(snippets)

    from cine_forge.ai import extract_scenes_for_entity

    return extract_scenes_for_entity(
        script_text=script_text,
        scene_index=scene_index,
        entity_type="character",
        entity_name=fallback_name,
    )


def _alias_context_line(entry: dict[str, Any]) -> str:
    aliases = entry.get("aliases") or []
    if not aliases:
        return ""
    return f"    - Known aliases: {', '.join(str(alias) for alias in aliases)}\n"


def _definition_with_entry_aliases(
    definition: CharacterBible, entry: dict[str, Any]
) -> CharacterBible:
    merged_aliases = list(definition.aliases)
    seen = {alias.strip().upper() for alias in merged_aliases if str(alias).strip()}
    for alias in entry.get("aliases") or []:
        alias_text = str(alias).strip()
        if not alias_text:
            continue
        alias_key = alias_text.upper()
        if alias_key in seen:
            continue
        merged_aliases.append(alias_text)
        seen.add(alias_key)
    return definition.model_copy(update={"aliases": merged_aliases})


def _build_extraction_prompt(
    char_name: str,
    entry: dict[str, Any],
    script: dict[str, Any],
    index: dict[str, Any],
    feedback: str = "",
) -> str:
    relevant_text = _extract_entry_script_context(
        script_text=script["script_text"],
        scene_index=index,
        entry=entry,
        fallback_name=char_name,
    )
    feedback_block = f"\nQA Feedback to address: {feedback}\n" if feedback else ""
    alias_context = _alias_context_line(entry)
    return f"""You are a character analyst. Extract a master definition for character: {char_name}.
    Base every field strictly on evidence from the provided screenplay \
text. If a trait, relationship, or detail cannot be determined from the \
scenes provided, leave the field empty or use 'unknown' rather than \
inventing plausible details.

    Return JSON matching CharacterBible schema.

    IMPORTANT — assign a "prominence" field based on production importance:
    - "primary": protagonist, antagonist, or key relationship character who drives the plot
    - "secondary": recurring supporting character with a named role and meaningful dialogue
    - "minor": walk-on, one-scene character, functional role (thug, guard, cop, etc.)
    {feedback_block}
    Character Context:
    - Name: {char_name}
{alias_context}\
    - Scene Count: {entry['scene_count']}
    - Dialogue Count: {entry['dialogue_count']}

    Before finalizing, verify that every field in the schema has been \
considered and that no dialogue, action, or description referencing \
this character has been overlooked in the provided scenes.

    Relevant Script Scenes (containing {char_name}):
    {relevant_text}
    """


def _build_lightweight_prompt(
    char_name: str,
    entry: dict[str, Any],
    script: dict[str, Any],
    index: dict[str, Any],
) -> str:
    """Minimal extraction prompt for minor/walk-on characters."""
    relevant_text = _extract_entry_script_context(
        script_text=script["script_text"],
        scene_index=index,
        entry=entry,
        fallback_name=char_name,
    )
    alias_context = _alias_context_line(entry)
    return f"""You are a character analyst. Extract a brief definition \
for minor character: {char_name}.
    Base all fields on evidence from the provided scene text. Do not \
invent backstory, motivations, or details not present in the screenplay.

    This is a walk-on or minor character. Return JSON matching CharacterBible schema.
    Focus only on: name, description, scene_presence, narrative_role, and prominence.
    For fields you cannot determine, use sensible defaults:
    - prominence: "minor"
    - narrative_role: "minor"
    - dialogue_summary: brief or "No significant dialogue."
    - explicit_evidence, inferred_traits, relationships: empty lists are fine
    - overall_confidence: your confidence in the description (0.0-1.0)

    Character Context:
    - Name: {char_name}
{alias_context}\
    - Scene Count: {entry['scene_count']}
    - Dialogue Count: {entry['dialogue_count']}

    Relevant Script Scenes (containing {char_name}):
    {relevant_text}
    """


def _mock_extract(char_name: str, entry: dict[str, Any]) -> CharacterBible:
    return CharacterBible(
        character_id=_slugify(char_name),
        name=char_name,
        aliases=list(entry.get("aliases", [])),
        description=f"A character named {char_name}.",
        prominence="secondary",
        explicit_evidence=[],
        inferred_traits=[],
        scene_presence=entry["scene_presence"],
        dialogue_summary=f"Speaking in {entry['dialogue_count']} lines.",
        narrative_role="supporting",
        narrative_role_confidence=0.8,
        relationships=[],
        overall_confidence=0.9,
    )


def _mock_minor_extract(char_name: str, entry: dict[str, Any]) -> CharacterBible:
    return CharacterBible(
        character_id=_slugify(char_name),
        name=char_name,
        aliases=list(entry.get("aliases", [])),
        description=f"A minor character: {char_name}.",
        prominence="minor",
        explicit_evidence=[],
        inferred_traits=[],
        scene_presence=entry["scene_presence"],
        dialogue_summary="No significant dialogue.",
        narrative_role="minor",
        narrative_role_confidence=0.9,
        relationships=[],
        overall_confidence=0.7,
    )
