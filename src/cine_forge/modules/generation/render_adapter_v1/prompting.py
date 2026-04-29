"""Prompt synthesis helpers for render_adapter_v1."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from cine_forge.ai.llm import call_llm
from cine_forge.schemas import EnginePack, RenderResolvedInput

GENERIC_META_PROMPT = """\
You are CineForge's render adapter. You are not a creative director and you do not
invent a new interpretation. Your job is to compile upstream film artifacts into a
single high-fidelity video-generation prompt that preserves intent while adapting to
the target engine pack.

Rules:
- Preserve the creative intent already established upstream.
- Prefer concrete physical language over abstract commentary.
- Make camera, blocking, lighting, environment, motion, and sound cues explicit.
- Preserve exact scripted dialogue lines provided by the shot plan verbatim; never
  replace them with summaries such as "delivers the joke" or "responds."
- Mention uploaded references only when they materially guide the model.
- Never ask the target model to do something the engine pack says is unsupported.
- If upstream context is missing, name the gap in `missing_inputs` instead of
  hallucinating details.
- Keep the final `prompt_text` as a single prompt meant to be sent directly to the
  video model.
"""

_CATEGORY_SPECS: dict[str, dict[str, Any]] = {
    "creative_brief": {
        "title": "Creative Brief",
        "source_role_id": "director",
        "source_artifact_types": [],
    },
    "shot_definition": {
        "title": "Shot Definition",
        "source_role_id": "shot_planning",
        "source_artifact_types": ["shot_plan"],
    },
    "look_and_feel": {
        "title": "Look & Feel",
        "source_role_id": "visual_architect",
        "source_artifact_types": ["look_and_feel"],
    },
    "sound_and_music": {
        "title": "Sound & Music",
        "source_role_id": "sound_designer",
        "source_artifact_types": ["sound_and_music"],
    },
    "character_and_performance": {
        "title": "Character & Performance",
        "source_role_id": "story_editor",
        "source_artifact_types": ["character_and_performance"],
    },
    "rhythm_and_flow": {
        "title": "Rhythm & Flow",
        "source_role_id": "editorial_architect",
        "source_artifact_types": ["rhythm_and_flow"],
    },
    "character_bible_state": {
        "title": "Character State",
        "source_role_id": "world_builder",
        "source_artifact_types": ["character_bible", "bible_manifest"],
    },
    "location_bible_state": {
        "title": "Location State",
        "source_role_id": "world_builder",
        "source_artifact_types": ["location_bible", "bible_manifest"],
    },
    "keyframes": {
        "title": "Keyframe Constraints",
        "source_role_id": "visualization",
        "source_artifact_types": ["keyframe"],
    },
    "injected_assets": {
        "title": "Injected Assets",
        "source_role_id": "human",
        "source_artifact_types": ["injected_asset_manifest", "bible_manifest"],
    },
}


class _PromptSectionDraft(BaseModel):
    section_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    body: str = Field(min_length=1)
    source_role_id: str | None = None
    source_artifact_types: list[str] = Field(default_factory=list)


class _PromptDraft(BaseModel):
    prompt_text: str = Field(min_length=1)
    sections: list[_PromptSectionDraft] = Field(default_factory=list, min_length=1)
    covered_categories: list[str] = Field(default_factory=list)
    missing_inputs: list[str] = Field(default_factory=list)
    operator_notes: list[str] = Field(default_factory=list)


def compile_render_prompt(
    *,
    compiler_model: str,
    engine_pack: EnginePack,
    scene_block: str,
    context_blocks: dict[str, str],
    resolved_inputs: list[RenderResolvedInput],
    target_provider: str,
    target_model: str,
    duration_seconds: int,
    resolution: str,
    aspect_ratio: str,
) -> tuple[_PromptDraft, dict[str, Any], list[str]]:
    """Compile one final provider-ready render prompt for a scene."""
    required_categories = [
        category
        for category, content in context_blocks.items()
        if category in _CATEGORY_SPECS and content.strip()
    ]
    prompt = _build_prompt(
        engine_pack=engine_pack,
        scene_block=scene_block,
        context_blocks=context_blocks,
        resolved_inputs=resolved_inputs,
        target_provider=target_provider,
        target_model=target_model,
        duration_seconds=duration_seconds,
        resolution=resolution,
        aspect_ratio=aspect_ratio,
        required_categories=required_categories,
    )
    if compiler_model == "mock":
        return _mock_prompt(context_blocks=context_blocks), _mock_cost(), required_categories
    response, cost = call_llm(
        prompt=prompt,
        model=compiler_model,
        response_schema=_PromptDraft,
        max_tokens=3200,
        temperature=0.2,
    )
    return response, cost, required_categories


def prompt_sources_from_sections(
    sections: list[_PromptSectionDraft],
    resolved_inputs: list[RenderResolvedInput],
) -> list[str]:
    """Compute a stable prompt-source list from prompt sections plus resolved inputs."""
    seen: set[str] = set()
    ordered: list[str] = []
    for section in sections:
        for artifact_type in section.source_artifact_types:
            if artifact_type and artifact_type not in seen:
                seen.add(artifact_type)
                ordered.append(artifact_type)
    for item in resolved_inputs:
        if item.source_ref is None:
            continue
        artifact_type = item.source_ref.artifact_type
        if artifact_type not in seen:
            seen.add(artifact_type)
            ordered.append(artifact_type)
    return ordered


def section_metadata(section_id: str) -> tuple[str | None, list[str]]:
    """Return default role/artifact metadata for a known section id."""
    spec = _CATEGORY_SPECS.get(section_id, {})
    role = spec.get("source_role_id")
    artifact_types = spec.get("source_artifact_types", [])
    return role if isinstance(role, str) else None, list(artifact_types)


def section_title(section_id: str) -> str:
    """Return the canonical display title for a known prompt section id."""
    spec = _CATEGORY_SPECS.get(section_id, {})
    title = spec.get("title")
    if isinstance(title, str) and title.strip():
        return title
    return section_id.replace("_", " ").title()


def known_prompt_categories() -> set[str]:
    """Return the canonical prompt category ids used by the render adapter."""
    return set(_CATEGORY_SPECS)


def _build_prompt(
    *,
    engine_pack: EnginePack,
    scene_block: str,
    context_blocks: dict[str, str],
    resolved_inputs: list[RenderResolvedInput],
    target_provider: str,
    target_model: str,
    duration_seconds: int,
    resolution: str,
    aspect_ratio: str,
    required_categories: list[str],
) -> str:
    blocks: list[str] = [
        GENERIC_META_PROMPT,
        "TARGET OUTPUT:",
        f"- provider: {target_provider}",
        f"- model: {target_model}",
        f"- duration_seconds: {duration_seconds}",
        f"- resolution: {resolution}",
        f"- aspect_ratio: {aspect_ratio}",
        "",
        "ENGINE PACK:",
        f"- pack_id: {engine_pack.pack_id}",
        f"- description: {engine_pack.description}",
        f"- preferred_prompt_style: {engine_pack.preferred_prompt_style}",
        f"- known_strengths: {', '.join(engine_pack.known_strengths) or 'none'}",
        f"- known_limitations: {', '.join(engine_pack.known_limitations) or 'none'}",
        (
            "- supported_inputs: "
            f"first_frame={engine_pack.limits.supports_first_frame}, "
            f"last_frame={engine_pack.limits.supports_last_frame}, "
            f"audio_upload={engine_pack.limits.supports_audio_upload}, "
            f"audio_cues={engine_pack.limits.supports_audio_cues}, "
            f"max_reference_images={engine_pack.limits.max_reference_images}"
        ),
        "",
        "SCENE CONTEXT:",
        scene_block,
    ]

    for category in required_categories:
        content = context_blocks.get(category, "").strip()
        if not content:
            continue
        spec = _CATEGORY_SPECS.get(category, {})
        blocks.extend(
            [
                "",
                f"{spec.get('title', category).upper()}:",
                content,
            ]
        )

    input_lines = ["", "RESOLVED INPUTS:"]
    if not resolved_inputs:
        input_lines.append("- none")
    for item in resolved_inputs:
        source = item.source_ref.artifact_type if item.source_ref is not None else "unknown"
        input_lines.append(
            f"- {item.input_id}: kind={item.kind}; used_as={item.used_as}; "
            f"required={item.required}; "
            f"lock_status={item.lock_status or 'n/a'}; "
            f"source={source}; notes={item.notes or 'none'}"
        )
    blocks.extend(input_lines)

    blocks.extend(
        [
            "",
            "RESPONSE CONTRACT:",
            "- Return JSON only.",
            "- `prompt_text` must be the direct final prompt for the video model.",
            "- `sections` should preserve the major source layers that shaped the final prompt.",
            (
                "- `covered_categories` may only use these ids: "
                f"{', '.join(sorted(_CATEGORY_SPECS))}."
            ),
            (
                "- `missing_inputs` should only name missing categories or hard gaps; do not "
                "report categories that were actually provided."
            ),
            "- If a category has no usable upstream information, omit its section and report it.",
        ]
    )
    return "\n".join(blocks)


def _mock_prompt(*, context_blocks: dict[str, str]) -> _PromptDraft:
    sections: list[_PromptSectionDraft] = []
    covered: list[str] = []
    for category, content in context_blocks.items():
        if category not in _CATEGORY_SPECS or not content.strip():
            continue
        spec = _CATEGORY_SPECS[category]
        sections.append(
            _PromptSectionDraft(
                section_id=category,
                title=str(spec["title"]),
                body=content.splitlines()[0][:240],
                source_role_id=str(spec["source_role_id"]),
                source_artifact_types=list(spec["source_artifact_types"]),
            )
        )
        covered.append(category)
    prompt_lines = [
        "Generate a cinematic scene render that preserves the current upstream intent.",
        "Use explicit shot progression, physical blocking, lighting, and atmosphere.",
    ]
    for section in sections:
        prompt_lines.append(f"{section.title}: {section.body}")
    return _PromptDraft(
        prompt_text="\n".join(prompt_lines),
        sections=sections,
        covered_categories=covered,
        missing_inputs=[],
        operator_notes=["Mock compiler prompt used for local verification."],
    )


def _mock_cost() -> dict[str, Any]:
    return {
        "model": "mock",
        "input_tokens": 0,
        "output_tokens": 0,
        "estimated_cost_usd": 0.0,
        "latency_seconds": 0.0,
        "request_id": "mock-render-prompt",
    }
