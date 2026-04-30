"""Shot planning module — scene-level coverage strategy plus shot lists."""

from __future__ import annotations

import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from cine_forge.ai.llm import call_llm
from cine_forge.ai.qa import qa_check
from cine_forge.artifacts import ArtifactStore
from cine_forge.pipeline.scene_actions import filter_scene_entries
from cine_forge.schemas import (
    ArtifactRef,
    ContinuityState,
    CoverageAdequacyCheck,
    CoverageStrategy,
    PlanningAudit,
    ShotDefinition,
    ShotPlan,
    Timeline,
    TimelineEntry,
    TrackEntry,
    TrackManifest,
)

logger = logging.getLogger(__name__)

_SLUG_RE = re.compile(r"[^a-z0-9]+")
_DIALOGUE_PARENTHETICAL_RE = re.compile(r"\([^)]*\)")
_DIALOGUE_NON_WORD_RE = re.compile(r"[^a-z0-9']+")
_PREVIZ_FAST_PROFILE = "previz_fast"
_PREVIZ_FAST_MAX_SHOTS = 5
_COMPACT_VALUE_CHARS = 180
_COMPACT_LIST_ITEMS = 3
_COMPACT_SCENE_SCRIPT_CHARS = 900

_SHOT_PLANNER_PERSONA = """\
You are CineForge's Shot Planner — the point where editorial, visual, sound, performance, \
and continuity decisions become concrete, shootable coverage.

Your job is to turn a scene into a cuttable shot plan that a real editor and set crew could use.
You do not create generic template coverage. Every shot must earn its place in the cut.

Your priorities:
- Coverage first: the scene must be cuttable.
- Creative intent second: camera, framing, blocking, and duration must express the upstream intent.
- Continuity always: shots must respect the current state of characters, props, and locations.
- Specificity over vagueness: blocking, action, and edit intent must be concrete.
"""


class _CoverageResponse(BaseModel):
    coverage_approach: str
    rhythm_and_flow_intent: str
    look_and_feel_intent: str
    sound_and_music_intent: str
    character_and_performance_notes: str
    coverage_patterns: list[str] = Field(default_factory=list)
    adequacy_verdict: str
    adequacy_rationale: str
    missing_coverage_risks: list[str] = Field(default_factory=list)
    rationale: str
    alternatives_considered: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


class _ShotResponse(BaseModel):
    shot_id: str
    shot_size: str
    camera_angle: str
    camera_movement: str
    lens_focal_length: str
    coverage_role: str
    characters_in_frame: list[str] = Field(default_factory=list)
    point_of_view_character: str | None = None
    blocking: str
    action_description: str
    dialogue_lines: list[str] = Field(default_factory=list)
    duration_estimate_seconds: float = Field(ge=0.0)
    edit_intent: str
    rationale: str
    alternatives_considered: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


class _ScenePlanResponse(BaseModel):
    coverage_strategy: _CoverageResponse
    shots: list[_ShotResponse] = Field(default_factory=list, min_length=1)


# Dynamic module loading does not always rebuild postponed annotations automatically.
_ScenePlanResponse.model_rebuild()


class _ScenePlanningContext:
    def __init__(
        self,
        *,
        scene_entry: dict[str, Any],
        scene_artifact: dict[str, Any],
        scene_ref: ArtifactRef,
        scene_text: str,
        timeline_entry: TimelineEntry | None,
        rhythm_and_flow: dict[str, Any],
        look_and_feel: dict[str, Any],
        sound_and_music: dict[str, Any],
        story_world: dict[str, Any] | None,
        intent_mood: dict[str, Any] | None,
        character_bibles: list[dict[str, Any]],
        character_bible_refs: list[ArtifactRef],
        character_performance: list[dict[str, Any]],
        character_performance_refs: list[ArtifactRef],
        continuity_states: list[tuple[ArtifactRef, ContinuityState]],
        upstream_artifact_refs: list[ArtifactRef],
    ) -> None:
        self.scene_entry = scene_entry
        self.scene_artifact = scene_artifact
        self.scene_ref = scene_ref
        self.scene_text = scene_text
        self.timeline_entry = timeline_entry
        self.rhythm_and_flow = rhythm_and_flow
        self.look_and_feel = look_and_feel
        self.sound_and_music = sound_and_music
        self.story_world = story_world
        self.intent_mood = intent_mood
        self.character_bibles = character_bibles
        self.character_bible_refs = character_bible_refs
        self.character_performance = character_performance
        self.character_performance_refs = character_performance_refs
        self.continuity_states = continuity_states
        self.upstream_artifact_refs = upstream_artifact_refs


