"""Prompt-context helpers for render adapter scene generation."""

from __future__ import annotations

from typing import Any

from cine_forge.modules.generation.render_adapter_v1.context_sections import (
    _character_state_block,
    _creative_brief_block,
    _injected_assets_block,
    _keyframe_block,
    _location_state_block,
    _look_and_feel_block,
    _performance_block,
    _rhythm_block,
    _sound_block,
)
from cine_forge.modules.generation.render_adapter_v1.dialogue_contracts import (
    _dialogue_timing_contract,
    _exact_dialogue_lines_for_shot,
)
from cine_forge.modules.generation.render_adapter_v1.prompting import (
    known_prompt_categories,
    prompt_sources_from_sections,
    section_metadata,
    section_title,
)
from cine_forge.modules.generation.render_adapter_v1.render_units import (
    remove_dialogue_quotes,
    render_clip_dialogue_lines,
)
from cine_forge.schemas import (
    RenderClip,
    RenderClipPlan,
    RenderCompletenessCheck,
    RenderPromptSection,
    RenderResolvedInput,
    Scene,
    ShotPlan,
)


def _scene_block(
    *,
    scene: Scene,
    plan: ShotPlan,
    render_clip: RenderClip | None = None,
) -> str:
    if render_clip is not None:
        clip_lines = [
            f"Scene {scene.scene_number}: {scene.heading}",
            (
                f"Render clip: {render_clip.clip_id} "
                f"({render_clip.start_time_seconds:.1f}-{render_clip.end_time_seconds:.1f}s, "
                f"target {render_clip.target_duration_seconds:.1f}s)"
            ),
            f"Location: {scene.location} ({scene.int_ext}, {scene.time_of_day})",
            f"Tone: {scene.tone_mood}",
            f"Characters present: {', '.join(scene.characters_present) or 'none'}",
        ]
        if render_clip.source_shot_ids:
            clip_lines.append("Source shots: " + ", ".join(render_clip.source_shot_ids))
        if render_clip.fallback_beat_ids:
            clip_lines.append("Fallback beats: " + ", ".join(render_clip.fallback_beat_ids))
        if render_clip.action_beats:
            clip_lines.append("Clip action beats:")
            clip_lines.extend(
                f"- {remove_dialogue_quotes(beat, render_clip.dialogue_lines)}"
                for beat in render_clip.action_beats
            )
        clip_dialogue = render_clip_dialogue_lines(render_clip)
        if clip_dialogue:
            clip_lines.append("Clip exact dialogue lines:")
            clip_lines.extend(f"- {line}" for line in clip_dialogue)
        if render_clip.continuity_start_notes or render_clip.continuity_end_notes:
            clip_lines.append("Clip continuity notes:")
            clip_lines.extend(f"- start: {note}" for note in render_clip.continuity_start_notes)
            clip_lines.extend(f"- end: {note}" for note in render_clip.continuity_end_notes)
        return "\n".join(clip_lines)

    excerpt_lines: list[str] = []
    for element in scene.elements[:6]:
        excerpt_lines.append(f"- {element.element_type}: {element.content}")
    if not excerpt_lines:
        excerpt_lines.append("- No scene excerpt available.")
    return (
        f"Scene {scene.scene_number}: {scene.heading}\n"
        f"Location: {scene.location} ({scene.int_ext}, {scene.time_of_day})\n"
        f"Tone: {scene.tone_mood}\n"
        f"Characters present: {', '.join(scene.characters_present) or 'none'}\n"
        f"Estimated shot-plan duration: {plan.total_estimated_duration_seconds:.1f}s\n"
        "Screenplay excerpt:\n" + "\n".join(excerpt_lines)
    )


