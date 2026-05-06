from __future__ import annotations

import json
from pathlib import Path

import pytest

from cine_forge.ai.video import VideoGenerationResult
from cine_forge.modules.generation.render_adapter_v1.main import run_module
from cine_forge.schemas import GeneratedVideoArtifact, Scene
from cine_forge.schemas.design_study import DesignStudyState
from cine_forge.services.design_study_backfill import (
    DefaultDesignStudyBackfillService,
    read_design_study_state,
)
from cine_forge.services.design_study_backfill_store import write_design_study_state
from cine_forge.services.injected_assets import InjectedAssetService
from tests.render_fixtures import seed_render_project
from tests.storyboard_fixtures import metadata, reference_raster_bytes, seed_storyboard_project


def _add_bible_manifest(
    project_dir: Path,
    *,
    entity_type: str,
    entity_id: str,
    display_name: str,
    data: dict[str, object],
) -> None:
    from cine_forge.artifacts import ArtifactStore

    ArtifactStore(project_dir=project_dir).save_bible_entry(
        entity_type=entity_type,
        entity_id=entity_id,
        display_name=display_name,
        files=[
            {
                "filename": "master_definition_v1.json",
                "purpose": "master_definition",
                "version": 1,
                "provenance": "ai_extracted",
            }
        ],
        data_files={"master_definition_v1.json": json.dumps(data)},
        metadata=metadata(f"seed {entity_type} bible manifest"),
    )


def _add_owen_and_console_bibles(project_dir: Path) -> None:
    _add_bible_manifest(
        project_dir,
        entity_type="character",
        entity_id="owen",
        display_name="OWEN",
        data={
            "character_id": "owen",
            "name": "OWEN",
            "description": "A pragmatist willing to accept collateral damage.",
            "narrative_role": "supporting",
            "scene_presence": ["scene_001"],
            "inferred_traits": [
                {
                    "trait": "wardrobe",
                    "value": "dark wool coat",
                    "confidence": 0.93,
                    "rationale": "Observed in the confrontation sequence.",
                }
            ],
        },
    )
    _add_bible_manifest(
        project_dir,
        entity_type="prop",
        entity_id="console",
        display_name="Console",
        data={
            "prop_id": "console",
            "name": "Console",
            "description": "A battered lab control console with dim status lights.",
            "narrative_significance": "The physical trigger object for the scene.",
            "associated_characters": ["mara", "owen"],
        },
    )


@pytest.mark.unit
def test_default_design_study_backfill_generates_missing_entity_references(tmp_path: Path) -> None:
    seeded = seed_storyboard_project(tmp_path, scene_count=1)
    project_dir = seeded["project_dir"]
    store = seeded["store"]
    _add_owen_and_console_bibles(project_dir)
    scene_ref = store.list_versions("scene", "scene_001")[-1]
    scene = Scene.model_validate(store.load_artifact(scene_ref).data)

    result = DefaultDesignStudyBackfillService(project_dir, image_model="mock").backfill_scene(
        scene
    )

    by_entity = {item.entity_id: item for item in result.items}
    assert by_entity["character_mara"].status == "skipped_existing_reference"
    assert by_entity["location_lab"].status == "skipped_existing_reference"
    assert by_entity["character_owen"].status == "generated"
    assert by_entity["prop_console"].status == "generated"

    owen_state = read_design_study_state(project_dir, "character_owen")
    assert owen_state is not None
    assert owen_state.selected_final_source == "system_default"
    assert owen_state.selected_final_filename == "design_study_r1_img1.jpg"
    assert owen_state.rounds[0].generation_mode == "default_backfill"
    assert owen_state.rounds[0].estimated_cost_usd == 0.0
    assert "default_backfill_contract" in owen_state.rounds[0].sources_used
    assert "automatic default reference" in owen_state.rounds[0].prompt

    owen_manifest_ref = store.list_versions("bible_manifest", "character_owen")[-1]
    owen_manifest, _ = store.load_bible_entry(owen_manifest_ref)
    assert owen_manifest.visual_reference_image == "design_study_r1_img1.jpg"
    assert (project_dir / "artifacts/bibles/character_owen/design_study_r1_img1.jpg").exists()


@pytest.mark.unit
def test_default_design_study_backfill_skips_existing_entity_uploaded_image(
    tmp_path: Path,
) -> None:
    seeded = seed_storyboard_project(tmp_path, scene_count=1)
    project_dir = seeded["project_dir"]
    store = seeded["store"]
    _add_owen_and_console_bibles(project_dir)

    InjectedAssetService(project_dir).inject_asset(
        target_kind="character",
        target_id="owen",
        purpose="reference_image",
        filename="owen_uploaded.jpg",
        content=reference_raster_bytes("OWEN", accent=(255, 190, 120)),
        lock_status="soft_locked",
        content_type="image/jpeg",
    )
    scene_ref = store.list_versions("scene", "scene_001")[-1]
    scene = Scene.model_validate(store.load_artifact(scene_ref).data)

    result = DefaultDesignStudyBackfillService(project_dir, image_model="mock").backfill_scene(
        scene
    )

    owen = {item.entity_id: item for item in result.items}["character_owen"]
    assert owen.status == "skipped_existing_reference"
    assert "image asset" in str(owen.reason)
    assert read_design_study_state(project_dir, "character_owen") is None


