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
import json
import tempfile
from pathlib import Path
from typing import Any

from scripts.story_141_creative_brief_probe_support import (
    JudgeVerdict,
    deterministic_lane_verdict,
    file_sha256,
    jpeg_bytes,
    legacy_intent_mood_context,
    legacy_project_config_context,
    project_fixture,
)
from tests.render_fixtures import seed_render_project

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
from cine_forge.services.still_image_prompt_compiler import (
    _look_and_feel_context,
    build_image_prompt,
    synthesize_image_prompt,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--judge-model",
        default="claude-opus-4-6",
        help="Model to use for the optional pairwise judge step.",
    )
    parser.add_argument(
        "--run-judge",
        action="store_true",
        help="Opt in to the paid live LLM judge; default is deterministic-only.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to write the JSON report.",
    )
    return parser.parse_args()


def _inject_taste_assets(project_dir: Path) -> list[dict[str, Any]]:
    service = InjectedAssetService(project_dir)
    service.inject_asset(
        target_kind="project",
        target_id="project",
        purpose="mood_board",
        filename="storm_palette_board.jpg",
        content=jpeg_bytes(),
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
    legacy_parts.extend(legacy_project_config_context(project_config))
    legacy_parts.extend(legacy_intent_mood_context(intent_mood))
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
    project_config, intent_mood = project_fixture()
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

    design_verdict = deterministic_lane_verdict(
        design_study["legacy_prompt"],
        design_study["new_prompt"],
    )
    render_verdict = deterministic_lane_verdict(
        render_adapter["legacy_prompt"],
        render_adapter["new_prompt"],
    )
    repo_root = Path(__file__).resolve().parents[1]
    report: dict[str, Any] = {
        "story": 141,
        "contract_version": "story-141-creative-brief-probe-v2",
        "evidence_scope": (
            "One repo-authored synthetic prompt fixture. Deterministic signal preservation "
            "is regression evidence only; it is not conversational creative-quality or "
            "production-render evidence."
        ),
        "contract_fingerprints": {
            "runner_sha256": file_sha256(Path(__file__).resolve()),
            "support_sha256": file_sha256(
                repo_root / "scripts" / "story_141_creative_brief_probe_support.py"
            ),
        },
        "judge_execution": {
            "requested": args.run_judge,
            "paid_live_call": args.run_judge,
        },
        "deterministic_checks": {
            "design_study": {
                **design_verdict,
                "new_sources_used": design_study["new_sources_used"],
            },
            "render_adapter": {
                **render_verdict,
                "new_sources_used": render_adapter["new_sources_used"],
            },
        },
        "deterministic_pass": bool(design_verdict["pass"] and render_verdict["pass"]),
        "artifacts": {
            "design_study_brief": design_study["brief"],
            "render_adapter_brief": render_adapter["brief"],
        },
        "judge": None,
    }

    if args.run_judge:
        report["judge"] = _judge_prompts(
            judge_model=args.judge_model,
            design_study=design_study,
            render_adapter=render_adapter,
        )

    output = json.dumps(report, indent=2)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
