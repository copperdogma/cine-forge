"""Look & Feel module — per-scene visual direction (Spec §12.2).

Produces one LookAndFeel artifact per scene and one LookAndFeelIndex for the
project.  Analyses scenes using a 3-scene sliding window (prev/current/next)
so the Visual Architect can reason about visual continuity across cuts.

Follows the editorial_direction_v1 pattern exactly.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from cine_forge.ai.llm import call_llm
from cine_forge.schemas.concern_groups import (
    LookAndFeel,
    LookAndFeelIndex,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Role persona — embedded inline (same pattern as editorial_direction_v1)
# ---------------------------------------------------------------------------

_VISUAL_ARCHITECT_PERSONA = """\
You are the Visual Architect — the film's cinematographer and production designer \
working in pre-production. You think in images: every scene is a canvas where light, \
colour, composition, and movement serve the story's emotional truth.

Your core responsibilities:
- LIGHTING PHILOSOPHY: Design the light for each scene. Motivated practicals vs. \
stylised mood lighting. Hard vs. soft quality. Key direction. How light evolves \
within a scene and across the narrative arc.
- COLOUR PALETTE: Temperature (warm/cool), saturation, contrast, dominant hues. \
Colour carries emotional meaning — not just aesthetics.
- COMPOSITION & FRAMING: Symmetry vs. asymmetry, negative space, depth of field \
intention, framing style. Frame sizes and angles that reveal character psychology.
- CAMERA PERSONALITY: Static vs. handheld. Controlled dollies vs. chaotic Steadicam. \
Observational distance vs. invasive intimacy. Match camera behaviour to the scene's \
emotional register.
- COSTUME & CHARACTER APPEARANCE: What characters wear and how they look — referencing \
bible states and continuity. Wardrobe tells the audience who someone is before they speak.
- PRODUCTION DESIGN: Set dressing, environment details, practical elements. The world \
the characters inhabit should feel specific and intentional.
- VISUAL MOTIFS: Recurring visual elements that carry thematic weight across scenes."""


def run_module(
    inputs: dict[str, Any], params: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    """Execute Look & Feel analysis across all scenes."""
    canonical_script, scene_index = _extract_inputs(inputs)
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
    verify_model = (
        params.get("verify_model")
        or params.get("qa_model")
        or runtime_params.get("verify_model")
        or runtime_params.get("qa_model")
        or "claude-haiku-4-5-20251001"
    )
    escalate_model = (
        params.get("escalate_model")
        or runtime_params.get("escalate_model")
        or "claude-opus-4-6"
    )
    skip_qa = bool(params.get("skip_qa", False))
    concurrency = int(params.get("concurrency") or runtime_params.get("concurrency") or 5)

    entries = scene_index.get("entries", [])
    script_text = canonical_script.get("script_text", "")
    script_lines = script_text.splitlines()

    # Optional enrichment inputs (loaded via store_inputs_optional in the recipe)
    bible_context = _build_bible_context(inputs)
    intent_context = _build_intent_context(inputs)

    print(f"[look_and_feel] Analysing {len(entries)} scenes (concurrency={concurrency}).")

    announce = context.get("announce_artifact")
    models_seen: set[str] = set()
    total_cost: dict[str, Any] = {
        "input_tokens": 0,
        "output_tokens": 0,
        "estimated_cost_usd": 0.0,
    }

    # Build scene windows and process in parallel
    artifacts: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        future_to_idx: dict[Any, int] = {}
        for idx, entry in enumerate(entries):
            window = _build_scene_window(entries, idx, script_lines)
            future_to_idx[executor.submit(
                _analyze_scene,
                entry=entry,
                window=window,
                bible_context=bible_context,
                intent_context=intent_context,
                work_model=work_model,
                verify_model=verify_model,
                escalate_model=escalate_model,
                skip_qa=skip_qa,
            )] = idx

        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            entry = entries[idx]
            try:
                direction, cost = future.result()
                artifact = _build_artifact(entry, direction)
                if announce:
                    announce(artifact)
                artifacts.append(artifact)
                _update_cost(total_cost, cost)
                m = cost.get("model", "code")
                if m and m != "code":
                    models_seen.update(m.split("+"))
            except Exception as exc:
                logger.warning(
                    "[look_and_feel] Failed scene '%s': %s",
                    entry.get("scene_id", f"idx_{idx}"),
                    exc,
                )

    # Stable output order
    artifacts.sort(key=lambda a: a["entity_id"])

    # Generate project-level index
    index_artifact, index_cost = _build_index(
        entries=entries,
        directions=[a["data"] for a in artifacts],
        work_model=work_model,
    )
    artifacts.append(index_artifact)
    _update_cost(total_cost, index_cost)
    m = index_cost.get("model", "code")
    if m and m != "code":
        models_seen.add(m)

    model_label = "+".join(sorted(models_seen)) if models_seen else "code"
    total_cost["model"] = model_label

    print(
        f"[look_and_feel] Complete: {len(artifacts) - 1} scene directions + 1 index. "
        f"Cost: ${total_cost['estimated_cost_usd']:.4f}"
    )

    return {"artifacts": artifacts, "cost": total_cost}


# ---------------------------------------------------------------------------
# Bible & intent context builders
# ---------------------------------------------------------------------------


def _build_bible_context(inputs: dict[str, Any]) -> str:
    """Extract character and location bible summaries from inputs."""
    sections: list[str] = []

    for payload in inputs.values():
        if not isinstance(payload, dict):
            continue

        # Character bible manifests have 'entries' with character data
        if "entries" in payload and isinstance(payload["entries"], list):
            for entry in payload["entries"]:
                if isinstance(entry, dict) and "name" in entry:
                    # Character bible entry
                    if any(k in entry for k in ("traits", "arc_summary", "description")):
                        name = entry.get("name", "Unknown")
                        desc = entry.get("description", "")
                        traits = entry.get("traits", [])
                        trait_str = ", ".join(traits[:5]) if isinstance(traits, list) else ""
                        sections.append(f"CHARACTER {name}: {desc} Traits: {trait_str}")
                    # Location bible entry
                    elif any(k in entry for k in ("atmosphere", "physical_description")):
                        name = entry.get("name", "Unknown")
                        desc = entry.get("physical_description") or entry.get("description", "")
                        atmosphere = entry.get("atmosphere", "")
                        sections.append(f"LOCATION {name}: {desc} Atmosphere: {atmosphere}")

        # Direct bible artifacts (character_bible, location_bible types)
        if payload.get("artifact_type") == "character_bible" or "traits" in payload:
            name = payload.get("name", payload.get("entity_id", "Unknown"))
            desc = payload.get("description", "")
            traits = payload.get("traits", [])
            if isinstance(traits, list):
                traits = [t.get("trait", t) if isinstance(t, dict) else str(t) for t in traits[:5]]
            sections.append(f"CHARACTER {name}: {desc} Traits: {', '.join(traits)}")

        if payload.get("artifact_type") == "location_bible" or (
            "physical_description" in payload and "atmosphere" in payload
        ):
            name = payload.get("name", payload.get("entity_id", "Unknown"))
            desc = payload.get("physical_description", "")
            atmosphere = payload.get("atmosphere", "")
            sections.append(f"LOCATION {name}: {desc} Atmosphere: {atmosphere}")

    if not sections:
        return ""
    return "ENTITY REFERENCE (from bibles):\n" + "\n".join(sections[:30])


def _build_intent_context(inputs: dict[str, Any]) -> str:
    """Extract Intent/Mood settings from inputs if available."""
    for payload in inputs.values():
        if not isinstance(payload, dict):
            continue
        # IntentMood artifact has mood_descriptors + reference_films
        if "mood_descriptors" in payload or "natural_language_intent" in payload:
            parts: list[str] = []
            moods = payload.get("mood_descriptors", [])
            if moods:
                parts.append(f"Mood: {', '.join(moods)}")
            refs = payload.get("reference_films", [])
            if refs:
                parts.append(f"References: {', '.join(refs)}")
            nl = payload.get("natural_language_intent")
            if nl:
                parts.append(f"Director's intent: {nl}")
            preset = payload.get("style_preset_id")
            if preset:
                parts.append(f"Style preset: {preset}")
            if parts:
                return "PROJECT INTENT/MOOD:\n" + "\n".join(parts)
    return ""


# ---------------------------------------------------------------------------
# Scene window construction
# ---------------------------------------------------------------------------


def _build_scene_window(
    entries: list[dict[str, Any]], idx: int, script_lines: list[str]
) -> dict[str, str | None]:
    """Build a 3-scene context window: previous, current, next scene text."""

    def _scene_text(entry: dict[str, Any]) -> str:
        span = entry.get("source_span", {})
        start = span.get("start_line", 1) - 1
        end = span.get("end_line", len(script_lines))
        return "\n".join(script_lines[start:end])

    prev_text = _scene_text(entries[idx - 1]) if idx > 0 else None
    current_text = _scene_text(entries[idx])
    next_text = _scene_text(entries[idx + 1]) if idx < len(entries) - 1 else None

    prev_heading = entries[idx - 1].get("heading", "") if idx > 0 else None
    next_heading = entries[idx + 1].get("heading", "") if idx < len(entries) - 1 else None

    return {
        "prev_heading": prev_heading,
        "prev_text": prev_text,
        "current_text": current_text,
        "next_heading": next_heading,
        "next_text": next_text,
    }


# ---------------------------------------------------------------------------
# Per-scene analysis
# ---------------------------------------------------------------------------


def _analyze_scene(
    entry: dict[str, Any],
    window: dict[str, str | None],
    bible_context: str,
    intent_context: str,
    work_model: str,
    verify_model: str,
    escalate_model: str,
    skip_qa: bool,
) -> tuple[LookAndFeel, dict[str, Any]]:
    """Analyse a single scene and return the Look & Feel direction."""
    scene_id = entry.get("scene_id", "unknown")
    cost: dict[str, Any] = {"input_tokens": 0, "output_tokens": 0, "estimated_cost_usd": 0.0}
    models_used: set[str] = set()

    if work_model == "mock":
        return _mock_direction(scene_id), {
            "model": "mock", "input_tokens": 0, "output_tokens": 0, "estimated_cost_usd": 0.0,
        }

    prompt = _build_scene_prompt(entry, window, bible_context, intent_context)
    direction, call_cost = call_llm(
        prompt=prompt,
        model=work_model,
        response_schema=LookAndFeel,
    )
    _update_cost(cost, call_cost)
    if call_cost.get("model"):
        models_used.add(call_cost["model"])

    # Override AI-generated IDs with canonical values
    direction = direction.model_copy(update={
        "scene_id": scene_id,
        "scope": "scene",
    })

    if not skip_qa and work_model != "mock":
        from cine_forge.ai import qa_check

        qa_result, qa_cost = qa_check(
            original_input=window["current_text"] or "",
            prompt_used="Look & Feel visual analysis",
            output_produced=direction.model_dump_json(),
            model=verify_model,
            criteria=["accuracy", "completeness", "visual_specificity"],
        )
        _update_cost(cost, qa_cost)
        if qa_cost.get("model"):
            models_used.add(qa_cost["model"])

        if not qa_result.passed:
            # Escalate with feedback
            escalate_prompt = _build_scene_prompt(
                entry, window, bible_context, intent_context, feedback=qa_result.summary,
            )
            direction, esc_cost = call_llm(
                prompt=escalate_prompt,
                model=escalate_model,
                response_schema=LookAndFeel,
            )
            direction = direction.model_copy(update={
                "scene_id": scene_id,
                "scope": "scene",
            })
            _update_cost(cost, esc_cost)
            if esc_cost.get("model"):
                models_used.add(esc_cost["model"])

    cost["model"] = "+".join(sorted(models_used)) if models_used else "code"
    return direction, cost


def _build_scene_prompt(
    entry: dict[str, Any],
    window: dict[str, str | None],
    bible_context: str,
    intent_context: str,
    feedback: str = "",
) -> str:
    """Construct the visual analysis prompt with 3-scene context and bible/intent enrichment."""
    scene_id = entry.get("scene_id", "unknown")
    heading = entry.get("heading", "")
    scene_number = entry.get("scene_number", 0)
    characters = ", ".join(entry.get("characters_present", []))
    tone = entry.get("tone_mood", "unspecified")
    time_of_day = entry.get("time_of_day", "")
    location = entry.get("location", "")

    # Build context sections
    prev_section = ""
    if window.get("prev_text"):
        prev_section = f"""
