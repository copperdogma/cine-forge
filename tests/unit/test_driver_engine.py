from __future__ import annotations

import json
from pathlib import Path

import pytest

from cine_forge.driver.engine import DriverEngine
from cine_forge.schemas import ArtifactHealth


def _write_echo_module(workspace_root: Path) -> None:
    module_dir = workspace_root / "src" / "cine_forge" / "modules" / "test" / "echo_v1"
    module_dir.mkdir(parents=True, exist_ok=True)
    (module_dir / "module.yaml").write_text(
        "\n".join(
            [
                "module_id: test.echo_v1",
                "stage: test",
                "description: test echo",
                "input_schemas:",
                "  - dict",
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
                "    del context",
                "    payload = params.get('payload', {'k': 'v'})",
                "    if inputs:",
                "        payload = list(inputs.values())[-1]",
                "    return {",
                "        'artifacts': [{",
                "            'artifact_type': params.get('artifact_type', 'echo'),",
                "            'entity_id': params.get('entity_id', 'project'),",
                "            'data': payload,",
                "            'metadata': {",
                "                'lineage': [],",
                "                'intent': 'test',",
                "                'rationale': 'test',",
                "                'alternatives_considered': [],",
                "                'confidence': 1.0,",
                "                'source': 'human',",
                "            },",
                "        }],",
                "        'cost': {",
                "            'model': 'code',",
                "            'input_tokens': 0,",
                "            'output_tokens': 0,",
                "            'estimated_cost_usd': 0.0,",
                "        },",
                "    }",
            ]
        ),
        encoding="utf-8",
    )


def _write_recipe(workspace_root: Path) -> Path:
    recipe_dir = workspace_root / "configs" / "recipes"
    recipe_dir.mkdir(parents=True, exist_ok=True)
    recipe_path = recipe_dir / "recipe.yaml"
    recipe_path.write_text(
        "\n".join(
            [
                "recipe_id: test-recipe",
                "description: test",
                "stages:",
                "  - id: a",
                "    module: test.echo_v1",
                "    params:",
                "      artifact_type: seed",
                "      entity_id: project",
                "      payload:",
                "        hello: world",
                "    needs: []",
                "  - id: b",
                "    module: test.echo_v1",
                "    params:",
                "      artifact_type: echo",
                "      entity_id: project",
                "    needs: [a]",
            ]
        ),
        encoding="utf-8",
    )
    return recipe_path


def _write_recipe_with_payload(workspace_root: Path, message: str) -> Path:
    recipe_path = _write_recipe(workspace_root)
    recipe_path.write_text(
        "\n".join(
            [
                "recipe_id: test-recipe",
                "description: test",
                "stages:",
                "  - id: a",
                "    module: test.echo_v1",
                "    params:",
                "      artifact_type: seed",
                "      entity_id: project",
                "      payload:",
                f"        hello: {message}",
                "    needs: []",
                "  - id: b",
                "    module: test.echo_v1",
                "    params:",
                "      artifact_type: echo",
                "      entity_id: project",
                "    needs: [a]",
            ]
        ),
        encoding="utf-8",
    )
    return recipe_path


def _rewrite_module_default_payload(workspace_root: Path, message: str) -> None:
    module_main = workspace_root / "src" / "cine_forge" / "modules" / "test" / "echo_v1" / "main.py"
    module_main.write_text(
        "\n".join(
            [
                "def run_module(inputs, params, context):",
                "    del context",
                f"    payload = params.get('payload', {{'k': '{message}'}})",
                "    if inputs:",
                "        payload = list(inputs.values())[-1]",
                "    return {",
                "        'artifacts': [{",
                "            'artifact_type': params.get('artifact_type', 'echo'),",
                "            'entity_id': params.get('entity_id', 'project'),",
                "            'data': payload,",
                "            'metadata': {",
                "                'lineage': [],",
                "                'intent': 'test',",
                "                'rationale': 'test',",
                "                'alternatives_considered': [],",
                "                'confidence': 1.0,",
                "                'source': 'human',",
                "            },",
                "        }],",
                "        'cost': {",
                "            'model': 'code',",
                "            'input_tokens': 0,",
                "            'output_tokens': 0,",
                "            'estimated_cost_usd': 0.0,",
                "        },",
                "    }",
            ]
        ),
        encoding="utf-8",
    )


def _touch_module_helper_file(workspace_root: Path, text: str) -> None:
    helper_path = (
        workspace_root / "src" / "cine_forge" / "modules" / "test" / "echo_v1" / "helper.py"
    )
    helper_path.write_text(text, encoding="utf-8")


def _write_runtime_echo_module(workspace_root: Path) -> None:
    module_dir = workspace_root / "src" / "cine_forge" / "modules" / "test" / "runtime_echo_v1"
    module_dir.mkdir(parents=True, exist_ok=True)
    (module_dir / "module.yaml").write_text(
        "\n".join(
            [
                "module_id: test.runtime_echo_v1",
                "stage: test",
                "description: runtime-aware echo",
                "input_schemas:",
                "  - dict",
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
                "    runtime = context.get('runtime_params', {})",
                "    marker = runtime.get('marker', 'missing')",
                "    payload = {'marker': marker}",
                "    if inputs:",
                "        payload = {**list(inputs.values())[-1], 'marker': marker}",
                "    return {",
                "        'artifacts': [{",
                "            'artifact_type': params.get('artifact_type', 'runtime_echo'),",
                "            'entity_id': params.get('entity_id', 'project'),",
                "            'data': payload,",
                "            'metadata': {",
                "                'lineage': [],",
                "                'intent': 'test',",
                "                'rationale': 'test runtime params',",
                "                'alternatives_considered': [],",
                "                'confidence': 1.0,",
                "                'source': 'human',",
                "            },",
                "        }],",
                "        'cost': {",
                "            'model': 'code',",
                "            'input_tokens': 0,",
                "            'output_tokens': 0,",
                "            'estimated_cost_usd': 0.0,",
                "        },",
                "    }",
            ]
        ),
        encoding="utf-8",
    )


