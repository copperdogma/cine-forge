"""Story World module — project-level motif and continuity authoring (Spec §12.6)."""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, Field

from cine_forge.ai.llm import call_llm
from cine_forge.schemas.concern_groups import MotifAnnotation, StoryWorld

logger = logging.getLogger(__name__)

_STORY_WORLD_ARCHITECT_PERSONA = """\
You are the Story World Architect — the continuity-minded collaborator who tracks \
what should persist across the film beyond any single scene. You identify recurring \
visual and audio elements, cross-scene behavioral rules, and deliberate continuity \
exceptions that give the project a coherent thematic world.

Your job is not to summarize the plot. Your job is to surface what should recur:
- VISUAL MOTIFS: recurring objects, framings, weather patterns, textures, or design choices
  that gain meaning through repetition.
- AUDIO MOTIFS: recurring sounds, hums, silences, music ideas, or offscreen sonic signatures
  that carry thematic weight.
- BEHAVIORAL CONSISTENCY: cross-scene rules the crew should preserve about how key characters
  behave or present.
- CONTINUITY OVERRIDES: intentional breaks, dream logic, surreal passages, or exceptions that
  downstream tools should not mistake for continuity errors.
- RHYTHM OF WORLD REVELATION: how the world should open up, intensify, or close down over time.

Only create motifs that are specific and repeatable. Avoid generic style adjectives masquerading
as motifs."""


class _StoryWorldAuthoringResponse(BaseModel):
    continuity_override_notes: str | None = Field(default=None)
    character_behavioral_consistency_notes: str | None = Field(default=None)
    narrative_rhythm_notes: str | None = Field(default=None)
    visual_motif_annotations: list[MotifAnnotation] = Field(default_factory=list)
    audio_motif_annotations: list[MotifAnnotation] = Field(default_factory=list)
    rationale: str = Field(
        description="Why these notes and motifs best define the story world."
    )
    confidence: float = Field(ge=0.0, le=1.0)


_StoryWorldAuthoringResponse.model_rebuild()


