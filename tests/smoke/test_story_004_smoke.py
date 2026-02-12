from __future__ import annotations

from pathlib import Path

import pytest

from cine_forge.driver.engine import DriverEngine
from cine_forge.schemas import ArtifactRef


@pytest.mark.smoke
def test_story_004_ingest_normalize_smoke() -> None:
    workspace_root = Path(__file__).resolve().parents[2]
    engine = DriverEngine(workspace_root=workspace_root)

    state = engine.run(
        recipe_path=workspace_root / "configs" / "recipes" / "recipe-ingest-normalize.yaml",
        run_id="smoke-story-004-normalize",
        force=True,
        runtime_params={"input_file": str(workspace_root / "samples" / "sample-prose.txt")},
    )

    assert state["stages"]["ingest"]["status"] == "done"
    assert state["stages"]["normalize"]["status"] == "done"

    canonical_ref = ArtifactRef.model_validate(state["stages"]["normalize"]["artifact_refs"][0])
    canonical = engine.store.load_artifact(canonical_ref)
    assert canonical.data["script_text"]
