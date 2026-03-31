from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from cine_forge.ai.fdx import ScreenplayExportResult
from cine_forge.api.app import create_app
from cine_forge.artifacts import ArtifactStore
from cine_forge.cli import handle_export
from cine_forge.export.call_sheet import build_call_sheet_document, generate_call_sheet_pdf
from cine_forge.export.interchange_fcpxml import (
    build_narrative_interchange_export,
    render_fcpxml,
)
from cine_forge.schemas import (
    ArtifactMetadata,
    ProjectConfig,
    Timeline,
    TimelineEntry,
    TrackEntry,
    TrackManifest,
)


def _metadata(intent: str) -> ArtifactMetadata:
    return ArtifactMetadata(
        lineage=[],
        intent=intent,
        rationale="unit test seed",
        confidence=1.0,
        source="code",
    )


def _seed_export_store(project_dir: Path) -> ArtifactStore:
    project_dir.mkdir(parents=True, exist_ok=True)
    store = ArtifactStore(project_dir=project_dir)

    scene_one = {
        "scene_id": "scene_001",
        "scene_number": 1,
        "heading": "INT. LAB - NIGHT",
        "location": "LAB",
        "time_of_day": "NIGHT",
        "int_ext": "INT",
        "characters_present": ["MARA", "OWEN"],
        "characters_present_ids": ["mara", "owen"],
        "props_mentioned": ["console"],
        "elements": [
            {"element_type": "action", "content": "Mara studies the unstable console."},
            {"element_type": "dialogue", "content": "We can still stop this."},
        ],
        "narrative_beats": [
            {
                "beat_type": "warning",
                "description": "Mara realizes the console is about to overload.",
                "approximate_location": "Opening exchange",
                "confidence": 0.95,
            },
            {
                "beat_type": "decision",
                "description": "Owen refuses to shut the system down.",
                "approximate_location": "End of scene",
                "confidence": 0.91,
            },
        ],
        "tone_mood": "tense",
        "tone_shifts": ["dread sharpens into open conflict"],
        "source_span": {"start_line": 1, "end_line": 8},
        "inferences": [],
        "provenance": [],
        "confidence": 1.0,
    }
    scene_two = {
        "scene_id": "scene_002",
        "scene_number": 2,
        "heading": "EXT. ROOF - DAWN",
        "location": "ROOF",
        "time_of_day": "DAWN",
        "int_ext": "EXT",
        "characters_present": ["MARA", "ELIAS"],
        "characters_present_ids": ["mara", "elias"],
        "props_mentioned": [],
        "elements": [
            {"element_type": "action", "content": "Wind tears at Mara's coat on the roof edge."},
            {"element_type": "dialogue", "content": "Tell me what it cost."},
        ],
        "narrative_beats": [
            {
                "beat_type": "reckoning",
                "description": "Elias forces Mara to face the fallout.",
                "approximate_location": "Mid-scene confrontation",
                "confidence": 0.93,
            }
        ],
        "tone_mood": "bleak",
        "tone_shifts": ["anger softens into regret"],
        "source_span": {"start_line": 10, "end_line": 15},
        "inferences": [],
        "provenance": [],
        "confidence": 1.0,
    }

    scene_one_ref = store.save_artifact(
        artifact_type="scene",
        entity_id="scene_001",
        data=scene_one,
        metadata=_metadata("seed scene_001"),
    )
    scene_two_ref = store.save_artifact(
        artifact_type="scene",
        entity_id="scene_002",
        data=scene_two,
        metadata=_metadata("seed scene_002"),
    )

    store.save_artifact(
        artifact_type="project_config",
        entity_id="project",
        data=ProjectConfig(
            title="Pressure Test",
            format="feature",
            genre=["thriller"],
            tone=["tense", "bleak"],
            estimated_duration_minutes=2.0,
            primary_characters=["mara"],
            supporting_characters=["owen", "elias"],
            location_count=2,
            locations_summary=["lab", "roof"],
            target_audience="adults",
            aspect_ratio="2.39:1",
            production_mode="hybrid",
            human_control_mode="checkpoint",
            style_packs={},
            budget_cap_usd=None,
            default_model="mock",
            confirmed=True,
        ).model_dump(mode="json"),
        metadata=_metadata("seed project config"),
    )

    timeline = Timeline(
        entries=[
            TimelineEntry(
                scene_id="scene_001",
                scene_ref=scene_one_ref,
                script_position=1,
                edit_position=1,
                story_position=2,
                estimated_duration_seconds=45.0,
                shot_count=0,
                shot_ids=[],
                story_order_confidence="high",
                story_order_rationale="Seed fixture.",
            ),
            TimelineEntry(
                scene_id="scene_002",
                scene_ref=scene_two_ref,
                script_position=2,
                edit_position=2,
                story_position=1,
                estimated_duration_seconds=30.0,
                shot_count=0,
                shot_ids=[],
                story_order_confidence="medium",
                story_order_rationale="Seed fixture.",
            ),
        ],
        total_scenes=2,
        estimated_runtime_seconds=75.0,
        chronology_source="scene_index_fallback",
    )
    timeline_ref = store.save_artifact(
        artifact_type="timeline",
        entity_id="project",
        data=timeline.model_dump(mode="json"),
        metadata=_metadata("seed timeline"),
    )

    manifest = TrackManifest(
        timeline_ref=timeline_ref,
        entries=[
            TrackEntry(
                track_type="script",
                scene_id="scene_001",
                artifact_ref=scene_one_ref,
                start_time_seconds=0.0,
                end_time_seconds=45.0,
                priority=400,
                status="available",
                notes="Seed script track.",
            ),
            TrackEntry(
                track_type="script",
                scene_id="scene_002",
                artifact_ref=scene_two_ref,
                start_time_seconds=45.0,
                end_time_seconds=75.0,
                priority=400,
                status="available",
                notes="Seed script track.",
            ),
        ],
        track_fill_counts={"script": 2},
    )
    store.save_artifact(
        artifact_type="track_manifest",
        entity_id="project",
        data=manifest.model_dump(mode="json"),
        metadata=_metadata("seed track manifest"),
    )

    store.save_artifact(
        artifact_type="canonical_script",
        entity_id="project",
        data={
            "script_text": (
                "Title Page\n"
                "INT. LAB - NIGHT\n"
                "Mara studies the unstable console.\n"
                "EXT. ROOF - DAWN\n"
                "Wind tears at Mara's coat.\n"
            )
        },
        metadata=_metadata("seed canonical script"),
    )

    return store


