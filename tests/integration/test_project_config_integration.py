from __future__ import annotations

from pathlib import Path

import pytest

from cine_forge.driver.engine import DriverEngine
from cine_forge.schemas import ArtifactRef


@pytest.mark.integration
def test_project_config_recipe_persists_confirmed_config_with_lineage() -> None:
    workspace_root = Path(__file__).resolve().parents[2]
    engine = DriverEngine(workspace_root=workspace_root)
    state = engine.run(
        recipe_path=workspace_root / "configs" / "recipes" / "recipe-ingest-extract-config.yaml",
        run_id="integration-project-config",
        force=True,
        runtime_params={
            "input_file": str(workspace_root / "samples" / "sample-screenplay.fountain")
        },
    )

    assert state["stages"]["config"]["status"] == "done"

    refs = [ArtifactRef.model_validate(item) for item in state["stages"]["config"]["artifact_refs"]]
    assert len(refs) == 1
    assert refs[0].artifact_type == "project_config"

    config_artifact = engine.store.load_artifact(refs[0])
    assert config_artifact.data["confirmed"] is True
    assert config_artifact.data["detection_details"]["title"]["rationale"]

    lineage_types = {ref.artifact_type for ref in config_artifact.metadata.lineage}
    assert "canonical_script" in lineage_types
    assert "scene_index" in lineage_types
