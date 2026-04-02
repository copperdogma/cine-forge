from __future__ import annotations

import uuid
from pathlib import Path

import pytest
import yaml

from cine_forge.api.artifact_manager import ArtifactManager
from cine_forge.driver.engine import DriverEngine


def _write_mock_recipe(
    *,
    source_path: Path,
    target_path: Path,
    stage_params: dict[str, dict[str, object]],
    keep_stage_ids: set[str] | None = None,
) -> Path:
    payload = yaml.safe_load(source_path.read_text(encoding="utf-8"))
    stages = payload.get("stages", [])
    if keep_stage_ids is not None:
        stages = [
            stage for stage in stages
            if isinstance(stage.get("id"), str) and stage["id"] in keep_stage_ids
        ]
        payload["stages"] = stages
    for stage in stages:
        stage_id = stage.get("id")
        if not isinstance(stage_id, str) or stage_id not in stage_params:
            continue
        params = stage.setdefault("params", {})
        params.update(stage_params[stage_id])
    target_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return target_path


@pytest.mark.integration
def test_deep_breakdown_does_not_leave_self_stale_attention(tmp_path: Path) -> None:
    workspace_root = Path(__file__).resolve().parents[2]
    project_dir = tmp_path / "project_world_building"
    run_id = f"test-world-building-{uuid.uuid4().hex[:8]}"
    input_file = workspace_root / "tests" / "fixtures" / "sample_screenplay.fountain"
    ingest_recipe = _write_mock_recipe(
        source_path=workspace_root / "configs" / "recipes" / "recipe-mvp-ingest.yaml",
        target_path=tmp_path / "recipe-mvp-ingest-mock.yaml",
        stage_params={
            "normalize": {"model": "mock", "qa_model": "mock"},
            "breakdown_scenes": {"work_model": "mock"},
            "script_bible": {"work_model": "mock"},
            "project_config": {"model": "mock", "qa_model": "mock"},
        },
    )
    world_building_recipe = _write_mock_recipe(
        source_path=workspace_root / "configs" / "recipes" / "recipe-world-building.yaml",
        target_path=tmp_path / "recipe-world-building-mock.yaml",
        stage_params={
            "analyze_scenes": {
                "work_model": "mock",
                "qa_model": "mock",
                "escalate_model": "mock",
            },
            "refresh_project_config": {"model": "mock", "qa_model": "mock"},
        },
        keep_stage_ids={"analyze_scenes", "refresh_project_config"},
    )

    engine = DriverEngine(workspace_root=workspace_root, project_dir=project_dir)
    engine.run(
        recipe_path=ingest_recipe,
        run_id=f"ingest-{run_id}",
        runtime_params={
            "input_file": str(input_file),
            "default_model": "mock",
            "work_model": "mock",
            "verify_model": "mock",
            "utility_model": "mock",
            "qa_model": "mock",
            "escalate_model": "mock",
            "sota_model": "mock",
            "skip_qa": True,
            "accept_config": True,
        }
    )

    state = engine.run(
        recipe_path=world_building_recipe,
        run_id=run_id,
        runtime_params={
            "input_file": str(input_file),
            "default_model": "mock",
            "work_model": "mock",
            "verify_model": "mock",
            "utility_model": "mock",
            "qa_model": "mock",
            "escalate_model": "mock",
            "sota_model": "mock",
            "skip_qa": True,
            "accept_config": True,
        }
    )

    assert state["stages"]["analyze_scenes"]["status"] == "done"
    assert state["stages"]["refresh_project_config"]["status"] == "done"

    artifact_manager = ArtifactManager(
        project_path_resolver=lambda _project_id: project_dir,
        role_context_factory=lambda _project_id: None,
        role_catalog=None,
    )
    groups = artifact_manager.list_artifact_groups("project_world_building")

    attention_groups = [
        group
        for group in groups
        if group["artifact_type"] != "stage_review"
        and group["health"] in {"stale", "needs_revision", "needs_review", "confirmed_valid"}
    ]
    assert attention_groups == []

    scene_groups = [group for group in groups if group["artifact_type"] == "scene"]
    assert scene_groups
    assert all(group["health"] not in {"stale", "needs_revision"} for group in scene_groups)

    project_config_group = next(
        group for group in groups if group["artifact_type"] == "project_config"
    )
    assert project_config_group["latest_version"] == 2
    assert project_config_group["health"] not in {"stale", "needs_revision"}
