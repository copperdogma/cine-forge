"""Provider request-shaping helpers for render adapter generation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cine_forge.ai.video import VideoGenerationRequest, VideoReferenceInput
from cine_forge.modules.generation.render_adapter_v1.support import (
    AUDIO_KINDS as _AUDIO_KINDS,
)
from cine_forge.modules.generation.render_adapter_v1.support import (
    IMAGE_KINDS as _IMAGE_KINDS,
)
from cine_forge.modules.generation.render_adapter_v1.support import (
    media_type_for_image,
)
from cine_forge.schemas import RenderResolvedInput


def _shape_generation_request(
    *,
    engine_pack: Any,
    project_dir: Path,
    resolved_inputs: list[RenderResolvedInput],
    duration_seconds: int,
    resolution: str,
    aspect_ratio: str,
    allow_prompt_only_required_media: bool = False,
) -> tuple[VideoGenerationRequest, list[RenderResolvedInput], list[str]]:
    updated = [item.model_copy(deep=True) for item in resolved_inputs]
    image_inputs = sorted(
        [item for item in updated if item.kind in _IMAGE_KINDS and item.relative_path],
        key=_image_input_priority_key,
    )
    audio_inputs = [item for item in updated if item.kind in _AUDIO_KINDS]
    notes: list[str] = []

    first_frame_item = _pop_priority_input(
        image_inputs,
        predicate=lambda item: item.kind == "keyframe" and " start " in item.label.lower(),
    )
    last_frame_item = _pop_priority_input(
        image_inputs,
        predicate=lambda item: item.kind == "keyframe" and " end " in item.label.lower(),
    )
    if first_frame_item is not None:
        if engine_pack.limits.supports_first_frame:
            first_frame_item.used_as = "input_reference"
        elif first_frame_item.required and not allow_prompt_only_required_media:
            raise ValueError(
                f"{engine_pack.pack_id} does not support locked opening-frame guidance"
            )
        else:
            first_frame_item.used_as = "prompt_context"
            notes.append("Opening-frame reference was kept in prompt text only.")
            first_frame_item = None
    if last_frame_item is not None:
        if engine_pack.limits.supports_last_frame:
            last_frame_item.used_as = "last_frame"
        elif last_frame_item.required and not allow_prompt_only_required_media:
            raise ValueError(f"{engine_pack.pack_id} does not support locked last-frame guidance")
        else:
            last_frame_item.used_as = "prompt_context"
            notes.append("Last-frame reference was kept in prompt text only.")
            last_frame_item = None
    if first_frame_item is None and engine_pack.provider == "openai":
        first_frame_item = _pop_priority_input(
            image_inputs,
            predicate=_is_uploadable_raster_image,
        )
    if first_frame_item is not None and first_frame_item.used_as == "prompt_context":
        first_frame_item.used_as = "input_reference"

    first_frame = _video_reference(project_dir, first_frame_item)
    last_frame = _video_reference(project_dir, last_frame_item)
    if first_frame_item is not None and first_frame is None:
        if first_frame_item.required and not allow_prompt_only_required_media:
            raise ValueError(
                f"{first_frame_item.label} is not an uploadable raster image "
                f"for {engine_pack.pack_id}"
            )
        first_frame_item.used_as = "prompt_context"
        notes.append(
            f"{first_frame_item.label} stayed prompt-only because it is not "
            "an uploadable raster image."
        )
    if last_frame_item is not None and last_frame is None:
        if last_frame_item.required and not allow_prompt_only_required_media:
            raise ValueError(
                f"{last_frame_item.label} is not an uploadable raster image "
                f"for {engine_pack.pack_id}"
            )
        last_frame_item.used_as = "prompt_context"
        notes.append(
            f"{last_frame_item.label} stayed prompt-only because it is not "
            "an uploadable raster image."
        )
    remaining_capacity = (
        0 if engine_pack.provider == "openai" else int(engine_pack.limits.max_reference_images)
    )

    reference_images: list[VideoReferenceInput] = []
    required_overflow: list[str] = []
    for item in image_inputs:
        if item.used_as != "prompt_context":
            continue
        if remaining_capacity > 0:
            item.used_as = "reference_image"
            reference = _video_reference(project_dir, item)
            if reference is not None:
                reference_images.append(reference)
                remaining_capacity -= 1
            elif item.required and not allow_prompt_only_required_media:
                item.used_as = "unsupported"
                required_overflow.append(item.label)
            else:
                item.used_as = "prompt_context"
                notes.append(
                    f"{item.label} stayed prompt-only because it is not an uploadable raster image."
                )
            continue
        if item.required and not allow_prompt_only_required_media:
            item.used_as = "unsupported"
            required_overflow.append(item.label)
        else:
            item.used_as = "prompt_context"
            notes.append(
                f"{item.label} stayed prompt-only because "
                f"{engine_pack.pack_id} ran out of image slots."
            )
    if required_overflow:
        raise ValueError(
            f"{engine_pack.pack_id} cannot satisfy required image constraints: "
            f"{', '.join(required_overflow)}"
        )

    if audio_inputs:
        if not engine_pack.limits.supports_audio_upload:
            required_audio = [item.label for item in audio_inputs if item.required]
            if required_audio and not allow_prompt_only_required_media:
                for item in audio_inputs:
                    if item.required:
                        item.used_as = "unsupported"
                raise ValueError(
                    f"{engine_pack.pack_id} does not support required audio uploads: "
                    f"{', '.join(required_audio)}"
                )
            for item in audio_inputs:
                item.used_as = "prompt_context"
            if engine_pack.limits.supports_audio_cues:
                notes.append("Audio references were kept as prompt-level sound cues.")
            else:
                notes.append(
                    "Audio references were ignored because the engine pack has no audio pathway."
                )

    if reference_images and bool(
        engine_pack.request_defaults.get("reference_images_require_eight_seconds")
    ):
        if duration_seconds != 8:
            required_refs = [
                item.label
                for item in updated
                if item.used_as == "reference_image" and item.required
            ]
            if required_refs and not allow_prompt_only_required_media:
                raise ValueError(
                    f"{engine_pack.pack_id} requires 8-second renders for reference images: "
                    f"{', '.join(required_refs)}"
                )
            for item in updated:
                if item.used_as == "reference_image":
                    item.used_as = "prompt_context"
            notes.append(
                "Reference images stayed prompt-only because this engine pack "
                "requires 8s for uploads."
            )
            reference_images = []
    if bool(engine_pack.request_defaults.get("high_resolution_requires_eight_seconds")):
        if resolution == "1080p" and duration_seconds != 8:
            raise ValueError(f"{engine_pack.pack_id} requires 8-second renders for {resolution}")
    if (
        reference_images
        and (first_frame is not None or last_frame is not None)
        and not bool(
            engine_pack.request_defaults.get(
                "mixed_frame_guidance_and_reference_images_supported",
                True,
            )
        )
    ):
        required_refs = [
            item.label
            for item in updated
            if item.used_as == "reference_image" and item.required
        ]
        if required_refs and not allow_prompt_only_required_media:
            for item in updated:
                if item.used_as == "reference_image" and item.required:
                    item.used_as = "unsupported"
            raise ValueError(
                f"{engine_pack.pack_id} cannot combine frame guidance with required "
                f"reference images on the live provider API: {', '.join(required_refs)}"
            )
        for item in updated:
            if item.used_as == "reference_image":
                item.used_as = "prompt_context"
        reference_images = []
        notes.append(
            "Additional reference images stayed prompt-only because the live provider "
            "API rejects mixing frame guidance with extra reference images."
        )

    return (
        VideoGenerationRequest(
            prompt="",
            duration_seconds=duration_seconds,
            resolution=resolution,
            aspect_ratio=aspect_ratio,
            first_frame=first_frame,
            last_frame=last_frame,
            reference_images=reference_images,
            provider_params={},
        ),
        updated,
        notes,
    )


def _video_reference(
    project_dir: Path, item: RenderResolvedInput | None
) -> VideoReferenceInput | None:
    if item is None or not item.relative_path:
        return None
    media_type = _resolved_media_type(item)
    if media_type is None:
        return None
    return VideoReferenceInput(
        path=project_dir / item.relative_path,
        media_type=media_type,
        usage=item.used_as,
    )


def _pop_priority_input(
    items: list[RenderResolvedInput],
    *,
    predicate: Any,
) -> RenderResolvedInput | None:
    for index, item in enumerate(items):
        if predicate(item):
            return items.pop(index)
    return None


def _image_input_priority_key(item: RenderResolvedInput) -> tuple[int, int, int, str]:
    return (
        0 if item.required else 1,
        _lock_priority_rank(item.lock_status),
        _kind_priority_rank(item.kind),
        item.label.lower(),
    )


def _lock_priority_rank(lock_status: str | None) -> int:
    if lock_status == "hard_locked":
        return 0
    if lock_status == "selected_visual_reference":
        return 1
    if lock_status == "system_default_visual_reference":
        return 2
    if lock_status == "soft_locked":
        return 3
    if lock_status == "unlocked":
        return 4
    return 5


def _kind_priority_rank(kind: str | None) -> int:
    if kind == "keyframe":
        return 0
    if kind == "character_injected_image":
        return 1
    if kind == "location_injected_image":
        return 2
    if kind == "prop_injected_image":
        return 3
    if kind == "scene_injected_image":
        return 4
    if kind == "project_injected_image":
        return 5
    return 6


def _resolved_media_type(item: RenderResolvedInput) -> str | None:
    media_type = item.media_type or media_type_for_image(item.relative_path or "")
    if media_type in {"image/jpeg", "image/png", "image/webp"}:
        return media_type
    return None


def _is_uploadable_raster_image(item: RenderResolvedInput) -> bool:
    return _resolved_media_type(item) is not None
