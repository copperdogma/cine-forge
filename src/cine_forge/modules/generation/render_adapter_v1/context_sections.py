"""Prompt context section builders for render adapter generation."""

from __future__ import annotations

from typing import Any

from cine_forge.modules.generation.render_adapter_v1.support import (
    AUDIO_KINDS as _AUDIO_KINDS,
)
from cine_forge.modules.generation.render_adapter_v1.support import (
    slugify as _slugify,
)
from cine_forge.schemas import (
    CharacterAndPerformance,
    CharacterBible,
    LocationBible,
    LookAndFeel,
    RenderResolvedInput,
    RhythmAndFlow,
    Scene,
    ShotPlan,
    SoundAndMusic,
)


def _creative_brief_block(creative_brief: Any) -> str:
    if creative_brief is None:
        return ""
    lines = getattr(creative_brief, "summary_lines", None)
    if not isinstance(lines, list):
        return ""
    return "\n".join(line for line in lines if isinstance(line, str) and line.strip())


def _look_and_feel_block(look_and_feel: LookAndFeel | None) -> str:
    if look_and_feel is None:
        return ""
    lines = _nonempty_lines(
        [
            look_and_feel.lighting_concept,
            look_and_feel.color_palette,
            look_and_feel.composition_philosophy,
            look_and_feel.camera_personality,
            look_and_feel.costume_notes,
            look_and_feel.production_design_notes,
        ]
    )
    if look_and_feel.reference_imagery:
        lines.append(f"Reference imagery: {', '.join(look_and_feel.reference_imagery)}")
    return "\n".join(lines)


def _sound_block(
    sound_and_music: SoundAndMusic | None,
    *,
    resolved_inputs: list[RenderResolvedInput],
) -> str:
    lines: list[str] = []
    if sound_and_music is not None:
        lines.extend(
            _nonempty_lines(
                [
                    sound_and_music.ambient_environment,
                    sound_and_music.emotional_soundscape,
                    sound_and_music.silence_placement,
                    sound_and_music.sound_driven_transitions,
                    sound_and_music.music_intent,
                    sound_and_music.diegetic_non_diegetic_notes,
                ]
            )
        )
        if sound_and_music.offscreen_audio_cues:
            lines.append(f"Offscreen cues: {', '.join(sound_and_music.offscreen_audio_cues)}")
        if sound_and_music.reference_audio_assets:
            lines.append(
                f"Reference audio assets: {', '.join(sound_and_music.reference_audio_assets)}"
            )
    audio_inputs = [item for item in resolved_inputs if item.kind in _AUDIO_KINDS]
    if audio_inputs:
        labels = ", ".join(
            f"{item.label} ({item.lock_status or 'unlocked'})" for item in audio_inputs
        )
        lines.append(f"Injected audio context: {labels}")
    return "\n".join(lines)


def _performance_block(
    performance_entries: list[CharacterAndPerformance],
    *,
    plan: ShotPlan,
) -> str:
    lines: list[str] = []
    for entry in performance_entries:
        lines.append(
            " | ".join(
                _nonempty_lines(
                    [
                        entry.character_id,
                        entry.emotional_state_entering,
                        entry.emotional_arc,
                        entry.motivation,
                        entry.subtext,
                        entry.physical_notes,
                        entry.relationship_dynamics,
                        entry.blocking_notes,
                    ]
                )
            )
        )
    if lines:
        return "\n".join(lines)
    fallback = {character for shot in plan.shots for character in shot.characters_in_frame}
    if not fallback:
        return ""
    return (
        "No formal scene character/performance artifact exists. Use shot-planning behavior and "
        "blocking as fallback for: " + ", ".join(sorted(fallback))
    )


def _rhythm_block(rhythm_and_flow: RhythmAndFlow | None) -> str:
    if rhythm_and_flow is None:
        return ""
    lines = _nonempty_lines(
        [
            rhythm_and_flow.scene_function,
            rhythm_and_flow.pacing_intent,
            rhythm_and_flow.transition_in,
            rhythm_and_flow.transition_out,
            rhythm_and_flow.coverage_priority,
            rhythm_and_flow.camera_movement_dynamics,
            rhythm_and_flow.parallel_editing_notes,
            rhythm_and_flow.act_level_notes,
        ]
    )
    if rhythm_and_flow.montage_candidates:
        lines.append(f"Montage candidates: {', '.join(rhythm_and_flow.montage_candidates)}")
    return "\n".join(lines)


def _character_state_block(
    *,
    scene: Scene,
    character_bibles: dict[str, CharacterBible],
) -> str:
    lines: list[str] = []
    for character_id in scene.characters_present_ids:
        bible = character_bibles.get(_slugify(character_id))
        if bible is None:
            continue
        traits = ", ".join(f"{item.trait}={item.value}" for item in bible.inferred_traits[:4])
        summary = f"{bible.name}: {bible.description}"
        if traits:
            summary = f"{summary} | inferred_traits: {traits}"
        lines.append(summary)
    return "\n".join(lines)


def _location_state_block(
    *,
    scene: Scene,
    location_bibles: dict[str, LocationBible],
) -> str:
    bible = location_bibles.get(_slugify(scene.location))
    if bible is None:
        return ""
    parts = [bible.name, bible.description]
    if bible.physical_traits:
        parts.append(f"physical_traits: {', '.join(bible.physical_traits[:6])}")
    parts.append(f"narrative_significance: {bible.narrative_significance}")
    return " | ".join(parts)


def _keyframe_block(resolved_inputs: list[RenderResolvedInput]) -> str:
    lines = [
        f"{item.label} | used_as={item.used_as} | notes={item.notes or 'none'}"
        for item in resolved_inputs
        if item.kind == "keyframe"
    ]
    return "\n".join(lines)


def _injected_assets_block(resolved_inputs: list[RenderResolvedInput]) -> str:
    lines = [
        f"{item.label} | kind={item.kind} | used_as={item.used_as} | "
        f"lock={item.lock_status or 'unlocked'}"
        for item in resolved_inputs
        if item.kind != "keyframe"
    ]
    return "\n".join(lines)


def _nonempty_lines(values: list[str | None]) -> list[str]:
    return [value.strip() for value in values if isinstance(value, str) and value.strip()]
