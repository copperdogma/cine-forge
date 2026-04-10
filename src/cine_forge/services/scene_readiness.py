"""Scene readiness loading for operator-facing UI surfaces."""

from __future__ import annotations

from typing import Any

from cine_forge.artifacts import ArtifactStore
from cine_forge.schemas import SceneReadiness, compute_scene_readiness

_SCENE_GROUPS = (
    "look_and_feel",
    "sound_and_music",
    "rhythm_and_flow",
    "character_and_performance",
)


def build_scene_readiness(store: ArtifactStore, scene_id: str) -> SceneReadiness:
    """Load the latest relevant artifacts and compute readiness for one scene."""

    artifacts: dict[str, dict[str, Any] | None] = {}
    scene_intent = _latest_artifact_data(store, artifact_type="intent_mood", entity_id=scene_id)
    artifacts["intent_mood"] = scene_intent or _latest_artifact_data(
        store,
        artifact_type="intent_mood",
        entity_id="project",
    )

    for artifact_type in _SCENE_GROUPS:
        artifacts[artifact_type] = _latest_artifact_data(
            store,
            artifact_type=artifact_type,
            entity_id=scene_id,
        )

    artifacts["story_world"] = _latest_artifact_data(
        store,
        artifact_type="story_world",
        entity_id="project",
    )
    return compute_scene_readiness(scene_id, artifacts)


def _latest_artifact_data(
    store: ArtifactStore,
    *,
    artifact_type: str,
    entity_id: str | None,
) -> dict[str, Any] | None:
    ref = store.latest_ref(artifact_type, entity_id)
    if ref is None:
        return None
    artifact = store.load_artifact(ref)
    if isinstance(artifact.data, dict):
        return artifact.data
    try:
        model_dump = artifact.data.model_dump(mode="json")
    except AttributeError:
        return None
    return model_dump if isinstance(model_dump, dict) else None
