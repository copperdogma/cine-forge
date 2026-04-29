"""Scene render clip planning module."""

from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any

from cine_forge.artifacts import ArtifactStore
from cine_forge.modules.generation.render_adapter_v1.support import load_engine_pack
from cine_forge.modules.generation.render_clip_plan_v1.prompting import (
    RenderClipPlanningResponse,
    RenderClipPlanningResponseClip,
    plan_render_clips_with_ai,
)
from cine_forge.pipeline.scene_actions import filter_scene_entries, filter_scene_payloads
from cine_forge.schemas import (
    ArtifactRef,
    RenderClip,
    RenderClipPlan,
    Scene,
    ShotPlan,
    Timeline,
    TimelineEntry,
    TrackManifest,
)

_WORD_RE = re.compile(r"[A-Za-z0-9']+")
_SILENCE_RE = re.compile(
    r"\b(long silence|uncomfortable silence|silent|pause|reaction beat|long beat|"
    r"go(?:es)? still)\b",
    re.I,
)


class _PlanningContext:
    def __init__(
        self,
        *,
        scene_entry: dict[str, Any],
        scene: Scene,
        scene_ref: ArtifactRef,
        scene_text: str,
        timeline_entry: TimelineEntry | None,
        timeline_ref: ArtifactRef | None,
        track_manifest_ref: ArtifactRef | None,
        shot_plan: ShotPlan | None,
        shot_plan_ref: ArtifactRef | None,
    ) -> None:
        self.scene_entry = scene_entry
        self.scene = scene
        self.scene_ref = scene_ref
        self.scene_text = scene_text
        self.timeline_entry = timeline_entry
        self.timeline_ref = timeline_ref
        self.track_manifest_ref = track_manifest_ref
        self.shot_plan = shot_plan
        self.shot_plan_ref = shot_plan_ref


class _ClipSeed:
    def __init__(
        self,
        *,
        source_shot_ids: list[str] | None = None,
        fallback_beat_ids: list[str] | None = None,
        duration_seconds: float,
        dialogue_lines: list[str] | None = None,
        action_beats: list[str] | None = None,
        continuity_start_notes: list[str] | None = None,
        continuity_end_notes: list[str] | None = None,
        reference_intent: list[str] | None = None,
        keyframe_intent: str | None = None,
        rationale: str,
        confidence: float,
    ) -> None:
        self.source_shot_ids = source_shot_ids or []
        self.fallback_beat_ids = fallback_beat_ids or []
        self.duration_seconds = duration_seconds
        self.dialogue_lines = dialogue_lines or []
        self.action_beats = action_beats or []
        self.continuity_start_notes = continuity_start_notes or []
        self.continuity_end_notes = continuity_end_notes or []
        self.reference_intent = reference_intent or []
        self.keyframe_intent = keyframe_intent
        self.rationale = rationale
        self.confidence = confidence


