from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest

from cine_forge.driver.engine import DriverEngine
from cine_forge.schemas import ArtifactRef


@pytest.mark.integration
def test_story_ingest_recipe_persists_raw_input_and_versions() -> None:
    workspace_root = Path(__file__).resolve().parents[2]
    engine = DriverEngine(workspace_root=workspace_root)
    recipe_path = workspace_root / "configs" / "recipes" / "recipe-ingest-only.yaml"

    screenplay_file = workspace_root / "samples" / "sample-screenplay.fountain"
    prose_file = workspace_root / "samples" / "sample-prose.txt"

    first = engine.run(
        recipe_path=recipe_path,
        run_id="integration-story-ingest-v1",
        force=True,
        runtime_params={"input_file": str(screenplay_file)},
    )
    second = engine.run(
        recipe_path=recipe_path,
        run_id="integration-story-ingest-v2",
        force=True,
        runtime_params={"input_file": str(prose_file)},
    )

    assert first["stages"]["ingest"]["status"] == "done"
    assert second["stages"]["ingest"]["status"] == "done"

    first_ref = ArtifactRef.model_validate(first["stages"]["ingest"]["artifact_refs"][0])
    second_ref = ArtifactRef.model_validate(second["stages"]["ingest"]["artifact_refs"][0])
    assert second_ref.version > first_ref.version

    previous = engine.store.load_artifact(first_ref)
    latest = engine.store.load_artifact(second_ref)
    assert latest.data["source_info"]["original_filename"] == "sample-prose.txt"
    assert previous.data["source_info"]["original_filename"] == "sample-screenplay.fountain"
    assert latest.data["content"]
    assert latest.data["classification"]["detected_format"] in {
        "screenplay",
        "prose",
        "hybrid",
        "notes",
        "unknown",
    }


@pytest.mark.integration
@pytest.mark.parametrize(
    ("fixture_name", "expected_file_format", "expected_detected_format"),
    [
        ("owl_creek_bridge.txt", "txt", "prose"),
        ("owl_creek_bridge_excerpt.md", "md", "prose"),
        ("run_like_hell_teaser.fountain", "fountain", "screenplay"),
        ("pit_and_pendulum.pdf", "pdf", "prose"),
    ],
)
def test_story_ingest_supports_all_fixture_formats(
    fixture_name: str,
    expected_file_format: str,
    expected_detected_format: str,
) -> None:
    if expected_file_format == "pdf" and importlib.util.find_spec("pypdf") is None:
        if os.getenv("CI"):
            pytest.fail("CI must install pypdf so PDF ingestion coverage does not skip")
        pytest.skip("pypdf is required for PDF fixture ingestion")

    workspace_root = Path(__file__).resolve().parents[2]
    fixture_path = workspace_root / "tests" / "fixtures" / "ingest_inputs" / fixture_name
    assert fixture_path.exists()

    engine = DriverEngine(workspace_root=workspace_root)
    run_id = f"integration-story-ingest-format-{expected_file_format}"
    state = engine.run(
        recipe_path=workspace_root / "configs" / "recipes" / "recipe-ingest-only.yaml",
        run_id=run_id,
        force=True,
        runtime_params={"input_file": str(fixture_path)},
    )
    assert state["stages"]["ingest"]["status"] == "done"

    artifact_ref = ArtifactRef.model_validate(state["stages"]["ingest"]["artifact_refs"][0])
    artifact = engine.store.load_artifact(artifact_ref)
    assert artifact.data["source_info"]["file_format"] == expected_file_format
    assert artifact.data["source_info"]["original_filename"] == fixture_name
    assert artifact.data["content"] or expected_file_format == "pdf"
    assert artifact.data["classification"]["detected_format"] == expected_detected_format
    assert artifact.data["classification"]["confidence"] >= 0.3
