from __future__ import annotations

import importlib.util
import os
import re
from pathlib import Path

import pytest

from cine_forge.driver.engine import DriverEngine
from cine_forge.schemas import ArtifactRef


@pytest.mark.integration
def test_story_ingest_recipe_persists_raw_input_and_versions() -> None:
    workspace_root = Path(__file__).resolve().parents[2]
    engine = DriverEngine(workspace_root=workspace_root)
    recipe_path = workspace_root / "tests" / "fixtures" / "recipes" / "recipe-ingest-only.yaml"

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
    ("fixture_name", "expected_file_format", "expected_detected_format", "min_confidence"),
    [
        ("owl_creek_bridge.txt", "txt", "prose", 0.3),
        ("owl_creek_bridge_excerpt.md", "md", "prose", 0.3),
        ("run_like_hell_teaser.fountain", "fountain", "screenplay", 0.3),
        ("pit_and_pendulum.pdf", "pdf", "prose", 0.3),
        ("patent_registering_votes_us272011_scan_5p.pdf", "pdf", "prose", 0.3),
        ("run_like_hell_teaser_scanned_5p.pdf", "pdf", "screenplay", 0.3),
        ("sample_script.fdx", "fdx", "screenplay", 0.3),
        ("sample_script.docx", "docx", "screenplay", 0.3),
    ],
)
def test_story_ingest_supports_all_fixture_formats(
    fixture_name: str,
    expected_file_format: str,
    expected_detected_format: str,
    min_confidence: float,
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
        recipe_path=workspace_root / "tests" / "fixtures" / "recipes" / "recipe-ingest-only.yaml",
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
    assert artifact.data["classification"]["confidence"] >= min_confidence


@pytest.mark.integration
@pytest.mark.parametrize(
    ("fixture_name", "expected_file_format"),
    [
        ("owl_creek_bridge.txt", "txt"),
        ("owl_creek_bridge_excerpt.md", "md"),
        ("run_like_hell_teaser.fountain", "fountain"),
        ("pit_and_pendulum.pdf", "pdf"),
        ("patent_registering_votes_us272011_scan_5p.pdf", "pdf"),
        ("run_like_hell_teaser_scanned_5p.pdf", "pdf"),
        ("sample_script.fdx", "fdx"),
        ("sample_script.docx", "docx"),
    ],
)
def test_ingest_normalize_handles_all_supported_formats_semantically(
    fixture_name: str,
    expected_file_format: str,
) -> None:
    if expected_file_format == "pdf" and importlib.util.find_spec("pypdf") is None:
        if os.getenv("CI"):
            pytest.fail("CI must install pypdf so PDF ingest+normalize coverage does not skip")
        pytest.skip("pypdf is required for PDF fixture ingestion")

    workspace_root = Path(__file__).resolve().parents[2]
    fixture_path = workspace_root / "tests" / "fixtures" / "ingest_inputs" / fixture_name
    assert fixture_path.exists()

    engine = DriverEngine(workspace_root=workspace_root)
    run_id = f"integration-ingest-normalize-{expected_file_format}"
    state = engine.run(
        recipe_path=(
            workspace_root / "tests" / "fixtures" / "recipes" / "recipe-ingest-normalize.yaml"
        ),
        run_id=run_id,
        force=True,
        runtime_params={"input_file": str(fixture_path)},
    )
    assert state["stages"]["ingest"]["status"] == "done"
    assert state["stages"]["normalize"]["status"] == "done"

    ingest_ref = ArtifactRef.model_validate(state["stages"]["ingest"]["artifact_refs"][0])
    normalize_ref = ArtifactRef.model_validate(state["stages"]["normalize"]["artifact_refs"][0])
    raw_artifact = engine.store.load_artifact(ingest_ref)
    canonical_artifact = engine.store.load_artifact(normalize_ref)

    assert raw_artifact.data["source_info"]["file_format"] == expected_file_format
    raw_text = raw_artifact.data["content"]
    assert isinstance(raw_text, str)
    assert len(raw_text.strip()) > 0
    assert "\x00" not in raw_text

    # Semantic extraction sanity: ensure we retained multiple normal word boundaries.
    raw_word_gap_count = len(re.findall(r"\b[A-Za-z]{3,}\s+[A-Za-z]{3,}\b", raw_text))
    min_raw_gaps = 3 if expected_file_format in {"docx", "fdx"} else 5
    assert raw_word_gap_count >= min_raw_gaps

    canonical_script = canonical_artifact.data.get("script_text", "")
    assert isinstance(canonical_script, str)
    assert "\x00" not in canonical_script

    # Some prose inputs are intentionally rejected to empty canonical script.
    # When script text exists, require baseline semantic readability.
    if canonical_script.strip():
        canonical_word_gaps = len(
            re.findall(r"\b[A-Za-z]{3,}\s+[A-Za-z]{3,}\b", canonical_script)
        )
        assert canonical_word_gaps >= 3

    if fixture_name == "run_like_hell_teaser_scanned_5p.pdf":
        extraction_diagnostics = (
            raw_artifact.metadata.annotations or {}
        ).get("extraction_diagnostics", {})
        assert extraction_diagnostics.get("pdf_extractor_selected") == "ocrmypdf"
