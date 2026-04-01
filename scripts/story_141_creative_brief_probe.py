#!/usr/bin/env python3
"""Story 141 prompt-quality probe for the shared creative-brief seam.

Compares legacy vs current prompt inputs for:
1. Design-study image generation
2. Render-adapter prompt compilation

The deterministic portion checks whether the shared brief preserves the
required taste cues and transparent project-reference participation. The
optional judge step asks a strong model to choose which prompt better preserves
project-level taste while staying honest about metadata-only references.
"""

from __future__ import annotations

import argparse
import io
import json
import tempfile
from pathlib import Path
from typing import Any, Literal

from PIL import Image
from pydantic import BaseModel, Field
from tests.render_fixtures import seed_render_project

from cine_forge.ai.image import (
    _look_and_feel_context,
    build_image_prompt,
    synthesize_image_prompt,
)
from cine_forge.ai.llm import call_llm
from cine_forge.modules.generation.render_adapter_v1.main import (
    _build_source_maps,
    _collect_resolved_inputs,
    _context_blocks,
    _scene_block,
)
from cine_forge.modules.generation.render_adapter_v1.prompting import _build_prompt
from cine_forge.modules.generation.render_adapter_v1.support import load_engine_pack
from cine_forge.schemas import Scene, ShotPlan
from cine_forge.services import InjectedAssetService
from cine_forge.services.creative_brief import build_visual_creative_brief


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


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--judge-model",
        default="claude-opus-4-6",
        help="Model to use for the optional pairwise judge step.",
    )
    parser.add_argument(
        "--skip-judge",
        action="store_true",
        help="Skip the LLM judge and emit deterministic results only.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to write the JSON report.",
    )
    return parser.parse_args()


def _jpeg_bytes(color: tuple[int, int, int] = (34, 56, 82)) -> bytes:
    buffer = io.BytesIO()
    image = Image.new("RGB", (1280, 720), color=color)
    image.save(buffer, format="JPEG", quality=90)
    return buffer.getvalue()