PREVIOUS SCENE ({window['prev_heading']}):
{window['prev_text'][:3000]}
"""

    next_section = ""
    if window.get("next_text"):
        next_section = f"""
NEXT SCENE ({window['next_heading']}):
{window['next_text'][:3000]}
"""

    feedback_block = f"\nQA FEEDBACK TO ADDRESS:\n{feedback}\n" if feedback else ""

    intent_block = f"\n{intent_context}\n" if intent_context else ""
    bible_block = f"\n{bible_context}\n" if bible_context else ""

    return f"""{_VISUAL_ARCHITECT_PERSONA}

Analyse the following scene and produce Look & Feel visual direction.

IMPORTANT: Consider the adjacent scenes for visual continuity across cuts.
A jarring colour shift or lighting change between scenes should be intentional, not accidental.
Reference the Intent/Mood settings as the director's global vision.
Reference character and location bibles for appearance consistency.
Be specific and cinematic — not "warm lighting" but "late afternoon practicals through
venetian blinds, warm amber, hard light, half his expression in shadow."
{feedback_block}{intent_block}{bible_block}
SCENE METADATA:
- Scene ID: {scene_id}
- Scene Number: {scene_number}
- Heading: {heading}
- Location: {location}
- Time of Day: {time_of_day}
- Characters: {characters}
- Tone/Mood: {tone}
{prev_section}
CURRENT SCENE ({heading}):
{window['current_text']}
{next_section}
Return JSON matching the LookAndFeel schema with these fields:
- scene_id: "{scene_id}"
- scope: "scene"
- lighting_concept: key light direction, quality, motivated vs. stylised
- color_palette: dominant colours, temperature, saturation, contrast
- composition_philosophy: symmetry, negative space, DOF, framing style
- camera_personality: static vs. handheld, observational vs. intimate
- reference_imagery: list of visual references informing this scene
- costume_notes: character appearance referencing bible states
- production_design_notes: set dressing, environment details
- visual_motifs: list of MotifAnnotation objects with thematic weight
- aspect_ratio_override: null unless scene needs a different ratio
"""


# ---------------------------------------------------------------------------
# Project-level index
# ---------------------------------------------------------------------------


def _build_index(
    entries: list[dict[str, Any]],
    directions: list[dict[str, Any]],
    work_model: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build the project-level Look & Feel index."""
    if work_model == "mock":
        index = LookAndFeelIndex(
            total_scenes=len(entries),
            scenes_with_direction=len(directions),
            overall_visual_language=(
                "Mock: Naturalistic with selective stylisation "
                "for emotional peaks."
            ),
            dominant_color_palette=(
                "Mock: Warm earth tones shifting to cool blues "
                "in Act 3."
            ),
            lighting_arc=(
                "Mock: Soft naturalism in Act 1, increasingly "
                "dramatic in Act 2, stark in Act 3."
            ),
            key_visual_motifs=["Window light", "Shadow play"],
            scenes_with_special_visual_needs=[],
            visual_consistency_concerns=[],
            confidence=0.9,
        )
        return _build_index_artifact(index, directions), {
            "model": "mock", "input_tokens": 0, "output_tokens": 0, "estimated_cost_usd": 0.0,
        }

    # Summarise per-scene directions for the index prompt
    scene_summaries = []
    for d in sorted(directions, key=lambda x: x.get("scene_number", 0)):
        scene_summaries.append(
            f"Scene ({d.get('heading', '?')}): "
            f"lighting={d.get('lighting_concept', '?')}, "
            f"palette={d.get('color_palette', '?')}, "
            f"camera={d.get('camera_personality', '?')}, "
            f"composition={d.get('composition_philosophy', '?')}"
        )
    summary_text = "\n".join(scene_summaries)

    prompt = f"""{_VISUAL_ARCHITECT_PERSONA}

You have completed per-scene Look & Feel direction for {len(directions)} scenes.
Now produce a project-level index that summarises the overall visual language
and identity of the film.

PER-SCENE DIRECTION SUMMARIES:
{summary_text}

Return JSON matching the LookAndFeelIndex schema:
- total_scenes: {len(entries)}
- scenes_with_direction: {len(directions)}
- overall_visual_language: high-level visual identity description for the entire film
- dominant_color_palette: project-wide colour tendencies — temperature, saturation, contrast arc
- lighting_arc: how lighting evolves across the narrative arc
- key_visual_motifs: list of recurring visual elements carrying thematic weight
- scenes_with_special_visual_needs: scenes requiring distinctive treatment (dream, flashback, etc.)
- visual_consistency_concerns: potential continuity or style coherence issues
- confidence: your confidence in this aggregate analysis (0.0-1.0)
"""

    index, cost = call_llm(
        prompt=prompt,
        model=work_model,
        response_schema=LookAndFeelIndex,
    )
    # Override counts with actual values
    index = index.model_copy(update={
        "total_scenes": len(entries),
        "scenes_with_direction": len(directions),
    })
    return _build_index_artifact(index, directions), cost


