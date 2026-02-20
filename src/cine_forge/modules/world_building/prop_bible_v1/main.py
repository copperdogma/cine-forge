"""Extract prop bibles and manifests from screenplay artifacts."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

from cine_forge.ai import adjudicate_entity_candidates, qa_check
from cine_forge.ai.llm import call_llm
from cine_forge.schemas import (
    EntityAdjudicationDecision,
    PropBible,
    QAResult,
)


def run_module(
    inputs: dict[str, Any], params: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    """Execute prop bible extraction."""
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

    # discovery pass for props since they aren't in scene_index
    if discovery_results and discovery_results.get("props"):
        props = discovery_results["props"]
        print(f"[prop_bible] Using {len(props)} props from discovery results.")
    else:
        props = _discover_props(canonical_script, work_model)

    # Sanity check: typical screenplay has 3-8 significant props
    if len(props) > 25:
        print(
            f"[prop_bible] WARNING: Discovered {len(props)} props, which is unusually high. "
            "Truncating to 25. This may indicate over-extraction or preamble filter failure."
        )
        props = props[:25]
    (
        props,
        adjudication_rejections,
        adjudication_decisions,
        adjudication_cost,
    ) = _adjudicate_candidates(
        props=props,
        script_text=canonical_script["script_text"],
        model=work_model,
    )

    artifacts = []
    models_seen: set[str] = set()
    if work_model != "mock":
        models_seen.add(work_model)

    total_cost = {
        "input_tokens": 0,
        "output_tokens": 0,
        "estimated_cost_usd": 0.0,
    }
    _update_total_cost(total_cost, adjudication_cost)
    if adjudication_cost.get("model") and adjudication_cost["model"] != "code":
        models_seen.add(str(adjudication_cost["model"]))

    # 2. Extract for each candidate
    for prop_name in props:
        slug = _slugify(prop_name)
        
        # Pass 1: Work
        definition, cost = _extract_prop_definition(
            prop_name=prop_name,
            canonical_script=canonical_script,
            model=work_model,
            scene_index=scene_index,
        )
        _update_total_cost(total_cost, cost)
        if cost.get("model") and cost["model"] != "code":
            models_seen.add(cost["model"])

        if not skip_qa and work_model != "mock":
            # Pass 2: Verify
            qa_result, qa_cost = _run_prop_qa(
                prop_name=prop_name,
                definition=definition,
                script_text=canonical_script["script_text"],
                model=verify_model,
            )
            _update_total_cost(total_cost, qa_cost)
            if qa_cost.get("model") and qa_cost["model"] != "code":
                models_seen.add(qa_cost["model"])

            if not qa_result.passed:
                # Pass 3: Escalate
                definition, esc_cost = _extract_prop_definition(
                    prop_name=prop_name,
                    canonical_script=canonical_script,
                    model=escalate_model,
                    feedback=qa_result.summary,
                    scene_index=scene_index,
                )
                _update_total_cost(total_cost, esc_cost)
                if esc_cost.get("model") and esc_cost["model"] != "code":
                    models_seen.add(esc_cost["model"])
        
        # 3. Build manifest and artifact bundle
        version = 1
        master_filename = f"master_v{version}.json"
        
        manifest_data = {
            "entity_type": "prop",
            "entity_id": slug,
            "display_name": prop_name,
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

        artifacts.append({
            "artifact_type": "prop_bible",
            "entity_id": slug,
            "data": definition.model_dump(mode="json"),
            "metadata": {
                "intent": f"Establish master definition for prop '{prop_name}'",
                "rationale": "AI-identified significant object from canonical script.",
                "confidence": definition.overall_confidence,
                "source": "ai",
                "annotations": _adjudication_annotation(
                    input_count=len(props) + len(adjudication_rejections),
                    approved_count=len(props),
                    rejected=adjudication_rejections,
                    decisions=adjudication_decisions,
                ),
            }
        })

        artifacts.append({
            "artifact_type": "bible_manifest",
            "entity_id": f"prop_{slug}",
            "data": manifest_data,
            "metadata": {
                "intent": f"Establish master bible for prop '{prop_name}'",
                "rationale": "Consolidate prop traits and narrative significance.",
                "confidence": definition.overall_confidence,
                "source": "ai",
                "annotations": _adjudication_annotation(
                    input_count=len(props) + len(adjudication_rejections),
                    approved_count=len(props),
                    rejected=adjudication_rejections,
                    decisions=adjudication_decisions,
                ),
            },
            "bible_files": {
                master_filename: definition.model_dump_json(indent=2)
            }
        })

    model_label = "+".join(sorted(list(models_seen))) if models_seen else "code"
    total_cost["model"] = model_label

    return {
        "artifacts": artifacts,
        "cost": total_cost,
    }


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
        if isinstance(payload, dict) and "unique_locations" in payload and "entries" in payload:
            scene_index = payload
        if isinstance(payload, dict) and "props" in payload and "characters" in payload:
            discovery_results = payload
    
    if not canonical_script or not scene_index:
        raise ValueError("prop_bible_v1 requires canonical_script and scene_index inputs")
    return canonical_script, scene_index, discovery_results


def _discover_props(script: dict[str, Any], model: str) -> list[str]:
    if model == "mock":
        return ["Hero Sword", "Secret Map"]

    prompt = f"""You are a prop scout. Identify significant props in the following script.

    A significant prop is an object that is:
    - Physically handled by characters
    - Has narrative significance (not just set dressing)
    - Appears in multiple scenes OR is crucial to a key moment

    List ONLY props that meet these criteria. Do not include generic items,
    background objects, or set dressing.
    Typically a screenplay has 3-10 significant props.

    Return a simple list of prop names, one per line. No preamble, no commentary, no numbering.

    Script Text:
    {script['script_text'][:5000]}
    """
    text, _ = call_llm(prompt=prompt, model=model)

    # Filter out preamble, commentary, and clean up formatting
    preamble_patterns = [
        r'\b(based\s+on|here\s+are|i\s+found|analysis|the\s+following|significant)\b',
        r'\b(identified|extracted|discovered|below|above)\b',
    ]
    preamble_regex = re.compile('|'.join(preamble_patterns), re.IGNORECASE)

    props = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        # Skip obvious preamble/commentary lines
        if preamble_regex.search(line):
            continue

        # Skip lines with too many words (prop names are typically 1-3 words)
        if len(line.split()) > 5:
            continue

        # Strip leading bullet markers and numbering
        line = re.sub(r'^[\-\*\•]\s*', '', line)  # bullets
        line = re.sub(r'^\d+[\.\)]\s*', '', line)  # numbering like "1. " or "1) "

        # Strip trailing punctuation
        line = re.sub(r'[\.\:\;]+$', '', line)
        line = line.strip()

        if line:
            props.append(line)

    return props


def _extract_prop_definition(
    prop_name: str,
    canonical_script: dict[str, Any],
    model: str,
    feedback: str = "",
    scene_index: dict[str, Any] | None = None,
) -> tuple[PropBible, dict[str, Any]]:
    if model == "mock":
        return _mock_extract(prop_name), {
            "model": "mock",
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": 0.0,
        }

    prompt = _build_extraction_prompt(prop_name, canonical_script, feedback, scene_index)
    definition, cost = call_llm(
        prompt=prompt,
        model=model,
        response_schema=PropBible,
    )
    return definition, cost


def _adjudicate_candidates(
    props: list[str],
    script_text: str,
    model: str,
) -> tuple[list[str], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    if not props:
        return [], [], [], _empty_cost(model)

    upper_script = script_text.upper()
    adjudication_input = [
        {
            "candidate": prop_name,
            "mention_count": upper_script.count(prop_name.upper()),
            "source_hint": "prop_discovery_pass",
        }
        for prop_name in props
    ]
    decisions, cost = adjudicate_entity_candidates(
        entity_type="prop",
        candidates=adjudication_input,
        script_text=script_text,
        model=model,
    )

    approved: list[str] = []
    rejected: list[dict[str, Any]] = []
    decision_log: list[dict[str, Any]] = []
    seen: set[str] = set()
    for decision in decisions:
        if decision.verdict != "valid":
            entry = _decision_to_rejection(decision)
            rejected.append(entry)
            decision_log.append({**entry, "outcome": "rejected_by_verdict"})
            continue
        canonical = (decision.canonical_name or decision.candidate).strip()
        if not canonical:
            entry = {
                **_decision_to_rejection(decision),
                "rationale": "empty canonical prop name",
                "outcome": "rejected_after_resolution",
            }
            rejected.append(entry)
            decision_log.append(entry)
            continue
        key = canonical.lower()
        if key in seen:
            decision_log.append(
                {
                    **_decision_to_rejection(decision),
                    "resolved_name": canonical,
                    "outcome": "deduped_duplicate_valid",
                }
            )
            continue
        seen.add(key)
        approved.append(canonical)
        decision_log.append(
            {
                **_decision_to_rejection(decision),
                "resolved_name": canonical,
                "outcome": "accepted",
            }
        )

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


def _run_prop_qa(
    prop_name: str,
    definition: PropBible,
    script_text: str,
    model: str,
) -> tuple[QAResult, dict[str, Any]]:
    return qa_check(
        original_input=script_text[:5000],
        prompt_used="Prop extraction prompt",
        output_produced=definition.model_dump_json(),
        model=model,
        criteria=["accuracy", "narrative_relevance"],
    )


def _build_extraction_prompt(
    prop_name: str,
    script: dict[str, Any],
    feedback: str = "",
    scene_index: dict[str, Any] | None = None,
) -> str:
    from cine_forge.ai import extract_scenes_for_entity

    if scene_index:
        relevant_text = extract_scenes_for_entity(
            script_text=script["script_text"],
            scene_index=scene_index,
            entity_type="prop",
            entity_name=prop_name,
        )
    else:
        relevant_text = script["script_text"]
    feedback_block = f"\nQA Feedback to address: {feedback}\n" if feedback else ""
    return f"""You are a prop analyst. Extract a master definition for prop: {prop_name}.

    Return JSON matching PropBible schema.
    {feedback_block}
    Relevant Script Scenes (mentioning {prop_name}):
    {relevant_text}
    """


def _mock_extract(prop_name: str) -> PropBible:
    return PropBible(
        prop_id=_slugify(prop_name),
        name=prop_name,
        description=f"A prop named {prop_name}.",
        scene_presence=["scene_001"],
        narrative_significance="Used in key scenes.",
        overall_confidence=0.9,
    )


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
