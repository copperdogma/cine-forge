"""Deterministic, text-free rendering for synthetic frame packets."""

from __future__ import annotations

import math

from PIL import Image, ImageDraw, ImageFilter
from video_understanding_dataset_model import OUTPUT_SIZE, ClipSpec


def render_frame(spec: ClipSpec, frame_idx: int, total_frames: int) -> Image.Image:
    """Render one source frame without authored labels, titles, or subtitles."""
    progress = frame_idx / max(total_frames - 1, 1)
    image = Image.new("RGB", OUTPUT_SIZE, spec.primary_color)
    draw = ImageDraw.Draw(image)
    _draw_gradient(draw, spec.primary_color, spec.secondary_color)
    _draw_environment(draw, spec, progress)
    _draw_scene_action(draw, spec, progress)

    if "pulsing_light" in spec.target.motion_tags:
        alpha = int(70 * abs(math.sin(progress * math.pi * 4)))
        overlay = Image.new("RGBA", OUTPUT_SIZE, (*spec.accent_color, alpha))
        image = Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")
    if "surreal" in spec.target.tone_tags or spec.scene_kind == "dream":
        image = image.filter(ImageFilter.GaussianBlur(radius=0.7))
    return image


def _draw_gradient(
    draw: ImageDraw.ImageDraw,
    top_color: tuple[int, int, int],
    bottom_color: tuple[int, int, int],
) -> None:
    width, height = OUTPUT_SIZE
    for y in range(height):
        ratio = y / max(height - 1, 1)
        color = tuple(
            int(top_color[index] * (1 - ratio) + bottom_color[index] * ratio) for index in range(3)
        )
        draw.line([(0, y), (width, y)], fill=color)


def _draw_environment(draw: ImageDraw.ImageDraw, spec: ClipSpec, progress: float) -> None:
    width, height = OUTPUT_SIZE
    indoor = {"dialogue", "tracking", "tableau", "vigil", "control_room", "portrait"}
    if spec.scene_kind in indoor:
        draw.rectangle((0, height * 0.68, width, height), fill=(28, 28, 34))
    if spec.scene_kind in {"chase", "panic"}:
        _draw_motion_lines(draw, spec, progress)
    if spec.slug == "alarm_chase_whip_pan":
        _draw_corridor(draw)
    if spec.slug == "rooftop_escape_crash_zoom":
        _draw_rooftops(draw)
    if spec.slug == "storm_tunnel_lateral_run":
        _draw_storm_tunnel(draw, progress)
    if spec.scene_kind == "stylized_city":
        for x in range(20, width, 60):
            draw.line((x, 0, x, height), fill=(100, 100, 135), width=1)
        for y in range(40, height, 40):
            draw.line((0, y, width, y), fill=(100, 100, 135), width=1)
    if spec.scene_kind == "surveillance":
        draw.rectangle((18, 18, width - 18, height - 18), outline=spec.accent_color, width=2)
    if spec.scene_kind in {"memory", "dream"}:
        draw.ellipse((420, 32, 610, 210), outline=spec.accent_color, width=4)
    if spec.scene_kind == "warehouse":
        for x in range(70, width, 120):
            draw.rectangle((x, 80, x + 25, height - 30), fill=(45, 45, 45))
            draw.rectangle((x + 35, 110, x + 60, height - 30), fill=(60, 60, 60))


def _draw_motion_lines(
    draw: ImageDraw.ImageDraw,
    spec: ClipSpec,
    progress: float,
) -> None:
    width, height = OUTPUT_SIZE
    speed = 120 if "fast_lateral" in spec.target.motion_tags else 35
    offset = int(progress * speed)
    for x in range(-60, width + 80, 80):
        draw.line((x - offset, 20, x + 80 - offset, height - 20), fill=(150, 150, 160), width=2)