def _contains_any(text: str, patterns: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(pattern in lowered for pattern in patterns)


def _signal_presence(text: str) -> dict[str, bool]:
    return {
        signal: _contains_any(text, patterns)
        for signal, patterns in SIGNAL_PATTERNS.items()
    }


def _ensure_sentence(value: str) -> str:
    value = value.strip()
    if not value:
        return ""
    if value.endswith((".", "!", "?")):
        return value
    return f"{value}."


def _string_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return [item.strip() for item in values if isinstance(item, str) and item.strip()]


def _legacy_project_config_context(project_config_data: dict[str, Any] | None) -> list[str]:
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
        if style_modifier:
            lines.append(f"Visual medium: {raw_format}. {style_modifier}")
        else:
            lines.append(f"Visual medium: {raw_format}.")

    return lines


def _legacy_intent_mood_context(intent_mood_data: dict[str, Any] | None) -> list[str]:
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


def _project_fixture() -> tuple[dict[str, Any], dict[str, Any]]:
    project_config = {
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
    }
    intent_mood = {
        "scope": "project",
        "scene_id": None,
        "mood_descriptors": ["lonely", "ominous"],
        "reference_films": ["The Lighthouse"],
        "filmmaker_anchors": ["Robert Eggers"],
        "style_preset_id": None,
        "natural_language_intent": "Make the world feel ancient and judging.",
        "look_notes": "Salt-crusted wardrobe and cold cyan palette.",
        "user_approved": False,
    }
    return project_config, intent_mood


def _inject_taste_assets(project_dir: Path) -> list[dict[str, Any]]:
    service = InjectedAssetService(project_dir)
    service.inject_asset(
        target_kind="project",
        target_id="project",
        purpose="mood_board",
        filename="storm_palette_board.jpg",
        content=_jpeg_bytes(),
        lock_status="soft_locked",
        content_type="image/jpeg",
    )
    service.inject_asset(
        target_kind="project",
        target_id="project",
        purpose="style_reference",
        filename="salt_crusted_costume_stills.pdf",
        content=b"%PDF-1.4 mock style reference",
        lock_status="hard_locked",
        content_type="application/pdf",
    )

    payloads: list[dict[str, Any]] = []
    for target_kind, target_id in (("project", "project"), ("scene", "scene_001")):
        manifest, _ref = service.load_manifest(target_kind=target_kind, target_id=target_id)
        if manifest is not None:
            payloads.append(manifest.model_dump(mode="json"))
    return payloads


def _design_study_prompts(
    *,
    project_config: dict[str, Any],
    intent_mood: dict[str, Any],
    look_and_feel: dict[str, Any],
    project_manifest: dict[str, Any],
) -> dict[str, Any]:
    entity_bible = {
        "name": "The Harbour",
        "description": "A fog-shrouded Victorian harbour judged by wind and stone.",
        "physical_traits": ["salt-streaked pilings", "cold mist", "black water"],
        "narrative_significance": "The harbour is the story's ancient gatekeeper.",
    }
    brief = build_visual_creative_brief(
        project_config_data=project_config,
        intent_mood_data=intent_mood,
        project_manifest=project_manifest,
    )
    if brief is None:
        raise ValueError("Creative brief probe fixture unexpectedly produced no brief.")

    legacy_parts = [synthesize_image_prompt("location", entity_bible)]
    legacy_parts.extend(_look_and_feel_context(look_and_feel))
    legacy_parts.extend(_legacy_project_config_context(project_config))
    legacy_parts.extend(_legacy_intent_mood_context(intent_mood))
    legacy_prompt = " ".join(part.strip() for part in legacy_parts if part and part.strip())

    new_prompt, new_sources = build_image_prompt(
        "location",
        entity_bible,
        look_and_feel_data=look_and_feel,
        creative_brief_data=brief,
    )
    return {
        "legacy_prompt": legacy_prompt,
        "new_prompt": new_prompt,
        "new_sources_used": new_sources,
        "brief": brief.model_dump(mode="json"),
    }


def _render_prompts(
    *,
    seeded: dict[str, Any],
    project_config: dict[str, Any],
    intent_mood: dict[str, Any],
    injected_manifest_payloads: list[dict[str, Any]],
) -> dict[str, Any]:
    inputs = dict(seeded["inputs"])
    inputs["project_config"] = project_config
    inputs["intent_mood"] = intent_mood
    inputs["injected_asset_manifest"] = injected_manifest_payloads

    source_maps = _build_source_maps(inputs)
    plan = ShotPlan.model_validate(inputs["shot_plan"][0])
    scene = Scene.model_validate(seeded["store"].load_artifact(plan.scene_ref).data)
    keyframe_artifact = source_maps["keyframes"].get(plan.scene_id)
    resolved_inputs = _collect_resolved_inputs(
        store=seeded["store"],
        scene=scene,
        keyframe_artifact=keyframe_artifact,
        source_maps=source_maps,
    )
    new_scene_block = _scene_block(scene=scene, plan=plan)
    legacy_scene_block = new_scene_block
    legacy_intent = intent_mood.get("natural_language_intent")
    if isinstance(legacy_intent, str) and legacy_intent.strip():
        legacy_scene_block += f"\nProject visual intent: {legacy_intent.strip()}"

    new_context_blocks = _context_blocks(
        scene=scene,
        plan=plan,
        source_maps=source_maps,
        resolved_inputs=resolved_inputs,
    )
    legacy_context_blocks = dict(new_context_blocks)
    legacy_context_blocks["creative_brief"] = ""

    engine_pack = load_engine_pack("openai_sora2")
    legacy_prompt = _build_prompt(
        engine_pack=engine_pack,
        scene_block=legacy_scene_block,
        context_blocks=legacy_context_blocks,
        resolved_inputs=resolved_inputs,
        target_provider=engine_pack.provider,
        target_model=engine_pack.target_model,
        duration_seconds=8,
        resolution="1080p",
        aspect_ratio="2.39:1",
        required_categories=[
            category
            for category, content in legacy_context_blocks.items()
            if content.strip()
        ],
    )
    new_prompt = _build_prompt(
        engine_pack=engine_pack,
        scene_block=new_scene_block,
        context_blocks=new_context_blocks,
        resolved_inputs=resolved_inputs,
        target_provider=engine_pack.provider,
        target_model=engine_pack.target_model,
        duration_seconds=8,
        resolution="1080p",
        aspect_ratio="2.39:1",
        required_categories=[
            category
            for category, content in new_context_blocks.items()
            if content.strip()
        ],
    )
    brief = source_maps["creative_brief"]
    return {
        "legacy_prompt": legacy_prompt,
        "new_prompt": new_prompt,
        "new_sources_used": list(brief.sources_used) if brief is not None else [],
        "brief": brief.model_dump(mode="json") if brief is not None else None,
    }


def _judge_prompts(
    *,
    judge_model: str,
    design_study: dict[str, Any],
    render_adapter: dict[str, Any],
) -> dict[str, Any]:
    prompt = f"""\
You are judging Story 141 in CineForge.

Task:
- Compare the legacy prompt vs the new prompt for each consumer lane.
- Pick which version better preserves project-level taste while remaining transparent.
- Transparency matters: project references here are metadata-only. Good prompts may name
  the assets and their bounded role, but must not hallucinate unseen image content.

Required taste signals to look for:
- visual medium
- mood descriptors
- film anchors
- filmmaker anchors
- look notes
- project-reference participation

Consumer 1: design-study image prompt
LEGACY:
{design_study["legacy_prompt"]}

NEW:
{design_study["new_prompt"]}

Consumer 2: render-adapter compiler prompt
LEGACY:
{render_adapter["legacy_prompt"]}

NEW:
{render_adapter["new_prompt"]}
"""
    result, metadata = call_llm(
        prompt=prompt,
        model=judge_model,
        response_schema=JudgeVerdict,
        max_tokens=1200,
        temperature=0.0,
    )
    return {
        "model": judge_model,
        "result": result.model_dump(mode="json"),
        "cost": metadata,
    }


def main() -> None:
    args = _parse_args()
    project_config, intent_mood = _project_fixture()
    look_and_feel = {
        "scene_id": "scene_001",
        "lighting_concept": "Single-source lantern light with hard monitor highlights.",
        "color_palette": "Steel blue, sea-worn cyan, and rust.",
        "camera_personality": "Close, observant, and slightly unstable.",
        "composition_philosophy": "Use practical geometry to trap the subject.",
        "production_design_notes": "Keep the wet docks and chains crowding frame edges.",
    }

    with tempfile.TemporaryDirectory(prefix="story-141-probe-") as tmp_dir:
        tmp_path = Path(tmp_dir)
        render_seed = seed_render_project(
            tmp_path,
            include_keyframe=True,
            include_scene_image=True,
        )
        project_dir = render_seed["project_dir"]
        injected_manifest_payloads = _inject_taste_assets(project_dir)
        project_manifest = next(
            payload
            for payload in injected_manifest_payloads
            if payload.get("target_kind") == "project" and payload.get("target_id") == "project"
        )

        design_study = _design_study_prompts(
            project_config=project_config,
            intent_mood=intent_mood,
            look_and_feel=look_and_feel,
            project_manifest=project_manifest,
        )
        render_adapter = _render_prompts(
            seeded=render_seed,
            project_config=project_config,
            intent_mood=intent_mood,
            injected_manifest_payloads=injected_manifest_payloads,
        )

    report: dict[str, Any] = {
        "story": 141,
        "deterministic_checks": {
            "design_study": {
                "legacy": _signal_presence(design_study["legacy_prompt"]),
                "new": _signal_presence(design_study["new_prompt"]),
                "new_sources_used": design_study["new_sources_used"],
            },
            "render_adapter": {
                "legacy": _signal_presence(render_adapter["legacy_prompt"]),
                "new": _signal_presence(render_adapter["new_prompt"]),
                "new_sources_used": render_adapter["new_sources_used"],
            },
        },
        "artifacts": {
            "design_study_brief": design_study["brief"],
            "render_adapter_brief": render_adapter["brief"],
        },
        "judge": None,
    }

    if not args.skip_judge:
        report["judge"] = _judge_prompts(
            judge_model=args.judge_model,
            design_study=design_study,
            render_adapter=render_adapter,
        )

    output = json.dumps(report, indent=2)
    if args.output is not None:
        args.output.write_text(output + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
