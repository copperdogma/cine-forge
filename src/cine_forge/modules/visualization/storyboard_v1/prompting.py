"""Prompt and lineage assembly for storyboard generation."""

from __future__ import annotations

import re
from typing import Any

from cine_forge.artifacts import ArtifactStore
from cine_forge.modules.visualization.storyboard_v1.support import (
    ALLOWED_STYLES,
    DEFAULT_STYLE,
    STYLE_PROMPTS,
    dedupe_refs,
    latest_entity_ref,
    latest_project_ref,
    maybe_latest_ref,
    normalize_aspect_ratio,
    resolve_character_bible,
    slugify,
    string_list,
)
from cine_forge.schemas import (
    ArtifactRef,
    ProjectConfig,
    Scene,
    ShotPlan,
    StoryboardCharacterIdentityLock,
)

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
_PHYSICAL_TRAIT_HINTS = (
    "appearance",
    "age",
    "build",
    "height",
    "hair",
    "eye",
    "skin",
    "costume",
    "wardrobe",
    "clothing",
    "physical",
    "facial hair",
    "mustache",
    "moustache",
    "beard",
    "silhouette",
)
_VISUAL_CONTINUITY_KEYS = {
    "appearance",
    "wardrobe",
    "clothing",
    "costume",
    "hair",
    "facial_hair",
    "mustache",
    "moustache",
    "beard",
    "build",
    "silhouette",
    "uniform",
}
_OFFSHOT_DESCRIPTION_HINTS = (
    "killed",
    "dies",
    "death",
    "murdered",
    "sniper",
    "later",
    "eventually",
    "moments before",
)
_QUOTED_TEXT_RE = re.compile(
    r'(?<!\w)"[^"\n]{1,240}"(?!\w)|'
    r"(?<!\w)'[^'\n]{2,240}'(?!\w)|"
    r"[“][^”\n]{1,240}[”]|"
    r"[‘][^’\n]{2,240}[’]"
)
_TEXT_DISPLAY_REPLACEMENTS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(r"\bON\s+AIR\b", flags=re.IGNORECASE),
        "an unlettered illuminated studio status sign",
    ),
    (
        re.compile(r"\b(?:K|W)[A-Z]{2,4}(?:[-\s]?(?:AM|FM|TV))?\b"),
        "an abstract radio call-sign marker",
    ),
    (
        re.compile(
            r"\b(?:whiteboard|chalkboard|blackboard)\b([^.!?]{0,120})",
            flags=re.IGNORECASE,
        ),
        "whiteboard with blank diagrams and illegible sketch marks",
    ),
    (
        re.compile(
            r"\b(?:screen|monitor|paper|note|map|sign|poster|label|slate)\b([^.!?]{0,80})",
            flags=re.IGNORECASE,
        ),
        "text-bearing surface rendered as blank shapes or illegible marks",
    ),
)


def resolve_style(
    *,
    params: dict[str, Any],
    runtime_params: dict[str, Any],
    project_config: ProjectConfig | None,
) -> str:
    style = (
        params.get("style")
        or runtime_params.get("storyboard_style")
        or (project_config.storyboard_style if project_config else None)
        or DEFAULT_STYLE
    )
    if not isinstance(style, str) or style not in ALLOWED_STYLES:
        raise ValueError(f"storyboard_v1 received unsupported style '{style}'")
    return style


def resolve_aspect_ratio(
    *,
    project_config_data: dict[str, Any] | None,
    look_and_feel_by_scene: dict[str, dict[str, Any]],
) -> dict[str, str]:
    default_ratio = normalize_aspect_ratio(
        look_and_feel_by_scene.get("__project__", {}).get("aspect_ratio_override")
        if "__project__" in look_and_feel_by_scene
        else None
    )
    if default_ratio is None and isinstance(project_config_data, dict):
        default_ratio = normalize_aspect_ratio(project_config_data.get("aspect_ratio"))
    resolved = {"__default__": default_ratio or "16:9"}
    for scene_id, payload in look_and_feel_by_scene.items():
        ratio = normalize_aspect_ratio(payload.get("aspect_ratio_override"))
        if ratio:
            resolved[scene_id] = ratio
    return resolved


