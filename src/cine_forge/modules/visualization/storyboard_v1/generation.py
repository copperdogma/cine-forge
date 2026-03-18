"""Scene-level storyboard artifact generation helpers."""

from __future__ import annotations

import time
from typing import Any

from cine_forge.ai.image import (
    ImageGenerationError,
    estimate_image_generation_cost_usd,
    generate_image,
)
from cine_forge.artifacts import ArtifactStore
from cine_forge.modules.visualization.storyboard_v1.prompting import (
    build_frame_prompt,
    load_continuity_states,
    reference_images_for_shot,
)
from cine_forge.modules.visualization.storyboard_v1.support import (
    empty_cost,
    image_format_for_model,
    latest_entity_ref,
    merge_cost,
    openai_quality_for_style,
    resolve_location_bible,
    storyboard_frame_dir,
)
from cine_forge.schemas import (
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
    aspect_ratio: str,
    project_config_data: dict[str, Any] | None,
    look_and_feel_data: dict[str, Any] | None,
    intent_mood_data: dict[str, Any] | None,
    character_bibles: dict[str, dict[str, Any]],
    location_bibles: dict[str, dict[str, Any]],
    max_retries: int,
    retry_delay_seconds: float,
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
            reference_images=reference_images,
        )
        image_bytes, model_used = generate_frame_bytes(
            prompt=prompt,
            image_model=image_model,
            style=style,
            aspect_ratio=aspect_ratio,
            max_retries=max_retries,
            retry_delay_seconds=retry_delay_seconds,
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
        frames=frames,
        total_estimated_cost_usd=round(
            sum(frame.cost.estimated_cost_usd for frame in frames),
            8,
        ),
    )
    return storyboard, total_cost


def generate_frame_bytes(
    *,
    prompt: str,
    image_model: str,
    style: str,
    aspect_ratio: str,
    max_retries: int,
    retry_delay_seconds: float,
) -> tuple[bytes, str]:
    last_error: Exception | None = None
    for attempt in range(max(max_retries, 0) + 1):
        try:
            return generate_image(
                prompt=prompt,
                entity_type="location",
                model=image_model,
                aspect_ratio=aspect_ratio,
                quality=openai_quality_for_style(style),
            )
        except ImageGenerationError as exc:
            last_error = exc
            if attempt >= max_retries:
                break
            time.sleep(retry_delay_seconds * (attempt + 1))
    raise ImageGenerationError(f"storyboard frame generation failed after retries: {last_error}")
