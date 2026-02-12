from __future__ import annotations

from pathlib import Path

import pytest

from cine_forge.driver.engine import DriverEngine
from cine_forge.schemas import ArtifactRef


@pytest.mark.integration
def test_ingest_normalize_extract_recipe_persists_scene_artifacts() -> None:
    workspace_root = Path(__file__).resolve().parents[2]
    engine = DriverEngine(workspace_root=workspace_root)
    state = engine.run(
        recipe_path=workspace_root / "configs" / "recipes" / "recipe-ingest-extract.yaml",
        run_id="integration-scene-extract",
        force=True,
        runtime_params={
            "input_file": str(workspace_root / "samples" / "sample-screenplay.fountain")
        },
    )

    assert state["stages"]["ingest"]["status"] == "done"
    assert state["stages"]["normalize"]["status"] == "done"
    assert state["stages"]["extract"]["status"] == "done"

    refs = [
        ArtifactRef.model_validate(item)
        for item in state["stages"]["extract"]["artifact_refs"]
    ]
    assert any(ref.artifact_type == "scene" for ref in refs)
    assert any(ref.artifact_type == "scene_index" for ref in refs)

    scene_index_ref = next(ref for ref in refs if ref.artifact_type == "scene_index")
    scene_index = engine.store.load_artifact(scene_index_ref)
    assert scene_index.data["total_scenes"] >= 1
    assert scene_index.data["scenes_passed_qa"] >= 1
