"""Compile prompt content while retaining incurred compiler cost immediately."""

from __future__ import annotations

from typing import Any

from cine_forge.artifacts import ArtifactStore
from cine_forge.modules.generation.render_adapter_v1.accounting import record_compiler_cost
from cine_forge.modules.generation.render_adapter_v1.dialogue_contracts import (
    _ensure_dialogue_prompt_contract,
)
from cine_forge.modules.generation.render_adapter_v1.outputs import _empty_cost
from cine_forge.modules.generation.render_adapter_v1.previz_prompting import (
    compile_scene_previz_prompt,
)
from cine_forge.modules.generation.render_adapter_v1.prompt_context import (
    _context_blocks,
    _finalize_prompt_sections,
    _render_clip_plan_notes,
    _scene_block,
)
from cine_forge.modules.generation.render_adapter_v1.prompting import compile_render_prompt
from cine_forge.modules.generation.render_adapter_v1.render_units import render_clip_time_note
from cine_forge.modules.generation.render_adapter_v1.unit_artifacts import build_prompt_artifact
from cine_forge.modules.generation.render_adapter_v1.unit_preparation import PreparedRenderUnit
from cine_forge.schemas import CompiledRenderPrompt, RenderClip, Scene, ShotPlan
from cine_forge.schemas.media_cost import CostReceipt
from cine_forge.schemas.scene_scope import SceneActionPreflight
from cine_forge.services.creative_brief import creative_brief_source_artifact_types


def compile_unit_prompt(
    *,
    store: ArtifactStore,
    scene: Scene,
    plan: ShotPlan,
    source_maps: dict[str, Any],
    engine_pack: Any,
    compiler_model: str,
    output_contract: dict[str, Any],
    scene_action_preflight: SceneActionPreflight | None,
    render_clip: RenderClip | None,
    unit: PreparedRenderUnit,
    cost_receipts: list[CostReceipt],
) -> CompiledRenderPrompt:
    if output_contract["prompt_mode"] == "ai_previz":
        contract, sections, completeness, prompt_sources = compile_scene_previz_prompt(
            scene=scene,
            plan=unit.plan,
            render_clip=render_clip,
            source_maps=source_maps,
            resolved_inputs=unit.resolved_inputs,
            engine_pack=engine_pack,
            consistency_strategy=output_contract["consistency_strategy"],
            prompt_profile=output_contract["prompt_profile"],
        )
        prompt_text = contract.prompt_text
        completeness = completeness.model_copy(update={"notes": [*completeness.notes, *unit.notes]})
        compile_cost = _empty_cost(model="code")
    else:
        prompt_text, sections, completeness, prompt_sources, compile_cost = _compile_render_content(
            scene=scene,
            plan=plan,
            source_maps=source_maps,
            engine_pack=engine_pack,
            compiler_model=compiler_model,
            render_clip=render_clip,
            unit=unit,
            cost_receipts=cost_receipts,
        )
    return build_prompt_artifact(
        store=store,
        scene=scene,
        plan=plan,
        unit=unit,
        render_clip=render_clip,
        source_maps=source_maps,
        engine_pack=engine_pack,
        compiler_model=compiler_model,
        output_contract=output_contract,
        scene_action_preflight=scene_action_preflight,
        compile_cost=compile_cost,
        prompt_text=prompt_text,
        sections=sections,
        completeness=completeness,
        prompt_sources=prompt_sources,
    )


def _compile_render_content(
    *,
    scene: Scene,
    plan: ShotPlan,
    source_maps: dict[str, Any],
    engine_pack: Any,
    compiler_model: str,
    render_clip: RenderClip | None,
    unit: PreparedRenderUnit,
    cost_receipts: list[CostReceipt],
) -> tuple[Any, ...]:
    blocks = _context_blocks(
        scene=scene,
        plan=unit.plan,
        source_maps=source_maps,
        resolved_inputs=unit.resolved_inputs,
        render_clip=render_clip,
    )
    draft, cost, categories = compile_render_prompt(
        compiler_model=compiler_model,
        engine_pack=engine_pack,
        scene_block=_scene_block(scene=scene, plan=unit.plan, render_clip=render_clip),
        context_blocks=blocks,
        resolved_inputs=unit.resolved_inputs,
        target_provider=engine_pack.provider,
        target_model=engine_pack.target_model,
        duration_seconds=unit.duration_seconds,
        resolution=unit.resolution,
        aspect_ratio=unit.aspect_ratio,
    )
    record_compiler_cost(cost_receipts, cost, scene_id=scene.scene_id, entity_id=unit.entity_id)
    sections, completeness, sources = _finalize_prompt_sections(
        prompt_draft=draft,
        required_categories=categories,
        context_blocks=blocks,
        resolved_inputs=unit.resolved_inputs,
        extra_source_artifact_types=creative_brief_source_artifact_types(
            source_maps["creative_brief"]
        ),
        notes=[
            n
            for n in (
                *unit.notes,
                render_clip_time_note(render_clip),
                *_render_clip_plan_notes(
                    source_maps["render_clip_plan"].get(plan.scene_id),
                    unit.duration_seconds,
                    render_clip=render_clip,
                ),
            )
            if n
        ],
    )
    if completeness.blocking_missing_categories:
        raise ValueError(
            f"render_adapter_v1 prompt for {plan.scene_id} is incomplete: "
            f"{', '.join(completeness.blocking_missing_categories)}"
        )
    text, dialogue_notes = _ensure_dialogue_prompt_contract(
        draft.prompt_text,
        unit.plan,
        duration_seconds=float(unit.duration_seconds),
        render_clip=render_clip,
    )
    if dialogue_notes:
        completeness = completeness.model_copy(
            update={"notes": [*completeness.notes, *dialogue_notes]}
        )
    return text, sections, completeness, sources, cost
