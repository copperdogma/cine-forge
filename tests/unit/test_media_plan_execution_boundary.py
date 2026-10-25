"""Offline worker tests: queued mutations stop; admitted work consumes captured inputs."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from cine_forge.ai.video_types import VideoGenerationResult
from cine_forge.driver.engine import DriverEngine
from cine_forge.execution_errors import ModuleCostError
from cine_forge.modules.generation.render_adapter_v1 import execution, render_unit
from cine_forge.modules.generation.render_adapter_v1.main import run_module
from cine_forge.schemas import ArtifactMetadata, CostRecord
from cine_forge.schemas.media_cost import CostReceipt
from cine_forge.schemas.media_execution_plan import MediaExecutionPlanRequest
from cine_forge.services.media_execution_plans import (
    prepare_media_execution,
    save_media_execution_plan,
)
from cine_forge.services.media_plan_execution import confirm_media_request
from cine_forge.services.run_parameters import build_runtime_params
from tests.unit.test_media_plan_preparation_helpers import _prepared_fixture

pytestmark = pytest.mark.unit
ROOT = Path(__file__).resolve().parents[2]


def _approved(tmp_path):
    common, clip = _prepared_fixture(tmp_path)
    store = common["store"]
    store.save_artifact(
        "render_clip_plan",
        "scene_001",
        common["source_maps"]["render_clip_plan"]["scene_001"].model_dump(mode="json"),
        ArtifactMetadata(
            intent="Fixture", rationale="Offline worker test", confidence=1, source="code"
        ),
    )
    root = tmp_path / "workspace"
    recipes = root / "configs/recipes"
    recipes.mkdir(parents=True)
    recipe = yaml.safe_load((ROOT / "configs/recipes/recipe-ai-previz-generation.yaml").read_text())
    next(s for s in recipe["stages"] if s["id"] == "ai_previz")["params"][
        "default_design_study_backfill"
    ] = False
    path = recipes / "recipe-ai-previz-generation.yaml"
    path.write_text(yaml.safe_dump(recipe))
    request = MediaExecutionPlanRequest(
        recipe_id="ai_previz_generation", scene_id="scene_001", render_clip_ids=[clip.clip_id]
    )
    kwargs = dict(
        workspace_root=root, project_dir=store.project_dir, project_id="test", request=request
    )
    response = save_media_execution_plan(**kwargs)
    assert response.plan.status == "ready", response.plan.blockers
    confirmed = confirm_media_request(
        workspace_root=root,
        project_dir=store.project_dir,
        project_id="test",
        request={"project_id": "test", "media_execution_plan_ref": response.plan_ref.model_dump()},
    )
    runtime = build_runtime_params(confirmed, {})
    runtime.update(
        media_execution_plan_ref=response.plan_ref.model_dump(),
        __media_plan_workspace_root=str(root),
    )
    prepared = prepare_media_execution(**kwargs)
    return store, root, path, response, runtime, prepared


def test_queued_source_mutation_stops_before_driver_execution(tmp_path, monkeypatch):
    store, root, path, _response, runtime, prepared = _approved(tmp_path)
    scene_path = store.project_dir / prepared.plans[0].scene_ref.path
    payload = json.loads(scene_path.read_text())
    payload["data"]["heading"] = "INT. UNAPPROVED SUBSTITUTION - DAY"
    scene_path.write_text(json.dumps(payload))
    monkeypatch.setattr(DriverEngine, "_run_recipe", lambda *a, **k: pytest.fail("worker ran"))
    with pytest.raises(ValueError, match="stale"):
        DriverEngine(root, project_dir=store.project_dir).run(
            recipe_path=path, runtime_params=runtime,
            start_from="ai_previz", end_at="validate_media",
        )


def test_actual_worker_parameter_override_stops_before_renderer(tmp_path, monkeypatch):
    store, _root, _path, _response, runtime, prepared = _approved(tmp_path)
    monkeypatch.setattr(execution, "execute_render", lambda **k: pytest.fail("renderer ran"))
    with pytest.raises(ValueError, match="Actual media parameters"):
        run_module(
            inputs=prepared.inputs,
            params={**prepared.params, "resolution": "720p"},
            context={"project_dir": str(store.project_dir), "runtime_params": runtime},
        )


def test_execution_uses_prepared_unit_and_pins_optional_output_lineage(tmp_path, monkeypatch):
    store, _root, _path, response, runtime, prepared = _approved(tmp_path)
    calls = []
    monkeypatch.setattr(
        render_unit,
        "prepare_render_unit",
        lambda **k: pytest.fail("execution reloaded live unit inputs"),
    )

    def video(*, request, engine_pack):
        calls.append(request)
        # A newly created optional input after admission must not appear in output lineage.
        store.save_artifact(
            "keyframe",
            "scene_001",
            {"new": "unapproved"},
            ArtifactMetadata(
                intent="Mutation", rationale="Race fixture", confidence=1, source="code"
            ),
        )
        return VideoGenerationResult(
            video_bytes=b"offline-video",
            media_type="video/mp4",
            model_used=engine_pack.target_model,
            provider_job_id="offline-job",
            cost_receipts=[
                CostReceipt(
                    receipt_id="offline-video",
                    component="video",
                    model=engine_pack.target_model,
                    cost=CostRecord(
                        model=engine_pack.target_model,
                        input_tokens=0,
                        output_tokens=0,
                        estimated_cost_usd=response.plan.video_estimate_usd,
                    ),
                )
            ],
        )

    monkeypatch.setattr(render_unit, "generate_video", video)
    result = run_module(
        inputs=prepared.inputs,
        params=prepared.params,
        context={"project_dir": str(store.project_dir), "runtime_params": runtime},
    )
    assert len(calls) == 1
    assert calls[0].duration_seconds == response.plan.units[0].duration_seconds == 4
    output = next(a["data"] for a in result["artifacts"] if a["artifact_type"] == "ai_previz_video")
    assert output["render_clip_id"] == response.plan.units[0].clip_id
    assert output["keyframe_ref"] is None
    assert output["cost_is_complete"] is True


def test_incidental_failure_preserves_already_incurred_compiler_receipt(tmp_path, monkeypatch):
    store, _root, _path, _response, runtime, prepared = _approved(tmp_path)
    receipt = CostReceipt(
        receipt_id="compiler",
        component="compiler",
        model="offline",
        cost=CostRecord(
            model="offline", input_tokens=10, output_tokens=20, estimated_cost_usd=0.01
        ),
    )

    def fail(**kwargs):
        kwargs["cost_receipts"].append(receipt)
        raise ValueError("failure after compiler")

    monkeypatch.setattr(execution, "execute_render", fail)
    with pytest.raises(ModuleCostError) as caught:
        run_module(
            inputs=prepared.inputs,
            params=prepared.params,
            context={"project_dir": str(store.project_dir), "runtime_params": runtime},
        )
    assert caught.value.cost_receipts == [receipt]