def _build_index_artifact(
    index: LookAndFeelIndex, directions: list[dict[str, Any]]
) -> dict[str, Any]:
    return {
        "artifact_type": "look_and_feel_index",
        "entity_id": "project",
        "data": index.model_dump(mode="json"),
        "schema_name": "look_and_feel_index",
        "metadata": {
            "intent": "Summarise Look & Feel direction across all scenes",
            "rationale": (
                f"Aggregate visual analysis of "
                f"{index.scenes_with_direction} scene directions."
            ),
            "confidence": index.confidence,
            "source": "ai",
            "annotations": {
                "scene_count": index.total_scenes,
                "direction_count": index.scenes_with_direction,
            },
        },
    }


# ---------------------------------------------------------------------------
# Artifact builders
# ---------------------------------------------------------------------------


def _build_artifact(entry: dict[str, Any], direction: LookAndFeel) -> dict[str, Any]:
    scene_id = entry.get("scene_id", "unknown")
    return {
        "artifact_type": "look_and_feel",
        "entity_id": scene_id,
        "data": direction.model_dump(mode="json"),
        "schema_name": "look_and_feel",
        "metadata": {
            "intent": f"Look & Feel direction for {entry.get('heading', scene_id)}",
            "rationale": (
                "Per-scene visual analysis: lighting, colour, composition, "
                "camera personality, costume, and visual motifs."
            ),
            "confidence": 0.85,
            "source": "ai",
            "annotations": {
                "lighting": direction.lighting_concept,
                "palette": direction.color_palette,
                "camera": direction.camera_personality,
            },
        },
    }