@pytest.mark.unit
def test_build_narrative_interchange_export_contains_scene_boundaries_beats_and_character_changes(
    tmp_path: Path,
) -> None:
    store = _seed_export_store(tmp_path / "project")

    payload = build_narrative_interchange_export(
        store,
        project_id="pressure-test",
        project_title="Pressure Test",
    )

    assert [scene.scene_number for scene in payload.scenes] == [1, 2]
    assert payload.track_manifest_ref is not None
    assert payload.total_duration_seconds == pytest.approx(75.0)

    labels = {annotation.label for annotation in payload.annotations}
    assert "Scene 1" in labels
    assert "Beat: warning" in labels
    assert "Beat: decision" in labels
    assert "Entrance: ELIAS" in labels
    assert "Exit: OWEN" in labels
    assert any(annotation.kind == "emotional_note" for annotation in payload.annotations)


@pytest.mark.unit
def test_render_fcpxml_contains_gap_sequence_and_marker_notes(tmp_path: Path) -> None:
    store = _seed_export_store(tmp_path / "project")
    payload = build_narrative_interchange_export(
        store,
        project_id="pressure-test",
        project_title="Pressure Test",
    )

    xml_text = render_fcpxml(payload)
    assert xml_text.startswith("<?xml")

    root = ET.fromstring(xml_text)
    assert root.tag == "fcpxml"
    gaps = root.findall(".//gap")
    assert len(gaps) == 2
    markers = root.findall(".//marker")
    assert len(markers) >= 6
    marker_values = {marker.attrib["value"] for marker in markers}
    assert "Scene 1" in marker_values
    assert "Entrance: ELIAS" in marker_values
    assert "Exit: OWEN" in marker_values
    assert any("Color label" in marker.attrib.get("note", "") for marker in markers)


@pytest.mark.unit
def test_build_call_sheet_document_marks_missing_logistics_honestly_and_pdf_smokes(
    tmp_path: Path,
) -> None:
    store = _seed_export_store(tmp_path / "project")
    scenes = [
        store.load_artifact(ref).data
        for ref in store.list_versions("scene", "scene_001")
    ]
    scenes.extend(
        store.load_artifact(ref).data
        for ref in store.list_versions("scene", "scene_002")
    )

    document = build_call_sheet_document(
        project_name="Pressure Test",
        scenes=scenes,
    )

    assert document.logistics[0].value == "Not specified in CineForge project data"
    assert "Planning-only call sheet" in document.draft_note
    assert any(row.character_name == "ELIAS" for row in document.cast)
    assert any(
        "Mara realizes the console is about to overload." in row.summary
        for row in document.schedule
    )

    pdf_path = tmp_path / "call-sheet.pdf"
    generate_call_sheet_pdf(
        project_name="Pressure Test",
        scenes=scenes,
        output_path=str(pdf_path),
    )
    assert pdf_path.exists()
    assert pdf_path.read_bytes().startswith(b"%PDF")