def _context_blocks(
    *,
    scene: Scene,
    plan: ShotPlan,
    source_maps: dict[str, Any],
    resolved_inputs: list[RenderResolvedInput],
    render_clip: RenderClip | None = None,
) -> dict[str, str]:
    return {
        "shot_definition": _shot_definition_block(plan),
        "render_clip_plan": _render_clip_plan_block(
            source_maps["render_clip_plan"].get(plan.scene_id),
            render_clip=render_clip,
        ),
        "creative_brief": _creative_brief_block(source_maps["creative_brief"]),
        "look_and_feel": _look_and_feel_block(source_maps["look_and_feel"].get(plan.scene_id)),
        "sound_and_music": _sound_block(
            source_maps["sound_and_music"].get(plan.scene_id),
            resolved_inputs=resolved_inputs,
        ),
        "character_and_performance": _performance_block(
            source_maps["character_and_performance"].get(plan.scene_id, []),
            plan=plan,
        ),
        "rhythm_and_flow": _rhythm_block(source_maps["rhythm_and_flow"].get(plan.scene_id)),
        "character_bible_state": _character_state_block(
            scene=scene,
            character_bibles=source_maps["character_bible"],
        ),
        "location_bible_state": _location_state_block(
            scene=scene,
            location_bibles=source_maps["location_bible"],
        ),
        "keyframes": _keyframe_block(resolved_inputs),
        "injected_assets": _injected_assets_block(resolved_inputs),
    }


def _shot_definition_block(plan: ShotPlan) -> str:
    lines = [
        f"Coverage approach: {plan.coverage_strategy.coverage_approach}",
        f"Rhythm intent: {plan.coverage_strategy.rhythm_and_flow_intent}",
        f"Visual intent: {plan.coverage_strategy.look_and_feel_intent}",
        f"Sound intent: {plan.coverage_strategy.sound_and_music_intent}",
        f"Performance notes: {plan.coverage_strategy.character_and_performance_notes}",
    ]
    for shot in plan.shots:
        shot_parts = [
            f"{shot.shot_id}",
            shot.shot_size,
            shot.camera_angle,
            shot.camera_movement,
            f"lens={shot.lens_focal_length}",
            f"duration={shot.duration_estimate_seconds:.1f}s",
            f"blocking={shot.blocking}",
            f"action={shot.action_description}",
            f"edit_intent={shot.edit_intent}",
        ]
        dialogue = _exact_dialogue_lines_for_shot(shot)
        if dialogue:
            shot_parts.append(
                f"dialogue_lines={len(dialogue)} exact line(s); see dialogue timing contract"
            )
        lines.append(" | ".join(shot_parts))
    dialogue_contract = _dialogue_timing_contract(
        plan,
        duration_seconds=plan.total_estimated_duration_seconds,
    )
    if dialogue_contract:
        lines.extend(["", dialogue_contract])
    return "\n".join(lines)


def _render_clip_plan_block(
    plan: RenderClipPlan | None,
    *,
    render_clip: RenderClip | None = None,
) -> str:
    if plan is None:
        return (
            "No render_clip_plan artifact was provided. The adapter is using the "
            "scene-level shot plan only, so duration compression risk is unknown."
        )
    lines = [
        (
            "Scene target dramatic duration: "
            f"{plan.target_dramatic_duration_seconds:.1f}s"
        ),
        f"Engine max clip duration: {plan.engine_max_clip_duration_seconds:.1f}s",
        f"Provenance: {plan.provenance_mode}; confidence={plan.confidence:.2f}",
        f"Duration rationale: {plan.duration_rationale}",
    ]
    if plan.missing_upstream_categories:
        lines.append(
            "Missing upstream categories: "
            + ", ".join(plan.missing_upstream_categories)
        )
    if render_clip is not None:
        lines.append("Render path: this prompt is for one planned render clip only.")
    elif len(plan.clips) > 1:
        lines.append(
            "Render path: this scene-level prompt is not expanding each planned "
            "clip; preserve this multi-clip pacing in the prompt and disclose "
            "compression risk."
        )
    clips = [render_clip] if render_clip is not None else list(plan.clips)
    for clip in clips:
        pieces = [
            clip.clip_id,
            f"{clip.start_time_seconds:.1f}-{clip.end_time_seconds:.1f}s",
            f"target={clip.target_duration_seconds:.1f}s",
        ]
        if clip.source_shot_ids:
            pieces.append(f"shots={', '.join(clip.source_shot_ids)}")
        if clip.fallback_beat_ids:
            pieces.append(f"beats={', '.join(clip.fallback_beat_ids)}")
        if clip.dialogue_lines:
            pieces.append(f"dialogue_lines={len(clip.dialogue_lines)}")
        if clip.action_beats:
            action_beats = [
                remove_dialogue_quotes(beat, clip.dialogue_lines)
                for beat in clip.action_beats[:2]
            ]
            pieces.append(f"action={'; '.join(action_beats)}")
        pieces.append(f"rationale={clip.rationale}")
        lines.append(" | ".join(pieces))
    return "\n".join(lines)


