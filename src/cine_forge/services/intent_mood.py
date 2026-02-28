"""Intent/Mood propagation service — takes user mood input and generates
suggested defaults for all five concern groups via the Director role.

This is the core AI logic behind §12.1 "auto-propagation." When a user
sets mood descriptors, picks a style preset, or types a natural-language
intent, this service asks the Director to generate coherent concern group
defaults that reflect that creative vision.

Uses call_llm directly (not RoleContext.invoke) because:
1. The response schema is a custom PropagationResult, not _StructuredRoleAnswer.
2. The output spans all 5 concern groups (~4K tokens), exceeding the 1200 cap.
3. We compose the Director's prompt ourselves, including style pack context.
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, Field

from cine_forge.ai.llm import call_llm
from cine_forge.presets.models import StylePreset
from cine_forge.schemas.concern_groups import IntentMood

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-sonnet-4-6"


# ---------------------------------------------------------------------------
# Propagation result schema — what the LLM returns
# ---------------------------------------------------------------------------


class PropagatedGroup(BaseModel):
    """Suggested defaults for a single concern group."""

    fields: dict[str, Any] = Field(
        description=(
            "Key-value pairs matching the concern group schema fields. "
            "Only include fields with meaningful suggestions."
        ),
    )
    rationale: str = Field(
        description="Why these specific values were chosen for this group"
    )


class PropagationResult(BaseModel):
    """Full propagation output — suggested defaults for all concern groups."""

    look_and_feel: PropagatedGroup | None = Field(
        default=None,
        description="Visual direction suggestions based on mood",
    )
    sound_and_music: PropagatedGroup | None = Field(
        default=None,
        description="Audio direction suggestions based on mood",
    )
    rhythm_and_flow: PropagatedGroup | None = Field(
        default=None,
        description="Editorial direction suggestions based on mood",
    )
    character_and_performance: PropagatedGroup | None = Field(
        default=None,
        description="Performance direction suggestions based on mood",
    )
    story_world: PropagatedGroup | None = Field(
        default=None,
        description="World-building suggestions based on mood",
    )
    overall_rationale: str = Field(
        description="High-level explanation of the creative vision being propagated"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="How confident the Director is in this propagation",
    )


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are the Director — the creative authority for this film project.
Your task is to translate the user's creative intent into coherent
defaults for all five concern groups.

You think in terms of the total cinematic experience. Every element
should reinforce the intended mood and tell one unified story.

Important:
- Only suggest field values that meaningfully serve the stated intent.
- Leave a group as null if the mood doesn't specifically inform it.
- Ground suggestions in the script context when available.
- Be specific and cinematic — "dark" is not a lighting concept; "single overhead
  practical with deep shadow falloff" is.
- Reference the style preset hints when provided — they are expert-authored
  starting points. Adapt them to the specific script context.
"""


def _build_propagation_prompt(
    intent: IntentMood,
    script_context: str | None,
    scene_id: str | None,
    preset: StylePreset | None,
) -> str:
    """Assemble the prompt sent to the Director for propagation."""
    parts: list[str] = []

    # Intent block
    parts.append("## Creative Intent")
    if intent.mood_descriptors:
        parts.append(f"Mood: {', '.join(intent.mood_descriptors)}")
    if intent.reference_films:
        parts.append(f"References: {', '.join(intent.reference_films)}")
    if intent.natural_language_intent:
        parts.append(f"Direction: {intent.natural_language_intent}")
    if intent.style_preset_id:
        parts.append(f"Style preset: {intent.style_preset_id}")

    # Preset hints
    if preset:
        parts.append("\n## Style Preset Hints (expert-authored starting points)")
        parts.append(f"Preset: {preset.display_name} — {preset.description}")
        for group_id, hints in preset.concern_group_hints.items():
            parts.append(f"\n### {group_id}")
            for field, value in hints.items():
                parts.append(f"  {field}: {value}")

    # Script context
    if script_context:
        parts.append("\n## Script Context")
        # Truncate to avoid blowing token limits
        max_context = 3000
        if len(script_context) > max_context:
            parts.append(script_context[:max_context] + "\n[...truncated]")
        else:
            parts.append(script_context)

    # Scope
    if scene_id:
        parts.append(f"\n## Scope: Scene-level override for {scene_id}")
        parts.append(
            "Tailor suggestions to this specific scene's dramatic needs. "
            "Diverge from the project-level mood where the scene demands it."
        )
    else:
        parts.append("\n## Scope: Project-wide defaults")
        parts.append(
            "Generate defaults that work across the entire project. "
            "Individual scenes can override these later."
        )

    parts.append(
        "\n## Instructions\n"
        "Generate coherent defaults for each concern group that reflects this creative intent.\n"
        "Return a JSON object with keys: look_and_feel, sound_and_music, rhythm_and_flow, "
        "character_and_performance, story_world. Each is an object with 'fields' (dict of "
        "schema field names to string values) and 'rationale' (why). Also include "
        "'overall_rationale' (string) and 'confidence' (0-1 float).\n"
        "Only include groups where the mood meaningfully informs the direction. "
        "Leave groups as null if the intent doesn't specifically affect them."
    )

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def propagate_intent(
    intent: IntentMood,
    script_context: str | None = None,
    scene_id: str | None = None,
    preset: StylePreset | None = None,
    model: str = DEFAULT_MODEL,
    director_system_prompt: str | None = None,
) -> tuple[PropagationResult, dict[str, Any]]:
    """Run mood propagation: IntentMood → suggested concern group defaults.

    Args:
        intent: The user's creative intent (mood, references, preset, NL).
        script_context: Script bible summary or scene text for grounding.
        scene_id: If set, propagation is scoped to this scene.
        preset: Resolved StylePreset (if intent.style_preset_id is set).
        model: LLM model to use for propagation.
        director_system_prompt: Optional override for the Director system prompt
            (e.g., with style pack injection).

    Returns:
        (PropagationResult, cost_metadata) tuple.
    """
    system = director_system_prompt or _SYSTEM_PROMPT
    user_prompt = _build_propagation_prompt(intent, script_context, scene_id, preset)
    full_prompt = f"{system}\n\n{user_prompt}"

    result, cost_meta = call_llm(
        prompt=full_prompt,
        model=model,
        response_schema=PropagationResult,
        max_tokens=4096,
        temperature=0.3,  # Slightly creative, not deterministic
    )

    if isinstance(result, PropagationResult):
        return result, cost_meta

    # Fallback: parse from dict/string if needed
    return PropagationResult.model_validate(result), cost_meta