def _write_runtime_recipe(workspace_root: Path) -> Path:
    recipe_dir = workspace_root / "configs" / "recipes"
    recipe_dir.mkdir(parents=True, exist_ok=True)
    recipe_path = recipe_dir / "runtime_recipe.yaml"
    recipe_path.write_text(
        "\n".join(
            [
                "recipe_id: runtime-recipe",
                "description: runtime",
                "stages:",
                "  - id: a",
                "    module: test.runtime_echo_v1",
                "    params:",
                "      artifact_type: seed",
                "      entity_id: project",
                "    needs: []",
                "  - id: b",
                "    module: test.runtime_echo_v1",
                "    params:",
                "      artifact_type: echo",
                "      entity_id: project",
                "    needs: [a]",
            ]
        ),
        encoding="utf-8",
    )
    return recipe_path


def _write_placeholder_recipe(workspace_root: Path) -> Path:
    recipe_dir = workspace_root / "configs" / "recipes"
    recipe_dir.mkdir(parents=True, exist_ok=True)
    recipe_path = recipe_dir / "placeholder_recipe.yaml"
    recipe_path.write_text(
        "\n".join(
            [
                "recipe_id: placeholder-recipe",
                "description: runtime placeholders",
                "stages:",
                "  - id: a",
                "    module: test.echo_v1",
                "    params:",
                "      artifact_type: seed",
                "      entity_id: project",
                "      payload:",
                "        hello: ${message}",
                "    needs: []",
            ]
        ),
        encoding="utf-8",
    )
    return recipe_path


def _write_pause_module(workspace_root: Path) -> None:
    module_dir = workspace_root / "src" / "cine_forge" / "modules" / "test" / "pause_v1"
    module_dir.mkdir(parents=True, exist_ok=True)
    (module_dir / "module.yaml").write_text(
        "\n".join(
            [
                "module_id: test.pause_v1",
                "stage: test",
                "description: pause module",
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
                "    del inputs, params, context",
                "    return {",
                "        'artifacts': [{",
                "            'artifact_type': 'draft',",
                "            'entity_id': 'project',",
                "            'data': {'ready': False},",
                "            'metadata': {",
                "                'lineage': [],",
                "                'intent': 'pause',",
                "                'rationale': 'pause',",
                "                'alternatives_considered': [],",
                "                'confidence': 1.0,",
                "                'source': 'human',",
                "            },",
                "        }],",
                "        'cost': {",
                "            'model': 'code',",
                "            'input_tokens': 0,",
                "            'output_tokens': 0,",
                "            'estimated_cost_usd': 0.0,",
                "        },",
                "        'pause_reason': 'Awaiting human confirmation.',",
                "    }",
            ]
        ),
        encoding="utf-8",
    )


def _write_pause_recipe(workspace_root: Path) -> Path:
    recipe_dir = workspace_root / "configs" / "recipes"
    recipe_dir.mkdir(parents=True, exist_ok=True)
    recipe_path = recipe_dir / "pause_recipe.yaml"
    recipe_path.write_text(
        "\n".join(
            [
                "recipe_id: pause-recipe",
                "description: pause",
                "stages:",
                "  - id: config",
                "    module: test.pause_v1",
                "    params: {}",
                "    needs: []",
                "  - id: next",
                "    module: test.echo_v1",
                "    params:",
                "      artifact_type: final",
                "      entity_id: project",
                "    needs: [config]",
            ]
        ),
        encoding="utf-8",
    )
    return recipe_path


def _write_project_config_producer_module(workspace_root: Path) -> None:
    module_dir = (
        workspace_root / "src" / "cine_forge" / "modules" / "test" / "project_config_seed_v1"
    )
    module_dir.mkdir(parents=True, exist_ok=True)
    (module_dir / "module.yaml").write_text(
        "\n".join(
            [
                "module_id: test.project_config_seed_v1",
                "stage: test",
                "description: emits project config",
                "input_schemas: []",
                "output_schemas:",
                "  - project_config",
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
                "    title = params.get('title', 'Project')",
                "    tone = params.get('tone', 'grounded')",
                "    payload = {",
                "        'title': title,",
                "        'format': 'short_film',",
                "        'genre': ['drama'],",
                "        'tone': [tone],",
                "        'estimated_duration_minutes': 10.0,",
                "        'primary_characters': ['MARA'],",
                "        'supporting_characters': [],",
                "        'location_count': 1,",
                "        'locations_summary': ['LAB'],",
                "        'target_audience': None,",
                "        'aspect_ratio': '16:9',",
                "        'production_mode': 'ai_generated',",
                "        'human_control_mode': 'checkpoint',",
                "        'style_packs': {},",
                "        'budget_cap_usd': None,",
                "        'default_model': 'mock',",
                "        'detection_details': {",
                "            'title': {",
                "                'value': title,",
                "                'confidence': 1.0,",
                "                'rationale': 'seed',",
                "                'source': 'user_specified',",
                "            },",
                "        },",
                "        'confirmed': True,",
                "        'confirmed_at': '2026-02-12T00:00:00Z',",
                "    }",
                "    return {",
                "        'artifacts': [{",
                "            'artifact_type': 'project_config',",
                "            'entity_id': 'project',",
                "            'data': payload,",
                "            'metadata': {",
                "                'lineage': [],",
                "                'intent': 'seed project config',",
                "                'rationale': 'test',",
                "                'alternatives_considered': [],",
                "                'confidence': 1.0,",
                "                'source': 'human',",
                "            },",
                "        }],",
                "        'cost': {",
                "            'model': 'code',",
                "            'input_tokens': 0,",
                "            'output_tokens': 0,",
                "            'estimated_cost_usd': 0.0,",
                "        },",
                "    }",
            ]
        ),
        encoding="utf-8",
    )


