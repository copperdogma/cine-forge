from __future__ import annotations

import json
import os
import uuid
from pathlib import Path

import pytest

from cine_forge.driver.engine import DriverEngine
from cine_forge.schemas import ArtifactHealth, ArtifactRef


def _assert_fixture_bundle_valid(fixture_root: Path) -> None:
    required_text = [
        fixture_root / "normalization_screenplay_cleanup.txt",
        fixture_root / "normalization_prose_conversion.txt",
        fixture_root / "normalization_qa.json",
        fixture_root / "project_config_autodetect.json",
    ]
    for path in required_text:
        assert path.exists(), f"Missing fixture file: {path}"
        assert path.read_text(encoding="utf-8").strip(), f"Empty fixture file: {path}"

    qa_scene_ids = sorted(
        path.stem.replace("_qa", "")
        for path in (fixture_root / "qa").glob("*_qa.json")
    )
    scene_scene_ids = sorted(path.stem for path in (fixture_root / "scenes").glob("scene_*.json"))
    assert len(qa_scene_ids) >= 5, "Expected at least five scene QA fixtures"
    assert qa_scene_ids == scene_scene_ids, "Scene and scene-QA fixture sets must match"

    scene_ids = qa_scene_ids
    for scene_id in scene_ids:
        qa_path = fixture_root / "qa" / f"{scene_id}_qa.json"
        scene_path = fixture_root / "scenes" / f"{scene_id}.json"
        assert qa_path.exists(), f"Missing scene QA fixture: {qa_path}"
        assert scene_path.exists(), f"Missing scene fixture: {scene_path}"
        assert qa_path.read_text(encoding="utf-8").strip(), f"Empty scene QA fixture: {qa_path}"
        assert scene_path.read_text(encoding="utf-8").strip(), f"Empty scene fixture: {scene_path}"
        json.loads(qa_path.read_text(encoding="utf-8"))
        json.loads(scene_path.read_text(encoding="utf-8"))


def _run_mvp_recipe(
    workspace_root: Path,
    *,
    run_id: str,
    input_file: Path,
    default_model: str,
    qa_model: str,
    project_dir: Path,
) -> tuple[DriverEngine, dict]:
    engine = DriverEngine(workspace_root=workspace_root, project_dir=project_dir)
    state = engine.run(
        recipe_path=workspace_root / "configs" / "recipes" / "recipe-mvp-ingest.yaml",
        run_id=run_id,
        force=True,
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
    assert canonical.metadata.annotations["qa_result"]["passed"] is True
    assert canonical.metadata.cost_data is not None
    assert canonical.metadata.cost_data.estimated_cost_usd >= 0.0
    normalize_call_models = {
        item["model"] for item in canonical.metadata.annotations["normalization_call_costs"]
    }
    assert normalize_call_models == {"fixture"}

    for scene_ref in scene_refs:
        scene_artifact = engine.store.load_artifact(scene_ref)
        lineage_types = {ref.artifact_type for ref in scene_artifact.metadata.lineage}
        assert "canonical_script" in lineage_types
        assert scene_artifact.metadata.annotations["qa_result"]["passed"] is True
        assert "Mock structured extraction fixture" in scene_artifact.metadata.annotations[
            "qa_result"
        ]["summary"]
        assert scene_artifact.metadata.cost_data is not None

    scene_index = engine.store.load_artifact(scene_index_ref)
    scene_index_lineage = {ref.artifact_type for ref in scene_index.metadata.lineage}
    assert "canonical_script" in scene_index_lineage
    assert "scene" in scene_index_lineage

    project_config = engine.store.load_artifact(project_config_ref)
    config_lineage = {ref.artifact_type for ref in project_config.metadata.lineage}
    assert "canonical_script" in config_lineage
    assert "scene_index" in config_lineage
    assert project_config.data["confirmed"] is True
    assert project_config.metadata.cost_data is not None

    run_dir = workspace_root / "output" / "runs" / run_id
    run_state_path = run_dir / "run_state.json"
    events_path = run_dir / "pipeline_events.jsonl"
    assert run_state_path.exists()
    assert events_path.exists()

    run_state_data = json.loads(run_state_path.read_text(encoding="utf-8"))
    assert run_state_data["total_cost_usd"] >= 0.0
    assert run_state_data["stages"]["project_config"]["status"] == "done"

    events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines()]
    started = [item for item in events if item["event"] == "stage_started"]
    finished = [item for item in events if item["event"] == "stage_finished"]
    assert len(started) == 4
    assert len(finished) == 4


