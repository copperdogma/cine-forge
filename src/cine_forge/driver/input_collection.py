"""Shared driver artifact projection for execution and inspected media plans."""

from __future__ import annotations

from typing import Any

from cine_forge.artifacts import ArtifactStore
from cine_forge.driver.recipe import Recipe
from cine_forge.pipeline.scene_actions import (
    scene_scope_from_runtime_params,
    scene_scope_matches_entity_id,
    scene_scoped_entity_artifact_types,
)
from cine_forge.schemas import ArtifactHealth, ArtifactRef


def collect_inputs(
    *,
    store: ArtifactStore,
    recipe: Recipe,
    stage_id: str,
    stage_outputs: dict[str, list[dict[str, Any]]],
    runtime_params: dict[str, Any],
) -> tuple[dict[str, Any], list[ArtifactRef]]:
    stage_by_id = {stage.id: stage for stage in recipe.stages}
    stage = stage_by_id[stage_id]
    if stage.module == "media_validation_v1" and runtime_params.get("media_execution_plan_ref"):
        from cine_forge.driver.media_validation_inputs import approved_validation_inputs

        return approved_validation_inputs(
            store=store,
            stage=stage,
            stage_outputs=stage_outputs,
            runtime_params=runtime_params,
        )
    if (
        not stage.needs
        and not stage.needs_all
        and not stage.store_inputs
        and not stage.store_inputs_optional
        and not stage.store_inputs_all
    ):
        return {}, []
    collected: dict[str, Any] = {}
    lineage: list[ArtifactRef] = []

    # Resolve in-recipe stage dependencies.
    # stage.after is intentionally excluded — ordering only, no data is piped.
    for dependency in stage.needs:
        outputs = stage_outputs.get(dependency, [])
        if not outputs:
            raise ValueError(
                f"Missing required upstream outputs for '{stage_id}': dependency '{dependency}'"
            )
        collected[dependency] = outputs[-1]["data"]
        lineage.append(outputs[-1]["ref"])

    for dependency in stage.needs_all:
        outputs = stage_outputs.get(dependency, [])
        if not outputs:
            raise ValueError(
                f"Missing required upstream outputs for '{stage_id}': "
                f"dependency '{dependency}' (needs_all)"
            )
        collected[dependency] = [o["data"] for o in outputs]
        lineage.extend([o["ref"] for o in outputs])

    _collect_project_inputs(store, stage, stage_id, collected, lineage)

    # Resolve store_inputs_all from artifact store
    scene_scope = scene_scope_from_runtime_params(runtime_params)
    selected_scene_ids = set(scene_scope.scene_ids)
    scene_artifact_types = scene_scoped_entity_artifact_types()
    for input_key, artifact_type in stage.store_inputs_all.items():
        entities = sorted(store.list_entities(artifact_type=artifact_type))
        if not entities:
            # Permissive: if no entities exist, just return empty list.
            # This allows "Refine Mode" to work on a fresh run (bootstrapping from nothing).
            collected[input_key] = []
            continue

        if scene_scope.is_scene_scoped and artifact_type in scene_artifact_types:
            entities = [
                entity_id
                for entity_id in entities
                if scene_scope_matches_entity_id(
                    artifact_type=artifact_type,
                    entity_id=entity_id,
                    scene_ids=selected_scene_ids,
                )
            ]
            if not entities:
                collected[input_key] = []
                continue

        all_data = []
        for ent_id in entities:
            versions = store.list_versions(artifact_type=artifact_type, entity_id=ent_id)
            if not versions:
                continue
            latest_ref = versions[-1]
            # Skip unhealthy artifacts
            health = store.graph.get_health(latest_ref)
            if health not in {ArtifactHealth.VALID, ArtifactHealth.CONFIRMED_VALID, None}:
                continue

            artifact = store.load_artifact(artifact_ref=latest_ref)
            all_data.append(artifact.data)
            lineage.append(latest_ref)

        collected[input_key] = all_data

    return collected, lineage


def _collect_project_inputs(
    store: ArtifactStore,
    stage: Any,
    stage_id: str,
    collected: dict[str, Any],
    lineage: list[ArtifactRef],
) -> None:
    # Resolve store_inputs from artifact store
    for input_key, artifact_type in stage.store_inputs.items():
        versions = store.list_versions(artifact_type=artifact_type, entity_id="project")
        if not versions:
            raise ValueError(
                f"Stage '{stage_id}' store_input '{input_key}' requires "
                f"artifact type '{artifact_type}', but none exist in the store. "
                f"Run the upstream recipe first."
            )
        latest_ref = versions[-1]
        health = store.graph.get_health(latest_ref)
        if health not in {ArtifactHealth.VALID, ArtifactHealth.CONFIRMED_VALID, None}:
            raise ValueError(
                f"Stage '{stage_id}' store_input '{input_key}': latest "
                f"'{artifact_type}' (v{latest_ref.version}) has health "
                f"'{health.value if health else 'unknown'}'. Re-run the upstream "
                f"recipe to produce a healthy version."
            )
        artifact = store.load_artifact(artifact_ref=latest_ref)
        collected[input_key] = artifact.data
        lineage.append(latest_ref)

    # Resolve optional store_inputs from artifact store
    for input_key, artifact_type in stage.store_inputs_optional.items():
        versions = store.list_versions(artifact_type=artifact_type, entity_id="project")
        if not versions:
            continue
        latest_ref = versions[-1]
        health = store.graph.get_health(latest_ref)
        if health not in {ArtifactHealth.VALID, ArtifactHealth.CONFIRMED_VALID, None}:
            continue
        artifact = store.load_artifact(artifact_ref=latest_ref)
        collected[input_key] = artifact.data
        lineage.append(latest_ref)
