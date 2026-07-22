from __future__ import annotations

from pathlib import Path

import pytest

from cine_forge.ai.video import VideoGenerationResult
from cine_forge.driver.engine import DriverEngine
from cine_forge.schemas import (
    ArtifactHealth,
    ArtifactRef,
    FinalOutputArtifact,
    MediaValidationArtifact,
)
from tests.render_fixtures import seed_final_output_project
from tests.storyboard_fixtures import seed_storyboard_project


@pytest.mark.integration
def test_final_output_recipe_builds_partial_project_cut(tmp_path: Path) -> None:
    workspace_root = Path(__file__).resolve().parents[2]
    seeded = seed_final_output_project(tmp_path, rendered_scene_ids=["scene_001"])
    engine = DriverEngine(workspace_root=workspace_root, project_dir=seeded["project_dir"])

    run_state = engine.run(
        recipe_path=workspace_root / "configs" / "recipes" / "recipe-final-output.yaml",
        run_id="integration-final-output-partial",
        force=True,
    )

    assert run_state["stages"]["final_output"]["status"] == "done"
    assert run_state["stages"]["final_output_validation"]["status"] == "done"
    refs = [
        ArtifactRef.model_validate(item)
        for item in run_state["stages"]["final_output"]["artifact_refs"]
    ]
    validation_refs = [
        ArtifactRef.model_validate(item)
        for item in run_state["stages"]["final_output_validation"]["artifact_refs"]
    ]
    assert len(refs) == 1
    assert refs[0].artifact_type == "final_output"
    assert len(validation_refs) == 1
    assert validation_refs[0].artifact_type == "media_validation"
    assert validation_refs[0].entity_id == "project"

    artifact = FinalOutputArtifact.model_validate(engine.store.load_artifact(refs[0]).data)
    validation = MediaValidationArtifact.model_validate(
        engine.store.load_artifact(validation_refs[0]).data
    )
    assert artifact.coverage_state == "partial"
    assert artifact.included_scene_ids == ["scene_001"]
    assert artifact.omitted_scene_ids == ["scene_002"]
    assert artifact.video.duration_seconds == pytest.approx(4.0, rel=0.1)
    assert (seeded["project_dir"] / artifact.video.relative_path).exists()
    assert validation.target.scope_kind == "project"
    assert validation.target.coverage_state == "partial"
    assert validation.target_ref.key() == refs[0].key()


@pytest.mark.integration
def test_final_output_recipe_builds_complete_project_cut(tmp_path: Path) -> None:
    workspace_root = Path(__file__).resolve().parents[2]
    seeded = seed_final_output_project(tmp_path, rendered_scene_ids=["scene_001", "scene_002"])
    engine = DriverEngine(workspace_root=workspace_root, project_dir=seeded["project_dir"])

    run_state = engine.run(
        recipe_path=workspace_root / "configs" / "recipes" / "recipe-final-output.yaml",
        run_id="integration-final-output-complete",
        force=True,
    )

    assert run_state["stages"]["final_output"]["status"] == "done"
    assert run_state["stages"]["final_output_validation"]["status"] == "done"
    refs = [
        ArtifactRef.model_validate(item)
        for item in run_state["stages"]["final_output"]["artifact_refs"]
    ]
    validation_refs = [
        ArtifactRef.model_validate(item)
        for item in run_state["stages"]["final_output_validation"]["artifact_refs"]
    ]
    artifact = FinalOutputArtifact.model_validate(engine.store.load_artifact(refs[0]).data)
    validation = MediaValidationArtifact.model_validate(
        engine.store.load_artifact(validation_refs[0]).data
    )

    assert artifact.coverage_state == "complete"
    assert artifact.included_scene_ids == ["scene_001", "scene_002"]
    assert artifact.omitted_scene_ids == []
    assert artifact.video.duration_seconds is not None
    assert artifact.video.duration_seconds > seeded["clip_meta"]["duration_seconds"]
    assert (seeded["project_dir"] / artifact.video.relative_path).exists()
    assert validation.target.scope_kind == "project"
    assert validation.target.coverage_state == "complete"
    assert validation.target_ref.key() == refs[0].key()


