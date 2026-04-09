"""Keyframe extraction from storyboard sources."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image

from cine_forge.artifacts import ArtifactStore
from cine_forge.modules.visualization.keyframe_v1.support import (
    DEFAULT_FRAME_HEIGHT,
    DEFAULT_FRAME_WIDTH,
    anticipated_entity_ref,
    create_placeholder_image,
    derive_motion_crop,
    frame_for_shot,
    keyframe_media_dir,
    latest_entity_ref,
    latest_project_ref,
    load_or_placeholder_image,
    open_image_or_none,
    relative_path,
    storyboard_by_scene,
    track_counts,
)
from cine_forge.pipeline.scene_actions import filter_scene_payloads
from cine_forge.schemas import (
    ArtifactRef,
    Keyframe,
    KeyframeArtifact,
    MediaFile,
    Scene,
    ShotPlan,
    TrackEntry,
    TrackManifest,
)


def run_module(
    inputs: dict[str, Any], params: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    """Generate per-scene keyframe artifacts."""
    project_dir_raw = context.get("project_dir")
    if not isinstance(project_dir_raw, str) or not project_dir_raw:
        raise ValueError("keyframe_v1 requires context.project_dir")

    project_dir = Path(project_dir_raw)
    store = ArtifactStore(project_dir=project_dir)
    width = int(params.get("frame_width") or DEFAULT_FRAME_WIDTH)
    height = int(params.get("frame_height") or DEFAULT_FRAME_HEIGHT)

    track_manifest_payload = inputs.get("track_manifest")
    if not isinstance(track_manifest_payload, dict):
        raise ValueError("keyframe_v1 requires track_manifest input")
    track_manifest = TrackManifest.model_validate(track_manifest_payload)

    shot_plan_payloads = inputs.get("shot_plan")
    if not isinstance(shot_plan_payloads, list) or not shot_plan_payloads:
        raise ValueError("keyframe_v1 requires one or more shot_plan inputs")
    runtime_params = context.get("runtime_params", {}) if isinstance(context, dict) else {}
    if not isinstance(runtime_params, dict):
        runtime_params = {}
    shot_plan_payloads = filter_scene_payloads(shot_plan_payloads, runtime_params)
    shot_plans = [
        ShotPlan.model_validate(item) for item in shot_plan_payloads if isinstance(item, dict)
    ]
    if not shot_plans:
        raise ValueError("keyframe_v1 could not parse any shot_plan inputs")

    storyboard_map = storyboard_by_scene(inputs.get("storyboard"))

    keyframe_artifacts: list[dict[str, Any]] = []
    keyframes_by_scene: dict[str, KeyframeArtifact] = {}
    keyframe_refs: dict[str, ArtifactRef] = {}

    for plan in sorted(shot_plans, key=lambda item: item.scene_number):
        scene_artifact = store.load_artifact(plan.scene_ref)
        scene = Scene.model_validate(scene_artifact.data)
        keyframe_ref = anticipated_entity_ref(store, "keyframe", plan.scene_id)
        keyframe_artifact = build_keyframes_for_scene(
            store=store,
            scene=scene,
            plan=plan,
            keyframe_ref=keyframe_ref,
            storyboard_data=storyboard_map.get(plan.scene_id),
            width=width,
            height=height,
        )
        keyframes_by_scene[plan.scene_id] = keyframe_artifact
        keyframe_refs[plan.scene_id] = keyframe_ref
        keyframe_artifacts.append(
            {
                "artifact_type": "keyframe",
                "entity_id": plan.scene_id,
                "data": keyframe_artifact.model_dump(mode="json"),
                "metadata": {
                    "lineage": [
                        ref.model_dump(mode="json")
                        for ref in keyframe_lineage(
                            store=store,
                            scene_id=plan.scene_id,
                            storyboard_present=plan.scene_id in storyboard_map,
                        )
                    ],
                    "intent": "Lockable start/mid/end frames for render constraints and review.",
                    "rationale": (
                        "Keyframes give the operator a stable visual constraint layer above"
                        " storyboard review."
                    ),
                    "confidence": 0.92,
                    "source": "hybrid",
                    "annotations": {"keyframe_count": len(keyframe_artifact.keyframes)},
                },
            }
        )

    track_manifest_ref = latest_project_ref(store, "track_manifest")
    if track_manifest_ref is None:
        raise ValueError("keyframe_v1 could not resolve latest track_manifest artifact")

    updated_manifest = update_track_manifest_with_keyframes(
        manifest=track_manifest,
        keyframes_by_scene=keyframes_by_scene,
        keyframe_refs=keyframe_refs,
    )
    keyframe_artifacts.append(
        {
            "artifact_type": "track_manifest",
            "entity_id": "project",
            "data": updated_manifest.model_dump(mode="json"),
            "include_stage_lineage": True,
            "metadata": {
                "lineage": [track_manifest_ref.model_dump(mode="json")],
                "intent": "Updated track manifest with keyframe entries.",
                "rationale": "Keyframes become available as downstream render constraints.",
                "confidence": 0.92,
                "source": "hybrid",
            },
        }
    )

    return {
        "artifacts": keyframe_artifacts,
        "cost": {
            "model": "code",
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": 0.0,
        },
    }


def build_keyframes_for_scene(
    *,
    store: ArtifactStore,
    scene: Scene,
    plan: ShotPlan,
    keyframe_ref: ArtifactRef,
    storyboard_data: dict[str, Any] | None,
    width: int,
    height: int,
) -> KeyframeArtifact:
    media_dir = keyframe_media_dir(store.project_dir, plan.scene_id, keyframe_ref.version)
    media_dir.mkdir(parents=True, exist_ok=True)

    keyframes: list[Keyframe] = []
    elapsed_seconds = 0.0
    for shot in plan.shots:
        frame_data = frame_for_shot(storyboard_data, shot.shot_id)
        source_image_path = extract_storyboard_image_path(frame_data)
        source_path, source_kind = load_or_placeholder_image(
            project_dir=store.project_dir,
            media_dir=media_dir,
            scene_heading=plan.scene_heading,
            shot=shot,
            source_path=source_image_path,
            width=width,
            height=height,
        )
        source_relative_path = relative_path(store.project_dir, source_path)
        source_image = open_image_or_none(store.project_dir, source_relative_path)
        if source_image is None:
            fallback_path = media_dir / f"{shot.shot_id.lower()}_keyframe_placeholder.jpg"
            create_placeholder_image(
                output_path=fallback_path,
                scene_heading=plan.scene_heading,
                shot=shot,
                width=width,
                height=height,
            )
            source_image = Image.open(fallback_path).convert("RGB")
            source_kind = "placeholder"

        for position, fraction in (("start", 0.0), ("mid", 0.5), ("end", 0.99)):
            derived = derive_motion_crop(
                source_image,
                position=position,
                movement=shot.camera_movement,
                width=width,
                height=height,
            )
            output_path = media_dir / f"{shot.shot_id.lower()}_{position}.jpg"
            derived.save(output_path, format="JPEG", quality=90)
            keyframes.append(
                Keyframe(
                    keyframe_id=f"{plan.scene_id}_{shot.shot_id.lower()}_{position}",
                    shot_id=shot.shot_id,
                    position=position,
                    timestamp_seconds=round(
                        elapsed_seconds + (shot.duration_estimate_seconds * fraction),
                        3,
                    ),
                    image=MediaFile(
                        relative_path=relative_path(store.project_dir, output_path),
                        media_type="image/jpeg",
                    ),
                    source_kind=source_kind,
                    source_segment_id=None,
                    is_locked=False,
                    shot_size=shot.shot_size,
                    camera_angle=shot.camera_angle,
                    camera_movement=shot.camera_movement,
                    notes=shot.edit_intent,
                )
            )
        elapsed_seconds += shot.duration_estimate_seconds

    storyboard_ref = latest_ref_or_none(store, "storyboard", plan.scene_id)
    return KeyframeArtifact(
        scene_id=plan.scene_id,
        scene_number=plan.scene_number,
        scene_heading=plan.scene_heading,
        shot_plan_ref=latest_entity_ref(store, "shot_plan", plan.scene_id),
        storyboard_ref=storyboard_ref,
        keyframes=keyframes,
    )


def extract_storyboard_image_path(frame_data: dict[str, Any] | None) -> str | None:
    if not isinstance(frame_data, dict):
        return None
    image = frame_data.get("image")
    if not isinstance(image, dict):
        return None
    rel_path = image.get("relative_path")
    return rel_path if isinstance(rel_path, str) else None

def latest_ref_or_none(
    store: ArtifactStore, artifact_type: str, entity_id: str
) -> ArtifactRef | None:
    refs = store.list_versions(artifact_type, entity_id)
    return refs[-1] if refs else None


def keyframe_lineage(
    *,
    store: ArtifactStore,
    scene_id: str,
    storyboard_present: bool,
) -> list[ArtifactRef]:
    refs: list[ArtifactRef] = [latest_entity_ref(store, "shot_plan", scene_id)]
    if storyboard_present:
        storyboard_ref = latest_ref_or_none(store, "storyboard", scene_id)
        if storyboard_ref is not None:
            refs.append(storyboard_ref)
    return refs


def update_track_manifest_with_keyframes(
    *,
    manifest: TrackManifest,
    keyframes_by_scene: dict[str, KeyframeArtifact],
    keyframe_refs: dict[str, ArtifactRef],
) -> TrackManifest:
    scene_ids = set(keyframes_by_scene)
    kept_entries = [
        entry
        for entry in manifest.entries
        if not (entry.track_type == "keyframes" and entry.scene_id in scene_ids)
    ]
    new_entries = list(kept_entries)
    for scene_id in sorted(scene_ids):
        artifact = keyframes_by_scene[scene_id]
        artifact_ref = keyframe_refs[scene_id]
        for idx, keyframe in enumerate(artifact.keyframes, start=1):
            new_entries.append(
                TrackEntry(
                    track_type="keyframes",
                    scene_id=scene_id,
                    shot_id=keyframe.shot_id,
                    artifact_ref=artifact_ref,
                    priority=175 + idx,
                    status="available",
                    notes=f"{keyframe.position} ({'locked' if keyframe.is_locked else 'unlocked'})",
                )
            )
    return manifest.model_copy(
        update={"entries": new_entries, "track_fill_counts": track_counts(new_entries)}
    )
