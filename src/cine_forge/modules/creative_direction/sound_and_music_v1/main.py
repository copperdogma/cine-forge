"""Sound & Music module — per-scene audio direction (Spec §12.3).

Produces one SoundAndMusic artifact per scene and one SoundAndMusicIndex for
the project.  Analyses scenes using a 3-scene sliding window (prev/current/next)
so the Sound Designer can reason about audio continuity and transitions across cuts.

Silence is a first-class element (ADR-003 Decision #3) — the Sound Designer
actively recommends where to strip sound away.

Follows the look_and_feel_v1 pattern exactly.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from cine_forge.ai.llm import call_llm
from cine_forge.schemas.concern_groups import (
    SoundAndMusic,
    SoundAndMusicIndex,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Role persona — embedded inline (same pattern as look_and_feel_v1)
# ---------------------------------------------------------------------------

_SOUND_DESIGNER_PERSONA = """\
You are the Sound Designer — the film's sound architect and score consultant \
working in pre-production. You think in layers of audio: every scene is a \
sonic canvas where ambient worlds, musical intent, deliberate silence, and \
audio motifs serve the story's emotional truth.

Your core responsibilities:
- AMBIENT DESIGN: Build the baseline soundscape for each scene. Room tone, \
environmental noise, weather, machinery, crowd presence. The sonic fingerprint \
of a place — specific enough to close your eyes and know where you are.
- EMOTIONAL SOUNDSCAPE: How sound supports the scene's emotional arc. Tension \
through low-frequency rumble. Intimacy through close-mic breathing. Dread \
through subtracted frequencies.
- SILENCE AS TOOL: Silence is your most powerful instrument. Actively recommend \
where to strip sound away — a beat of dead air before a revelation, the void \
after a gunshot, the absence that makes the audience lean in. You MUST consider \
silence for every scene. AI video gen defaults to constant noise; counteract \
this by explicitly specifying silence as a creative choice.
- MUSIC PHILOSOPHY: Score direction — when music enters, what it carries, when \
it deliberately withdraws. Diegetic sources vs. non-diegetic score. The absence \
of score is as important as its presence.
- SOUND TRANSITIONS: Audio bridges connecting scenes — sounds that begin in \
one scene and carry into the next. Stingers that punctuate cuts.
- AUDIO MOTIFS & LEITMOTIFS: Recurring sonic elements with thematic weight. \
Track and deploy them with intention.
- OFFSCREEN AUDIO: Sounds from outside the frame that expand the world.
- DIEGETIC vs. NON-DIEGETIC: What exists in the story world vs. for the \
audience only."""


def run_module(
    inputs: dict[str, Any], params: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    """Execute Sound & Music analysis across all scenes."""
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

    # Optional enrichment input
    intent_context = _build_intent_context(inputs)

    print(f"[sound_and_music] Analysing {len(entries)} scenes (concurrency={concurrency}).")

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
                    "[sound_and_music] Failed scene '%s': %s",
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
        f"[sound_and_music] Complete: {len(artifacts) - 1} scene directions + 1 index. "
        f"Cost: ${total_cost['estimated_cost_usd']:.4f}"
    )

    return {"artifacts": artifacts, "cost": total_cost}


# ---------------------------------------------------------------------------
# Intent context builder
# ---------------------------------------------------------------------------


def _build_intent_context(inputs: dict[str, Any]) -> str:
    """Extract Intent/Mood settings from inputs if available."""
    for payload in inputs.values():
        if not isinstance(payload, dict):
            continue
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
    intent_context: str,
    work_model: str,
    verify_model: str,
    escalate_model: str,
    skip_qa: bool,
) -> tuple[SoundAndMusic, dict[str, Any]]:
    """Analyse a single scene and return the Sound & Music direction."""
    scene_id = entry.get("scene_id", "unknown")
    cost: dict[str, Any] = {"input_tokens": 0, "output_tokens": 0, "estimated_cost_usd": 0.0}
    models_used: set[str] = set()

    if work_model == "mock":
        return _mock_direction(scene_id), {
            "model": "mock", "input_tokens": 0, "output_tokens": 0, "estimated_cost_usd": 0.0,
        }

    prompt = _build_scene_prompt(entry, window, intent_context)
    direction, call_cost = call_llm(
        prompt=prompt,
        model=work_model,
        response_schema=SoundAndMusic,
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
            prompt_used="Sound & Music audio analysis",
            output_produced=direction.model_dump_json(),
            model=verify_model,
            criteria=["accuracy", "completeness", "sonic_specificity"],
        )
        _update_cost(cost, qa_cost)
        if qa_cost.get("model"):
            models_used.add(qa_cost["model"])

        if not qa_result.passed:
            escalate_prompt = _build_scene_prompt(
                entry, window, intent_context, feedback=qa_result.summary,
            )
            direction, esc_cost = call_llm(
                prompt=escalate_prompt,
                model=escalate_model,
                response_schema=SoundAndMusic,
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
    intent_context: str,
    feedback: str = "",
) -> str:
    """Construct the audio analysis prompt with 3-scene context and intent enrichment."""
    scene_id = entry.get("scene_id", "unknown")
    heading = entry.get("heading", "")
    scene_number = entry.get("scene_number", 0)
    characters = ", ".join(entry.get("characters_present", []))
    tone = entry.get("tone_mood", "unspecified")
    time_of_day = entry.get("time_of_day", "")
    location = entry.get("location", "")

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

    return f"""{_SOUND_DESIGNER_PERSONA}