def run_module(
    inputs: dict[str, Any], params: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    """Produce one project-level Story World artifact."""
    canonical_script, scene_index = _extract_inputs(inputs)
    intent_mood = (
        inputs.get("intent_mood")
        if isinstance(inputs.get("intent_mood"), dict)
        else None
    )
    script_bible = (
        inputs.get("script_bible")
        if isinstance(inputs.get("script_bible"), dict)
        else None
    )
    character_bibles = _coerce_artifact_list(inputs.get("character_bible"))
    location_bibles = _coerce_artifact_list(inputs.get("location_bible"))
    prop_bibles = _coerce_artifact_list(inputs.get("prop_bible"))

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

    character_ids = _baseline_ids(character_bibles, "character_id")
    location_ids = _baseline_ids(location_bibles, "location_id")
    prop_ids = _baseline_ids(prop_bibles, "prop_id")

    print(
        "[story_world] Building project-level story world "
        f"(characters={len(character_ids)}, locations={len(location_ids)}, props={len(prop_ids)})."
    )

    if work_model == "mock":
        authored = _mock_response()
        cost: dict[str, Any] = {
            "model": "mock",
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": 0.0,
        }
    else:
        prompt = _build_prompt(
            canonical_script=canonical_script,
            scene_index=scene_index,
            intent_mood=intent_mood,
            script_bible=script_bible,
            character_bibles=character_bibles,
            location_bibles=location_bibles,
            prop_bibles=prop_bibles,
        )
        authored, call_cost = call_llm(
            prompt=prompt,
            model=work_model,
            response_schema=_StoryWorldAuthoringResponse,
            max_tokens=3200,
        )
        cost = {
            "model": call_cost.get("model", work_model),
            "input_tokens": call_cost.get("input_tokens", 0),
            "output_tokens": call_cost.get("output_tokens", 0),
            "estimated_cost_usd": call_cost.get("estimated_cost_usd", 0.0),
        }

    story_world = StoryWorld(
        character_design_baselines=character_ids,
        location_design_baselines=location_ids,
        prop_design_baselines=prop_ids,
        continuity_override_notes=authored.continuity_override_notes,
        character_behavioral_consistency_notes=authored.character_behavioral_consistency_notes,
        narrative_rhythm_notes=authored.narrative_rhythm_notes,
        visual_motif_annotations=authored.visual_motif_annotations,
        audio_motif_annotations=authored.audio_motif_annotations,
        user_approved=False,
    )

    artifact = _build_artifact(story_world, authored.rationale, authored.confidence)
    if announce:
        announce(artifact)

    print(
        "[story_world] Complete: "
        f"{len(story_world.visual_motif_annotations)} visual motifs, "
        f"{len(story_world.audio_motif_annotations)} audio motifs. "
        f"Cost: ${cost['estimated_cost_usd']:.4f}"
    )

    return {"artifacts": [artifact], "cost": cost}


def _build_prompt(
    *,
    canonical_script: dict[str, Any],
    scene_index: dict[str, Any],
    intent_mood: dict[str, Any] | None,
    script_bible: dict[str, Any] | None,
    character_bibles: list[dict[str, Any]],
    location_bibles: list[dict[str, Any]],
    prop_bibles: list[dict[str, Any]],
) -> str:
    script_text = str(canonical_script.get("script_text", ""))
    script_excerpt = script_text[:5000]
    scene_entries = scene_index.get("entries", [])

    scene_summary_lines: list[str] = []
    for entry in scene_entries[:10]:
        if not isinstance(entry, dict):
            continue
        scene_summary_lines.append(
            f"- {entry.get('scene_id', '?')} {entry.get('heading', 'Unknown')} "
            f"(tone={entry.get('tone_mood', 'n/a')}, "
            f"location={entry.get('location', 'n/a')}, "
            f"characters={', '.join(entry.get('characters_present', [])[:4]) or 'n/a'})"
        )
    scene_summary = "\n".join(scene_summary_lines) or "- No scene summaries available."

    bible_block = _entity_reference_block(
        label="CHARACTERS",
        items=character_bibles,
        id_key="character_id",
        name_key="name",
        detail_keys=("description",),
    )
    location_block = _entity_reference_block(
        label="LOCATIONS",
        items=location_bibles,
        id_key="location_id",
        name_key="name",
        detail_keys=("physical_description", "atmosphere", "description"),
    )
    prop_block = _entity_reference_block(
        label="PROPS",
        items=prop_bibles,
        id_key="prop_id",
        name_key="name",
        detail_keys=("description", "dramatic_significance"),
    )

    intent_block = _intent_block(intent_mood)
    script_bible_block = _script_bible_block(script_bible)

    return f"""{_STORY_WORLD_ARCHITECT_PERSONA}

Analyse the project and author a Story World artifact.

Hard requirements:
- Only attach motif `entity_id` values that appear in the provided entity reference lists.
- Use `scope="world"` for project-wide motifs.
- Use `character` / `location` / `prop` when tied to a specific entity.
- Use `scene` only when a motif is intentionally local to named scenes.
- Use `scene_refs` only with valid scene IDs from the scene summary list.
- Prefer 2 to 6 strong visual motifs and 1 to 5 strong audio motifs over many weak ones.
- Do not repeat generic look or sound adjectives unless they form a specific recurring pattern.
- Return JSON only.

{intent_block}{script_bible_block}
PROJECT OVERVIEW:
- Total scenes: {len(scene_entries)}
- Unique characters: {', '.join(scene_index.get('unique_characters', [])[:20]) or 'n/a'}
- Unique locations: {', '.join(scene_index.get('unique_locations', [])[:20]) or 'n/a'}

SCENE SUMMARY:
{scene_summary}

ENTITY REFERENCES:
{bible_block}
{location_block}
{prop_block}

SCRIPT EXCERPT:
{script_excerpt}

Return JSON with these fields:
- continuity_override_notes
- character_behavioral_consistency_notes
- narrative_rhythm_notes
- visual_motif_annotations
- audio_motif_annotations
- rationale
- confidence
"""


def _intent_block(intent_mood: dict[str, Any] | None) -> str:
    if not intent_mood:
        return ""
    parts: list[str] = ["INTENT / MOOD:"]
    moods = intent_mood.get("mood_descriptors", [])
    if moods:
        parts.append(f"- Mood: {', '.join(moods)}")
    refs = intent_mood.get("reference_films", [])
    if refs:
        parts.append(f"- References: {', '.join(refs)}")
    natural_language = intent_mood.get("natural_language_intent")
    if natural_language:
        parts.append(f"- Intent: {natural_language}")
    style_preset = intent_mood.get("style_preset_id")
    if style_preset:
        parts.append(f"- Style preset: {style_preset}")
    return "\n".join(parts) + "\n\n"


def _script_bible_block(script_bible: dict[str, Any] | None) -> str:
    if not script_bible:
        return ""
    lines = ["SCRIPT BIBLE:"]
    if script_bible.get("title"):
        lines.append(f"- Title: {script_bible['title']}")
    if script_bible.get("logline"):
        lines.append(f"- Logline: {script_bible['logline']}")
    themes = script_bible.get("themes", [])
    if isinstance(themes, list) and themes:
        rendered_themes = [
            str(item.get("theme", item)) if isinstance(item, dict) else str(item)
            for item in themes[:6]
        ]
        lines.append(f"- Themes: {', '.join(rendered_themes)}")
    return "\n".join(lines) + "\n\n"


def _entity_reference_block(
    *,
    label: str,
    items: list[dict[str, Any]],
    id_key: str,
    name_key: str,
    detail_keys: tuple[str, ...],
) -> str:
    if not items:
        return f"{label}:\n- None provided."
    lines = [f"{label}:"]
    for item in items[:12]:
        entity_id = _entity_id(item, id_key)
        if not entity_id:
            continue
        name = str(item.get(name_key) or entity_id)
        detail = next(
            (
                str(item.get(key)).strip()
                for key in detail_keys
                if item.get(key)
            ),
            "",
        )
        suffix = f" — {detail[:180]}" if detail else ""
        lines.append(f"- {entity_id}: {name}{suffix}")
    return "\n".join(lines)


def _build_artifact(story_world: StoryWorld, rationale: str, confidence: float) -> dict[str, Any]:
    return {
        "artifact_type": "story_world",
        "entity_id": "project",
        "data": story_world.model_dump(mode="json"),
        "schema_name": "story_world",
        "metadata": {
            "intent": "Project-level Story World baselines and motifs",
            "rationale": rationale,
            "confidence": confidence,
            "source": "ai",
            "annotations": {
                "character_baseline_count": len(story_world.character_design_baselines),
                "location_baseline_count": len(story_world.location_design_baselines),
                "prop_baseline_count": len(story_world.prop_design_baselines),
                "visual_motif_count": len(story_world.visual_motif_annotations),
                "audio_motif_count": len(story_world.audio_motif_annotations),
            },
        },
    }


def _mock_response() -> _StoryWorldAuthoringResponse:
    return _StoryWorldAuthoringResponse(
        continuity_override_notes=(
            "Treat the final rooftop sequence as emotionally heightened but still literal. "
            "Do not introduce surreal continuity breaks elsewhere without explicit cause."
        ),
        character_behavioral_consistency_notes=(
            "Mara stays tightly controlled until decisive breaks; Owen projects calm even "
            "when making ruthless choices."
        ),
        narrative_rhythm_notes=(
            "The world should feel increasingly stripped back: crowded machinery and process "
            "early, then wind, distance, and exposed silence as the cost becomes visible."
        ),
        visual_motif_annotations=[
            MotifAnnotation(
                motif_name="Threshold Glass",
                description="Transparent barriers mark the line between control and consequence.",
                scope="location",
                entity_id="lab",
                scene_refs=["scene_001"],
            ),
            MotifAnnotation(
                motif_name="Wind Exposure",
                description=(
                    "Open air and exposed horizons signal emotional truth after sealed spaces."
                ),
                scope="world",
                scene_refs=["scene_002"],
            ),
        ],
        audio_motif_annotations=[
            MotifAnnotation(
                motif_name="Mechanical Hum",
                description=(
                    "System noise represents the cost of letting harmful processes keep running."
                ),
                scope="world",
                scene_refs=["scene_001"],
            ),
            MotifAnnotation(
                motif_name="Held Silence",
                description=(
                    "Silence lands whenever a character is forced to face the moral price "
                    "of a choice."
                ),
                scope="scene",
                entity_id="scene_002",
                scene_refs=["scene_002"],
            ),
        ],
        rationale=(
            "The story world is defined by systems, thresholds, and the exposed silence "
            "that follows irreversible choices."
        ),
        confidence=0.84,
    )


def _extract_inputs(inputs: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    canonical_script = None
    scene_index = None
    for payload in inputs.values():
        if isinstance(payload, dict) and "script_text" in payload:
            canonical_script = payload
        if isinstance(payload, dict) and "entries" in payload and "unique_characters" in payload:
            scene_index = payload
    if not canonical_script or not scene_index:
        raise ValueError("story_world_v1 requires canonical_script and scene_index inputs")
    return canonical_script, scene_index


def _coerce_artifact_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _baseline_ids(items: list[dict[str, Any]], preferred_key: str) -> list[str]:
    seen: list[str] = []
    for item in items:
        entity_id = _entity_id(item, preferred_key)
        if entity_id and entity_id not in seen:
            seen.append(entity_id)
    return seen


def _entity_id(item: dict[str, Any], preferred_key: str) -> str | None:
    for key in (preferred_key, "entity_id", "character_id", "location_id", "prop_id"):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None
