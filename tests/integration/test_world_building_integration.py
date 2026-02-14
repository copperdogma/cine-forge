from __future__ import annotations

import uuid
from pathlib import Path

import pytest

from cine_forge.driver.engine import DriverEngine
from cine_forge.schemas import ArtifactRef


@pytest.mark.integration
def test_world_building_pipeline_creates_character_bibles(tmp_path: Path) -> None:
    workspace_root = Path(__file__).resolve().parents[2]
    project_dir = tmp_path / "project_world_building"
    run_id = f"test-world-building-{uuid.uuid4().hex[:8]}"
    
    # We'll use the sample screenplay fixture
    input_file = workspace_root / "tests" / "fixtures" / "sample_screenplay.fountain"
    
    engine = DriverEngine(workspace_root=workspace_root, project_dir=project_dir)
    # Run ingest first to populate the store for store_inputs
    engine.run(
        recipe_path=workspace_root / "configs" / "recipes" / "recipe-mvp-ingest.yaml",
        run_id=f"ingest-{run_id}",
        runtime_params={
            "input_file": str(input_file),
            "default_model": "mock",
            "utility_model": "mock",
            "sota_model": "mock",
            "skip_qa": True,
            "accept_config": True,
        }
    )

    state = engine.run(
        recipe_path=workspace_root / "configs" / "recipes" / "recipe-world-building.yaml",
        run_id=run_id,
        runtime_params={
            "input_file": str(input_file),
            "default_model": "mock",
            "utility_model": "mock",
            "sota_model": "mock",
            "skip_qa": True,
            "accept_config": True,
        }
    )
    
    assert state["stages"]["character_bible"]["status"] == "done"
    
    # Check bible artifacts
    bible_refs = [
        ArtifactRef.model_validate(ref)
        for ref in state["stages"]["character_bible"]["artifact_refs"]
    ]
    # In Signal in the Rain: Aria (6), Noah (6), June (8), Kell (5)
    # should all pass min_appearances=3
    assert len(bible_refs) >= 4

    location_refs = [
        ref
        for ref in state["stages"]["location_bible"]["artifact_refs"]
        if ref["artifact_type"] == "bible_manifest"
    ]
    # STUDIO should be produced
    assert len(location_refs) >= 1

    prop_refs = [
        ref
        for ref in state["stages"]["prop_bible"]["artifact_refs"]
        if ref["artifact_type"] == "bible_manifest"
    ]
    # Mock returns 2 props
    assert len(prop_refs) == 2
    
    for ref in bible_refs:
        assert ref.artifact_type == "bible_manifest"
        manifest, metadata = engine.store.load_bible_entry(ref)
        assert manifest.entity_type == "character"
        assert manifest.version == 1
        assert len(manifest.files) == 1
        assert manifest.files[0].purpose == "master_definition"
        
        # Check master file exists
        master_path = (
            project_dir
            / "artifacts"
            / "bibles"
            / f"character_{manifest.entity_id}"
            / manifest.files[0].filename
        )
        assert master_path.exists()