def _draw_corridor(draw: ImageDraw.ImageDraw) -> None:
    width, height = OUTPUT_SIZE
    draw.line((0, height, width // 2, 100), fill=(180, 65, 65), width=3)
    draw.line((width, height, width // 2, 100), fill=(180, 65, 65), width=3)
    draw.rectangle((260, 85, 380, 270), outline=(155, 40, 40), width=3)


def _draw_rooftops(draw: ImageDraw.ImageDraw) -> None:
    width, height = OUTPUT_SIZE
    draw.rectangle((0, 275, 310, height), fill=(14, 16, 28))
    draw.rectangle((390, 258, width, height), fill=(14, 16, 28))
    draw.line((310, 275, 390, 258), fill=(250, 190, 70), width=2)


def _draw_storm_tunnel(draw: ImageDraw.ImageDraw, progress: float) -> None:
    width, height = OUTPUT_SIZE
    draw.arc((40, 20, width - 40, 420), start=180, end=360, fill=(110, 175, 195), width=4)
    offset = int(progress * 55)
    for x in range(-40, width + 40, 42):
        draw.line((x + offset, 35, x - 25 + offset, 155), fill=(115, 190, 210), width=2)


def _draw_scene_action(draw: ImageDraw.ImageDraw, spec: ClipSpec, progress: float) -> None:
    if spec.scene_kind in {"dialogue", "tracking", "memory"}:
        _draw_two_shot(draw, spec, progress)
    elif spec.scene_kind in {"chase", "panic"}:
        _draw_runner(draw, spec, progress)
    elif spec.scene_kind == "vigil":
        draw.rectangle((140, 180, 430, 250), fill=(105, 112, 130), outline=(230, 230, 230), width=3)
        draw.rectangle((120, 155, 145, 300), fill=(166, 127, 76))
        draw.ellipse((105, 130, 160, 180), fill=spec.accent_color)
        _draw_character(draw, 480, 248, 1.0, spec.accent_color)
    elif spec.scene_kind == "tableau":
        draw.rectangle((150, 170, 500, 230), fill=(96, 82, 72))
        draw.rectangle((130, 230, 520, 280), fill=(70, 52, 43))
    elif spec.scene_kind == "stylized_city":
        draw.polygon([(240, 300), (320, 120), (410, 300)], fill=spec.accent_color)
        draw.rectangle((60, 260, 140, 340), fill=(24, 24, 32))
        draw.rectangle((470, 220, 610, 340), fill=(24, 24, 32))
    elif spec.scene_kind == "surveillance":
        draw.rectangle((270, 120, 370, 280), outline=spec.accent_color, width=3)
        draw.rectangle((305, 160, 335, 280), fill=spec.accent_color)
    elif spec.scene_kind == "portrait":
        _draw_character(draw, 270, 245, 1.25, spec.accent_color)
        draw.line((342, 70, 342, 310), fill=(255, 255, 255), width=3)
        _draw_character(draw, 420, 245, 1.05, tuple(reversed(spec.accent_color)))
    elif spec.scene_kind == "warehouse":
        draw.rectangle((280, 90, 360, 170), fill=(220, 215, 175))
    elif spec.scene_kind == "control_room":
        _draw_control_room(draw, spec)
    elif spec.scene_kind == "dream":
        for radius in range(40, 130, 28):
            draw.ellipse(
                (320 - radius, 180 - radius, 320 + radius, 180 + radius),
                outline=spec.accent_color,
                width=4,
            )
    _draw_prop(draw, spec, progress)


def _draw_two_shot(draw: ImageDraw.ImageDraw, spec: ClipSpec, progress: float) -> None:
    cross_cut = "cross_cut" in spec.target.camera_tags
    left_x = int(170 + (-18 if cross_cut and progress > 0.5 else 0))
    right_x = int(470 + (18 if cross_cut and progress < 0.5 else 0))
    push = 0.16 * progress if "slow_push_in" in spec.target.camera_tags else 0.0
    pull = -0.12 * progress if "slow_pull_back" in spec.target.camera_tags else 0.0
    scale = 1.0 + push + pull
    _draw_character(draw, left_x, 250, scale, spec.accent_color)
    _draw_character(draw, right_x, 250, scale + 0.05, tuple(reversed(spec.accent_color)))


def _draw_runner(draw: ImageDraw.ImageDraw, spec: ClipSpec, progress: float) -> None:
    x = int(120 + progress * 320)
    if "handheld_jitter" in spec.target.camera_tags:
        x += int(math.sin(progress * 60) * 10)
    y = 245 + int(math.sin(progress * math.pi * 4) * 8)
    if spec.slug == "rooftop_escape_crash_zoom":
        y -= int(math.sin(progress * math.pi) * 72)
    scale = 1.0 + (0.3 * progress if "crash_zoom" in spec.target.camera_tags else 0.0)
    _draw_character(draw, x, y, scale, spec.accent_color)


def _draw_control_room(draw: ImageDraw.ImageDraw, spec: ClipSpec) -> None:
    draw.rectangle((80, 70, 240, 150), outline=spec.accent_color, width=3)
    draw.rectangle((255, 60, 385, 140), outline=spec.accent_color, width=3)
    draw.rectangle((400, 70, 560, 150), outline=spec.accent_color, width=3)
    _draw_character(draw, 320, 255, 1.1, spec.accent_color)


def _draw_character(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    scale: float,
    color: tuple[int, int, int],
) -> None:
    body_w = int(40 * scale)
    body_h = int(90 * scale)
    head_r = int(18 * scale)
    draw.ellipse((x - head_r, y - body_h - head_r * 2, x + head_r, y - body_h), fill=color)
    draw.rounded_rectangle((x - body_w, y - body_h, x + body_w, y), radius=14, fill=color)


def _draw_prop(draw: ImageDraw.ImageDraw, spec: ClipSpec, progress: float) -> None:
    if spec.prop_color_start is None:
        return
    color = spec.prop_color_start
    if spec.prop_color_end is not None and progress > 0.5:
        color = spec.prop_color_end
    if spec.scene_kind in {"chase", "panic"}:
        x = int(145 + progress * 320)
        y = 205 + int(math.sin(progress * math.pi * 4) * 8)
        if spec.slug == "rooftop_escape_crash_zoom":
            y -= int(math.sin(progress * math.pi) * 72)
    elif spec.scene_kind == "tableau":
        x, y = 280, 185
    else:
        x, y = 430, 210
    draw.rounded_rectangle(
        (x, y, x + 60, y + 26), radius=6, fill=color, outline=(255, 255, 255), width=2
    )
