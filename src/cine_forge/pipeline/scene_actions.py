"""Scene-action scope helpers and preflight classification."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cine_forge.artifacts import ArtifactStore
from cine_forge.schemas import ArtifactHealth, ArtifactRef
from cine_forge.schemas.scene_scope import (
    SceneActionPreflight,
    SceneActionPreflightItem,
    SceneExecutionScope,
)

_CONCERN_GROUP_LABELS = {
    "rhythm_and_flow": "Rhythm & Flow",
    "look_and_feel": "Look & Feel",
    "sound_and_music": "Sound & Music",
    "character_and_performance": "Character & Performance",
    "story_world": "Story World",
}

_SCENE_ENTITY_ARTIFACT_TYPES = {
    "scene",
    "rhythm_and_flow",
    "look_and_feel",
    "sound_and_music",
    "character_and_performance",
    "shot_plan",
    "storyboard",
    "keyframe",
    "ai_previz_prompt",
    "ai_previz_video",
    "render_prompt",
    "generated_video",
    "media_validation",
}

_OPTIONAL_DIRECTION_ARTIFACTS = (
    ("rhythm_and_flow", "Rhythm & Flow"),
    ("look_and_feel", "Look & Feel"),
    ("sound_and_music", "Sound & Music"),
)


def scene_scope_from_runtime_params(runtime_params: dict[str, Any] | None) -> SceneExecutionScope:
    """Read the typed scene scope from runtime params, defaulting safely."""
    raw = (runtime_params or {}).get("scene_scope")
    if isinstance(raw, SceneExecutionScope):
        return raw
    if isinstance(raw, dict):
        try:
            return SceneExecutionScope.model_validate(raw)
        except Exception:
            return SceneExecutionScope()
    return SceneExecutionScope()


def selected_scene_ids(runtime_params: dict[str, Any] | None) -> list[str]:
    """Return selected scene ids for current-scene runs, else an empty list."""
    scope = scene_scope_from_runtime_params(runtime_params)
    return list(scope.scene_ids) if scope.is_scene_scoped else []


def scene_scoped_entity_artifact_types() -> set[str]:
    """Artifact types whose entity ids are guaranteed to be scene ids."""
    return set(_SCENE_ENTITY_ARTIFACT_TYPES)


def load_latest_scene_payloads(
    store: ArtifactStore,
    artifact_type: str,
) -> dict[str, dict[str, Any]]:
    """Load the latest persisted payload for each scene-scoped artifact group."""
    payloads: dict[str, dict[str, Any]] = {}
    for scene_id in store.list_entities(artifact_type):
        versions = store.list_versions(artifact_type=artifact_type, entity_id=scene_id)
        if not versions:
            continue
        try:
            artifact = store.load_artifact(versions[-1])
        except Exception:
            continue
        if isinstance(artifact.data, dict):
            payloads[scene_id] = artifact.data
    return payloads


def load_latest_scene_refs(
    store: ArtifactStore,
    artifact_type: str,
) -> dict[str, ArtifactRef]:
    """Return the latest ref for each scene-scoped artifact group."""
    refs: dict[str, ArtifactRef] = {}
    for scene_id in store.list_entities(artifact_type):
        versions = store.list_versions(artifact_type=artifact_type, entity_id=scene_id)
        if versions:
            refs[scene_id] = versions[-1]
    return refs


def filter_scene_entries(
    entries: list[dict[str, Any]],
    runtime_params: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Filter scene-index style entries down to the selected scenes."""
    scene_ids = set(selected_scene_ids(runtime_params))
    if not scene_ids:
        return list(entries)
    return [
        entry for entry in entries
        if isinstance(entry, dict) and str(entry.get("scene_id") or "") in scene_ids
    ]


def filter_scene_payloads(
    payloads: list[dict[str, Any]],
    runtime_params: dict[str, Any] | None,
    *,
    scene_key: str = "scene_id",
) -> list[dict[str, Any]]:
    """Filter scene-scoped payload dicts down to the selected scenes."""
    scene_ids = set(selected_scene_ids(runtime_params))
    if not scene_ids:
        return list(payloads)
    return [
        item for item in payloads
        if isinstance(item, dict) and str(item.get(scene_key) or "") in scene_ids
    ]


