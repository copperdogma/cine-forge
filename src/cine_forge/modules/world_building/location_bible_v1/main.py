"""Extract location bibles and manifests from screenplay artifacts."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

from cine_forge.ai import qa_check
from cine_forge.ai.llm import call_llm
from cine_forge.schemas import (
    LocationBible,
    QAResult,
)


def run_module(
    inputs: dict[str, Any], params: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    """Execute location bible extraction."""
    canonical_script, scene_index = _extract_inputs(inputs)
    
    # Tiered Model Strategy (Subsumption)
    work_model = params.get("work_model") or params.get("model") or "gpt-4o-mini"
    verify_model = params.get("verify_model") or "gpt-4o-mini"
    escalate_model = params.get("escalate_model") or "gpt-4o"
    skip_qa = bool(params.get("skip_qa", False))

    # Higher default for bibles to avoid noise pollution
    min_appearances = int(params.get("min_scene_appearances", 1))

    # 1. Aggregate and Filter
    locations = _aggregate_locations(scene_index)
    ranked = _rank_locations(locations, scene_index)

    candidates = [
        loc for loc in ranked if loc["scene_count"] >= min_appearances
    ]

    artifacts = []
    models_seen: set[str] = set()
    total_cost = {
        "input_tokens": 0,
        "output_tokens": 0,
        "estimated_cost_usd": 0.0,
    }

    # 2. Extract for each candidate
    for entry in candidates:
        loc_name = entry["name"]
        slug = _slugify(loc_name)
        
        # Pass 1: Work
        definition, cost = _extract_location_definition(
            loc_name=loc_name,
            entry=entry,
            canonical_script=canonical_script,
            scene_index=scene_index,
            model=work_model,
        )
        _update_total_cost(total_cost, cost)
        if cost.get("model") and cost["model"] != "code":
            models_seen.add(cost["model"])

        if not skip_qa and work_model != "mock":
            # Pass 2: Verify
            qa_result, qa_cost = _run_location_qa(
                loc_name=loc_name,
                definition=definition,
                script_text=canonical_script["script_text"],
                model=verify_model,
            )
            _update_total_cost(total_cost, qa_cost)
            if qa_cost.get("model") and qa_cost["model"] != "code":
                models_seen.add(qa_cost["model"])

            if not qa_result.passed:
                # Pass 3: Escalate
                definition, esc_cost = _extract_location_definition(
                    loc_name=loc_name,
                    entry=entry,
                    canonical_script=canonical_script,
                    scene_index=scene_index,
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

        artifacts.append({
            "artifact_type": "location_bible",
            "entity_id": slug,
            "data": definition.model_dump(mode="json"),
            "metadata": {
                "intent": f"Establish master definition for location '{loc_name}'",
                "rationale": "Extracted from canonical script and scene headings.",
                "confidence": definition.overall_confidence,
                "source": "ai",
            }
        })

        artifacts.append({
            "artifact_type": "bible_manifest",
            "entity_id": f"location_{slug}",
            "data": manifest_data,
            "metadata": {
                "intent": f"Establish master bible for location '{loc_name}'",
                "rationale": "Consolidate location traits and narrative significance.",
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
        raise ValueError("location_bible_v1 requires canonical_script and scene_index inputs")
    return canonical_script, scene_index


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


def _extract_location_definition(
    loc_name: str,
    entry: dict[str, Any],
    canonical_script: dict[str, Any],
    scene_index: dict[str, Any],
    model: str,
    feedback: str = "",
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
    )
    return definition, cost


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
    feedback_block = f"\nQA Feedback to address: {feedback}\n" if feedback else ""
    return f"""You are a location analyst. Extract a master definition for location: {loc_name}.
    
    Return JSON matching LocationBible schema.
    {feedback_block}
    Location Context:
    - Name: {loc_name}
    - Scene Count: {entry['scene_count']}
    
    Script Text:
    {script['script_text']}
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
