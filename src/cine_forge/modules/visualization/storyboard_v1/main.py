"""Scene-level storyboard generation grounded in shot plans and design direction."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cine_forge.artifacts import ArtifactStore
from cine_forge.modules.visualization.storyboard_v1.generation import (
    generate_storyboard_for_scene,
)
from cine_forge.modules.visualization.storyboard_v1.prompting import (
    resolve_aspect_ratio,
    resolve_style,
    storyboard_lineage,
)
from cine_forge.modules.visualization.storyboard_v1.support import (
    DEFAULT_IMAGE_MODEL,
    anticipated_storyboard_ref,
    average_values,
    empty_cost,
    entity_map,
    latest_project_ref,
    merge_cost,
    scene_map,
    storyboard_confidence,
    track_counts,
)
from cine_forge.pipeline.scene_actions import filter_scene_payloads
from cine_forge.schemas import (
    ArtifactRef,
    ProjectConfig,
    Scene,
    ShotPlan,
    TrackEntry,
    TrackManifest,
)


def run_module(
    inputs: dict[str, Any], params: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    """Generate scene-level storyboard artifacts and update storyboard track entries."""
    project_dir_raw = context.get("project_dir")
    if not isinstance(project_dir_raw, str) or not project_dir_raw:
        raise ValueError("storyboard_v1 requires context.project_dir")
    store = ArtifactStore(project_dir=Path(project_dir_raw))

    track_manifest_payload = inputs.get("track_manifest")
    if not isinstance(track_manifest_payload, dict):
        raise ValueError("storyboard_v1 requires track_manifest input")
    track_manifest = TrackManifest.model_validate(track_manifest_payload)

    shot_plan_payloads = inputs.get("shot_plan")
    if not isinstance(shot_plan_payloads, list) or not shot_plan_payloads:
        raise ValueError("storyboard_v1 requires one or more shot_plan inputs")

    runtime_params = context.get("runtime_params", {}) if isinstance(context, dict) else {}
    if not isinstance(runtime_params, dict):
        runtime_params = {}
    shot_plan_payloads = filter_scene_payloads(shot_plan_payloads, runtime_params)
    shot_plans = [
        ShotPlan.model_validate(item)
        for item in shot_plan_payloads
        if isinstance(item, dict)
    ]
    if not shot_plans:
        raise ValueError("storyboard_v1 could not parse any shot_plan inputs")

    project_config_data = (
        inputs.get("project_config") if isinstance(inputs.get("project_config"), dict) else None
    )
    project_config = (
        ProjectConfig.model_validate(project_config_data)
        if project_config_data is not None
        else None
    )
    style = resolve_style(
        params=params,
        runtime_params=runtime_params,
        project_config=project_config,
    )
    if style == "photoreal" and not bool(params.get("photoreal_opt_in", False)):
        raise ValueError("storyboard_v1 photoreal style requires params.photoreal_opt_in=true")

    image_model = (
        params.get("image_model")
        or runtime_params.get("image_model")
        or DEFAULT_IMAGE_MODEL
    )
    max_retries = int(params.get("max_retries") or runtime_params.get("max_retries") or 2)
    retry_delay_seconds = float(
        params.get("retry_delay_seconds") or runtime_params.get("retry_delay_seconds") or 0.5
    )

    look_and_feel_by_scene = scene_map(inputs.get("look_and_feel"))
    aspect_ratio_by_scene = resolve_aspect_ratio(
        project_config_data=project_config_data,
        look_and_feel_by_scene=look_and_feel_by_scene,
    )
    intent_mood = inputs.get("intent_mood") if isinstance(inputs.get("intent_mood"), dict) else None
    character_bibles = entity_map(
        inputs.get("character_bible"),
        key="character_id",
        fallback_key="name",
    )
    location_bibles = entity_map(
        inputs.get("location_bible"),
        key="location_id",
        fallback_key="name",
    )

    storyboard_artifacts: list[dict[str, Any]] = []
    storyboard_refs: dict[str, ArtifactRef] = {}
    storyboard_confidences: dict[str, float] = {}
    storyboards_by_scene: dict[str, Any] = {}
    total_cost = empty_cost(model=str(image_model))

    for plan in sorted(shot_plans, key=lambda item: item.scene_number):
        scene_artifact = store.load_artifact(plan.scene_ref)
        scene = Scene.model_validate(scene_artifact.data)
        storyboard_ref = anticipated_storyboard_ref(store=store, scene_id=plan.scene_id)
        storyboard, cost = generate_storyboard_for_scene(
            store=store,
            storyboard_ref=storyboard_ref,
            scene=scene,
            plan=plan,
            style=style,
            image_model=str(image_model),
            aspect_ratio=aspect_ratio_by_scene.get(plan.scene_id)
            or aspect_ratio_by_scene["__default__"],
            project_config_data=project_config_data,
            look_and_feel_data=look_and_feel_by_scene.get(plan.scene_id),
            intent_mood_data=intent_mood,
            character_bibles=character_bibles,
            location_bibles=location_bibles,
            max_retries=max_retries,
            retry_delay_seconds=retry_delay_seconds,
        )
        storyboard_artifacts.append(
            {
                "artifact_type": "storyboard",
                "entity_id": plan.scene_id,
                "data": storyboard.model_dump(mode="json"),
                "metadata": {
                    "lineage": [
                        ref.model_dump(mode="json")
                        for ref in storyboard_lineage(
                            store=store,
                            plan=plan,
                            scene=scene,
                            location_bibles=location_bibles,
                            project_config_present=project_config_data is not None,
                            look_and_feel_present=plan.scene_id in look_and_feel_by_scene,
                            intent_mood_present=intent_mood is not None,
                        )
                    ],
                    "intent": "Scene-level storyboard frames for composition and blocking review.",
                    "rationale": (
                        "Storyboard generation converts shot-planning intent into a cheap visual"
                        " fallback lane before animatics or final renders exist."
                    ),
                    "confidence": storyboard_confidence(plan),
                    "source": "hybrid",
                    "annotations": {
                        "frame_count": len(storyboard.frames),
                        "style": style,
                        "image_model": image_model,
                    },
                },
            }
        )
        storyboard_refs[plan.scene_id] = storyboard_ref
        storyboard_confidences[plan.scene_id] = storyboard_confidence(plan)
        storyboards_by_scene[plan.scene_id] = storyboard
        merge_cost(total_cost, cost)

    track_manifest_ref = latest_project_ref(store, "track_manifest")
    if track_manifest_ref is None:
        raise ValueError("storyboard_v1 could not resolve latest track_manifest artifact")

    updated_manifest = _update_track_manifest_with_storyboards(
        manifest=track_manifest,
        storyboards_by_scene=storyboards_by_scene,
        storyboard_refs=storyboard_refs,
    )
    storyboard_artifacts.append(
        {
            "artifact_type": "track_manifest",
            "entity_id": "project",
            "data": updated_manifest.model_dump(mode="json"),
            "include_stage_lineage": True,
            "metadata": {
                "lineage": [track_manifest_ref.model_dump(mode="json")],
                "intent": (
                    "Updated track manifest with storyboard entries for always-playable "
                    "fallback."
                ),
                "rationale": (
                    "Storyboard frames become the next visual representation layer when animatics"
                    " or generated video are not yet available."
                ),
                "confidence": average_values(storyboard_confidences.values()),
                "source": "hybrid",
            },
        }
    )

    return {"artifacts": storyboard_artifacts, "cost": total_cost}


def _update_track_manifest_with_storyboards(
    *,
    manifest: TrackManifest,
    storyboards_by_scene: dict[str, Any],
    storyboard_refs: dict[str, ArtifactRef],
) -> TrackManifest:
    storyboard_scene_ids = set(storyboards_by_scene)
    kept_entries = [
        entry
        for entry in manifest.entries
        if not (entry.track_type == "storyboards" and entry.scene_id in storyboard_scene_ids)
    ]
    new_entries = list(kept_entries)
    for scene_id in sorted(storyboard_scene_ids):
        storyboard = storyboards_by_scene[scene_id]
        storyboard_ref = storyboard_refs[scene_id]
        for idx, frame in enumerate(storyboard.frames, start=1):
            new_entries.append(
                TrackEntry(
                    track_type="storyboards",
                    scene_id=scene_id,
                    shot_id=frame.primary_shot_id,
                    artifact_ref=storyboard_ref,
                    priority=200 + idx,
                    status="available",
                    notes=frame.overlay.edit_intent or frame.notes,
                )
            )
    return manifest.model_copy(
        update={"entries": new_entries, "track_fill_counts": track_counts(new_entries)}
    )
