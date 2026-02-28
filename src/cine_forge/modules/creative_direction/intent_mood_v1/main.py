"""Intent & Mood module — project-level tone/mood auto-detection (Spec §12.1).

Analyzes the script from a Director's perspective to produce a single IntentMood
artifact capturing the overall emotional register, cinematic references, and a
natural-language intent summary. This artifact propagates suggested defaults to
all other concern groups.
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, Field

from cine_forge.ai.llm import call_llm
from cine_forge.schemas.concern_groups import IntentMood

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Role persona
# ---------------------------------------------------------------------------

_DIRECTOR_PERSONA = """\
You are the Director — the creative vision-holder for this film. You read the script \
as a whole and identify its essential emotional DNA: the mood it lives in, the feeling \
it should leave the audience with, and the cinematic language it calls for.

Your role here is diagnostic, not prescriptive. You are surfacing what the script \
already is, not imposing a foreign aesthetic. Ground every observation in specific \
story elements, character choices, and structural patterns you observe in the text."""


# ---------------------------------------------------------------------------
# LLM response schema (structured output)
# ---------------------------------------------------------------------------

class _IntentMoodResponse(BaseModel):
    """Structured LLM output for intent/mood analysis."""

    mood_descriptors: list[str] = Field(
        description=(
            "3 to 7 emotional tags that characterize the overall tone. "
            "Examples: tense, warm, chaotic, dreamy, epic, intimate, raw, unsettling, lyrical."
        ),
        min_length=3,
        max_length=7,
    )
    reference_films: list[str] = Field(
        description=(
            "2 to 5 film titles (or director/cinematographer references) this script evokes. "
            "Be specific — prefer 'Wong Kar-wai's In the Mood for Love' over generic genre refs."
        ),
        min_length=2,
        max_length=5,
    )
    natural_language_intent: str = Field(
        description=(
            "A 2–4 sentence summary of the script's overall cinematic intent: "
            "what the story feels like, what emotional experience it builds toward, "
            "and what distinguishes its aesthetic register."
        ),
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def run_module(
    inputs: dict[str, Any], params: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    """Detect intent and mood from the script and produce one IntentMood artifact."""
    canonical_script, scene_index, script_bible = _extract_inputs(inputs)

    runtime_params = context.get("runtime_params", {}) if isinstance(context, dict) else {}
    if not isinstance(runtime_params, dict):
        runtime_params = {}

    work_model = (
        params.get("work_model")
        or params.get("model")
        or runtime_params.get("work_model")
        or runtime_params.get("model")
        or "claude-sonnet-4-6"
    )

    announce = context.get("announce_artifact")

    print(f"[intent_mood] Analyzing project-level intent & mood (model={work_model}).")

    if work_model == "mock":
        mood_data = _mock_intent_mood()
        cost: dict[str, Any] = {
            "model": "mock",
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": 0.0,
        }
    else:
        prompt = _build_prompt(canonical_script, scene_index, script_bible)
        response, call_cost = call_llm(
            prompt=prompt,
            model=work_model,
            response_schema=_IntentMoodResponse,
        )
        mood_data = {
            "scope": "project",
            "scene_id": None,
            "mood_descriptors": response.mood_descriptors,
            "reference_films": response.reference_films,
            "style_preset_id": None,
            "natural_language_intent": response.natural_language_intent,
            "user_approved": False,
        }
        cost = {
            "model": call_cost.get("model", work_model),
            "input_tokens": call_cost.get("input_tokens", 0),
            "output_tokens": call_cost.get("output_tokens", 0),
            "estimated_cost_usd": call_cost.get("estimated_cost_usd", 0.0),
        }

    # Validate against schema
    intent_mood = IntentMood(**mood_data)

    artifact = _build_artifact(intent_mood)

    if announce:
        announce(artifact)

    print(
        f"[intent_mood] Complete: mood={intent_mood.mood_descriptors}, "
        f"refs={intent_mood.reference_films}. "
        f"Cost: ${cost['estimated_cost_usd']:.4f}"
    )

    return {"artifacts": [artifact], "cost": cost}


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------


def _build_prompt(
    canonical_script: dict[str, Any],
    scene_index: dict[str, Any],
    script_bible: dict[str, Any] | None,
) -> str:
    """Construct the Director's intent/mood analysis prompt."""
    script_text = canonical_script.get("script_text", "")
    # Truncate for token budget — first ~4000 chars gives a strong tonal read
    script_excerpt = script_text[:4000]
    truncated = len(script_text) > 4000

    scene_count = len(scene_index.get("entries", []))
    characters = scene_index.get("unique_characters", [])
    char_list = ", ".join(characters[:20]) if characters else "unknown"

    bible_block = ""
    if script_bible:
        title = script_bible.get("title", "")
        genre = script_bible.get("genre", "")
        logline = script_bible.get("logline", "")
        if any([title, genre, logline]):
            bible_block = f"""
SCRIPT BIBLE SUMMARY:
- Title: {title or 'untitled'}
- Genre: {genre or 'unspecified'}
- Logline: {logline or 'none'}
"""

    truncation_note = (
        "\n[SCRIPT TRUNCATED — excerpt above covers first 4000 characters only]\n"
        if truncated else ""
    )

    return f"""{_DIRECTOR_PERSONA}

Analyze the following script excerpt and produce a precise intent/mood assessment.
{bible_block}
PRODUCTION CONTEXT:
- Total scenes: {scene_count}
- Principal characters: {char_list}

SCRIPT:
{script_excerpt}
{truncation_note}
Return JSON with three fields:
- mood_descriptors: a list of 3–7 emotional tags (e.g. "tense", "melancholic", "lyrical")
- reference_films: a list of 2–5 specific film titles or filmmakers this script evokes
- natural_language_intent: a 2–4 sentence paragraph describing the script's overall
  cinematic intent and emotional register

Ground every choice in what you actually observe in this script — tone of dialogue,
structural choices, character dynamics, thematic preoccupations. Do not invent.
"""


