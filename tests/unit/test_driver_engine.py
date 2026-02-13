from __future__ import annotations

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
                "            'model': 'none',",
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
                "            'model': 'none',",
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
                "            'model': 'none',",
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
                "            'model': 'none',",
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
                "            'model': 'none',",
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
                "            'model': 'none',",
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