def build_frame_prompt(
    *,
    scene: Scene,
    plan: ShotPlan,
    shot: Any,
    style: str,
    project_config_data: dict[str, Any] | None,
    look_and_feel_data: dict[str, Any] | None,
    intent_mood_data: dict[str, Any] | None,
    character_bibles: dict[str, dict[str, Any]],
    location_bible: dict[str, Any] | None,
    continuity_states: list[dict[str, Any]],
    character_identity_locks: dict[str, StoryboardCharacterIdentityLock] | None,
    reference_images: list[str],
) -> tuple[str, list[str]]:
    lines = [
        STYLE_PROMPTS[style],
        "",
        "Literal shot requirements:",
        f"- Scene setting: {_ensure_sentence(_scene_setting(scene))}",
        (
            f"- Shot framing: size={shot.shot_size}; angle={shot.camera_angle}; "
            f"movement={shot.camera_movement}; lens feel={_lens_feel(shot.lens_focal_length)}."
        ),
        f"- Coverage role: {_ensure_sentence(shot.coverage_role)}",
        f"- Blocking: {_ensure_sentence(_sanitize_visual_text(shot.blocking))}",
        f"- Action: {_ensure_sentence(_sanitize_visual_text(shot.action_description))}",
        f"- Edit intent: {_ensure_sentence(_sanitize_visual_text(shot.edit_intent))}",
    ]
    sources = ["shot_plan"]
    coverage_strategy = _first_scene_sentence(plan.coverage_strategy.coverage_approach)
    if coverage_strategy:
        lines.append(f"- Scene coverage intent: {_ensure_sentence(coverage_strategy)}")

    if isinstance(look_and_feel_data, dict):
        look_and_feel_lines: list[str] = []
        for field_name in (
            "lighting_concept",
            "color_palette",
            "composition_philosophy",
            "camera_personality",
            "costume_notes",
            "production_design_notes",
        ):
            value = look_and_feel_data.get(field_name)
            if isinstance(value, str) and value.strip():
                look_and_feel_lines.append(
                    f"- {field_name.replace('_', ' ').title()}: {_ensure_sentence(value)}"
                )
        if look_and_feel_lines:
            lines.extend(["", "Look and feel anchors:", *look_and_feel_lines])
            sources.append("look_and_feel")

    if isinstance(project_config_data, dict):
        genres = string_list(project_config_data.get("genre"))
        tones = string_list(project_config_data.get("tone"))
        context_lines: list[str] = []
        if genres:
            context_lines.append(f"- Genre context: {', '.join(genres)}.")
        if tones:
            context_lines.append(f"- Tone context: {', '.join(tones)}.")
        production_format = project_config_data.get("production_format")
        if isinstance(production_format, str) and production_format.strip():
            context_lines.append(f"- Production format: {production_format.strip()}.")
        if context_lines:
            lines.extend(["", "Project context:", *context_lines])
            sources.append("project_config")

    if isinstance(intent_mood_data, dict):
        moods = string_list(intent_mood_data.get("mood_descriptors"))
        mood_lines: list[str] = []
        if moods:
            mood_lines.append(f"- Mood descriptors: {', '.join(moods)}.")
        intent = intent_mood_data.get("natural_language_intent")
        if isinstance(intent, str) and intent.strip():
            mood_lines.append(f"- Intent brief: {_ensure_sentence(intent)}")
        if mood_lines:
            lines.extend(["", "Intent and mood:", *mood_lines])
            sources.append("intent_mood")

    visible_subject_line = _visible_subject_requirement(shot, character_bibles)
    if visible_subject_line:
        lines.extend(["", "Visible subjects:", visible_subject_line])

    lines.extend(["", "Scene style lock:", *_style_lock_lines(style)])

    character_identity_lines = _character_identity_lines(
        shot=shot,
        character_bibles=character_bibles,
        continuity_states=continuity_states,
        character_identity_locks=character_identity_locks,
    )
    if character_identity_lines:
        lines.extend(["", "Character identity locks:", *character_identity_lines])
        sources.append("character_bible")

    for character_id in shot.characters_in_frame:
        character_bible = resolve_character_bible(character_bibles, character_id)
        if not character_bible:
            continue
        scene_relevant_description = _scene_relevant_description(character_bible.get("description"))
        if scene_relevant_description:
            character_name = str(character_bible.get("name") or character_id).strip()
            lines.append(
                f"- Scene-relevant character context for {character_name}: "
                f"{_ensure_sentence(scene_relevant_description)}"
            )

    if location_bible:
        location_description = _scene_relevant_description(
            location_bible.get("description") or scene.location
        )
        lines.extend(
            [
                "",
                "Location anchor:",
                f"- {_ensure_sentence(location_description or scene.location)}",
            ]
        )
        sources.append("location_bible")

    continuity_notes = continuity_notes_for_prompt(continuity_states)
    if continuity_notes:
        lines.extend(["", "Continuity anchors:", *[f"- {note}" for note in continuity_notes]])
        sources.append("continuity_state")

    if reference_images:
        lines.extend(
            [
                "",
                "Reference-image constraints:",
                (
                    "- Use the supplied reference images as hard anchors for recurring "
                    "character identity, wardrobe, silhouette, and location design."
                ),
                (
                    "- Preserve those reference cues unless the literal shot description "
                    "explicitly requires a visible change."
                ),
            ]
        )
        sources.append("reference_images")

    lines.extend(
        [
            "",
            "Hard constraints:",
            "- Show the literal present-moment shot described above.",
            (
                "- Do not render dialogue, captions, speech bubbles, subtitles, "
                "labels, slates, UI, or any readable text."
            ),
            (
                "- Generate the image area only, not a storyboard page layout: "
                "no panel borders, headers, shot numbers, lens labels, or "
                "editorial annotations."
            ),
            (
                "- Keep the exact same rendering medium, line treatment, finish, "
                "and overall illustration discipline across every frame in this "
                "scene."
            ),
            (
                "- Do not invent flashbacks, future events, police-uniform hero "
                "shots, symbolic metaphors, or montage imagery unless the shot "
                "explicitly asks for them."
            ),
            (
                "- If the screenplay leaves appearance under-specified, choose "
                "one grounded version and keep age band, face, ethnicity, build, "
                "hair, facial hair, and wardrobe silhouette fixed across every "
                "frame in this scene."
            ),
        ]
    )
    if _shot_is_insert(shot):
        lines.append(
            "- This is an insert/detail frame, so a prop-focused "
            "composition is allowed only if it matches the blocking and "
            "action above."
        )
    else:
        lines.append(
            "- This is not a prop-only cutaway. Keep the named character "
            "subjects visible and do not replace them with isolated shoes, "
            "bottles, hands, or product-photo compositions."
        )
    lines.append("- Single storyboard frame only.")

    prompt = "\n".join(line.rstrip() for line in lines if line is not None).strip()
    return prompt, list(dict.fromkeys(sources))


