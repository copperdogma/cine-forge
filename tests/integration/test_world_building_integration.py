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
    state = engine.run(
        recipe_path=workspace_root / "configs" / "recipes" / "recipe-world-building.yaml",
        run_id=run_id,
        runtime_params={
            "input_file": str(input_file),
            "default_model": "mock",
        }
    )
    
    assert state["stages"]["character_bible"]["status"] == "done"
    
    # Check bible artifacts
    bible_refs = [
        ArtifactRef.model_validate(ref)
        for ref in state["stages"]["character_bible"]["artifact_refs"]
    ]
    assert len(bible_refs) >= 3 # Aria, Noah, June at least
    
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