Analyse the following scene and produce Sound & Music audio direction.

IMPORTANT: Consider the adjacent scenes for audio continuity across cuts.
A jarring sound shift between scenes should be intentional, not accidental.
Design audio transitions (bridges, stingers) that connect scene boundaries.
Reference the Intent/Mood settings as the director's global vision.

CRITICAL — SILENCE MANDATE: You MUST actively evaluate every scene for silence
opportunities. Silence is a first-class creative element, not the absence of
direction. If this scene would benefit from a moment of deliberate silence,
specify exactly where and why. If the scene genuinely needs continuous sound,
explain why silence would undermine it — do not simply leave silence_placement
empty without consideration.

Be specific and cinematic — not "ambient noise" but "distant harbour foghorns
layered under a close-mic dripping tap, low-frequency engine hum from the
building's ventilation, punctuated by a single seagull cry."
{feedback_block}{intent_block}
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
Return JSON matching the SoundAndMusic schema with these fields:
- scene_id: "{scene_id}"
- scope: "scene"
- ambient_environment: baseline soundscape for this location and time
- emotional_soundscape: how sound supports the scene's emotional arc
- silence_placement: WHERE and WHY to use deliberate silence (or why not)
- offscreen_audio_cues: list of sounds from outside the frame
- sound_driven_transitions: audio bridges, stingers connecting to adjacent scenes
- music_intent: score direction — tension, release, theme, absence of score
- diegetic_non_diegetic_notes: what sounds are in-world vs. audience-only
- audio_motifs: list of MotifAnnotation objects with thematic weight
"""


# ---------------------------------------------------------------------------
# Project-level index
# ---------------------------------------------------------------------------


def _build_index(
    entries: list[dict[str, Any]],
    directions: list[dict[str, Any]],
    work_model: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build the project-level Sound & Music index."""
    if work_model == "mock":
        index = SoundAndMusicIndex(
            total_scenes=len(entries),
            scenes_with_direction=len(directions),
            overall_sonic_language=(
                "Mock: Naturalistic room tones with selective "
                "heightening for emotional peaks. Silence used as "
                "punctuation between acts."
            ),
            dominant_soundscape=(
                "Mock: Urban industrial baseline — distant traffic, "
                "mechanical hum, wind through corridors. Interior "
                "scenes favour close-mic intimacy."
            ),
            score_arc=(
                "Mock: Minimal score in Act 1, building orchestral "
                "tension in Act 2, stark absence in Act 3 climax."
            ),
            key_audio_motifs=["Clock ticking", "Distant foghorn"],
            scenes_with_intentional_silence=[],
            sonic_consistency_concerns=[],
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
            f"ambient={d.get('ambient_environment', '?')}, "
            f"music={d.get('music_intent', '?')}, "
            f"silence={d.get('silence_placement', '?')}, "
            f"transitions={d.get('sound_driven_transitions', '?')}"
        )
    summary_text = "\n".join(scene_summaries)

    prompt = f"""{_SOUND_DESIGNER_PERSONA}

You have completed per-scene Sound & Music direction for {len(directions)} scenes.
Now produce a project-level index that summarises the overall sonic language
and identity of the film.

PER-SCENE DIRECTION SUMMARIES:
{summary_text}

Return JSON matching the SoundAndMusicIndex schema:
- total_scenes: {len(entries)}
- scenes_with_direction: {len(directions)}
- overall_sonic_language: high-level audio identity description for the entire film
- dominant_soundscape: project-wide ambient/atmospheric tendencies
- score_arc: how score/music evolves across the narrative arc
- key_audio_motifs: list of recurring sound elements carrying thematic weight
- scenes_with_intentional_silence: scenes where silence is deliberately specified
- sonic_consistency_concerns: potential audio continuity or style coherence issues
- confidence: your confidence in this aggregate analysis (0.0-1.0)
"""

    index, cost = call_llm(
        prompt=prompt,
        model=work_model,
        response_schema=SoundAndMusicIndex,
    )
    # Override counts with actual values
    index = index.model_copy(update={
        "total_scenes": len(entries),
        "scenes_with_direction": len(directions),
    })
    return _build_index_artifact(index, directions), cost


