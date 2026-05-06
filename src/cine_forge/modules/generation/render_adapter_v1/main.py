"""Scene-level render adapter module."""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any

from cine_forge.ai.video import (
    VideoGenerationError,
    VideoGenerationRequest,
    VideoReferenceInput,
    generate_video,
)
from cine_forge.artifacts import ArtifactStore
from cine_forge.modules.generation.render_adapter_v1.previz_prompting import (
    compile_scene_previz_prompt,
)
from cine_forge.modules.generation.render_adapter_v1.prompting import (
    compile_render_prompt,
    known_prompt_categories,
    prompt_sources_from_sections,
    section_metadata,
    section_title,
)
from cine_forge.modules.generation.render_adapter_v1.render_units import (
    clipped_shot_plan,
    remove_dialogue_quotes,
    render_clip_dialogue_lines,
    render_clip_time_note,
    render_unit_entity_id,
    render_unit_kind,
)
from cine_forge.modules.generation.render_adapter_v1.support import (
    anticipated_entity_ref,
    dedupe_refs,
    latest_entity_ref,
    latest_project_ref,
    load_engine_pack,
    media_type_for_image,
    normalize_aspect_ratio,
    normalize_duration_seconds,
    relative_path,
    render_media_dir,
    track_counts,
)
from cine_forge.pipeline.scene_actions import filter_scene_payloads
from cine_forge.schemas import (
    ArtifactRef,
    CharacterAndPerformance,
    CharacterBible,
    CompiledRenderPrompt,
    CostRecord,
    GeneratedVideoArtifact,
    InjectedAssetManifest,
    IntentMood,
    KeyframeArtifact,
    LocationBible,
    LookAndFeel,
    MediaFile,
    PreviewProvenance,
    ProjectConfig,
    RenderClip,
    RenderClipPlan,
    RenderCompletenessCheck,
    RenderPromptSection,
    RenderResolvedInput,
    RhythmAndFlow,
    Scene,
    ShotPlan,
    SoundAndMusic,
    TrackEntry,
    TrackManifest,
)
from cine_forge.schemas.scene_scope import SceneActionPreflight
from cine_forge.services.creative_brief import (
    build_visual_creative_brief,
    creative_brief_source_artifact_types,
)
from cine_forge.services.design_study_backfill import (
    DEFAULT_DESIGN_STUDY_BACKFILL_MODEL,
    DefaultDesignStudyBackfillService,
    read_design_study_state,
)
from cine_forge.services.injected_assets import manifest_entity_id

_SLUG_RE = re.compile(r"[^a-z0-9]+")
_IMAGE_KINDS = {
    "keyframe",
    "scene_injected_image",
    "project_injected_image",
    "character_injected_image",
    "location_injected_image",
    "prop_injected_image",
}
_AUDIO_KINDS = {"scene_injected_audio", "project_injected_audio"}


class GeneratedVideoTrackRef:
    """Internal track-registration carrier for a generated scene or render clip."""

    def __init__(
        self,
        *,
        scene_id: str,
        artifact_ref: ArtifactRef,
        render_clip_id: str | None,
        start_time_seconds: float | None,
        end_time_seconds: float | None,
    ) -> None:
        self.scene_id = scene_id
        self.artifact_ref = artifact_ref
        self.render_clip_id = render_clip_id
        self.start_time_seconds = start_time_seconds
        self.end_time_seconds = end_time_seconds


