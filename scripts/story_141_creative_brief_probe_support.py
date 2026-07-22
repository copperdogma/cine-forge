"""Deterministic fixture and signal contract for the Story 141 prompt probe."""

from __future__ import annotations

import hashlib
import io
from pathlib import Path
from typing import Any, Literal

from PIL import Image
from pydantic import BaseModel, Field


class LaneJudgment(BaseModel):
    winner: Literal["new", "legacy", "tie"]
    rationale: str
    preserved_signals: list[str] = Field(default_factory=list)
    regressions: list[str] = Field(default_factory=list)


class JudgeVerdict(BaseModel):
    design_study: LaneJudgment
    render_adapter: LaneJudgment
    overall_summary: str


SIGNAL_PATTERNS: dict[str, tuple[str, ...]] = {
    "visual_medium": ("animation 3d", "animation_3d"),
    "mood_descriptors": ("lonely", "ominous"),
    "reference_film": ("the lighthouse",),
    "filmmaker_anchor": ("robert eggers",),
    "look_notes": ("salt-crusted wardrobe", "cold cyan palette"),
    "project_reference_filename": ("storm_palette_board.jpg",),
    "reference_transparency": ("filename/purpose only", "named cue only"),
    "look_and_feel": ("hard monitor highlights", "steel blue"),
}

_LEGACY_FORMAT_STYLE_MODIFIERS: dict[str, str] = {
    "live_action": (
        "Render as live-action film imagery: photorealistic materials, real actors,"
        " cinematic lighting, and natural lens behavior."
    ),
    "animation_2d": (
        "Override the visual medium to 2D animated feature art with hand-drawn linework,"
        " stylized shapes, and flat color fills. Do not render as live-action."
    ),
    "animation_3d": (
        "Override the visual medium to 3D animated feature-film imagery with stylized"
        " physically based rendering, expressive proportions, and polished surface lighting."
        " Do not render as live-action."
    ),
    "anime": (
        "Override the visual medium to anime cel art with crisp linework, stylized facial"
        " language, and vibrant flat colors. Do not render as live-action."
    ),
    "graphic_novel": (
        "Override the visual medium to graphic novel illustration with inked contours,"
        " bold contrast, and printed-page texture. Do not render as photorealistic live-action."
    ),
    "concept_art": (
        "Emphasize exploratory production concept art with painterly ideation, key-art energy,"
        " and art-department visualization rather than final photorealism."
    ),
}


def jpeg_bytes(color: tuple[int, int, int] = (34, 56, 82)) -> bytes:
    buffer = io.BytesIO()
    image = Image.new("RGB", (1280, 720), color=color)
    image.save(buffer, format="JPEG", quality=90)
    return buffer.getvalue()


def signal_presence(text: str) -> dict[str, bool]:
    lowered = text.lower()
    return {
        signal: any(pattern in lowered for pattern in patterns)
        for signal, patterns in SIGNAL_PATTERNS.items()
    }


def deterministic_lane_verdict(legacy_prompt: str, new_prompt: str) -> dict[str, Any]:
    legacy = signal_presence(legacy_prompt)
    new = signal_presence(new_prompt)
    missing_new = sorted(signal for signal, present in new.items() if not present)
    improvements = sorted(
        signal for signal, present in new.items() if present and not legacy[signal]
    )
    return {
        "legacy": legacy,
        "new": new,
        "pass": not missing_new and bool(improvements),
        "missing_new_signals": missing_new,
        "improvements_over_legacy": improvements,
    }


def legacy_project_config_context(project_config_data: dict[str, Any] | None) -> list[str]:
    if not isinstance(project_config_data, dict):
        return []
    lines: list[str] = []
    genres = _string_list(project_config_data.get("genre"))
    tones = _string_list(project_config_data.get("tone"))
    if genres:
        lines.append(f"Genre direction: {', '.join(genres)}.")
    if tones:
        lines.append(f"Tone targets: {', '.join(tones)}.")
    raw_format = project_config_data.get("production_format")
    if isinstance(raw_format, str) and raw_format.strip():
        style_modifier = _LEGACY_FORMAT_STYLE_MODIFIERS.get(raw_format)
        suffix = f" {style_modifier}" if style_modifier else ""
        lines.append(f"Visual medium: {raw_format}.{suffix}")
    return lines


def legacy_intent_mood_context(intent_mood_data: dict[str, Any] | None) -> list[str]:
    if not isinstance(intent_mood_data, dict):
        return []
    lines: list[str] = []
    mood_descriptors = _string_list(intent_mood_data.get("mood_descriptors"))
    if mood_descriptors:
        lines.append(f"Mood descriptors: {', '.join(mood_descriptors)}.")
    reference_films = _string_list(intent_mood_data.get("reference_films"))
    if reference_films:
        lines.append(f"Reference films: {', '.join(reference_films)}.")
    natural_language_intent = intent_mood_data.get("natural_language_intent")
    if isinstance(natural_language_intent, str) and natural_language_intent.strip():
        lines.append(f"Intent brief: {_ensure_sentence(natural_language_intent)}")
    style_preset_id = intent_mood_data.get("style_preset_id")
    if isinstance(style_preset_id, str) and style_preset_id.strip():
        lines.append(f"Style preset: {style_preset_id.strip()}.")
    return lines


def project_fixture() -> tuple[dict[str, Any], dict[str, Any]]:
    return (
        {
            "title": "The Mariner",
            "format": "screenplay",
            "genre": ["nautical drama"],
            "tone": ["bleak", "windswept"],
            "estimated_duration_minutes": 2.0,
            "primary_characters": ["mara"],
            "supporting_characters": ["owen"],
            "location_count": 2,
            "locations_summary": ["harbour", "lighthouse"],
            "target_audience": "adults",
            "aspect_ratio": "2.39:1",
            "production_mode": "ai_generated",
            "production_format": "animation_3d",
            "human_control_mode": "advisory",
            "style_packs": {},
            "budget_cap_usd": 250.0,
            "default_model": "claude-sonnet-4-6",
            "confirmed": True,
        },
        {
            "scope": "project",
            "scene_id": None,
            "mood_descriptors": ["lonely", "ominous"],
            "reference_films": ["The Lighthouse"],
            "filmmaker_anchors": ["Robert Eggers"],
            "style_preset_id": None,
            "natural_language_intent": "Make the world feel ancient and judging.",
            "look_notes": "Salt-crusted wardrobe and cold cyan palette.",
            "user_approved": False,
        },
    )


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _ensure_sentence(value: str) -> str:
    value = value.strip()
    return value if not value or value.endswith((".", "!", "?")) else f"{value}."


def _string_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return [item.strip() for item in values if isinstance(item, str) and item.strip()]
