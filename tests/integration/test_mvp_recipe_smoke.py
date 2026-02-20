from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any

import pytest
import yaml

from cine_forge.artifacts import ArtifactStore
from cine_forge.driver.engine import DriverEngine
from cine_forge.schemas import ArtifactHealth, ArtifactRef


def _assert_fixture_bundle_valid(fixture_root: Path) -> None:
    """Ensure mock response files exist for common extraction points."""
    required = [
        "normalization_screenplay_cleanup.txt",
        "normalization_qa.json",
        "project_config_autodetect.json",
    ]
    for filename in required:
        if not (fixture_root / filename).exists():
            raise FileNotFoundError(f"Mock fixture missing: {fixture_root / filename}")


def _run_mvp_recipe(
    workspace_root: Path,
    run_id: str,
    input_file: Path,
    default_model: str,
    qa_model: str,
    project_dir: Path,
    force: bool = True,
) -> tuple[DriverEngine, dict[str, Any]]:
    # Clean up prior project dir to ensure a fresh smoke run
    if project_dir.exists():
        import shutil

        shutil.rmtree(project_dir)
    project_dir.mkdir(parents=True, exist_ok=True)

    engine = DriverEngine(workspace_root=workspace_root, project_dir=project_dir)
    recipe_path = workspace_root / "configs" / "recipes" / "recipe-mvp-ingest.yaml"

    state = engine.run(
        recipe_path=recipe_path,
        run_id=run_id,
        force=force,
        runtime_params={
            "input_file": str(input_file),
            "default_model": default_model,
            "qa_model": qa_model,
            "accept_config": True,
        },
    )
    return engine, state


@pytest.mark.integration
@pytest.mark.smoke
def test_mvp_recipe_smoke_mocked_end_to_end(monkeypatch: pytest.MonkeyPatch) -> None:
    workspace_root = Path(__file__).resolve().parents[2]
    run_id = f"smoke-mvp-mock-{uuid.uuid4().hex[:8]}"
    input_file = workspace_root / "tests" / "fixtures" / "sample_screenplay.fountain"
    project_dir = workspace_root / "output" / "project_smoke_mvp_mock"
    fixture_root = workspace_root / "tests" / "fixtures" / "mvp_mock_responses"
    _assert_fixture_bundle_valid(fixture_root)
    monkeypatch.setenv("CINE_FORGE_MOCK_FIXTURE_DIR", str(fixture_root))

    engine, state = _run_mvp_recipe(
        workspace_root=workspace_root,
        run_id=run_id,
        input_file=input_file,
        default_model="fixture",
        qa_model="fixture",
        project_dir=project_dir,
    )

    assert state["stages"]["ingest"]["status"] == "done"
    assert state["stages"]["normalize"]["status"] == "done"
    assert state["stages"]["extract_scenes"]["status"] == "done"
    assert state["stages"]["project_config"]["status"] == "done"

    ingest_ref = ArtifactRef.model_validate(state["stages"]["ingest"]["artifact_refs"][0])
    canonical_ref = ArtifactRef.model_validate(state["stages"]["normalize"]["artifact_refs"][0])
    extract_refs = [
        ArtifactRef.model_validate(item)
        for item in state["stages"]["extract_scenes"]["artifact_refs"]
    ]
    scene_refs = [ref for ref in extract_refs if ref.artifact_type == "scene"]
    scene_index_ref = next(ref for ref in extract_refs if ref.artifact_type == "scene_index")
    project_config_ref = ArtifactRef.model_validate(
        state["stages"]["project_config"]["artifact_refs"][0]
    )

    assert scene_refs
    assert len(scene_refs) >= 5

    produced_refs = [ingest_ref, canonical_ref, *scene_refs, scene_index_ref, project_config_ref]
    for artifact_ref in produced_refs:
        artifact = engine.store.load_artifact(artifact_ref)
        assert (project_dir / artifact_ref.path).exists()
        validation = engine.schemas.validate(
            schema_name=artifact_ref.artifact_type,
            data=artifact.data,
        )
        assert validation.valid is True
        assert engine.store.graph.get_health(artifact_ref) == ArtifactHealth.VALID

    canonical = engine.store.load_artifact(canonical_ref)
    assert canonical.metadata.lineage
    assert canonical.metadata.lineage[0].artifact_type == "raw_input"
    if "qa_result" in canonical.metadata.annotations:
        assert canonical.metadata.annotations["qa_result"]["passed"] is True
    assert canonical.metadata.cost_data is not None
    assert canonical.metadata.cost_data.estimated_cost_usd >= 0.0
    normalization_costs = canonical.metadata.annotations.get("normalization_call_costs", [])
    if normalization_costs:
        normalize_call_models = {
            item["model"] for item in normalization_costs
        }
        assert "fixture" in normalize_call_models
    for scene_ref in scene_refs:
        scene_artifact = engine.store.load_artifact(scene_ref)
        lineage_types = {ref.artifact_type for ref in scene_artifact.metadata.lineage}
        assert "canonical_script" in lineage_types
        # Some scenes might fail QA due to model noise, but we should verify it was recorded
        if "qa_result" in scene_artifact.metadata.annotations:
            # If it failed, it should be marked NEEDS_REVIEW
            if not scene_artifact.metadata.annotations["qa_result"]["passed"]:
                assert scene_artifact.metadata.health == ArtifactHealth.NEEDS_REVIEW.value
            else:
                assert scene_artifact.metadata.health == ArtifactHealth.VALID.value
        assert scene_artifact.metadata.cost_data is not None

    scene_index = engine.store.load_artifact(scene_index_ref)
    scene_index_lineage = {ref.artifact_type for ref in scene_index.metadata.lineage}
    assert "canonical_script" in scene_index_lineage
    assert "scene" in scene_index_lineage

    project_config = engine.store.load_artifact(project_config_ref)
    config_lineage = {ref.artifact_type for ref in project_config.metadata.lineage}
    assert "canonical_script" in config_lineage