@pytest.mark.unit
def test_default_design_study_backfill_ignores_stale_injected_image_manifest(
    tmp_path: Path,
) -> None:
    seeded = seed_storyboard_project(tmp_path, scene_count=1)
    project_dir = seeded["project_dir"]
    store = seeded["store"]
    _add_owen_and_console_bibles(project_dir)

    manifest = InjectedAssetService(project_dir).inject_asset(
        target_kind="character",
        target_id="owen",
        purpose="reference_image",
        filename="owen_uploaded.jpg",
        content=reference_raster_bytes("OWEN", accent=(255, 190, 120)),
        lock_status="soft_locked",
        content_type="image/jpeg",
    )
    stale_asset_path = project_dir / manifest.assets[0].file_path
    stale_asset_path.unlink()

    scene_ref = store.list_versions("scene", "scene_001")[-1]
    scene = Scene.model_validate(store.load_artifact(scene_ref).data)

    result = DefaultDesignStudyBackfillService(project_dir, image_model="mock").backfill_scene(
        scene
    )

    owen = {item.entity_id: item for item in result.items}["character_owen"]
    assert owen.status == "generated"
    assert owen.image_filename == "design_study_r1_img1.jpg"


@pytest.mark.unit
def test_default_design_study_backfill_restores_existing_selected_state_to_manifest(
    tmp_path: Path,
) -> None:
    seeded = seed_storyboard_project(tmp_path, scene_count=1)
    project_dir = seeded["project_dir"]
    store = seeded["store"]
    _add_owen_and_console_bibles(project_dir)

    image_filename = "design_study_r1_img1.jpg"
    image_path = project_dir / "artifacts" / "bibles" / "character_owen" / image_filename
    image_path.write_bytes(reference_raster_bytes("OWEN", accent=(255, 190, 120)))
    write_design_study_state(
        project_dir,
        "character_owen",
        DesignStudyState(
            entity_id="character_owen",
            entity_type="character",
            selected_final_filename=image_filename,
            selected_final_source="system_default",
        ),
    )

    scene_ref = store.list_versions("scene", "scene_001")[-1]
    scene = Scene.model_validate(store.load_artifact(scene_ref).data)

    result = DefaultDesignStudyBackfillService(project_dir, image_model="mock").backfill_scene(
        scene
    )

    owen = {item.entity_id: item for item in result.items}["character_owen"]
    assert owen.status == "skipped_existing_reference"
    assert owen.image_filename == image_filename
    assert "restored to the manifest" in str(owen.reason)

    owen_manifest_ref = store.list_versions("bible_manifest", "character_owen")[-1]
    owen_manifest, owen_metadata = store.load_bible_entry(owen_manifest_ref)
    assert owen_manifest.visual_reference_image == image_filename
    assert owen_metadata.source == "code"


@pytest.mark.unit
def test_render_adapter_backfills_design_studies_before_reference_resolution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seeded = seed_render_project(
        tmp_path,
        include_keyframe=False,
        include_scene_image=False,
        include_project_taste_refs=False,
    )
    project_dir = seeded["project_dir"]
    _add_owen_and_console_bibles(project_dir)

    monkeypatch.setattr(
        "cine_forge.modules.generation.render_adapter_v1.main.generate_video",
        lambda *, request, engine_pack: VideoGenerationResult(
            video_bytes=b"fake-mp4",
            media_type="video/mp4",
            model_used=engine_pack.target_model,
            request_id="video-backfill-001",
            provider_job_id="job-backfill-001",
        ),
    )

    result = run_module(
        inputs=seeded["inputs"],
        params={
            "compiler_model": "mock",
            "engine_pack_id": "google_veo31",
            "duration_seconds": 8,
            "default_design_study_backfill": True,
            "default_design_study_backfill_model": "mock",
        },
        context={"project_dir": str(project_dir)},
    )

    prompt_payload = next(
        artifact["data"]
        for artifact in result["artifacts"]
        if artifact["artifact_type"] == "render_prompt"
    )
    resolved_by_id = {item["input_id"]: item for item in prompt_payload["resolved_inputs"]}
    assert resolved_by_id["character_visual_owen"]["lock_status"] == (
        "system_default_visual_reference"
    )
    assert resolved_by_id["prop_visual_console"]["lock_status"] == (
        "system_default_visual_reference"
    )
    assert "not yet human-approved" in resolved_by_id["character_visual_owen"]["notes"]

    video_payload = next(
        artifact["data"]
        for artifact in result["artifacts"]
        if artifact["artifact_type"] == "generated_video"
    )
    generated_video = GeneratedVideoArtifact.model_validate(video_payload)
    assert any(
        item.input_id == "character_visual_owen"
        for item in generated_video.resolved_inputs
    )
    assert any(item.input_id == "prop_visual_console" for item in generated_video.resolved_inputs)
