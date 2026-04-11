"""Extract location bibles and manifests from screenplay artifacts."""

from __future__ import annotations

import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from typing import Any

from cine_forge.ai import adjudicate_entity_candidates, qa_check
from cine_forge.ai.llm import call_llm
from cine_forge.schemas import (
    EntityAdjudicationDecision,
    LocationBible,
    QAResult,
)

logger = logging.getLogger(__name__)

DEFAULT_LOCATION_BIBLE_MAX_TOKENS = 4096
LOCATION_TIME_SUFFIXES = (
    "DAY",
    "NIGHT",
    "MORNING",
    "EVENING",
    "DUSK",
    "DAWN",
    "CONTINUOUS",
    "LATER",
    "MOMENTS LATER",
)
LOCATION_TIME_SUFFIX_PATTERN = "|".join(LOCATION_TIME_SUFFIXES)


def run_module(
    inputs: dict[str, Any], params: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    """Execute location bible extraction."""
    canonical_script, scene_index, discovery_results = _extract_inputs(inputs)
    options = _resolve_execution_options(params=params, context=context)
    (
        ranked,
        candidates,
        adjudication_rejections,
        adjudication_decisions,
        adjudication_cost,
    ) = _prepare_location_candidates(
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

    # 2. Extract for each candidate in parallel; announce each entity as it completes
    # so the engine can save mid-stage and the sidebar count ticks up live (story-072).
    print(
        f"[location_bible] Extracting {len(candidates)} locations "
        f"(concurrency={options['concurrency']})."
    )
    artifacts, extraction_cost, extraction_models = _extract_location_artifacts(
        candidates=candidates,
        canonical_script=canonical_script,
        scene_index=scene_index,
        ranked=ranked,
        adjudication_rejections=adjudication_rejections,
        adjudication_decisions=adjudication_decisions,
        work_model=options["work_model"],
        verify_model=options["verify_model"],
        escalate_model=options["escalate_model"],
        skip_qa=options["skip_qa"],
        concurrency=options["concurrency"],
        location_bible_max_tokens=options["location_bible_max_tokens"],
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
        "min_appearances": int(params.get("min_scene_appearances", 1)),
        "location_bible_max_tokens": int(
            params.get("location_bible_max_tokens")
            or runtime_params.get("location_bible_max_tokens")
            or DEFAULT_LOCATION_BIBLE_MAX_TOKENS
        ),
    }


def _prepare_location_candidates(
    canonical_script: dict[str, Any],
    scene_index: dict[str, Any],
    discovery_results: dict[str, Any] | None,
    min_appearances: int,
    model: str,
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, Any],
]:
    if discovery_results and discovery_results.get("locations"):
        ranked, candidates, should_adjudicate = _build_discovery_location_candidates(
            scene_index=scene_index,
            discovery_results=discovery_results,
        )
        if not should_adjudicate:
            print(
                "[location_bible] Skipping second-pass adjudication for "
                "discovery-backed candidates."
            )
            return ranked, candidates, [], [], _empty_cost(model)
    else:
        locations = _aggregate_locations(scene_index)
        ranked = _rank_locations(locations, scene_index)
        candidates = [
            candidate for candidate in ranked if candidate["scene_count"] >= min_appearances
        ]

    candidates, rejected, decisions, cost = _adjudicate_candidates(
        candidates=candidates,
        script_text=canonical_script["script_text"],
        model=model,
    )
    return ranked, candidates, rejected, decisions, cost


def _build_discovery_location_candidates(
    scene_index: dict[str, Any],
    discovery_results: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], bool]:
    approved_locations = {
        _normalize_location_name(name)
        for name in discovery_results["locations"]
        if _normalize_location_name(name)
    }
    print(f"[location_bible] Using {len(approved_locations)} locations from discovery results.")
    all_locations = _aggregate_locations(scene_index)
    ranked = _rank_locations(all_locations, scene_index)
    candidates = [
        candidate
        for candidate in ranked
        if _normalize_location_name(candidate["name"]) in approved_locations
    ]
    if candidates:
        return ranked, candidates, False

    # Normalization still didn't match (unusual format) — fall back to all locations.
    print("[location_bible] No approved matches; falling back to all scene_index locations.")
    return ranked, ranked, True