def storyboard_lineage(
    *,
    store: ArtifactStore,
    plan: ShotPlan,
    scene: Scene,
    location_bibles: dict[str, dict[str, Any]],
    project_config_present: bool,
    look_and_feel_present: bool,
    intent_mood_present: bool,
) -> list[ArtifactRef]:
    refs: list[ArtifactRef] = [
        plan.scene_ref,
        latest_entity_ref(store, "shot_plan", plan.scene_id),
    ]
    if look_and_feel_present:
        refs.append(latest_entity_ref(store, "look_and_feel", plan.scene_id))
    if intent_mood_present:
        intent_ref = latest_project_ref(store, "intent_mood")
        if intent_ref is not None:
            refs.append(intent_ref)
    if project_config_present:
        project_ref = latest_project_ref(store, "project_config")
        if project_ref is not None:
            refs.append(project_ref)
    for shot in plan.shots:
        refs.extend(ArtifactRef.model_validate(item) for item in shot.continuity_state_refs)
        for character_id in shot.characters_in_frame:
            ref = maybe_latest_ref(store, "character_bible", slugify(character_id))
            if ref is not None:
                refs.append(ref)
            manifest_ref = maybe_latest_ref(
                store,
                "bible_manifest",
                f"character_{slugify(character_id)}",
            )
            if manifest_ref is not None:
                refs.append(manifest_ref)
    location_key = slugify(scene.location)
    if location_key in location_bibles:
        location_ref = maybe_latest_ref(store, "location_bible", location_key)
        if location_ref is not None:
            refs.append(location_ref)
        manifest_ref = maybe_latest_ref(store, "bible_manifest", f"location_{location_key}")
        if manifest_ref is not None:
            refs.append(manifest_ref)
    return dedupe_refs(refs)


def reference_images_for_shot(
    *,
    store: ArtifactStore,
    shot: Any,
    scene_location: str,
    character_bibles: dict[str, dict[str, Any]],
    location_bible: dict[str, Any] | None,
) -> list[str]:
    paths: list[str] = []
    for character_id in shot.characters_in_frame:
        if resolve_character_bible(character_bibles, character_id) is None:
            continue
        manifest_ref = maybe_latest_ref(
            store,
            "bible_manifest",
            f"character_{slugify(character_id)}",
        )
        if manifest_ref is not None:
            paths.extend(manifest_reference_images(store, manifest_ref))
    if location_bible is not None:
        location_key = slugify(str(location_bible.get("location_id") or scene_location))
        manifest_ref = maybe_latest_ref(store, "bible_manifest", f"location_{location_key}")
        if manifest_ref is not None:
            paths.extend(manifest_reference_images(store, manifest_ref))
    return list(dict.fromkeys(paths))