def _render_clip_plan_notes(
    plan: RenderClipPlan | None,
    duration_seconds: float,
    *,
    render_clip: RenderClip | None = None,
) -> list[str]:
    if plan is None:
        return [
            "No render_clip_plan artifact was available; render prompt compilation "
            "could not verify scene-duration compression risk."
        ]
    if len(plan.clips) <= 1:
        return []
    if render_clip is not None:
        return [
            (
                f"Rendering planned clip {render_clip.clip_id} from a "
                f"{len(plan.clips)}-clip scene render plan."
            )
        ]
    return [
        (
            "Current scene-level render compresses a "
            f"{plan.target_dramatic_duration_seconds:g}s render-clip plan with "
            f"{len(plan.clips)} planned clips into one {duration_seconds:g}s provider clip; "
            "Story 194 owns multi-clip execution."
        )
    ]


def _finalize_prompt_sections(
    *,
    prompt_draft: Any,
    required_categories: list[str],
    context_blocks: dict[str, str],
    resolved_inputs: list[RenderResolvedInput],
    extra_source_artifact_types: list[str],
    notes: list[str],
) -> tuple[list[RenderPromptSection], RenderCompletenessCheck, list[str]]:
    sections: list[RenderPromptSection] = []
    covered: set[str] = set()
    required = {
        category.strip()
        for category in required_categories
        if isinstance(category, str) and category.strip()
    }
    for section in prompt_draft.sections:
        role, artifact_types = section_metadata(section.section_id)
        source_artifact_types = list(dict.fromkeys(section.source_artifact_types or artifact_types))
        sections.append(
            RenderPromptSection(
                section_id=section.section_id,
                title=section.title,
                body=section.body,
                source_role_id=section.source_role_id or role,
                source_artifact_types=source_artifact_types,
            )
        )
        covered.add(section.section_id)
    covered.update(item for item in prompt_draft.covered_categories if isinstance(item, str))
    reported_missing = {
        item.strip()
        for item in prompt_draft.missing_inputs
        if isinstance(item, str) and item.strip()
    }
    known_categories = known_prompt_categories()
    synthesized_categories: list[str] = []
    for category in sorted(required - covered):
        content = context_blocks.get(category, "").strip()
        if not content or category not in known_categories:
            continue
        role, artifact_types = section_metadata(category)
        sections.append(
            RenderPromptSection(
                section_id=category,
                title=section_title(category),
                body=content,
                source_role_id=role,
                source_artifact_types=artifact_types,
            )
        )
        covered.add(category)
        synthesized_categories.append(category)

    blocking_missing = {category for category in required if category not in covered}
    advisory_missing: set[str] = set()
    for item in reported_missing:
        if item not in known_categories:
            blocking_missing.add(item)
            continue
        if item in synthesized_categories:
            continue
        if item in required:
            blocking_missing.add(item)
            continue
        advisory_missing.add(item)
    missing = blocking_missing | advisory_missing
    prompt_sources = prompt_sources_from_sections(sections, resolved_inputs)
    for artifact_type in extra_source_artifact_types:
        if artifact_type not in prompt_sources:
            prompt_sources.append(artifact_type)
    synthesis_notes = list(notes)
    if synthesized_categories:
        synthesis_notes.append(
            "Adapter synthesized fallback sections for: "
            + ", ".join(synthesized_categories)
            + "."
        )
    completeness = RenderCompletenessCheck(
        included_categories=sorted(covered),
        missing_categories=sorted(missing),
        blocking_missing_categories=sorted(blocking_missing),
        advisory_missing_categories=sorted(advisory_missing),
        notes=[*prompt_draft.operator_notes, *synthesis_notes],
    )
    return sections, completeness, prompt_sources
