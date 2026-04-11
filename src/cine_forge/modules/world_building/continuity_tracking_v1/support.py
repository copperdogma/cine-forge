"""Support helpers for continuity_tracking_v1."""

from __future__ import annotations

import logging
import re
from collections.abc import Callable
from typing import Any

from cine_forge.modules.world_building.continuity_tracking_v1.prompting import (
    EntityStateExtraction,
    _extract_scene_continuity,
)
from cine_forge.schemas import (
    ContinuityEvent,
    ContinuityIndex,
    ContinuityState,
    EntityTimeline,
    StateProperty,
)

logger = logging.getLogger(__name__)

GAP_CONFIDENCE_THRESHOLD = 0.4


def _collect_module_inputs(
    inputs: dict[str, Any],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, Any] | None,
    str | None,
]:
    """Normalize the module's heterogenous input payloads."""
    character_bibles: list[dict[str, Any]] = []
    location_bibles: list[dict[str, Any]] = []
    prop_bibles: list[dict[str, Any]] = []
    scene_index: dict[str, Any] | None = None
    script_text: str | None = None

    for _stage_id, data_list in inputs.items():
        if not isinstance(data_list, list):
            if isinstance(data_list, dict):
                if "unique_locations" in data_list:
                    scene_index = data_list
                elif "script_text" in data_list:
                    script_text = data_list["script_text"]
            continue

        for data in data_list:
            if not isinstance(data, dict):
                continue
            if "character_id" in data:
                character_bibles.append(data)
            elif "location_id" in data:
                location_bibles.append(data)
            elif "prop_id" in data:
                prop_bibles.append(data)

    return character_bibles, location_bibles, prop_bibles, scene_index, script_text


def _resolve_work_model(params: dict[str, Any], context: dict[str, Any]) -> str:
    """Resolve the active work model using the repo's standard runtime fallback chain."""
    runtime_params = context.get("runtime_params", {}) if isinstance(context, dict) else {}
    if not isinstance(runtime_params, dict):
        runtime_params = {}

    return (
        params.get("work_model")
        or params.get("model")
        or params.get("default_model")
        or runtime_params.get("work_model")
        or runtime_params.get("default_model")
        or runtime_params.get("model")
        or "claude-sonnet-4-6"
    )


