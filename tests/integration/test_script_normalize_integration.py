from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest

from cine_forge.ai.fountain_parser import validate_fountain_structure
from cine_forge.driver.engine import DriverEngine
from cine_forge.modules.ingest.script_normalize_v1.main import run_module
from cine_forge.schemas import ArtifactRef


@pytest.mark.integration
def test_ingest_and_normalize_recipe_persists_canonical_script() -> None:
    workspace_root = Path(__file__).resolve().parents[2]
    engine = DriverEngine(workspace_root=workspace_root)
    state = engine.run(
        recipe_path=workspace_root / "configs" / "recipes" / "recipe-ingest-normalize.yaml",
        run_id="integration-script-normalize",
        force=True,
        runtime_params={"input_file": str(workspace_root / "samples" / "sample-prose.txt")},
    )

    assert state["stages"]["ingest"]["status"] == "done"
    assert state["stages"]["normalize"]["status"] == "done"
    assert state["total_cost_usd"] >= 0.0

    canonical_ref = ArtifactRef.model_validate(state["stages"]["normalize"]["artifact_refs"][0])
    canonical = engine.store.load_artifact(canonical_ref)

    assert canonical.data["script_text"]
    assert canonical.data["normalization"]["strategy"] in {"passthrough_cleanup", "full_conversion"}
    assert canonical.metadata.lineage
    assert canonical.metadata.lineage[0].artifact_type == "raw_input"
    assert canonical.metadata.cost_data is not None
    assert canonical.metadata.annotations["qa_result"]["passed"] is True


def _fixture_raw_input(
    fixture_name: str,
    detected_format: str,
    confidence: float,
    file_format: str,
) -> dict[str, object]:
    workspace_root = Path(__file__).resolve().parents[2]
    fixture_path = workspace_root / "tests" / "fixtures" / "normalize_inputs" / fixture_name
    content = fixture_path.read_text(encoding="utf-8")
    return {
        "content": content,
        "source_info": {
            "original_filename": fixture_path.name,
            "file_size_bytes": fixture_path.stat().st_size,
            "character_count": len(content),
            "line_count": content.count("\n") + 1,
            "file_format": file_format,
        },
        "classification": {
            "detected_format": detected_format,
            "confidence": confidence,
            "evidence": ["fixture"],
        },
    }


@pytest.mark.integration
def test_normalization_valid_screenplay_fixture_emits_parseable_output() -> None:
    result = run_module(
        inputs={
            "ingest": _fixture_raw_input(
                fixture_name="valid_screenplay.fountain",
                detected_format="screenplay",
                confidence=0.95,
                file_format="fountain",
            )
        },
        params={"model": "mock", "qa_model": "mock", "skip_qa": False},
        context={"run_id": "integration-fixture-valid", "stage_id": "normalize"},
    )
    script_text = result["artifacts"][0]["data"]["script_text"]
    assert validate_fountain_structure(script_text).parseable is True


@pytest.mark.integration
def test_normalization_malformed_screenplay_fixture_emits_parseable_output() -> None:
    result = run_module(
        inputs={
            "ingest": _fixture_raw_input(
                fixture_name="malformed_screenplay.txt",
                detected_format="screenplay",
                confidence=0.2,
                file_format="txt",
            )
        },
        params={"model": "mock", "qa_model": "mock", "skip_qa": False},
        context={"run_id": "integration-fixture-malformed", "stage_id": "normalize"},
    )
    script_text = result["artifacts"][0]["data"]["script_text"]
    assert validate_fountain_structure(script_text).parseable is True


@pytest.mark.integration
def test_normalization_fdx_fixture_detects_interop_and_emits_parseable_output() -> None:
    result = run_module(
        inputs={
            "ingest": _fixture_raw_input(
                fixture_name="sample_script.fdx",
                detected_format="unknown",
                confidence=0.1,
                file_format="fdx",
            )
        },
        params={
            "model": "mock",
            "qa_model": "mock",
            "skip_qa": False,
            "export_formats": ["fdx"],
        },
        context={"run_id": "integration-fixture-fdx", "stage_id": "normalize"},
    )
    artifact = result["artifacts"][0]
    assert artifact["metadata"]["annotations"]["fdx_input_detected"] is True
    assert artifact["metadata"]["annotations"]["interop_exports"][0]["success"] is True
    script_text = artifact["data"]["script_text"]
    assert validate_fountain_structure(script_text).parseable is True


@pytest.mark.integration
def test_normalization_live_llm_short_sample() -> None:
    if os.getenv("CINE_FORGE_LIVE_TESTS") != "1":
        pytest.skip("Set CINE_FORGE_LIVE_TESTS=1 to run live normalization integration test")
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY is required for live normalization integration test")

    live_model = os.getenv("CINE_FORGE_LIVE_MODEL", "gpt-4o-mini")
    input_payload = {
        "content": "Mara enters the lab and whispers that the storm has arrived.",
        "source_info": {
            "original_filename": "live-short-sample.txt",
            "file_size_bytes": 62,
            "character_count": 62,
            "line_count": 1,
            "file_format": "txt",
        },
        "classification": {
            "detected_format": "prose",
            "confidence": 0.9,
            "evidence": ["live integration test input"],
        },
    }

    result = run_module(
        inputs={"ingest": input_payload},
        params={
            "model": live_model,
            "skip_qa": True,
            "max_retries": 1,
            "max_tokens": 1200,
            "cost_ceiling_usd": 1.0,
        },
        context={"run_id": "integration-live-normalize", "stage_id": "normalize"},
    )

    artifact = result["artifacts"][0]
    script_text = artifact["data"]["script_text"]
    parser_check = validate_fountain_structure(script_text)

    assert script_text
    assert parser_check.parseable is True
    assert result["cost"]["estimated_cost_usd"] >= 0.0


@pytest.mark.integration
def test_normalization_pdf_export_with_screenplain_optional() -> None:
    if os.getenv("CINE_FORGE_PDF_EXPORT_TESTS") != "1":
        pytest.skip("Set CINE_FORGE_PDF_EXPORT_TESTS=1 to run PDF export integration test")
    if not shutil.which("screenplain"):
        pytest.skip("screenplain CLI is required for PDF export integration test")

    result = run_module(
        inputs={
            "ingest": _fixture_raw_input(
                fixture_name="valid_screenplay.fountain",
                detected_format="screenplay",
                confidence=0.95,
                file_format="fountain",
            )
        },
        params={
            "model": "mock",
            "qa_model": "mock",
            "skip_qa": True,
            "export_formats": ["pdf"],
        },
        context={"run_id": "integration-fixture-pdf-export", "stage_id": "normalize"},
    )

    exports = result["artifacts"][0]["metadata"]["annotations"]["interop_exports"]
    pdf_export = next(item for item in exports if item["format"] == "pdf")
    assert pdf_export["success"] is True
    assert pdf_export["backend"] == "screenplain-cli"
    assert pdf_export["byte_count"] > 0
