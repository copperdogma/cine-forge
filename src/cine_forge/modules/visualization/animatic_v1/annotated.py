"""Helpers for richer deterministic annotated animatic output."""

from __future__ import annotations

import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from cine_forge.modules.visualization.animatic_v1.support import (
    normalized_duration,
    render_motion_frame,
    run_ffmpeg,
)
from cine_forge.schemas import MediaFile


def annotate_previz_frame(
    image: Image.Image,
    *,
    scene_heading: str,
    shot_id: str,
    shot_size: str,
    camera_angle: str,
    camera_movement: str,
    characters: list[str],
    edit_intent: str,
    duration_seconds: float,
) -> Image.Image:
    """Overlay a camera/blocking summary onto one preview frame."""
    canvas = image.convert("RGB").copy()
    draw = ImageDraw.Draw(canvas, "RGBA")
    title_font = ImageFont.load_default()
    body_font = ImageFont.load_default()
    width, height = canvas.size

    draw.rounded_rectangle((24, 20, width - 24, 112), radius=16, fill=(8, 12, 20, 212))
    draw.text((40, 34), "ANNOTATED PREVIZ", fill=(244, 247, 255), font=title_font)
    draw.text((40, 58), scene_heading[:72], fill=(210, 222, 255), font=body_font)
    draw.text(
        (40, 82),
        f"{shot_id} | {shot_size} | {camera_angle} | {camera_movement}",
        fill=(172, 190, 220),
        font=body_font,
    )

    draw.rounded_rectangle(
        (24, height - 114, width - 24, height - 24),
        radius=16,
        fill=(8, 12, 20, 220),
    )
    draw.text(
        (40, height - 102),
        f"Blocking: {', '.join(characters) if characters else 'No character labels'}",
        fill=(244, 240, 210),
        font=body_font,
    )
    draw.text(
        (40, height - 78),
        f"Intent: {edit_intent[:88]}",
        fill=(245, 218, 239),
        font=body_font,
    )
    draw.text(
        (40, height - 54),
        f"Pacing: {duration_seconds:.1f}s segment",
        fill=(196, 228, 255),
        font=body_font,
    )

    guide_left = int(width * 0.18)
    guide_top = int(height * 0.12)
    guide_right = int(width * 0.82)
    guide_bottom = int(height * 0.82)
    draw.rectangle(
        (guide_left, guide_top, guide_right, guide_bottom),
        outline=(140, 162, 196, 168),
        width=2,
    )
    return canvas


def compose_annotated_segment_video(
    *,
    ffmpeg: str,
    image_path: Path,
    output_path: Path,
    duration_seconds: float,
    camera_movement: str,
    width: int,
    height: int,
    fps: int,
    scene_heading: str,
    shot_id: str,
    shot_size: str,
    camera_angle: str,
    characters: list[str],
    edit_intent: str,
) -> MediaFile:
    """Compose one deterministic segment with static explanatory overlays."""
    duration = normalized_duration(duration_seconds)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(image_path) as opened_image:
        source_image = opened_image.convert("RGB")

    frame_count = max(int(round(duration * fps)), 2)
    with tempfile.TemporaryDirectory(
        prefix=f"{output_path.stem}_frames_",
        dir=output_path.parent,
    ) as temp_dir_raw:
        temp_dir = Path(temp_dir_raw)
        for frame_idx in range(frame_count):
            progress = frame_idx / (frame_count - 1)
            frame_image = render_motion_frame(
                source_image,
                progress=progress,
                movement=camera_movement,
                width=width,
                height=height,
            )
            annotated = annotate_previz_frame(
                frame_image,
                scene_heading=scene_heading,
                shot_id=shot_id,
                shot_size=shot_size,
                camera_angle=camera_angle,
                camera_movement=camera_movement,
                characters=characters,
                edit_intent=edit_intent,
                duration_seconds=duration,
            )
            annotated.save(temp_dir / f"frame_{frame_idx:05d}.jpg", format="JPEG", quality=90)

        run_ffmpeg(
            [
                ffmpeg,
                "-v",
                "error",
                "-y",
                "-framerate",
                str(fps),
                "-i",
                str(temp_dir / "frame_%05d.jpg"),
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-an",
                str(output_path),
            ]
        )
    return MediaFile(
        relative_path=str(output_path),
        media_type="video/mp4",
        duration_seconds=duration,
    )