def _build_entity_catalog(
    character_bibles: list[dict[str, Any]],
    location_bibles: list[dict[str, Any]],
    prop_bibles: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Build a keyed map of continuity-trackable entities."""
    entities: dict[str, dict[str, Any]] = {}
    for character in character_bibles:
        entities[f"character:{character['character_id']}"] = {
            "type": "character",
            "data": character,
        }
    for location in location_bibles:
        entities[f"location:{location['location_id']}"] = {
            "type": "location",
            "data": location,
        }
    for prop in prop_bibles:
        entities[f"prop:{prop['prop_id']}"] = {
            "type": "prop",
            "data": prop,
        }
    return entities


def _resolve_present_entities(
    scene_entry: dict[str, Any],
    entities: dict[str, dict[str, Any]],
) -> list[str]:
    """Resolve the continuity-tracked entities present in one scene."""
    present_entities: list[str] = []
    for char in scene_entry.get("characters_present", []):
        present_entities.append(f"character:{_slugify(char)}")
    if scene_entry.get("location"):
        present_entities.append(f"location:{_slugify(scene_entry['location'])}")
    for prop_name in scene_entry.get("props_mentioned", []):
        present_entities.append(f"prop:{_slugify(prop_name)}")

    return [entity_key for entity_key in present_entities if entity_key in entities]


def _process_scene_entries(
    *,
    scene_entries: list[dict[str, Any]],
    script_text: str | None,
    entities: dict[str, dict[str, Any]],
    work_model: str,
    llm_callable: Callable[..., Any],
) -> tuple[
    list[dict[str, Any]],
    dict[str, EntityTimeline],
    dict[str, ContinuityState],
    dict[str, Any],
    dict[str, int],
]:
    """Process all scenes and produce continuity artifacts plus throughput metadata."""
    script_lines: list[str] = script_text.splitlines() if script_text else []
    all_artifacts: list[dict[str, Any]] = []
    timelines: dict[str, EntityTimeline] = {}
    all_states: dict[str, ContinuityState] = {}
    total_cost: dict[str, Any] = {
        "model": work_model,
        "input_tokens": 0,
        "output_tokens": 0,
        "estimated_cost_usd": 0.0,
    }
    current_states: dict[str, dict[str, StateProperty]] = {}
    throughput = {
        "scene_calls": 0,
        "observed_properties": 0,
        "carried_forward_properties": 0,
        "change_event_count": 0,
    }

    for story_pos, scene_entry in enumerate(scene_entries):
        scene_id = scene_entry["scene_id"]
        present_entities = _resolve_present_entities(scene_entry, entities)
        if not present_entities:
            continue

        if work_model == "mock":
            _process_mock_scene(
                scene_id=scene_id,
                story_pos=story_pos,
                present_entities=present_entities,
                entities=entities,
                all_artifacts=all_artifacts,
                all_states=all_states,
                timelines=timelines,
                current_states=current_states,
                throughput=throughput,
            )
            continue

        _process_ai_scene(
            scene_entry=scene_entry,
            script_lines=script_lines,
            story_pos=story_pos,
            present_entities=present_entities,
            entities=entities,
            model=work_model,
            llm_callable=llm_callable,
            current_states=current_states,
            total_cost=total_cost,
            throughput=throughput,
            all_artifacts=all_artifacts,
            all_states=all_states,
            timelines=timelines,
        )

    return all_artifacts, timelines, all_states, total_cost, throughput


def _process_ai_scene(
    *,
    scene_entry: dict[str, Any],
    script_lines: list[str],
    story_pos: int,
    present_entities: list[str],
    entities: dict[str, dict[str, Any]],
    model: str,
    llm_callable: Callable[..., Any],
    current_states: dict[str, dict[str, StateProperty]],
    total_cost: dict[str, Any],
    throughput: dict[str, int],
    all_artifacts: list[dict[str, Any]],
    all_states: dict[str, ContinuityState],
    timelines: dict[str, EntityTimeline],
) -> None:
    """Process one scene through the real LLM continuity path."""
    scene_id = scene_entry["scene_id"]
    scene_text = _extract_scene_text(script_lines, scene_entry)
    if not scene_text.strip():
        logger.warning("[continuity] Empty scene text for %s, skipping AI call", scene_id)
        return

    throughput["scene_calls"] += 1
    extraction, call_cost = _extract_scene_continuity(
        scene_entry=scene_entry,
        scene_text=scene_text,
        present_entities=present_entities,
        entities=entities,
        current_states=current_states,
        model=model,
        llm_callable=llm_callable,
    )
    _update_total_cost(total_cost, call_cost)

    extraction_map = {
        entity_state.entity_key: entity_state
        for entity_state in extraction.entity_states
    }
    for entity_key in present_entities:
        ent_info = entities[entity_key]
        state_data, observed_count, carried_forward_count, change_event_count = (
            _build_state_snapshot(
                entity_key=entity_key,
                ent_info=ent_info,
                scene_id=scene_id,
                story_pos=story_pos,
                extraction=extraction_map.get(entity_key),
                previous_state=current_states.get(entity_key, {}),
            )
        )
        throughput["observed_properties"] += observed_count
        throughput["carried_forward_properties"] += carried_forward_count
        throughput["change_event_count"] += change_event_count

        artifact_id = f"{entity_key.replace(':', '_')}_{scene_id}"
        _record_state(
            state_data=state_data,
            artifact_id=artifact_id,
            entity_key=entity_key,
            ent_info=ent_info,
            all_artifacts=all_artifacts,
            all_states=all_states,
            timelines=timelines,
            current_states=current_states,
        )


def _process_mock_scene(
    *,
    scene_id: str,
    story_pos: int,
    present_entities: list[str],
    entities: dict[str, dict[str, Any]],
    all_artifacts: list[dict[str, Any]],
    all_states: dict[str, ContinuityState],
    timelines: dict[str, EntityTimeline],
    current_states: dict[str, dict[str, StateProperty]],
    throughput: dict[str, int],
) -> None:
    """Produce deterministic continuity states for the mock model path."""
    for entity_key in present_entities:
        ent_info = entities[entity_key]
        state_data = _generate_mock_state(
            entity_key=entity_key,
            ent_info=ent_info,
            scene_id=scene_id,
            story_pos=story_pos,
        )
        throughput["observed_properties"] += len(state_data.properties)
        artifact_id = f"{entity_key.replace(':', '_')}_{scene_id}"
        _record_state(
            state_data=state_data,
            artifact_id=artifact_id,
            entity_key=entity_key,
            ent_info=ent_info,
            all_artifacts=all_artifacts,
            all_states=all_states,
            timelines=timelines,
            current_states=current_states,
        )


def _build_index_artifact(
    *,
    all_artifacts: list[dict[str, Any]],
    timelines: dict[str, EntityTimeline],
    all_states: dict[str, ContinuityState],
    throughput: dict[str, int],
    scene_count: int,
    work_model: str,
) -> None:
    """Append the project-level continuity index artifact."""
    total_gaps = sum(len(timeline.gaps) for timeline in timelines.values())
    total_states = sum(len(timeline.states) for timeline in timelines.values())
    overall_score = _compute_overall_score(
        timelines=timelines,
        all_states=all_states,
        total_states=total_states,
    )

    index = ContinuityIndex(
        timelines=timelines,
        total_gaps=total_gaps,
        overall_continuity_score=round(min(max(overall_score, 0.0), 1.0), 3),
    )

    all_artifacts.append(
        {
            "artifact_type": "continuity_index",
            "entity_id": "project",
            "data": index.model_dump(mode="json"),
            "metadata": {
                "intent": "Master index of all entity state timelines.",
                "rationale": (
                    f"Tracked {len(timelines)} entities across {scene_count} scenes. "
                    f"{total_gaps} gaps detected."
                ),
                "confidence": index.overall_continuity_score,
                "source": "ai" if work_model != "mock" else "mock",
                "throughput": throughput,
            },
        }
    )


def _compute_overall_score(
    *,
    timelines: dict[str, EntityTimeline],
    all_states: dict[str, ContinuityState],
    total_states: int,
) -> float:
    """Compute the weighted continuity score for the project."""
    if total_states <= 0:
        return 0.0

    weighted_sum = 0.0
    for timeline in timelines.values():
        entity_confidences = [
            all_states[state_id].overall_confidence
            for state_id in timeline.states
            if state_id in all_states
        ]
        if entity_confidences:
            weighted_sum += sum(entity_confidences)
    return weighted_sum / total_states


def _extract_scene_text(script_lines: list[str], scene_entry: dict[str, Any]) -> str:
    """Extract script text for a scene using source_span (1-based -> 0-indexed)."""
    span = scene_entry.get("source_span", {})
    start = span.get("start_line", 1) - 1
    end = span.get("end_line", len(script_lines))
    return "\n".join(script_lines[start:end])


def _build_state_snapshot(
    *,
    entity_key: str,
    ent_info: dict[str, Any],
    scene_id: str,
    story_pos: int,
    extraction: EntityStateExtraction | None,
    previous_state: dict[str, StateProperty],
) -> tuple[ContinuityState, int, int, int]:
    """Build the persisted state snapshot from sparse scene-local extraction."""
    if extraction is None:
        return _build_missing_state(
            entity_key=entity_key,
            ent_info=ent_info,
            scene_id=scene_id,
            story_pos=story_pos,
            previous_state=previous_state,
        )

    merged_properties, carried_forward_count = _merge_state_properties(
        previous_state=previous_state,
        extracted_properties=extraction.properties,
        change_events=extraction.change_events,
    )
    return (
        ContinuityState(
            entity_type=ent_info["type"],
            entity_id=entity_key.split(":")[1],
            scene_id=scene_id,
            story_time_position=story_pos,
            properties=merged_properties,
            change_events=extraction.change_events,
            overall_confidence=extraction.confidence,
        ),
        len(extraction.properties),
        carried_forward_count,
        len(extraction.change_events),
    )


def _build_missing_state(
    *,
    entity_key: str,
    ent_info: dict[str, Any],
    scene_id: str,
    story_pos: int,
    previous_state: dict[str, StateProperty],
) -> tuple[ContinuityState, int, int, int]:
    """Fallback state when the model omits an entity from the scene response."""
    carried_forward = [prop.model_copy(deep=True) for prop in previous_state.values()]
    return (
        ContinuityState(
            entity_type=ent_info["type"],
            entity_id=entity_key.split(":")[1],
            scene_id=scene_id,
            story_time_position=story_pos,
            properties=carried_forward,
            change_events=[],
            overall_confidence=0.35 if carried_forward else 0.3,
        ),
        0,
        len(carried_forward),
        0,
    )


def _merge_state_properties(
    *,
    previous_state: dict[str, StateProperty],
    extracted_properties: list[StateProperty],
    change_events: list[ContinuityEvent],
) -> tuple[list[StateProperty], int]:
    """Merge sparse scene-local properties with the last known carried-forward state."""
    merged: dict[str, StateProperty] = {
        key: prop.model_copy(deep=True) for key, prop in previous_state.items()
    }
    removed_keys = {
        event.property_key for event in change_events if event.new_value is None
    }
    for key in removed_keys:
        merged.pop(key, None)

    extracted_keys: list[str] = []
    for prop in extracted_properties:
        merged[prop.key] = prop.model_copy(deep=True)
        if prop.key not in extracted_keys:
            extracted_keys.append(prop.key)

    ordered_keys: list[str] = []
    for key in extracted_keys:
        if key in merged and key not in ordered_keys:
            ordered_keys.append(key)
    for key in previous_state:
        if key in merged and key not in ordered_keys:
            ordered_keys.append(key)

    carry_forward_count = sum(1 for key in ordered_keys if key not in extracted_keys)
    return [merged[key] for key in ordered_keys], carry_forward_count


def _record_state(
    *,
    state_data: ContinuityState,
    artifact_id: str,
    entity_key: str,
    ent_info: dict[str, Any],
    all_artifacts: list[dict[str, Any]],
    all_states: dict[str, ContinuityState],
    timelines: dict[str, EntityTimeline],
    current_states: dict[str, dict[str, StateProperty]],
) -> None:
    """Record a state snapshot as an artifact and update tracking structures."""
    all_artifacts.append(
        {
            "artifact_type": "continuity_state",
            "entity_id": artifact_id,
            "data": state_data.model_dump(mode="json"),
            "metadata": {
                "intent": f"Continuity snapshot for {entity_key} in scene {state_data.scene_id}",
                "rationale": "Automated state tracking based on scene progression.",
                "confidence": state_data.overall_confidence,
                "source": "ai",
            },
        }
    )
    all_states[artifact_id] = state_data

    timeline = timelines.setdefault(
        entity_key,
        EntityTimeline(
            entity_type=ent_info["type"],  # type: ignore[arg-type]
            entity_id=entity_key.split(":")[1],
        ),
    )
    timeline.states.append(artifact_id)
    current_states[entity_key] = {
        prop.key: prop.model_copy(deep=True) for prop in state_data.properties
    }


def _detect_and_record_gaps(
    timelines: dict[str, EntityTimeline],
    all_states: dict[str, ContinuityState],
) -> None:
    """Scan timelines for low-confidence, empty-state, or contradictory snapshots."""
    for timeline in timelines.values():
        gaps: list[str] = []
        prev_props: dict[str, str] = {}

        for state_id in timeline.states:
            state = all_states.get(state_id)
            if not state:
                continue
            if not state.properties:
                gaps.append(state.scene_id)
                continue
            if state.overall_confidence < GAP_CONFIDENCE_THRESHOLD:
                gaps.append(state.scene_id)

            current_props = {prop.key: prop.value for prop in state.properties}
            change_keys = {event.property_key for event in state.change_events}
            for key, value in current_props.items():
                if key in prev_props and prev_props[key] != value and key not in change_keys:
                    if state.scene_id not in gaps:
                        gaps.append(state.scene_id)
                    break
            prev_props = current_props

        timeline.gaps = gaps


def _generate_mock_state(
    entity_key: str,
    ent_info: dict[str, Any],
    scene_id: str,
    story_pos: int,
) -> ContinuityState:
    """Generate deterministic mock states for testing."""
    props: list[StateProperty] = []
    if ent_info["type"] == "character":
        props.append(StateProperty(key="costume", value="Standard", confidence=1.0))
        props.append(StateProperty(key="condition", value="Healthy", confidence=1.0))
    elif ent_info["type"] == "location":
        props.append(StateProperty(key="lighting", value="Natural", confidence=1.0))

    return ContinuityState(
        entity_type=ent_info["type"],  # type: ignore[arg-type]
        entity_id=entity_key.split(":")[1],
        scene_id=scene_id,
        story_time_position=story_pos,
        properties=props,
        change_events=[],
        overall_confidence=1.0,
    )


def _update_total_cost(total: dict[str, Any], call_cost: dict[str, Any]) -> None:
    total["input_tokens"] += call_cost.get("input_tokens", 0)
    total["output_tokens"] += call_cost.get("output_tokens", 0)
    total["estimated_cost_usd"] += call_cost.get("estimated_cost_usd", 0.0)


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