def _build_index_artifact(
    index: SoundAndMusicIndex, directions: list[dict[str, Any]]
) -> dict[str, Any]:
    return {
        "artifact_type": "sound_and_music_index",
        "entity_id": "project",
        "data": index.model_dump(mode="json"),
        "schema_name": "sound_and_music_index",
        "metadata": {
            "intent": "Summarise Sound & Music direction across all scenes",
            "rationale": (
                f"Aggregate audio analysis of "
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


def _build_artifact(entry: dict[str, Any], direction: SoundAndMusic) -> dict[str, Any]:
    scene_id = entry.get("scene_id", "unknown")
    return {
        "artifact_type": "sound_and_music",
        "entity_id": scene_id,
        "data": direction.model_dump(mode="json"),
        "schema_name": "sound_and_music",
        "metadata": {
            "intent": f"Sound & Music direction for {entry.get('heading', scene_id)}",
            "rationale": (
                "Per-scene audio analysis: ambient environment, emotional "
                "soundscape, silence placement, music intent, and audio motifs."
            ),
            "confidence": 0.85,
            "source": "ai",
            "annotations": {
                "ambient": direction.ambient_environment,
                "music_intent": direction.music_intent,
                "silence": direction.silence_placement,
            },
        },
    }


# ---------------------------------------------------------------------------
# Mock support
# ---------------------------------------------------------------------------


def _mock_direction(scene_id: str) -> SoundAndMusic:
    return SoundAndMusic(
        scope="scene",
        scene_id=scene_id,
        ambient_environment=(
            "Low-frequency ventilation hum from the building's HVAC. Distant traffic "
            "filtered through closed windows — muted horns, tyre hiss on wet asphalt. "
            "Close-mic: fluorescent light buzz overhead, intermittent."
        ),
        emotional_soundscape=(
            "Tension built through subtractive sound design — stripping layers as "
            "the conversation intensifies. The room tone narrows to a tight, "
            "claustrophobic frequency band. Breathing becomes audible."
        ),
        silence_placement=(
            "Dead silence for two beats after the key revelation at mid-scene. "
            "All ambient drops out — no room tone, no traffic, no hum. The void "
            "forces the audience to hold their breath with the character before "
            "the world rushes back in."
        ),
        offscreen_audio_cues=[
            "A door closing somewhere down the corridor — someone leaving",
            "Distant siren rising then fading — the outside world continuing without them",
        ],
        sound_driven_transitions=(
            "The ventilation hum from this scene carries over the cut into the "
            "next scene's exterior, where it transforms into wind — an audio "
            "bridge linking interior confinement to exterior exposure."
        ),
        music_intent=(
            "No score. This scene lives in pure diegetic sound. The absence of "
            "music makes the silence beat hit harder. Score re-enters only in "
            "the following scene as a single sustained cello note."
        ),
        diegetic_non_diegetic_notes=(
            "Everything is diegetic — the hum, the traffic, the breathing. "
            "No non-diegetic elements. The raw, unmediated soundscape puts "
            "the audience inside the room with the characters."
        ),
        audio_motifs=[],
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
            "sound_and_music_v1 requires canonical_script and scene_index inputs"
        )
    return canonical_script, scene_index


def _update_cost(total: dict[str, Any], call_cost: dict[str, Any]) -> None:
    total["input_tokens"] += call_cost.get("input_tokens", 0)
    total["output_tokens"] += call_cost.get("output_tokens", 0)
    total["estimated_cost_usd"] += call_cost.get("estimated_cost_usd", 0.0)
