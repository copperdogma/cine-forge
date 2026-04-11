"""Prompting and LLM extraction helpers for continuity tracking."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, Field

from cine_forge.schemas import ContinuityEvent, StateProperty

logger = logging.getLogger(__name__)

SCENE_CONTINUITY_MAX_TOKENS = 2400
SCENE_CONTINUITY_MAX_ATTEMPTS = 2
SCENE_CONTINUITY_REQUEST_TIMEOUT_SECONDS = 45.0
SCENE_CONTINUITY_RETRY_DELAY_SECONDS = 1.0
SCENE_CONTINUITY_ERROR_MAX_CHARS = 240
PROMPT_STATE_VALUE_MAX_CHARS = 120


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


def _extract_scene_continuity(
    *,
    scene_entry: dict[str, Any],
    scene_text: str,
    present_entities: list[str],
    entities: dict[str, dict[str, Any]],
    current_states: dict[str, dict[str, StateProperty]],
    model: str,
    llm_callable: Callable[..., Any],
) -> tuple[SceneContinuityExtraction, dict[str, Any]]:
    """Call the LLM to extract continuity state for all entities in a scene."""
    prompt = _build_continuity_prompt(
        scene_entry=scene_entry,
        scene_text=scene_text,
        present_entities=present_entities,
        entities=entities,
        current_states=current_states,
    )

    scene_id = scene_entry.get("scene_id", "unknown")
    last_exc: Exception | None = None
    last_reason = "unknown_error"
    attempts_used = 0

    for attempt in range(1, SCENE_CONTINUITY_MAX_ATTEMPTS + 1):
        attempts_used = attempt
        try:
            result, metadata = llm_callable(
                prompt=prompt,
                model=model,
                response_schema=SceneContinuityExtraction,
                max_retries=0,
                max_tokens=SCENE_CONTINUITY_MAX_TOKENS,
                temperature=0.0,
                fail_on_truncation=True,
                enable_caching=True,
                request_timeout_seconds=SCENE_CONTINUITY_REQUEST_TIMEOUT_SECONDS,
            )
            return result, {
                "model": metadata.get("model", model),
                "input_tokens": metadata.get("input_tokens", 0),
                "output_tokens": metadata.get("output_tokens", 0),
                "estimated_cost_usd": metadata.get("estimated_cost_usd", 0.0),
                "scene_result_status": "success",
                "scene_result_reason": "completed",
                "scene_result_error": None,
                "attempt_count": attempt,
                "retry_count": attempt - 1,
            }
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            last_reason = _classify_scene_failure(exc)
            if attempt < SCENE_CONTINUITY_MAX_ATTEMPTS and _scene_failure_is_retryable(
                last_reason
            ):
                logger.warning(
                    "[continuity] Scene %s attempt %s/%s failed (%s); retrying: %s",
                    scene_id,
                    attempt,
                    SCENE_CONTINUITY_MAX_ATTEMPTS,
                    last_reason,
                    exc,
                )
                time.sleep(SCENE_CONTINUITY_RETRY_DELAY_SECONDS)
                continue
            logger.warning(
                "[continuity] Scene %s failed after %s attempt(s) (%s): %s",
                scene_id,
                attempt,
                last_reason,
                exc,
            )
            break

    return SceneContinuityExtraction(
        scene_id=scene_id,
        entity_states=[],
    ), {
        "model": model,
        "input_tokens": 0,
        "output_tokens": 0,
        "estimated_cost_usd": 0.0,
        "scene_result_status": "failed",
        "scene_result_reason": last_reason,
        "scene_result_error": _clip_scene_error(str(last_exc) if last_exc else None),
        "attempt_count": attempts_used,
        "retry_count": max(attempts_used - 1, 0),
    }


def _scene_failure_is_retryable(reason: str) -> bool:
    return reason in {
        "invalid_json",
        "overloaded",
        "rate_limited",
        "timeout",
        "transport_error",
        "truncated",
    }


def _classify_scene_failure(exc: Exception) -> str:
    message = str(exc).lower()
    if "timed out" in message or "timeout" in message:
        return "timeout"
    if "rate limit" in message or "http error 429" in message:
        return "rate_limited"
    if "overloaded" in message or "http error 529" in message:
        return "overloaded"
    if "valid json" in message:
        return "invalid_json"
    if "truncated" in message or "max token limit" in message:
        return "truncated"
    if "request failed" in message or "temporarily unavailable" in message:
        return "transport_error"
    return "llm_error"


def _clip_scene_error(error: str | None) -> str | None:
    if error is None:
        return None
    normalized = " ".join(error.split())
    if len(normalized) <= SCENE_CONTINUITY_ERROR_MAX_CHARS:
        return normalized
    return normalized[: SCENE_CONTINUITY_ERROR_MAX_CHARS - 3].rstrip() + "..."


def _build_continuity_prompt(
    scene_entry: dict[str, Any],
    scene_text: str,
    present_entities: list[str],
    entities: dict[str, dict[str, Any]],
    current_states: dict[str, dict[str, StateProperty]],
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
        name = (
            ent_data.get("name")
            or ent_data.get("character_id")
            or ent_data.get("location_id")
            or ent_data.get("prop_id")
            or entity_key
        )
        prev_text = _format_previous_state_for_prompt(current_states.get(entity_key, {}))
        prop_guidance = _property_guidance_for_entity_type(ent_type)
        entity_sections.append(
            f"### {ent_type.title()}: {name} (key: {entity_key})\n"
            f"Previous state:\n{prev_text}\n"
            f"{prop_guidance}"
        )

    entities_block = "\n\n".join(entity_sections)
    lines = [
        "You are a script supervisor reading screenplay continuity.",
        "",
        "Read the scene and return structured continuity updates for each listed entity.",
        "Focus on continuity-relevant state only.",
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
        "1. Return `properties` only for state observed in this scene or needed",
        "   to explain a change. Do not repeat unchanged carried-forward state;",
        "   the caller will merge it into the final snapshot.",
        "2. Each property needs:",
        '   - `key`: property name (e.g. "costume", "emotional_state")',
        "   - `value`: concise value (prefer <=12 words)",
        "   - `confidence`: 0.0-1.0 (1.0 = explicit in script,",
        "     0.5-0.8 = inferred, <0.5 = guessing)",
        "",
        "3. If a property truly changes from the previous state, add a",
        "   `change_event`:",
        "   - `property_key`: which property changed",
        "   - `previous_value`: what it was before (null if first appearance)",
        "   - `new_value`: what it is now, or null if the property no longer applies",
        "   - `reason`: very short why-change note",
        "   - `evidence`: short direct excerpt from the scene text",
        "   - `is_explicit`: true if stated in script, false if inferred",
        "   - `confidence`: how certain you are about this change",
        "",
        "4. Set `confidence` for each entity: overall confidence in the",
        "   accuracy of this state extraction (0.0-1.0).",
        "",
        "Important:",
        "- Only extract properties with scene evidence. Do not invent filler.",
        "- If nothing continuity-relevant changes for an entity, keep the entity",
        "  in the response with empty `properties` and empty `change_events`.",
        "- If a property from the previous state is not mentioned, leave it out",
        "  of `properties` instead of restating it.",
        "- Prefer concise evidence excerpts, not full-sentence quotes.",
        "- Use the exact entity_key values provided",
        '  (e.g. "character:billy", "location:dock").',
        f"- The scene_id in your response must be: {scene_id}",
    ]
    return "\n".join(lines)


def _property_guidance_for_entity_type(entity_type: str) -> str:
    """Return concise property guidance for one entity type."""
    if entity_type == "character":
        return (
            "Track: costume/wardrobe, physical_condition, emotional_state, "
            "props_carried."
        )
    if entity_type == "location":
        return (
            "Track: lighting, time_of_day, weather, damage_or_changes, atmosphere."
        )
    if entity_type == "prop":
        return "Track: condition, position, ownership."
    return "Track only continuity-relevant observable state."


def _format_previous_state_for_prompt(previous_state: dict[str, StateProperty]) -> str:
    """Render the prior state compactly for prompt context."""
    if not previous_state:
        return "  (First appearance — no previous state)"

    return "\n".join(
        f"  - {key}: {_clip_prompt_value(prop.value)}"
        for key, prop in previous_state.items()
    )


def _clip_prompt_value(value: str) -> str:
    """Trim verbose carried-forward values so prompt context stays compact."""
    normalized = " ".join(value.split())
    if len(normalized) <= PROMPT_STATE_VALUE_MAX_CHARS:
        return normalized
    return normalized[: PROMPT_STATE_VALUE_MAX_CHARS - 1].rstrip() + "…"
