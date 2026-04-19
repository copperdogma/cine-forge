"""Low-fidelity AI previz prompt contracts for benchmarked candidate lanes."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from pydantic import BaseModel, Field

from cine_forge.schemas import (
    EnginePack,
    PrevizConsistencyStrategy,
    PrevizPromptContract,
    PrevizPromptProfile,
    PrevizStyleProfile,
    RenderCompletenessCheck,
    RenderPromptSection,
    RenderResolvedInput,
    Scene,
    ShotPlan,
)

_CAMERA_TAG_LINES = {
    "locked_two_shot": "Use a locked two-shot that keeps both subjects legible.",
    "wide_master": "Frame the space as a wide master so subject and prop placement stay obvious.",
    "profile_closeup": "Use a profile-oriented close-up without losing spatial readability.",
    "slow_push_in": (
        "Move with a slow push-in that clarifies emotional pressure rather than spectacle."
    ),
    "slow_pull_back": "Use a slow pull-back that reveals spacing and staging.",
    "lateral_track": "Track laterally so movement across the set stays easy to read.",
    "overhead_reveal": "Reveal the space from above without adding decorative flourishes.",
    "whip_pan": "Use a controlled whip pan only if it preserves the key blocking beat.",
    "cross_cut": "Favor clean cross-cut readability over stylized editing tricks.",
    "static": "Hold the camera steady unless motion is required by the shot.",
}
_MOTION_TAG_LINES = {
    "stillness": "Keep body movement minimal and readable.",
    "measured": "Keep movement measured and intentional.",
    "fast_lateral": "Prioritize directional travel over animation detail.",
    "escalating": "Let motion intensity rise only as much as the blocking requires.",
    "slow_drift": "Allow a gentle drift if it clarifies staging.",
    "abrupt_cut": "Keep cut-style energy readable rather than flashy.",
}
_DEFAULT_NEGATIVE_TERMS = [
    "photorealistic skin detail",
    "ornate textures",
    "beauty-lighting polish",
    "hyper-detailed props",
    "decorative camera flourishes",
    "bokeh glamour shots",
    "final-render finish",
]
_HOUSE_STYLE_PROFILE = PrevizStyleProfile(
    profile_id="cineforge_low_fidelity_previz_v1",
    title="CineForge Low-Fidelity Previz",
    summary=(
        "A production-readable schematic animation language for camera, blocking, "
        "motion, and prop/location staging review."
    ),
    identity_strategy=(
        "Keep characters distinct through silhouette, wardrobe color blocking, and "
        "minimal on-costume labels only when identity would otherwise be ambiguous."
    ),
    location_strategy=(
        "Render locations and props only to the level needed for staging, entrances, "
        "exits, and scene geography."
    ),
    motion_priority=(
        "Prioritize camera path, subject blocking, and movement arcs over surface detail."
    ),
    detail_suppression=[
        "photoreal facial features",
        "complex material rendering",
        "ambient decoration not needed for staging",
        "shot-beautification effects",
    ],
    prompt_guidance=[
        "Use simplified, flat-shaded schematic animation rather than polished final imagery.",
        "Keep silhouettes clean and backgrounds restrained.",
        "Preserve continuity anchors such as key props and their positions.",
        "Treat audio as secondary to readable camera and blocking.",
    ],
)


class PrevizShotBrief(BaseModel):
    """Minimal shot brief used to compile a low-detail previz prompt."""

    clip_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    summary_reference: str = Field(min_length=1)
    transcript: str | None = None
    audio_description: str | None = None
    tone_tags: list[str] = Field(default_factory=list)
    emotion_tags: list[str] = Field(default_factory=list)
    color_tags: list[str] = Field(default_factory=list)
    camera_tags: list[str] = Field(default_factory=list)
    motion_tags: list[str] = Field(default_factory=list)
    continuity_notes: list[str] = Field(default_factory=list)
    clip_tags: list[str] = Field(default_factory=list)
    character_labels: list[str] = Field(default_factory=list)


def compile_low_fidelity_previz_prompt(
    *,
    brief: PrevizShotBrief,
    engine_pack: EnginePack,
    consistency_strategy: PrevizConsistencyStrategy = "prompt_only",
    prompt_profile: PrevizPromptProfile = "standard",
) -> PrevizPromptContract:
    """Compile a deterministic low-fidelity previz prompt for one engine pack."""
    character_line = (
        ", ".join(brief.character_labels) if brief.character_labels else "Unnamed subject"
    )
    tone_line = ", ".join(brief.tone_tags) if brief.tone_tags else "neutral"
    color_line = ", ".join(brief.color_tags) if brief.color_tags else "restrained"
    camera_lines = _ordered_lines(brief.camera_tags, _CAMERA_TAG_LINES)
    motion_lines = _ordered_lines(brief.motion_tags, _MOTION_TAG_LINES)
    continuity_line = (
        "; ".join(brief.continuity_notes)
        if brief.continuity_notes
        else "Preserve the core prop and body positions from start to finish."
    )
    audio_line = (
        brief.audio_description
        if brief.audio_description
        else "Keep audio minimal and subordinate to the visual staging read."
    )
    transcript_line = brief.transcript or "No spoken line needs explicit lip-sync detail."
    engine_line = engine_pack.preferred_prompt_style.strip()
    prompt_lines = _prompt_lines_for_profile(
        prompt_profile=prompt_profile,
        character_line=character_line,
        tone_line=tone_line,
        color_line=color_line,
        camera_lines=camera_lines,
        motion_lines=motion_lines,
        continuity_line=continuity_line,
        audio_line=audio_line,
        transcript_line=transcript_line,
        shot_brief=brief.summary_reference,
        engine_line=engine_line,
    )
    prompt_text = _fit_prompt_lines_to_budget(
        prompt_lines,
        max_chars=_request_int(engine_pack, "max_prompt_chars"),
    )

    notes = [
        f"consistency_strategy={consistency_strategy}",
        f"prompt_profile={prompt_profile}",
        f"engine_pack_id={engine_pack.pack_id}",
        f"target_model={engine_pack.target_model}",
    ]
    if consistency_strategy == "prompt_only":
        notes.append(
            "Prompt-only identity/style consistency requested; no reference images assumed."
        )

    return PrevizPromptContract(
        target_engine_pack_id=engine_pack.pack_id,
        consistency_strategy=consistency_strategy,
        prompt_profile=prompt_profile,
        style_profile=_HOUSE_STYLE_PROFILE,
        prompt_text=prompt_text,
        negative_prompt_terms=list(_DEFAULT_NEGATIVE_TERMS),
        notes=notes,
    )


def shot_brief_from_target(
    *,
    target: dict[str, Any],
    meta: dict[str, Any],
    character_labels: Sequence[str] | None = None,
) -> PrevizShotBrief:
    """Build a benchmark previz shot brief from target/meta records."""
    return PrevizShotBrief(
        clip_id=str(target["clip_id"]),
        title=str(target["title"]),
        summary_reference=str(target["summary_reference"]),
        transcript=_string_or_none(target.get("transcript"))
        or _string_or_none(meta.get("transcript")),
        audio_description=_string_or_none(target.get("audio_description"))
        or _string_or_none(meta.get("audio_description")),
        tone_tags=_string_list(target.get("tone_tags")),
        emotion_tags=_string_list(target.get("emotion_tags")),
        color_tags=_string_list(target.get("color_tags")),
        camera_tags=_string_list(target.get("camera_tags")),
        motion_tags=_string_list(target.get("motion_tags")),
        continuity_notes=_string_list(target.get("continuity_notes")),
        clip_tags=_string_list(target.get("clip_tags")),
        character_labels=list(character_labels or []),
    )


def low_fidelity_previz_profile() -> PrevizStyleProfile:
    """Return the shared low-fidelity previz style profile."""
    return _HOUSE_STYLE_PROFILE.model_copy(deep=True)


def compile_scene_previz_prompt(
    *,
    scene: Scene,
    plan: ShotPlan,
    source_maps: dict[str, Any],
    resolved_inputs: Sequence[RenderResolvedInput],
    engine_pack: EnginePack,
    consistency_strategy: PrevizConsistencyStrategy = "prompt_only",
    prompt_profile: PrevizPromptProfile = "standard",
) -> tuple[PrevizPromptContract, list[RenderPromptSection], RenderCompletenessCheck, list[str]]:
    """Compile a deterministic low-fidelity previz prompt from scene artifacts."""
    primary_shot = plan.shots[0] if plan.shots else None
    transcript_lines = _collect_dialogue_lines(plan)
    sound_and_music = source_maps.get("sound_and_music", {}).get(plan.scene_id)
    look_and_feel = source_maps.get("look_and_feel", {}).get(plan.scene_id)
    rhythm_and_flow = source_maps.get("rhythm_and_flow", {}).get(plan.scene_id)
    intent_mood = source_maps.get("intent_mood")

    target = {
        "clip_id": plan.scene_id,
        "title": plan.scene_heading,
        "summary_reference": _summary_reference(
            scene=scene,
            plan=plan,
            look_and_feel=look_and_feel,
            rhythm_and_flow=rhythm_and_flow,
        ),
        "transcript": " ".join(transcript_lines) if transcript_lines else None,
        "audio_description": _audio_description(sound_and_music),
        "tone_tags": _tone_tags(intent_mood, rhythm_and_flow),
        "color_tags": _color_tags(look_and_feel),
        "camera_tags": _camera_tags(primary_shot),
        "motion_tags": _motion_tags(primary_shot, rhythm_and_flow),
        "continuity_notes": _continuity_notes(
            scene=scene,
            primary_shot=primary_shot,
            resolved_inputs=resolved_inputs,
        ),
        "clip_tags": _clip_tags(scene=scene, plan=plan),
    }
    brief = shot_brief_from_target(
        target=target,
        meta={},
        character_labels=_character_labels(scene=scene, primary_shot=primary_shot),
    )
    contract = compile_low_fidelity_previz_prompt(
        brief=brief,
        engine_pack=engine_pack,
        consistency_strategy=consistency_strategy,
        prompt_profile=prompt_profile,
    )
    sections = [
        RenderPromptSection(
            section_id="shot_brief",
            title="Shot Brief",
            body=target["summary_reference"],
            source_artifact_types=["scene", "shot_plan"],
        ),
        RenderPromptSection(
            section_id="house_style",
            title="Previz House Style",
            body=contract.style_profile.summary,
            source_artifact_types=["shot_plan"],
        ),
    ]
    if look_and_feel is not None:
        sections.append(
            RenderPromptSection(
                section_id="look_and_feel",
                title="Look & Feel",
                body=_first_non_empty(
                    getattr(look_and_feel, "lighting_concept", None),
                    getattr(look_and_feel, "composition_philosophy", None),
                    getattr(look_and_feel, "camera_personality", None),
                    getattr(look_and_feel, "production_design_notes", None),
                )
                or "Keep the visual treatment schematic and staging-first.",
                source_artifact_types=["look_and_feel"],
            )
        )
    if rhythm_and_flow is not None:
        sections.append(
            RenderPromptSection(
                section_id="rhythm_and_flow",
                title="Rhythm & Flow",
                body=_first_non_empty(
                    getattr(rhythm_and_flow, "pacing_intent", None),
                    getattr(rhythm_and_flow, "coverage_priority", None),
                    getattr(rhythm_and_flow, "camera_movement_dynamics", None),
                )
                or "Keep the pace readable and focused on blocking beats.",
                source_artifact_types=["rhythm_and_flow"],
            )
        )
    if sound_and_music is not None:
        sections.append(
            RenderPromptSection(
                section_id="sound_and_music",
                title="Sound & Music",
                body=_audio_description(sound_and_music),
                source_artifact_types=["sound_and_music"],
            )
        )
    if transcript_lines:
        sections.append(
            RenderPromptSection(
                section_id="dialogue",
                title="Dialogue Cue",
                body=" ".join(transcript_lines),
                source_artifact_types=["shot_plan"],
            )
        )
    if resolved_inputs:
        sections.append(
            RenderPromptSection(
                section_id="resolved_inputs",
                title="Resolved Inputs",
                body=", ".join(input_item.label for input_item in resolved_inputs[:6]),
                source_artifact_types=sorted(
                    {
                        input_item.source_ref.artifact_type
                        for input_item in resolved_inputs
                        if input_item.source_ref
                    }
                ),
            )
        )
    prompt_sources = sorted(
        {
            source
            for section in sections
            for source in section.source_artifact_types
            if source
        }
    )
    completeness = RenderCompletenessCheck(
        included_categories=[
            "shot_definition",
            "blocking_review",
            "house_style",
            "camera_motion",
            "staging_readability",
        ],
        missing_categories=[],
        notes=[
            f"consistency_strategy={contract.consistency_strategy}",
            f"prompt_profile={contract.prompt_profile}",
            f"style_profile={contract.style_profile.profile_id}",
        ],
    )
    return contract, sections, completeness, prompt_sources


def _prompt_lines_for_profile(
    *,
    prompt_profile: PrevizPromptProfile,
    character_line: str,
    tone_line: str,
    color_line: str,
    camera_lines: list[str],
    motion_lines: list[str],
    continuity_line: str,
    audio_line: str,
    transcript_line: str,
    shot_brief: str,
    engine_line: str,
) -> list[str]:
    if prompt_profile == "compact":
        return [
            "Create a low-fidelity previs clip in CineForge's shared house style.",
            (
                "This is previs, not a final render. Prioritize readable blocking, camera path, "
                "motion, subject positions, prop positions, and scene geography."
            ),
            (
                "Visual treatment: simplified flat-shaded schematic animation, clear silhouettes, "
                "restrained texture, non-photoreal finish."
            ),
            (
                f"Characters: {character_line}. Distinguish them by silhouette and wardrobe "
                "color; label only if needed."
            ),
            f"Shot brief: {shot_brief}",
            f"Tone and color: {tone_line}; {color_line}.",
            f"Camera: {_join_unique_lines(camera_lines)}",
            f"Motion: {_join_unique_lines(motion_lines)}",
            f"Continuity: {continuity_line}",
            f"Audio: {audio_line}",
            f"Dialogue: {transcript_line}",
            (
                "Avoid photoreal polish, ornate texture, decorative camera flourishes, and "
                "final-render finish."
            ),
            f"Engine guidance: {engine_line}",
        ]

    return [
        "Create a low-fidelity previs clip in CineForge's shared house style.",
        (
            "This is previs, not a final render. Make camera placement, blocking, motion, "
            "subject positions, prop positions, and location readability obvious at a glance."
        ),
        f"House style: {_HOUSE_STYLE_PROFILE.summary}",
        (
            "Visual treatment: simplified flat-shaded animation, clear silhouettes, "
            "restrained texture, non-photoreal finish."
        ),
        f"Characters to keep distinct: {character_line}.",
        (
            "Identity handling: keep characters distinguishable through silhouette and wardrobe "
            "color coding; add minimal chest labels only if identity would otherwise be unclear."
        ),
        f"Shot brief: {shot_brief}",
        f"Tone cue: {tone_line}.",
        f"Color cue: {color_line}.",
        *camera_lines,
        *motion_lines,
        f"Continuity anchor: {continuity_line}",
        f"Audio cue: {audio_line}",
        f"Dialogue cue: {transcript_line}",
        (
            "Suppress distracting detail: no photoreal surfaces, no elaborate set dressing, "
            "no beauty pass, no cinematic prestige finish."
        ),
        (
            "Keep the same simplified house style that would read consistently across "
            "other previz clips."
        ),
        f"Engine guidance: {engine_line}",
    ]


def _ordered_lines(tags: Sequence[str], mapping: dict[str, str]) -> list[str]:
    lines: list[str] = []
    for tag in tags:
        line = mapping.get(tag)
        if line and line not in lines:
            lines.append(line)
    return lines or ["Keep the camera and motion readable without extra flourish."]


def _join_unique_lines(lines: Sequence[str]) -> str:
    unique = [line.strip().rstrip(".") for line in lines if isinstance(line, str) and line.strip()]
    if not unique:
        return "Keep the camera and motion readable without extra flourish."
    return "; ".join(dict.fromkeys(unique)) + "."


def _fit_prompt_lines_to_budget(
    prompt_lines: list[str],
    *,
    max_chars: int | None,
) -> str:
    prompt_text = "\n".join(prompt_lines)
    if not max_chars or len(prompt_text) <= max_chars:
        return prompt_text

    adjusted = _apply_line_caps(
        prompt_lines,
        {
            "Shot brief: ": 900,
            "Color cue: ": 240,
            "Continuity anchor: ": 240,
            "Audio cue: ": 320,
            "Dialogue cue: ": 220,
        },
    )
    prompt_text = "\n".join(adjusted)
    if len(prompt_text) <= max_chars:
        return prompt_text

    adjusted = _apply_line_caps(
        adjusted,
        {
            "Shot brief: ": 720,
            "Color cue: ": 180,
            "Continuity anchor: ": 180,
            "Audio cue: ": 220,
            "Dialogue cue: ": 160,
        },
    )
    prompt_text = "\n".join(adjusted)
    if len(prompt_text) <= max_chars:
        return prompt_text

    overflow = len(prompt_text) - max_chars
    for prefix in ("Shot brief: ", "Audio cue: ", "Color cue: ", "Dialogue cue: "):
        adjusted, reduced = _trim_prefixed_line(adjusted, prefix=prefix, overflow=overflow)
        if not reduced:
            continue
        prompt_text = "\n".join(adjusted)
        if len(prompt_text) <= max_chars:
            return prompt_text
        overflow = len(prompt_text) - max_chars

    return prompt_text[: max_chars - 3].rstrip() + "..."


def _apply_line_caps(prompt_lines: list[str], caps: dict[str, int]) -> list[str]:
    adjusted = list(prompt_lines)
    for index, line in enumerate(adjusted):
        for prefix, limit in caps.items():
            if line.startswith(prefix):
                adjusted[index] = prefix + _shorten_text(line[len(prefix) :], limit)
                break
    return adjusted


def _trim_prefixed_line(
    prompt_lines: list[str],
    *,
    prefix: str,
    overflow: int,
) -> tuple[list[str], bool]:
    adjusted = list(prompt_lines)
    for index, line in enumerate(adjusted):
        if not line.startswith(prefix):
            continue
        trimmed = _shorten_text(
            line[len(prefix) :],
            max(120, len(line[len(prefix) :]) - overflow - 8),
        )
        adjusted[index] = prefix + trimmed
        return adjusted, True
    return adjusted, False


def _shorten_text(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    trimmed = text[: max_chars - 3].rstrip(" ,;:.")
    sentence_break = max(
        trimmed.rfind(". "),
        trimmed.rfind("; "),
        trimmed.rfind(", "),
    )
    if sentence_break >= max_chars // 2:
        trimmed = trimmed[:sentence_break].rstrip(" ,;:.")
    return trimmed + "..."


def _request_int(engine_pack: EnginePack, key: str) -> int | None:
    value = engine_pack.request_defaults.get(key)
    return value if isinstance(value, int) and value > 0 else None


def _string_or_none(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if isinstance(item, str) and str(item).strip()]


def _summary_reference(
    *,
    scene: Scene,
    plan: ShotPlan,
    look_and_feel: Any,
    rhythm_and_flow: Any,
) -> str:
    shot = plan.shots[0] if plan.shots else None
    pieces = [
        scene.heading,
        getattr(plan.coverage_strategy, "coverage_approach", None),
        getattr(rhythm_and_flow, "pacing_intent", None),
        getattr(look_and_feel, "camera_personality", None),
        getattr(shot, "blocking", None),
        getattr(shot, "action_description", None),
    ]
    return ". ".join(piece.strip() for piece in pieces if isinstance(piece, str) and piece.strip())


def _collect_dialogue_lines(plan: ShotPlan) -> list[str]:
    lines: list[str] = []
    for shot in plan.shots:
        for line in shot.dialogue_lines:
            cleaned = line.strip()
            if cleaned and cleaned not in lines:
                lines.append(cleaned)
    return lines[:3]


def _audio_description(sound_and_music: Any) -> str:
    description = _first_non_empty(
        getattr(sound_and_music, "ambient_environment", None),
        getattr(sound_and_music, "emotional_soundscape", None),
        getattr(sound_and_music, "music_intent", None),
        getattr(sound_and_music, "silence_placement", None),
    )
    return description or "Keep audio minimal and subordinate to the visual staging read."


def _tone_tags(intent_mood: Any, rhythm_and_flow: Any) -> list[str]:
    tags: list[str] = []
    if intent_mood is not None:
        tags.extend(_string_list(getattr(intent_mood, "mood_descriptors", [])))
    pacing = _first_non_empty(getattr(rhythm_and_flow, "pacing_intent", None))
    if pacing:
        tags.append(pacing)
    return tags[:4]


def _color_tags(look_and_feel: Any) -> list[str]:
    palette = _first_non_empty(getattr(look_and_feel, "color_palette", None))
    if not palette:
        return []
    return [part.strip() for part in palette.replace("/", ",").split(",") if part.strip()][:4]


def _camera_tags(primary_shot: Any) -> list[str]:
    shot_size = _normalize_token(getattr(primary_shot, "shot_size", None))
    movement = _normalize_token(getattr(primary_shot, "camera_movement", None))
    mapping: list[str] = []
    if shot_size and "two" in shot_size:
        mapping.append("locked_two_shot")
    elif shot_size and ("wide" in shot_size or "master" in shot_size):
        mapping.append("wide_master")
    elif shot_size and ("close" in shot_size or "single" in shot_size):
        mapping.append("profile_closeup")
    if movement and "push" in movement:
        mapping.append("slow_push_in")
    elif movement and ("pull" in movement or "back" in movement):
        mapping.append("slow_pull_back")
    elif movement and ("track" in movement or "dolly" in movement):
        mapping.append("lateral_track")
    elif movement and ("pan" in movement or "whip" in movement):
        mapping.append("whip_pan")
    if not mapping:
        mapping.append("static")
    return mapping


def _motion_tags(primary_shot: Any, rhythm_and_flow: Any) -> list[str]:
    dynamics = _normalize_token(getattr(rhythm_and_flow, "camera_movement_dynamics", None))
    movement = _normalize_token(getattr(primary_shot, "camera_movement", None))
    if dynamics and ("fast" in dynamics or "urgent" in dynamics):
        return ["fast_lateral"]
    if movement and "drift" in movement:
        return ["slow_drift"]
    if movement and ("handheld" in movement or "shaky" in movement):
        return ["escalating"]
    return ["measured"]


def _continuity_notes(
    *,
    scene: Scene,
    primary_shot: Any,
    resolved_inputs: Sequence[RenderResolvedInput],
) -> list[str]:
    notes: list[str] = []
    blocking = _first_non_empty(getattr(primary_shot, "blocking", None))
    if blocking:
        notes.append(blocking)
    if scene.location:
        notes.append(f"Keep location geography legible in {scene.location}.")
    if resolved_inputs:
        notes.append(
            "Carry forward locked references: "
            + ", ".join(input_item.label for input_item in resolved_inputs[:4])
        )
    return notes[:4]


def _clip_tags(*, scene: Scene, plan: ShotPlan) -> list[str]:
    tags = [scene.int_ext.lower(), scene.time_of_day.lower()]
    if plan.shots:
        tags.append(plan.shots[0].coverage_role.lower())
    return [tag for tag in tags if tag]


def _character_labels(*, scene: Scene, primary_shot: Any) -> list[str]:
    if primary_shot is not None and getattr(primary_shot, "characters_in_frame", None):
        return list(primary_shot.characters_in_frame)
    return list(scene.characters_present[:3])


def _first_non_empty(*values: Any) -> str | None:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _normalize_token(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip().lower()