@pytest.mark.integration
@pytest.mark.smoke
def test_mvp_recipe_smoke_reused_caching(monkeypatch: pytest.MonkeyPatch) -> None:
    workspace_root = Path(__file__).resolve().parents[2]
    run_id_first = f"smoke-mvp-cache-first-{uuid.uuid4().hex[:8]}"
    run_id_second = f"smoke-mvp-cache-second-{uuid.uuid4().hex[:8]}"
    input_file = workspace_root / "tests" / "fixtures" / "sample_screenplay.fountain"
    project_dir = workspace_root / "output" / "project_smoke_mvp_stale"
    fixture_root = workspace_root / "tests" / "fixtures" / "mvp_mock_responses"
    _assert_fixture_bundle_valid(fixture_root)
    monkeypatch.setenv("CINE_FORGE_MOCK_FIXTURE_DIR", str(fixture_root))

    # 1. Run once to populate cache
    engine, state_first = _run_mvp_recipe(
        workspace_root=workspace_root,
        run_id=run_id_first,
        input_file=input_file,
        default_model="fixture",
        qa_model="fixture",
        project_dir=project_dir,
    )
    assert state_first["stages"]["ingest"]["status"] == "done"

    # 2. Run again — should reuse everything
    state_second = engine.run(
        recipe_path=workspace_root / "configs" / "recipes" / "recipe-mvp-ingest.yaml",
        run_id=run_id_second,
        force=False,
        runtime_params={
            "input_file": str(input_file),
            "default_model": "fixture",
            "qa_model": "fixture",
            "accept_config": True,
        },
    )
    for stage_id in ["ingest", "normalize", "extract_scenes", "project_config"]:
        assert state_second["stages"][stage_id]["status"] == "skipped_reused"


@pytest.mark.integration
@pytest.mark.smoke
def test_mvp_recipe_live_smoke() -> None:
    """Run full MVP ingest against live SOTA model (skipped by default)."""
    if os.getenv("CINE_FORGE_LIVE_TESTS") != "1":
        pytest.skip("Set CINE_FORGE_LIVE_TESTS=1 to run live smoke test")

    workspace_root = Path(__file__).resolve().parents[2]
    run_id = f"smoke-mvp-live-{uuid.uuid4().hex[:8]}"
    input_file = workspace_root / "tests" / "fixtures" / "sample_screenplay.fountain"
    project_dir = workspace_root / "output" / "project_smoke_mvp_live"

    engine, state = _run_mvp_recipe(
        workspace_root=workspace_root,
        run_id=run_id,
        input_file=input_file,
        default_model=os.getenv("CINE_FORGE_LIVE_MODEL", "claude-haiku-4-5-20251001"),
        qa_model=os.getenv("CINE_FORGE_LIVE_MODEL", "claude-haiku-4-5-20251001"),
        project_dir=project_dir,
    )

    assert state["stages"]["project_config"]["status"] == "done"
    assert state["total_cost_usd"] > 0.0