@pytest.mark.integration
def test_final_output_recipe_builds_partial_cut_from_preserved_render_batch_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_root = Path(__file__).resolve().parents[2]
    seeded = seed_storyboard_project(tmp_path, scene_count=2)
    engine = DriverEngine(workspace_root=workspace_root, project_dir=seeded["project_dir"])
    clip_bytes = (
        workspace_root
        / "benchmarks"
        / "video_understanding"
        / "dialogue_confession_push_in"
        / "clip.mp4"
    ).read_bytes()

    def _fake_call_llm(**kwargs):
        schema = kwargs["response_schema"]
        prompt = str(kwargs.get("prompt") or "")
        scene_id = "scene_002" if "Scene 2:" in prompt else "scene_001"
        return (
            schema.model_validate(
                {
                    "prompt_text": f"Render {scene_id} as a controlled test shot.",
                    "sections": [
                        {
                            "section_id": "creative_brief",
                            "title": "Creative Brief",
                            "body": "Keep the render inspectable and realistic.",
                            "source_artifact_types": [],
                        },
                        {
                            "section_id": "shot_definition",
                            "title": "Shot Definition",
                            "body": f"Planned coverage for {scene_id}.",
                            "source_artifact_types": ["shot_plan"],
                        },
                    ],
                    "covered_categories": ["creative_brief", "shot_definition"],
                    "missing_inputs": [],
                    "operator_notes": [],
                }
            ),
            {
                "model": kwargs["model"],
                "input_tokens": 120,
                "output_tokens": 90,
                "estimated_cost_usd": 0.01,
                "latency_seconds": 0.2,
                "request_id": f"compile-{scene_id}",
            },
        )

    call_count = {"value": 0}

    def _fake_generate_video(*, request, engine_pack):
        call_count["value"] += 1
        if "scene_002" in request.prompt:
            raise RuntimeError("synthetic second-scene failure")
        return VideoGenerationResult(
            video_bytes=clip_bytes,
            media_type="video/mp4",
            model_used=engine_pack.target_model,
            request_id=f"video-{call_count['value']}",
            provider_job_id=f"job-{call_count['value']}",
        )

    monkeypatch.setattr(
        "cine_forge.modules.generation.render_adapter_v1.prompting.call_llm",
        _fake_call_llm,
    )
    monkeypatch.setattr("cine_forge.ai.video.generate_video", _fake_generate_video)

    with pytest.raises(RuntimeError, match="preserved 2 successful render unit"):
        engine.run(
            recipe_path=workspace_root / "configs" / "recipes" / "recipe-render-generation.yaml",
            run_id="integration-render-partial-for-final-output",
            force=True,
            start_from="render_clip_planning",
            runtime_params={
                "scene_scope": {"mode": "all_scenes", "scene_ids": []},
                "engine_pack_id": "google_veo31",
                "compiler_model": "gpt-5.4-mini",
                "planner_model": "mock",
                "duration_seconds": 8,
            },
        )

    run_state = engine.run(
        recipe_path=workspace_root / "configs" / "recipes" / "recipe-final-output.yaml",
        run_id="integration-final-output-from-partial-render-failure",
        force=True,
    )

    assert run_state["stages"]["final_output"]["status"] == "done"
    assert run_state["stages"]["final_output_validation"]["status"] == "done"
    refs = [
        ArtifactRef.model_validate(item)
        for item in run_state["stages"]["final_output"]["artifact_refs"]
    ]
    validation_refs = [
        ArtifactRef.model_validate(item)
        for item in run_state["stages"]["final_output_validation"]["artifact_refs"]
    ]
    artifact = FinalOutputArtifact.model_validate(engine.store.load_artifact(refs[0]).data)
    validation = MediaValidationArtifact.model_validate(
        engine.store.load_artifact(validation_refs[0]).data
    )

    assert artifact.coverage_state == "partial"
    assert artifact.included_scene_ids == ["scene_001"]
    assert artifact.omitted_scene_ids == ["scene_002"]
    assert (seeded["project_dir"] / artifact.video.relative_path).exists()
    assert validation.target.scope_kind == "project"
    assert validation.target.coverage_state == "partial"
    assert validation.target_ref.key() == refs[0].key()


@pytest.mark.integration
def test_final_output_recipe_allows_stale_but_compatible_timeline_refs(tmp_path: Path) -> None:
    workspace_root = Path(__file__).resolve().parents[2]
    seeded = seed_final_output_project(tmp_path, rendered_scene_ids=["scene_001"])
    engine = DriverEngine(workspace_root=workspace_root, project_dir=seeded["project_dir"])

    timeline_ref = engine.store.latest_ref("timeline", "project")
    track_manifest_ref = engine.store.latest_ref("track_manifest", "project")
    assert timeline_ref is not None
    assert track_manifest_ref is not None

    engine.store.graph.set_manual_health_override(
        timeline_ref,
        health=ArtifactHealth.STALE,
        trigger_ref=track_manifest_ref,
        source_artifact_ref=track_manifest_ref,
        rationale="Exercise final_output recipe against a stale-but-compatible timeline.",
        decided_by="tests.integration",
    )

    run_state = engine.run(
        recipe_path=workspace_root / "configs" / "recipes" / "recipe-final-output.yaml",
        run_id="integration-final-output-stale-compatible-timeline",
        force=True,
    )

    assert run_state["stages"]["final_output"]["status"] == "done"
    assert run_state["stages"]["final_output_validation"]["status"] == "done"
