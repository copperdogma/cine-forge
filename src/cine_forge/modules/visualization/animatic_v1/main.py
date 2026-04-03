"""Deterministic animatic composition from shot plans and storyboard stills."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from cine_forge.artifacts import ArtifactStore
from cine_forge.modules.visualization.animatic_v1.annotated import (
    compose_annotated_segment_video,
)
from cine_forge.modules.visualization.animatic_v1.support import (
    DEFAULT_FPS,
    DEFAULT_FRAME_HEIGHT,
    DEFAULT_FRAME_WIDTH,
    animatic_lineage,
    animatic_media_dir,
    anticipated_entity_ref,
    anticipated_project_ref,
    audio_references_for_scene,
    choose_primary_audio,
    compose_segment_video,
    concat_videos,
    ensure_ffmpeg,
    frame_for_shot,
    latest_project_ref,
    load_or_placeholder_image,
    mux_audio_track,
    normalized_duration,
    previz_lineage,
    previz_media_dir,
    relative_media_file,
    relative_path,
    sound_and_music_by_scene,
    storyboard_by_scene,
    track_counts,
)
from cine_forge.schemas import (
    Animatic,
    AnimaticSegment,
    ArtifactRef,
    MediaFile,
    PreviewProvenance,
    PrevizReel,
    PrevizSceneSegment,
    Scene,
    ShotPlan,
    TrackEntry,
    TrackManifest,
)


def run_module(
    inputs: dict[str, Any], params: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    """Generate per-scene animatics and a project-level previz reel."""
    project_dir_raw = context.get("project_dir")
    if not isinstance(project_dir_raw, str) or not project_dir_raw:
        raise ValueError("animatic_v1 requires context.project_dir")

    project_dir = Path(project_dir_raw)
    store = ArtifactStore(project_dir=project_dir)
    ffmpeg = ensure_ffmpeg()
    fps = int(params.get("fps") or DEFAULT_FPS)
    width = int(params.get("frame_width") or DEFAULT_FRAME_WIDTH)
    height = int(params.get("frame_height") or DEFAULT_FRAME_HEIGHT)
    previz_mode = _previz_mode(params)

    track_manifest_payload = inputs.get("track_manifest")
    if not isinstance(track_manifest_payload, dict):
        raise ValueError("animatic_v1 requires track_manifest input")
    track_manifest = TrackManifest.model_validate(track_manifest_payload)

    shot_plan_payloads = inputs.get("shot_plan")
    if not isinstance(shot_plan_payloads, list) or not shot_plan_payloads:
        raise ValueError("animatic_v1 requires one or more shot_plan inputs")
    shot_plans = [
        ShotPlan.model_validate(item) for item in shot_plan_payloads if isinstance(item, dict)
    ]
    if not shot_plans:
        raise ValueError("animatic_v1 could not parse any shot_plan inputs")

    storyboard_map = storyboard_by_scene(inputs.get("storyboard"))
    sound_map = sound_and_music_by_scene(inputs.get("sound_and_music"))

    animatic_artifacts: list[dict[str, Any]] = []
    animatics_by_scene: dict[str, Animatic] = {}
    animatic_refs: dict[str, ArtifactRef] = {}

    for plan in sorted(shot_plans, key=lambda item: item.scene_number):
        scene_artifact = store.load_artifact(plan.scene_ref)
        scene = Scene.model_validate(scene_artifact.data)
        animatic_ref = anticipated_entity_ref(store, "animatic", plan.scene_id)
        animatic = build_scene_animatic(
            store=store,
            ffmpeg=ffmpeg,
            scene=scene,
            plan=plan,
            animatic_ref=animatic_ref,
            storyboard_data=storyboard_map.get(plan.scene_id),
            sound_and_music_data=sound_map.get(plan.scene_id),
            width=width,
            height=height,
            fps=fps,
            previz_mode=previz_mode,
        )
        animatics_by_scene[plan.scene_id] = animatic
        animatic_refs[plan.scene_id] = animatic_ref
        animatic_artifacts.append(
            {
                "artifact_type": "animatic",
                "entity_id": plan.scene_id,
                "data": animatic.model_dump(mode="json"),
                "metadata": {
                    "lineage": [
                        ref.model_dump(mode="json")
                        for ref in animatic_lineage(
                            store=store,
                            scene_id=plan.scene_id,
                            storyboard_present=plan.scene_id in storyboard_map,
                            sound_and_music_present=plan.scene_id in sound_map,
                        )
                    ],
                    "intent": "Scene-level animatic for timing, motion, and rough review.",
                    "rationale": (
                        "Animatic composition reuses storyboard stills and shot timing to create"
                        " a cheap time-based visualization before render."
                    ),
                    "confidence": scene_animatic_confidence(plan),
                    "source": "hybrid",
                    "annotations": {
                        "segment_count": len(animatic.segments),
                        "audio_ref_count": len(animatic.audio_refs),
                        "source_mix": animatic.source_mix,
                    },
                },
            }
        )

    track_manifest_ref = latest_project_ref(store, "track_manifest")
    if track_manifest_ref is None:
        raise ValueError("animatic_v1 could not resolve latest track_manifest artifact")

    updated_manifest = update_track_manifest_with_animatics(
        manifest=track_manifest,
        animatics_by_scene=animatics_by_scene,
        animatic_refs=animatic_refs,
    )
    animatic_artifacts.append(
        {
            "artifact_type": "track_manifest",
            "entity_id": "project",
            "data": updated_manifest.model_dump(mode="json"),
            "include_stage_lineage": True,
            "metadata": {
                "lineage": [track_manifest_ref.model_dump(mode="json")],
                "intent": "Updated track manifest with animatic entries.",
                "rationale": (
                    "Animatics become the highest available watchable representation before"
                    " generated video exists."
                ),
                "confidence": average_confidence(animatics_by_scene.values()),
                "source": "hybrid",
            },
        }
    )

    previz_ref = anticipated_project_ref(store, "previz_reel")
    previz_reel = build_previz_reel(
        store=store,
        ffmpeg=ffmpeg,
        previz_ref=previz_ref,
        track_manifest_ref=anticipated_project_ref(store, "track_manifest"),
        timeline_ref=track_manifest.timeline_ref,
        shot_plans=shot_plans,
        animatics_by_scene=animatics_by_scene,
        animatic_refs=animatic_refs,
        fps=fps,
        width=width,
        height=height,
    )
    animatic_artifacts.append(
        {
            "artifact_type": "previz_reel",
            "entity_id": "project",
            "data": previz_reel.model_dump(mode="json"),
            "metadata": {
                "lineage": [
                    ref.model_dump(mode="json")
                    for ref in previz_lineage(
                        timeline_ref=track_manifest.timeline_ref,
                        track_manifest_ref=track_manifest_ref,
                        scene_refs=list(animatic_refs.values()),
                    )
                ],
                "intent": (
                    "Project-level playable previz reel assembled from available "
                    "scene animatics."
                ),
                "rationale": (
                    "Previz reel lets the operator watch the current assembly without leaving"
                    " the artifact system."
                ),
                "confidence": average_confidence(animatics_by_scene.values()),
                "source": "hybrid",
            },
        }
    )

    return {
        "artifacts": animatic_artifacts,
        "cost": {
            "model": "code+ffmpeg",
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": 0.0,
        },
    }


def build_scene_animatic(
    *,
    store: ArtifactStore,
    ffmpeg: str,
    scene: Scene,
    plan: ShotPlan,
    animatic_ref: ArtifactRef,
    storyboard_data: dict[str, Any] | None,
    sound_and_music_data: dict[str, Any] | None,
    width: int,
    height: int,
    fps: int,
    previz_mode: str,
) -> Animatic:
    started = time.perf_counter()
    media_dir = animatic_media_dir(store.project_dir, plan.scene_id, animatic_ref.version)
    media_dir.mkdir(parents=True, exist_ok=True)

    segments: list[AnimaticSegment] = []
    segment_paths: list[Path] = []
    audio_refs = audio_references_for_scene(
        project_dir=store.project_dir,
        scene_id=plan.scene_id,
        sound_and_music_data=sound_and_music_data,
    )

    for idx, shot in enumerate(plan.shots, start=1):
        frame_data = frame_for_shot(storyboard_data, shot.shot_id)
        source_image_path = extract_storyboard_image_path(frame_data)
        image_path, source_kind = load_or_placeholder_image(
            project_dir=store.project_dir,
            media_dir=media_dir,
            scene_heading=plan.scene_heading,
            shot=shot,
            source_path=source_image_path,
            width=width,
            height=height,
        )
        segment_output = media_dir / f"segment_{idx:02d}_{shot.shot_id.lower()}.mp4"
        if previz_mode == "annotated_symbolic":
            segment_video = compose_annotated_segment_video(
                ffmpeg=ffmpeg,
                image_path=image_path,
                output_path=segment_output,
                duration_seconds=shot.duration_estimate_seconds,
                camera_movement=shot.camera_movement,
                width=width,
                height=height,
                fps=fps,
                scene_heading=plan.scene_heading,
                shot_id=shot.shot_id,
                shot_size=shot.shot_size,
                camera_angle=shot.camera_angle,
                characters=shot.characters_in_frame,
                edit_intent=shot.edit_intent,
            )
        else:
            segment_video = compose_segment_video(
                ffmpeg=ffmpeg,
                image_path=image_path,
                output_path=segment_output,
                duration_seconds=shot.duration_estimate_seconds,
                camera_movement=shot.camera_movement,
                width=width,
                height=height,
                fps=fps,
            )
        segment_paths.append(segment_output)
        segments.append(
            AnimaticSegment(
                segment_id=f"{plan.scene_id}_segment_{idx:02d}",
                shot_id=shot.shot_id,
                storyboard_frame_id=(
                    frame_data.get("frame_id") if isinstance(frame_data, dict) else None
                ),
                source_kind=source_kind,
                source_image_path=source_image_path,
                video=relative_media_file(store.project_dir, segment_video),
                duration_seconds=normalized_duration(shot.duration_estimate_seconds),
                shot_size=shot.shot_size,
                camera_angle=shot.camera_angle,
                camera_movement=shot.camera_movement,
                characters_in_frame=shot.characters_in_frame,
                edit_intent=shot.edit_intent,
                notes=shot.action_description,
            )
        )

    scene_video_temp = media_dir / "scene_animatic_video_only.mp4"
    concat_videos(ffmpeg=ffmpeg, input_paths=segment_paths, output_path=scene_video_temp)
    scene_video_output = media_dir / "scene_animatic.mp4"
    mux_audio_track(
        ffmpeg=ffmpeg,
        project_dir=store.project_dir,
        video_path=scene_video_temp,
        output_path=scene_video_output,
        audio_ref=choose_primary_audio(audio_refs),
    )

    storyboard_ref = latest_ref_or_none(store, "storyboard", plan.scene_id)
    sound_ref = latest_ref_or_none(store, "sound_and_music", plan.scene_id)
    latency_ms = round((time.perf_counter() - started) * 1000)

    return Animatic(
        scene_id=plan.scene_id,
        scene_number=plan.scene_number,
        scene_heading=plan.scene_heading,
        scene_ref=plan.scene_ref,
        shot_plan_ref=latest_ref_or_none(store, "shot_plan", plan.scene_id) or plan.scene_ref,
        storyboard_ref=storyboard_ref,
        sound_and_music_ref=sound_ref,
        video=MediaFile(
            relative_path=relative_path(store.project_dir, scene_video_output),
            media_type="video/mp4",
            duration_seconds=sum(segment.duration_seconds for segment in segments),
        ),
        segments=segments,
        audio_refs=audio_refs,
        total_duration_seconds=sum(segment.duration_seconds for segment in segments),
        source_mix=sorted({segment.source_kind for segment in segments}),
        preview_provenance=PreviewProvenance(
            mode=previz_mode,
            fidelity_intent=(
                "blocking_review" if previz_mode == "annotated_symbolic" else "symbolic_baseline"
            ),
            intended_use=["human_review"],
            upstream_inputs=_animatic_upstream_inputs(
                storyboard_ref=storyboard_ref,
                sound_ref=sound_ref,
            ),
            estimated_cost_usd=0.0,
            generation_latency_ms=latency_ms,
        ),
    )


def build_previz_reel(
    *,
    store: ArtifactStore,
    ffmpeg: str,
    previz_ref: ArtifactRef,
    track_manifest_ref: ArtifactRef,
    timeline_ref: ArtifactRef,
    shot_plans: list[ShotPlan],
    animatics_by_scene: dict[str, Animatic],
    animatic_refs: dict[str, ArtifactRef],
    fps: int,
    width: int,
    height: int,
) -> PrevizReel:
    media_dir = previz_media_dir(store.project_dir, previz_ref.version)
    media_dir.mkdir(parents=True, exist_ok=True)
    scene_items: list[PrevizSceneSegment] = []
    input_paths: list[Path] = []

    for plan in sorted(shot_plans, key=lambda item: item.scene_number):
        animatic = animatics_by_scene.get(plan.scene_id)
        if animatic is None:
            continue
        clip_path = store.project_dir / animatic.video.relative_path
        input_paths.append(clip_path)
        scene_items.append(
            PrevizSceneSegment(
                scene_id=plan.scene_id,
                scene_number=plan.scene_number,
                scene_heading=plan.scene_heading,
                source_track_type="animatics",
                artifact_ref=animatic_refs[plan.scene_id],
                video=animatic.video,
                audio_refs=animatic.audio_refs,
                duration_seconds=animatic.total_duration_seconds,
                notes="Scene animatic selected as the best available representation.",
                preview_provenance=animatic.preview_provenance,
            )
        )

    if not input_paths:
        raise ValueError("animatic_v1 could not assemble a previz reel without scene clips")

    reel_output = media_dir / "previz_reel.mp4"
    concat_videos(ffmpeg=ffmpeg, input_paths=input_paths, output_path=reel_output)
    return PrevizReel(
        timeline_ref=timeline_ref,
        track_manifest_ref=track_manifest_ref,
        reel_video=MediaFile(
            relative_path=relative_path(store.project_dir, reel_output),
            media_type="video/mp4",
            duration_seconds=sum(item.duration_seconds for item in scene_items),
        ),
        scenes=scene_items,
        total_duration_seconds=sum(item.duration_seconds for item in scene_items),
    )


def _previz_mode(params: dict[str, Any]) -> str:
    raw = params.get("previz_mode")
    if raw is None:
        return "annotated_symbolic"
    value = str(raw).strip().lower()
    if value not in {"symbolic", "annotated_symbolic"}:
        raise ValueError("animatic_v1 previz_mode must be 'symbolic' or 'annotated_symbolic'")
    return value


def _animatic_upstream_inputs(
    *,
    storyboard_ref: ArtifactRef | None,
    sound_ref: ArtifactRef | None,
) -> list[str]:
    inputs = ["scene", "shot_plan"]
    if storyboard_ref is not None:
        inputs.append("storyboard")
    if sound_ref is not None:
        inputs.append("sound_and_music")
    return inputs


def extract_storyboard_image_path(frame_data: dict[str, Any] | None) -> str | None:
    if not isinstance(frame_data, dict):
        return None
    image_data = frame_data.get("image")
    if not isinstance(image_data, dict):
        return None
    relative_path = image_data.get("relative_path")
    return relative_path if isinstance(relative_path, str) else None


def latest_ref_or_none(
    store: ArtifactStore, artifact_type: str, entity_id: str
) -> ArtifactRef | None:
    refs = store.list_versions(artifact_type, entity_id)
    return refs[-1] if refs else None


def scene_animatic_confidence(plan: ShotPlan) -> float:
    values = [plan.coverage_strategy.audit.confidence]
    values.extend(shot.audit.confidence for shot in plan.shots)
    return round(sum(values) / len(values), 4) if values else 0.0


def average_confidence(animatics: Any) -> float:
    values = [scene.total_duration_seconds for scene in animatics]
    if not values:
        return 0.0
    return 0.9


def update_track_manifest_with_animatics(
    *,
    manifest: TrackManifest,
    animatics_by_scene: dict[str, Animatic],
    animatic_refs: dict[str, ArtifactRef],
) -> TrackManifest:
    animatic_scene_ids = set(animatics_by_scene)
    kept_entries = [
        entry
        for entry in manifest.entries
        if not (entry.track_type == "animatics" and entry.scene_id in animatic_scene_ids)
    ]
    new_entries = list(kept_entries)
    for scene_id in sorted(animatic_scene_ids):
        animatic = animatics_by_scene[scene_id]
        animatic_ref = animatic_refs[scene_id]
        for idx, segment in enumerate(animatic.segments, start=1):
            new_entries.append(
                TrackEntry(
                    track_type="animatics",
                    scene_id=scene_id,
                    shot_id=segment.shot_id,
                    artifact_ref=animatic_ref,
                    priority=150 + idx,
                    status="available",
                    notes=segment.edit_intent,
                )
            )
    return manifest.model_copy(
        update={"entries": new_entries, "track_fill_counts": track_counts(new_entries)}
    )
