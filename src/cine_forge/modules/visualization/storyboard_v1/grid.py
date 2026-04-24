"""Template-backed storyboard grid rendering helpers."""

from __future__ import annotations

import io
import math
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

GRID_PROMPT_MAX_CHARS = 24_000
GRID_PROMPT_BEAT_MAX_CHARS = 700
GRID_PROMPT_PANEL_MAX_CHARS = 1_200
GRID_PROMPT_MIN_ITEM_CHARS = 320


class StoryboardGridLayout:
    """Resolved panel layout for one generated storyboard grid image."""

    def __init__(
        self,
        *,
        columns: int,
        rows: int,
        size: str,
        panel_count: int,
        border_px: int = 8,
        gutter_px: int = 12,
    ) -> None:
        self.columns = columns
        self.rows = rows
        self.size = size
        self.panel_count = panel_count
        self.border_px = border_px
        self.gutter_px = gutter_px

    @property
    def width(self) -> int:
        return int(self.size.split("x", maxsplit=1)[0])

    @property
    def height(self) -> int:
        return int(self.size.split("x", maxsplit=1)[1])

    @property
    def panel_boxes(self) -> list[tuple[int, int, int, int]]:
        panel_width = (
            self.width - (2 * self.border_px) - ((self.columns - 1) * self.gutter_px)
        ) / self.columns
        panel_height = (
            self.height - (2 * self.border_px) - ((self.rows - 1) * self.gutter_px)
        ) / self.rows
        boxes: list[tuple[int, int, int, int]] = []
        for index in range(self.panel_count):
            row = index // self.columns
            column = index % self.columns
            left = round(self.border_px + column * (panel_width + self.gutter_px))
            top = round(self.border_px + row * (panel_height + self.gutter_px))
            right = round(left + panel_width)
            bottom = round(top + panel_height)
            boxes.append((left, top, right, bottom))
        return boxes

    @property
    def content_boxes(self) -> list[tuple[int, int, int, int]]:
        inset = max(18, self.border_px + self.gutter_px)
        return [
            (left + inset, top + inset, right - inset, bottom - inset)
            for left, top, right, bottom in self.panel_boxes
        ]


def resolve_grid_layout(
    *,
    panel_count: int,
    requested_size: str | None = None,
) -> StoryboardGridLayout:
    if panel_count <= 0:
        raise ValueError("storyboard grid requires at least one panel")
    if requested_size is not None:
        columns, rows = _balanced_grid(panel_count)
        return StoryboardGridLayout(
            columns=columns,
            rows=rows,
            size=requested_size,
            panel_count=panel_count,
        )
    if panel_count <= 4:
        return StoryboardGridLayout(columns=2, rows=2, size="1536x1024", panel_count=panel_count)
    if panel_count <= 6:
        return StoryboardGridLayout(columns=3, rows=2, size="1536x1024", panel_count=panel_count)
    if panel_count <= 8:
        return StoryboardGridLayout(columns=2, rows=4, size="1024x1536", panel_count=panel_count)
    columns, rows = _balanced_grid(panel_count)
    return StoryboardGridLayout(
        columns=columns,
        rows=rows,
        size="1536x1024",
        panel_count=panel_count,
    )


def render_grid_template(layout: StoryboardGridLayout, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (layout.width, layout.height), "white")
    draw = ImageDraw.Draw(image)
    for box in layout.panel_boxes:
        draw.rectangle(box, outline="black", width=layout.border_px)
    image.save(path, format="JPEG", quality=95)


def slice_grid_image(
    *,
    image_bytes: bytes,
    layout: StoryboardGridLayout,
    output_paths: list[Path],
) -> None:
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    if image.size != (layout.width, layout.height):
        image = image.resize((layout.width, layout.height))
    for box, output_path in zip(layout.content_boxes, output_paths, strict=True):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.crop(box).save(output_path, format="JPEG", quality=92)