def _write_project_config_consumer_module(workspace_root: Path) -> None:
    module_dir = (
        workspace_root / "src" / "cine_forge" / "modules" / "test" / "project_config_consumer_v1"
    )
    module_dir.mkdir(parents=True, exist_ok=True)
    (module_dir / "module.yaml").write_text(
        "\n".join(
            [
                "module_id: test.project_config_consumer_v1",
                "stage: test",
                "description: reads project config",
                "input_schemas:",
                "  - project_config",
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
                "    del params, context",
                "    config = list(inputs.values())[-1]",
                "    payload = {'title': config['title'], 'tone': config['tone']}",
                "    return {",
                "        'artifacts': [{",
                "            'artifact_type': 'config_summary',",
                "            'entity_id': 'project',",
                "            'data': payload,",
                "            'metadata': {",
                "                'lineage': [],",
                "                'intent': 'consume config',",
                "                'rationale': 'test dependency',",
                "                'alternatives_considered': [],",
                "                'confidence': 1.0,",
                "                'source': 'human',",
                "            },",
                "        }],",
                "        'cost': {",
                "            'model': 'code',",
                "            'input_tokens': 0,",
                "            'output_tokens': 0,",
                "            'estimated_cost_usd': 0.0,",
                "        },",
                "    }",
            ]
        ),
        encoding="utf-8",
    )


def _write_project_config_dependency_recipe(workspace_root: Path, tone: str) -> Path:
    recipe_dir = workspace_root / "configs" / "recipes"
    recipe_dir.mkdir(parents=True, exist_ok=True)
    recipe_path = recipe_dir / "project_config_dependency.yaml"
    recipe_path.write_text(
        "\n".join(
            [
                "recipe_id: project-config-dependency",
                "description: dependency",
                "stages:",
                "  - id: config",
                "    module: test.project_config_seed_v1",
                "    params:",
                "      title: Story",
                f"      tone: {tone}",
                "    needs: []",
                "  - id: consume",
                "    module: test.project_config_consumer_v1",
                "    params: {}",
                "    needs: [config]",
            ]
        ),
        encoding="utf-8",
    )
    return recipe_path


def _write_fallback_module(workspace_root: Path) -> None:
    module_dir = workspace_root / "src" / "cine_forge" / "modules" / "test" / "fallback_v1"
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
                "                'intent': 'fallback',",
                "                'rationale': 'fallback test',",
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


