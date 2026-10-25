"""Mechanical offline API-to-persisted-media proof; not provider or UI acceptance."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from cine_forge.ai.video_types import VideoGenerationResult
from cine_forge.api.app import create_app
from cine_forge.artifacts import ArtifactStore
from cine_forge.schemas import CostRecord
from cine_forge.schemas.media_cost import CostReceipt
from tests.unit.test_media_execution_plans import media_case as shared_media_case

pytestmark = pytest.mark.unit
ROOT = Path(__file__).resolve().parents[2]


def test_ref_only_api_confirmation_executes_real_worker_and_persists_media(tmp_path, monkeypatch):
    case = shared_media_case.__wrapped__(tmp_path)
    # Discover the real modules through the isolated workspace's normal driver path.
    (case["workspace_root"] / "src").symlink_to(ROOT / "src", target_is_directory=True)
    monkeypatch.setenv("CINE_FORGE_XAI_API_KEY", "offline-test-placeholder")
    provider_requests = []

    def offline_video(*, request, engine_pack):
        provider_requests.append((request, engine_pack))
        return VideoGenerationResult(
            video_bytes=b"offline-api-boundary-video",
            media_type="video/mp4",
            model_used=engine_pack.target_model,
            provider_job_id="offline-api-job",
            cost_receipts=[
                CostReceipt(
                    receipt_id="offline-api-video",
                    component="video",
                    model=engine_pack.target_model,
                    provider=engine_pack.provider,
                    provider_job_id="offline-api-job",
                    cost=CostRecord(
                        model=engine_pack.target_model,
                        input_tokens=0,
                        output_tokens=0,
                        estimated_cost_usd=0.2,
                    ),
                )
            ],
        )

    # AI previz prompt compilation is deterministic code. Only the provider call is stubbed.
    monkeypatch.setattr(
        "cine_forge.modules.generation.render_adapter_v1.render_unit.generate_video",
        offline_video,
    )
    app = create_app(case["workspace_root"], enable_startup_dependency_checks=False)
    service = app.state.console_service
    service._project_registry[case["project_id"]] = case["project_dir"]
    with TestClient(app) as client:
        inspection = client.post(
            f"/api/projects/{case['project_id']}/media-execution-plans",
            json={
                "recipe_id": "ai_previz_generation",
                "scene_id": case["scene_id"],
                "render_clip_ids": [case["clip"].clip_id],
            },
        )
        assert inspection.status_code == 200, inspection.text
        approved = inspection.json()
        assert approved["plan"]["status"] == "ready", approved
        confirmation = client.post(
            "/api/runs/start",
            json={
                "project_id": case["project_id"],
                "media_execution_plan_ref": approved["plan_ref"],
            },
        )
        assert confirmation.status_code == 200, confirmation.text
        run_id = confirmation.json()["run_id"]
        with service._orchestrator._run_lock:
            worker = service._orchestrator._run_threads.get(run_id)
        if worker is not None:
            worker.join(timeout=15)
            assert not worker.is_alive(), "Offline worker failed to finish"
        assert run_id not in service._orchestrator._run_errors, service._orchestrator._run_errors
        result = client.get(confirmation.json()["state_url"])
        assert result.status_code == 200, result.text

    state = json.loads(
        (case["workspace_root"] / "output/runs" / run_id / "run_state.json").read_text()
    )
    assert state["stage_order"] == ["ai_previz", "validate_media"]
    assert state["stages"]["validate_media"]["status"] == "done", state
    assert state["stages"]["ai_previz"]["status"] == "done", state
    assert state["runtime_params"]["media_execution_plan_ref"] == approved["plan_ref"]
    assert state["runtime_params"]["render_clip_ids"] == [case["clip"].clip_id]
    assert state["total_cost_usd"] == pytest.approx(0.2)
    assert len(provider_requests) == 1
    request, pack = provider_requests[0]
    assert pack.pack_id == "xai_grok_imagine_video"
    assert request.duration_seconds == approved["plan"]["units"][0]["duration_seconds"] == 4
    store = ArtifactStore(case["project_dir"])
    prompt_ref = store.latest_ref("ai_previz_prompt", case["clip"].clip_id)
    video_ref = store.latest_ref("ai_previz_video", case["clip"].clip_id)
    assert prompt_ref is not None and video_ref is not None
    video = store.load_artifact(video_ref)
    assert video.data["render_clip_id"] == case["clip"].clip_id
    assert video.data["cost_is_complete"] is True
    assert video.data["cost"]["estimated_cost_usd"] == pytest.approx(0.2)
    assert video.metadata.producing_module == "render_adapter_v1"
    assert any(ref.artifact_type == "render_clip_plan" for ref in video.metadata.lineage)
    assert (
        case["project_dir"] / video.data["video"]["relative_path"]
    ).read_bytes() == b"offline-api-boundary-video"
    claims = case["project_dir"] / "media_plan_claims"
    assert len(list(claims.glob("*.started"))) == 1
    assert next(claims.glob("*.started")).read_text() == run_id

    validation_ref = store.latest_ref("media_validation", case["clip"].clip_id)
    assert validation_ref is not None
    validation = store.load_artifact(validation_ref)
    assert validation.data["target_ref"] == video_ref.model_dump(mode="json")
    assert validation.data["validated_media"] == video.data["video"]