def build_grid_prompt(
    *,
    scene: Any,
    style: str,
    style_instruction: str,
    layout: StoryboardGridLayout,
    panel_briefs: list[str],
    shot_ids: list[str],
    uses_template_reference: bool,
    ordered_story_beats: list[str] | None = None,
) -> str:
    template_line = (
        "Use the supplied blank storyboard grid image as the exact panel layout."
        if uses_template_reference
        else "Create one clean storyboard grid with the exact panel layout requested below."
    )
    lines = [
        (
            "Render one multi-panel storyboard grid image for a single film scene. "
            f"{template_line}"
        ),
        (
            f"Grid layout: {layout.columns} columns x {layout.rows} rows, "
            f"{layout.panel_count} active panels, filled left-to-right then top-to-bottom."
        ),
        f"Scene: {getattr(scene, 'heading', '')}. Style: {style}.",
        f"Visual style instruction: {style_instruction}",
        (
            "Preserve the same character faces, age bands, wardrobe silhouettes, "
            "line treatment, and grayscale storyboard medium across every panel."
        ),
        (
            "Prioritize location and environment specificity: do not replace named "
            "locations with generic rooms, rooftops, streets, or landscapes. If the "
            "briefs mention catwalks, towers, antennas, radios, lanterns, storm, "
            "wind, rain, emergency lights, or dark town scale, make those cues "
            "plainly visible as visual objects and weather, not written labels."
        ),
        (
            "Do not add panel numbers, captions, speech bubbles, subtitles, labels, "
            "slates, UI, watermarks, or any readable text inside the panels."
        ),
        (
            "If a panel brief mentions a sign, radio call sign, whiteboard, note, "
            "map, screen, label, or other written surface, translate it into blank "
            "shapes, lights, diagrams, or illegible scribbles. Never copy words, "
            "letters, numerals, or call signs from the brief into the image."
        ),
        (
            "Keep each panel as a clean full-bleed storyboard drawing inside its own "
            "box. Do not merge panels, skip panels, add extra panels, or create a "
            "comic page with typography."
        ),
    ]
    beat_cap, panel_cap = _prompt_item_budgets(
        base_lines=lines,
        ordered_story_beats=ordered_story_beats or [],
        panel_briefs=panel_briefs,
    )
    if ordered_story_beats:
        lines.extend(
            [
                "",
                "Ordered scene beat router:",
                (
                    "Make the full grid read as one continuous film scene sequence. "
                    "Each active panel must satisfy both its ordered beat and its panel "
                    "brief, moving left-to-right then top-to-bottom."
                ),
            ]
        )
        for beat in ordered_story_beats:
            lines.append(f"- {_compact_prompt_text(beat, beat_cap)}")
    lines.extend(["", "Panel briefs:"])
    for index, (shot_id, brief) in enumerate(zip(shot_ids, panel_briefs, strict=True), start=1):
        lines.extend(
            [
                "",
                f"Panel {index} / shot {shot_id}:",
                _compact_prompt_text(brief, panel_cap),
            ]
        )
    return "\n".join(line.rstrip() for line in lines if line is not None).strip()


def _prompt_item_budgets(
    *,
    base_lines: list[str],
    ordered_story_beats: list[str],
    panel_briefs: list[str],
) -> tuple[int, int]:
    """Keep reference-image edit prompts under OpenAI's practical prompt ceiling."""
    base_len = len("\n".join(base_lines))
    remaining = max(4_000, GRID_PROMPT_MAX_CHARS - base_len - 1_000)
    beat_count = len(ordered_story_beats)
    panel_count = len(panel_briefs)
    if beat_count and panel_count:
        beat_budget = remaining * 2 // 5
        panel_budget = remaining - beat_budget
        return (
            min(
                GRID_PROMPT_BEAT_MAX_CHARS,
                max(GRID_PROMPT_MIN_ITEM_CHARS, beat_budget // beat_count),
            ),
            min(
                GRID_PROMPT_PANEL_MAX_CHARS,
                max(GRID_PROMPT_MIN_ITEM_CHARS, panel_budget // panel_count),
            ),
        )
    if panel_count:
        return (
            GRID_PROMPT_BEAT_MAX_CHARS,
            min(
                GRID_PROMPT_PANEL_MAX_CHARS,
                max(GRID_PROMPT_MIN_ITEM_CHARS, remaining // panel_count),
            ),
        )
    return GRID_PROMPT_BEAT_MAX_CHARS, GRID_PROMPT_PANEL_MAX_CHARS


def _compact_prompt_text(value: str, max_chars: int) -> str:
    text = " ".join(str(value).split())
    if len(text) <= max_chars:
        return text
    cutoff = max(
        text.rfind(". ", 0, max_chars),
        text.rfind("; ", 0, max_chars),
        text.rfind(", ", 0, max_chars),
    )
    if cutoff < max_chars // 2:
        cutoff = max_chars
    return text[:cutoff].rstrip(" ,;.") + "."


def _balanced_grid(panel_count: int) -> tuple[int, int]:
    columns = math.ceil(math.sqrt(panel_count))
    rows = math.ceil(panel_count / columns)
    return columns, rows