def _extract_location_artifacts(
    *,
    candidates: list[dict[str, Any]],
    canonical_script: dict[str, Any],
    scene_index: dict[str, Any],
    ranked: list[dict[str, Any]],
    adjudication_rejections: list[dict[str, Any]],
    adjudication_decisions: list[dict[str, Any]],
    work_model: str,
    verify_model: str,
    escalate_model: str,
    skip_qa: bool,
    concurrency: int,
    location_bible_max_tokens: int,
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
        future_to_entry = {
            executor.submit(
                _process_location,
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
                max_tokens=location_bible_max_tokens,
            ): entry
            for entry in candidates
        }
        for future in as_completed(future_to_entry):
            entry = future_to_entry[future]
            try:
                entity_artifacts, entity_cost = future.result()
                if announce:
                    for artifact in entity_artifacts:
                        if artifact.get("artifact_type") == "location_bible":
                            announce(artifact)
                artifacts.extend(entity_artifacts)
                _update_total_cost(total_cost, entity_cost)
                _record_models(models_seen, entity_cost.get("model"))
            except Exception as exc:
                logger.warning(
                    "[location_bible] Failed to extract '%s': %s", entry["name"], exc
                )
    return artifacts, total_cost, models_seen


def _process_location(
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
    """Extract bible for a single location; returns (artifacts, cost)."""
    loc_name = entry["name"]
    slug = _slugify(loc_name)
    entity_cost: dict[str, Any] = {"input_tokens": 0, "output_tokens": 0, "estimated_cost_usd": 0.0}
    models_in_entity: set[str] = set()

    # Pass 1: Work
    definition, cost = _extract_location_definition(
        loc_name=loc_name,
        entry=entry,
        canonical_script=canonical_script,
        scene_index=scene_index,
        model=work_model,
        max_tokens=max_tokens,
    )
    # Override AI-generated location_id with canonical slug so the data field
    # always matches the artifact entity_id (AI often writes "loc_xxx" etc.)
    definition = definition.model_copy(update={"location_id": slug})
    _update_total_cost(entity_cost, cost)
    if cost.get("model") and cost["model"] != "code":
        models_in_entity.add(cost["model"])

    if not skip_qa and work_model != "mock":
        # Pass 2: Verify
        qa_result, qa_cost = _run_location_qa(
            loc_name=loc_name,
            definition=definition,
            script_text=canonical_script["script_text"],
            model=verify_model,
        )
        _update_total_cost(entity_cost, qa_cost)
        if qa_cost.get("model") and qa_cost["model"] != "code":
            models_in_entity.add(qa_cost["model"])

        if not qa_result.passed:
            # Pass 3: Escalate
            definition, esc_cost = _extract_location_definition(
                loc_name=loc_name,
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
        "entity_type": "location",
        "entity_id": slug,
        "display_name": loc_name,
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
            "artifact_type": "location_bible",
            "entity_id": slug,
            "data": definition.model_dump(mode="json"),
            "metadata": {
                "intent": f"Establish master definition for location '{loc_name}'",
                "rationale": "Extracted from canonical script and scene headings.",
                "confidence": definition.overall_confidence,
                "source": "ai",
                "annotations": annotation,
            },
        },
        {
            "artifact_type": "bible_manifest",
            "entity_id": f"location_{slug}",
            "data": manifest_data,
            "metadata": {
                "intent": f"Establish master bible for location '{loc_name}'",
                "rationale": "Consolidate location traits and narrative significance.",
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
        if isinstance(payload, dict) and "unique_locations" in payload and "entries" in payload:
            scene_index = payload
        if isinstance(payload, dict) and "props" in payload and "characters" in payload:
            discovery_results = payload

    if not canonical_script or not scene_index:
        raise ValueError("location_bible_v1 requires canonical_script and scene_index inputs")
    return canonical_script, scene_index, discovery_results


def _aggregate_locations(scene_index: dict[str, Any]) -> list[str]:
    return scene_index.get("unique_locations", [])


def _rank_locations(names: list[str], index: dict[str, Any]) -> list[dict[str, Any]]:
    scene_counts = {name: 0 for name in names}
    scene_presence = {name: [] for name in names}
    for entry in index.get("entries", []):
        loc = entry.get("location")
        if loc in scene_counts:
            scene_counts[loc] += 1
            scene_presence[loc].append(entry["scene_id"])

    results = []
    for name in names:
        results.append({
            "name": name,
            "scene_count": scene_counts[name],
            "scene_presence": scene_presence[name],
        })
    results.sort(key=lambda x: x["scene_count"], reverse=True)
    return results


def _normalize_location_name(value: str) -> str:
    normalized = re.sub(r"^(INT\.|EXT\.)\s*", "", value.upper())
    normalized = re.sub(rf"\s*-\s*({LOCATION_TIME_SUFFIX_PATTERN}).*$", "", normalized)
    return normalized.strip()


def _extract_location_definition(
    loc_name: str,
    entry: dict[str, Any],
    canonical_script: dict[str, Any],
    scene_index: dict[str, Any],
    model: str,
    feedback: str = "",
    max_tokens: int = DEFAULT_LOCATION_BIBLE_MAX_TOKENS,
) -> tuple[LocationBible, dict[str, Any]]:
    if model == "mock":
        return _mock_extract(loc_name, entry), {
            "model": "mock",
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": 0.0,
        }

    prompt = _build_extraction_prompt(loc_name, entry, canonical_script, scene_index, feedback)
    definition, cost = call_llm(
        prompt=prompt,
        model=model,
        response_schema=LocationBible,
        max_tokens=max_tokens,
        fail_on_truncation=True,
        enable_caching=True,
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
            "scene_presence": item["scene_presence"][:8],
            "source_hint": "scene_index.unique_locations",
        }
        for item in candidates
    ]
    decisions, cost = adjudicate_entity_candidates(
        entity_type="location",
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
        canonical = (decision.canonical_name or decision.candidate).strip()
        if not canonical:
            entry = {
                **_decision_to_rejection(decision),
                "rationale": "empty canonical location name",
                "outcome": "rejected_after_resolution",
            }
            rejected.append(entry)
            decision_log.append(entry)
            continue
        decision_log.append(
            {
                **_decision_to_rejection(decision),
                "resolved_name": canonical,
                "outcome": "accepted",
            }
        )
        existing = merged.get(canonical)
        if not existing:
            merged[canonical] = {
                "name": canonical,
                "scene_count": source["scene_count"],
                "scene_presence": list(source["scene_presence"]),
            }
            continue
        existing["scene_count"] += source["scene_count"]
        existing["scene_presence"] = sorted(
            list(set(existing["scene_presence"] + list(source["scene_presence"])))
        )

    approved = sorted(merged.values(), key=lambda item: item["scene_count"], reverse=True)
    return approved, rejected, decision_log, cost


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


def _run_location_qa(
    loc_name: str,
    definition: LocationBible,
    script_text: str,
    model: str,
) -> tuple[QAResult, dict[str, Any]]:
    return qa_check(
        original_input=script_text[:5000],
        prompt_used="Location extraction prompt",
        output_produced=definition.model_dump_json(),
        model=model,
        criteria=["accuracy", "narrative_relevance"],
    )


def _build_extraction_prompt(
    loc_name: str,
    entry: dict[str, Any],
    script: dict[str, Any],
    index: dict[str, Any],
    feedback: str = "",
) -> str:
    from cine_forge.ai import extract_scenes_for_entity

    relevant_text = extract_scenes_for_entity(
        script_text=script["script_text"],
        scene_index=index,
        entity_type="location",
        entity_name=loc_name,
    )
    feedback_block = f"\nQA Feedback to address: {feedback}\n" if feedback else ""
    return f"""You are a location analyst. Extract a master definition for location: {loc_name}.
    Base every field strictly on evidence from the provided screenplay \
text — scene headings, action lines, and dialogue. If an attribute \
(e.g., time period, architectural style) cannot be determined from \
the text, leave it empty rather than inventing plausible details.

    Return JSON matching LocationBible schema.
    {feedback_block}
    Before finalizing, verify that every scene set at this location \
has been considered and no descriptive details from action lines or \
dialogue have been missed.

    Location Context:
    - Name: {loc_name}
    - Scene Count: {entry['scene_count']}

    Relevant Script Scenes (set at {loc_name}):
    {relevant_text}
    """


def _mock_extract(loc_name: str, entry: dict[str, Any]) -> LocationBible:
    return LocationBible(
        location_id=_slugify(loc_name),
        name=loc_name,
        aliases=[],
        description=f"A location named {loc_name}.",
        physical_traits=["Standard location features."],
        scene_presence=entry["scene_presence"],
        narrative_significance="Host for several scenes.",
        overall_confidence=0.9,
    )


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