def _write_fallback_recipe(workspace_root: Path) -> Path:
    recipe_dir = workspace_root / "configs" / "recipes"
    recipe_dir.mkdir(parents=True, exist_ok=True)
    recipe_path = recipe_dir / "fallback_recipe.yaml"
    recipe_path.write_text(
        "\n".join(
            [
                "recipe_id: fallback-recipe",
                "description: fallback test",
                "resilience:",
                "  retry_base_delay_seconds: 0",
                "  retry_jitter_ratio: 0",
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
    return recipe_path


def _write_fallback_recipe_with_resilience_override(workspace_root: Path) -> Path:
    recipe_dir = workspace_root / "configs" / "recipes"
    recipe_dir.mkdir(parents=True, exist_ok=True)
    recipe_path = recipe_dir / "fallback_recipe_override.yaml"
    recipe_path.write_text(
        "\n".join(
            [
                "recipe_id: fallback-recipe-override",
                "description: fallback override test",
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
    return recipe_path


def _write_fallback_recipe_with_attempt_budget(workspace_root: Path, max_attempts: int) -> Path:
    recipe_dir = workspace_root / "configs" / "recipes"
    recipe_dir.mkdir(parents=True, exist_ok=True)
    recipe_path = recipe_dir / "fallback_recipe_budget.yaml"
    recipe_path.write_text(
        "\n".join(
            [
                "recipe_id: fallback-recipe-budget",
                "description: fallback attempt budget test",
                "resilience:",
                f"  max_attempts_per_stage: {max_attempts}",
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
    return recipe_path


@pytest.mark.unit
def test_driver_dry_run_writes_state(tmp_path: Path) -> None:
    _write_echo_module(tmp_path)
    recipe_path = _write_recipe(tmp_path)
    engine = DriverEngine(workspace_root=tmp_path)
    state = engine.run(recipe_path=recipe_path, run_id="dry-1", dry_run=True)
    assert state["dry_run"] is True
    assert (tmp_path / "output" / "runs" / "dry-1" / "run_state.json").exists()


@pytest.mark.unit
def test_driver_executes_stages_and_records_state(tmp_path: Path) -> None:
    _write_echo_module(tmp_path)
    recipe_path = _write_recipe(tmp_path)
    engine = DriverEngine(workspace_root=tmp_path)
    state = engine.run(recipe_path=recipe_path, run_id="run-1")
    assert state["stages"]["a"]["status"] == "done"
    assert state["stages"]["b"]["status"] == "done"
    assert (tmp_path / "output" / "runs" / "run-1" / "pipeline_events.jsonl").exists()


@pytest.mark.unit
def test_driver_start_from_reuses_upstream_artifacts(tmp_path: Path) -> None:
    _write_echo_module(tmp_path)
    recipe_path = _write_recipe(tmp_path)
    engine = DriverEngine(workspace_root=tmp_path)
    engine.run(recipe_path=recipe_path, run_id="baseline")

    state = engine.run(
        recipe_path=recipe_path,
        run_id="resume-b",
        start_from="b",
        force=True,
    )
    latest_echo_ref = engine.store.list_versions("echo", "project")[-1]
    latest_echo = engine.store.load_artifact(latest_echo_ref)

    assert state["stages"]["a"]["status"] == "skipped_reused"
    assert state["stages"]["b"]["status"] == "done"
    assert latest_echo.data == {"hello": "world"}


@pytest.mark.unit
def test_driver_records_lineage_and_graph_edges(tmp_path: Path) -> None:
    _write_echo_module(tmp_path)
    recipe_path = _write_recipe(tmp_path)
    engine = DriverEngine(workspace_root=tmp_path)
    engine.run(recipe_path=recipe_path, run_id="lineage-1")

    latest_echo_ref = engine.store.list_versions("echo", "project")[-1]
    latest_echo = engine.store.load_artifact(latest_echo_ref)
    dependencies = engine.store.graph.get_dependencies(latest_echo_ref)

    assert latest_echo.metadata.lineage
    assert any(ref.artifact_type == "seed" for ref in latest_echo.metadata.lineage)
    assert any(ref.artifact_type == "seed" for ref in dependencies)


@pytest.mark.unit
def test_driver_force_controls_skip_behavior(tmp_path: Path) -> None:
    _write_echo_module(tmp_path)
    recipe_path = _write_recipe(tmp_path)
    engine = DriverEngine(workspace_root=tmp_path)
    engine.run(recipe_path=recipe_path, run_id="first")

    reused = engine.run(recipe_path=recipe_path, run_id="second")
    forced = engine.run(recipe_path=recipe_path, run_id="third", force=True)

    assert reused["stages"]["a"]["status"] == "skipped_reused"
    assert reused["stages"]["b"]["status"] == "skipped_reused"
    assert forced["stages"]["a"]["status"] == "done"
    assert forced["stages"]["b"]["status"] == "done"


@pytest.mark.unit
def test_driver_cache_invalidates_when_stage_params_change(tmp_path: Path) -> None:
    _write_echo_module(tmp_path)
    recipe_path = _write_recipe_with_payload(tmp_path, "world")
    engine = DriverEngine(workspace_root=tmp_path)
    engine.run(recipe_path=recipe_path, run_id="first")

    updated_recipe_path = _write_recipe_with_payload(tmp_path, "galaxy")
    rerun = engine.run(recipe_path=updated_recipe_path, run_id="second")
    latest_seed_ref = engine.store.list_versions("seed", "project")[-1]
    latest_seed = engine.store.load_artifact(latest_seed_ref)

    assert rerun["stages"]["a"]["status"] == "done"
    assert rerun["stages"]["b"]["status"] == "done"
    assert latest_seed.data == {"hello": "galaxy"}


@pytest.mark.unit
def test_driver_cache_invalidates_when_module_code_changes(tmp_path: Path) -> None:
    _write_echo_module(tmp_path)
    recipe_path = _write_recipe(tmp_path)
    engine = DriverEngine(workspace_root=tmp_path)
    engine.run(recipe_path=recipe_path, run_id="first")

    _rewrite_module_default_payload(tmp_path, "updated")
    rerun = engine.run(recipe_path=recipe_path, run_id="second")

    assert rerun["stages"]["a"]["status"] == "done"
    assert rerun["stages"]["b"]["status"] == "done"


@pytest.mark.unit
def test_driver_cache_invalidates_when_module_helper_changes(tmp_path: Path) -> None:
    _write_echo_module(tmp_path)
    recipe_path = _write_recipe(tmp_path)
    engine = DriverEngine(workspace_root=tmp_path)
    engine.run(recipe_path=recipe_path, run_id="first")

    _touch_module_helper_file(tmp_path, "VALUE = 1\n")
    rerun = engine.run(recipe_path=recipe_path, run_id="second")

    assert rerun["stages"]["a"]["status"] == "done"
    assert rerun["stages"]["b"]["status"] == "done"


@pytest.mark.unit
def test_driver_start_from_reuses_runtime_param_fingerprint(tmp_path: Path) -> None:
    _write_runtime_echo_module(tmp_path)
    recipe_path = _write_runtime_recipe(tmp_path)
    engine = DriverEngine(workspace_root=tmp_path)
    engine.run(
        recipe_path=recipe_path,
        run_id="first",
        runtime_params={"marker": "same"},
    )

    resumed = engine.run(
        recipe_path=recipe_path,
        run_id="resume-b",
        start_from="b",
        force=True,
        runtime_params={"marker": "same"},
    )
    latest_echo_ref = engine.store.list_versions("echo", "project")[-1]
    latest_echo = engine.store.load_artifact(latest_echo_ref)

    assert resumed["stages"]["a"]["status"] == "skipped_reused"
    assert resumed["stages"]["b"]["status"] == "done"
    assert latest_echo.data["marker"] == "same"


@pytest.mark.unit
def test_driver_start_from_can_reuse_upstream_from_resume_ref_payloads(tmp_path: Path) -> None:
    _write_echo_module(tmp_path)
    recipe_path = _write_recipe(tmp_path)
    engine = DriverEngine(workspace_root=tmp_path)
    baseline = engine.run(recipe_path=recipe_path, run_id="baseline-refs")

    # Simulate historical run without usable stage cache.
    stage_cache_path = tmp_path / "output" / "project" / "stage_cache.json"
    if stage_cache_path.exists():
        stage_cache_path.unlink()

    resume_refs = {
        stage_id: stage_state["artifact_refs"]
        for stage_id, stage_state in baseline["stages"].items()
    }
    resumed = engine.run(
        recipe_path=recipe_path,
        run_id="resume-refs",
        start_from="b",
        force=True,
        runtime_params={"__resume_artifact_refs_by_stage": resume_refs},
    )

    assert resumed["stages"]["a"]["status"] == "skipped_reused"
    assert resumed["stages"]["b"]["status"] == "done"


@pytest.mark.unit
def test_driver_resolves_runtime_placeholders_in_stage_params(tmp_path: Path) -> None:
    _write_echo_module(tmp_path)
    recipe_path = _write_placeholder_recipe(tmp_path)
    engine = DriverEngine(workspace_root=tmp_path)

    state = engine.run(
        recipe_path=recipe_path,
        run_id="placeholder",
        runtime_params={"message": "galaxy"},
    )
    latest_seed_ref = engine.store.list_versions("seed", "project")[-1]
    latest_seed = engine.store.load_artifact(latest_seed_ref)

    assert state["stages"]["a"]["status"] == "done"
    assert latest_seed.data == {"hello": "galaxy"}


@pytest.mark.unit
def test_driver_raises_when_runtime_placeholder_missing(tmp_path: Path) -> None:
    _write_echo_module(tmp_path)
    recipe_path = _write_placeholder_recipe(tmp_path)
    engine = DriverEngine(workspace_root=tmp_path)

    with pytest.raises(ValueError, match="Missing runtime parameter"):
        engine.run(recipe_path=recipe_path, run_id="placeholder-missing")


@pytest.mark.unit
def test_driver_registers_scene_schemas(tmp_path: Path) -> None:
    engine = DriverEngine(workspace_root=tmp_path)
    assert engine.schemas.has("scene") is True
    assert engine.schemas.has("scene_index") is True
    assert engine.schemas.has("project_config") is True


@pytest.mark.unit
def test_driver_schema_selection_prefers_artifact_type_for_multi_output() -> None:
    selected = DriverEngine._schema_names_for_artifact(
        artifact={"artifact_type": "scene"},
        output_schemas=["scene", "scene_index"],
    )
    assert selected == ["scene"]


@pytest.mark.unit
def test_driver_cache_invalidates_when_config_file_content_changes(tmp_path: Path) -> None:
    _write_echo_module(tmp_path)
    recipe_path = _write_recipe(tmp_path)
    config_path = tmp_path / "user_config.yaml"
    config_path.write_text("title: one\n", encoding="utf-8")
    engine = DriverEngine(workspace_root=tmp_path)

    engine.run(
        recipe_path=recipe_path,
        run_id="first",
        runtime_params={"config_file": str(config_path)},
    )
    reused = engine.run(
        recipe_path=recipe_path,
        run_id="second",
        runtime_params={"config_file": str(config_path)},
    )

    config_path.write_text("title: two\n", encoding="utf-8")
    rerun = engine.run(
        recipe_path=recipe_path,
        run_id="third",
        runtime_params={"config_file": str(config_path)},
    )

    assert reused["stages"]["a"]["status"] == "skipped_reused"
    assert reused["stages"]["b"]["status"] == "skipped_reused"
    assert rerun["stages"]["a"]["status"] == "done"
    assert rerun["stages"]["b"]["status"] == "done"


@pytest.mark.unit
def test_driver_records_paused_stage_and_stops_downstream(tmp_path: Path) -> None:
    _write_echo_module(tmp_path)
    _write_pause_module(tmp_path)
    recipe_path = _write_pause_recipe(tmp_path)
    engine = DriverEngine(workspace_root=tmp_path)

    state = engine.run(recipe_path=recipe_path, run_id="paused")

    assert state["stages"]["config"]["status"] == "paused"
    assert state["stages"]["next"]["status"] == "pending"
    events_path = tmp_path / "output" / "runs" / "paused" / "pipeline_events.jsonl"
    events = events_path.read_text(encoding="utf-8")
    assert "stage_paused" in events


@pytest.mark.unit
def test_driver_falls_back_to_next_model_on_transient_stage_error(tmp_path: Path) -> None:
    _write_fallback_module(tmp_path)
    recipe_path = _write_fallback_recipe(tmp_path)
    engine = DriverEngine(workspace_root=tmp_path)

    state = engine.run(recipe_path=recipe_path, run_id="fallback")

    assert state["stages"]["normalize"]["status"] == "done"
    assert state["stages"]["normalize"]["attempt_count"] == 2
    assert state["stages"]["normalize"]["model_used"] == "claude-opus-4-6"
    assert state["stages"]["normalize"]["attempts"][0]["status"] == "failed"
    assert state["stages"]["normalize"]["attempts"][0]["provider"] == "anthropic"
    assert state["stages"]["normalize"]["attempts"][0]["error_code"] == "529"
    assert state["stages"]["normalize"]["attempts"][0]["transient"] is True
    assert state["stages"]["normalize"]["attempts"][1]["status"] == "success"

    latest_ref = engine.store.list_versions("dict", "project")[-1]
    latest = engine.store.load_artifact(latest_ref)
    assert latest.data["used_model"] == "claude-opus-4-6"
    assert latest.metadata.annotations["final_stage_model_used"] == "claude-opus-4-6"
    assert latest.metadata.annotations["final_stage_provider_used"] == "anthropic"

    events_path = tmp_path / "output" / "runs" / "fallback" / "pipeline_events.jsonl"
    events = [
        json.loads(line)
        for line in events_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    retry_event = next(event for event in events if event["event"] == "stage_retrying")
    fallback_event = next(event for event in events if event["event"] == "stage_fallback")
    assert retry_event["error_code"] == "529"
    assert retry_event["retry_delay_seconds"] == 0.0
    assert fallback_event["to_model"] == "claude-opus-4-6"


@pytest.mark.unit
def test_driver_uses_recipe_resilience_fallback_override(tmp_path: Path) -> None:
    _write_fallback_module(tmp_path)
    recipe_path = _write_fallback_recipe_with_resilience_override(tmp_path)
    engine = DriverEngine(workspace_root=tmp_path)

    state = engine.run(recipe_path=recipe_path, run_id="fallback-override")

    assert state["stages"]["normalize"]["status"] == "done"
    assert state["stages"]["normalize"]["attempt_count"] == 2
    assert state["stages"]["normalize"]["model_used"] == "gpt-4.1"
    assert state["stages"]["normalize"]["attempts"][1]["model"] == "gpt-4.1"
    latest_ref = engine.store.list_versions("dict", "project")[-1]
    latest = engine.store.load_artifact(latest_ref)
    assert latest.metadata.annotations["final_stage_model_used"] == "gpt-4.1"
    assert latest.metadata.annotations["final_stage_provider_used"] == "openai"


@pytest.mark.unit
def test_driver_skips_unhealthy_provider_models_in_attempt_plan(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_fallback_module(tmp_path)
    recipe_path = _write_fallback_recipe(tmp_path)
    engine = DriverEngine(workspace_root=tmp_path)

    monkeypatch.setattr(
        DriverEngine,
        "_provider_is_healthy",
        staticmethod(lambda provider: provider != "anthropic"),
    )

    state = engine.run(recipe_path=recipe_path, run_id="fallback-skip-unhealthy")

    assert state["stages"]["normalize"]["status"] == "done"
    assert state["stages"]["normalize"]["attempt_count"] == 1
    assert state["stages"]["normalize"]["model_used"] == "gpt-4.1"
    assert state["stages"]["normalize"]["attempts"][0]["model"] == "gpt-4.1"


@pytest.mark.unit
def test_driver_respects_max_attempts_per_stage_budget(tmp_path: Path) -> None:
    _write_fallback_module(tmp_path)
    recipe_path = _write_fallback_recipe_with_attempt_budget(tmp_path, max_attempts=1)
    engine = DriverEngine(workspace_root=tmp_path)

    with pytest.raises(RuntimeError, match="529"):
        engine.run(recipe_path=recipe_path, run_id="fallback-budget")

    state_path = tmp_path / "output" / "runs" / "fallback-budget" / "run_state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    stage = state["stages"]["normalize"]
    assert stage["status"] == "failed"
    assert stage["attempt_count"] == 1

    events_path = tmp_path / "output" / "runs" / "fallback-budget" / "pipeline_events.jsonl"
    events = [
        json.loads(line)
        for line in events_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    failure_event = next(event for event in events if event["event"] == "stage_failed")
    assert failure_event["attempt_count"] == 1
    assert failure_event["error_code"] == "529"
    assert failure_event["provider"] == "anthropic"
    assert failure_event["terminal_reason"] == "retry_budget_exhausted_or_no_fallback"
    assert not any(event["event"] == "stage_fallback" for event in events)


def _write_store_inputs_recipe(workspace_root: Path, store_inputs: dict[str, str]) -> Path:
    recipe_dir = workspace_root / "configs" / "recipes"
    recipe_dir.mkdir(parents=True, exist_ok=True)
    recipe_path = recipe_dir / "store_inputs_recipe.yaml"
    store_inputs_yaml = "\n".join(f"        {k}: {v}" for k, v in store_inputs.items())
    recipe_path.write_text(
        "\n".join(
            [
                "recipe_id: store-inputs-recipe",
                "description: store inputs test",
                "stages:",
                "  - id: consumer",
                "    module: test.echo_v1",
                "    params:",
                "      artifact_type: echo",
                "      entity_id: project",
                "    needs: []",
                "    store_inputs:",
                store_inputs_yaml,
            ]
        ),
        encoding="utf-8",
    )
    return recipe_path


def _write_store_inputs_optional_recipe(
    workspace_root: Path, store_inputs_optional: dict[str, str]
) -> Path:
    recipe_dir = workspace_root / "configs" / "recipes"
    recipe_dir.mkdir(parents=True, exist_ok=True)
    recipe_path = recipe_dir / "store_inputs_optional_recipe.yaml"
    store_inputs_optional_yaml = "\n".join(
        f"        {k}: {v}" for k, v in store_inputs_optional.items()
    )
    recipe_path.write_text(
        "\n".join(
            [
                "recipe_id: store-inputs-optional-recipe",
                "description: optional store inputs test",
                "stages:",
                "  - id: consumer",
                "    module: test.echo_v1",
                "    params:",
                "      artifact_type: echo",
                "      entity_id: project",
                "    needs: []",
                "    store_inputs_optional:",
                store_inputs_optional_yaml,
            ]
        ),
        encoding="utf-8",
    )
    return recipe_path


def _write_store_inputs_overlap_recipe(workspace_root: Path) -> Path:
    recipe_dir = workspace_root / "configs" / "recipes"
    recipe_dir.mkdir(parents=True, exist_ok=True)
    recipe_path = recipe_dir / "overlap_recipe.yaml"
    recipe_path.write_text(
        "\n".join(
            [
                "recipe_id: overlap-recipe",
                "description: overlap test",
                "stages:",
                "  - id: producer",
                "    module: test.echo_v1",
                "    params:",
                "      artifact_type: seed",
                "      entity_id: project",
                "    needs: []",
                "  - id: consumer",
                "    module: test.echo_v1",
                "    params:",
                "      artifact_type: result",
                "      entity_id: project",
                "    needs: [producer]",
                "    store_inputs:",
                "      producer: dict",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return recipe_path


@pytest.mark.unit
def test_store_inputs_resolves_from_store(tmp_path: Path) -> None:
    """Run recipe A to produce a 'dict' artifact, then recipe B with store_inputs resolves it."""
    _write_echo_module(tmp_path)

    # First run: produce an 'echo' (type=dict-compatible) artifact in the store.
    # The default echo module saves artifact_type based on params; use a recipe
    # that produces artifact_type='dict' so store_inputs validation passes.
    recipe_dir = tmp_path / "configs" / "recipes"
    recipe_dir.mkdir(parents=True, exist_ok=True)
    producer_path = recipe_dir / "producer.yaml"
    producer_path.write_text(
        "\n".join(
            [
                "recipe_id: producer-recipe",
                "description: produce dict artifact",
                "stages:",
                "  - id: a",
                "    module: test.echo_v1",
                "    params:",
                "      artifact_type: dict",
                "      entity_id: project",
                "      payload:",
                "        hello: world",
                "    needs: []",
            ]
        ),
        encoding="utf-8",
    )
    engine = DriverEngine(workspace_root=tmp_path)
    engine.run(recipe_path=producer_path, run_id="producer-run")

    dict_versions = engine.store.list_versions("dict", "project")
    assert len(dict_versions) >= 1

    # Second run: consume via store_inputs
    consumer_recipe = _write_store_inputs_recipe(tmp_path, {"upstream": "dict"})
    state = engine.run(recipe_path=consumer_recipe, run_id="consumer-run")

    assert state["stages"]["consumer"]["status"] == "done"
    # The echo module passes through the last input value as payload
    echo_ref = engine.store.list_versions("echo", "project")[-1]
    echo_artifact = engine.store.load_artifact(echo_ref)
    assert echo_artifact.data == {"hello": "world"}


@pytest.mark.unit
def test_store_inputs_error_when_missing(tmp_path: Path) -> None:
    """store_inputs referencing a non-existent artifact type raises ValueError."""
    _write_echo_module(tmp_path)
    engine = DriverEngine(workspace_root=tmp_path)

    consumer_recipe = _write_store_inputs_recipe(tmp_path, {"upstream": "dict"})
    with pytest.raises(ValueError, match="none exist in the store"):
        engine.run(recipe_path=consumer_recipe, run_id="missing-run")


@pytest.mark.unit
def test_store_inputs_error_when_stale(tmp_path: Path) -> None:
    """store_inputs referencing a stale artifact raises ValueError."""
    _write_echo_module(tmp_path)

    # Produce a dict artifact
    recipe_dir = tmp_path / "configs" / "recipes"
    recipe_dir.mkdir(parents=True, exist_ok=True)
    producer_path = recipe_dir / "producer.yaml"
    producer_path.write_text(
        "\n".join(
            [
                "recipe_id: producer-recipe",
                "description: produce dict artifact",
                "stages:",
                "  - id: a",
                "    module: test.echo_v1",
                "    params:",
                "      artifact_type: dict",
                "      entity_id: project",
                "      payload:",
                "        data: test",
                "    needs: []",
            ]
        ),
        encoding="utf-8",
    )
    engine = DriverEngine(workspace_root=tmp_path)
    engine.run(recipe_path=producer_path, run_id="producer-run")

    # Mark the artifact as stale by directly manipulating the graph file
    dict_ref = engine.store.list_versions("dict", "project")[-1]
    graph = engine.store.graph._read_graph()
    graph["nodes"][dict_ref.key()]["health"] = ArtifactHealth.STALE.value
    engine.store.graph._write_graph(graph)

    consumer_recipe = _write_store_inputs_recipe(tmp_path, {"upstream": "dict"})
    with pytest.raises(ValueError, match="has health"):
        engine.run(recipe_path=consumer_recipe, run_id="stale-run")


@pytest.mark.unit
def test_store_inputs_rejects_overlap_with_needs(tmp_path: Path) -> None:
    """Validation rejects a stage with the same key in both needs and store_inputs."""
    _write_echo_module(tmp_path)
    engine = DriverEngine(workspace_root=tmp_path)

    overlap_recipe = _write_store_inputs_overlap_recipe(tmp_path)
    with pytest.raises(ValueError, match="both 'needs' and 'store_inputs'"):
        engine.run(recipe_path=overlap_recipe, run_id="overlap-run")


@pytest.mark.unit
def test_store_inputs_optional_uses_store_when_available(tmp_path: Path) -> None:
    _write_echo_module(tmp_path)
    recipe_dir = tmp_path / "configs" / "recipes"
    recipe_dir.mkdir(parents=True, exist_ok=True)
    producer_path = recipe_dir / "producer.yaml"
    producer_path.write_text(
        "\n".join(
            [
                "recipe_id: producer-recipe",
                "description: produce dict artifact",
                "stages:",
                "  - id: a",
                "    module: test.echo_v1",
                "    params:",
                "      artifact_type: dict",
                "      entity_id: project",
                "      payload:",
                "        hello: optional-world",
                "    needs: []",
            ]
        ),
        encoding="utf-8",
    )
    engine = DriverEngine(workspace_root=tmp_path)
    engine.run(recipe_path=producer_path, run_id="producer-run")

    consumer_recipe = _write_store_inputs_optional_recipe(tmp_path, {"upstream": "dict"})
    state = engine.run(recipe_path=consumer_recipe, run_id="consumer-run")
    assert state["stages"]["consumer"]["status"] == "done"
    echo_ref = engine.store.list_versions("echo", "project")[-1]
    echo_artifact = engine.store.load_artifact(echo_ref)
    assert echo_artifact.data == {"hello": "optional-world"}


@pytest.mark.unit
def test_store_inputs_optional_skips_when_missing_or_unhealthy(tmp_path: Path) -> None:
    _write_echo_module(tmp_path)
    engine = DriverEngine(workspace_root=tmp_path)

    consumer_recipe = _write_store_inputs_optional_recipe(tmp_path, {"upstream": "dict"})
    state_missing = engine.run(recipe_path=consumer_recipe, run_id="optional-missing-run")
    assert state_missing["stages"]["consumer"]["status"] == "done"
    echo_ref_missing = engine.store.list_versions("echo", "project")[-1]
    echo_artifact_missing = engine.store.load_artifact(echo_ref_missing)
    assert echo_artifact_missing.data == {"k": "v"}

    recipe_dir = tmp_path / "configs" / "recipes"
    recipe_dir.mkdir(parents=True, exist_ok=True)
    producer_path = recipe_dir / "producer.yaml"
    producer_path.write_text(
        "\n".join(
            [
                "recipe_id: producer-recipe",
                "description: produce dict artifact",
                "stages:",
                "  - id: a",
                "    module: test.echo_v1",
                "    params:",
                "      artifact_type: dict",
                "      entity_id: project",
                "      payload:",
                "        hello: stale-world",
                "    needs: []",
            ]
        ),
        encoding="utf-8",
    )
    engine.run(recipe_path=producer_path, run_id="producer-run")
    dict_ref = engine.store.list_versions("dict", "project")[-1]
    graph = engine.store.graph._read_graph()
    graph["nodes"][dict_ref.key()]["health"] = ArtifactHealth.STALE.value
    engine.store.graph._write_graph(graph)

    state_unhealthy = engine.run(
        recipe_path=consumer_recipe,
        run_id="optional-unhealthy-run",
        force=True,
    )
    assert state_unhealthy["stages"]["consumer"]["status"] == "done"
    echo_ref_unhealthy = engine.store.list_versions("echo", "project")[-1]
    echo_artifact_unhealthy = engine.store.load_artifact(echo_ref_unhealthy)
    assert echo_artifact_unhealthy.data == {"k": "v"}


@pytest.mark.unit
def test_project_config_change_marks_downstream_artifacts_stale(tmp_path: Path) -> None:
    _write_project_config_producer_module(tmp_path)
    _write_project_config_consumer_module(tmp_path)
    first_recipe = _write_project_config_dependency_recipe(tmp_path, tone="grounded")
    engine = DriverEngine(workspace_root=tmp_path)

    engine.run(recipe_path=first_recipe, run_id="first")
    first_summary_ref = engine.store.list_versions("config_summary", "project")[-1]

    second_recipe = _write_project_config_dependency_recipe(tmp_path, tone="dark")
    engine.run(recipe_path=second_recipe, run_id="second")
    second_summary_ref = engine.store.list_versions("config_summary", "project")[-1]

    assert first_summary_ref.version == 1
    assert second_summary_ref.version == 2
    assert engine.store.graph.get_health(first_summary_ref) == ArtifactHealth.STALE


def _write_parallel_recipe(workspace_root: Path) -> Path:
    """Recipe with a seed stage followed by 3 independent stages (parallelizable)."""
    recipe_dir = workspace_root / "configs" / "recipes"
    recipe_dir.mkdir(parents=True, exist_ok=True)
    recipe_path = recipe_dir / "parallel_recipe.yaml"
    recipe_path.write_text(
        "\n".join(
            [
                "recipe_id: parallel-recipe",
                "description: parallel test",
                "stages:",
                "  - id: seed",
                "    module: test.echo_v1",
                "    params:",
                "      artifact_type: seed",
                "      entity_id: project",
                "      payload:",
                "        hello: world",
                "    needs: []",
                "  - id: branch_a",
                "    module: test.echo_v1",
                "    params:",
                "      artifact_type: echo",
                "      entity_id: branch_a",
                "    needs: [seed]",
                "  - id: branch_b",
                "    module: test.echo_v1",
                "    params:",
                "      artifact_type: echo",
                "      entity_id: branch_b",
                "    needs: [seed]",
                "  - id: branch_c",
                "    module: test.echo_v1",
                "    params:",
                "      artifact_type: echo",
                "      entity_id: branch_c",
                "    needs: [seed]",
            ]
        ),
        encoding="utf-8",
    )
    return recipe_path


@pytest.mark.unit
def test_driver_parallel_independent_stages(tmp_path: Path) -> None:
    """Independent stages with the same dependency run in parallel and all complete."""
    _write_echo_module(tmp_path)
    recipe_path = _write_parallel_recipe(tmp_path)
    engine = DriverEngine(workspace_root=tmp_path)

    state = engine.run(recipe_path=recipe_path, run_id="parallel-1")

    assert state["stages"]["seed"]["status"] == "done"
    assert state["stages"]["branch_a"]["status"] == "done"
    assert state["stages"]["branch_b"]["status"] == "done"
    assert state["stages"]["branch_c"]["status"] == "done"
    assert state.get("finished_at") is not None

    # All three branches should produce artifacts
    for entity in ["branch_a", "branch_b", "branch_c"]:
        versions = engine.store.list_versions("echo", entity)
        assert len(versions) >= 1

    # Verify wave computation: seed is wave 0, branches are wave 1
    from cine_forge.driver.recipe import load_recipe, resolve_execution_order

    recipe = load_recipe(recipe_path=recipe_path)
    order = resolve_execution_order(recipe=recipe)
    stage_by_id = {s.id: s for s in recipe.stages}
    waves = DriverEngine._compute_execution_waves(order, stage_by_id)
    assert waves == [["seed"], ["branch_a", "branch_b", "branch_c"]]


@pytest.mark.unit
def test_driver_parallel_all_independent_stages(tmp_path: Path) -> None:
    """All stages with needs=[] run in a single wave."""
    _write_echo_module(tmp_path)
    recipe_dir = tmp_path / "configs" / "recipes"
    recipe_dir.mkdir(parents=True, exist_ok=True)
    recipe_path = recipe_dir / "all_parallel.yaml"
    recipe_path.write_text(
        "\n".join(
            [
                "recipe_id: all-parallel",
                "description: all parallel",
                "stages:",
                "  - id: x",
                "    module: test.echo_v1",
                "    params:",
                "      artifact_type: echo",
                "      entity_id: x",
                "    needs: []",
                "  - id: y",
                "    module: test.echo_v1",
                "    params:",
                "      artifact_type: echo",
                "      entity_id: y",
                "    needs: []",
                "  - id: z",
                "    module: test.echo_v1",
                "    params:",
                "      artifact_type: echo",
                "      entity_id: z",
                "    needs: []",
            ]
        ),
        encoding="utf-8",
    )
    engine = DriverEngine(workspace_root=tmp_path)
    state = engine.run(recipe_path=recipe_path, run_id="all-par")

    assert state["stages"]["x"]["status"] == "done"
    assert state["stages"]["y"]["status"] == "done"
    assert state["stages"]["z"]["status"] == "done"

    from cine_forge.driver.recipe import load_recipe, resolve_execution_order

    recipe = load_recipe(recipe_path=recipe_path)
    order = resolve_execution_order(recipe=recipe)
    stage_by_id = {s.id: s for s in recipe.stages}
    waves = DriverEngine._compute_execution_waves(order, stage_by_id)
    # All 3 should be in a single wave
    assert len(waves) == 1
    assert set(waves[0]) == {"x", "y", "z"}
