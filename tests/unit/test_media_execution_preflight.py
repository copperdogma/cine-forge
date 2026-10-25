"""Preparation slices remain available without generation credentials."""

from pathlib import Path

import pytest

from cine_forge.api.models import RunStartRequest
from cine_forge.pipeline.scene_actions import build_scene_action_preflight
from cine_forge.schemas.scene_scope import SceneExecutionScope
from tests.unit.test_scene_actions import _seed_scene_action_project

pytestmark = pytest.mark.unit


def test_text_preparation_does_not_require_xai(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("CINE_FORGE_XAI_API_KEY", raising=False)
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    project = _seed_scene_action_project(tmp_path)
    common = dict(
        project_path=project,
        recipe_id="ai_previz_generation",
        scene_scope=SceneExecutionScope(mode="current_scene", scene_ids=["scene_001"]),
    )
    preparation = build_scene_action_preflight(**common, end_at="render_clip_planning")
    assert preparation.status != "soft_block"
    assert not any("credentials" in item.label for item in preparation.items)
    generation = build_scene_action_preflight(**common)
    assert generation.status == "soft_block"
    assert any("credentials unavailable" in item.label for item in generation.items)


def test_api_requires_normal_inputs_but_accepts_plan_only():
    with pytest.raises(ValueError, match="input_file and default_model"):
        RunStartRequest(project_id="project")
    request = RunStartRequest(
        project_id="project",
        media_execution_plan_ref={
            "artifact_type": "media_execution_plan",
            "entity_id": "plan-1",
            "version": 1,
            "path": "artifacts/media_execution_plan/plan-1/v1.json",
        },
    )
    assert set(request.model_dump(exclude_unset=True)) == {"project_id", "media_execution_plan_ref"}