# ---------------------------------------------------------------------------
# Artifact builder
# ---------------------------------------------------------------------------


def _build_artifact(intent_mood: IntentMood) -> dict[str, Any]:
    return {
        "artifact_type": "intent_mood",
        "entity_id": "project",
        "data": intent_mood.model_dump(mode="json"),
        "schema_name": "intent_mood",
        "metadata": {
            "intent": "Project-level mood and tone — propagates defaults to all concern groups",
            "rationale": (
                "Director-perspective analysis of the script's emotional register, "
                "cinematic references, and overall aesthetic intent."
            ),
            "confidence": 0.85,
            "source": "ai",
            "annotations": {
                "mood_count": len(intent_mood.mood_descriptors),
                "reference_count": len(intent_mood.reference_films),
                "user_approved": intent_mood.user_approved,
            },
        },
    }


# ---------------------------------------------------------------------------
# Mock support
# ---------------------------------------------------------------------------


def _mock_intent_mood() -> dict[str, Any]:
    return {
        "scope": "project",
        "scene_id": None,
        "mood_descriptors": ["tense", "atmospheric", "melancholic"],
        "reference_films": ["Blade Runner", "In the Mood for Love"],
        "style_preset_id": None,
        "natural_language_intent": (
            "A brooding, atmospheric piece with underlying tension and moments of quiet beauty."
        ),
        "user_approved": False,
    }


# ---------------------------------------------------------------------------
# Input extraction
# ---------------------------------------------------------------------------


def _extract_inputs(
    inputs: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any] | None]:
    """Extract canonical_script, scene_index, and optional script_bible via duck-typing."""
    canonical_script = None
    scene_index = None
    script_bible = None

    for payload in inputs.values():
        if not isinstance(payload, dict):
            continue
        if "script_text" in payload:
            canonical_script = payload
        elif "entries" in payload and "unique_characters" in payload:
            scene_index = payload
        elif "title" in payload and "logline" in payload:
            script_bible = payload

    if not canonical_script:
        raise ValueError(
            "intent_mood_v1 requires a canonical_script input"
            " (must have 'script_text')"
        )
    if not scene_index:
        raise ValueError(
            "intent_mood_v1 requires a scene_index input"
            " (must have 'entries' and 'unique_characters')"
        )

    return canonical_script, scene_index, script_bible
