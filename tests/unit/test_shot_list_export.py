from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from cine_forge.api.app import create_app
from cine_forge.artifacts import ArtifactStore
from cine_forge.export.shot_list import (
    generate_shot_list_pdf,
    load_shot_plans,
    render_shot_list_csv,
)
from cine_forge.schemas import (
    ArtifactMetadata,
    ArtifactRef,
    CoverageAdequacyCheck,
    CoverageStrategy,
    PlanningAudit,
    ProjectConfig,
    ShotDefinition,
    ShotPlan,
)


def _metadata(intent: str) -> ArtifactMetadata:
    return ArtifactMetadata(
        lineage=[],
        intent=intent,
        rationale="unit test seed",
        confidence=1.0,
        source="code",
    )


def _scene_ref(scene_id: str) -> ArtifactRef:
    return ArtifactRef(
        artifact_type="scene",
        entity_id=scene_id,
        version=1,
        path=f"artifacts/scene/{scene_id}/v1.json",
    )


def _audit(intent: str) -> PlanningAudit:
    return PlanningAudit(
        intent=intent,
        rationale="Shot list export fixture.",
        alternatives_considered=[],
        confidence=0.9,
        source="code",
    )


def _build_plan(scene_id: str, scene_number: int, heading: str) -> ShotPlan:
    return ShotPlan(
        scene_id=scene_id,
        scene_number=scene_number,
        scene_heading=heading,
        scene_ref=_scene_ref(scene_id),
        coverage_strategy=CoverageStrategy(
            coverage_approach="Master plus selective inserts.",
            rhythm_and_flow_intent="Hold, then tighten.",
            look_and_feel_intent="Hard practical contrast.",
            sound_and_music_intent="Sparse room tone with no score.",
            character_and_performance_notes="Play restraint until the cutaway lands.",
            coverage_patterns=["Master", "Insert"],
            adequacy_check=CoverageAdequacyCheck(
                verdict="adequate",
                rationale="The editor has the geography and the detail beat.",
            ),
            audit=_audit("Scene coverage strategy"),
        ),
        shots=[
            ShotDefinition(
                scene_id=scene_id,
                shot_id=f"S{scene_number:03d}-A",
                shot_size="Wide Master",
                camera_angle="Eye level",
                camera_movement="Static",
                lens_focal_length="Normal (40-60mm)",
                coverage_role="Master",
                characters_in_frame=["MARA", "OWEN"],
                blocking="Hold both performers across the table.",
                action_description="Play the exchange as a complete safety setup.",
                dialogue_lines=["We can still stop this.", "No. We let it run."],
                duration_estimate_seconds=12.0,
                edit_intent="Editorial safety net and geography anchor.",
                continuity_state_refs=[],
                upstream_artifact_refs=[_scene_ref(scene_id)],
                audit=_audit("Editorial safety net and geography anchor."),
            ),
            ShotDefinition(
                scene_id=scene_id,
                shot_id=f"S{scene_number:03d}-B",
                shot_size="Insert",
                camera_angle="High",
                camera_movement="Static",
                lens_focal_length="Wide (18-35mm)",
                coverage_role="Insert",
                characters_in_frame=[],
                blocking="Frame the switch and Mara's hand.",
                action_description="Catch the key action detail on the console.",
                dialogue_lines=[],
                duration_estimate_seconds=3.0,
                edit_intent="Give the cut a decisive detail insert.",
                continuity_state_refs=[],
                upstream_artifact_refs=[_scene_ref(scene_id)],
                audit=_audit("Give the cut a decisive detail insert."),
            ),
        ],
        total_estimated_duration_seconds=15.0,
    )


def _seed_shot_plan_store(project_dir: Path) -> ArtifactStore:
    project_dir.mkdir(parents=True, exist_ok=True)
    store = ArtifactStore(project_dir=project_dir)
    plan_two = _build_plan("scene_002", 2, "EXT. ROOF - DAWN")
    plan_one = _build_plan("scene_001", 1, "INT. LAB - NIGHT")
    store.save_artifact(
        artifact_type="shot_plan",
        entity_id=plan_two.scene_id,
        data=plan_two.model_dump(mode="json"),
        metadata=_metadata("seed scene_002 shot plan"),
    )
    store.save_artifact(
        artifact_type="shot_plan",
        entity_id=plan_one.scene_id,
        data=plan_one.model_dump(mode="json"),
        metadata=_metadata("seed scene_001 shot plan"),
    )
    store.save_artifact(
        artifact_type="project_config",
        entity_id="project",
        data=ProjectConfig(
            title="Pressure Test",
            format="feature",
            genre=["thriller"],
            tone=["tense"],
            estimated_duration_minutes=2.0,
            primary_characters=["MARA", "OWEN"],
            supporting_characters=[],
            location_count=2,
            locations_summary=["LAB", "ROOF"],
            target_audience=None,
            aspect_ratio="2.39:1",
            production_mode="hybrid",
            human_control_mode="autonomous",
            style_packs={},
            budget_cap_usd=None,
            default_model="mock",
            confirmed=True,
        ).model_dump(mode="json"),
        metadata=_metadata("seed project config"),
    )
    return store


@pytest.mark.unit
def test_shot_list_helpers_render_csv_and_pdf(tmp_path: Path) -> None:
    store = _seed_shot_plan_store(tmp_path / "project")

    plans = load_shot_plans(store)
    assert [plan.scene_number for plan in plans] == [1, 2]

    csv_content = render_shot_list_csv(plans)
    assert "scene_number,scene_heading,shot_id" in csv_content
    assert "S001-A" in csv_content
    assert "INT. LAB - NIGHT" in csv_content

    pdf_path = tmp_path / "shot-list.pdf"
    generate_shot_list_pdf(
        project_name="Pressure Test",
        plans=plans,
        output_path=str(pdf_path),
    )
    assert pdf_path.exists()
    assert pdf_path.read_bytes().startswith(b"%PDF")


@pytest.mark.unit
def test_export_routes_return_shot_list_files(tmp_path: Path) -> None:
    app = create_app(workspace_root=tmp_path)
    client = TestClient(app)
    project_path = tmp_path / "output" / "shot-export"

    response = client.post("/api/projects/new", json={"project_path": str(project_path)})
    assert response.status_code == 200
    project_id = response.json()["project_id"]

    _seed_shot_plan_store(project_path)

    csv_response = client.get(f"/api/projects/{project_id}/export/shot-list.csv")
    assert csv_response.status_code == 200
    assert "text/csv" in csv_response.headers["content-type"]
    assert "S001-A" in csv_response.text

    pdf_response = client.get(f"/api/projects/{project_id}/export/shot-list.pdf")
    assert pdf_response.status_code == 200
    assert pdf_response.headers["content-type"] == "application/pdf"
    assert pdf_response.content.startswith(b"%PDF")