@pytest.mark.integration
def test_mvp_recipe_with_params_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    workspace_root = Path(__file__).resolve().parents[2]
    run_id = f"smoke-params-file-{uuid.uuid4().hex[:8]}"
    input_file = workspace_root / "tests" / "fixtures" / "sample_screenplay.fountain"
    project_dir = tmp_path / "project_params_test"
    fixture_root = workspace_root / "tests" / "fixtures" / "mvp_mock_responses"
    monkeypatch.setenv("CINE_FORGE_MOCK_FIXTURE_DIR", str(fixture_root))

    params_file = tmp_path / "params.yaml"
    params_file.write_text(
        yaml.dump(
            {
                "input_file": str(input_file),
                "default_model": "fixture",
                "qa_model": "fixture",
                "accept_config": True,
            }
        ),
        encoding="utf-8",
    )

    engine = DriverEngine(workspace_root=workspace_root, project_dir=project_dir)
    recipe_path = workspace_root / "configs" / "recipes" / "recipe-mvp-ingest.yaml"

    # Runtime params from file should be respected
    state = engine.run(
        recipe_path=recipe_path,
        run_id=run_id,
        runtime_params=yaml.safe_load(params_file.read_text(encoding="utf-8")),
    )

    assert state["stages"]["ingest"]["status"] == "done"
    assert state["runtime_params"]["default_model"] == "fixture"


@pytest.mark.integration
def test_mvp_recipe_stale_propagation(monkeypatch: pytest.MonkeyPatch) -> None:
    workspace_root = Path(__file__).resolve().parents[2]
    run_id_first = f"smoke-mvp-stale-first-{uuid.uuid4().hex[:8]}"
    run_id_second = f"smoke-mvp-stale-second-{uuid.uuid4().hex[:8]}"
    input_file = workspace_root / "tests" / "fixtures" / "sample_screenplay.fountain"
    project_dir = workspace_root / "output" / "project_smoke_mvp_stale_propagation"
    fixture_root = workspace_root / "tests" / "fixtures" / "mvp_mock_responses"
    monkeypatch.setenv("CINE_FORGE_MOCK_FIXTURE_DIR", str(fixture_root))

    # 1. First run to baseline everything
    engine, state_first = _run_mvp_recipe(
        workspace_root=workspace_root,
        run_id=run_id_first,
        input_file=input_file,
        default_model="fixture",
        qa_model="fixture",
        project_dir=project_dir,
    )
    assert state_first["stages"]["project_config"]["status"] == "done"

    # 2. Mark canonical_script as STALE manually
    # (Simulates an external change or re-normalization requirement)
    store = ArtifactStore(project_dir=project_dir)
    canonical_ref = ArtifactRef.model_validate(
        state_first["stages"]["normalize"]["artifact_refs"][0]
    )

    graph_data = store.graph._read_graph()
    graph_data["nodes"][canonical_ref.key()]["health"] = ArtifactHealth.STALE.value
    store.graph._write_graph(graph_data)

    # 3. Second run — stages depending on canonical_script should re-run
    # extract_scenes depends on normalize (which produces canonical_script)
    state_second = engine.run(
        recipe_path=workspace_root / "configs" / "recipes" / "recipe-mvp-ingest.yaml",
        run_id=run_id_second,
        force=False,
        runtime_params={
            "input_file": str(input_file),
            "default_model": "fixture",
            "qa_model": "fixture",
            "accept_config": True,
        },
    )

    # Ingest should still be skipped (upstream of normalize)
    assert state_second["stages"]["ingest"]["status"] == "skipped_reused"
    # normalize should re-run because it was marked stale
    assert state_second["stages"]["normalize"]["status"] == "done"
    # extract_scenes should re-run because its input (canonical_script) was marked stale
    assert state_second["stages"]["extract_scenes"]["status"] == "done"
    # project_config should re-run because its inputs were re-produced
    assert state_second["stages"]["project_config"]["status"] == "done"
