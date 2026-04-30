"""AI prompt helpers for render_clip_plan_v1."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from cine_forge.ai.llm import call_llm


class RenderClipPlanningResponseClip(BaseModel):
    """One AI-proposed clip before deterministic validation."""

    source_shot_ids: list[str] = Field(default_factory=list)
    fallback_beat_ids: list[str] = Field(default_factory=list)
    target_duration_seconds: float = Field(gt=0.0)
    dialogue_lines: list[str] = Field(default_factory=list)
    action_beats: list[str] = Field(default_factory=list)
    continuity_start_notes: list[str] = Field(default_factory=list)
    continuity_end_notes: list[str] = Field(default_factory=list)
    reference_intent: list[str] = Field(default_factory=list)
    keyframe_intent: str | None = None
    rationale: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)


class RenderClipPlanningResponse(BaseModel):
    """AI response for scene-level render clip planning."""

    target_dramatic_duration_seconds: float = Field(gt=0.0)
    duration_rationale: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    clips: list[RenderClipPlanningResponseClip] = Field(default_factory=list, min_length=1)


RenderClipPlanningResponse.model_rebuild()


def plan_render_clips_with_ai(
    *,
    model: str,
    scene_context: str,
    engine_pack_id: str,
    engine_max_clip_duration_seconds: float,
    deterministic_lower_bound_seconds: float,
    max_tokens: int,
) -> tuple[RenderClipPlanningResponse, dict[str, Any]]:
    """Ask a model for dramatic scene duration and clip grouping."""
    prompt = _build_prompt(
        scene_context=scene_context,
        engine_pack_id=engine_pack_id,
        engine_max_clip_duration_seconds=engine_max_clip_duration_seconds,
        deterministic_lower_bound_seconds=deterministic_lower_bound_seconds,
    )
    response, cost = call_llm(
        prompt=prompt,
        model=model,
        response_schema=RenderClipPlanningResponse,
        max_tokens=max_tokens,
        temperature=0.2,
    )
    return response, cost


def _build_prompt(
    *,
    scene_context: str,
    engine_pack_id: str,
    engine_max_clip_duration_seconds: float,
    deterministic_lower_bound_seconds: float,
) -> str:
    return (
        "You are CineForge's render clip planner. Your job is to decide how long "
        "the scene should actually play, then split it into video-generation clips "
        "that fit the selected engine.\n\n"
        "Rules:\n"
        "- Preserve dramatic pacing, pauses, reaction beats, and silence. Do not compress "
        "dialogue into rapid-fire delivery just because the engine clips are short.\n"
        "- A render clip is a provider-bounded generation unit, not necessarily one shot.\n"
        "- Every clip target_duration_seconds must be at or below the engine max.\n"
        "- Preserve exact dialogue lines verbatim when assigning them to clips.\n"
        "- Assign each exact speaker/utterance to one clip only. Do not repeat the "
        "same line across clips for overlapping coverage.\n"
        "- Use dialogue_lines as the only place for exact spoken words. action_beats "
        "should describe behavior around the line without quoting it again.\n"
        "- If a long silence or uncomfortable beat is scripted, give it real duration.\n"
        "- Do not invent new story events, characters, or dialogue.\n"
        "- Return JSON only matching the provided schema.\n"
        "- Before responding, verify all required fields are present and every clip "
        "fits the engine duration limit.\n\n"
        "ENGINE CONSTRAINTS:\n"
        f"- engine_pack_id: {engine_pack_id}\n"
        f"- engine_max_clip_duration_seconds: {engine_max_clip_duration_seconds:g}\n"
        f"- deterministic_lower_bound_seconds: {deterministic_lower_bound_seconds:g}\n\n"
        "SCENE CONTEXT:\n"
        f"{scene_context}\n"
    )