def manifest_reference_images(store: ArtifactStore, manifest_ref: ArtifactRef) -> list[str]:
    manifest_artifact = store.load_artifact(manifest_ref)
    filename = manifest_artifact.data.get("visual_reference_image")
    if not isinstance(filename, str) or not filename.strip():
        return []
    parent = (store.project_dir / manifest_ref.path).parent.relative_to(store.project_dir)
    return [str(parent / filename)]


def load_continuity_states(store: ArtifactStore, refs: list[ArtifactRef]) -> list[dict[str, Any]]:
    states: list[dict[str, Any]] = []
    for ref in refs:
        parsed = ArtifactRef.model_validate(ref)
        states.append(store.load_artifact(parsed).data)
    return states


def continuity_notes_for_prompt(states: list[dict[str, Any]]) -> list[str]:
    notes: list[str] = []
    for state in states:
        entity_id = str(state.get("entity_id") or "").strip()
        properties = state.get("properties")
        if not isinstance(properties, list):
            continue
        detail = ", ".join(
            f"{item.get('key')}: {item.get('value')}"
            for item in properties
            if isinstance(item, dict) and item.get("key") and item.get("value")
        )
        if detail:
            notes.append(f"{entity_id} -> {detail}.")
    return notes


def _ensure_sentence(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if text.endswith((".", "!", "?")):
        return text
    return f"{text}."


def _split_sentences(value: Any) -> list[str]:
    text = str(value or "").strip()
    if not text:
        return []
    return [part.strip() for part in _SENTENCE_SPLIT_RE.split(text) if part.strip()]


def _first_scene_sentence(value: Any) -> str:
    sentences = _split_sentences(value)
    return sentences[0] if sentences else str(value or "").strip()


def _scene_relevant_description(value: Any) -> str:
    sentences = _split_sentences(value)
    if not sentences:
        return str(value or "").strip()
    for sentence in sentences:
        lowered = sentence.lower()
        if any(hint in lowered for hint in _OFFSHOT_DESCRIPTION_HINTS):
            continue
        return sentence
    return sentences[0]


def _shot_is_insert(shot: Any) -> bool:
    role = str(getattr(shot, "coverage_role", "") or "").lower()
    size = str(getattr(shot, "shot_size", "") or "").lower()
    return "insert" in role or "insert" in size


def _scene_setting(scene: Scene) -> str:
    int_ext = str(getattr(scene, "int_ext", "") or "").strip().lower()
    location = str(getattr(scene, "location", "") or "").strip()
    time_of_day = str(getattr(scene, "time_of_day", "") or "").strip().lower()
    parts = [part for part in (int_ext, location, time_of_day) if part]
    return " ".join(parts) if parts else str(scene.heading)


def _lens_feel(value: Any) -> str:
    text = str(value or "").strip().lower()
    if not text:
        return "natural perspective"
    if "macro" in text:
        return "macro detail"
    if "wide" in text:
        return "wide lens perspective"
    if "telephoto" in text:
        return "telephoto compression"
    if "35" in text or "32" in text or "28" in text or "24" in text:
        return "wide lens perspective"
    if "85" in text or "100" in text or "135" in text:
        return "telephoto compression"
    return "natural perspective"


def _sanitize_visual_text(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    text = _QUOTED_TEXT_RE.sub("the spoken line", text)
    for pattern, replacement in _TEXT_DISPLAY_REPLACEMENTS:
        text = pattern.sub(replacement, text)
    text = re.sub(r"\b[A-Z][A-Z0-9_' ]{1,20}:\s*", "", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def _style_lock_lines(style: str) -> list[str]:
    common = [
        "- Keep one consistent visual medium for the entire scene sequence.",
        (
            "- Never output a storyboard sheet, comic page, script page, contact "
            "sheet, or frame with embedded labels."
        ),
    ]
    if style == "sketch":
        return common + [
            (
                "- Render as monochrome hand-drawn pencil storyboard art with "
                "rough graphite linework and restrained grayscale shading."
            ),
            (
                "- Do not render live-action photography, painted concept art, "
                "glossy illustration, or mixed-media collage."
            ),
        ]
    if style == "clean_line":
        return common + [
            (
                "- Render as monochrome clean-line storyboard illustration with "
                "crisp outlines and restrained shading."
            ),
            (
                "- Do not render live-action photography, photoreal concept art, "
                "or sketchbook page markup."
            ),
        ]
    if style == "animation_style":
        return common + [
            (
                "- Render as monochrome drawn animation-style storyboard art "
                "with simplified linework and readable silhouettes."
            ),
            ("- Do not render live-action photography, 3D renders, or painted concept art."),
        ]
    if style == "abstract_color_coded":
        return common + [
            (
                "- Render as flat graphic storyboard art with controlled color "
                "blocks and simplified shapes."
            ),
            (
                "- Do not render live-action photography, painterly concept art, "
                "or labeled infographic layouts."
            ),
        ]
    return common + [
        (
            "- Even in photoreal mode, render a single clean full-bleed "
            "cinematic frame rather than a page or contact sheet."
        ),
    ]


def _visible_subject_requirement(
    shot: Any,
    character_bibles: dict[str, dict[str, Any]],
) -> str | None:
    if _shot_is_insert(shot) and not shot.characters_in_frame:
        return "- Prop/detail insert only; no full character face is required."
    visible_names: list[str] = []
    for character_id in shot.characters_in_frame:
        character_bible = resolve_character_bible(character_bibles, character_id)
        if character_bible:
            visible_names.append(str(character_bible.get("name") or character_id).strip())
        else:
            visible_names.append(str(character_id).strip())
    if not visible_names:
        return None
    return (
        "- Keep these named subjects physically present in frame as described: "
        + ", ".join(visible_names)
        + "."
    )


def _character_identity_lines(
    *,
    shot: Any,
    character_bibles: dict[str, dict[str, Any]],
    continuity_states: list[dict[str, Any]],
    character_identity_locks: dict[str, StoryboardCharacterIdentityLock] | None,
) -> list[str]:
    lines: list[str] = []
    multiple_characters = len(shot.characters_in_frame) > 1
    locks = character_identity_locks or {}
    for character_id in shot.characters_in_frame:
        character_bible = resolve_character_bible(character_bibles, character_id)
        if not character_bible:
            continue
        lock = locks.get(slugify(character_id))
        if lock is not None:
            name = lock.name.strip()
            detail_parts = [
                f"{name}: {_ensure_sentence(lock.appearance_summary)}",
            ]
            if lock.distinguishing_features:
                detail_parts.append(
                    "Distinctive visual anchors: "
                    + "; ".join(
                        item.strip().rstrip(".")
                        for item in lock.distinguishing_features[:4]
                        if item and item.strip()
                    )
                    + "."
                )
            if lock.wardrobe_summary:
                detail_parts.append(f"Wardrobe anchor: {_ensure_sentence(lock.wardrobe_summary)}")
        else:
            name = str(character_bible.get("name") or character_id).strip()
            summary = _scene_relevant_description(character_bible.get("description"))
            visual_traits = _character_visual_traits(character_bible, continuity_states)
            detail_parts = [
                f"{name}: {summary}" if summary else f"{name}: recurring character in this scene."
            ]
            if visual_traits:
                detail_parts.append(
                    "Scene-visible identity cues: "
                    + "; ".join(item.strip().rstrip(".") for item in visual_traits[:4] if item)
                    + "."
                )
            else:
                detail_parts.append(
                    "Appearance is under-specified by the screenplay, so choose "
                    "one grounded visual design now and keep it fixed."
                )
        detail_parts.append(
            "Keep the exact same face structure, age band, build, hair, "
            "facial hair status, and wardrobe silhouette across every "
            "storyboard frame in this scene."
        )
        if multiple_characters:
            detail_parts.append(
                "Keep this character visually distinct from the other named "
                "characters in the scene."
            )
        lines.append(
            "- " + " ".join(part.strip() for part in detail_parts if part and part.strip())
        )
    return lines


def _character_visual_traits(
    character_bible: dict[str, Any],
    continuity_states: list[dict[str, Any]],
) -> list[str]:
    traits: list[str] = []
    inferred_traits = character_bible.get("inferred_traits")
    if isinstance(inferred_traits, list):
        for item in inferred_traits:
            if not isinstance(item, dict):
                continue
            trait_name = str(item.get("trait") or "").lower()
            value = str(item.get("value") or "").strip()
            if not value:
                continue
            if any(hint in trait_name for hint in _PHYSICAL_TRAIT_HINTS):
                traits.append(value)

    character_key = slugify(
        str(character_bible.get("character_id") or character_bible.get("name") or "").strip()
    )
    for state in continuity_states:
        if slugify(str(state.get("entity_id") or "").strip()) != character_key:
            continue
        properties = state.get("properties")
        if not isinstance(properties, list):
            continue
        for item in properties:
            if not isinstance(item, dict):
                continue
            key = str(item.get("key") or "").strip().lower()
            value = str(item.get("value") or "").strip()
            if key in _VISUAL_CONTINUITY_KEYS and value:
                traits.append(value)
    return list(dict.fromkeys(traits))
