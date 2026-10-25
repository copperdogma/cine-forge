"""Focused offline regressions from independent media-plan review."""

from __future__ import annotations

import json

import pytest

from cine_forge.artifacts import ArtifactStore
from cine_forge.driver.engine import DriverEngine
from cine_forge.driver.input_collection import collect_inputs
from cine_forge.services.media_execution_plans import prepare_media_execution
from cine_forge.services.media_plan_execution import checked_execution
from cine_forge.services.media_plan_sources import MediaSourceSnapshot
from tests.unit.test_media_execution_plans import (
    _kwargs,
    _metadata,
    _save,
)

pytestmark = pytest.mark.unit


@pytest.fixture
def media_case(tmp_path):
    from tests.unit.test_media_execution_plans import media_case as shared_fixture

    return shared_fixture.__wrapped__(tmp_path)


def test_reversed_entity_discovery_has_identical_worker_and_inspection_projection(
    media_case,
    monkeypatch,
):
    store = media_case["store"]
    # Ensure at least two unrelated global bibles are projected by the real recipe.
    first = store.list_entities("character_bible")[0]
    original = store.load_artifact(store.latest_ref("character_bible", first)).data
    original = {**original, "character_id": "zz_review_character", "name": "ZZ Review Character"}
    store.save_artifact("character_bible", "zz_review_character", original, _metadata())
    real_list = ArtifactStore.list_entities

    def reversed_entities(self, artifact_type):
        return sorted(real_list(self, artifact_type), reverse=True)

    monkeypatch.setattr(ArtifactStore, "list_entities", reversed_entities)
    prepared = prepare_media_execution(**_kwargs(media_case))
    assert prepared.plan.status == "ready", prepared.plan.blockers
    assert len(prepared.inputs["character_bible"]) >= 2
    ordinary, ordinary_refs = collect_inputs(
        store=ArtifactStore(media_case["project_dir"]),
        recipe=prepared.recipe,
        stage_id=prepared.stage.id,
        stage_outputs={},
        runtime_params=prepared.runtime,
    )
    frozen, frozen_refs = collect_inputs(
        store=MediaSourceSnapshot(media_case["project_dir"]),
        recipe=prepared.recipe,
        stage_id=prepared.stage.id,
        stage_outputs={},
        runtime_params=prepared.runtime,
    )
    assert ordinary == frozen
    assert ordinary_refs == frozen_refs
    saved = _save(media_case)
    checked = checked_execution(
        **{k: media_case[k] for k in ("workspace_root", "project_dir", "project_id")},
        ref=saved.plan_ref,
        actual_inputs=ordinary,
    )
    assert checked.inputs == ordinary


def test_run_state_exists_before_media_guard_and_rejection_remains_readable(
    tmp_path,
    monkeypatch,
):
    from cine_forge.api.service import OperatorConsoleService

    run_id = "run-media-rejected"
    engine = DriverEngine(workspace_root=tmp_path)
    runtime = {"media_execution_plan_ref": {"deliberate": "rejection-fixture"}}
    state_path = tmp_path / "output/runs" / run_id / "run_state.json"
    (tmp_path / "unused-recipe.yaml").write_text(
        "recipe_id: test\ndescription: fixture\nstages: []\n"
    )
    observed = []

    def rejecting_guard(**kwargs):
        state = json.loads(state_path.read_text())
        observed.append(state)
        assert state["recipe_id"] == "initializing"
        assert state["runtime_params"] == runtime
        raise ValueError("Deliberate stale media approval rejection")

    monkeypatch.setattr(
        "cine_forge.services.media_plan_execution.validate_media_run_envelope",
        rejecting_guard,
    )
    with pytest.raises(ValueError, match="Deliberate stale"):
        engine.run(
            recipe_path=tmp_path / "unused-recipe.yaml", run_id=run_id, runtime_params=runtime
        )
    assert len(observed) == 1
    persisted = json.loads(state_path.read_text())
    assert persisted["runtime_params"] == runtime
    assert persisted.get("finished_at")
    assert "Deliberate stale media approval rejection" in state_path.read_text()
    response = OperatorConsoleService(tmp_path)._orchestrator.read_run_state(run_id)
    assert response["run_id"] == run_id
    assert response["state"]["finished_at"]


def test_distinct_plan_inspections_do_not_reserve_output_artifact_versions(media_case):
    """Mechanical concurrency probe: a plan claim alone cannot serialize output writes."""
    first = _save(media_case)
    second = _save(media_case)
    assert first.plan_ref != second.plan_ref
    snapshots = [
        checked_execution(
            **{k: media_case[k] for k in ("workspace_root", "project_dir", "project_id")},
            ref=saved.plan_ref,
        )
        for saved in (first, second)
    ]
    entity = media_case["clip"].clip_id
    first_unit, second_unit = (snapshot.units[entity] for snapshot in snapshots)
    assert first_unit.video_ref == second_unit.video_ref
    assert first_unit.prompt_ref == second_unit.prompt_ref
    # Inputs remain the same approval while output counts are deliberately unbound.
    assert snapshots[0].plan.binding_sha256 == snapshots[1].plan.binding_sha256


@pytest.mark.parametrize("recipe_id", ["ai_previz_generation", "render_generation"])
def test_approved_validation_uses_only_current_run_selected_outputs(media_case, recipe_id):
    from cine_forge.schemas import ArtifactRef

    saved = _save(media_case)
    if recipe_id == "render_generation":
        artifact = media_case["store"].load_artifact(saved.plan_ref)
        plan = {**artifact.data, "recipe_id": recipe_id}
        plan_ref = media_case["store"].save_artifact(
            "media_execution_plan", "offline-render-validation", plan, _metadata()
        )
    else:
        plan_ref = saved.plan_ref
    prepared = prepare_media_execution(**_kwargs(media_case))
    stage = next(stage for stage in prepared.recipe.stages if stage.id == "validate_media")
    video_type = "generated_video" if recipe_id == "render_generation" else "ai_previz_video"
    stage = stage.model_copy(update={"params": {"target_artifact_type": video_type}})
    recipe = prepared.recipe.model_copy(update={"stages": [stage]})
    entity = saved.plan.units[0].entity_id
    ref = ArtifactRef(
        artifact_type=video_type, entity_id=entity, version=2,
        path=f"artifacts/{video_type}/{entity}/v2.json",
    )
    current = {"ref": ref, "data": {"marker": "fresh selected output"}}
    runtime = {"media_execution_plan_ref": plan_ref.model_dump(mode="json")}
    generation = "render" if recipe_id == "render_generation" else "ai_previz"
    # Store-wide old or nonselected media must never be queried as a fallback.
    def no_store_enumeration(*args, **kwargs):
        raise AssertionError("Approved validation attempted store-wide latest lookup")
    media_case["store"].list_entities = no_store_enumeration
    inputs, lineage = collect_inputs(
        store=media_case["store"], recipe=recipe, stage_id="validate_media",
        stage_outputs={generation: [current]}, runtime_params=runtime,
    )
    assert inputs == {"generated_video": [current["data"]]}
    assert lineage == [ref]
    other_ref = ref.model_copy(update={"entity_id": "unselected-clip"})
    for outputs in ([], [current, current], [{"ref": other_ref, "data": {}}]):
        with pytest.raises(ValueError, match="exactly this run's selected"):
            collect_inputs(
                store=media_case["store"], recipe=recipe, stage_id="validate_media",
                stage_outputs={generation: outputs}, runtime_params=runtime,
            )
