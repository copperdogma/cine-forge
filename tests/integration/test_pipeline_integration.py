from __future__ import annotations

import json
from pathlib import Path

import pytest

from cine_forge.driver.engine import DriverEngine


@pytest.mark.integration
def test_recipe_executes_end_to_end() -> None:
    workspace_root = Path(__file__).resolve().parents[2]
    engine = DriverEngine(workspace_root=workspace_root)
    run_id = "integration-echo"
    state = engine.run(
        recipe_path=workspace_root / "configs" / "recipes" / "recipe-test-echo.yaml",
        run_id=run_id,
        force=True,
    )

    run_dir = workspace_root / "output" / "runs" / run_id
    state_path = run_dir / "run_state.json"
    events_path = run_dir / "pipeline_events.jsonl"

    assert run_dir.exists()
    assert state_path.exists()
    assert events_path.exists()
    assert state["stages"]["seed"]["status"] == "done"
    assert state["stages"]["echo"]["status"] == "done"

    run_state_data = json.loads(state_path.read_text(encoding="utf-8"))
    assert run_state_data["total_cost_usd"] >= 0.0
    assert run_state_data["stages"]["echo"]["artifact_refs"]


@pytest.mark.integration
def test_injected_provider_overload_falls_back_and_completes(tmp_path: Path) -> None:
    module_dir = tmp_path / "src" / "cine_forge" / "modules" / "test" / "fallback_v1"
    module_dir.mkdir(parents=True, exist_ok=True)
    (module_dir / "module.yaml").write_text(
        "\n".join(
            [
                "module_id: test.fallback_v1",
                "stage: test",
                "description: fallback module",
                "input_schemas: []",
                "output_schemas:",
                "  - dict",
                "parameters: {}",
            ]
        ),
        encoding="utf-8",
    )
    (module_dir / "main.py").write_text(
        "\n".join(
            [
                "def run_module(inputs, params, context):",
                "    del inputs, context",
                "    model = params.get('work_model') or params.get('model') or 'unknown'",
                "    if model == 'claude-sonnet-4-6':",
                "        raise RuntimeError('Anthropic HTTP error 529: overloaded_error')",
                "    return {",
                "        'artifacts': [{",
                "            'artifact_type': 'dict',",
                "            'entity_id': 'project',",
                "            'data': {'used_model': model},",
                "            'metadata': {",
                "                'lineage': [],",
                "                'intent': 'integration-fallback',",
                "                'rationale': 'simulate provider overload',",
                "                'alternatives_considered': [],",
                "                'confidence': 1.0,",
                "                'source': 'human',",
                "            },",
                "        }],",
                "        'cost': {",
                "            'model': model,",
                "            'input_tokens': 1,",
                "            'output_tokens': 1,",
                "            'estimated_cost_usd': 0.0,",
                "        },",
                "    }",
            ]
        ),
        encoding="utf-8",
    )

    recipe_dir = tmp_path / "configs" / "recipes"
    recipe_dir.mkdir(parents=True, exist_ok=True)
    recipe_path = recipe_dir / "recipe-overload-smoke.yaml"
    recipe_path.write_text(
        "\n".join(
            [
                "recipe_id: overload-smoke",
                "description: injected overload with fallback",
                "resilience:",
                "  retry_base_delay_seconds: 0",
                "  retry_jitter_ratio: 0",
                "  stage_fallback_models:",
                "    normalize:",
                "      - gpt-4.1",
                "stages:",
                "  - id: normalize",
                "    module: test.fallback_v1",
                "    params:",
                "      model: claude-sonnet-4-6",
                "    needs: []",
            ]
        ),
        encoding="utf-8",
    )

    engine = DriverEngine(workspace_root=tmp_path)
    state = engine.run(recipe_path=recipe_path, run_id="integration-overload-fallback")

    assert state["stages"]["normalize"]["status"] == "done"
    assert state["stages"]["normalize"]["attempt_count"] == 2
    assert state["stages"]["normalize"]["model_used"] == "gpt-4.1"

    run_dir = tmp_path / "output" / "runs" / "integration-overload-fallback"
    events_path = run_dir / "pipeline_events.jsonl"
    assert events_path.exists()
    events_text = events_path.read_text(encoding="utf-8")
    assert "stage_retrying" in events_text
    assert "stage_fallback" in events_text