def build_scene_action_preflight(
    *,
    project_path: Path,
    recipe_id: str,
    scene_scope: SceneExecutionScope,
    start_from: str | None = None,
    end_at: str | None = None,
) -> SceneActionPreflight:
    """Classify warnings / auto-build steps / soft blocks for a scene action."""
    store = ArtifactStore(project_dir=project_path)
    action_label = _action_label(recipe_id=recipe_id, start_from=start_from, end_at=end_at)
    scope_label = _scope_label(scene_scope)
    preflight = SceneActionPreflight(
        recipe_id=recipe_id,
        recipe_name=action_label,
        start_from=start_from,
        end_at=end_at,
        scene_scope=scene_scope,
        summary="",
        items=[],
    )

    scene_ids = _target_scene_ids(store=store, scene_scope=scene_scope)
    if not _project_has_input(project_path):
        preflight.items.append(SceneActionPreflightItem(
            kind="soft_block",
            label="No screenplay input",
            detail="Upload a screenplay or script input before starting this run.",
        ))
    if not _has_project_artifact(store, "canonical_script"):
        preflight.items.append(SceneActionPreflightItem(
            kind="soft_block",
            label="Script normalization missing",
            detail="Run the script breakdown path first so CineForge has a canonical script.",
        ))
    if not _has_project_artifact(store, "scene_index"):
        preflight.items.append(SceneActionPreflightItem(
            kind="soft_block",
            label="Scene breakdown missing",
            detail=(
                "Break the script into scenes first. Scene-scoped generation has no "
                "target scene without that substrate."
            ),
        ))
    if scene_scope.is_scene_scoped and not scene_ids:
        preflight.items.append(SceneActionPreflightItem(
            kind="soft_block",
            label="Current scene unavailable",
            detail="The requested scene is missing or no longer exists in the project.",
        ))

    if recipe_id == "animatics_generation":
        preflight.items.append(SceneActionPreflightItem(
            kind="soft_block",
            label="Deterministic baseline removed",
            detail=(
                "Animatics generation is no longer part of the shipped workflow. "
                "Use Storyboards for still planning frames or AI Previz for generated motion."
            ),
        ))
        preflight.status = "soft_block"
        preflight.summary = f"{action_label} is no longer available for {scope_label}."
        return preflight

    if recipe_id == "creative_direction":
        _populate_concern_group_preflight(
            preflight=preflight,
            store=store,
            scene_ids=scene_ids,
            stage_id=start_from if start_from == end_at else None,
        )
    else:
        _populate_generation_preflight(
            preflight=preflight,
            store=store,
            recipe_id=recipe_id,
            scene_ids=scene_ids,
        )
        if start_from is None:
            preflight.start_from = _recommended_generation_start_stage(
                preflight=preflight,
                store=store,
                recipe_id=recipe_id,
                scene_ids=scene_ids,
            )

    if any(item.kind == "soft_block" for item in preflight.items):
        preflight.status = "soft_block"
        preflight.summary = f"{action_label} can't run for {scope_label} yet."
    elif preflight.items:
        preflight.status = "warn"
        preflight.summary = f"{action_label} can run for {scope_label} with warnings."
    else:
        preflight.status = "ready"
        preflight.summary = f"{action_label} is ready for {scope_label}."
    return preflight


