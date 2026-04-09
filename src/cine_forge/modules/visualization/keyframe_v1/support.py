"""Shared helpers for keyframe extraction and preview crops."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError

from cine_forge.artifacts import ArtifactStore
from cine_forge.modules.visualization.storyboard_v1 import support as storyboard_support
from cine_forge.schemas import ArtifactRef, ShotDefinition

DEFAULT_FRAME_WIDTH = 1280
DEFAULT_FRAME_HEIGHT = 720


def anticipated_entity_ref(store: ArtifactStore, artifact_type: str, entity_id: str) -> ArtifactRef:
    versions = store.list_versions(artifact_type, entity_id)
    next_version = versions[-1].version + 1 if versions else 1
    return ArtifactRef(
        artifact_type=artifact_type,
        entity_id=entity_id,
        version=next_version,
        path=f"artifacts/{artifact_type}/{entity_id}/v{next_version}.json",
    )


def keyframe_media_dir(project_dir: Path, scene_id: str, version: int) -> Path:
    return project_dir / "artifacts" / "keyframe_media" / scene_id / f"v{version}"


def create_placeholder_image(
    *,
    output_path: Path,
    scene_heading: str,
    shot: ShotDefinition,
    width: int,
    height: int,
) -> str:
    image = Image.new("RGB", (width, height), color=(17, 24, 39))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()

    draw.rectangle((32, 32, width - 32, height - 32), outline=(99, 102, 241), width=3)
    draw.text((64, 70), scene_heading, fill=(255, 255, 255), font=font)
    draw.text((64, 140), f"{shot.shot_id}  {shot.shot_size}", fill=(226, 232, 240), font=font)
    draw.text(
        (64, 190),
        f"{shot.camera_angle} / {shot.camera_movement}",
        fill=(148, 163, 184),
        font=font,
    )
    draw.text((64, 240), shot.edit_intent[:96], fill=(244, 114, 182), font=font)
    draw.text((64, 320), shot.action_description[:128], fill=(191, 219, 254), font=font)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, format="JPEG", quality=88)
    return "image/jpeg"


def load_or_placeholder_image(
    *,
    project_dir: Path,
    media_dir: Path,
    scene_heading: str,
    shot: ShotDefinition,
    source_path: str | None,
    width: int,
    height: int,
) -> tuple[Path, str]:
    if source_path:
        candidate = project_dir / source_path
        if candidate.exists() and _is_pillow_readable(candidate):
            return candidate, "storyboard"
    placeholder_path = media_dir / f"{shot.shot_id.lower()}_placeholder.jpg"
    create_placeholder_image(
        output_path=placeholder_path,
        scene_heading=scene_heading,
        shot=shot,
        width=width,
        height=height,
    )
    return placeholder_path, "placeholder"


def open_image_or_none(project_dir: Path, relative_path: str | None) -> Image.Image | None:
    if not relative_path:
        return None
    candidate = project_dir / relative_path
    if not candidate.exists():
        return None
    try:
        with Image.open(candidate) as image:
            return image.convert("RGB")
    except (OSError, UnidentifiedImageError):
        return None


def relative_path(project_dir: Path, absolute_path: Path) -> str:
    return str(absolute_path.relative_to(project_dir))


def storyboard_by_scene(payload: Any) -> dict[str, dict[str, Any]]:
    return storyboard_support.scene_map(payload)


def frame_for_shot(storyboard_data: dict[str, Any] | None, shot_id: str) -> dict[str, Any] | None:
    if not isinstance(storyboard_data, dict):
        return None
    frames = storyboard_data.get("frames")
    if not isinstance(frames, list):
        return None
    for frame in frames:
        if not isinstance(frame, dict):
            continue
        shot_ids = frame.get("shot_ids")
        if isinstance(shot_ids, list) and shot_id in shot_ids:
            return frame
        if frame.get("primary_shot_id") == shot_id:
            return frame
    return None


def latest_entity_ref(store: ArtifactStore, artifact_type: str, entity_id: str) -> ArtifactRef:
    return storyboard_support.latest_entity_ref(store, artifact_type, entity_id)


def latest_project_ref(store: ArtifactStore, artifact_type: str) -> ArtifactRef | None:
    return storyboard_support.latest_project_ref(store, artifact_type)


def track_counts(entries: list[Any]) -> dict[str, int]:
    return storyboard_support.track_counts(entries)


def resize_contain(image: Image.Image, width: int, height: int) -> Image.Image:
    src_w, src_h = image.size
    scale = min(width / src_w, height / src_h)
    scaled = image.resize(
        (max(1, int(src_w * scale)), max(1, int(src_h * scale))),
        Image.Resampling.LANCZOS,
    )
    canvas = Image.new("RGB", (width, height), color=(11, 16, 27))
    left = (width - scaled.width) // 2
    top = (height - scaled.height) // 2
    canvas.paste(scaled, (left, top))
    return canvas


def _smoothstep(progress: float) -> float:
    clipped = min(max(progress, 0.0), 1.0)
    return clipped * clipped * (3.0 - (2.0 * clipped))


def render_motion_frame(
    image: Image.Image,
    *,
    progress: float,
    movement: str,
    width: int,
    height: int,
) -> Image.Image:
    movement_text = movement.lower()
    eased = _smoothstep(progress)
    scale = 1.0
    if any(token in movement_text for token in ("pan", "tilt")):
        scale = 1.06

    if "push" in movement_text or "dolly in" in movement_text or "zoom in" in movement_text:
        scale = max(scale, 1.0 + (0.08 * eased))
    elif "pull" in movement_text or "dolly out" in movement_text or "zoom out" in movement_text:
        scale = max(scale, 1.08 - (0.08 * eased))
    elif "static" not in movement_text:
        scale = max(scale, 1.0 + (0.02 * eased))

    base = resize_contain(
        image,
        max(int(width * scale), width),
        max(int(height * scale), height),
    )
    max_left = max(base.width - width, 0)
    max_top = max(base.height - height, 0)
    left = max_left // 2
    top = max_top // 2

    if "pan left" in movement_text:
        left = round(max_left * eased)
    elif "pan right" in movement_text:
        left = round(max_left * (1.0 - eased))
    elif "tilt up" in movement_text:
        top = round(max_top * (1.0 - eased))
    elif "tilt down" in movement_text:
        top = round(max_top * eased)

    return base.crop((left, top, left + width, top + height))


def derive_motion_crop(
    image: Image.Image,
    *,
    position: str,
    movement: str,
    width: int,
    height: int,
) -> Image.Image:
    progress_by_position = {"start": 0.0, "mid": 0.5, "end": 0.99}
    return render_motion_frame(
        image,
        progress=progress_by_position.get(position, 0.5),
        movement=movement,
        width=width,
        height=height,
    )


def _is_pillow_readable(path: Path) -> bool:
    try:
        with Image.open(path) as image:
            image.verify()
        return True
    except (OSError, UnidentifiedImageError):
        return False
