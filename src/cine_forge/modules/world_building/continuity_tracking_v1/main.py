"""Track entity state changes (continuity) across scenes."""

from __future__ import annotations

from typing import Any

from cine_forge.ai.llm import call_llm
from cine_forge.modules.world_building.continuity_tracking_v1.prompting import (
    PROMPT_STATE_VALUE_MAX_CHARS,
    SCENE_CONTINUITY_MAX_TOKENS,
    EntityStateExtraction,
    SceneContinuityExtraction,
    _build_continuity_prompt,
    _extract_scene_continuity,
    _format_previous_state_for_prompt,
    _property_guidance_for_entity_type,
)
from cine_forge.modules.world_building.continuity_tracking_v1.support import (
    GAP_CONFIDENCE_THRESHOLD,
    _build_entity_catalog,
    _build_index_artifact,
    _build_state_snapshot,
    _collect_module_inputs,
    _detect_and_record_gaps,
    _extract_scene_text,
    _merge_state_properties,
    _process_scene_entries,
    _resolve_present_entities,
    _resolve_work_model,
)

__all__ = [
    "EntityStateExtraction",
    "GAP_CONFIDENCE_THRESHOLD",
    "PROMPT_STATE_VALUE_MAX_CHARS",
    "SCENE_CONTINUITY_MAX_TOKENS",
    "SceneContinuityExtraction",
    "_build_continuity_prompt",
    "_build_state_snapshot",
    "_detect_and_record_gaps",
    "_extract_scene_continuity",
    "_extract_scene_text",
    "_format_previous_state_for_prompt",
    "_merge_state_properties",
    "_property_guidance_for_entity_type",
    "_resolve_present_entities",
    "run_module",
]


def run_module(
    inputs: dict[str, Any], params: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    """Execute continuity tracking."""
    (
        character_bibles,
        location_bibles,
        prop_bibles,
        scene_index,
        script_text,
    ) = _collect_module_inputs(inputs)
    if not scene_index:
        raise ValueError("continuity_tracking_v1 requires scene_index input")

    work_model = _resolve_work_model(params, context)
    entities = _build_entity_catalog(character_bibles, location_bibles, prop_bibles)
    scene_entries = scene_index.get("entries", [])
    all_artifacts, timelines, all_states, total_cost, throughput = _process_scene_entries(
        scene_entries=scene_entries,
        script_text=script_text,
        entities=entities,
        work_model=work_model,
        llm_callable=call_llm,
    )
    _detect_and_record_gaps(timelines, all_states)
    _build_index_artifact(
        all_artifacts=all_artifacts,
        timelines=timelines,
        all_states=all_states,
        throughput=throughput,
        scene_count=len(scene_entries),
        work_model=work_model,
    )
    return {"artifacts": all_artifacts, "cost": total_cost}
