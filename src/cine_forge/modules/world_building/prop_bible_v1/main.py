"""Extract prop bibles and manifests from screenplay artifacts."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

from cine_forge.ai import qa_check
from cine_forge.ai.llm import call_llm
from cine_forge.schemas import (
    PropBible,
    QAResult,
)


def run_module(
    inputs: dict[str, Any], params: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    """Execute prop bible extraction."""
    canonical_script, scene_index = _extract_inputs(inputs)
    
    # Tiered Model Strategy (Subsumption)
    work_model = params.get("work_model") or params.get("model") or "gpt-4o-mini"
    verify_model = params.get("verify_model") or "gpt-4o-mini"
    escalate_model = params.get("escalate_model") or "gpt-4o"
    skip_qa = bool(params.get("skip_qa", False))

    # discovery pass for props since they aren't in scene_index
    props = _discover_props(canonical_script, work_model)

    artifacts = []
    models_seen: set[str] = set()
    if work_model != "mock":
        models_seen.add(work_model)

    total_cost = {
        "input_tokens": 0,
        "output_tokens": 0,
        "estimated_cost_usd": 0.0,
    }

    # 2. Extract for each candidate
    for prop_name in props:
        slug = _slugify(prop_name)
        
        # Pass 1: Work
        definition, cost = _extract_prop_definition(
            prop_name=prop_name,
            canonical_script=canonical_script,
            model=work_model,
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
            "artifact_type": "bible_manifest",
            "entity_id": f"prop_{slug}",
            "data": manifest_data,
            "metadata": {
                "intent": f"Establish master bible for prop '{prop_name}'",
                "rationale": "Consolidate prop traits and narrative significance.",
                "confidence": definition.overall_confidence,
                "source": "ai",
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


def _extract_inputs(inputs: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    canonical_script = None
    scene_index = None
    for payload in inputs.values():
        if isinstance(payload, dict) and "script_text" in payload:
            canonical_script = payload
        if isinstance(payload, dict) and "unique_locations" in payload and "entries" in payload:
            scene_index = payload
    
    if not canonical_script or not scene_index:
        raise ValueError("prop_bible_v1 requires canonical_script and scene_index inputs")
    return canonical_script, scene_index


def _discover_props(script: dict[str, Any], model: str) -> list[str]:
    if model == "mock":
        return ["Hero Sword", "Secret Map"]
    
    prompt = f"""You are a prop scout. Identify significant props in the following script.
    A significant prop is an object that is repeatedly used or has narrative importance.
    Return a simple list of prop names, one per line.
    
    Script Text:
    {script['script_text'][:5000]}
    """
    text, _ = call_llm(prompt=prompt, model=model)
    return [line.strip() for line in text.splitlines() if line.strip()]


def _extract_prop_definition(
    prop_name: str,
    canonical_script: dict[str, Any],
    model: str,
    feedback: str = "",
) -> tuple[PropBible, dict[str, Any]]:
    if model == "mock":
        return _mock_extract(prop_name), {
            "model": "mock",
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": 0.0,
        }

    prompt = _build_extraction_prompt(prop_name, canonical_script, feedback)
    definition, cost = call_llm(
        prompt=prompt,
        model=model,
        response_schema=PropBible,
    )
    return definition, cost


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
) -> str:
    feedback_block = f"\nQA Feedback to address: {feedback}\n" if feedback else ""
    return f"""You are a prop analyst. Extract a master definition for prop: {prop_name}.
    
    Return JSON matching PropBible schema.
    {feedback_block}
    Script Text:
    {script['script_text']}
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
