"""Recovery must retain the inspected-media preparation stop boundary."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from cine_forge.api.service import OperatorConsoleService
from cine_forge.driver.engine import DriverEngine
from tests.unit.test_driver_engine import _write_echo_module

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("action,status", [("retry", "failed"), ("resume", "paused")])
def test_recovery_runs_preparation_without_entering_media(
    tmp_path: Path, monkeypatch, action, status
):
    _write_echo_module(tmp_path)
    media_dir = tmp_path / "src/cine_forge/modules/test/forbidden_media"
    media_dir.mkdir()
    (media_dir / "module.yaml").write_text(
        yaml.safe_dump(
            {
                "module_id": "render_adapter_v1",
                "stage": "test",
                "description": "forbidden media sentinel",
                "input_schemas": ["dict"],
                "output_schemas": ["dict"],
                "parameters": {},
            }
        )
    )
    (media_dir / "main.py").write_text(
        "def run_module(inputs, params, context):\n"
        "    raise AssertionError('Paid media stage was reached without confirmation')\n"
    )
    recipes = tmp_path / "configs/recipes"
    recipes.mkdir(parents=True)
    recipe = recipes / "recipe-ai-previz-generation.yaml"
    recipe.write_text(
        yaml.safe_dump(
            {
                "recipe_id": "ai_previz_generation",
                "description": "bounded recovery fixture",
                "stages": [
                    {"id": "render_clip_planning", "module": "test.echo_v1", "params": {}},
                    {
                        "id": "ai_previz",
                        "module": "render_adapter_v1",
                        "after": ["render_clip_planning"],
                    },
                ],
            }
        )
    )
    project = tmp_path / "output/recovery"
    project.mkdir(parents=True)
    old = tmp_path / "output/runs/original"
    old.mkdir(parents=True)
    (old / "run_meta.json").write_text(
        json.dumps({"project_id": "recovery", "project_path": str(project)})
    )
    (old / "run_state.json").write_text(
        json.dumps(
            {
                "run_id": "original",
                "recipe_id": "ai_previz_generation",
                "runtime_params": {
                    "input_file": "fixture.fountain",
                    "default_model": "mock",
                    "end_at": "render_clip_planning",
                },
                "stages": {
                    "render_clip_planning": {"status": status},
                    "ai_previz": {"status": "pending"},
                },
            }
        )
    )
    captured = {}

    class Thread:
        def __init__(self, *, target, kwargs, daemon):
            captured.update(kwargs)

        def start(self):
            pass

    monkeypatch.setattr("cine_forge.api.run_orchestrator.threading.Thread", Thread)
    service = OperatorConsoleService(tmp_path)
    if action == "resume":
        service.resume_run("original", overrides={"run_budget_limit_usd": 2})
    else:
        service.retry_failed_stage("original")
    assert captured["end_at"] == captured["runtime_params"]["end_at"] == "render_clip_planning"
    engine = DriverEngine(tmp_path, project_dir=project)
    engine.schemas.register("echo", dict)
    state = engine.run(
        recipe_path=captured["recipe_path"],
        run_id=captured["run_id"],
        runtime_params=captured["runtime_params"],
        start_from=captured["start_from"],
        end_at=captured["end_at"],
    )
    assert state["stages"]["render_clip_planning"]["status"] == "done"
    assert state["stages"]["ai_previz"]["status"] == "pending"
    assert state["stage_order"] == ["render_clip_planning"]