def run_module(
    inputs: dict[str, Any], params: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    """Generate per-scene shot plans and update timeline/track artifacts."""
    project_dir = context.get("project_dir")
    if not isinstance(project_dir, str) or not project_dir:
        raise ValueError("shot_plan_v1 requires context.project_dir")

    canonical_script = _required_dict(inputs, "normalize")
    scene_index = _required_dict(inputs, "scene_index")
    timeline_payload = _required_dict(inputs, "timeline")
    track_manifest_payload = _required_dict(inputs, "track_manifest")
    continuity_index = (
        inputs.get("continuity_index") if isinstance(inputs.get("continuity_index"), dict) else {}
    )

    store = ArtifactStore(project_dir=Path(project_dir))
    timeline = Timeline.model_validate(timeline_payload)
    track_manifest = TrackManifest.model_validate(track_manifest_payload)

    runtime_params = context.get("runtime_params", {}) if isinstance(context, dict) else {}
    if not isinstance(runtime_params, dict):
        runtime_params = {}

    work_model = (
        params.get("work_model")
        or params.get("model")
        or params.get("default_model")
        or runtime_params.get("work_model")
        or runtime_params.get("default_model")
        or runtime_params.get("model")
        or "claude-sonnet-4-6"
    )
    verify_model = (
        params.get("verify_model")
        or params.get("qa_model")
        or runtime_params.get("verify_model")
        or runtime_params.get("qa_model")
        or params.get("utility_model")
        or "claude-haiku-4-5-20251001"
    )
    escalate_model = (
        params.get("escalate_model")
        or params.get("sota_model")
        or runtime_params.get("escalate_model")
        or runtime_params.get("sota_model")
        or "claude-opus-4-6"
    )
    concurrency = int(params.get("concurrency") or runtime_params.get("concurrency") or 4)
    announce = context.get("announce_artifact")
    intent_mood = inputs.get("intent_mood") if isinstance(inputs.get("intent_mood"), dict) else None
    story_world = inputs.get("story_world") if isinstance(inputs.get("story_world"), dict) else None

    rhythm_by_scene = _scene_map(inputs.get("rhythm_and_flow", []))
    look_by_scene = _scene_map(inputs.get("look_and_feel", []))
    sound_by_scene = _scene_map(inputs.get("sound_and_music", []))
    char_bible_map = _character_bible_map(inputs.get("character_bible", []))
    perf_by_scene, perf_ref_map = _character_performance_map(
        inputs.get("character_and_performance", [])
    )

    scene_entries = filter_scene_entries(scene_index.get("entries", []), runtime_params)
    single_scene_scope = _is_single_scene_scope(runtime_params, scene_entries)
    prompt_profile = (
        str(
            params.get("prompt_profile")
            or runtime_params.get("prompt_profile")
            or (_PREVIZ_FAST_PROFILE if single_scene_scope else "default")
        )
        .strip()
        .lower()
        or "default"
    )
    max_tokens = int(
        params.get("max_tokens")
        or runtime_params.get("max_tokens")
        or (2400 if prompt_profile == _PREVIZ_FAST_PROFILE else 4800)
    )
    max_shots = int(
        params.get("max_shots")
        or runtime_params.get("max_shots")
        or (_PREVIZ_FAST_MAX_SHOTS if prompt_profile == _PREVIZ_FAST_PROFILE else 8)
    )
    skip_qa = bool(params.get("skip_qa", runtime_params.get("skip_qa", False)))
    contexts = [
        _build_scene_context(
            scene_entry=entry,
            canonical_script=canonical_script,
            timeline=timeline,
            store=store,
            rhythm_by_scene=rhythm_by_scene,
            look_by_scene=look_by_scene,
            sound_by_scene=sound_by_scene,
            story_world=story_world,
            intent_mood=intent_mood,
            char_bible_map=char_bible_map,
            perf_by_scene=perf_by_scene,
            perf_ref_map=perf_ref_map,
            continuity_index=continuity_index,
        )
        for entry in scene_entries
    ]

    if not contexts:
        raise ValueError("shot_plan_v1 requires at least one scene entry")

    print(
        f"[shot_planning] Planning {len(contexts)} scenes "
        f"(model={work_model}, concurrency={concurrency})."
    )

    artifacts: list[dict[str, Any]] = []
    shot_plan_refs: dict[str, ArtifactRef] = {}
    shot_plans_by_scene: dict[str, ShotPlan] = {}
    total_cost: dict[str, Any] = {
        "input_tokens": 0,
        "output_tokens": 0,
        "estimated_cost_usd": 0.0,
    }
    models_seen: set[str] = set()

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        future_to_scene = {
            executor.submit(
                _plan_scene,
                scene_context=scene_context,
                work_model=work_model,
                verify_model=verify_model,
                escalate_model=escalate_model,
                skip_qa=skip_qa,
                max_tokens=max_tokens,
                prompt_profile=prompt_profile,
                max_shots=max_shots,
            ): scene_context.scene_entry["scene_id"]
            for scene_context in contexts
        }

        for future in as_completed(future_to_scene):
            scene_id = future_to_scene[future]
            try:
                artifact, shot_plan, cost = future.result()
            except Exception as exc:  # pragma: no cover - defensive log path
                logger.warning("[shot_planning] Failed scene '%s': %s", scene_id, exc)
                continue

            if announce:
                announce(artifact)
            artifact_ref = _shot_plan_ref_for_artifact(store, artifact)
            artifacts.append(artifact)
            shot_plan_refs[scene_id] = artifact_ref
            shot_plans_by_scene[scene_id] = shot_plan
            _update_cost(total_cost, cost)
            model_label = cost.get("model")
            if model_label and model_label != "code":
                models_seen.update(str(model_label).split("+"))

    if not shot_plans_by_scene:
        raise ValueError("shot_plan_v1 produced no scene shot plans")

    artifacts.sort(key=lambda item: str(item.get("entity_id") or ""))

    timeline_ref = _latest_project_ref(store, "timeline")
    if timeline_ref is None:
        raise ValueError("shot_plan_v1 could not resolve latest timeline artifact")
    next_timeline_ref = _anticipated_project_ref(store, "timeline")
    track_manifest_ref = _latest_project_ref(store, "track_manifest")
    if track_manifest_ref is None:
        raise ValueError("shot_plan_v1 could not resolve latest track manifest artifact")

    updated_timeline = _update_timeline_with_shots(timeline, shot_plans_by_scene)
    artifacts.append(
        {
            "artifact_type": "timeline",
            "entity_id": "project",
            "data": updated_timeline.model_dump(mode="json"),
            "include_stage_lineage": True,
            "exclude_upstream_lineage_types": ["track_manifest"],
            "metadata": {
                "lineage": [timeline_ref.model_dump(mode="json")],
                "intent": "Updated project timeline with shot counts and shot IDs.",
                "rationale": (
                    "Shot planning fills the timeline subdivision placeholders created by "
                    "Story 012."
                ),
                "confidence": _average_confidence(shot_plans_by_scene.values()),
                "source": "hybrid",
            },
        }
    )

    updated_manifest = _update_track_manifest_with_shots(
        manifest=track_manifest,
        timeline_ref=next_timeline_ref,
        shot_plans_by_scene=shot_plans_by_scene,
        shot_plan_refs=shot_plan_refs,
    )
    artifacts.append(
        {
            "artifact_type": "track_manifest",
            "entity_id": "project",
            "data": updated_manifest.model_dump(mode="json"),
            "include_stage_lineage": True,
            "metadata": {
                "lineage": [track_manifest_ref.model_dump(mode="json")],
                "intent": "Updated track manifest with shot-level entries on the shots track.",
                "rationale": (
                    "Each planned shot becomes addressable on the shared shots track "
                    "without mutating existing track artifacts in place."
                ),
                "confidence": _average_confidence(shot_plans_by_scene.values()),
                "source": "hybrid",
            },
        }
    )

    total_cost["model"] = "+".join(sorted(models_seen)) if models_seen else "code"
    print(
        f"[shot_planning] Complete: {len(shot_plans_by_scene)} shot plans, "
        f"${total_cost['estimated_cost_usd']:.4f}."
    )
    return {"artifacts": artifacts, "cost": total_cost}


def _plan_scene(
    scene_context: _ScenePlanningContext,
    work_model: str,
    verify_model: str,
    escalate_model: str,
    skip_qa: bool,
    max_tokens: int,
    prompt_profile: str,
    max_shots: int,
) -> tuple[dict[str, Any], ShotPlan, dict[str, Any]]:
    if work_model == "mock":
        plan = _mock_shot_plan(scene_context)
        artifact = _build_shot_plan_artifact(scene_context, plan, source="mock")
        return artifact, plan, {
            "model": "mock",
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": 0.0,
        }

    prompt = _build_scene_prompt(
        scene_context,
        prompt_profile=prompt_profile,
        max_shots=max_shots,
    )
    response, call_cost = call_llm(
        prompt=prompt,
        model=work_model,
        response_schema=_ScenePlanResponse,
        max_tokens=max_tokens,
        temperature=0.2,
    )
    cost: dict[str, Any] = {
        "input_tokens": call_cost.get("input_tokens", 0),
        "output_tokens": call_cost.get("output_tokens", 0),
        "estimated_cost_usd": call_cost.get("estimated_cost_usd", 0.0),
    }
    models_used: set[str] = {str(call_cost.get("model", work_model))}

    if not skip_qa:
        qa_result, qa_cost = qa_check(
            original_input=scene_context.scene_text,
            prompt_used=prompt,
            output_produced=response.model_dump_json(),
            model=verify_model,
            criteria=[
                "coverage adequacy",
                "shot completeness",
                "continuity grounding",
                "creative alignment with upstream direction",
            ],
        )
        _update_cost(cost, qa_cost)
        models_used.add(str(qa_cost.get("model", verify_model)))
        if not qa_result.passed:
            escalate_prompt = _build_scene_prompt(
                scene_context,
                feedback=qa_result.summary,
                prompt_profile=prompt_profile,
                max_shots=max_shots,
            )
            response, esc_cost = call_llm(
                prompt=escalate_prompt,
                model=escalate_model,
                response_schema=_ScenePlanResponse,
                max_tokens=max_tokens,
                temperature=0.2,
            )
            _update_cost(cost, esc_cost)
            models_used.add(str(esc_cost.get("model", escalate_model)))

    plan = _convert_response_to_plan(scene_context, response)
    artifact = _build_shot_plan_artifact(scene_context, plan, source="ai")
    cost["model"] = "+".join(sorted(models_used))
    return artifact, plan, cost


def _convert_response_to_plan(
    scene_context: _ScenePlanningContext,
    response: _ScenePlanResponse,
) -> ShotPlan:
    coverage = CoverageStrategy(
        coverage_approach=response.coverage_strategy.coverage_approach,
        rhythm_and_flow_intent=response.coverage_strategy.rhythm_and_flow_intent,
        look_and_feel_intent=response.coverage_strategy.look_and_feel_intent,
        sound_and_music_intent=response.coverage_strategy.sound_and_music_intent,
        character_and_performance_notes=(
            response.coverage_strategy.character_and_performance_notes
        ),
        coverage_patterns=response.coverage_strategy.coverage_patterns,
        adequacy_check=CoverageAdequacyCheck(
            verdict=_normalize_adequacy_verdict(response.coverage_strategy.adequacy_verdict),
            rationale=response.coverage_strategy.adequacy_rationale,
            missing_coverage_risks=response.coverage_strategy.missing_coverage_risks,
        ),
        audit=PlanningAudit(
            intent="Scene coverage strategy",
            rationale=response.coverage_strategy.rationale,
            alternatives_considered=response.coverage_strategy.alternatives_considered,
            confidence=response.coverage_strategy.confidence,
            source="ai",
        ),
    )

    continuity_refs = _scene_level_continuity_refs(scene_context)
    shots = []
    for shot in response.shots:
        shot_refs = _shot_upstream_refs(scene_context, shot.characters_in_frame)
        shots.append(
            ShotDefinition(
                scene_id=scene_context.scene_entry["scene_id"],
                shot_id=shot.shot_id,
                shot_size=shot.shot_size,
                camera_angle=shot.camera_angle,
                camera_movement=shot.camera_movement,
                lens_focal_length=shot.lens_focal_length,
                coverage_role=shot.coverage_role,
                characters_in_frame=shot.characters_in_frame,
                point_of_view_character=shot.point_of_view_character,
                blocking=shot.blocking,
                action_description=shot.action_description,
                dialogue_lines=shot.dialogue_lines,
                duration_estimate_seconds=shot.duration_estimate_seconds,
                edit_intent=shot.edit_intent,
                continuity_state_refs=_shot_continuity_refs(
                    scene_context,
                    characters_in_frame=shot.characters_in_frame,
                    fallback_refs=continuity_refs,
                ),
                upstream_artifact_refs=shot_refs,
                audit=PlanningAudit(
                    intent=shot.edit_intent,
                    rationale=shot.rationale,
                    alternatives_considered=shot.alternatives_considered,
                    confidence=shot.confidence,
                    source="ai",
                ),
            )
        )

    shots = _dedupe_dialogue_across_shots(shots)
    total_duration = sum(item.duration_estimate_seconds for item in shots)
    return ShotPlan(
        scene_id=scene_context.scene_entry["scene_id"],
        scene_number=int(scene_context.scene_entry.get("scene_number", 1)),
        scene_heading=str(scene_context.scene_entry.get("heading", "Unknown")),
        scene_ref=scene_context.scene_ref,
        coverage_strategy=coverage,
        shots=shots,
        total_estimated_duration_seconds=total_duration,
    )


def _build_shot_plan_artifact(
    scene_context: _ScenePlanningContext,
    plan: ShotPlan,
    source: str,
) -> dict[str, Any]:
    return {
        "artifact_type": "shot_plan",
        "entity_id": plan.scene_id,
        "data": plan.model_dump(mode="json"),
        "schema_name": "shot_plan",
        "exclude_upstream_lineage_types": ["timeline", "track_manifest"],
        "metadata": {
            "lineage": [
                ref.model_dump(mode="json") for ref in scene_context.upstream_artifact_refs
            ],
            "intent": f"Shot plan for {plan.scene_heading}",
            "rationale": (
                "Scene-level coverage strategy plus individual shot definitions grounded in "
                "upstream concern groups, bibles, and continuity state snapshots."
            ),
            "alternatives_considered": plan.coverage_strategy.audit.alternatives_considered,
            "confidence": _plan_confidence(plan),
            "source": "ai" if source != "mock" else "code",
            "annotations": {
                "scene_number": plan.scene_number,
                "shot_count": len(plan.shots),
                "adequacy_verdict": plan.coverage_strategy.adequacy_check.verdict,
            },
        },
    }


def _build_scene_context(
    scene_entry: dict[str, Any],
    canonical_script: dict[str, Any],
    timeline: Timeline,
    store: ArtifactStore,
    rhythm_by_scene: dict[str, dict[str, Any]],
    look_by_scene: dict[str, dict[str, Any]],
    sound_by_scene: dict[str, dict[str, Any]],
    story_world: dict[str, Any] | None,
    intent_mood: dict[str, Any] | None,
    char_bible_map: dict[str, dict[str, Any]],
    perf_by_scene: dict[str, list[dict[str, Any]]],
    perf_ref_map: dict[str, list[ArtifactRef]],
    continuity_index: dict[str, Any],
) -> _ScenePlanningContext:
    scene_id = str(scene_entry.get("scene_id") or "")
    if not scene_id:
        raise ValueError("scene entry missing scene_id")
    scene_ref = _latest_entity_ref(store, "scene", scene_id)
    scene_artifact = store.load_artifact(scene_ref).data
    rhythm = rhythm_by_scene.get(scene_id) or {}
    look = look_by_scene.get(scene_id) or {}
    sound = sound_by_scene.get(scene_id) or {}

    character_ids = _scene_character_ids(scene_entry)
    character_bibles = []
    character_bible_refs = []
    for character_id in character_ids:
        payload = char_bible_map.get(character_id)
        if payload is None:
            continue
        ref = _latest_entity_ref(store, "character_bible", character_id)
        character_bibles.append(payload)
        character_bible_refs.append(ref)

    continuity_states = _continuity_states_for_scene(store, continuity_index, scene_id)
    performance_entries = perf_by_scene.get(scene_id, [])
    performance_refs = perf_ref_map.get(scene_id, [])

    concern_refs: list[ArtifactRef] = []
    if scene_id in rhythm_by_scene:
        concern_refs.append(_latest_entity_ref(store, "rhythm_and_flow", scene_id))
    if scene_id in look_by_scene:
        concern_refs.append(_latest_entity_ref(store, "look_and_feel", scene_id))
    if scene_id in sound_by_scene:
        concern_refs.append(_latest_entity_ref(store, "sound_and_music", scene_id))
    if story_world is not None:
        story_world_ref = _latest_project_ref(store, "story_world")
        if story_world_ref is not None:
            concern_refs.append(story_world_ref)
    if intent_mood is not None:
        intent_ref = _latest_project_ref(store, "intent_mood")
        if intent_ref is not None:
            concern_refs.append(intent_ref)

    upstream_refs = [
        scene_ref,
        *concern_refs,
        *character_bible_refs,
        *performance_refs,
        *[ref for ref, _ in continuity_states],
    ]

    scene_text = _scene_text_from_script(
        script_text=str(canonical_script.get("script_text", "")),
        source_span=scene_entry.get("source_span", {}),
    )
    timeline_entry = next(
        (entry for entry in timeline.entries if entry.scene_id == scene_id),
        None,
    )
    return _ScenePlanningContext(
        scene_entry=scene_entry,
        scene_artifact=scene_artifact,
        scene_ref=scene_ref,
        scene_text=scene_text,
        timeline_entry=timeline_entry,
        rhythm_and_flow=rhythm,
        look_and_feel=look,
        sound_and_music=sound,
        story_world=story_world,
        intent_mood=intent_mood,
        character_bibles=character_bibles,
        character_bible_refs=character_bible_refs,
        character_performance=performance_entries,
        character_performance_refs=performance_refs,
        continuity_states=continuity_states,
        upstream_artifact_refs=_dedupe_refs(upstream_refs),
    )


def _build_scene_prompt(
    scene_context: _ScenePlanningContext,
    feedback: str = "",
    *,
    prompt_profile: str = "default",
    max_shots: int = 8,
) -> str:
    compact = prompt_profile == _PREVIZ_FAST_PROFILE
    feedback_block = f"\nQA FEEDBACK TO FIX:\n{feedback}\n" if feedback else ""
    shot_range = f"3 to {max(3, max_shots)}"
    compact_guidance = (
        "- Keep coverage_strategy fields concise and operator-readable.\n"
        "- Keep shot rationale and edit_intent to one short sentence.\n"
        "- Leave alternatives_considered empty unless a tradeoff materially changes coverage.\n"
        "- Cap coverage_patterns at 4 short items.\n"
    ) if compact else ""
    scene_script = (
        _compact_text(scene_context.scene_text, max_chars=_COMPACT_SCENE_SCRIPT_CHARS)
        if compact
        else scene_context.scene_text
    )
    return (
        f"{_SHOT_PLANNER_PERSONA}\n\n"
        "Return JSON only matching the provided schema.\n"
        "Hard requirements:\n"
        "- Populate EVERY required field in coverage_strategy and in every shot.\n"
        f"- Create {shot_range} shots only.\n"
        "- Use concrete, cuttable coverage patterns.\n"
        "- Do not invent characters, props, or events not supported by the scene.\n"
        "- Treat dialogue_lines as the sequential timing assignment: each exact scripted "
        "speaker/utterance may appear in one planned shot only. If master or reaction "
        "coverage overlaps a line, describe that coverage in action_description or "
        "edit_intent instead of repeating the exact line in dialogue_lines.\n"
        "- Before responding, verify every required field is present and non-empty.\n"
        f"{compact_guidance}"
        f"{feedback_block}\n"
        f"SCENE ID: {scene_context.scene_entry['scene_id']}\n"
        f"SCENE HEADING: {scene_context.scene_entry.get('heading', 'Unknown')}\n\n"
        f"{_intent_block(scene_context.intent_mood, compact=compact)}"
        f"RHYTHM & FLOW:\n{_format_payload(scene_context.rhythm_and_flow, compact=compact)}\n\n"
        f"LOOK & FEEL:\n{_format_payload(scene_context.look_and_feel, compact=compact)}\n\n"
        f"SOUND & MUSIC:\n{_format_payload(scene_context.sound_and_music, compact=compact)}\n\n"
        f"STORY WORLD:\n{_format_payload(scene_context.story_world or {}, compact=compact)}\n\n"
        f"CHARACTER CONTEXT:\n{_character_context(scene_context, compact=compact)}\n\n"
        f"CONTINUITY STATES:\n{_continuity_context(scene_context, compact=compact)}\n\n"
        f"SCENE SCRIPT:\n{scene_script}\n"
    )


def _mock_shot_plan(scene_context: _ScenePlanningContext) -> ShotPlan:
    scene_id = scene_context.scene_entry["scene_id"]
    scene_number = int(scene_context.scene_entry.get("scene_number", 1))
    characters = _scene_character_names(scene_context.scene_entry)
    primary = characters[0] if characters else "Lead"
    secondary = characters[1] if len(characters) > 1 else primary
    continuity_refs = _scene_level_continuity_refs(scene_context)
    base_refs = _shot_upstream_refs(scene_context, characters)
    shots = [
        ShotDefinition(
            scene_id=scene_id,
            shot_id=f"S{scene_number:03d}-A",
            shot_size="Wide Master",
            camera_angle="Eye level",
            camera_movement="Static",
            lens_focal_length="Normal (40-60mm)",
            coverage_role="Master",
            characters_in_frame=characters,
            blocking="Establish the full scene geography and character spacing.",
            action_description="Play the full scene action in a wide safety setup.",
            dialogue_lines=_all_dialogue_lines(scene_context.scene_artifact),
            duration_estimate_seconds=18.0,
            edit_intent="Editorial safety net and geography anchor.",
            continuity_state_refs=continuity_refs,
            upstream_artifact_refs=base_refs,
            audit=PlanningAudit(
                intent="Anchor scene geography",
                rationale="The editor needs a complete version of the scene.",
                alternatives_considered=["Open tighter and reveal space later."],
                confidence=0.82,
                source="code",
            ),
        ),
        ShotDefinition(
            scene_id=scene_id,
            shot_id=f"S{scene_number:03d}-B",
            shot_size="Medium Close-Up",
            camera_angle="Eye level",
            camera_movement="Slow push",
            lens_focal_length="Normal (40-60mm)",
            coverage_role="Single",
            characters_in_frame=[primary],
            blocking=f"Hold {primary} in frame as the emotional driver of the beat.",
            action_description=f"Track {primary}'s reaction and delivery.",
            dialogue_lines=_dialogue_lines_for_character(scene_context.scene_artifact, primary),
            duration_estimate_seconds=10.0,
            edit_intent="Isolate the scene's primary emotional beat.",
            continuity_state_refs=_shot_continuity_refs(
                scene_context, [primary], continuity_refs
            ),
            upstream_artifact_refs=_shot_upstream_refs(scene_context, [primary]),
            audit=PlanningAudit(
                intent="Capture the primary emotional beat",
                rationale="Dialogue scenes need a single on the key speaker.",
                alternatives_considered=["Stay entirely in the master."],
                confidence=0.8,
                source="code",
            ),
        ),
        ShotDefinition(
            scene_id=scene_id,
            shot_id=f"S{scene_number:03d}-C",
            shot_size="Close-Up",
            camera_angle="Eye level",
            camera_movement="Static",
            lens_focal_length="Telephoto (85mm+)",
            coverage_role="Reaction",
            characters_in_frame=[secondary],
            blocking=f"Hold {secondary} nearly still to capture the reaction.",
            action_description=f"Observe {secondary}'s response without cutting away early.",
            dialogue_lines=_dialogue_lines_for_character(scene_context.scene_artifact, secondary),
            duration_estimate_seconds=8.0,
            edit_intent="Give the editor a reaction option and emotional contrast.",
            continuity_state_refs=_shot_continuity_refs(
                scene_context, [secondary], continuity_refs
            ),
            upstream_artifact_refs=_shot_upstream_refs(scene_context, [secondary]),
            audit=PlanningAudit(
                intent="Provide reaction coverage",
                rationale="Reaction coverage gives the edit emotional shape.",
                alternatives_considered=["Cut directly back to the master."],
                confidence=0.78,
                source="code",
            ),
        ),
    ]
    coverage = CoverageStrategy(
        coverage_approach="Master plus selective singles and reaction coverage.",
        rhythm_and_flow_intent=_summary_text(scene_context.rhythm_and_flow),
        look_and_feel_intent=_summary_text(scene_context.look_and_feel),
        sound_and_music_intent=_summary_text(scene_context.sound_and_music),
        character_and_performance_notes=_character_context(scene_context),
        coverage_patterns=["Master", "Single", "Reaction"],
        adequacy_check=CoverageAdequacyCheck(
            verdict="adequate",
            rationale="Master plus selective close coverage gives the editor a clean scene.",
            missing_coverage_risks=[],
        ),
        audit=PlanningAudit(
            intent="Scene coverage strategy",
            rationale="Mock coverage is deterministic but still aims for cuttable variety.",
            alternatives_considered=["Master-only coverage."],
            confidence=0.8,
            source="code",
        ),
    )
    return ShotPlan(
        scene_id=scene_id,
        scene_number=scene_number,
        scene_heading=str(scene_context.scene_entry.get("heading", "Unknown")),
        scene_ref=scene_context.scene_ref,
        coverage_strategy=coverage,
        shots=shots,
        total_estimated_duration_seconds=sum(shot.duration_estimate_seconds for shot in shots),
    )


def _update_timeline_with_shots(
    timeline: Timeline,
    shot_plans_by_scene: dict[str, ShotPlan],
) -> Timeline:
    updated_entries = []
    for entry in timeline.entries:
        plan = shot_plans_by_scene.get(entry.scene_id)
        if plan is None:
            updated_entries.append(entry)
            continue
        updated_entries.append(
            entry.model_copy(
                update={
                    "shot_count": len(plan.shots),
                    "shot_ids": [shot.shot_id for shot in plan.shots],
                }
            )
        )
    return timeline.model_copy(update={"entries": updated_entries})


def _update_track_manifest_with_shots(
    manifest: TrackManifest,
    timeline_ref: ArtifactRef,
    shot_plans_by_scene: dict[str, ShotPlan],
    shot_plan_refs: dict[str, ArtifactRef],
) -> TrackManifest:
    planned_scene_ids = set(shot_plans_by_scene)
    kept_entries = [
        entry
        for entry in manifest.entries
        if not (entry.track_type == "shots" and entry.scene_id in planned_scene_ids)
    ]
    new_entries = list(kept_entries)
    for scene_id in sorted(planned_scene_ids):
        plan = shot_plans_by_scene[scene_id]
        plan_ref = shot_plan_refs[scene_id]
        for idx, shot in enumerate(plan.shots, start=1):
            new_entries.append(
                TrackEntry(
                    track_type="shots",
                    scene_id=scene_id,
                    shot_id=shot.shot_id,
                    artifact_ref=plan_ref,
                    priority=300 + idx,
                    status="available",
                    notes=shot.edit_intent,
                )
            )
    return manifest.model_copy(
        update={
            "timeline_ref": timeline_ref,
            "entries": new_entries,
            "track_fill_counts": _track_counts(new_entries),
        }
    )


def _required_dict(inputs: dict[str, Any], key: str) -> dict[str, Any]:
    payload = inputs.get(key)
    if not isinstance(payload, dict):
        raise ValueError(f"shot_plan_v1 requires '{key}' input")
    return payload


def _scene_map(payload: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(payload, list):
        return {}
    mapped: dict[str, dict[str, Any]] = {}
    for item in payload:
        if not isinstance(item, dict):
            continue
        scene_id = item.get("scene_id")
        if isinstance(scene_id, str) and scene_id:
            mapped[scene_id] = item
    return mapped


def _character_bible_map(payload: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(payload, list):
        return {}
    mapped: dict[str, dict[str, Any]] = {}
    for item in payload:
        if not isinstance(item, dict):
            continue
        character_id = item.get("character_id")
        if not isinstance(character_id, str) or not character_id:
            continue
        mapped[character_id] = item
    return mapped


def _is_single_scene_scope(
    runtime_params: dict[str, Any],
    scene_entries: list[dict[str, Any]],
) -> bool:
    raw_scope = runtime_params.get("scene_scope")
    if not isinstance(raw_scope, dict) or raw_scope.get("mode") != "current_scene":
        return False
    scene_ids = raw_scope.get("scene_ids")
    return (
        isinstance(scene_ids, list)
        and len(scene_ids) == 1
        and len(scene_entries) == 1
        and scene_entries[0].get("scene_id") == scene_ids[0]
    )


def _character_performance_map(
    payload: Any,
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[ArtifactRef]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    refs: dict[str, list[ArtifactRef]] = {}
    if not isinstance(payload, list):
        return grouped, refs
    for item in payload:
        if not isinstance(item, dict):
            continue
        if "entries" in item and isinstance(item.get("scene_id"), str):
            scene_id = item["scene_id"]
            entries = [entry for entry in item.get("entries", []) if isinstance(entry, dict)]
            grouped.setdefault(scene_id, []).extend(entries)
            continue
        scene_id = item.get("scene_id")
        if isinstance(scene_id, str):
            grouped.setdefault(scene_id, []).append(item)
    return grouped, refs


def _continuity_states_for_scene(
    store: ArtifactStore,
    continuity_index: dict[str, Any],
    scene_id: str,
) -> list[tuple[ArtifactRef, ContinuityState]]:
    refs: list[tuple[ArtifactRef, ContinuityState]] = []
    seen: set[str] = set()
    for timeline in continuity_index.get("timelines", {}).values():
        if not isinstance(timeline, dict):
            continue
        for state_id in timeline.get("states", []):
            if not isinstance(state_id, str) or state_id in seen:
                continue
            versions = store.list_versions("continuity_state", state_id)
            if not versions:
                continue
            ref = versions[-1]
            state = ContinuityState.model_validate(store.load_artifact(ref).data)
            if state.scene_id != scene_id:
                continue
            refs.append((ref, state))
            seen.add(state_id)
    return refs


def _scene_text_from_script(script_text: str, source_span: dict[str, Any]) -> str:
    lines = script_text.splitlines()
    start_line = max(int(source_span.get("start_line", 1)) - 1, 0)
    end_line = max(int(source_span.get("end_line", len(lines))), start_line)
    return "\n".join(lines[start_line:end_line]).strip()


def _scene_character_ids(scene_entry: dict[str, Any]) -> list[str]:
    ids = scene_entry.get("characters_present_ids")
    if isinstance(ids, list) and ids:
        return [str(item) for item in ids if isinstance(item, str)]
    return [_slugify(name) for name in _scene_character_names(scene_entry)]


def _scene_character_names(scene_entry: dict[str, Any]) -> list[str]:
    names = scene_entry.get("characters_present", [])
    if not isinstance(names, list):
        return []
    return [str(name) for name in names if isinstance(name, str)]


def _character_context(scene_context: _ScenePlanningContext, *, compact: bool = False) -> str:
    if not scene_context.character_bibles and not scene_context.character_performance:
        return "No character bible or performance notes available."
    lines: list[str] = []
    for bible in scene_context.character_bibles:
        traits = bible.get("inferred_traits", [])
        trait_labels = []
        for item in traits[:2]:
            if isinstance(item, dict) and item.get("trait"):
                trait_labels.append(str(item["trait"]))
        trait_text = f" Traits: {', '.join(trait_labels)}." if trait_labels else ""
        lines.append(
            f"- {bible.get('name', bible.get('character_id', 'Unknown'))}: "
            f"{bible.get('description', '').strip()}{trait_text}"
        )
    for perf in scene_context.character_performance:
        lines.append(
            f"- Performance {perf.get('character_id', 'unknown')}: "
            f"motivation={perf.get('motivation', 'n/a')}; "
            f"subtext={perf.get('subtext', 'n/a')}; "
            f"blocking={perf.get('blocking_notes', 'n/a')}"
        )
    if compact:
        lines = [_compact_text(line, max_chars=_COMPACT_VALUE_CHARS) for line in lines[:4]]
    return "\n".join(lines)


def _continuity_context(scene_context: _ScenePlanningContext, *, compact: bool = False) -> str:
    if not scene_context.continuity_states:
        return "No continuity states available."
    lines: list[str] = []
    states = (
        scene_context.continuity_states[:_COMPACT_LIST_ITEMS]
        if compact
        else scene_context.continuity_states
    )
    for ref, state in states:
        properties = ", ".join(
            f"{prop.key}={prop.value}" for prop in state.properties[: (2 if compact else 4)]
        ) or "no explicit properties"
        lines.append(
            f"- {state.entity_type}:{state.entity_id} [{ref.entity_id}] -> {properties}"
        )
    if compact:
        lines = [_compact_text(line, max_chars=_COMPACT_VALUE_CHARS) for line in lines]
    return "\n".join(lines)


def _intent_block(intent_mood: dict[str, Any] | None, *, compact: bool = False) -> str:
    if not intent_mood:
        return ""
    moods = ", ".join(intent_mood.get("mood_descriptors", [])[: (4 if compact else 6)])
    refs = ", ".join(intent_mood.get("reference_films", [])[: (2 if compact else 4)])
    intent = _compact_text(
        intent_mood.get("natural_language_intent", ""),
        max_chars=_COMPACT_VALUE_CHARS,
    ) if compact else intent_mood.get("natural_language_intent", "")
    return (
        "INTENT & MOOD:\n"
        f"Moods: {moods or 'n/a'}\n"
        f"References: {refs or 'n/a'}\n"
        f"Intent: {intent or 'n/a'}\n\n"
    )


def _format_payload(payload: dict[str, Any], *, compact: bool = False) -> str:
    lines = []
    items = list(payload.items())
    if compact:
        items = items[:5]
    for key, value in items:
        if value in (None, "", [], {}):
            continue
        label = key.replace("_", " ")
        rendered = _render_prompt_value(value, compact=compact)
        lines.append(f"- {label}: {rendered}")
    return "\n".join(lines) or "- No explicit direction."


def _render_prompt_value(value: Any, *, compact: bool) -> str:
    if isinstance(value, list):
        rendered_items: list[str] = []
        limit = _COMPACT_LIST_ITEMS if compact else len(value)
        for item in value[:limit]:
            if isinstance(item, dict):
                rendered_items.append(
                    str(
                        item.get("motif_name")
                        or item.get("description")
                        or item.get("entity_id")
                        or item
                    )
                )
            else:
                rendered_items.append(str(item))
        rendered = ", ".join(
            _compact_text(item, max_chars=80 if compact else 180)
            for item in rendered_items
            if item.strip()
        )
        if compact and len(value) > limit:
            rendered = f"{rendered}, ..."
        return rendered
    if isinstance(value, dict):
        pieces = []
        for key, item in list(value.items())[: (_COMPACT_LIST_ITEMS if compact else len(value))]:
            if item in (None, "", [], {}):
                continue
            pieces.append(
                f"{key}={_compact_text(str(item), max_chars=60 if compact else 140)}"
            )
        return ", ".join(pieces)
    return _compact_text(str(value), max_chars=_COMPACT_VALUE_CHARS if compact else 2000)


def _compact_text(value: Any, *, max_chars: int) -> str:
    normalized = " ".join(str(value or "").split())
    if len(normalized) <= max_chars:
        return normalized
    clipped = normalized[: max_chars - 3].rstrip()
    if " " in clipped:
        clipped = clipped.rsplit(" ", 1)[0]
    return f"{clipped}..."


def _summary_text(payload: dict[str, Any]) -> str:
    return " ".join(
        f"{key.replace('_', ' ')}: {value}."
        for key, value in payload.items()
        if value not in (None, "", [], {})
    ) or "No explicit notes."


def _all_dialogue_lines(scene_artifact: dict[str, Any]) -> list[str]:
    return [
        str(element.get("content", ""))
        for element in scene_artifact.get("elements", [])
        if isinstance(element, dict) and element.get("element_type") == "dialogue"
    ]


def _dialogue_lines_for_character(scene_artifact: dict[str, Any], name: str) -> list[str]:
    lines: list[str] = []
    current_character = None
    for element in scene_artifact.get("elements", []):
        if not isinstance(element, dict):
            continue
        if element.get("element_type") == "character":
            current_character = str(element.get("content", "")).strip()
            continue
        if element.get("element_type") == "dialogue" and current_character == name:
            lines.append(str(element.get("content", "")))
    return lines or _all_dialogue_lines(scene_artifact)[:1]


def _dedupe_dialogue_across_shots(shots: list[ShotDefinition]) -> list[ShotDefinition]:
    last_occurrence: dict[str, int] = {}
    for index, shot in enumerate(shots):
        for line in shot.dialogue_lines:
            key = _dialogue_key(line)
            if key:
                last_occurrence[key] = index

    updated: list[ShotDefinition] = []
    for index, shot in enumerate(shots):
        seen_in_shot: set[str] = set()
        dialogue_lines: list[str] = []
        for line in shot.dialogue_lines:
            key = _dialogue_key(line)
            if not key or key in seen_in_shot or last_occurrence.get(key) != index:
                continue
            seen_in_shot.add(key)
            dialogue_lines.append(line)
        if dialogue_lines == shot.dialogue_lines:
            updated.append(shot)
        else:
            updated.append(shot.model_copy(update={"dialogue_lines": dialogue_lines}))
    return updated


def _dialogue_key(line: str) -> str:
    smart_quotes = str.maketrans(
        {
            "\u2018": "'",
            "\u2019": "'",
            "\u201c": '"',
            "\u201d": '"',
        }
    )
    text = str(line).strip().translate(smart_quotes)
    if not text:
        return ""
    speaker = ""
    utterance = text
    if ":" in text:
        speaker, utterance = text.split(":", 1)
    utterance = _DIALOGUE_PARENTHETICAL_RE.sub(" ", utterance)
    normalized_speaker = _DIALOGUE_NON_WORD_RE.sub(" ", speaker.casefold()).strip()
    normalized_utterance = _DIALOGUE_NON_WORD_RE.sub(" ", utterance.casefold()).strip()
    if not normalized_utterance:
        return ""
    if normalized_speaker:
        return f"{normalized_speaker}:{normalized_utterance}"
    return normalized_utterance


def _shot_upstream_refs(
    scene_context: _ScenePlanningContext,
    characters_in_frame: list[str],
) -> list[ArtifactRef]:
    character_ids = {_slugify(name) for name in characters_in_frame}
    refs = [
        scene_context.scene_ref,
        *[
            ref
            for ref in scene_context.upstream_artifact_refs
            if ref.artifact_type
            in {
                "rhythm_and_flow",
                "look_and_feel",
                "sound_and_music",
                "intent_mood",
            }
        ],
    ]
    for ref in scene_context.character_bible_refs:
        if ref.entity_id in character_ids:
            refs.append(ref)
    for ref in scene_context.character_performance_refs:
        refs.append(ref)
    refs.extend(_scene_level_continuity_refs(scene_context))
    return _dedupe_refs(refs)


def _scene_level_continuity_refs(scene_context: _ScenePlanningContext) -> list[ArtifactRef]:
    return [ref for ref, _ in scene_context.continuity_states]


def _shot_continuity_refs(
    scene_context: _ScenePlanningContext,
    characters_in_frame: list[str],
    fallback_refs: list[ArtifactRef],
) -> list[ArtifactRef]:
    character_ids = {_slugify(name) for name in characters_in_frame}
    refs = []
    for ref, state in scene_context.continuity_states:
        if state.entity_type in {"location", "prop"}:
            refs.append(ref)
            continue
        if state.entity_type == "character" and state.entity_id in character_ids:
            refs.append(ref)
    return _dedupe_refs(refs or fallback_refs)


def _track_counts(entries: list[TrackEntry]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in entries:
        counts[entry.track_type] = counts.get(entry.track_type, 0) + 1
    return counts


def _normalize_adequacy_verdict(verdict: str) -> str:
    normalized = verdict.strip().lower()
    if "inadequate" in normalized:
        return "inadequate"
    if "border" in normalized:
        return "borderline"
    return "adequate"


def _average_confidence(plans: Any) -> float:
    values = [_plan_confidence(plan) for plan in plans]
    return sum(values) / len(values) if values else 0.0


def _plan_confidence(plan: ShotPlan) -> float:
    shot_confidences = [shot.audit.confidence for shot in plan.shots]
    if not shot_confidences:
        return plan.coverage_strategy.audit.confidence
    return (plan.coverage_strategy.audit.confidence + sum(shot_confidences)) / (
        len(shot_confidences) + 1
    )


def _shot_plan_ref_for_artifact(store: ArtifactStore, artifact: dict[str, Any]) -> ArtifactRef:
    if artifact.get("pre_saved_ref"):
        return ArtifactRef.model_validate(artifact["pre_saved_ref"])
    entity_id = artifact.get("entity_id")
    versions = store.list_versions("shot_plan", entity_id)
    next_version = (versions[-1].version + 1) if versions else 1
    entity_key = entity_id or "__project__"
    return ArtifactRef(
        artifact_type="shot_plan",
        entity_id=entity_id,
        version=next_version,
        path=f"artifacts/shot_plan/{entity_key}/v{next_version}.json",
    )


def _latest_project_ref(store: ArtifactStore, artifact_type: str) -> ArtifactRef | None:
    refs = store.list_versions(artifact_type, "project")
    return refs[-1] if refs else None


def _anticipated_project_ref(store: ArtifactStore, artifact_type: str) -> ArtifactRef:
    refs = store.list_versions(artifact_type, "project")
    next_version = (refs[-1].version + 1) if refs else 1
    return ArtifactRef(
        artifact_type=artifact_type,
        entity_id="project",
        version=next_version,
        path=f"artifacts/{artifact_type}/project/v{next_version}.json",
    )


def _latest_entity_ref(store: ArtifactStore, artifact_type: str, entity_id: str) -> ArtifactRef:
    refs = store.list_versions(artifact_type, entity_id)
    if not refs:
        raise ValueError(f"missing '{artifact_type}' artifact for '{entity_id}'")
    return refs[-1]


def _dedupe_refs(refs: list[ArtifactRef]) -> list[ArtifactRef]:
    seen: set[tuple[str, str | None, int, str]] = set()
    deduped: list[ArtifactRef] = []
    for ref in refs:
        key = (ref.artifact_type, ref.entity_id, ref.version, ref.path)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(ref)
    return deduped


def _slugify(value: str) -> str:
    return _SLUG_RE.sub("_", value.strip().lower()).strip("_")


def _update_cost(total: dict[str, Any], call_cost: dict[str, Any]) -> None:
    total["input_tokens"] += call_cost.get("input_tokens", 0)
    total["output_tokens"] += call_cost.get("output_tokens", 0)
    total["estimated_cost_usd"] += call_cost.get("estimated_cost_usd", 0.0)
