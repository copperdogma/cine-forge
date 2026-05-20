"""Scene-level render adapter module."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from cine_forge.ai.video import (
    VideoGenerationRequest,
    generate_video,
)
from cine_forge.artifacts import ArtifactStore
from cine_forge.modules.generation.render_adapter_v1.dialogue_contracts import (
    _ensure_dialogue_prompt_contract,
)
from cine_forge.modules.generation.render_adapter_v1.orchestration import (
    _ensure_required_render_clip_plans,
    _planned_render_unit_count,
    _render_failure_summary,
    _render_scene_outputs,
)
from cine_forge.modules.generation.render_adapter_v1.outputs import (
    GeneratedVideoTrackRef,
    _build_preview_provenance,
    _empty_cost,
    _merge_cost,
    _merge_model_labels,
    _prompt_artifact_dict,
    _scene_cost,
    _track_manifest_artifact_dict,
    _update_track_manifest_with_video_track,
    _video_artifact_dict,
)
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
from cine_forge.modules.generation.render_adapter_v1.render_units import (
    clipped_shot_plan,
    render_clip_time_note,
    render_unit_entity_id,
    render_unit_kind,
)
from cine_forge.modules.generation.render_adapter_v1.request_shaping import (
    _shape_generation_request,
)
from cine_forge.modules.generation.render_adapter_v1.resolved_inputs import (
    _collect_resolved_inputs,
    _look_and_feel_aspect_ratio,
    _project_aspect_ratio,
    _resolve_resolution,
)
from cine_forge.modules.generation.render_adapter_v1.support import (
    anticipated_entity_ref,
    latest_entity_ref,
    latest_project_ref,
    load_engine_pack,
    normalize_aspect_ratio,
    normalize_duration_seconds,
    relative_path,
    render_media_dir,
)
from cine_forge.modules.generation.render_adapter_v1.support import (
    optional_string as _optional_string,
)
from cine_forge.modules.generation.render_adapter_v1.support import (
    slugify as _slugify,
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
    ProjectConfig,
    RenderClip,
    RenderClipPlan,
    RhythmAndFlow,
    Scene,
    ShotPlan,
    SoundAndMusic,
    TrackManifest,
)
from cine_forge.schemas.scene_scope import SceneActionPreflight
from cine_forge.services.creative_brief import (
    build_visual_creative_brief,
    creative_brief_source_artifact_types,
)
from cine_forge.services.design_study_backfill import (
    DEFAULT_DESIGN_STUDY_BACKFILL_MODEL,
)


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
            render_scene=_render_scene,
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
