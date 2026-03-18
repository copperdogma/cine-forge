"""Prompt and lineage assembly for storyboard generation."""

from __future__ import annotations

from typing import Any

from cine_forge.artifacts import ArtifactStore
from cine_forge.modules.visualization.storyboard_v1.support import (
    ALLOWED_STYLES,
    DEFAULT_STYLE,
    STYLE_PROMPTS,
    clean_prompt_lines,
    dedupe_refs,
    latest_entity_ref,
    latest_project_ref,
    maybe_latest_ref,
    normalize_aspect_ratio,
    resolve_character_bible,
    slugify,
    string_list,
)
from cine_forge.schemas import ArtifactRef, ProjectConfig, Scene, ShotPlan


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
    reference_images: list[str],
) -> tuple[str, list[str]]:
    lines = [STYLE_PROMPTS[style]]
    sources = ["shot_plan"]

    lines.extend(
        [
            f"Scene heading: {plan.scene_heading}.",
            f"Coverage strategy: {plan.coverage_strategy.coverage_approach}.",
            f"Shot size: {shot.shot_size}. Camera angle: {shot.camera_angle}.",
            f"Camera movement: {shot.camera_movement}. Lens: {shot.lens_focal_length}.",
            f"Coverage role: {shot.coverage_role}.",
            f"Blocking: {shot.blocking}.",
            f"Action: {shot.action_description}.",
            f"Edit intent: {shot.edit_intent}.",
        ]
    )
    if shot.dialogue_lines:
        lines.append(f"Key dialogue beat: {' / '.join(shot.dialogue_lines[:2])}.")

    if isinstance(look_and_feel_data, dict):
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
                lines.append(value.strip())
        sources.append("look_and_feel")

    if isinstance(project_config_data, dict):
        genres = string_list(project_config_data.get("genre"))
        tones = string_list(project_config_data.get("tone"))
        if genres:
            lines.append(f"Genre context: {', '.join(genres)}.")
        if tones:
            lines.append(f"Tone context: {', '.join(tones)}.")
        production_format = project_config_data.get("production_format")
        if isinstance(production_format, str) and production_format.strip():
            lines.append(f"Production format: {production_format}.")
        sources.append("project_config")

    if isinstance(intent_mood_data, dict):
        moods = string_list(intent_mood_data.get("mood_descriptors"))
        if moods:
            lines.append(f"Mood descriptors: {', '.join(moods)}.")
        intent = intent_mood_data.get("natural_language_intent")
        if isinstance(intent, str) and intent.strip():
            lines.append(f"Intent brief: {intent.strip()}.")
        sources.append("intent_mood")

    for character_id in shot.characters_in_frame:
        character_bible = resolve_character_bible(character_bibles, character_id)
        if not character_bible:
            continue
        lines.append(
            f"Character {character_bible.get('name', character_id)}: "
            f"{str(character_bible.get('description') or '').strip()}."
        )
        sources.append("character_bible")

    if location_bible:
        lines.append(
            f"Location: {str(location_bible.get('description') or scene.location).strip()}."
        )
        sources.append("location_bible")

    continuity_notes = continuity_notes_for_prompt(continuity_states)
    if continuity_notes:
        lines.append(f"Continuity anchors: {' '.join(continuity_notes)}")
        sources.append("continuity_state")

    if reference_images:
        lines.append(
            "Preserve approved design continuity from the available visual reference images for"
            " recurring characters and locations."
        )
        sources.append("bible_manifest")

    lines.append(
        "Single storyboard frame only. No letters, captions, UI, comic panels, or visible text."
    )

    prompt = " ".join(clean_prompt_lines(lines))
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