@pytest.mark.unit
def test_export_routes_return_fcpxml_and_call_sheet_files(tmp_path: Path) -> None:
    app = create_app(workspace_root=tmp_path)
    client = TestClient(app)
    project_path = tmp_path / "output" / "export-project"

    response = client.post("/api/projects/new", json={"project_path": str(project_path)})
    assert response.status_code == 200
    project_id = response.json()["project_id"]

    _seed_export_store(project_path)

    fcpxml_response = client.get(f"/api/projects/{project_id}/export/fcpxml")
    assert fcpxml_response.status_code == 200
    assert "application/xml" in fcpxml_response.headers["content-type"]
    fcpxml_root = ET.fromstring(fcpxml_response.text)
    assert fcpxml_root.tag == "fcpxml"

    pdf_response = client.get(f"/api/projects/{project_id}/export/pdf?layout=call-sheet")
    assert pdf_response.status_code == 200
    assert pdf_response.headers["content-type"] == "application/pdf"
    assert pdf_response.content.startswith(b"%PDF")


@pytest.mark.unit
def test_screenplay_pdf_export_falls_back_to_uploaded_input_before_breakdown(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = create_app(workspace_root=tmp_path)
    client = TestClient(app)
    project_path = tmp_path / "output" / "raw-script-project"

    response = client.post("/api/projects/new", json={"project_path": str(project_path)})
    assert response.status_code == 200
    project_id = response.json()["project_id"]

    inputs_dir = project_path / "inputs"
    inputs_dir.mkdir(parents=True, exist_ok=True)
    (inputs_dir / "11111111_raw-script.fountain").write_text(
        "INT. DOCK - NIGHT\n\nTHE MARINER\nThe tide is turning.\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "cine_forge.ai.fdx.export_screenplay_text",
        lambda screenplay_text, export_format: ScreenplayExportResult(
            export_format=export_format,
            success=True,
            backend="test-fixture",
            content=b"%PDF-1.4 screenplay-fixture",
            issues=[],
        ),
    )

    pdf_response = client.get(
        f"/api/projects/{project_id}/export/pdf?layout=screenplay&include=script"
    )
    assert pdf_response.status_code == 200
    assert pdf_response.headers["content-type"] == "application/pdf"
    assert pdf_response.content.startswith(b"%PDF-1.4 screenplay-fixture")


@pytest.mark.unit
def test_report_and_call_sheet_exports_require_breakdown_artifacts(tmp_path: Path) -> None:
    app = create_app(workspace_root=tmp_path)
    client = TestClient(app)
    project_path = tmp_path / "output" / "empty-export-project"

    response = client.post("/api/projects/new", json={"project_path": str(project_path)})
    assert response.status_code == 200
    project_id = response.json()["project_id"]

    inputs_dir = project_path / "inputs"
    inputs_dir.mkdir(parents=True, exist_ok=True)
    (inputs_dir / "22222222_script.fountain").write_text(
        "INT. CABIN - NIGHT\n\nMARA\nWe are not ready.\n",
        encoding="utf-8",
    )

    report_response = client.get(f"/api/projects/{project_id}/export/pdf?layout=report")
    assert report_response.status_code == 409
    report_payload = report_response.json()
    assert "Run basic breakdown first" in (
        report_payload.get("detail") or report_payload.get("message") or ""
    )

    call_sheet_response = client.get(f"/api/projects/{project_id}/export/pdf?layout=call-sheet")
    assert call_sheet_response.status_code == 409
    call_sheet_payload = call_sheet_response.json()
    assert "Run basic breakdown first" in (
        call_sheet_payload.get("detail") or call_sheet_payload.get("message") or ""
    )


@pytest.mark.unit
def test_cli_handle_export_writes_fcpxml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project_id = "cli-export-project"
    project_path = tmp_path / "output" / project_id
    _seed_export_store(project_path)
    monkeypatch.chdir(tmp_path)

    out_path = tmp_path / "exports" / "timeline.fcpxml"
    handle_export(
        SimpleNamespace(
            project=project_id,
            format="fcpxml",
            scope="everything",
            layout="report",
            out=str(out_path),
        )
    )

    assert out_path.exists()
    root = ET.fromstring(out_path.read_text(encoding="utf-8"))
    assert root.tag == "fcpxml"
    assert len(root.findall(".//marker")) >= 6