@pytest.mark.integration
def test_mvp_recipe_live_end_to_end_gated() -> None:
    if os.getenv("CINE_FORGE_LIVE_TESTS") != "1":
        pytest.skip("Set CINE_FORGE_LIVE_TESTS=1 to run the live MVP smoke test")
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY is required for the live MVP smoke test")

    workspace_root = Path(__file__).resolve().parents[2]
    run_id = f"smoke-mvp-live-{uuid.uuid4().hex[:8]}"
    model = os.getenv("CINE_FORGE_LIVE_MODEL", "gpt-4o-mini")
    qa_model = os.getenv("CINE_FORGE_LIVE_QA_MODEL", "gpt-4o-mini")
    input_file = workspace_root / "tests" / "fixtures" / "sample_screenplay.fountain"
    project_dir = workspace_root / "output" / "project_smoke_mvp_live"

    engine, state = _run_mvp_recipe(
        workspace_root=workspace_root,
        run_id=run_id,
        input_file=input_file,
        default_model=model,
        qa_model=qa_model,
        project_dir=project_dir,
    )

    assert state["stages"]["project_config"]["status"] == "done"
    assert state["total_cost_usd"] >= 0.0
    assert len(state["stages"]["extract_scenes"]["artifact_refs"]) >= 2
    print(f"Live MVP total_cost_usd={state['total_cost_usd']:.6f}")

    project_config_ref = ArtifactRef.model_validate(
        state["stages"]["project_config"]["artifact_refs"][0]
    )
    project_config = engine.store.load_artifact(project_config_ref)
    assert project_config.data["confirmed"] is True
    assert project_config.data["genre"]
    assert project_config.data["tone"]


@pytest.mark.integration
def test_mvp_staleness_propagation_after_new_raw_input_version() -> None:
    workspace_root = Path(__file__).resolve().parents[2]
    run_id = f"smoke-mvp-stale-{uuid.uuid4().hex[:8]}"
    project_dir = workspace_root / "output" / "project_smoke_mvp_stale"

    fixture_v1 = workspace_root / "tests" / "fixtures" / "sample_screenplay.fountain"
    fixture_v2 = project_dir / "sample_screenplay_variant.fountain"
    fixture_v2.parent.mkdir(parents=True, exist_ok=True)
    fixture_v2.write_text(
        fixture_v1.read_text(encoding="utf-8") + "\n\n# Added line for staleness check.\n",
        encoding="utf-8",
    )

    engine, state_v1 = _run_mvp_recipe(
        workspace_root=workspace_root,
        run_id=f"{run_id}-v1",
        input_file=fixture_v1,
        default_model="mock",
        qa_model="mock",
        project_dir=project_dir,
    )

    canonical_v1 = ArtifactRef.model_validate(state_v1["stages"]["normalize"]["artifact_refs"][0])
    extract_refs_v1 = [
        ArtifactRef.model_validate(item)
        for item in state_v1["stages"]["extract_scenes"]["artifact_refs"]
    ]
    scene_index_v1 = next(ref for ref in extract_refs_v1 if ref.artifact_type == "scene_index")
    project_config_v1 = ArtifactRef.model_validate(
        state_v1["stages"]["project_config"]["artifact_refs"][0]
    )

    engine.run(
        recipe_path=workspace_root / "configs" / "recipes" / "recipe-ingest-only.yaml",
        run_id=f"{run_id}-ingest-v2",
        force=True,
        runtime_params={"input_file": str(fixture_v2)},
    )

    stale_refs = engine.store.graph.get_stale()
    stale_keys = {ref.key() for ref in stale_refs}
    assert canonical_v1.key() in stale_keys
    assert scene_index_v1.key() in stale_keys
    assert project_config_v1.key() in stale_keys
    assert any(ref.artifact_type == "scene" for ref in stale_refs)

    _, state_v2 = _run_mvp_recipe(
        workspace_root=workspace_root,
        run_id=f"{run_id}-v2",
        input_file=fixture_v2,
        default_model="mock",
        qa_model="mock",
        project_dir=project_dir,
    )
    canonical_v2 = ArtifactRef.model_validate(state_v2["stages"]["normalize"]["artifact_refs"][0])
    assert canonical_v2.version > canonical_v1.version
    assert engine.store.graph.get_health(canonical_v2) == ArtifactHealth.VALID