# ---------------------------------------------------------------------------
# Mock support
# ---------------------------------------------------------------------------


def _mock_direction(scene_id: str) -> LookAndFeel:
    return LookAndFeel(
        scope="scene",
        scene_id=scene_id,
        lighting_concept=(
            "Motivated practicals — overhead fluorescent with a warm key from the window. "
            "Hard light cutting diagonal shadows across the desk."
        ),
        color_palette=(
            "Desaturated warm base — muted ochre and brown. Cool blue-grey in the shadows. "
            "Moderate contrast with lifted blacks."
        ),
        composition_philosophy=(
            "Slightly off-centre framing. Shallow depth of field isolating the subject "
            "against a soft background. Negative space camera-right suggesting absence."
        ),
        camera_personality=(
            "Static on a tripod for dialogue. Slow push-in on key emotional beats. "
            "Observational — the camera watches rather than participates."
        ),
        reference_imagery=[
            "Roger Deakins — Prisoners (2013): natural window light, muted palette",
            "Bradford Young — Arrival (2016): shallow focus, atmospheric haze",
        ],
        costume_notes="Character in worn earth-toned layers — practical, lived-in.",
        production_design_notes=(
            "Cluttered desk with personal artefacts. Walls showing age. "
            "Window with half-drawn blinds filtering afternoon light."
        ),
        visual_motifs=[],
        aspect_ratio_override=None,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_inputs(
    inputs: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    canonical_script = None
    scene_index = None
    for payload in inputs.values():
        if isinstance(payload, dict) and "script_text" in payload:
            canonical_script = payload
        if isinstance(payload, dict) and "entries" in payload and "unique_characters" in payload:
            scene_index = payload
    if not canonical_script or not scene_index:
        raise ValueError(
            "look_and_feel_v1 requires canonical_script and scene_index inputs"
        )
    return canonical_script, scene_index


def _update_cost(total: dict[str, Any], call_cost: dict[str, Any]) -> None:
    total["input_tokens"] += call_cost.get("input_tokens", 0)
    total["output_tokens"] += call_cost.get("output_tokens", 0)
    total["estimated_cost_usd"] += call_cost.get("estimated_cost_usd", 0.0)