def run_module(
    inputs: dict[str, Any], params: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    """Compile scene-level render prompts, generate videos, and update the video track."""
    project_dir = _project_dir(context)
    store = ArtifactStore(project_dir=project_dir)
    track_manifest = _track_manifest(inputs)
    runtime_params = _runtime_params(context)
    scene_action_preflight = _scene_action_preflight(runtime_params)
    selected_render_clip_ids = _selected_render_clip_ids(runtime_params)
    shot_plans = _shot_plans(inputs, runtime_params=runtime_params)
    output_contract = _output_contract(params=params, runtime_params=runtime_params)

    engine_pack_id = str(
        params.get("engine_pack_id")
        or runtime_params.get("engine_pack_id")
        or output_contract["default_engine_pack_id"]
    )
    compiler_model = str(
        params.get("compiler_model")
        or runtime_params.get("compiler_model")
        or output_contract["default_compiler_model"]
    )
    default_design_study_backfill = _default_design_study_backfill_enabled(
        params=params,
        runtime_params=runtime_params,
    )
    default_design_study_backfill_model = _default_design_study_backfill_model(
        params=params,
        runtime_params=runtime_params,
        compiler_model=compiler_model,
    )
    requested_duration_seconds = float(
        params.get("duration_seconds") or runtime_params.get("duration_seconds") or 8.0
    )
    requested_resolution = _optional_string(
        params.get("resolution") or runtime_params.get("resolution")
    )
    requested_aspect_ratio = _optional_string(
        params.get("aspect_ratio") or runtime_params.get("aspect_ratio")
    )
    engine_pack = load_engine_pack(engine_pack_id)
    source_maps = _build_source_maps(inputs)
    _ensure_required_render_clip_plans(
        params=params,
        context=context,
        shot_plans=shot_plans,
        source_maps=source_maps,
    )
    announce_artifact = _artifact_announcer(context)

    artifacts: list[dict[str, Any]] = []
    total_cost = _empty_cost(model=compiler_model)
    generated_refs: list[GeneratedVideoTrackRef] = []
    render_failures: list[dict[str, Any]] = []
    planned_render_count = 0

    for plan in sorted(shot_plans, key=lambda item: item.scene_number):
        scene_artifact = store.load_artifact(plan.scene_ref)
        scene = Scene.model_validate(scene_artifact.data)
        planned_render_count += _planned_render_unit_count(
            plan=plan,
            source_maps=source_maps,
            output_contract=output_contract,
            selected_render_clip_ids=selected_render_clip_ids,
        )
        scene_outputs, scene_failures = _render_scene_outputs(
            store=store,
            scene=scene,
            plan=plan,
            source_maps=source_maps,
            engine_pack=engine_pack,
            compiler_model=compiler_model,
            requested_duration_seconds=requested_duration_seconds,
            requested_resolution=requested_resolution,
            requested_aspect_ratio=requested_aspect_ratio,
            output_contract=output_contract,
            scene_action_preflight=scene_action_preflight,
            selected_render_clip_ids=selected_render_clip_ids,
            default_design_study_backfill=default_design_study_backfill,
            default_design_study_backfill_model=default_design_study_backfill_model,
        )
        for failure in scene_failures:
            render_failures.append(failure)
            unit_label = (
                f"{failure['scene_id']}:{failure['render_clip_id']}"
                if failure.get("render_clip_id")
                else failure["scene_id"]
            )
            print(
                "[render_adapter] Failed "
                f"{unit_label} with {engine_pack.pack_id}: {failure['error']}"
            )

        for prompt_artifact, video_artifact, cost in scene_outputs:
            _announce_artifact(announce_artifact, prompt_artifact)
            video_ref = _announce_artifact(announce_artifact, video_artifact)
            if video_ref is None:
                video_ref = anticipated_entity_ref(
                    store,
                    output_contract["video_artifact_type"],
                    str(video_artifact["entity_id"]),
                )
            generated_video = GeneratedVideoArtifact.model_validate(video_artifact["data"])
            generated_refs.append(
                GeneratedVideoTrackRef(
                    scene_id=generated_video.scene_id,
                    artifact_ref=video_ref,
                    render_clip_id=generated_video.render_clip_id,
                    start_time_seconds=generated_video.render_clip_start_time_seconds,
                    end_time_seconds=generated_video.render_clip_end_time_seconds,
                )
            )
            artifacts.extend([prompt_artifact, video_artifact])
            _merge_cost(total_cost, cost)
            unit_label = (
                f"{generated_video.scene_id}:{generated_video.render_clip_id}"
                if generated_video.render_clip_id
                else generated_video.scene_id
            )
            print(
                "[render_adapter] Compiled and rendered "
                f"{unit_label} as {output_contract['video_artifact_type']} "
                f"with {engine_pack.pack_id}."
            )

    if not generated_refs and render_failures:
        if len(render_failures) == 1:
            raise render_failures[0]["exception"]
        raise RuntimeError(
            _render_failure_summary(
                failures=render_failures,
                success_count=0,
                total_count=planned_render_count or len(shot_plans),
            )
        )

    track_manifest_ref = latest_project_ref(store, "track_manifest")
    if track_manifest_ref is None:
        raise ValueError("render_adapter_v1 could not resolve latest track_manifest artifact")

    updated_manifest = _update_track_manifest_with_video_track(
        manifest=track_manifest,
        generated_video_refs=generated_refs,
        track_type=output_contract["track_type"],
        priority=output_contract["track_priority"],
        notes=output_contract["track_note"],
    )
    track_manifest_artifact = _track_manifest_artifact_dict(
        updated_manifest=updated_manifest,
        track_manifest_ref=track_manifest_ref,
        generated_video_refs=generated_refs,
    )
    _announce_artifact(announce_artifact, track_manifest_artifact)
    artifacts.append(track_manifest_artifact)

    if render_failures:
        raise RuntimeError(
            _render_failure_summary(
                failures=render_failures,
                success_count=len(generated_refs),
                total_count=planned_render_count or len(shot_plans),
            )
        )
    return {"artifacts": artifacts, "cost": total_cost}


def _render_scene_outputs(
    *,
    store: ArtifactStore,
    scene: Scene,
    plan: ShotPlan,
    source_maps: dict[str, Any],
    engine_pack: Any,
    compiler_model: str,
    requested_duration_seconds: float,
    requested_resolution: str | None,
    requested_aspect_ratio: str | None,
    output_contract: dict[str, Any],
    scene_action_preflight: SceneActionPreflight | None,
    selected_render_clip_ids: set[str] | None,
    default_design_study_backfill: bool,
    default_design_study_backfill_model: str,
) -> tuple[list[tuple[dict[str, Any], dict[str, Any], dict[str, Any]]], list[dict[str, Any]]]:
    render_clip_plan = source_maps["render_clip_plan"].get(plan.scene_id)
    render_clips = _render_clips_for_scene(
        scene_id=plan.scene_id,
        render_clip_plan=render_clip_plan,
        output_contract=output_contract,
        selected_render_clip_ids=selected_render_clip_ids,
    )
    outputs: list[tuple[dict[str, Any], dict[str, Any], dict[str, Any]]] = []
    failures: list[dict[str, Any]] = []
    if default_design_study_backfill:
        _backfill_default_design_studies(
            store=store,
            scene=scene,
            image_model=default_design_study_backfill_model,
        )
    for render_clip in render_clips:
        try:
            outputs.append(
                _render_scene(
                    store=store,
                    scene=scene,
                    plan=plan,
                    source_maps=source_maps,
                    engine_pack=engine_pack,
                    compiler_model=compiler_model,
                    requested_duration_seconds=requested_duration_seconds,
                    requested_resolution=requested_resolution,
                    requested_aspect_ratio=requested_aspect_ratio,
                    output_contract=output_contract,
                    scene_action_preflight=scene_action_preflight,
                    render_clip=render_clip,
                )
            )
        except Exception as exc:  # noqa: BLE001
            failures.append(_scene_failure(plan=plan, exc=exc, render_clip=render_clip))
            if _should_abort_remaining_render_units(exc):
                break
    return outputs, failures


def _backfill_default_design_studies(
    *,
    store: ArtifactStore,
    scene: Scene,
    image_model: str,
) -> None:
    result = DefaultDesignStudyBackfillService(
        store.project_dir,
        image_model=image_model,
    ).backfill_scene(scene)
    failures = [item for item in result.items if item.status == "failed"]
    if failures:
        details = "; ".join(
            f"{item.entity_id}: {item.reason or 'unknown failure'}" for item in failures
        )
        raise ValueError(f"Default design-study backfill failed before render: {details}")
    if result.generated_count:
        print(
            "[render_adapter] Backfilled "
            f"{result.generated_count} default design-study reference(s) "
            f"for {scene.scene_id} with {image_model}."
        )


def _should_abort_remaining_render_units(exc: Exception) -> bool:
    if not isinstance(exc, VideoGenerationError):
        return False
    message = str(exc).lower()
    return "timed out after" in message and "waiting for completion" in message


def _render_clips_for_scene(
    *,
    scene_id: str,
    render_clip_plan: RenderClipPlan | None,
    output_contract: dict[str, Any],
    selected_render_clip_ids: set[str] | None = None,
) -> list[RenderClip | None]:
    if render_clip_plan is not None and len(render_clip_plan.clips) > 1:
        clips = list(render_clip_plan.clips)
        if selected_render_clip_ids is None:
            return clips
        selected_clips = [
            clip for clip in clips if clip.clip_id in selected_render_clip_ids
        ]
        matched_clip_ids = {clip.clip_id for clip in selected_clips}
        missing_clip_ids = selected_render_clip_ids - matched_clip_ids
        if missing_clip_ids:
            requested = ", ".join(sorted(missing_clip_ids))
            available = ", ".join(clip.clip_id for clip in clips)
            raise ValueError(
                "render_adapter_v1 could not find requested render clip(s) "
                f"for {scene_id}: {requested}. Available clips: {available}."
            )
        return selected_clips
    if selected_render_clip_ids is not None:
        requested = ", ".join(sorted(selected_render_clip_ids))
        raise ValueError(
            "render_adapter_v1 received render_clip_ids for a scene without a "
            f"multi-clip render_clip_plan: {scene_id} ({requested})."
        )
    return [None]


def _ensure_required_render_clip_plans(
    *,
    params: dict[str, Any],
    context: dict[str, Any],
    shot_plans: list[ShotPlan],
    source_maps: dict[str, Any],
) -> None:
    if not bool(params.get("require_render_clip_plan")):
        return
    missing_scene_ids = [
        plan.scene_id
        for plan in shot_plans
        if plan.scene_id not in source_maps["render_clip_plan"]
    ]
    if not missing_scene_ids:
        return
    stage_id = context.get("stage_id", "render") if isinstance(context, dict) else "render"
    missing = ", ".join(sorted(missing_scene_ids))
    raise ValueError(
        f"Stage '{stage_id}' requires render_clip_plan artifacts for {missing}. "
        "Run render_clip_planning before this stage."
    )


def _planned_render_unit_count(
    *,
    plan: ShotPlan,
    source_maps: dict[str, Any],
    output_contract: dict[str, Any],
    selected_render_clip_ids: set[str] | None = None,
) -> int:
    return len(
        _render_clips_for_scene(
            scene_id=plan.scene_id,
            render_clip_plan=source_maps["render_clip_plan"].get(plan.scene_id),
            output_contract=output_contract,
            selected_render_clip_ids=selected_render_clip_ids,
        )
    )


def _artifact_announcer(context: dict[str, Any]) -> Any | None:
    announce = context.get("announce_artifact") if isinstance(context, dict) else None
    return announce if callable(announce) else None


def _announce_artifact(announce: Any | None, artifact: dict[str, Any]) -> ArtifactRef | None:
    if not callable(announce):
        return None
    announce(artifact)
    return _pre_saved_ref(artifact)


def _pre_saved_ref(artifact: dict[str, Any]) -> ArtifactRef | None:
    raw = artifact.get("pre_saved_ref")
    if not isinstance(raw, dict):
        return None
    return ArtifactRef.model_validate(raw)


def _scene_failure(
    *,
    plan: ShotPlan,
    exc: Exception,
    render_clip: RenderClip | None = None,
) -> dict[str, Any]:
    return {
        "scene_id": plan.scene_id,
        "scene_number": plan.scene_number,
        "scene_heading": plan.scene_heading,
        "render_clip_id": render_clip.clip_id if render_clip else None,
        "error_class": exc.__class__.__name__,
        "error": _clean_error_detail(str(exc)),
        "exception": exc,
    }


def _clean_error_detail(message: str) -> str:
    compact = " ".join(message.split())
    return compact if compact else "Unknown render failure"


def _render_failure_summary(
    *,
    failures: list[dict[str, Any]],
    success_count: int,
    total_count: int,
) -> str:
    failure_count = len(failures)
    details = ", ".join(
        (
            f"{failure['scene_id']}:{failure['render_clip_id']}"
            if failure.get("render_clip_id")
            else failure["scene_id"]
        )
        + f" ({failure['error_class']}: {failure['error']})"
        for failure in failures[:5]
    )
    if failure_count > 5:
        details += f", +{failure_count - 5} more"
    if success_count > 0:
        return (
            "Render generation preserved "
            f"{success_count} successful render unit(s) but failed for "
            f"{failure_count}/{total_count} render unit(s): {details}."
        )
    return (
        "Render generation failed before any render units were preserved: "
        f"{details}."
    )


def _render_scene(
    *,
    store: ArtifactStore,
    scene: Scene,
    plan: ShotPlan,
    source_maps: dict[str, Any],
    engine_pack: Any,
    compiler_model: str,
    requested_duration_seconds: float,
    requested_resolution: str | None,
    requested_aspect_ratio: str | None,
    output_contract: dict[str, Any],
    scene_action_preflight: SceneActionPreflight | None,
    render_clip: RenderClip | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    started = time.perf_counter()
    unit_entity_id = render_unit_entity_id(plan.scene_id, render_clip)
    unit_plan = clipped_shot_plan(plan, render_clip)
    unit_requested_duration_seconds = (
        render_clip.target_duration_seconds if render_clip else requested_duration_seconds
    )
    prompt_ref = anticipated_entity_ref(
        store, output_contract["prompt_artifact_type"], unit_entity_id
    )
    video_ref = anticipated_entity_ref(
        store, output_contract["video_artifact_type"], unit_entity_id
    )
    shot_plan_ref = latest_entity_ref(store, "shot_plan", plan.scene_id)
    if shot_plan_ref is None:
        raise ValueError(f"render_adapter_v1 could not resolve shot_plan ref for {plan.scene_id}")
    render_clip_plan = source_maps["render_clip_plan"].get(plan.scene_id)
    render_clip_plan_ref = latest_entity_ref(store, "render_clip_plan", plan.scene_id)

    aspect_ratio, aspect_note = normalize_aspect_ratio(
        requested_aspect_ratio
        or _look_and_feel_aspect_ratio(source_maps["look_and_feel"].get(plan.scene_id))
        or _project_aspect_ratio(source_maps["project_config"]),
        engine_pack.limits.supported_aspect_ratios,
    )
    duration_seconds, duration_note = normalize_duration_seconds(
        unit_requested_duration_seconds,
        engine_pack.limits.supported_durations_seconds,
    )
    resolution, resolution_note = _resolve_resolution(
        requested_resolution=requested_resolution,
        engine_pack=engine_pack,
        aspect_ratio=aspect_ratio,
    )

    keyframe_artifact = source_maps["keyframes"].get(plan.scene_id)
    resolved_inputs = _collect_resolved_inputs(
        store=store,
        scene=scene,
        keyframe_artifact=keyframe_artifact,
        source_maps=source_maps,
    )
    request, resolved_inputs, request_notes = _shape_generation_request(
        engine_pack=engine_pack,
        project_dir=store.project_dir,
        resolved_inputs=resolved_inputs,
        duration_seconds=duration_seconds,
        resolution=resolution,
        aspect_ratio=aspect_ratio,
        allow_prompt_only_required_media=output_contract["prompt_mode"] == "ai_previz",
    )
    if output_contract["prompt_mode"] == "ai_previz":
        previz_contract, sections, completeness, prompt_sources = compile_scene_previz_prompt(
            scene=scene,
            plan=unit_plan,
            render_clip=render_clip,
            source_maps=source_maps,
            resolved_inputs=resolved_inputs,
            engine_pack=engine_pack,
            consistency_strategy=output_contract["consistency_strategy"],
            prompt_profile=output_contract["prompt_profile"],
        )
        prompt_text = previz_contract.prompt_text
        completeness = completeness.model_copy(
            update={
                "notes": [
                    *completeness.notes,
                    *[
                        note
                        for note in (aspect_note, duration_note, resolution_note, *request_notes)
                        if note
                    ],
                ]
            }
        )
        compile_cost = _empty_cost(model="code")
    else:
        prompt_draft, compile_cost, required_categories = compile_render_prompt(
            compiler_model=compiler_model,
            engine_pack=engine_pack,
            scene_block=_scene_block(scene=scene, plan=unit_plan, render_clip=render_clip),
            context_blocks=_context_blocks(
                scene=scene,
                plan=unit_plan,
                source_maps=source_maps,
                resolved_inputs=resolved_inputs,
                render_clip=render_clip,
            ),
            resolved_inputs=resolved_inputs,
            target_provider=engine_pack.provider,
            target_model=engine_pack.target_model,
            duration_seconds=duration_seconds,
            resolution=resolution,
            aspect_ratio=aspect_ratio,
        )
        sections, completeness, prompt_sources = _finalize_prompt_sections(
            prompt_draft=prompt_draft,
            required_categories=required_categories,
            context_blocks=_context_blocks(
                scene=scene,
                plan=unit_plan,
                source_maps=source_maps,
                resolved_inputs=resolved_inputs,
                render_clip=render_clip,
            ),
            resolved_inputs=resolved_inputs,
            extra_source_artifact_types=creative_brief_source_artifact_types(
                source_maps["creative_brief"]
            ),
            notes=[
                note
                for note in (
                    aspect_note,
                    duration_note,
                    resolution_note,
                    render_clip_time_note(render_clip),
                    *_render_clip_plan_notes(
                        render_clip_plan,
                        duration_seconds,
                        render_clip=render_clip,
                    ),
                    *request_notes,
                )
                if note
            ],
        )
        if completeness.blocking_missing_categories:
            raise ValueError(
                f"render_adapter_v1 prompt for {plan.scene_id} is incomplete: "
                f"{', '.join(completeness.blocking_missing_categories)}"
            )
        prompt_text, dialogue_notes = _ensure_dialogue_prompt_contract(
            prompt_draft.prompt_text,
            unit_plan,
            duration_seconds=float(duration_seconds),
            render_clip=render_clip,
        )
        if dialogue_notes:
            completeness = completeness.model_copy(
                update={"notes": [*completeness.notes, *dialogue_notes]}
            )

    scene_cost = _scene_cost(
        compile_cost=compile_cost,
        generation_model=engine_pack.target_model,
        request_id=None,
    )
    preview_provenance = _build_preview_provenance(
        output_contract=output_contract,
        scene_cost=scene_cost,
        prompt_sources=prompt_sources,
        resolved_inputs=resolved_inputs,
        generation_latency_ms=None,
        scene_action_preflight=scene_action_preflight,
    )
    prompt_artifact = CompiledRenderPrompt(
        scene_id=plan.scene_id,
        scene_number=plan.scene_number,
        scene_heading=plan.scene_heading,
        render_unit=render_unit_kind(render_clip),
        render_clip_id=render_clip.clip_id if render_clip else None,
        render_clip_start_time_seconds=render_clip.start_time_seconds if render_clip else None,
        render_clip_end_time_seconds=render_clip.end_time_seconds if render_clip else None,
        source_shot_ids=list(render_clip.source_shot_ids) if render_clip else [],
        fallback_beat_ids=list(render_clip.fallback_beat_ids) if render_clip else [],
        scene_ref=plan.scene_ref,
        shot_plan_ref=shot_plan_ref,
        render_clip_plan_ref=render_clip_plan_ref,
        keyframe_ref=latest_entity_ref(store, "keyframe", plan.scene_id),
        target_provider=engine_pack.provider,
        target_model=engine_pack.target_model,
        engine_pack_id=engine_pack.pack_id,
        compiler_model=compiler_model,
        requested_duration_seconds=float(unit_requested_duration_seconds),
        resolved_duration_seconds=float(duration_seconds),
        resolution=resolution,
        aspect_ratio=aspect_ratio,
        provider_params=request.provider_params,
        prompt_text=prompt_text,
        sections=sections,
        completeness=completeness,
        prompt_sources_used=prompt_sources,
        creative_brief_preview=source_maps["creative_brief"],
        resolved_inputs=resolved_inputs,
        preview_provenance=preview_provenance,
    )

    request = VideoGenerationRequest(
        prompt=prompt_text,
        duration_seconds=request.duration_seconds,
        resolution=request.resolution,
        aspect_ratio=request.aspect_ratio,
        first_frame=request.first_frame,
        last_frame=request.last_frame,
        reference_images=request.reference_images,
        provider_params=request.provider_params,
    )
    result = generate_video(request=request, engine_pack=engine_pack)
    scene_cost["model"] = _merge_model_labels(
        scene_cost.get("model"),
        result.model_used,
    )
    scene_cost["request_id"] = result.request_id

    media_dir = render_media_dir(
        store.project_dir,
        unit_entity_id,
        video_ref.version,
        media_root=output_contract["media_root"],
    )
    media_dir.mkdir(parents=True, exist_ok=True)
    output_path = media_dir / output_contract["media_filename"]
    output_path.write_bytes(result.video_bytes)
    latency_ms = round((time.perf_counter() - started) * 1000)

    generated_video = GeneratedVideoArtifact(
        scene_id=plan.scene_id,
        scene_number=plan.scene_number,
        scene_heading=plan.scene_heading,
        render_unit=render_unit_kind(render_clip),
        render_clip_id=render_clip.clip_id if render_clip else None,
        render_clip_start_time_seconds=render_clip.start_time_seconds if render_clip else None,
        render_clip_end_time_seconds=render_clip.end_time_seconds if render_clip else None,
        source_shot_ids=list(render_clip.source_shot_ids) if render_clip else [],
        fallback_beat_ids=list(render_clip.fallback_beat_ids) if render_clip else [],
        scene_ref=plan.scene_ref,
        shot_plan_ref=shot_plan_ref,
        render_clip_plan_ref=render_clip_plan_ref,
        prompt_ref=prompt_ref,
        keyframe_ref=latest_entity_ref(store, "keyframe", plan.scene_id),
        video=MediaFile(
            relative_path=relative_path(store.project_dir, output_path),
            media_type=result.media_type,
            duration_seconds=float(duration_seconds),
        ),
        duration_seconds=float(duration_seconds),
        resolution=resolution,
        aspect_ratio=aspect_ratio,
        generation_params={
            "duration_seconds": duration_seconds,
            "resolution": resolution,
            "aspect_ratio": aspect_ratio,
            "provider_params": request.provider_params,
        },
        target_provider=engine_pack.provider,
        target_model=result.model_used,
        engine_pack_id=engine_pack.pack_id,
        request_id=result.request_id or result.provider_job_id,
        cost=CostRecord.model_validate(scene_cost),
        resolved_inputs=resolved_inputs,
        notes=completeness.notes,
        preview_provenance=_build_preview_provenance(
            output_contract=output_contract,
            scene_cost=scene_cost,
            prompt_sources=prompt_sources,
            resolved_inputs=resolved_inputs,
            generation_latency_ms=latency_ms,
            scene_action_preflight=scene_action_preflight,
        ),
    )
    return (
        _prompt_artifact_dict(prompt_artifact, output_contract=output_contract),
        _video_artifact_dict(
            generated_video=generated_video,
            prompt_artifact=prompt_artifact,
            compile_cost=scene_cost,
            request_notes=request_notes,
            output_contract=output_contract,
        ),
        scene_cost,
    )


def _project_dir(context: dict[str, Any]) -> Path:
    project_dir_raw = context.get("project_dir")
    if not isinstance(project_dir_raw, str) or not project_dir_raw:
        raise ValueError("render_adapter_v1 requires context.project_dir")
    return Path(project_dir_raw)


def _runtime_params(context: dict[str, Any]) -> dict[str, Any]:
    runtime_params = context.get("runtime_params", {}) if isinstance(context, dict) else {}
    return runtime_params if isinstance(runtime_params, dict) else {}


def _selected_render_clip_ids(runtime_params: dict[str, Any]) -> set[str] | None:
    raw_ids = runtime_params.get("render_clip_ids")
    if not isinstance(raw_ids, list):
        return None
    clip_ids = {
        item.strip()
        for item in raw_ids
        if isinstance(item, str) and item.strip()
    }
    return clip_ids or None


def _scene_action_preflight(runtime_params: dict[str, Any]) -> SceneActionPreflight | None:
    raw = runtime_params.get("scene_action_preflight")
    if isinstance(raw, SceneActionPreflight):
        return raw
    if isinstance(raw, dict):
        try:
            return SceneActionPreflight.model_validate(raw)
        except Exception:
            return None
    return None


def _default_design_study_backfill_enabled(
    *,
    params: dict[str, Any],
    runtime_params: dict[str, Any],
) -> bool:
    raw = params.get("default_design_study_backfill")
    if raw is None:
        raw = runtime_params.get("default_design_study_backfill")
    if raw is None:
        return False
    return _bool_param(raw)


def _default_design_study_backfill_model(
    *,
    params: dict[str, Any],
    runtime_params: dict[str, Any],
    compiler_model: str,
) -> str:
    configured = _optional_string(
        params.get("default_design_study_backfill_model")
        or runtime_params.get("default_design_study_backfill_model")
    )
    if configured:
        return configured
    if compiler_model == "mock":
        return "mock"
    return DEFAULT_DESIGN_STUDY_BACKFILL_MODEL


def _bool_param(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() not in {"0", "false", "no", "off"}
    return bool(value)


def _build_preview_provenance(
    *,
    output_contract: dict[str, Any],
    scene_cost: dict[str, Any],
    prompt_sources: list[str],
    resolved_inputs: list[RenderResolvedInput],
    generation_latency_ms: int | None,
    scene_action_preflight: SceneActionPreflight | None,
) -> PreviewProvenance:
    return PreviewProvenance(
        mode=output_contract["preview_mode"],
        fidelity_intent=output_contract["fidelity_intent"],
        intended_use=list(output_contract["intended_use"]),
        upstream_inputs=_render_upstream_inputs(
            prompt_sources=prompt_sources,
            resolved_inputs=resolved_inputs,
        ),
        consistency_strategy=output_contract["consistency_strategy"],
        prompt_profile=output_contract.get("prompt_profile"),
        prerequisite_strategy=(
            scene_action_preflight.prerequisite_strategy
            if output_contract["preview_mode"] == "ai_previz" and scene_action_preflight
            else None
        ),
        reused_artifact_types=(
            list(scene_action_preflight.reused_artifact_types)
            if output_contract["preview_mode"] == "ai_previz" and scene_action_preflight
            else []
        ),
        auto_build_artifact_types=(
            list(scene_action_preflight.auto_build_artifact_types)
            if output_contract["preview_mode"] == "ai_previz" and scene_action_preflight
            else []
        ),
        missing_optional_artifact_types=(
            list(scene_action_preflight.missing_optional_artifact_types)
            if output_contract["preview_mode"] == "ai_previz" and scene_action_preflight
            else []
        ),
        estimated_cost_usd=_preview_cost_value(
            scene_cost=scene_cost,
            output_contract=output_contract,
        ),
        generation_latency_ms=generation_latency_ms,
    )


def _output_contract(
    *,
    params: dict[str, Any],
    runtime_params: dict[str, Any],
) -> dict[str, Any]:
    prompt_mode = _optional_string(
        params.get("prompt_mode") or runtime_params.get("prompt_mode")
    ) or "render"
    if prompt_mode == "ai_previz":
        return {
            "prompt_mode": "ai_previz",
            "prompt_artifact_type": "ai_previz_prompt",
            "video_artifact_type": "ai_previz_video",
            "track_type": "ai_previz_video",
            "track_priority": 125,
            "track_note": "AI previz clip for render-unit blocking and camera review.",
            "media_root": "ai_previz_video_media",
            "media_filename": "ai_previz.mp4",
            "preview_mode": "ai_previz",
            "fidelity_intent": "blocking_review",
            "intended_use": ["human_review"],
            "consistency_strategy": _optional_string(
                params.get("consistency_strategy") or runtime_params.get("consistency_strategy")
            )
            or "prompt_only",
            "prompt_profile": _optional_string(
                params.get("prompt_profile") or runtime_params.get("prompt_profile")
            )
            or "standard",
            "default_engine_pack_id": "xai_grok_imagine_video",
            "default_compiler_model": "code",
            "prompt_intent": "Compiled low-fidelity AI previz prompt for scene blocking review.",
            "prompt_rationale": (
                "AI previz prompts stay reviewable so operators can inspect the non-final "
                "house-style instructions CineForge sent downstream."
            ),
            "video_intent": "AI previz clip for render-unit blocking, camera, and motion review.",
            "video_rationale": (
                "AI previz turns reviewed planning artifacts into low-fidelity planning clips "
                "without conflating previz with final render."
            ),
        }
    return {
        "prompt_mode": "render",
        "prompt_artifact_type": "render_prompt",
        "video_artifact_type": "generated_video",
        "track_type": "generated_video",
        "track_priority": 100,
        "track_note": "Scene-level generated video render.",
        "media_root": "generated_video_media",
        "media_filename": "scene_render.mp4",
        "preview_mode": "generated_render",
        "fidelity_intent": "render_preview",
        "intended_use": ["human_review", "ai_conditioning"],
        "consistency_strategy": None,
        "default_engine_pack_id": "google_veo31",
        "default_compiler_model": "gpt-5.4-mini",
        "prompt_intent": "Compiled, provider-ready generation prompt for a scene render.",
        "prompt_rationale": (
            "Prompt artifacts stay immutable and reviewable so operators can inspect "
            "what CineForge actually sent downstream."
        ),
        "video_intent": "Scene-level generated video derived from compiled upstream film intent.",
        "video_rationale": (
            "Render adapter turns reviewed planning artifacts into a playable high-fidelity "
            "preview without mutating upstream creative intent."
        ),
    }


def _track_manifest(inputs: dict[str, Any]) -> TrackManifest:
    payload = inputs.get("track_manifest")
    if not isinstance(payload, dict):
        raise ValueError("render_adapter_v1 requires track_manifest input")
    return TrackManifest.model_validate(payload)


def _shot_plans(
    inputs: dict[str, Any],
    *,
    runtime_params: dict[str, Any] | None = None,
) -> list[ShotPlan]:
    payloads = inputs.get("shot_plan")
    if not isinstance(payloads, list) or not payloads:
        raise ValueError("render_adapter_v1 requires one or more shot_plan inputs")
    payloads = filter_scene_payloads(payloads, runtime_params or {})
    plans = [ShotPlan.model_validate(item) for item in payloads if isinstance(item, dict)]
    if not plans:
        raise ValueError("render_adapter_v1 could not parse any shot_plan inputs")
    return plans


def _build_source_maps(inputs: dict[str, Any]) -> dict[str, Any]:
    project_config = (
        ProjectConfig.model_validate(inputs["project_config"])
        if isinstance(inputs.get("project_config"), dict)
        else None
    )
    intent_mood = (
        IntentMood.model_validate(inputs["intent_mood"])
        if isinstance(inputs.get("intent_mood"), dict)
        else None
    )
    look_and_feel = _scene_payload_map(
        inputs.get("look_and_feel"), LookAndFeel, scene_key="scene_id"
    )
    sound_and_music = _scene_payload_map(
        inputs.get("sound_and_music"), SoundAndMusic, scene_key="scene_id"
    )
    rhythm_and_flow = _scene_payload_map(
        inputs.get("rhythm_and_flow"), RhythmAndFlow, scene_key="scene_id"
    )
    keyframes = _scene_payload_map(inputs.get("keyframe"), KeyframeArtifact, scene_key="scene_id")
    render_clip_plan = _render_clip_plan_map(inputs)
    manifests = _manifest_payload_map(inputs.get("injected_asset_manifest"))
    return {
        "project_config": project_config,
        "intent_mood": intent_mood,
        "creative_brief": build_visual_creative_brief(
            project_config_data=project_config.model_dump(mode="json") if project_config else None,
            intent_mood_data=intent_mood,
            project_manifest=manifests.get(("project", "project")),
        ),
        "look_and_feel": look_and_feel,
        "sound_and_music": sound_and_music,
        "rhythm_and_flow": rhythm_and_flow,
        "render_clip_plan": render_clip_plan,
        "character_and_performance": _performance_by_scene(inputs.get("character_and_performance")),
        "character_bible": _entity_payload_map(
            inputs.get("character_bible"),
            schema=CharacterBible,
            id_keys=("character_id", "name"),
        ),
        "location_bible": _entity_payload_map(
            inputs.get("location_bible"),
            schema=LocationBible,
            id_keys=("location_id", "name"),
        ),
        "keyframes": keyframes,
        "injected_manifests": manifests,
    }


def _render_clip_plan_map(inputs: dict[str, Any]) -> dict[str, RenderClipPlan]:
    payloads: list[Any] = []
    raw_store_payloads = inputs.get("render_clip_plan")
    if isinstance(raw_store_payloads, list):
        payloads.extend(raw_store_payloads)
    raw_stage_payloads = inputs.get("render_clip_planning")
    if isinstance(raw_stage_payloads, list):
        payloads.extend(raw_stage_payloads)

    result: dict[str, RenderClipPlan] = {}
    for item in payloads:
        if not isinstance(item, dict):
            continue
        plan = RenderClipPlan.model_validate(item)
        result[plan.scene_id] = plan
    return result


def _scene_payload_map(
    payload: Any,
    schema: Any,
    *,
    scene_key: str,
) -> dict[str, Any]:
    if not isinstance(payload, list):
        return {}
    result: dict[str, Any] = {}
    for item in payload:
        if not isinstance(item, dict):
            continue
        scene_id = item.get(scene_key)
        if not isinstance(scene_id, str) or not scene_id:
            continue
        result[scene_id] = schema.model_validate(item)
    return result


def _entity_payload_map(
    payload: Any,
    *,
    schema: Any,
    id_keys: tuple[str, ...],
) -> dict[str, Any]:
    if not isinstance(payload, list):
        return {}
    result: dict[str, Any] = {}
    for item in payload:
        if not isinstance(item, dict):
            continue
        parsed = schema.model_validate(item)
        for key in id_keys:
            raw = getattr(parsed, key, None)
            if isinstance(raw, str) and raw.strip():
                result[_slugify(raw)] = parsed
    return result


def _performance_by_scene(payload: Any) -> dict[str, list[CharacterAndPerformance]]:
    if not isinstance(payload, list):
        return {}
    result: dict[str, list[CharacterAndPerformance]] = {}
    for item in payload:
        if not isinstance(item, dict):
            continue
        if "entries" in item and isinstance(item["entries"], list):
            scene_id = item.get("scene_id")
            if not isinstance(scene_id, str) or not scene_id:
                continue
            entries = [
                CharacterAndPerformance.model_validate(entry)
                for entry in item["entries"]
                if isinstance(entry, dict)
            ]
            if entries:
                result.setdefault(scene_id, []).extend(entries)
            continue
        parsed = CharacterAndPerformance.model_validate(item)
        result.setdefault(parsed.scene_id, []).append(parsed)
    return result


def _manifest_payload_map(payload: Any) -> dict[tuple[str, str], InjectedAssetManifest]:
    if not isinstance(payload, list):
        return {}
    result: dict[tuple[str, str], InjectedAssetManifest] = {}
    for item in payload:
        if not isinstance(item, dict):
            continue
        manifest = InjectedAssetManifest.model_validate(item)
        result[(manifest.target_kind, manifest.target_id)] = manifest
    return result


def _collect_resolved_inputs(
    *,
    store: ArtifactStore,
    scene: Scene,
    keyframe_artifact: KeyframeArtifact | None,
    source_maps: dict[str, Any],
) -> list[RenderResolvedInput]:
    inputs: list[RenderResolvedInput] = []
    if keyframe_artifact is not None:
        keyframe_ref = latest_entity_ref(store, "keyframe", scene.scene_id)
        for keyframe in keyframe_artifact.keyframes:
            if not keyframe.is_locked:
                continue
            inputs.append(
                RenderResolvedInput(
                    input_id=keyframe.keyframe_id,
                    kind="keyframe",
                    label=f"Locked {keyframe.position} keyframe for {keyframe.shot_id}",
                    relative_path=keyframe.image.relative_path,
                    media_type=keyframe.image.media_type,
                    source_ref=keyframe_ref,
                    lock_status="hard_locked",
                    required=True,
                    notes=keyframe.notes,
                )
            )

    for manifest in _relevant_manifests(scene=scene, source_maps=source_maps).values():
        manifest_ref = latest_entity_ref(
            store,
            "injected_asset_manifest",
            manifest_entity_id(manifest.target_kind, manifest.target_id),
        )
        for asset in manifest.assets:
            if asset.asset_type not in {"image", "audio"}:
                continue
            kind = _manifest_asset_kind(manifest.target_kind, asset.asset_type)
            label = f"{manifest.display_name}: {asset.filename}"
            inputs.append(
                RenderResolvedInput(
                    input_id=asset.asset_id,
                    kind=kind,
                    label=label,
                    relative_path=asset.file_path,
                    media_type=asset.content_type,
                    source_ref=manifest_ref,
                    lock_status=asset.lock_status,
                    required=asset.lock_status == "hard_locked",
                    notes=f"purpose={asset.purpose}",
                )
            )

    for character_id in scene.characters_present_ids:
        visual_ref = _bible_visual_reference(
            store=store,
            target_kind="character",
            target_id=character_id,
        )
        if visual_ref is not None:
            path, ref, selection_source = visual_ref
            inputs.append(
                RenderResolvedInput(
                    input_id=f"character_visual_{character_id}",
                    kind="character_injected_image",
                    label=f"Character visual reference: {character_id}",
                    relative_path=path,
                    media_type=media_type_for_image(path),
                    source_ref=ref,
                    lock_status=_visual_reference_lock_status(selection_source),
                    required=False,
                    notes=_visual_reference_note(selection_source),
                )
            )

    location_id = _slugify(scene.location)
    visual_ref = _bible_visual_reference(
        store=store,
        target_kind="location",
        target_id=location_id,
    )
    if visual_ref is not None:
        path, ref, selection_source = visual_ref
        inputs.append(
            RenderResolvedInput(
                input_id=f"location_visual_{location_id}",
                kind="location_injected_image",
                label=f"Location visual reference: {scene.location}",
                relative_path=path,
                media_type=media_type_for_image(path),
                source_ref=ref,
                lock_status=_visual_reference_lock_status(selection_source),
                required=False,
                notes=_visual_reference_note(selection_source),
            )
        )

    for prop_name in scene.props_mentioned:
        if not isinstance(prop_name, str) or not prop_name.strip():
            continue
        prop_id = _slugify(prop_name)
        visual_ref = _bible_visual_reference(
            store=store,
            target_kind="prop",
            target_id=prop_id,
        )
        if visual_ref is None:
            continue
        path, ref, selection_source = visual_ref
        inputs.append(
            RenderResolvedInput(
                input_id=f"prop_visual_{prop_id}",
                kind="prop_injected_image",
                label=f"Prop visual reference: {prop_name}",
                relative_path=path,
                media_type=media_type_for_image(path),
                source_ref=ref,
                lock_status=_visual_reference_lock_status(selection_source),
                required=False,
                notes=_visual_reference_note(selection_source),
            )
        )
    return inputs


def _relevant_manifests(
    *,
    scene: Scene,
    source_maps: dict[str, Any],
) -> dict[tuple[str, str], InjectedAssetManifest]:
    manifests: dict[tuple[str, str], InjectedAssetManifest] = {}
    for key in (("project", "project"), ("scene", scene.scene_id)):
        manifest = source_maps["injected_manifests"].get(key)
        if manifest is not None:
            manifests[key] = manifest
    for character_id in scene.characters_present_ids:
        if isinstance(character_id, str) and character_id:
            key = ("character", character_id)
            manifest = source_maps["injected_manifests"].get(key)
            if manifest is not None:
                manifests[key] = manifest
    location_name = scene.location
    if isinstance(location_name, str) and location_name:
        key = ("location", _slugify(location_name))
        manifest = source_maps["injected_manifests"].get(key)
        if manifest is not None:
            manifests[key] = manifest
    for prop_name in scene.props_mentioned:
        if isinstance(prop_name, str) and prop_name:
            key = ("prop", _slugify(prop_name))
            manifest = source_maps["injected_manifests"].get(key)
            if manifest is not None:
                manifests[key] = manifest
    return manifests


def _bible_visual_reference(
    *,
    store: ArtifactStore,
    target_kind: str,
    target_id: str,
) -> tuple[str, ArtifactRef, str | None] | None:
    manifest_ref = latest_entity_ref(store, "bible_manifest", f"{target_kind}_{target_id}")
    if manifest_ref is None:
        return None
    artifact = store.load_artifact(manifest_ref)
    filename = artifact.data.get("visual_reference_image")
    if not isinstance(filename, str) or not filename.strip():
        return None
    rel_path = str(
        (store.project_dir / manifest_ref.path)
        .parent.joinpath(filename)
        .relative_to(store.project_dir)
    )
    if not (store.project_dir / rel_path).exists():
        return None
    selection_source = None
    state = read_design_study_state(store.project_dir, f"{target_kind}_{target_id}")
    if state is not None and state.selected_final_filename == filename:
        selection_source = state.selected_final_source
    return rel_path, manifest_ref, selection_source


def _visual_reference_lock_status(selection_source: str | None) -> str:
    if selection_source == "system_default":
        return "system_default_visual_reference"
    return "selected_visual_reference"


def _visual_reference_note(selection_source: str | None) -> str | None:
    if selection_source == "system_default":
        return (
            "system_default_design_study=true; generated as render/AI-previz backfill "
            "and not yet human-approved"
        )
    if selection_source == "human":
        return "human_selected_design_study=true"
    return None


def _shape_generation_request(
    *,
    engine_pack: Any,
    project_dir: Path,
    resolved_inputs: list[RenderResolvedInput],
    duration_seconds: int,
    resolution: str,
    aspect_ratio: str,
    allow_prompt_only_required_media: bool = False,
) -> tuple[VideoGenerationRequest, list[RenderResolvedInput], list[str]]:
    updated = [item.model_copy(deep=True) for item in resolved_inputs]
    image_inputs = sorted(
        [item for item in updated if item.kind in _IMAGE_KINDS and item.relative_path],
        key=_image_input_priority_key,
    )
    audio_inputs = [item for item in updated if item.kind in _AUDIO_KINDS]
    notes: list[str] = []

    first_frame_item = _pop_priority_input(
        image_inputs,
        predicate=lambda item: item.kind == "keyframe" and " start " in item.label.lower(),
    )
    last_frame_item = _pop_priority_input(
        image_inputs,
        predicate=lambda item: item.kind == "keyframe" and " end " in item.label.lower(),
    )
    if first_frame_item is not None:
        if engine_pack.limits.supports_first_frame:
            first_frame_item.used_as = "input_reference"
        elif first_frame_item.required and not allow_prompt_only_required_media:
            raise ValueError(
                f"{engine_pack.pack_id} does not support locked opening-frame guidance"
            )
        else:
            first_frame_item.used_as = "prompt_context"
            notes.append("Opening-frame reference was kept in prompt text only.")
            first_frame_item = None
    if last_frame_item is not None:
        if engine_pack.limits.supports_last_frame:
            last_frame_item.used_as = "last_frame"
        elif last_frame_item.required and not allow_prompt_only_required_media:
            raise ValueError(f"{engine_pack.pack_id} does not support locked last-frame guidance")
        else:
            last_frame_item.used_as = "prompt_context"
            notes.append("Last-frame reference was kept in prompt text only.")
            last_frame_item = None
    if first_frame_item is None and engine_pack.provider == "openai":
        first_frame_item = _pop_priority_input(
            image_inputs,
            predicate=_is_uploadable_raster_image,
        )
    if first_frame_item is not None and first_frame_item.used_as == "prompt_context":
        first_frame_item.used_as = "input_reference"

    first_frame = _video_reference(project_dir, first_frame_item)
    last_frame = _video_reference(project_dir, last_frame_item)
    if first_frame_item is not None and first_frame is None:
        if first_frame_item.required and not allow_prompt_only_required_media:
            raise ValueError(
                f"{first_frame_item.label} is not an uploadable raster image "
                f"for {engine_pack.pack_id}"
            )
        first_frame_item.used_as = "prompt_context"
        notes.append(
            f"{first_frame_item.label} stayed prompt-only because it is not "
            "an uploadable raster image."
        )
    if last_frame_item is not None and last_frame is None:
        if last_frame_item.required and not allow_prompt_only_required_media:
            raise ValueError(
                f"{last_frame_item.label} is not an uploadable raster image "
                f"for {engine_pack.pack_id}"
            )
        last_frame_item.used_as = "prompt_context"
        notes.append(
            f"{last_frame_item.label} stayed prompt-only because it is not "
            "an uploadable raster image."
        )
    remaining_capacity = (
        0 if engine_pack.provider == "openai" else int(engine_pack.limits.max_reference_images)
    )

    reference_images: list[VideoReferenceInput] = []
    required_overflow: list[str] = []
    for item in image_inputs:
        if item.used_as != "prompt_context":
            continue
        if remaining_capacity > 0:
            item.used_as = "reference_image"
            reference = _video_reference(project_dir, item)
            if reference is not None:
                reference_images.append(reference)
                remaining_capacity -= 1
            elif item.required and not allow_prompt_only_required_media:
                item.used_as = "unsupported"
                required_overflow.append(item.label)
            else:
                item.used_as = "prompt_context"
                notes.append(
                    f"{item.label} stayed prompt-only because it is not an uploadable raster image."
                )
            continue
        if item.required and not allow_prompt_only_required_media:
            item.used_as = "unsupported"
            required_overflow.append(item.label)
        else:
            item.used_as = "prompt_context"
            notes.append(
                f"{item.label} stayed prompt-only because "
                f"{engine_pack.pack_id} ran out of image slots."
            )
    if required_overflow:
        raise ValueError(
            f"{engine_pack.pack_id} cannot satisfy required image constraints: "
            f"{', '.join(required_overflow)}"
        )

    if audio_inputs:
        if not engine_pack.limits.supports_audio_upload:
            required_audio = [item.label for item in audio_inputs if item.required]
            if required_audio and not allow_prompt_only_required_media:
                for item in audio_inputs:
                    if item.required:
                        item.used_as = "unsupported"
                raise ValueError(
                    f"{engine_pack.pack_id} does not support required audio uploads: "
                    f"{', '.join(required_audio)}"
                )
            for item in audio_inputs:
                item.used_as = "prompt_context"
            if engine_pack.limits.supports_audio_cues:
                notes.append("Audio references were kept as prompt-level sound cues.")
            else:
                notes.append(
                    "Audio references were ignored because the engine pack has no audio pathway."
                )

    if reference_images and bool(
        engine_pack.request_defaults.get("reference_images_require_eight_seconds")
    ):
        if duration_seconds != 8:
            required_refs = [
                item.label
                for item in updated
                if item.used_as == "reference_image" and item.required
            ]
            if required_refs and not allow_prompt_only_required_media:
                raise ValueError(
                    f"{engine_pack.pack_id} requires 8-second renders for reference images: "
                    f"{', '.join(required_refs)}"
                )
            for item in updated:
                if item.used_as == "reference_image":
                    item.used_as = "prompt_context"
            notes.append(
                "Reference images stayed prompt-only because this engine pack "
                "requires 8s for uploads."
            )
            reference_images = []
    if bool(engine_pack.request_defaults.get("high_resolution_requires_eight_seconds")):
        if resolution == "1080p" and duration_seconds != 8:
            raise ValueError(f"{engine_pack.pack_id} requires 8-second renders for {resolution}")
    if (
        reference_images
        and (first_frame is not None or last_frame is not None)
        and not bool(
            engine_pack.request_defaults.get(
                "mixed_frame_guidance_and_reference_images_supported",
                True,
            )
        )
    ):
        required_refs = [
            item.label
            for item in updated
            if item.used_as == "reference_image" and item.required
        ]
        if required_refs and not allow_prompt_only_required_media:
            for item in updated:
                if item.used_as == "reference_image" and item.required:
                    item.used_as = "unsupported"
            raise ValueError(
                f"{engine_pack.pack_id} cannot combine frame guidance with required "
                f"reference images on the live provider API: {', '.join(required_refs)}"
            )
        for item in updated:
            if item.used_as == "reference_image":
                item.used_as = "prompt_context"
        reference_images = []
        notes.append(
            "Additional reference images stayed prompt-only because the live provider "
            "API rejects mixing frame guidance with extra reference images."
        )

    return (
        VideoGenerationRequest(
            prompt="",
            duration_seconds=duration_seconds,
            resolution=resolution,
            aspect_ratio=aspect_ratio,
            first_frame=first_frame,
            last_frame=last_frame,
            reference_images=reference_images,
            provider_params={},
        ),
        updated,
        notes,
    )


def _scene_block(
    *,
    scene: Scene,
    plan: ShotPlan,
    render_clip: RenderClip | None = None,
) -> str:
    if render_clip is not None:
        clip_lines = [
            f"Scene {scene.scene_number}: {scene.heading}",
            (
                f"Render clip: {render_clip.clip_id} "
                f"({render_clip.start_time_seconds:.1f}-{render_clip.end_time_seconds:.1f}s, "
                f"target {render_clip.target_duration_seconds:.1f}s)"
            ),
            f"Location: {scene.location} ({scene.int_ext}, {scene.time_of_day})",
            f"Tone: {scene.tone_mood}",
            f"Characters present: {', '.join(scene.characters_present) or 'none'}",
        ]
        if render_clip.source_shot_ids:
            clip_lines.append("Source shots: " + ", ".join(render_clip.source_shot_ids))
        if render_clip.fallback_beat_ids:
            clip_lines.append("Fallback beats: " + ", ".join(render_clip.fallback_beat_ids))
        if render_clip.action_beats:
            clip_lines.append("Clip action beats:")
            clip_lines.extend(
                f"- {remove_dialogue_quotes(beat, render_clip.dialogue_lines)}"
                for beat in render_clip.action_beats
            )
        clip_dialogue = render_clip_dialogue_lines(render_clip)
        if clip_dialogue:
            clip_lines.append("Clip exact dialogue lines:")
            clip_lines.extend(f"- {line}" for line in clip_dialogue)
        if render_clip.continuity_start_notes or render_clip.continuity_end_notes:
            clip_lines.append("Clip continuity notes:")
            clip_lines.extend(f"- start: {note}" for note in render_clip.continuity_start_notes)
            clip_lines.extend(f"- end: {note}" for note in render_clip.continuity_end_notes)
        return "\n".join(clip_lines)

    excerpt_lines: list[str] = []
    for element in scene.elements[:6]:
        excerpt_lines.append(f"- {element.element_type}: {element.content}")
    if not excerpt_lines:
        excerpt_lines.append("- No scene excerpt available.")
    return (
        f"Scene {scene.scene_number}: {scene.heading}\n"
        f"Location: {scene.location} ({scene.int_ext}, {scene.time_of_day})\n"
        f"Tone: {scene.tone_mood}\n"
        f"Characters present: {', '.join(scene.characters_present) or 'none'}\n"
        f"Estimated shot-plan duration: {plan.total_estimated_duration_seconds:.1f}s\n"
        "Screenplay excerpt:\n" + "\n".join(excerpt_lines)
    )


def _context_blocks(
    *,
    scene: Scene,
    plan: ShotPlan,
    source_maps: dict[str, Any],
    resolved_inputs: list[RenderResolvedInput],
    render_clip: RenderClip | None = None,
) -> dict[str, str]:
    return {
        "shot_definition": _shot_definition_block(plan),
        "render_clip_plan": _render_clip_plan_block(
            source_maps["render_clip_plan"].get(plan.scene_id),
            render_clip=render_clip,
        ),
        "creative_brief": _creative_brief_block(source_maps["creative_brief"]),
        "look_and_feel": _look_and_feel_block(source_maps["look_and_feel"].get(plan.scene_id)),
        "sound_and_music": _sound_block(
            source_maps["sound_and_music"].get(plan.scene_id),
            resolved_inputs=resolved_inputs,
        ),
        "character_and_performance": _performance_block(
            source_maps["character_and_performance"].get(plan.scene_id, []),
            plan=plan,
        ),
        "rhythm_and_flow": _rhythm_block(source_maps["rhythm_and_flow"].get(plan.scene_id)),
        "character_bible_state": _character_state_block(
            scene=scene,
            character_bibles=source_maps["character_bible"],
        ),
        "location_bible_state": _location_state_block(
            scene=scene,
            location_bibles=source_maps["location_bible"],
        ),
        "keyframes": _keyframe_block(resolved_inputs),
        "injected_assets": _injected_assets_block(resolved_inputs),
    }


def _shot_definition_block(plan: ShotPlan) -> str:
    lines = [
        f"Coverage approach: {plan.coverage_strategy.coverage_approach}",
        f"Rhythm intent: {plan.coverage_strategy.rhythm_and_flow_intent}",
        f"Visual intent: {plan.coverage_strategy.look_and_feel_intent}",
        f"Sound intent: {plan.coverage_strategy.sound_and_music_intent}",
        f"Performance notes: {plan.coverage_strategy.character_and_performance_notes}",
    ]
    for shot in plan.shots:
        shot_parts = [
            f"{shot.shot_id}",
            shot.shot_size,
            shot.camera_angle,
            shot.camera_movement,
            f"lens={shot.lens_focal_length}",
            f"duration={shot.duration_estimate_seconds:.1f}s",
            f"blocking={shot.blocking}",
            f"action={shot.action_description}",
            f"edit_intent={shot.edit_intent}",
        ]
        dialogue = _exact_dialogue_lines_for_shot(shot)
        if dialogue:
            shot_parts.append(
                f"dialogue_lines={len(dialogue)} exact line(s); see dialogue timing contract"
            )
        lines.append(" | ".join(shot_parts))
    dialogue_contract = _dialogue_timing_contract(
        plan,
        duration_seconds=plan.total_estimated_duration_seconds,
    )
    if dialogue_contract:
        lines.extend(["", dialogue_contract])
    return "\n".join(lines)


def _render_clip_plan_block(
    plan: RenderClipPlan | None,
    *,
    render_clip: RenderClip | None = None,
) -> str:
    if plan is None:
        return (
            "No render_clip_plan artifact was provided. The adapter is using the "
            "scene-level shot plan only, so duration compression risk is unknown."
        )
    lines = [
        (
            "Scene target dramatic duration: "
            f"{plan.target_dramatic_duration_seconds:.1f}s"
        ),
        f"Engine max clip duration: {plan.engine_max_clip_duration_seconds:.1f}s",
        f"Provenance: {plan.provenance_mode}; confidence={plan.confidence:.2f}",
        f"Duration rationale: {plan.duration_rationale}",
    ]
    if plan.missing_upstream_categories:
        lines.append(
            "Missing upstream categories: "
            + ", ".join(plan.missing_upstream_categories)
        )
    if render_clip is not None:
        lines.append("Render path: this prompt is for one planned render clip only.")
    elif len(plan.clips) > 1:
        lines.append(
            "Render path: this scene-level prompt is not expanding each planned "
            "clip; preserve this multi-clip pacing in the prompt and disclose "
            "compression risk."
        )
    clips = [render_clip] if render_clip is not None else list(plan.clips)
    for clip in clips:
        pieces = [
            clip.clip_id,
            f"{clip.start_time_seconds:.1f}-{clip.end_time_seconds:.1f}s",
            f"target={clip.target_duration_seconds:.1f}s",
        ]
        if clip.source_shot_ids:
            pieces.append(f"shots={', '.join(clip.source_shot_ids)}")
        if clip.fallback_beat_ids:
            pieces.append(f"beats={', '.join(clip.fallback_beat_ids)}")
        if clip.dialogue_lines:
            pieces.append(f"dialogue_lines={len(clip.dialogue_lines)}")
        if clip.action_beats:
            action_beats = [
                remove_dialogue_quotes(beat, clip.dialogue_lines)
                for beat in clip.action_beats[:2]
            ]
            pieces.append(f"action={'; '.join(action_beats)}")
        pieces.append(f"rationale={clip.rationale}")
        lines.append(" | ".join(pieces))
    return "\n".join(lines)


def _render_clip_plan_notes(
    plan: RenderClipPlan | None,
    duration_seconds: float,
    *,
    render_clip: RenderClip | None = None,
) -> list[str]:
    if plan is None:
        return [
            "No render_clip_plan artifact was available; render prompt compilation "
            "could not verify scene-duration compression risk."
        ]
    if len(plan.clips) <= 1:
        return []
    if render_clip is not None:
        return [
            (
                f"Rendering planned clip {render_clip.clip_id} from a "
                f"{len(plan.clips)}-clip scene render plan."
            )
        ]
    return [
        (
            "Current scene-level render compresses a "
            f"{plan.target_dramatic_duration_seconds:g}s render-clip plan with "
            f"{len(plan.clips)} planned clips into one {duration_seconds:g}s provider clip; "
            "Story 194 owns multi-clip execution."
        )
    ]


def _exact_dialogue_lines_for_shot(shot: Any) -> list[str]:
    return [
        line.strip()
        for line in getattr(shot, "dialogue_lines", [])
        if isinstance(line, str) and line.strip()
    ]


def _exact_dialogue_lines_for_plan(plan: ShotPlan) -> list[str]:
    seen: set[str] = set()
    lines: list[str] = []
    for shot in plan.shots:
        for line in _exact_dialogue_lines_for_shot(shot):
            if line in seen:
                continue
            seen.add(line)
            lines.append(line)
    return lines


def _ensure_dialogue_prompt_contract(
    prompt_text: str,
    plan: ShotPlan,
    *,
    duration_seconds: float,
    render_clip: RenderClip | None = None,
) -> tuple[str, list[str]]:
    dialogue_lines = _exact_dialogue_lines_for_render_unit(plan, render_clip)
    if not dialogue_lines:
        return prompt_text, []

    notes: list[str] = []
    normalized_prompt = _normalize_dialogue_text(prompt_text)
    missing = [
        line
        for line in dialogue_lines
        if _normalize_dialogue_text(line) not in normalized_prompt
    ]
    updated_prompt = prompt_text.rstrip()
    if missing:
        updated_prompt += "\n\n" + _dialogue_timing_contract(
            plan,
            duration_seconds=duration_seconds,
            render_clip=render_clip,
        )
        sample = "; ".join(missing[:3])
        if len(missing) > 3:
            sample += f"; +{len(missing) - 3} more"
        punctuation = "" if sample.endswith((".", "!", "?")) else "."
        notes.append(
            "Adapter appended a dialogue timing contract from the shot plan because "
            f"the compiler omitted: {sample}{punctuation}"
        )

    cadence_guidance, cadence_note = _dialogue_cadence_guidance(
        dialogue_lines=dialogue_lines,
        duration_seconds=duration_seconds,
    )
    normalized_updated = _normalize_dialogue_text(updated_prompt)
    normalized_cadence = _normalize_dialogue_text(cadence_guidance)
    if cadence_guidance and normalized_cadence not in normalized_updated:
        updated_prompt += "\n\n" + cadence_guidance
        notes.append(cadence_note)

    return updated_prompt, notes


def _exact_dialogue_lines_for_render_unit(
    plan: ShotPlan,
    render_clip: RenderClip | None,
) -> list[str]:
    if render_clip is not None:
        return render_clip_dialogue_lines(render_clip)
    return _exact_dialogue_lines_for_plan(plan)


def _dialogue_timing_contract(
    plan: ShotPlan,
    *,
    duration_seconds: float | None,
    render_clip: RenderClip | None = None,
) -> str:
    dialogue_lines = _exact_dialogue_lines_for_render_unit(plan, render_clip)
    if not dialogue_lines:
        return ""
    lines = [
        "Dialogue timing / exact lines:",
        (
            "- Single dialogue pass: include each line once, in this order, "
            "with one speaker at a time."
        ),
        (
            "- Cadence: leave a visible breath or reaction beat after each line; "
            "honor any planned silence or stillness cues from the shot action."
        ),
    ]
    density_guidance, _ = _dialogue_cadence_guidance(
        dialogue_lines=dialogue_lines,
        duration_seconds=duration_seconds,
    )
    if density_guidance:
        lines.append("- " + density_guidance.removeprefix("Dialogue cadence: "))
    if render_clip is not None:
        lines.append(
            f"- {render_clip.clip_id} "
            f"(render clip, about {render_clip.target_duration_seconds:.1f}s):"
        )
        for line in dialogue_lines:
            lines.append(f"  - {line}")
        return "\n".join(lines)

    for shot in plan.shots:
        dialogue = _exact_dialogue_lines_for_shot(shot)
        if not dialogue:
            continue
        lines.append(
            f"- {shot.shot_id} ({shot.shot_size}, about {shot.duration_estimate_seconds:.1f}s):"
        )
        for line in dialogue:
            lines.append(f"  - {line}")
    return "\n".join(lines)


def _dialogue_cadence_guidance(
    *,
    dialogue_lines: list[str],
    duration_seconds: float | None,
) -> tuple[str, str]:
    if not dialogue_lines:
        return "", ""
    estimated_spoken_seconds = _estimated_dialogue_seconds(dialogue_lines)
    if duration_seconds and estimated_spoken_seconds > (duration_seconds * 0.8):
        return (
            "Dialogue cadence: This is dialogue-dense for the requested "
            f"{duration_seconds:g}s clip; keep delivery terse but distinct, with clear "
            "breaths and reaction beats instead of back-to-back rapid-fire speech.",
            "Adapter added dialogue cadence guidance because the exact line count is dense "
            f"for the requested {duration_seconds:g}s render.",
        )
    return (
        "Dialogue cadence: Deliver the exact lines with distinct breaths and reaction beats, "
        "one speaker at a time.",
        "Adapter added dialogue cadence guidance for exact scripted lines.",
    )


def _estimated_dialogue_seconds(dialogue_lines: list[str]) -> float:
    word_count = 0
    for line in dialogue_lines:
        utterance = line.split(":", 1)[1] if ":" in line else line
        word_count += len(re.findall(r"[A-Za-z0-9']+", utterance))
    spoken_seconds = word_count / 2.7
    reaction_beats = max(len(dialogue_lines) - 1, 0) * 0.35
    return spoken_seconds + reaction_beats


def _normalize_dialogue_text(text: str) -> str:
    normalized = (
        text.replace("\u2018", "'")
        .replace("\u2019", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace('"', "")
        .replace("`", "")
    )
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = re.sub(r"\s+([:;,.!?])", r"\1", normalized)
    normalized = re.sub(r":\s*", ": ", normalized)
    return normalized.strip().casefold()


def _creative_brief_block(creative_brief: Any) -> str:
    if creative_brief is None:
        return ""
    lines = getattr(creative_brief, "summary_lines", None)
    if not isinstance(lines, list):
        return ""
    return "\n".join(line for line in lines if isinstance(line, str) and line.strip())


def _look_and_feel_block(look_and_feel: LookAndFeel | None) -> str:
    if look_and_feel is None:
        return ""
    lines = _nonempty_lines(
        [
            look_and_feel.lighting_concept,
            look_and_feel.color_palette,
            look_and_feel.composition_philosophy,
            look_and_feel.camera_personality,
            look_and_feel.costume_notes,
            look_and_feel.production_design_notes,
        ]
    )
    if look_and_feel.reference_imagery:
        lines.append(f"Reference imagery: {', '.join(look_and_feel.reference_imagery)}")
    return "\n".join(lines)


def _sound_block(
    sound_and_music: SoundAndMusic | None,
    *,
    resolved_inputs: list[RenderResolvedInput],
) -> str:
    lines: list[str] = []
    if sound_and_music is not None:
        lines.extend(
            _nonempty_lines(
                [
                    sound_and_music.ambient_environment,
                    sound_and_music.emotional_soundscape,
                    sound_and_music.silence_placement,
                    sound_and_music.sound_driven_transitions,
                    sound_and_music.music_intent,
                    sound_and_music.diegetic_non_diegetic_notes,
                ]
            )
        )
        if sound_and_music.offscreen_audio_cues:
            lines.append(f"Offscreen cues: {', '.join(sound_and_music.offscreen_audio_cues)}")
        if sound_and_music.reference_audio_assets:
            lines.append(
                f"Reference audio assets: {', '.join(sound_and_music.reference_audio_assets)}"
            )
    audio_inputs = [item for item in resolved_inputs if item.kind in _AUDIO_KINDS]
    if audio_inputs:
        labels = ", ".join(
            f"{item.label} ({item.lock_status or 'unlocked'})" for item in audio_inputs
        )
        lines.append(f"Injected audio context: {labels}")
    return "\n".join(lines)


def _performance_block(
    performance_entries: list[CharacterAndPerformance],
    *,
    plan: ShotPlan,
) -> str:
    lines: list[str] = []
    for entry in performance_entries:
        lines.append(
            " | ".join(
                _nonempty_lines(
                    [
                        entry.character_id,
                        entry.emotional_state_entering,
                        entry.emotional_arc,
                        entry.motivation,
                        entry.subtext,
                        entry.physical_notes,
                        entry.relationship_dynamics,
                        entry.blocking_notes,
                    ]
                )
            )
        )
    if lines:
        return "\n".join(lines)
    fallback = {character for shot in plan.shots for character in shot.characters_in_frame}
    if not fallback:
        return ""
    return (
        "No formal scene character/performance artifact exists. Use shot-planning behavior and "
        "blocking as fallback for: " + ", ".join(sorted(fallback))
    )


def _rhythm_block(rhythm_and_flow: RhythmAndFlow | None) -> str:
    if rhythm_and_flow is None:
        return ""
    lines = _nonempty_lines(
        [
            rhythm_and_flow.scene_function,
            rhythm_and_flow.pacing_intent,
            rhythm_and_flow.transition_in,
            rhythm_and_flow.transition_out,
            rhythm_and_flow.coverage_priority,
            rhythm_and_flow.camera_movement_dynamics,
            rhythm_and_flow.parallel_editing_notes,
            rhythm_and_flow.act_level_notes,
        ]
    )
    if rhythm_and_flow.montage_candidates:
        lines.append(f"Montage candidates: {', '.join(rhythm_and_flow.montage_candidates)}")
    return "\n".join(lines)


def _character_state_block(
    *,
    scene: Scene,
    character_bibles: dict[str, CharacterBible],
) -> str:
    lines: list[str] = []
    for character_id in scene.characters_present_ids:
        bible = character_bibles.get(_slugify(character_id))
        if bible is None:
            continue
        traits = ", ".join(f"{item.trait}={item.value}" for item in bible.inferred_traits[:4])
        summary = f"{bible.name}: {bible.description}"
        if traits:
            summary = f"{summary} | inferred_traits: {traits}"
        lines.append(summary)
    return "\n".join(lines)


def _location_state_block(
    *,
    scene: Scene,
    location_bibles: dict[str, LocationBible],
) -> str:
    bible = location_bibles.get(_slugify(scene.location))
    if bible is None:
        return ""
    parts = [bible.name, bible.description]
    if bible.physical_traits:
        parts.append(f"physical_traits: {', '.join(bible.physical_traits[:6])}")
    parts.append(f"narrative_significance: {bible.narrative_significance}")
    return " | ".join(parts)


def _keyframe_block(resolved_inputs: list[RenderResolvedInput]) -> str:
    lines = [
        f"{item.label} | used_as={item.used_as} | notes={item.notes or 'none'}"
        for item in resolved_inputs
        if item.kind == "keyframe"
    ]
    return "\n".join(lines)


def _injected_assets_block(resolved_inputs: list[RenderResolvedInput]) -> str:
    lines = [
        f"{item.label} | kind={item.kind} | used_as={item.used_as} | "
        f"lock={item.lock_status or 'unlocked'}"
        for item in resolved_inputs
        if item.kind != "keyframe"
    ]
    return "\n".join(lines)


def _finalize_prompt_sections(
    *,
    prompt_draft: Any,
    required_categories: list[str],
    context_blocks: dict[str, str],
    resolved_inputs: list[RenderResolvedInput],
    extra_source_artifact_types: list[str],
    notes: list[str],
) -> tuple[list[RenderPromptSection], RenderCompletenessCheck, list[str]]:
    sections: list[RenderPromptSection] = []
    covered: set[str] = set()
    required = {
        category.strip()
        for category in required_categories
        if isinstance(category, str) and category.strip()
    }
    for section in prompt_draft.sections:
        role, artifact_types = section_metadata(section.section_id)
        source_artifact_types = list(dict.fromkeys(section.source_artifact_types or artifact_types))
        sections.append(
            RenderPromptSection(
                section_id=section.section_id,
                title=section.title,
                body=section.body,
                source_role_id=section.source_role_id or role,
                source_artifact_types=source_artifact_types,
            )
        )
        covered.add(section.section_id)
    covered.update(item for item in prompt_draft.covered_categories if isinstance(item, str))
    reported_missing = {
        item.strip()
        for item in prompt_draft.missing_inputs
        if isinstance(item, str) and item.strip()
    }
    known_categories = known_prompt_categories()
    synthesized_categories: list[str] = []
    for category in sorted(required - covered):
        content = context_blocks.get(category, "").strip()
        if not content or category not in known_categories:
            continue
        role, artifact_types = section_metadata(category)
        sections.append(
            RenderPromptSection(
                section_id=category,
                title=section_title(category),
                body=content,
                source_role_id=role,
                source_artifact_types=artifact_types,
            )
        )
        covered.add(category)
        synthesized_categories.append(category)

    blocking_missing = {category for category in required if category not in covered}
    advisory_missing: set[str] = set()
    for item in reported_missing:
        if item not in known_categories:
            blocking_missing.add(item)
            continue
        if item in synthesized_categories:
            continue
        if item in required:
            blocking_missing.add(item)
            continue
        advisory_missing.add(item)
    missing = blocking_missing | advisory_missing
    prompt_sources = prompt_sources_from_sections(sections, resolved_inputs)
    for artifact_type in extra_source_artifact_types:
        if artifact_type not in prompt_sources:
            prompt_sources.append(artifact_type)
    synthesis_notes = list(notes)
    if synthesized_categories:
        synthesis_notes.append(
            "Adapter synthesized fallback sections for: "
            + ", ".join(synthesized_categories)
            + "."
        )
    completeness = RenderCompletenessCheck(
        included_categories=sorted(covered),
        missing_categories=sorted(missing),
        blocking_missing_categories=sorted(blocking_missing),
        advisory_missing_categories=sorted(advisory_missing),
        notes=[*prompt_draft.operator_notes, *synthesis_notes],
    )
    return sections, completeness, prompt_sources


def _prompt_artifact_dict(
    prompt_artifact: CompiledRenderPrompt,
    *,
    output_contract: dict[str, Any],
) -> dict[str, Any]:
    entity_id = _render_artifact_entity_id(
        prompt_artifact.scene_id, prompt_artifact.render_clip_id
    )
    return {
        "artifact_type": output_contract["prompt_artifact_type"],
        "entity_id": entity_id,
        "data": prompt_artifact.model_dump(mode="json"),
        "exclude_upstream_lineage_types": ["track_manifest"],
        "metadata": {
            "lineage": _lineage_dump(
                [
                    prompt_artifact.scene_ref,
                    prompt_artifact.shot_plan_ref,
                    prompt_artifact.render_clip_plan_ref,
                    prompt_artifact.keyframe_ref,
                    *[item.source_ref for item in prompt_artifact.resolved_inputs],
                ]
            ),
            "intent": output_contract["prompt_intent"],
            "rationale": output_contract["prompt_rationale"],
            "confidence": 0.9 if not prompt_artifact.completeness.missing_categories else 0.55,
            "source": "code" if output_contract["prompt_mode"] == "ai_previz" else "hybrid",
            "annotations": {
                "engine_pack_id": prompt_artifact.engine_pack_id,
                "render_unit": prompt_artifact.render_unit,
                "render_clip_id": prompt_artifact.render_clip_id,
                "target_provider": prompt_artifact.target_provider,
                "target_model": prompt_artifact.target_model,
                "compiler_model": prompt_artifact.compiler_model,
                "preview_mode": prompt_artifact.preview_provenance.mode
                if prompt_artifact.preview_provenance
                else None,
                "missing_categories": prompt_artifact.completeness.missing_categories,
                "blocking_missing_categories": (
                    prompt_artifact.completeness.blocking_missing_categories
                ),
                "advisory_missing_categories": (
                    prompt_artifact.completeness.advisory_missing_categories
                ),
            },
        },
    }


def _video_artifact_dict(
    *,
    generated_video: GeneratedVideoArtifact,
    prompt_artifact: CompiledRenderPrompt,
    compile_cost: dict[str, Any],
    request_notes: list[str],
    output_contract: dict[str, Any],
) -> dict[str, Any]:
    entity_id = _render_artifact_entity_id(
        generated_video.scene_id, generated_video.render_clip_id
    )
    return {
        "artifact_type": output_contract["video_artifact_type"],
        "entity_id": entity_id,
        "data": generated_video.model_dump(mode="json"),
        "include_stage_lineage": True,
        "exclude_upstream_lineage_types": ["track_manifest"],
        "metadata": {
            "lineage": _lineage_dump(
                [
                    generated_video.scene_ref,
                    generated_video.shot_plan_ref,
                    generated_video.render_clip_plan_ref,
                    generated_video.prompt_ref,
                    generated_video.keyframe_ref,
                    *[item.source_ref for item in generated_video.resolved_inputs],
                ]
            ),
            "intent": output_contract["video_intent"],
            "rationale": output_contract["video_rationale"],
            "confidence": 0.84 if not prompt_artifact.completeness.missing_categories else 0.5,
            "source": "hybrid",
            "annotations": {
                "engine_pack_id": generated_video.engine_pack_id,
                "render_unit": generated_video.render_unit,
                "render_clip_id": generated_video.render_clip_id,
                "target_provider": generated_video.target_provider,
                "target_model": generated_video.target_model,
                "duration_seconds": generated_video.duration_seconds,
                "resolution": generated_video.resolution,
                "aspect_ratio": generated_video.aspect_ratio,
                "request_notes": request_notes,
                "compile_model": compile_cost.get("model"),
            },
        },
    }


def _track_manifest_artifact_dict(
    *,
    updated_manifest: TrackManifest,
    track_manifest_ref: ArtifactRef,
    generated_video_refs: list[GeneratedVideoTrackRef],
) -> dict[str, Any]:
    refs = [item.artifact_ref for item in generated_video_refs]
    scene_ids = {item.scene_id for item in generated_video_refs}
    return {
        "artifact_type": "track_manifest",
        "entity_id": "project",
        "data": updated_manifest.model_dump(mode="json"),
        "include_stage_lineage": True,
        "metadata": {
            "lineage": _lineage_dump([track_manifest_ref, *refs]),
            "intent": "Updated track manifest with generated video entries.",
            "rationale": (
                "Generated video becomes the highest-fidelity playable track when "
                "scene renders are available."
            ),
            "confidence": 0.88,
            "source": "hybrid",
            "annotations": {
                "generated_scene_count": len(scene_ids),
                "generated_render_count": len(generated_video_refs),
                "generated_clip_count": len(
                    [item for item in generated_video_refs if item.render_clip_id]
                ),
            },
        },
    }


def _update_track_manifest_with_video_track(
    *,
    manifest: TrackManifest,
    generated_video_refs: list[GeneratedVideoTrackRef],
    track_type: str,
    priority: int,
    notes: str,
) -> TrackManifest:
    scene_ids = {item.scene_id for item in generated_video_refs}
    render_clip_ids = {
        item.render_clip_id for item in generated_video_refs if item.render_clip_id is not None
    }
    kept_entries = [
        entry
        for entry in manifest.entries
        if not (
            entry.track_type == track_type
            and entry.scene_id in scene_ids
            and (
                entry.render_clip_id is None
                or not render_clip_ids
                or entry.render_clip_id in render_clip_ids
            )
        )
    ]
    new_entries = list(kept_entries)
    for item in sorted(generated_video_refs, key=_generated_track_ref_sort_key):
        start_time, end_time = _track_entry_window(manifest, item)
        new_entries.append(
            TrackEntry(
                track_type=track_type,
                scene_id=item.scene_id,
                render_clip_id=item.render_clip_id,
                artifact_ref=item.artifact_ref,
                start_time_seconds=start_time,
                end_time_seconds=end_time,
                priority=priority,
                status="available",
                notes=notes,
            )
        )
    return manifest.model_copy(
        update={"entries": new_entries, "track_fill_counts": track_counts(new_entries)}
    )


def _generated_track_ref_sort_key(item: GeneratedVideoTrackRef) -> tuple[str, float, str]:
    return (
        item.scene_id,
        item.start_time_seconds if item.start_time_seconds is not None else -1.0,
        item.render_clip_id or "",
    )


def _track_entry_window(
    manifest: TrackManifest,
    item: GeneratedVideoTrackRef,
) -> tuple[float | None, float | None]:
    if item.render_clip_id is not None:
        return item.start_time_seconds, item.end_time_seconds
    return _scene_window_for_manifest(manifest, item.scene_id)


def _render_artifact_entity_id(scene_id: str, render_clip_id: str | None) -> str:
    if not render_clip_id:
        return scene_id
    if render_clip_id == scene_id or render_clip_id.startswith(f"{scene_id}_"):
        return render_clip_id
    return f"{scene_id}__{render_clip_id}"


def _scene_window_for_manifest(
    manifest: TrackManifest,
    scene_id: str,
) -> tuple[float | None, float | None]:
    for entry in manifest.entries:
        if entry.scene_id != scene_id:
            continue
        if entry.shot_id is None and entry.start_time_seconds is not None:
            return entry.start_time_seconds, entry.end_time_seconds
    return None, None


def _lineage_dump(refs: list[ArtifactRef | None]) -> list[dict[str, Any]]:
    return [
        ref.model_dump(mode="json") for ref in dedupe_refs([ref for ref in refs if ref is not None])
    ]


def _scene_cost(
    *,
    compile_cost: dict[str, Any],
    generation_model: str,
    request_id: str | None,
) -> dict[str, Any]:
    return {
        "model": _merge_model_labels(compile_cost.get("model"), generation_model),
        "input_tokens": int(compile_cost.get("input_tokens", 0) or 0),
        "output_tokens": int(compile_cost.get("output_tokens", 0) or 0),
        "estimated_cost_usd": float(compile_cost.get("estimated_cost_usd", 0.0) or 0.0),
        "latency_seconds": compile_cost.get("latency_seconds"),
        "request_id": request_id or compile_cost.get("request_id"),
    }


def _preview_cost_value(
    *,
    scene_cost: dict[str, Any],
    output_contract: dict[str, Any],
) -> float | None:
    if output_contract["prompt_mode"] == "ai_previz":
        return None
    return float(scene_cost.get("estimated_cost_usd", 0.0) or 0.0)


def _empty_cost(*, model: str) -> dict[str, Any]:
    return {
        "model": model,
        "input_tokens": 0,
        "output_tokens": 0,
        "estimated_cost_usd": 0.0,
    }


def _merge_cost(total: dict[str, Any], cost: dict[str, Any]) -> None:
    total["model"] = _merge_model_labels(total.get("model"), cost.get("model"))
    total["input_tokens"] += int(cost.get("input_tokens", 0) or 0)
    total["output_tokens"] += int(cost.get("output_tokens", 0) or 0)
    total["estimated_cost_usd"] = round(
        float(total["estimated_cost_usd"]) + float(cost.get("estimated_cost_usd", 0.0) or 0.0),
        8,
    )


def _merge_model_labels(*values: Any) -> str:
    labels = {
        item.strip() for value in values for item in str(value or "").split("+") if item.strip()
    }
    return "+".join(sorted(labels)) if labels else "code"


def _optional_string(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _look_and_feel_aspect_ratio(look_and_feel: LookAndFeel | None) -> str | None:
    if look_and_feel is None:
        return None
    return _optional_string(look_and_feel.aspect_ratio_override)


def _render_upstream_inputs(
    *,
    prompt_sources: list[str],
    resolved_inputs: list[RenderResolvedInput],
) -> list[str]:
    labels = set(prompt_sources)
    labels.update(item.kind for item in resolved_inputs)
    return sorted(labels)


def _project_aspect_ratio(project_config: ProjectConfig | None) -> str | None:
    if project_config is None:
        return None
    return _optional_string(project_config.aspect_ratio)


def _resolve_resolution(
    *,
    requested_resolution: str | None,
    engine_pack: Any,
    aspect_ratio: str,
) -> tuple[str, str | None]:
    supported = list(engine_pack.limits.supported_resolutions)
    if requested_resolution:
        if requested_resolution in supported:
            return requested_resolution, None
        return supported[0], (
            f"Resolution '{requested_resolution}' is not supported by {engine_pack.pack_id}; "
            f"defaulted to {supported[0]}."
        )
    defaults = engine_pack.request_defaults
    if aspect_ratio == "9:16":
        portrait = defaults.get("portrait_size") or defaults.get("default_resolution")
        if isinstance(portrait, str) and portrait in supported:
            return portrait, None
        for candidate in supported:
            if candidate.endswith("x1280") or candidate == "720p":
                return candidate, None
    landscape = defaults.get("landscape_size") or defaults.get("default_resolution")
    if isinstance(landscape, str) and landscape in supported:
        return landscape, None
    return supported[0], None


def _video_reference(
    project_dir: Path, item: RenderResolvedInput | None
) -> VideoReferenceInput | None:
    if item is None or not item.relative_path:
        return None
    media_type = _resolved_media_type(item)
    if media_type is None:
        return None
    return VideoReferenceInput(
        path=project_dir / item.relative_path,
        media_type=media_type,
        usage=item.used_as,
    )


def _pop_priority_input(
    items: list[RenderResolvedInput],
    *,
    predicate: Any,
) -> RenderResolvedInput | None:
    for index, item in enumerate(items):
        if predicate(item):
            return items.pop(index)
    return None


def _manifest_asset_kind(target_kind: str, asset_type: str) -> str:
    if asset_type == "audio":
        return "scene_injected_audio" if target_kind == "scene" else "project_injected_audio"
    if target_kind == "character":
        return "character_injected_image"
    if target_kind == "location":
        return "location_injected_image"
    if target_kind == "prop":
        return "prop_injected_image"
    return "scene_injected_image" if target_kind == "scene" else "project_injected_image"


def _image_input_priority_key(item: RenderResolvedInput) -> tuple[int, int, int, str]:
    return (
        0 if item.required else 1,
        _lock_priority_rank(item.lock_status),
        _kind_priority_rank(item.kind),
        item.label.lower(),
    )


def _lock_priority_rank(lock_status: str | None) -> int:
    if lock_status == "hard_locked":
        return 0
    if lock_status == "selected_visual_reference":
        return 1
    if lock_status == "system_default_visual_reference":
        return 2
    if lock_status == "soft_locked":
        return 3
    if lock_status == "unlocked":
        return 4
    return 5


def _kind_priority_rank(kind: str | None) -> int:
    if kind == "keyframe":
        return 0
    if kind == "character_injected_image":
        return 1
    if kind == "location_injected_image":
        return 2
    if kind == "prop_injected_image":
        return 3
    if kind == "scene_injected_image":
        return 4
    if kind == "project_injected_image":
        return 5
    return 6


def _slugify(value: str) -> str:
    return _SLUG_RE.sub("_", value.strip().lower()).strip("_")


def _nonempty_lines(values: list[str | None]) -> list[str]:
    return [value.strip() for value in values if isinstance(value, str) and value.strip()]


def _resolved_media_type(item: RenderResolvedInput) -> str | None:
    media_type = item.media_type or media_type_for_image(item.relative_path or "")
    if media_type in {"image/jpeg", "image/png", "image/webp"}:
        return media_type
    return None


def _is_uploadable_raster_image(item: RenderResolvedInput) -> bool:
    return _resolved_media_type(item) is not None