@pytest.mark.integration
def test_mvp_recipe_handles_tokenized_pdf_screenplay_without_placeholder_fallback(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    workspace_root = Path(__file__).resolve().parents[2]
    run_id = f"smoke-mvp-tokenized-{uuid.uuid4().hex[:8]}"
    project_dir = tmp_path / "project_tokenized_pdf"
    input_file = tmp_path / "tokenized_input.pdf"
    input_file.write_bytes(b"%PDF-1.4 tokenized fixture")

    tokenized_pdf_text = "\n".join(
        [
            "FADE",
            "IN:",
            "EXT.",
            "CITY",
            "CENTRE",
            "-",
            "NIGHT",
            "A",
            "ruined",
            "city",
            "THE",
            "MARINER",
            "charges",
            "in",
            "CUT",
            "TO:",
            "EXT.",
            "RUDDY",
            "&",
            "GREENE",
            "BUILDING",
            "-",
            "FRONT",
            "-",
            "NIGHT",
            "Gunshots",
            "echo",
        ]
        * 5
    )
    class _FakePage:
        def extract_text(self) -> str:
            return tokenized_pdf_text

    class _FakePdfReader:
        def __init__(self, _: str) -> None:
            self.pages = [_FakePage()]

    monkeypatch.setattr("pypdf.PdfReader", _FakePdfReader)

    engine, state = _run_mvp_recipe(
        workspace_root=workspace_root,
        run_id=run_id,
        input_file=input_file,
        default_model="mock",
        qa_model="mock",
        project_dir=project_dir,
    )

    assert state["stages"]["project_config"]["status"] == "done"

    canonical_ref = ArtifactRef.model_validate(state["stages"]["normalize"]["artifact_refs"][0])
    canonical = engine.store.load_artifact(canonical_ref)
    assert "UNKNOWN LOCATION" not in canonical.data["script_text"]

    extract_refs = [
        ArtifactRef.model_validate(item)
        for item in state["stages"]["extract_scenes"]["artifact_refs"]
    ]
    scene_index_ref = next(ref for ref in extract_refs if ref.artifact_type == "scene_index")
    scene_index = engine.store.load_artifact(scene_index_ref)

    assert scene_index.data["total_scenes"] >= 2
    assert "Unknown Location" not in scene_index.data["unique_locations"]


@pytest.mark.integration
def test_mvp_recipe_handles_compact_pdf_scene_headings_without_placeholder_fallback(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    workspace_root = Path(__file__).resolve().parents[2]
    run_id = f"smoke-mvp-compact-{uuid.uuid4().hex[:8]}"
    project_dir = tmp_path / "project_compact_pdf"
    input_file = tmp_path / "compact_input.pdf"
    input_file.write_bytes(b"%PDF-1.4 compact fixture")

    compact_pdf_text = "\n".join(
        [
            "EXT.CITYCENTRE- NIGHT",
            "A ruined city.",
            "EXT.RUDDY& GREENEBUILDING- FRONT- NIGHT",
            "Cars idle outside.",
            "INT.RUDDY& GREENBUILDING- ELEVATOR",
            "ROSE",
            "Where are we?",
            "INT.11THFLOOR- CONTINUOUS",
            "MARINER",
            "Move.",
        ]
    )

    class _FakePage:
        def extract_text(self) -> str:
            return compact_pdf_text

    class _FakePdfReader:
        def __init__(self, _: str) -> None:
            self.pages = [_FakePage()]

    monkeypatch.setattr("pypdf.PdfReader", _FakePdfReader)

    engine, state = _run_mvp_recipe(
        workspace_root=workspace_root,
        run_id=run_id,
        input_file=input_file,
        default_model="mock",
        qa_model="mock",
        project_dir=project_dir,
    )

    ingest_ref = ArtifactRef.model_validate(state["stages"]["ingest"]["artifact_refs"][0])
    canonical_ref = ArtifactRef.model_validate(state["stages"]["normalize"]["artifact_refs"][0])
    extract_refs = [
        ArtifactRef.model_validate(item)
        for item in state["stages"]["extract_scenes"]["artifact_refs"]
    ]
    scene_index_ref = next(ref for ref in extract_refs if ref.artifact_type == "scene_index")

    raw = engine.store.load_artifact(ingest_ref)
    canonical = engine.store.load_artifact(canonical_ref)
    scene_index = engine.store.load_artifact(scene_index_ref)

    assert raw.data["classification"]["detected_format"] == "screenplay"
    assert "UNKNOWN LOCATION" not in canonical.data["script_text"]
    assert scene_index.data["total_scenes"] >= 3
    assert "Unknown Location" not in scene_index.data["unique_locations"]


@pytest.mark.integration
def test_mvp_recipe_handles_docx_screenplay(tmp_path: Path) -> None:
    workspace_root = Path(__file__).resolve().parents[2]
    run_id = f"smoke-mvp-docx-{uuid.uuid4().hex[:8]}"
    project_dir = tmp_path / "project_docx"
    input_file = workspace_root / "tests" / "fixtures" / "ingest_inputs" / "the_signal.docx"
    
    engine, state = _run_mvp_recipe(
        workspace_root=workspace_root,
        run_id=run_id,
        input_file=input_file,
        default_model="mock",
        qa_model="mock",
        project_dir=project_dir,
    )

    assert state["stages"]["project_config"]["status"] == "done"
    
    ingest_ref = ArtifactRef.model_validate(state["stages"]["ingest"]["artifact_refs"][0])
    raw = engine.store.load_artifact(ingest_ref)
    assert raw.data["classification"]["detected_format"] == "screenplay"
    assert raw.data["source_info"]["file_format"] == "docx"
    assert "INT. COMMUNITY RADIO STUDIO" in raw.data["content"]