def _populate_concern_group_preflight(
    *,
    preflight: SceneActionPreflight,
    store: ArtifactStore,
    scene_ids: list[str],
    stage_id: str | None,
) -> None:
    if stage_id == "character_and_performance":
        if not store.list_entities("character_bible"):
            preflight.items.append(SceneActionPreflightItem(
                kind="warning",
                label="Character bibles missing",
                detail=(
                    "Character & Performance can still run, but motivations and subtext "
                    "will lean more on scene text than structured character grounding."
                ),
            ))
        if not _has_project_artifact(store, "intent_mood"):
            preflight.items.append(SceneActionPreflightItem(
                kind="warning",
                label="Intent & Mood missing",
                detail=(
                    "Character & Performance can still run, but tonal alignment will rely "
                    "more on the current scene than project-level creative intent."
                ),
            ))

    if stage_id == "look_and_feel":
        if not store.list_entities("character_bible"):
            preflight.items.append(SceneActionPreflightItem(
                kind="warning",
                label="Character bibles missing",
                detail=(
                    "Look & Feel can still run, but wardrobe and character-specific "
                    "visual notes will lean more on AI defaults."
                ),
            ))
        if not store.list_entities("location_bible"):
            preflight.items.append(SceneActionPreflightItem(
                kind="warning",
                label="Location bibles missing",
                detail=(
                    "Look & Feel can still run, but production-design grounding will "
                    "rely more on scene text alone."
                ),
            ))
    if stage_id == "rhythm_and_flow" and not store.list_entities("character_bible"):
        preflight.items.append(SceneActionPreflightItem(
            kind="warning",
            label="Character bibles missing",
            detail=(
                "Rhythm & Flow can still run, but beat-specific performance and "
                "coverage nuance will have less upstream grounding."
            ),
        ))
    if stage_id == "sound_and_music" and not _has_project_artifact(store, "intent_mood"):
        preflight.items.append(SceneActionPreflightItem(
            kind="warning",
            label="Intent & Mood missing",
            detail=(
                "Sound & Music can still run, but tonal alignment will rely more on "
                "scene text than project-level intent."
            ),
        ))
    if stage_id == "story_world":
        if not _has_project_artifact(store, "intent_mood"):
            preflight.items.append(SceneActionPreflightItem(
                kind="warning",
                label="Intent & Mood missing",
                detail=(
                    "Story World can still run, but motif suggestions will lean more on "
                    "script text than explicit project taste inputs."
                ),
            ))
        if not store.list_entities("character_bible"):
            preflight.items.append(SceneActionPreflightItem(
                kind="warning",
                label="Character bibles missing",
                detail=(
                    "Story World can still run, but character-linked motifs and design "
                    "baselines will have less structured grounding."
                ),
            ))
        if not store.list_entities("location_bible"):
            preflight.items.append(SceneActionPreflightItem(
                kind="warning",
                label="Location bibles missing",
                detail=(
                    "Story World can still run, but location-linked motifs and baseline "
                    "references will rely more on the scene text alone."
                ),
            ))
        if not store.list_entities("prop_bible"):
            preflight.items.append(SceneActionPreflightItem(
                kind="warning",
                label="Prop bibles missing",
                detail=(
                    "Story World can still run, but prop-linked motifs and baseline "
                    "references will be limited until prop bibles exist."
                ),
            ))

    if preflight.scene_scope.is_scene_scoped and not scene_ids:
        preflight.items.append(SceneActionPreflightItem(
            kind="soft_block",
            label="No target scene",
            detail="Pick a valid scene before running a current-scene direction pass.",
        ))


def _populate_generation_preflight(
    *,
    preflight: SceneActionPreflight,
    store: ArtifactStore,
    recipe_id: str,
    scene_ids: list[str],
) -> None:
    if not _has_healthy_project_artifact(store, "timeline"):
        preflight.items.append(SceneActionPreflightItem(
            kind="auto_build",
            label="Timeline",
            detail="This run will build the project timeline first.",
        ))
    if not _has_healthy_project_artifact(store, "track_manifest"):
        preflight.items.append(SceneActionPreflightItem(
            kind="auto_build",
            label="Track manifest",
            detail="This run will register baseline track rows before generating scene outputs.",
        ))
    if not _has_healthy_project_artifact(store, "continuity_index"):
        preflight.items.append(SceneActionPreflightItem(
            kind="warning",
            label="Continuity tracking missing",
            detail=(
                "Scene planning can still run, but state carry-over and continuity "
                "checks will rely more on scene text and may need cleanup later."
            ),
        ))

    if recipe_id in {
        "storyboard_generation",
        "ai_previz_generation",
        "render_generation",
    }:
        missing_shot_plan = _missing_or_unhealthy_scene_artifact_count(
            store,
            "shot_plan",
            scene_ids,
            preflight.scene_scope,
        )
        if missing_shot_plan:
            preflight.items.append(SceneActionPreflightItem(
                kind="auto_build",
                label="Shot planning",
                detail=_auto_build_detail(
                    preflight.scene_scope,
                    missing_shot_plan,
                    "This run will build shot plans first.",
                    "This run will build shot plans for the missing scenes first.",
                ),
            ))

    if recipe_id in {
        "shot_planning",
        "storyboard_generation",
        "ai_previz_generation",
        "render_generation",
    }:
        for artifact_type, label in _OPTIONAL_DIRECTION_ARTIFACTS:
            missing = _missing_or_unhealthy_scene_artifact_count(
                store,
                artifact_type,
                scene_ids,
                preflight.scene_scope,
            )
            if not missing:
                continue
            preflight.items.append(SceneActionPreflightItem(
                kind="warning",
                label=f"{label} missing",
                detail=_warning_detail(
                    preflight.scene_scope,
                    missing,
                    (
                        f"{label} hasn't been generated for this scene yet. "
                        "CineForge can still continue, but quality will lean "
                        "more on AI defaults."
                    ),
                    (
                        f"{label} is missing for {missing} scenes. CineForge can "
                        "still continue, but those outputs will lean more on "
                        "AI defaults."
                    ),
                ),
            ))

    if recipe_id == "render_generation":
        missing_keyframes = _missing_or_unhealthy_scene_artifact_count(
            store,
            "keyframe",
            scene_ids,
            preflight.scene_scope,
        )
        if missing_keyframes:
            preflight.items.append(SceneActionPreflightItem(
                kind="warning",
                label="Keyframes missing",
                detail=_warning_detail(
                    preflight.scene_scope,
                    missing_keyframes,
                    (
                        "No keyframes are locked for this scene yet. Render will "
                        "proceed prompt-first and may need a later framing pass."
                    ),
                    (
                        f"Keyframes are missing for {missing_keyframes} scenes. "
                        "Those renders will proceed prompt-first and may need a "
                        "later framing pass."
                    ),
                ),
            ))


