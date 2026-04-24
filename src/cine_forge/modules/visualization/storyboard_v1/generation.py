"""Scene-level storyboard artifact generation helpers."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from cine_forge.ai.image import (
    REFERENCE_IMAGE_FALLBACK_MODEL,
    ImageGenerationError,
    estimate_image_generation_cost_usd,
    generate_image,
    supports_direct_reference_images,
)
from cine_forge.artifacts import ArtifactStore
from cine_forge.modules.visualization.storyboard_v1.beats import build_ordered_grid_beats
from cine_forge.modules.visualization.storyboard_v1.grid import (
    build_grid_prompt,
    render_grid_template,
    resolve_grid_layout,
    slice_grid_image,
)
from cine_forge.modules.visualization.storyboard_v1.identity import (
    build_scene_character_identity_locks,
)
from cine_forge.modules.visualization.storyboard_v1.prompting import (
    _sanitize_visual_text,
    build_frame_prompt,
    load_continuity_states,
    reference_images_for_shot,
)
from cine_forge.modules.visualization.storyboard_v1.support import (
    STYLE_PROMPTS,
    empty_cost,
    image_format_for_model,
    latest_entity_ref,
    merge_cost,
    openai_quality_for_style,
    resolve_location_bible,
    slugify,
    storyboard_frame_dir,
)
from cine_forge.schemas import (
    ArtifactRef,
    CostRecord,
    Scene,
    ShotPlan,
    Storyboard,
    StoryboardFrame,
    StoryboardImageFile,
    StoryboardOverlay,
)


def generate_storyboard_for_scene(
    *,
    store: ArtifactStore,
    storyboard_ref: Any,
    scene: Scene,
    plan: ShotPlan,
    style: str,
    image_model: str,
    image_size: str | None,
    aspect_ratio: str,
    project_config_data: dict[str, Any] | None,
    look_and_feel_data: dict[str, Any] | None,
    intent_mood_data: dict[str, Any] | None,
    character_bibles: dict[str, dict[str, Any]],
    location_bibles: dict[str, dict[str, Any]],
    identity_model: str,
    max_retries: int,
    retry_delay_seconds: float,
    grid_mode: str = "off",
    grid_max_panels: int = 8,
) -> tuple[Storyboard, dict[str, Any]]:
    frames: list[StoryboardFrame] = []
    total_cost = empty_cost(model=image_model)
    scene_dir = storyboard_frame_dir(
        project_dir=store.project_dir,
        scene_id=plan.scene_id,
        version=storyboard_ref.version,
    )
    scene_dir.mkdir(parents=True, exist_ok=True)

    location_bible = resolve_location_bible(location_bibles, scene.location)
    scene_continuity_states = _scene_continuity_states(store, plan)
    character_identity_locks, identity_cost = build_scene_character_identity_locks(
        scene=scene,
        plan=plan,
        character_bibles=character_bibles,
        continuity_states=scene_continuity_states,
        project_config_data=project_config_data,
        model=identity_model,
    )
    merge_cost(total_cost, identity_cost)

    if grid_mode != "off":
        return _generate_grid_storyboard_for_scene(
            store=store,
            storyboard_ref=storyboard_ref,
            scene=scene,
            plan=plan,
            style=style,
            image_model=image_model,
            image_size=image_size,
            aspect_ratio=aspect_ratio,
            project_config_data=project_config_data,
            look_and_feel_data=look_and_feel_data,
            intent_mood_data=intent_mood_data,
            character_bibles=character_bibles,
            location_bible=location_bible,
            character_identity_locks=character_identity_locks,
            total_cost=total_cost,
            identity_cost=identity_cost,
            scene_dir=scene_dir,
            max_retries=max_retries,
            retry_delay_seconds=retry_delay_seconds,
            grid_mode=grid_mode,
            grid_max_panels=grid_max_panels,
        )

    for idx, shot in enumerate(plan.shots, start=1):
        continuity_states = load_continuity_states(store, shot.continuity_state_refs)
        reference_images = reference_images_for_shot(
            store=store,
            shot=shot,
            scene_location=scene.location,
            character_bibles=character_bibles,
            location_bible=location_bible,
        )
        prompt, prompt_sources = build_frame_prompt(
            scene=scene,
            plan=plan,
            shot=shot,
            style=style,
            project_config_data=project_config_data,
            look_and_feel_data=look_and_feel_data,
            intent_mood_data=intent_mood_data,
            character_bibles=character_bibles,
            location_bible=location_bible,
            continuity_states=continuity_states,
            character_identity_locks=character_identity_locks,
            reference_images=reference_images,
        )
        image_bytes, model_used, direct_reference_images = generate_frame_bytes(
            prompt=prompt,
            image_model=image_model,
            image_size=image_size,
            style=style,
            aspect_ratio=aspect_ratio,
            max_retries=max_retries,
            retry_delay_seconds=retry_delay_seconds,
            project_dir=store.project_dir,
            reference_images=reference_images,
        )
        extension, media_type = image_format_for_model(model_used)
        filename = f"frame_{idx:02d}_{shot.shot_id.lower()}{extension}"
        relative_path = str((scene_dir / filename).relative_to(store.project_dir))
        (scene_dir / filename).write_bytes(image_bytes)

        frame_cost = CostRecord(
            model=model_used,
            input_tokens=0,
            output_tokens=0,
            estimated_cost_usd=estimate_image_generation_cost_usd(
                model_used,
                entity_type="location",
                quality=openai_quality_for_style(style),
                size=image_size,
            ),
        )
        frames.append(
            StoryboardFrame(
                frame_id=f"{plan.scene_id}_frame_{idx:02d}",
                shot_ids=[shot.shot_id],
                primary_shot_id=shot.shot_id,
                image=StoryboardImageFile(relative_path=relative_path, media_type=media_type),
                prompt_used=prompt,
                prompt_sources_used=prompt_sources,
                visual_reference_images=reference_images,
                direct_reference_images=direct_reference_images,
                overlay=StoryboardOverlay(
                    shot_ids=[shot.shot_id],
                    shot_size=shot.shot_size,
                    camera_angle=shot.camera_angle,
                    camera_movement=shot.camera_movement,
                    character_labels=shot.characters_in_frame,
                    blocking_indicator=shot.blocking,
                    camera_indicator=(
                        f"{shot.camera_angle}; movement={shot.camera_movement}; "
                        f"lens={shot.lens_focal_length}"
                    ),
                    edit_intent=shot.edit_intent,
                ),
                duration_estimate_seconds=shot.duration_estimate_seconds,
                cost=frame_cost,
                notes=shot.action_description,
            )
        )
        merge_cost(
            total_cost,
            {
                "model": model_used,
                "input_tokens": 0,
                "output_tokens": 0,
                "estimated_cost_usd": frame_cost.estimated_cost_usd,
            },
        )

    storyboard = Storyboard(
        scene_id=plan.scene_id,
        scene_number=plan.scene_number,
        scene_heading=plan.scene_heading,
        scene_ref=plan.scene_ref,
        shot_plan_ref=latest_entity_ref(store, "shot_plan", plan.scene_id),
        style=style,
        aspect_ratio=aspect_ratio,
        character_identity_locks=list(character_identity_locks.values()),
        frames=frames,
        total_estimated_cost_usd=round(
            sum(frame.cost.estimated_cost_usd for frame in frames)
            + float(identity_cost.get("estimated_cost_usd", 0.0) or 0.0),
            8,
        ),
    )
    return storyboard, total_cost


def _generate_grid_storyboard_for_scene(
    *,
    store: ArtifactStore,
    storyboard_ref: Any,
    scene: Scene,
    plan: ShotPlan,
    style: str,
    image_model: str,
    image_size: str | None,
    aspect_ratio: str,
    project_config_data: dict[str, Any] | None,
    look_and_feel_data: dict[str, Any] | None,
    intent_mood_data: dict[str, Any] | None,
    character_bibles: dict[str, dict[str, Any]],
    location_bible: dict[str, Any] | None,
    character_identity_locks: dict[str, Any],
    total_cost: dict[str, Any],
    identity_cost: dict[str, Any],
    scene_dir: Path,
    max_retries: int,
    retry_delay_seconds: float,
    grid_mode: str,
    grid_max_panels: int,
) -> tuple[Storyboard, dict[str, Any]]:
    frames: list[StoryboardFrame] = []
    shot_chunks = _chunks(list(plan.shots), max(grid_max_panels, 1))

    for chunk_index, shots in enumerate(shot_chunks, start=1):
        layout = resolve_grid_layout(panel_count=len(shots), requested_size=image_size)
        template_path = scene_dir / f"grid_{chunk_index:02d}_template.jpg"
        uses_template_reference = grid_mode in {"template", "beat_template"}
        uses_beat_router = grid_mode == "beat_template"
        if uses_template_reference:
            render_grid_template(layout, template_path)

        panel_briefs: list[str] = []
        prompt_sources_by_shot: list[list[str]] = []
        reference_images_by_shot: list[list[str]] = []
        for shot in shots:
            continuity_states = load_continuity_states(store, shot.continuity_state_refs)
            reference_images = reference_images_for_shot(
                store=store,
                shot=shot,
                scene_location=scene.location,
                character_bibles=character_bibles,
                location_bible=location_bible,
            )
            _prompt, prompt_sources = build_frame_prompt(
                scene=scene,
                plan=plan,
                shot=shot,
                style=style,
                project_config_data=project_config_data,
                look_and_feel_data=look_and_feel_data,
                intent_mood_data=intent_mood_data,
                character_bibles=character_bibles,
                location_bible=location_bible,
                continuity_states=continuity_states,
                character_identity_locks=character_identity_locks,
                reference_images=reference_images,
            )
            panel_briefs.append(
                _panel_brief(
                    shot=shot,
                    scene=scene,
                    character_identity_locks=character_identity_locks,
                )
            )
            prompt_sources_by_shot.append(prompt_sources)
            reference_images_by_shot.append(reference_images)

        grid_prompt = build_grid_prompt(
            scene=scene,
            style=style,
            style_instruction=STYLE_PROMPTS[style],
            layout=layout,
            panel_briefs=panel_briefs,
            shot_ids=[shot.shot_id for shot in shots],
            uses_template_reference=uses_template_reference,
            ordered_story_beats=(
                build_ordered_grid_beats(
                    scene=scene,
                    shots=shots,
                    character_identity_locks=character_identity_locks,
                )
                if uses_beat_router
                else None
            ),
        )
        grid_bytes, model_used, direct_reference_images = generate_grid_bytes(
            prompt=grid_prompt,
            image_model=image_model,
            image_size=layout.size,
            style=style,
            aspect_ratio=aspect_ratio,
            max_retries=max_retries,
            retry_delay_seconds=retry_delay_seconds,
            project_dir=store.project_dir,
            reference_images=_dedupe(
                ref for shot_refs in reference_images_by_shot for ref in shot_refs
            ),
            template_path=template_path if uses_template_reference else None,
        )
        extension, media_type = image_format_for_model(model_used)
        grid_filename = f"grid_{chunk_index:02d}_full{extension}"
        (scene_dir / grid_filename).write_bytes(grid_bytes)

        output_paths: list[Path] = []
        for offset, shot in enumerate(shots, start=1):
            frame_number = len(frames) + offset
            output_paths.append(
                scene_dir / f"frame_{frame_number:02d}_{shot.shot_id.lower()}{extension}"
            )
        slice_grid_image(image_bytes=grid_bytes, layout=layout, output_paths=output_paths)

        grid_cost = estimate_image_generation_cost_usd(
            model_used,
            entity_type="location",
            quality=openai_quality_for_style(style),
            size=layout.size,
        )
        frame_cost = grid_cost / len(shots)
        for shot, output_path, prompt_sources, reference_images in zip(
            shots,
            output_paths,
            prompt_sources_by_shot,
            reference_images_by_shot,
            strict=True,
        ):
            frames.append(
                StoryboardFrame(
                    frame_id=f"{plan.scene_id}_frame_{len(frames) + 1:02d}",
                    shot_ids=[shot.shot_id],
                    primary_shot_id=shot.shot_id,
                    image=StoryboardImageFile(
                        relative_path=str(output_path.relative_to(store.project_dir)),
                        media_type=media_type,
                    ),
                    prompt_used=grid_prompt,
                    prompt_sources_used=_dedupe(
                        [*prompt_sources, "storyboard_grid"]
                        + (["storyboard_grid_beats"] if uses_beat_router else [])
                        + (["grid_template"] if uses_template_reference else [])
                    ),
                    visual_reference_images=reference_images,
                    direct_reference_images=[
                        ref for ref in reference_images if ref in direct_reference_images
                    ],
                    overlay=StoryboardOverlay(
                        shot_ids=[shot.shot_id],
                        shot_size=shot.shot_size,
                        camera_angle=shot.camera_angle,
                        camera_movement=shot.camera_movement,
                        character_labels=shot.characters_in_frame,
                        blocking_indicator=shot.blocking,
                        camera_indicator=(
                            f"{shot.camera_angle}; movement={shot.camera_movement}; "
                            f"lens={shot.lens_focal_length}"
                        ),
                        edit_intent=shot.edit_intent,
                    ),
                    duration_estimate_seconds=shot.duration_estimate_seconds,
                    cost=CostRecord(
                        model=model_used,
                        input_tokens=0,
                        output_tokens=0,
                        estimated_cost_usd=round(frame_cost, 8),
                    ),
                    notes=shot.action_description,
                )
            )
        merge_cost(
            total_cost,
            {
                "model": model_used,
                "input_tokens": 0,
                "output_tokens": 0,
                "estimated_cost_usd": grid_cost,
            },
        )

    storyboard = Storyboard(
        scene_id=plan.scene_id,
        scene_number=plan.scene_number,
        scene_heading=plan.scene_heading,
        scene_ref=plan.scene_ref,
        shot_plan_ref=latest_entity_ref(store, "shot_plan", plan.scene_id),
        style=style,
        aspect_ratio=aspect_ratio,
        character_identity_locks=list(character_identity_locks.values()),
        frames=frames,
        total_estimated_cost_usd=round(
            sum(frame.cost.estimated_cost_usd for frame in frames)
            + float(identity_cost.get("estimated_cost_usd", 0.0) or 0.0),
            8,
        ),
    )
    return storyboard, total_cost


def generate_frame_bytes(
    *,
    prompt: str,
    image_model: str,
    image_size: str | None,
    style: str,
    aspect_ratio: str,
    max_retries: int,
    retry_delay_seconds: float,
    project_dir: Path,
    reference_images: list[str],
) -> tuple[bytes, str, list[str]]:
    last_error: Exception | None = None
    effective_model, direct_reference_paths, direct_reference_images = (
        _resolve_storyboard_image_request(
            project_dir=project_dir,
            image_model=image_model,
            reference_images=reference_images,
        )
    )
    for attempt in range(max(max_retries, 0) + 1):
        try:
            image_bytes, model_used = generate_image(
                prompt=prompt,
                entity_type="location",
                model=effective_model,
                aspect_ratio=aspect_ratio,
                quality=openai_quality_for_style(style),
                reference_image_paths=direct_reference_paths,
                size=image_size,
            )
            return image_bytes, model_used, direct_reference_images
        except ImageGenerationError as exc:
            last_error = exc
            if attempt >= max_retries:
                break
            time.sleep(retry_delay_seconds * (attempt + 1))
    raise ImageGenerationError(f"storyboard frame generation failed after retries: {last_error}")


def generate_grid_bytes(
    *,
    prompt: str,
    image_model: str,
    image_size: str,
    style: str,
    aspect_ratio: str,
    max_retries: int,
    retry_delay_seconds: float,
    project_dir: Path,
    reference_images: list[str],
    template_path: Path | None,
) -> tuple[bytes, str, list[str]]:
    last_error: Exception | None = None
    effective_model, direct_reference_paths, direct_reference_images = (
        _resolve_storyboard_image_request(
            project_dir=project_dir,
            image_model=image_model,
            reference_images=reference_images,
            template_path=template_path,
        )
    )
    for attempt in range(max(max_retries, 0) + 1):
        try:
            image_bytes, model_used = generate_image(
                prompt=prompt,
                entity_type="location",
                model=effective_model,
                aspect_ratio=aspect_ratio,
                quality=openai_quality_for_style(style),
                reference_image_paths=direct_reference_paths,
                size=image_size,
            )
            return image_bytes, model_used, direct_reference_images
        except ImageGenerationError as exc:
            last_error = exc
            if attempt >= max_retries:
                break
            time.sleep(retry_delay_seconds * (attempt + 1))
    raise ImageGenerationError(f"storyboard grid generation failed after retries: {last_error}")


def _resolve_storyboard_image_request(
    *,
    project_dir: Path,
    image_model: str,
    reference_images: list[str],
    template_path: Path | None = None,
) -> tuple[str, list[str], list[str]]:
    effective_model = image_model
    has_reference_inputs = bool(reference_images) or template_path is not None
    if (
        has_reference_inputs
        and image_model != "mock"
        and not supports_direct_reference_images(image_model)
    ):
        effective_model = REFERENCE_IMAGE_FALLBACK_MODEL

    if not has_reference_inputs or not supports_direct_reference_images(effective_model):
        return effective_model, [], []

    direct_reference_paths = [
        str(_resolve_path(project_dir, relative_path)) for relative_path in reference_images
    ]
    if template_path is not None:
        direct_reference_paths.insert(0, str(template_path))
    return effective_model, direct_reference_paths, list(reference_images)


def _resolve_path(project_dir: Path, relative_path: str) -> Path:
    return project_dir / relative_path


def _scene_continuity_states(store: ArtifactStore, plan: ShotPlan) -> list[dict[str, Any]]:
    refs: list[ArtifactRef] = []
    seen: set[tuple[str, str, int, str]] = set()
    for shot in plan.shots:
        for raw_ref in shot.continuity_state_refs:
            loaded_ref = ArtifactRef.model_validate(raw_ref)
            key = (
                loaded_ref.artifact_type,
                loaded_ref.entity_id,
                loaded_ref.version,
                loaded_ref.path,
            )
            if key in seen:
                continue
            seen.add(key)
            refs.append(loaded_ref)
    return load_continuity_states(store, refs)


def _chunks(values: list[Any], size: int) -> list[list[Any]]:
    return [values[index : index + size] for index in range(0, len(values), size)]


def _dedupe(values: Any) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        deduped.append(text)
    return deduped


def _panel_brief(
    *,
    shot: Any,
    scene: Scene,
    character_identity_locks: dict[str, Any],
) -> str:
    character_lines: list[str] = []
    for character_id in getattr(shot, "characters_in_frame", []):
        lock = character_identity_locks.get(slugify(str(character_id)))
        if lock is None:
            continue
        details = [f"{lock.name}: {lock.appearance_summary}"]
        if getattr(lock, "wardrobe_summary", None):
            details.append(f"wardrobe {lock.wardrobe_summary}")
        character_lines.append("; ".join(details))
    character_note = " | ".join(character_lines) or "No named character identity lock."
    return "\n".join(
        [
            f"Setting: {scene.heading}.",
            (
                f"Framing: {shot.shot_size}, {shot.camera_angle}, "
                f"movement {shot.camera_movement}, lens {shot.lens_focal_length}."
            ),
            f"Characters: {', '.join(shot.characters_in_frame) or 'none'}. {character_note}",
            f"Blocking: {_sanitize_grid_panel_text(shot.blocking)}",
            f"Action: {_sanitize_grid_panel_text(shot.action_description)}",
            f"Edit intent: {_sanitize_grid_panel_text(shot.edit_intent)}",
            (
                "Written-surface rule: signs, screens, whiteboards, notes, maps, "
                "slates, and labels must be blank or illegible marks only."
            ),
        ]
    )


def _sanitize_grid_panel_text(value: Any) -> str:
    text = _sanitize_visual_text(value)
    if not text:
        return ""
    lower = text.lower()
    if any(
        marker in lower
        for marker in (
            "whiteboard",
            "sign",
            "screen",
            "monitor",
            "paper",
            "note",
            "map",
            "label",
            "slate",
            "call-sign",
        )
    ):
        return f"{text}; render all written content as blank shapes or illegible marks."
    return text
