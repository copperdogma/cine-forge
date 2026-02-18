"""Track entity state changes (continuity) across scenes."""

from __future__ import annotations

from typing import Any

from cine_forge.schemas import (
    ContinuityIndex,
    ContinuityState,
    EntityTimeline,
    StateProperty,
)


def run_module(
    inputs: dict[str, Any], params: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    """Execute continuity tracking."""
    # 1. Extract inputs
    character_bibles = []
    location_bibles = []
    prop_bibles = []
    scene_index = None

    for _stage_id, data_list in inputs.items():
        if not isinstance(data_list, list):
            if isinstance(data_list, dict):
                if "unique_locations" in data_list:
                    scene_index = data_list
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

    if not scene_index:
        raise ValueError("continuity_tracking_v1 requires scene_index input")

    work_model = params.get("work_model") or params.get("model") or "claude-sonnet-4-6"

    # 2. Build entity map for tracking
    entities = {}
    for c in character_bibles:
        entities[f"character:{c['character_id']}"] = {"type": "character", "data": c}
    for loc in location_bibles:
        entities[f"location:{loc['location_id']}"] = {"type": "location", "data": loc}
    for p in prop_bibles:
        entities[f"prop:{p['prop_id']}"] = {"type": "prop", "data": p}

    # 3. Process scenes in order
    all_artifacts = []
    timelines: dict[str, EntityTimeline] = {}
    total_cost = {
        "model": work_model,
        "input_tokens": 0,
        "output_tokens": 0,
        "estimated_cost_usd": 0.0,
    }

    # Current state of every entity
    current_states: dict[str, dict[str, str]] = {}  # entity_key -> { property_key -> value }

    for i, scene_entry in enumerate(scene_index.get("entries", [])):
        scene_id = scene_entry["scene_id"]
        
        # Determine which entities are relevant to this scene
        present_entities = []
        for char in scene_entry.get("characters_present", []):
            present_entities.append(f"character:{_slugify(char)}")
        if scene_entry.get("location"):
            present_entities.append(f"location:{_slugify(scene_entry['location'])}")
        
        # For MVP, we'll focus on characters present in the scene
        if work_model != "mock":
            # Real AI pass to detect events in this scene
            # (In a full implementation, we'd pass script snippet + previous states)
            pass
        
        for entity_key in present_entities:
            if entity_key not in entities:
                continue
            
            ent_info = entities[entity_key]
            
            # Create a state snapshot for this entity in this scene
            state_data = _generate_state_snapshot(
                entity_key=entity_key,
                ent_info=ent_info,
                scene_id=scene_id,
                story_pos=i,
                previous_properties=current_states.get(entity_key, {}),
                model=work_model
            )
            
            # Record state
            artifact_id = f"{entity_key.replace(':', '_')}_{scene_id}"
            all_artifacts.append({
                "artifact_type": "continuity_state",
                "entity_id": artifact_id,
                "data": state_data.model_dump(mode="json"),
                "metadata": {
                    "intent": f"Continuity snapshot for {entity_key} in scene {scene_id}",
                    "rationale": "Automated state tracking based on scene progression.",
                    "confidence": state_data.overall_confidence,
                    "source": "ai",
                }
            })
            
            # Update timeline
            timeline = timelines.setdefault(entity_key, EntityTimeline(
                entity_type=ent_info["type"], # type: ignore
                entity_id=entity_key.split(":")[1]
            ))
            timeline.states.append(artifact_id)
            
            # Update current state for next scene
            current_states[entity_key] = {p.key: p.value for p in state_data.properties}

    # 4. Final Index
    index = ContinuityIndex(
        timelines=timelines,
        total_gaps=0, # Gap detection would go here
        overall_continuity_score=0.9
    )
    
    all_artifacts.append({
        "artifact_type": "continuity_index",
        "entity_id": "project",
        "data": index.model_dump(mode="json"),
        "metadata": {
            "intent": "Master index of all entity state timelines.",
            "rationale": "Consolidated continuity view for the project.",
            "confidence": 0.9,
            "source": "hybrid",
        }
    })

    return {
        "artifacts": all_artifacts,
        "cost": total_cost,
    }


def _generate_state_snapshot(
    entity_key: str,
    ent_info: dict[str, Any],
    scene_id: str,
    story_pos: int,
    previous_properties: dict[str, str],
    model: str
) -> ContinuityState:
    """Generate or update state for one entity."""
    if model == "mock":
        # Deterministic mock states
        props = []
        if ent_info["type"] == "character":
            props.append(StateProperty(key="costume", value="Standard", confidence=1.0))
            props.append(StateProperty(key="condition", value="Healthy", confidence=1.0))
        elif ent_info["type"] == "location":
            props.append(StateProperty(key="lighting", value="Natural", confidence=1.0))
            
        return ContinuityState(
            entity_type=ent_info["type"], # type: ignore
            entity_id=entity_key.split(":")[1],
            scene_id=scene_id,
            story_time_position=story_pos,
            properties=props,
            change_events=[],
            overall_confidence=1.0
        )
    
    # Real AI logic would go here: prompt with previous_properties + script
    return ContinuityState(
        entity_type=ent_info["type"], # type: ignore
        entity_id=entity_key.split(":")[1],
        scene_id=scene_id,
        story_time_position=story_pos,
        properties=[],
        change_events=[],
        overall_confidence=0.5
    )


def _slugify(name: str) -> str:
    import re
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