def _project_has_input(project_path: Path) -> bool:
    inputs_dir = project_path / "inputs"
    return inputs_dir.exists() and any(path.is_file() for path in inputs_dir.iterdir())


def _has_project_artifact(store: ArtifactStore, artifact_type: str) -> bool:
    return bool(store.list_versions(artifact_type=artifact_type, entity_id="project"))


def _has_healthy_project_artifact(store: ArtifactStore, artifact_type: str) -> bool:
    versions = store.list_versions(artifact_type=artifact_type, entity_id="project")
    if not versions:
        return False
    return _ref_is_healthy(store, versions[-1])


def _target_scene_ids(store: ArtifactStore, scene_scope: SceneExecutionScope) -> list[str]:
    if scene_scope.is_scene_scoped:
        available = set(store.list_entities("scene"))
        return [scene_id for scene_id in scene_scope.scene_ids if scene_id in available]
    return sorted(store.list_entities("scene"))


def _missing_or_unhealthy_scene_artifact_count(
    store: ArtifactStore,
    artifact_type: str,
    scene_ids: list[str],
    scene_scope: SceneExecutionScope,
) -> int:
    target_scene_ids = (
        scene_ids
        if scene_scope.is_scene_scoped
        else sorted(store.list_entities("scene"))
    )
    if not target_scene_ids:
        return 0
    missing = 0
    for scene_id in target_scene_ids:
        versions = store.list_versions(artifact_type=artifact_type, entity_id=scene_id)
        if not versions or not _ref_is_healthy(store, versions[-1]):
            missing += 1
    return missing


def _ref_is_healthy(store: ArtifactStore, artifact_ref: ArtifactRef) -> bool:
    try:
        health = store.load_artifact(artifact_ref).metadata.health
    except Exception:
        health = store.graph.get_health(artifact_ref)
    return health in {ArtifactHealth.VALID, ArtifactHealth.CONFIRMED_VALID, None}


def _recommended_generation_start_stage(
    *,
    preflight: SceneActionPreflight,
    store: ArtifactStore,
    recipe_id: str,
    scene_ids: list[str],
) -> str | None:
    if not _has_healthy_project_artifact(store, "track_manifest"):
        return None
    if recipe_id == "ai_previz_generation":
        missing_shot_plan = _missing_or_unhealthy_scene_artifact_count(
            store,
            "shot_plan",
            scene_ids,
            preflight.scene_scope,
        )
        return "ai_previz" if missing_shot_plan == 0 else None
    return None


def _scope_label(scene_scope: SceneExecutionScope) -> str:
    if not scene_scope.is_scene_scoped:
        return "all scenes"
    if len(scene_scope.scene_ids) == 1:
        return scene_scope.scene_ids[0]
    return f"{len(scene_scope.scene_ids)} selected scenes"


def _action_label(*, recipe_id: str, start_from: str | None, end_at: str | None) -> str:
    if recipe_id == "creative_direction" and start_from and start_from == end_at:
        return _CONCERN_GROUP_LABELS.get(start_from, "Creative Direction")
    labels = {
        "shot_planning": "Shot Planning",
        "storyboard_generation": "Storyboards",
        "animatics_generation": "Animatics",
        "ai_previz_generation": "AI Previz",
        "render_generation": "Render",
        "creative_direction": "Creative Direction",
    }
    return labels.get(recipe_id, recipe_id.replace("_", " ").title())


def _auto_build_detail(
    scene_scope: SceneExecutionScope,
    missing_count: int,
    singular: str,
    plural: str,
) -> str:
    return singular if scene_scope.is_scene_scoped or missing_count == 1 else plural


def _warning_detail(
    scene_scope: SceneExecutionScope,
    missing_count: int,
    singular: str,
    plural: str,
) -> str:
    return singular if scene_scope.is_scene_scoped or missing_count == 1 else plural