def run_module(
    inputs: dict[str, Any], params: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    """Estimate dramatic scene duration and persist render clip plans."""
    project_dir_raw = context.get("project_dir")
    if not isinstance(project_dir_raw, str) or not project_dir_raw:
        raise ValueError("render_clip_plan_v1 requires context.project_dir")

    project_dir = Path(project_dir_raw)
    store = ArtifactStore(project_dir=project_dir)
    runtime_params = _runtime_params(context)
    scene_index = _required_dict(inputs, "scene_index")
    timeline = Timeline.model_validate(_required_dict(inputs, "timeline"))
    TrackManifest.model_validate(_required_dict(inputs, "track_manifest"))
    canonical_script = inputs.get("normalize") if isinstance(inputs.get("normalize"), dict) else {}
    shot_plans = _shot_plan_map(inputs.get("shot_plan"), runtime_params=runtime_params)

    engine_pack_id = str(
        params.get("engine_pack_id")
        or runtime_params.get("engine_pack_id")
        or "google_veo31"
    )
    engine_pack = load_engine_pack(engine_pack_id)
    engine_max = float(max(engine_pack.limits.supported_durations_seconds))
    planner_model = str(
        params.get("planner_model")
        or params.get("work_model")
        or runtime_params.get("planner_model")
        or runtime_params.get("work_model")
        or "claude-opus-4-6"
    )
    max_tokens = int(params.get("max_tokens") or runtime_params.get("max_tokens") or 2400)

    scene_entries = filter_scene_entries(scene_index.get("entries", []), runtime_params)
    if not scene_entries:
        raise ValueError("render_clip_plan_v1 requires at least one scene entry")

    timeline_ref = _latest_project_ref(store, "timeline")
    track_manifest_ref = _latest_project_ref(store, "track_manifest")
    artifacts: list[dict[str, Any]] = []
    total_cost = _empty_cost(model=planner_model)
    models_seen: set[str] = set()
    announce = context.get("announce_artifact")

    for scene_entry in scene_entries:
        planning_context = _build_context(
            store=store,
            scene_entry=scene_entry,
            canonical_script=canonical_script,
            timeline=timeline,
            timeline_ref=timeline_ref,
            track_manifest_ref=track_manifest_ref,
            shot_plans=shot_plans,
        )
        plan, cost = _plan_scene(
            planning_context=planning_context,
            planner_model=planner_model,
            max_tokens=max_tokens,
            engine_pack_id=engine_pack.pack_id,
            engine_max_clip_duration_seconds=engine_max,
        )
        artifact = _artifact_dict(plan)
        if announce:
            announce(artifact)
        artifacts.append(artifact)
        _merge_cost(total_cost, cost)
        model_label = str(cost.get("model") or "")
        if model_label and model_label != "code":
            models_seen.update(model_label.split("+"))

    total_cost["model"] = "+".join(sorted(models_seen)) if models_seen else "code"
    return {"artifacts": artifacts, "cost": total_cost}


def _plan_scene(
    *,
    planning_context: _PlanningContext,
    planner_model: str,
    max_tokens: int,
    engine_pack_id: str,
    engine_max_clip_duration_seconds: float,
) -> tuple[RenderClipPlan, dict[str, Any]]:
    lower_bound = _deterministic_lower_bound(planning_context)
    if planner_model in {"mock", "code"}:
        return (
            _code_plan(
                planning_context=planning_context,
                engine_pack_id=engine_pack_id,
                engine_max_clip_duration_seconds=engine_max_clip_duration_seconds,
                lower_bound=lower_bound,
                note="Code-default planner used because planner_model is mock/code.",
            ),
            _empty_cost(model="code"),
        )

    scene_context = _ai_scene_context(
        planning_context=planning_context,
        lower_bound=lower_bound,
    )
    try:
        response, cost = plan_render_clips_with_ai(
            model=planner_model,
            scene_context=scene_context,
            engine_pack_id=engine_pack_id,
            engine_max_clip_duration_seconds=engine_max_clip_duration_seconds,
            deterministic_lower_bound_seconds=lower_bound,
            max_tokens=max_tokens,
        )
        plan = _ai_plan(
            planning_context=planning_context,
            response=response,
            engine_pack_id=engine_pack_id,
            engine_max_clip_duration_seconds=engine_max_clip_duration_seconds,
            lower_bound=lower_bound,
            planner_model=str(cost.get("model") or planner_model),
        )
        return plan, cost
    except Exception as exc:
        return (
            _code_plan(
                planning_context=planning_context,
                engine_pack_id=engine_pack_id,
                engine_max_clip_duration_seconds=engine_max_clip_duration_seconds,
                lower_bound=lower_bound,
                note=f"AI planner failed; code fallback used: {exc}",
            ),
            _empty_cost(model="code"),
        )


def _ai_plan(
    *,
    planning_context: _PlanningContext,
    response: RenderClipPlanningResponse,
    engine_pack_id: str,
    engine_max_clip_duration_seconds: float,
    lower_bound: float,
    planner_model: str,
) -> RenderClipPlan:
    seeds = [_seed_from_ai_clip(clip) for clip in response.clips]
    target_duration = max(
        lower_bound,
        float(response.target_dramatic_duration_seconds),
        sum(seed.duration_seconds for seed in seeds),
    )
    clips = _build_clips(
        scene_id=planning_context.scene.scene_id,
        seeds=_with_duration_padding(
            seeds,
            target_duration=target_duration,
            engine_max_clip_duration_seconds=engine_max_clip_duration_seconds,
        ),
        engine_max_clip_duration_seconds=engine_max_clip_duration_seconds,
        derivation="hybrid" if planning_context.shot_plan else "ai_fallback",
    )
    return _plan_from_clips(
        planning_context=planning_context,
        engine_pack_id=engine_pack_id,
        engine_max_clip_duration_seconds=engine_max_clip_duration_seconds,
        lower_bound=lower_bound,
        duration_rationale=response.duration_rationale,
        confidence=response.confidence,
        source="hybrid" if planning_context.shot_plan else "ai",
        provenance_mode="shot_plan_ai" if planning_context.shot_plan else "fallback_ai",
        planner_model=planner_model,
        clips=clips,
        notes=_missing_upstream_notes(planning_context),
    )


def _code_plan(
    *,
    planning_context: _PlanningContext,
    engine_pack_id: str,
    engine_max_clip_duration_seconds: float,
    lower_bound: float,
    note: str,
) -> RenderClipPlan:
    seeds = _shot_plan_seeds(planning_context) if planning_context.shot_plan else []
    if not seeds:
        seeds = _scene_element_seeds(planning_context)
    target_duration = max(lower_bound, sum(seed.duration_seconds for seed in seeds))
    clips = _build_clips(
        scene_id=planning_context.scene.scene_id,
        seeds=_with_duration_padding(
            seeds,
            target_duration=target_duration,
            engine_max_clip_duration_seconds=engine_max_clip_duration_seconds,
        ),
        engine_max_clip_duration_seconds=engine_max_clip_duration_seconds,
        derivation="shot_plan" if planning_context.shot_plan else "code_default",
    )
    return _plan_from_clips(
        planning_context=planning_context,
        engine_pack_id=engine_pack_id,
        engine_max_clip_duration_seconds=engine_max_clip_duration_seconds,
        lower_bound=lower_bound,
        duration_rationale=_code_duration_rationale(planning_context, lower_bound),
        confidence=0.68 if planning_context.shot_plan else 0.42,
        source="code",
        provenance_mode="shot_plan_code" if planning_context.shot_plan else "fallback_code",
        planner_model=None,
        clips=clips,
        notes=[note, *_missing_upstream_notes(planning_context)],
    )


def _plan_from_clips(
    *,
    planning_context: _PlanningContext,
    engine_pack_id: str,
    engine_max_clip_duration_seconds: float,
    lower_bound: float,
    duration_rationale: str,
    confidence: float,
    source: str,
    provenance_mode: str,
    planner_model: str | None,
    clips: list[RenderClip],
    notes: list[str],
) -> RenderClipPlan:
    target_duration = round(sum(clip.target_duration_seconds for clip in clips), 2)
    return RenderClipPlan(
        scene_id=planning_context.scene.scene_id,
        scene_number=planning_context.scene.scene_number,
        scene_heading=planning_context.scene.heading,
        scene_ref=planning_context.scene_ref,
        shot_plan_ref=planning_context.shot_plan_ref,
        timeline_ref=planning_context.timeline_ref,
        track_manifest_ref=planning_context.track_manifest_ref,
        selected_engine_pack_id=engine_pack_id,
        engine_max_clip_duration_seconds=engine_max_clip_duration_seconds,
        target_dramatic_duration_seconds=target_duration,
        duration_rationale=duration_rationale,
        confidence=max(0.0, min(float(confidence), 1.0)),
        source=source,  # type: ignore[arg-type]
        provenance_mode=provenance_mode,  # type: ignore[arg-type]
        planner_model=planner_model,
        missing_upstream_categories=_missing_upstream_categories(planning_context),
        deterministic_lower_bound_seconds=round(lower_bound, 2),
        clips=clips,
        notes=notes,
    )


def _build_context(
    *,
    store: ArtifactStore,
    scene_entry: dict[str, Any],
    canonical_script: dict[str, Any],
    timeline: Timeline,
    timeline_ref: ArtifactRef | None,
    track_manifest_ref: ArtifactRef | None,
    shot_plans: dict[str, ShotPlan],
) -> _PlanningContext:
    scene_id = str(scene_entry.get("scene_id") or "")
    if not scene_id:
        raise ValueError("render_clip_plan_v1 scene entry missing scene_id")
    scene_ref = _latest_entity_ref(store, "scene", scene_id)
    scene = Scene.model_validate(store.load_artifact(scene_ref).data)
    shot_plan = shot_plans.get(scene_id)
    shot_plan_ref = _latest_entity_ref_optional(store, "shot_plan", scene_id)
    timeline_entry = next((entry for entry in timeline.entries if entry.scene_id == scene_id), None)
    scene_text = _scene_text(
        scene=scene,
        canonical_script=canonical_script,
        scene_entry=scene_entry,
    )
    return _PlanningContext(
        scene_entry=scene_entry,
        scene=scene,
        scene_ref=scene_ref,
        scene_text=scene_text,
        timeline_entry=timeline_entry,
        timeline_ref=timeline_ref,
        track_manifest_ref=track_manifest_ref,
        shot_plan=shot_plan,
        shot_plan_ref=shot_plan_ref if shot_plan is not None else None,
    )


def _deterministic_lower_bound(planning_context: _PlanningContext) -> float:
    dialogue_lines = _dialogue_lines(planning_context)
    dialogue_seconds = _estimated_dialogue_seconds(dialogue_lines)
    action_seconds = _action_count(planning_context) * 2.0
    silence_seconds = _silence_bonus(planning_context)
    script_bound = dialogue_seconds + action_seconds + silence_seconds
    shot_bound = (
        planning_context.shot_plan.total_estimated_duration_seconds
        if planning_context.shot_plan is not None
        else 0.0
    )
    fallback_bound = 4.0 if not dialogue_lines else 6.0
    return round(max(fallback_bound, shot_bound, script_bound), 2)


def _shot_plan_seeds(planning_context: _PlanningContext) -> list[_ClipSeed]:
    if planning_context.shot_plan is None:
        return []
    seeds: list[_ClipSeed] = []
    for shot in planning_context.shot_plan.shots:
        duration = max(
            float(shot.duration_estimate_seconds),
            _estimated_dialogue_seconds(shot.dialogue_lines) + _text_silence_bonus(
                " ".join([shot.action_description, shot.edit_intent])
            ),
            1.5,
        )
        seeds.append(
            _ClipSeed(
                source_shot_ids=[shot.shot_id],
                duration_seconds=duration,
                dialogue_lines=list(shot.dialogue_lines),
                action_beats=[shot.action_description, shot.edit_intent],
                continuity_start_notes=[
                    f"Start from shot {shot.shot_id} continuity state."
                ],
                continuity_end_notes=[f"End ready for the beat after {shot.shot_id}."],
                reference_intent=[shot.coverage_role],
                keyframe_intent=shot.edit_intent,
                rationale=shot.audit.rationale,
                confidence=shot.audit.confidence,
            )
        )
    return seeds


def _scene_element_seeds(planning_context: _PlanningContext) -> list[_ClipSeed]:
    seeds: list[_ClipSeed] = []
    current_character = ""
    beat_number = 1
    for element in planning_context.scene.elements:
        content = element.content.strip()
        if not content:
            continue
        if element.element_type == "character":
            current_character = content
            continue
        if element.element_type == "dialogue":
            line = f"{current_character}: {content}" if current_character else content
            seeds.append(
                _ClipSeed(
                    fallback_beat_ids=[f"beat_{beat_number:03d}"],
                    duration_seconds=max(_estimated_dialogue_seconds([line]), 1.5),
                    dialogue_lines=[line],
                    rationale="Fallback dialogue beat from scene script.",
                    confidence=0.45,
                )
            )
            beat_number += 1
            continue
        if element.element_type in {"action", "shot", "note"}:
            seeds.append(
                _ClipSeed(
                    fallback_beat_ids=[f"beat_{beat_number:03d}"],
                    duration_seconds=max(2.5 + _text_silence_bonus(content), 2.5),
                    action_beats=[content],
                    rationale="Fallback action beat from scene script.",
                    confidence=0.42,
                )
            )
            beat_number += 1
    if not seeds:
        duration = planning_context.timeline_entry.estimated_duration_seconds if (
            planning_context.timeline_entry is not None
        ) else 6.0
        seeds.append(
            _ClipSeed(
                fallback_beat_ids=["beat_001"],
                duration_seconds=min(max(float(duration), 4.0), 12.0),
                action_beats=[planning_context.scene.heading],
                rationale="Fallback scene-heading beat.",
                confidence=0.35,
            )
        )
    return seeds


def _build_clips(
    *,
    scene_id: str,
    seeds: list[_ClipSeed],
    engine_max_clip_duration_seconds: float,
    derivation: str,
) -> list[RenderClip]:
    expanded = _split_overlong_seeds(seeds, engine_max_clip_duration_seconds)
    clips: list[RenderClip] = []
    start = 0.0
    active: list[_ClipSeed] = []
    active_duration = 0.0
    for seed in expanded:
        if active and active_duration + seed.duration_seconds > engine_max_clip_duration_seconds:
            clip, start = _materialize_clip(scene_id, active, start, len(clips) + 1, derivation)
            clips.append(clip)
            active = []
            active_duration = 0.0
        active.append(seed)
        active_duration += seed.duration_seconds
    if active:
        clip, _ = _materialize_clip(scene_id, active, start, len(clips) + 1, derivation)
        clips.append(clip)
    return clips


def _materialize_clip(
    scene_id: str,
    seeds: list[_ClipSeed],
    start: float,
    index: int,
    derivation: str,
) -> tuple[RenderClip, float]:
    duration = round(sum(seed.duration_seconds for seed in seeds), 2)
    end = round(start + duration, 2)
    clip = RenderClip(
        clip_id=f"{scene_id}_clip_{index:03d}",
        scene_id=scene_id,
        source_shot_ids=_dedupe_text(
            shot_id for seed in seeds for shot_id in seed.source_shot_ids
        ),
        fallback_beat_ids=_dedupe_text(
            beat_id for seed in seeds for beat_id in seed.fallback_beat_ids
        ),
        start_time_seconds=round(start, 2),
        end_time_seconds=end,
        target_duration_seconds=duration,
        dialogue_lines=_dedupe_text(
            line for seed in seeds for line in seed.dialogue_lines
        ),
        action_beats=_dedupe_text(
            beat for seed in seeds for beat in seed.action_beats
        ),
        continuity_start_notes=_dedupe_text(
            note for seed in seeds for note in seed.continuity_start_notes
        ),
        continuity_end_notes=_dedupe_text(
            note for seed in seeds for note in seed.continuity_end_notes
        ),
        reference_intent=_dedupe_text(
            item for seed in seeds for item in seed.reference_intent
        ),
        keyframe_intent=next(
            (seed.keyframe_intent for seed in seeds if seed.keyframe_intent),
            None,
        ),
        derivation=derivation,  # type: ignore[arg-type]
        rationale=" / ".join(_dedupe_text(seed.rationale for seed in seeds)),
        confidence=round(sum(seed.confidence for seed in seeds) / len(seeds), 3),
    )
    return clip, end


def _split_overlong_seeds(
    seeds: list[_ClipSeed],
    engine_max_clip_duration_seconds: float,
) -> list[_ClipSeed]:
    expanded: list[_ClipSeed] = []
    for seed in seeds:
        if seed.duration_seconds <= engine_max_clip_duration_seconds:
            expanded.append(seed)
            continue
        part_count = int(math.ceil(seed.duration_seconds / engine_max_clip_duration_seconds))
        remaining_duration = round(seed.duration_seconds, 2)
        for idx in range(part_count):
            remaining_parts = part_count - idx
            part_duration = (
                round(remaining_duration, 2)
                if remaining_parts == 1
                else round(seed.duration_seconds / part_count, 2)
            )
            remaining_duration = round(remaining_duration - part_duration, 2)
            expanded.append(
                _ClipSeed(
                    source_shot_ids=seed.source_shot_ids,
                    fallback_beat_ids=[
                        f"{beat}_part_{idx + 1}" for beat in seed.fallback_beat_ids
                    ] or seed.fallback_beat_ids,
                    duration_seconds=part_duration,
                    dialogue_lines=seed.dialogue_lines if idx == 0 else [],
                    action_beats=seed.action_beats,
                    continuity_start_notes=seed.continuity_start_notes if idx == 0 else [],
                    continuity_end_notes=(
                        seed.continuity_end_notes if idx == part_count - 1 else []
                    ),
                    reference_intent=seed.reference_intent,
                    keyframe_intent=seed.keyframe_intent,
                    rationale=f"{seed.rationale} (split for engine duration cap)",
                    confidence=max(seed.confidence - 0.05, 0.0),
                )
            )
    return expanded


def _with_duration_padding(
    seeds: list[_ClipSeed],
    *,
    target_duration: float,
    engine_max_clip_duration_seconds: float,
) -> list[_ClipSeed]:
    current = sum(seed.duration_seconds for seed in seeds)
    extra = round(max(target_duration - current, 0.0), 2)
    if extra <= 0.05:
        return seeds
    padded = list(seeds)
    pad_index = 1
    while extra > 0.05:
        duration = min(extra, engine_max_clip_duration_seconds)
        padded.append(
            _ClipSeed(
                fallback_beat_ids=[f"pacing_hold_{pad_index:03d}"],
                duration_seconds=round(duration, 2),
                action_beats=["Hold the scripted pause, reaction, or transition beat."],
                rationale="Duration padding added to satisfy the dramatic-duration estimate.",
                confidence=0.4,
            )
        )
        extra = round(extra - duration, 2)
        pad_index += 1
    return padded


def _seed_from_ai_clip(clip: RenderClipPlanningResponseClip) -> _ClipSeed:
    return _ClipSeed(
        source_shot_ids=clip.source_shot_ids,
        fallback_beat_ids=clip.fallback_beat_ids,
        duration_seconds=float(clip.target_duration_seconds),
        dialogue_lines=clip.dialogue_lines,
        action_beats=clip.action_beats,
        continuity_start_notes=clip.continuity_start_notes,
        continuity_end_notes=clip.continuity_end_notes,
        reference_intent=clip.reference_intent,
        keyframe_intent=clip.keyframe_intent,
        rationale=clip.rationale,
        confidence=clip.confidence,
    )


def _ai_scene_context(
    *,
    planning_context: _PlanningContext,
    lower_bound: float,
) -> str:
    lines = [
        f"Scene id: {planning_context.scene.scene_id}",
        f"Scene heading: {planning_context.scene.heading}",
        f"Deterministic lower bound: {lower_bound:g}s",
        "",
        "Scene script:",
        planning_context.scene_text or _scene_elements_text(planning_context.scene),
    ]
    if planning_context.timeline_entry is not None:
        lines.extend(
            [
                "",
                "Timeline:",
                (
                    f"- estimated_duration_seconds: "
                    f"{planning_context.timeline_entry.estimated_duration_seconds:g}"
                ),
                f"- shot_ids: {', '.join(planning_context.timeline_entry.shot_ids) or 'none'}",
            ]
        )
    if planning_context.shot_plan is not None:
        lines.extend(["", "Shot plan:"])
        for shot in planning_context.shot_plan.shots:
            dialogue = "; ".join(shot.dialogue_lines) or "none"
            lines.append(
                f"- {shot.shot_id}: duration={shot.duration_estimate_seconds:g}s; "
                f"role={shot.coverage_role}; action={shot.action_description}; "
                f"dialogue={dialogue}; edit={shot.edit_intent}"
            )
    else:
        lines.extend(["", "Shot plan: missing; create fallback clip boundaries from script."])
    return "\n".join(lines)


def _scene_text(
    *,
    scene: Scene,
    canonical_script: dict[str, Any],
    scene_entry: dict[str, Any],
) -> str:
    script_text = canonical_script.get("script_text")
    if isinstance(script_text, str) and script_text.strip():
        source_span = scene_entry.get("source_span", {})
        if isinstance(source_span, dict):
            lines = script_text.splitlines()
            start_line = max(int(source_span.get("start_line", 1)) - 1, 0)
            end_line = max(int(source_span.get("end_line", len(lines))), start_line)
            text = "\n".join(lines[start_line:end_line]).strip()
            if text:
                return text
    return _scene_elements_text(scene)


def _scene_elements_text(scene: Scene) -> str:
    return "\n".join(
        f"{element.element_type.upper()}: {element.content}"
        for element in scene.elements
        if element.content.strip()
    )


def _dialogue_lines(planning_context: _PlanningContext) -> list[str]:
    if planning_context.shot_plan is not None:
        lines = [line for shot in planning_context.shot_plan.shots for line in shot.dialogue_lines]
        if lines:
            return _dedupe_text(lines)
    lines: list[str] = []
    current_character = ""
    for element in planning_context.scene.elements:
        if element.element_type == "character":
            current_character = element.content.strip()
            continue
        if element.element_type == "dialogue":
            content = element.content.strip()
            lines.append(f"{current_character}: {content}" if current_character else content)
    return _dedupe_text(lines)


def _estimated_dialogue_seconds(dialogue_lines: list[str]) -> float:
    words = 0
    for line in dialogue_lines:
        utterance = line.split(":", 1)[1] if ":" in line else line
        words += len(_WORD_RE.findall(utterance))
    spoken_seconds = words / 2.2 if words else 0.0
    turn_spacing = max(len(dialogue_lines) - 1, 0) * 0.8
    return round(spoken_seconds + turn_spacing, 2)


def _action_count(planning_context: _PlanningContext) -> int:
    if planning_context.shot_plan is not None:
        return len([shot for shot in planning_context.shot_plan.shots if shot.action_description])
    return len(
        [
            element
            for element in planning_context.scene.elements
            if element.element_type in {"action", "shot", "note"} and element.content.strip()
        ]
    )


def _silence_bonus(planning_context: _PlanningContext) -> float:
    texts = [planning_context.scene_text]
    if planning_context.shot_plan is not None:
        for shot in planning_context.shot_plan.shots:
            texts.extend([shot.action_description, shot.edit_intent, shot.audit.rationale])
    return sum(_text_silence_bonus(text) for text in texts)


def _text_silence_bonus(text: str) -> float:
    matches = _SILENCE_RE.findall(text)
    if not matches:
        return 0.0
    return min(8.0, 2.5 + (len(matches) - 1) * 1.5)


def _code_duration_rationale(planning_context: _PlanningContext, lower_bound: float) -> str:
    dialogue_count = len(_dialogue_lines(planning_context))
    action_count = _action_count(planning_context)
    shot_note = (
        f" shot-plan total={planning_context.shot_plan.total_estimated_duration_seconds:g}s;"
        if planning_context.shot_plan is not None
        else " no shot plan available;"
    )
    return (
        "Code fallback estimated scene duration from"
        f"{shot_note} dialogue_lines={dialogue_count}; action_beats={action_count}; "
        f"lower_bound={lower_bound:g}s."
    )


def _artifact_dict(plan: RenderClipPlan) -> dict[str, Any]:
    return {
        "artifact_type": "render_clip_plan",
        "entity_id": plan.scene_id,
        "data": plan.model_dump(mode="json"),
        "exclude_upstream_lineage_types": ["track_manifest"],
        "metadata": {
            "lineage": [
                ref.model_dump(mode="json")
                for ref in _dedupe_refs(
                    [
                        plan.scene_ref,
                        plan.shot_plan_ref,
                        plan.timeline_ref,
                    ]
                )
            ],
            "intent": f"Provider-bounded render clip plan for {plan.scene_heading}.",
            "rationale": plan.duration_rationale,
            "confidence": plan.confidence,
            "source": plan.source,
            "annotations": {
                "scene_number": plan.scene_number,
                "clip_count": len(plan.clips),
                "target_dramatic_duration_seconds": plan.target_dramatic_duration_seconds,
                "engine_pack_id": plan.selected_engine_pack_id,
                "engine_max_clip_duration_seconds": plan.engine_max_clip_duration_seconds,
                "provenance_mode": plan.provenance_mode,
                "missing_upstream_categories": plan.missing_upstream_categories,
            },
        },
    }


def _shot_plan_map(payload: Any, *, runtime_params: dict[str, Any]) -> dict[str, ShotPlan]:
    if not isinstance(payload, list):
        return {}
    plans: dict[str, ShotPlan] = {}
    for item in filter_scene_payloads(payload, runtime_params):
        if not isinstance(item, dict):
            continue
        plan = ShotPlan.model_validate(item)
        plans[plan.scene_id] = plan
    return plans


def _required_dict(inputs: dict[str, Any], key: str) -> dict[str, Any]:
    payload = inputs.get(key)
    if not isinstance(payload, dict):
        raise ValueError(f"render_clip_plan_v1 requires '{key}' input")
    return payload


def _runtime_params(context: dict[str, Any]) -> dict[str, Any]:
    runtime_params = context.get("runtime_params", {}) if isinstance(context, dict) else {}
    return runtime_params if isinstance(runtime_params, dict) else {}


def _missing_upstream_categories(planning_context: _PlanningContext) -> list[str]:
    missing = []
    if planning_context.shot_plan is None:
        missing.append("shot_plan")
    if not planning_context.scene_text.strip():
        missing.append("canonical_script")
    return missing


def _missing_upstream_notes(planning_context: _PlanningContext) -> list[str]:
    missing = _missing_upstream_categories(planning_context)
    if not missing:
        return []
    return [f"Fallback/default planning used missing upstream categories: {', '.join(missing)}."]


def _latest_project_ref(store: ArtifactStore, artifact_type: str) -> ArtifactRef | None:
    refs = store.list_versions(artifact_type, "project")
    return refs[-1] if refs else None


def _latest_entity_ref(store: ArtifactStore, artifact_type: str, entity_id: str) -> ArtifactRef:
    ref = _latest_entity_ref_optional(store, artifact_type, entity_id)
    if ref is None:
        raise ValueError(f"missing '{artifact_type}' artifact for '{entity_id}'")
    return ref


def _latest_entity_ref_optional(
    store: ArtifactStore,
    artifact_type: str,
    entity_id: str,
) -> ArtifactRef | None:
    refs = store.list_versions(artifact_type, entity_id)
    return refs[-1] if refs else None


def _dedupe_refs(refs: list[ArtifactRef | None]) -> list[ArtifactRef]:
    seen: set[str] = set()
    deduped: list[ArtifactRef] = []
    for ref in refs:
        if ref is None or ref.key() in seen:
            continue
        seen.add(ref.key())
        deduped.append(ref)
    return deduped


def _dedupe_text(values: Any) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if not isinstance(value, str):
            continue
        text = value.strip()
        if not text or text in seen:
            continue
        seen.add(text)
        deduped.append(text)
    return deduped


def _empty_cost(model: str) -> dict[str, Any]:
    return {
        "model": model,
        "input_tokens": 0,
        "output_tokens": 0,
        "estimated_cost_usd": 0.0,
        "latency_seconds": 0.0,
        "request_id": None,
    }


def _merge_cost(total: dict[str, Any], cost: dict[str, Any]) -> None:
    total["input_tokens"] += int(cost.get("input_tokens", 0) or 0)
    total["output_tokens"] += int(cost.get("output_tokens", 0) or 0)
    total["estimated_cost_usd"] += float(cost.get("estimated_cost_usd", 0.0) or 0.0)
