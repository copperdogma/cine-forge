"""Track entity state changes (continuity) across scenes.

Story 092: Implements the real LLM-powered continuity detection — reading script
text scene-by-scene, extracting entity state properties, detecting change events
with evidence, and flagging gaps where state is ambiguous or contradictory.
"""

import logging
import re
from typing import Any

from pydantic import BaseModel, Field

from cine_forge.ai.llm import call_llm
from cine_forge.schemas import (
    ContinuityEvent,
    ContinuityIndex,
    ContinuityState,
    EntityTimeline,
    StateProperty,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# LLM response schemas (module-internal, not persisted as artifacts)
# ---------------------------------------------------------------------------


class EntityStateExtraction(BaseModel):
    """LLM extraction result for one entity in a scene."""

    entity_key: str = Field(description="Entity key, e.g. 'character:billy' or 'location:dock'")
    properties: list[StateProperty] = Field(default_factory=list)
    change_events: list[ContinuityEvent] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=0.7)


class SceneContinuityExtraction(BaseModel):
    """LLM extraction result for all entities in a single scene."""

    scene_id: str
    entity_states: list[EntityStateExtraction] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Minimum confidence below which a state is flagged as a gap
GAP_CONFIDENCE_THRESHOLD = 0.4


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def run_module(
    inputs: dict[str, Any], params: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    """Execute continuity tracking."""
    # 1. Extract inputs
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

    if not scene_index:
        raise ValueError("continuity_tracking_v1 requires scene_index input")

    # Tiered Model Strategy (subsumption chain — matches character_bible_v1)
    runtime_params = context.get("runtime_params", {}) if isinstance(context, dict) else {}
    if not isinstance(runtime_params, dict):
        runtime_params = {}

    work_model = (
        params.get("work_model")
        or params.get("model")
        or params.get("default_model")
        or runtime_params.get("work_model")
        or runtime_params.get("default_model")
        or runtime_params.get("model")
        or "claude-sonnet-4-6"
    )

    # 2. Build entity map for tracking
    entities: dict[str, dict[str, Any]] = {}
    for c in character_bibles:
        entities[f"character:{c['character_id']}"] = {"type": "character", "data": c}
    for loc in location_bibles:
        entities[f"location:{loc['location_id']}"] = {"type": "location", "data": loc}
    for p in prop_bibles:
        entities[f"prop:{p['prop_id']}"] = {"type": "prop", "data": p}

    # Pre-split script lines for scene text extraction
    script_lines: list[str] = script_text.splitlines() if script_text else []

    # 3. Process scenes in order
    all_artifacts: list[dict[str, Any]] = []
    timelines: dict[str, EntityTimeline] = {}
    # Map from artifact_id -> ContinuityState for gap detection
    all_states: dict[str, ContinuityState] = {}
    total_cost: dict[str, Any] = {
        "model": work_model,
        "input_tokens": 0,
        "output_tokens": 0,
        "estimated_cost_usd": 0.0,
    }

    # Current state of every entity (carry-forward between scenes)
    current_states: dict[str, dict[str, str]] = {}  # entity_key -> {property_key -> value}

    scene_entries = scene_index.get("entries", [])
    for i, scene_entry in enumerate(scene_entries):
        scene_id = scene_entry["scene_id"]

        # Determine which entities are present in this scene
        present_entities: list[str] = []
        for char in scene_entry.get("characters_present", []):
            present_entities.append(f"character:{_slugify(char)}")
        if scene_entry.get("location"):
            present_entities.append(f"location:{_slugify(scene_entry['location'])}")
        for prop_name in scene_entry.get("props_mentioned", []):
            present_entities.append(f"prop:{_slugify(prop_name)}")

        # Filter to entities we actually have bibles for
        present_entities = [ek for ek in present_entities if ek in entities]

        if not present_entities:
            continue

        if work_model == "mock":
            # Mock path: per-entity deterministic stubs (unchanged from Story 011)
            for entity_key in present_entities:
                ent_info = entities[entity_key]
                state_data = _generate_mock_state(
                    entity_key=entity_key,
                    ent_info=ent_info,
                    scene_id=scene_id,
                    story_pos=i,
                )
                artifact_id = f"{entity_key.replace(':', '_')}_{scene_id}"
                _record_state(
                    state_data, artifact_id, entity_key, ent_info,
                    all_artifacts, all_states, timelines, current_states,
                )
        else:
            # Real AI path: one LLM call per scene covering all present entities
            scene_text = _extract_scene_text(script_lines, scene_entry)
            if not scene_text.strip():
                logger.warning("[continuity] Empty scene text for %s, skipping AI call", scene_id)
                continue

            extraction, call_cost = _extract_scene_continuity(
                scene_entry=scene_entry,
                scene_text=scene_text,
                present_entities=present_entities,
                entities=entities,
                current_states=current_states,
                model=work_model,
            )
            _update_total_cost(total_cost, call_cost)

            # Map LLM results to individual ContinuityState artifacts
            extraction_map = {es.entity_key: es for es in extraction.entity_states}
            for entity_key in present_entities:
                ent_info = entities[entity_key]
                es = extraction_map.get(entity_key)

                if es:
                    state_data = ContinuityState(
                        entity_type=ent_info["type"],
                        entity_id=entity_key.split(":")[1],
                        scene_id=scene_id,
                        story_time_position=i,
                        properties=es.properties,
                        change_events=es.change_events,
                        overall_confidence=es.confidence,
                    )
                else:
                    # LLM didn't return data for this entity — low-confidence empty state
                    state_data = ContinuityState(
                        entity_type=ent_info["type"],
                        entity_id=entity_key.split(":")[1],
                        scene_id=scene_id,
                        story_time_position=i,
                        properties=[],
                        change_events=[],
                        overall_confidence=0.3,
                    )

                artifact_id = f"{entity_key.replace(':', '_')}_{scene_id}"
                _record_state(
                    state_data, artifact_id, entity_key, ent_info,
                    all_artifacts, all_states, timelines, current_states,
                )

    # 4. Gap detection
    _detect_and_record_gaps(timelines, all_states)

    # 5. Compute real scores
    total_gaps = sum(len(tl.gaps) for tl in timelines.values())
    total_states = sum(len(tl.states) for tl in timelines.values())
    if total_states > 0:
        # Weighted average: each entity's avg confidence × number of states
        weighted_sum = 0.0
        for _entity_key, tl in timelines.items():
            entity_confidences = [
                all_states[sid].overall_confidence
                for sid in tl.states
                if sid in all_states
            ]
            if entity_confidences:
                weighted_sum += sum(entity_confidences)
        overall_score = weighted_sum / total_states
    else:
        overall_score = 0.0

    index = ContinuityIndex(
        timelines=timelines,
        total_gaps=total_gaps,
        overall_continuity_score=round(min(max(overall_score, 0.0), 1.0), 3),
    )

    all_artifacts.append({
        "artifact_type": "continuity_index",
        "entity_id": "project",
        "data": index.model_dump(mode="json"),
        "metadata": {
            "intent": "Master index of all entity state timelines.",
            "rationale": f"Tracked {len(timelines)} entities across {len(scene_entries)} scenes. "
                         f"{total_gaps} gaps detected.",
            "confidence": index.overall_continuity_score,
            "source": "ai" if work_model != "mock" else "mock",
        },
    })

    return {
        "artifacts": all_artifacts,
        "cost": total_cost,
    }


# ---------------------------------------------------------------------------
# Scene text extraction
# ---------------------------------------------------------------------------


def _extract_scene_text(script_lines: list[str], scene_entry: dict[str, Any]) -> str:
    """Extract script text for a scene using source_span (1-based → 0-indexed)."""
    span = scene_entry.get("source_span", {})
    start = span.get("start_line", 1) - 1
    end = span.get("end_line", len(script_lines))
    return "\n".join(script_lines[start:end])


# ---------------------------------------------------------------------------
# LLM continuity extraction
# ---------------------------------------------------------------------------


def _extract_scene_continuity(
    scene_entry: dict[str, Any],
    scene_text: str,
    present_entities: list[str],
    entities: dict[str, dict[str, Any]],
    current_states: dict[str, dict[str, str]],
    model: str,
) -> tuple[SceneContinuityExtraction, dict[str, Any]]:
    """Call the LLM to extract continuity state for all entities in a scene."""
    prompt = _build_continuity_prompt(
        scene_entry=scene_entry,
        scene_text=scene_text,
        present_entities=present_entities,
        entities=entities,
        current_states=current_states,
    )

    try:
        result, metadata = call_llm(
            prompt=prompt,
            model=model,
            response_schema=SceneContinuityExtraction,
            max_tokens=4096,
            temperature=0.0,
        )
        cost = {
            "model": metadata.get("model", model),
            "input_tokens": metadata.get("input_tokens", 0),
            "output_tokens": metadata.get("output_tokens", 0),
            "estimated_cost_usd": metadata.get("estimated_cost_usd", 0.0),
        }
        return result, cost
    except Exception as exc:
        logger.warning(
            "[continuity] LLM call failed for scene %s: %s",
            scene_entry.get("scene_id", "?"),
            exc,
        )
        # Return empty extraction on failure — states will have low confidence
        fallback = SceneContinuityExtraction(
            scene_id=scene_entry.get("scene_id", "unknown"),
            entity_states=[],
        )
        return fallback, {"input_tokens": 0, "output_tokens": 0, "estimated_cost_usd": 0.0}


def _build_continuity_prompt(
    scene_entry: dict[str, Any],
    scene_text: str,
    present_entities: list[str],
    entities: dict[str, dict[str, Any]],
    current_states: dict[str, dict[str, str]],
) -> str:
    """Build the prompt for continuity extraction."""
    scene_id = scene_entry.get("scene_id", "unknown")
    heading = scene_entry.get("heading", "UNKNOWN")
    scene_number = scene_entry.get("scene_number", "?")

    entity_sections = []
    for entity_key in present_entities:
        ent_info = entities.get(entity_key, {})
        ent_type = ent_info.get("type", "unknown")
        ent_data = ent_info.get("data", {})

        # Entity name from bible
        name = (
            ent_data.get("name")
            or ent_data.get("character_id")
            or ent_data.get("location_id")
            or ent_data.get("prop_id")
            or entity_key
        )

        # Previous state
        prev = current_states.get(entity_key, {})
        if prev:
            prev_text = "\n".join(f"  - {k}: {v}" for k, v in prev.items())
        else:
            prev_text = "  (First appearance — no previous state)"

        # Property guidance based on entity type
        if ent_type == "character":
            prop_guidance = (
                "Extract: costume/wardrobe, physical_condition (injuries, visible changes), "
                "emotional_state, props_carried (items they have)"
            )
        elif ent_type == "location":
            prop_guidance = (
                "Extract: lighting, time_of_day, weather, damage_or_changes, "
                "atmosphere (mood of the space)"
            )
        elif ent_type == "prop":
            prop_guidance = (
                "Extract: condition (intact/damaged/destroyed), position (where it is), "
                "ownership (who has it)"
            )
        else:
            prop_guidance = "Extract all observable state properties."

        entity_sections.append(
            f"### {ent_type.title()}: {name} (key: {entity_key})\n"
            f"Previous state:\n{prev_text}\n"
            f"{prop_guidance}"
        )

    entities_block = "\n\n".join(entity_sections)

    # Build prompt as a list of lines to stay within line-length limits
    lines = [
        "You are a Script Supervisor analyzing continuity for a screenplay.",
        "",
        "Your job: read the scene text and for each entity present, extract",
        "their current observable state and detect changes from previous state.",
        "",
        "## Scene",
        f"Scene {scene_number}: {heading}",
        f"Scene ID: {scene_id}",
        "",
        "```",
        scene_text,
        "```",
        "",
        "## Entities Present",
        "",
        entities_block,
        "",
        "## Instructions",
        "",
        "For each entity:",
        "1. Extract current state **properties** — only include properties",
        "   observable or inferable from this scene. Each property needs:",
        '   - `key`: property name (e.g. "costume", "emotional_state")',
        "   - `value`: current value as a concise description",
        "   - `confidence`: 0.0-1.0 (1.0 = explicit in script,",
        "     0.5-0.8 = inferred, <0.5 = guessing)",
        "",
        "2. Detect **change_events** — if a property differs from the",
        "   previous state, record:",
        "   - `property_key`: which property changed",
        "   - `previous_value`: what it was before (null if first appearance)",
        "   - `new_value`: what it is now",
        "   - `reason`: why it changed (brief)",
        "   - `evidence`: exact quote from the scene text",
        "   - `is_explicit`: true if stated in script, false if inferred",
        "   - `confidence`: how certain you are about this change",
        "",
        "3. Set `confidence` for each entity: overall confidence in the",
        "   accuracy of this state extraction (0.0-1.0).",
        "",
        "Important:",
        "- Only extract properties with evidence in this scene.",
        "  Do not invent state.",
        "- If a property from the previous state is not mentioned,",
        "  carry it forward unchanged (not a change event).",
        "- Use the exact entity_key values provided",
        '  (e.g. "character:billy", "location:dock").',
        f"- The scene_id in your response must be: {scene_id}",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# State recording helpers
# ---------------------------------------------------------------------------


def _record_state(
    state_data: ContinuityState,
    artifact_id: str,
    entity_key: str,
    ent_info: dict[str, Any],
    all_artifacts: list[dict[str, Any]],
    all_states: dict[str, ContinuityState],
    timelines: dict[str, EntityTimeline],
    current_states: dict[str, dict[str, str]],
) -> None:
    """Record a state snapshot as an artifact and update tracking structures."""
    all_artifacts.append({
        "artifact_type": "continuity_state",
        "entity_id": artifact_id,
        "data": state_data.model_dump(mode="json"),
        "metadata": {
            "intent": f"Continuity snapshot for {entity_key} in scene {state_data.scene_id}",
            "rationale": "Automated state tracking based on scene progression.",
            "confidence": state_data.overall_confidence,
            "source": "ai",
        },
    })

    all_states[artifact_id] = state_data

    timeline = timelines.setdefault(entity_key, EntityTimeline(
        entity_type=ent_info["type"],  # type: ignore[arg-type]
        entity_id=entity_key.split(":")[1],
    ))
    timeline.states.append(artifact_id)

    # Update carry-forward state for next scene
    current_states[entity_key] = {p.key: p.value for p in state_data.properties}


# ---------------------------------------------------------------------------
# Gap detection
# ---------------------------------------------------------------------------


def _detect_and_record_gaps(
    timelines: dict[str, EntityTimeline],
    all_states: dict[str, ContinuityState],
) -> None:
    """Scan timelines for gaps: low confidence, empty properties, or unexplained contradictions."""
    for _entity_key, timeline in timelines.items():
        gaps: list[str] = []
        prev_props: dict[str, str] = {}

        for state_id in timeline.states:
            state = all_states.get(state_id)
            if not state:
                continue

            # Gap condition 1: no properties extracted
            if not state.properties:
                gaps.append(state.scene_id)
                continue

            # Gap condition 2: overall confidence below threshold
            if state.overall_confidence < GAP_CONFIDENCE_THRESHOLD:
                gaps.append(state.scene_id)

            # Gap condition 3: property contradiction without a change event
            current_props = {p.key: p.value for p in state.properties}
            change_keys = {ce.property_key for ce in state.change_events}
            for key, value in current_props.items():
                if key in prev_props and prev_props[key] != value and key not in change_keys:
                    # Value changed but no change event explains it
                    if state.scene_id not in gaps:
                        gaps.append(state.scene_id)
                    break

            prev_props = current_props

        timeline.gaps = gaps


# ---------------------------------------------------------------------------
# Mock state generation (preserved from Story 011)
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def _update_total_cost(total: dict[str, Any], call_cost: dict[str, Any]) -> None:
    total["input_tokens"] += call_cost.get("input_tokens", 0)
    total["output_tokens"] += call_cost.get("output_tokens", 0)
    total["estimated_cost_usd"] += call_cost.get("estimated_cost_usd", 0.0)


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
