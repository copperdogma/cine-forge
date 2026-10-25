"""Offline acceptance of immutable media inspection and confirmation authority."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from cine_forge.api.exceptions import ServiceError
from cine_forge.api.service import OperatorConsoleService
from cine_forge.schemas import ArtifactHealth, ArtifactMetadata
from cine_forge.schemas.media_execution_plan import MediaExecutionPlanRequest
from cine_forge.services.media_execution_plans import (
    prepare_media_execution,
    save_media_execution_plan,
)
from cine_forge.services.media_plan_execution import (
    checked_execution,
    claim_media_plan,
    confirm_media_request,
    consume_media_plan,
    execute_approved_media,
    validate_media_run_envelope,
)
from tests.unit.test_media_plan_preparation_helpers import _prepared_fixture

pytestmark = pytest.mark.unit
ROOT = Path(__file__).resolve().parents[2]


def _metadata():
    return ArtifactMetadata(
        intent="Offline fixture", rationale="Bounded contract proof", confidence=1, source="code"
    )


@pytest.fixture
def media_case(tmp_path):
    common, clip = _prepared_fixture(tmp_path)
    store = common["store"]
    project_dir = store.project_dir
    scene_id = common["scene"].scene_id
    store.save_artifact(
        "render_clip_plan",
        scene_id,
        common["source_maps"]["render_clip_plan"][scene_id].model_dump(mode="json"),
        _metadata(),
    )
    (project_dir / "inputs").mkdir()
    (project_dir / "inputs/script.fountain").write_text("INT. ROOM - NIGHT\nA short scene.")
    (project_dir / "project.json").write_text(json.dumps({"slug": "fixture-project"}))
    workspace = tmp_path / "workspace"
    recipes = workspace / "configs/recipes"
    recipes.mkdir(parents=True)
    for recipe_id in ("render_generation", "ai_previz_generation"):
        name = f"recipe-{recipe_id.replace('_', '-')}.yaml"
        data = yaml.safe_load((ROOT / "configs/recipes" / name).read_text())
        stage = next(s for s in data["stages"] if s["module"] == "render_adapter_v1")
        # Only this offline fixture suppresses unavailable automatic backfill.
        stage["params"]["default_design_study_backfill"] = False
        (recipes / name).write_text(yaml.safe_dump(data))
    return dict(
        workspace_root=workspace,
        project_dir=project_dir,
        project_id="fixture-project",
        store=store,
        scene_id=scene_id,
        clip=clip,
    )


def _kwargs(case, recipe="ai_previz_generation", selected=True):
    return {k: case[k] for k in ("workspace_root", "project_dir", "project_id")} | {
        "request": MediaExecutionPlanRequest(
            recipe_id=recipe,
            scene_id=case["scene_id"],
            render_clip_ids=[case["clip"].clip_id] if selected else None,
        )
    }


def _save(case, **kwargs):
    saved = save_media_execution_plan(**_kwargs(case, **kwargs))
    assert saved.plan.status == "ready", saved.plan.blockers
    return saved


def _checked(case, saved):
    return checked_execution(
        **{k: case[k] for k in ("workspace_root", "project_dir", "project_id")}, ref=saved.plan_ref
    )


def test_selected_single_clip_uses_actual_normalized_work_and_sourced_subtotal(media_case):
    saved = _save(media_case)
    unit = saved.plan.units[0]
    assert (unit.clip_id, unit.planned_duration_seconds, unit.duration_seconds) == (
        media_case["clip"].clip_id,
        3.2,
        4,
    )
    assert unit.price.source_url.startswith("https://docs.x.ai/")
    assert unit.video_estimate_usd == saved.plan.video_estimate_usd == 0.2
    assert saved.plan.total_estimate_usd is None
    assert _checked(media_case, saved).units[unit.entity_id].duration_seconds == 4


def test_retired_target_still_exposes_inspectable_units_and_no_quote(media_case):
    prepared = prepare_media_execution(**_kwargs(media_case, recipe="render_generation"))
    assert prepared.plan.status == "blocked"
    assert prepared.plan.units and prepared.plan.units[0].duration_seconds == 4
    assert prepared.plan.video_estimate_usd is None
    assert any("unavailable" in b for b in prepared.plan.blockers)


@pytest.mark.parametrize("mutation", ["source_bytes", "source_version", "project", "recipe"])
def test_changed_sources_defaults_or_recipe_reject_existing_approval(media_case, mutation):
    saved = _save(media_case)
    store = media_case["store"]
    if mutation.startswith("source"):
        ref = store.latest_ref("shot_plan", media_case["scene_id"])
        artifact = store.load_artifact(ref)
        if mutation == "source_bytes":
            path = media_case["project_dir"] / ref.path
            raw = json.loads(path.read_text())
            raw["data"]["coverage_strategy"]["coverage_approach"] += " changed"
            path.write_text(json.dumps(raw))
        else:
            store.save_artifact("shot_plan", media_case["scene_id"], artifact.data, _metadata())
    elif mutation == "project":
        (media_case["project_dir"] / "project.json").write_text(
            json.dumps({"slug": "fixture-project", "default_model": "different-model"})
        )
    else:
        path = media_case["workspace_root"] / "configs/recipes/recipe-ai-previz-generation.yaml"
        data = yaml.safe_load(path.read_text())
        next(s for s in data["stages"] if s["id"] == "ai_previz")["params"]["resolution"] = "720p"
        path.write_text(yaml.safe_dump(data))
    with pytest.raises(ValueError, match="stale"):
        _checked(media_case, saved)
    with pytest.raises(ServiceError) as error:
        confirm_media_request(
            **{k: media_case[k] for k in ("workspace_root", "project_dir", "project_id")},
            request={"media_execution_plan_ref": saved.plan_ref.model_dump(mode="json")},
        )
    assert error.value.status_code == 409


def test_absent_optional_manifest_becoming_present_invalidates_plan(media_case):
    saved = _save(media_case)
    media_case["store"].save_artifact(
        "injected_asset_manifest",
        "project",
        {
            "target_kind": "project",
            "target_id": "project",
            "display_name": "Project",
            "assets": [],
            "version": 1,
        },
        _metadata(),
    )
    with pytest.raises(ValueError, match="stale"):
        _checked(media_case, saved)


def test_optional_health_change_invalidates_plan(media_case):
    store = media_case["store"]
    ref = store.latest_ref("look_and_feel", media_case["scene_id"])
    assert ref is not None
    store.graph.set_manual_health_override(
        ref,
        health=ArtifactHealth.NEEDS_REVIEW,
        trigger_ref=None,
        source_artifact_ref=None,
        rationale="Offline fixture",
        decided_by="test",
    )
    saved = _save(media_case)
    store.graph.set_manual_health_override(
        ref,
        health=ArtifactHealth.VALID,
        trigger_ref=None,
        source_artifact_ref=None,
        rationale="Offline fixture",
        decided_by="test",
    )
    with pytest.raises(ValueError, match="stale"):
        _checked(media_case, saved)


@pytest.mark.parametrize("mutation", ["state", "image"])
def test_mutable_selected_reference_bytes_are_bound(media_case, mutation):
    store = media_case["store"]
    entity = "character_" + _checked_scene_character(media_case)
    ref = store.latest_ref("bible_manifest", entity)
    assert ref is not None
    path = media_case["project_dir"] / ref.path
    raw = json.loads(path.read_text())
    raw["data"]["visual_reference_image"] = "reviewed.png"
    path.write_text(json.dumps(raw))
    image = path.parent / "reviewed.png"
    image.write_bytes(b"original-reference")
    saved = _save(media_case)
    target = image if mutation == "image" else path.parent / "design_study_state.json"
    target.write_bytes(b"changed-reference" if mutation == "image" else b"{}")
    with pytest.raises(ValueError, match="stale"):
        _checked(media_case, saved)


def _checked_scene_character(case):
    ref = case["store"].latest_ref("scene", case["scene_id"])
    return case["store"].load_artifact(ref).data["characters_present_ids"][0]


def test_new_output_versions_do_not_invalidate_inspected_inputs(media_case):
    saved = _save(media_case)
    for kind in ("render_prompt", "ai_previz_prompt", "generated_video", "ai_previz_video"):
        media_case["store"].save_artifact(kind, media_case["clip"].clip_id, {}, _metadata())
    assert _checked(media_case, saved).plan.binding_sha256 == saved.plan.binding_sha256


def test_confirmation_refuses_overrides_and_plan_claim_is_one_use(media_case):
    saved = _save(media_case)
    base = {k: media_case[k] for k in ("workspace_root", "project_dir", "project_id")}
    with pytest.raises(ServiceError) as error:
        confirm_media_request(
            **base,
            request={
                "media_execution_plan_ref": saved.plan_ref.model_dump(mode="json"),
                "render_clip_ids": ["different"],
            },
        )
    assert error.value.status_code == 409
    claim_media_plan(media_case["project_dir"], saved.plan_ref, "run-1")
    with pytest.raises(ServiceError, match="already been confirmed"):
        claim_media_plan(media_case["project_dir"], saved.plan_ref, "run-2")
    consume_media_plan(media_case["project_dir"], saved.plan_ref, "run-1")
    with pytest.raises(ValueError, match="already started"):
        consume_media_plan(media_case["project_dir"], saved.plan_ref, "run-1")


def test_worker_rejects_post_start_source_mutation_before_any_paid_call(media_case, monkeypatch):
    saved = _save(media_case)
    prepared = _checked(media_case, saved)
    runtime = prepared.runtime | {
        "media_execution_plan_ref": saved.plan_ref.model_dump(mode="json")
    }
    path = media_case["workspace_root"] / "configs/recipes/recipe-ai-previz-generation.yaml"
    runtime = validate_media_run_envelope(
        workspace_root=media_case["workspace_root"],
        project_dir=media_case["project_dir"],
        recipe_path=path,
        runtime_params=runtime,
        start_from="ai_previz",
        end_at="validate_media",
        run_id="run-mutate",
    )
    ref = media_case["store"].latest_ref("shot_plan", media_case["scene_id"])
    payload = media_case["store"].load_artifact(ref).data
    media_case["store"].save_artifact("shot_plan", media_case["scene_id"], payload, _metadata())
    monkeypatch.setattr(
        "cine_forge.modules.generation.render_adapter_v1.render_unit.generate_video",
        lambda **kw: pytest.fail("No video call may occur"),
    )
    monkeypatch.setattr(
        "cine_forge.modules.generation.render_adapter_v1.unit_prompt.compile_render_prompt",
        lambda **kw: pytest.fail("No compiler call may occur"),
    )
    with pytest.raises(ValueError, match="stale"):
        execute_approved_media(
            inputs=prepared.inputs,
            params=prepared.params,
            context={"project_dir": str(media_case["project_dir"]), "runtime_params": runtime},
        )


def test_confirmed_api_keeps_missing_xai_preflight_and_creates_no_worker(media_case, monkeypatch):
    saved = _save(media_case)
    service = OperatorConsoleService(media_case["workspace_root"])
    service._project_registry[media_case["project_id"]] = media_case["project_dir"]
    monkeypatch.setattr("cine_forge.pipeline.scene_actions.resolve_env", lambda name: None)
    monkeypatch.setattr(
        service._orchestrator,
        "start_run",
        lambda *a, **kw: pytest.fail("Blocked confirmation must not enqueue"),
    )
    with pytest.raises(ServiceError) as error:
        service.start_run(
            media_case["project_id"],
            {
                "project_id": media_case["project_id"],
                "media_execution_plan_ref": saved.plan_ref.model_dump(mode="json"),
            },
        )
    assert error.value.status_code == 422
    assert "CINE_FORGE_XAI_API_KEY" in str(error.value.hint)


def test_unpriced_target_keeps_units_visible_without_numeric_estimate(media_case, monkeypatch):
    from cine_forge.modules.generation.render_adapter_v1.support import load_engine_pack

    pack = load_engine_pack("xai_grok_imagine_video").model_copy(
        update={"target_model": "unqualified-test-model"}
    )
    monkeypatch.setattr(
        "cine_forge.services.media_execution_plans.load_engine_pack", lambda pack_id: pack
    )
    prepared = prepare_media_execution(**_kwargs(media_case))
    assert prepared.plan.status == "blocked"
    assert len(prepared.plan.units) == 1
    assert prepared.plan.units[0].duration_seconds == 4
    assert prepared.plan.units[0].video_estimate_usd is None
    assert any("No qualified current video price" in b for b in prepared.plan.blockers)


def test_live_backfill_requirement_is_visible_without_generating_images(media_case, monkeypatch):
    path = media_case["workspace_root"] / "configs/recipes/recipe-ai-previz-generation.yaml"
    data = yaml.safe_load(path.read_text())
    next(s for s in data["stages"] if s["id"] == "ai_previz")["params"][
        "default_design_study_backfill"
    ] = True
    path.write_text(yaml.safe_dump(data))
    monkeypatch.setattr(
        "cine_forge.services.design_study_backfill.DefaultDesignStudyBackfillService.generation_required",
        lambda self, scene: True,
    )
    monkeypatch.setattr(
        "cine_forge.services.design_study_backfill.DefaultDesignStudyBackfillService.backfill_scene",
        lambda *a, **kw: pytest.fail("Inspection cannot generate reference images"),
    )
    prepared = prepare_media_execution(**_kwargs(media_case))
    assert prepared.plan.status == "blocked"
    assert prepared.plan.units[0].video_estimate_usd == 0.2
    assert prepared.plan.total_estimate_usd is None
    assert any("automatic image generation is not authorized" in b for b in prepared.plan.blockers)
