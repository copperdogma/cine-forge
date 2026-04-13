from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from cine_forge.ai.video import VideoGenerationResult
from cine_forge.driver.engine import DriverEngine
from cine_forge.modules.timeline.track_system_v1.main import best_for_scene
from cine_forge.schemas import (
    ArtifactHealth,
    ArtifactRef,
    GeneratedVideoArtifact,
    MediaValidationArtifact,
    TrackManifest,
)
from tests.render_fixtures import seed_render_project


@pytest.mark.integration
def test_render_recipe_persists_prompt_video_and_track_entries(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_root = Path(__file__).resolve().parents[2]
    seeded = seed_render_project(tmp_path, include_keyframe=True, include_scene_image=True)
    engine = DriverEngine(workspace_root=workspace_root, project_dir=seeded["project_dir"])
    clip_bytes = (
        workspace_root
        / "benchmarks"
        / "video_understanding"
        / "dialogue_confession_push_in"
        / "clip.mp4"
    ).read_bytes()

    def _fake_call_llm(**kwargs):
        schema = kwargs["response_schema"]
        return (
            schema.model_validate(
                {
                    "prompt_text": (
                        "Render the lab confrontation as an eight-second controlled push through "
                        "cold monitor spill, matching the locked opening frame before the camera "
                        "advances into Mara's decision."
                    ),
                    "sections": [
                        {
                            "section_id": "creative_brief",
                            "title": "Creative Brief",
                            "body": (
                                "Project-level tension, pressure, and named taste cues "
                                "remain active."
                            ),
                            "source_artifact_types": [],
                        },
                        {
                            "section_id": "shot_definition",
                            "title": "Shot Definition",
                            "body": "Preserve the planned coverage and slow push.",
                            "source_artifact_types": ["shot_plan"],
                        },
                        {
                            "section_id": "look_and_feel",
                            "title": "Look & Feel",
                            "body": (
                                "Cold practical spill, clipped whites, and divided "
                                "monitor geometry."
                            ),
                            "source_artifact_types": ["look_and_feel"],
                        },
                        {
                            "section_id": "sound_and_music",
                            "title": "Sound & Music",
                            "body": "Keep machinery hum and held tension in the soundtrack cues.",
                            "source_artifact_types": ["sound_and_music"],
                        },
                        {
                            "section_id": "character_and_performance",
                            "title": "Character & Performance",
                            "body": (
                                "Keep Mara compressed and deliberate while the frame "
                                "tightens around her."
                            ),
                            "source_artifact_types": ["character_and_performance", "shot_plan"],
                        },
                        {
                            "section_id": "keyframes",
                            "title": "Keyframe Constraints",
                            "body": "Match the locked opening frame before motion begins.",
                            "source_artifact_types": ["keyframe"],
                        },
                        {
                            "section_id": "character_bible_state",
                            "title": "Character State",
                            "body": "Mara remains exhausted but deliberate in frame.",
                            "source_artifact_types": ["character_bible", "bible_manifest"],
                        },
                        {
                            "section_id": "location_bible_state",
                            "title": "Location State",
                            "body": "The lab is steel-blue, wet, and dense with screens.",
                            "source_artifact_types": ["location_bible", "bible_manifest"],
                        },
                        {
                            "section_id": "injected_assets",
                            "title": "Injected Assets",
                            "body": "Use the scene image only as a supporting look reference.",
                            "source_artifact_types": ["injected_asset_manifest"],
                        },
                    ],
                    "covered_categories": [
                        "creative_brief",
                        "shot_definition",
                        "look_and_feel",
                        "sound_and_music",
                        "character_and_performance",
                        "keyframes",
                        "character_bible_state",
                        "location_bible_state",
                        "injected_assets",
                    ],
                    "missing_inputs": [],
                    "operator_notes": [],
                }
            ),
            {
                "model": kwargs["model"],
                "input_tokens": 200,
                "output_tokens": 150,
                "estimated_cost_usd": 0.01,
                "latency_seconds": 0.5,
                "request_id": "compile-001",
            },
        )

    def _fake_generate_video(*, request, engine_pack):
        return VideoGenerationResult(
            video_bytes=clip_bytes,
            media_type="video/mp4",
            model_used=engine_pack.target_model,
            request_id="video-001",
            provider_job_id="job-001",
        )

    monkeypatch.setattr(
        "cine_forge.modules.generation.render_adapter_v1.prompting.call_llm",
        _fake_call_llm,
    )
    monkeypatch.setattr("cine_forge.ai.video.generate_video", _fake_generate_video)

    run_state = engine.run(
        recipe_path=workspace_root / "configs" / "recipes" / "recipe-render-generation.yaml",
        run_id="integration-render",
        force=True,
        start_from="render",
        runtime_params={
            "engine_pack_id": "openai_sora2",
            "compiler_model": "gpt-5.4-mini",
            "duration_seconds": 8,
        },
    )

    assert run_state["stages"]["render"]["status"] == "done"
    assert run_state["stages"]["validate_media"]["status"] == "done"

    refs = [
        ArtifactRef.model_validate(item) for item in run_state["stages"]["render"]["artifact_refs"]
    ]
    render_prompt_refs = [ref for ref in refs if ref.artifact_type == "render_prompt"]
    generated_video_refs = [ref for ref in refs if ref.artifact_type == "generated_video"]
    assert len(render_prompt_refs) == 1
    assert len(generated_video_refs) == 1

    generated_video = GeneratedVideoArtifact.model_validate(
        engine.store.load_artifact(generated_video_refs[0]).data
    )
    assert (seeded["project_dir"] / generated_video.video.relative_path).exists()
    assert generated_video.preview_provenance is not None
    assert generated_video.preview_provenance.mode == "generated_render"
    render_prompt = engine.store.load_artifact(render_prompt_refs[0]).data
    assert render_prompt["creative_brief_preview"] is not None
    assert render_prompt["preview_provenance"]["mode"] == "generated_render"

    track_ref = next(ref for ref in refs if ref.artifact_type == "track_manifest")
    manifest = TrackManifest.model_validate(engine.store.load_artifact(track_ref).data)
    assert (
        best_for_scene(manifest, scene_id=seeded["scene_id"])["selected_track_type"]
        == "generated_video"
    )

    validation_refs = [
        ArtifactRef.model_validate(item)
        for item in run_state["stages"]["validate_media"]["artifact_refs"]
    ]
    assert len(validation_refs) == 1
    assert validation_refs[0].artifact_type == "media_validation"

    validation = MediaValidationArtifact.model_validate(
        engine.store.load_artifact(validation_refs[0]).data
    )
    assert validation.target_ref.path == generated_video_refs[0].path
    assert validation.recommended_health == ArtifactHealth.NEEDS_REVIEW


@pytest.mark.integration
def test_render_recipe_allows_warning_level_prompt_gaps(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_root = Path(__file__).resolve().parents[2]
    seeded = seed_render_project(tmp_path, include_keyframe=False, include_scene_image=False)
    engine = DriverEngine(workspace_root=workspace_root, project_dir=seeded["project_dir"])
    clip_bytes = (
        workspace_root
        / "benchmarks"
        / "video_understanding"
        / "dialogue_confession_push_in"
        / "clip.mp4"
    ).read_bytes()

    project_config_ref = seeded["store"].latest_ref("project_config", "project")
    assert project_config_ref is not None
    project_config_artifact = seeded["store"].load_artifact(project_config_ref)
    project_config_payload = dict(project_config_artifact.data)
    project_config_payload["production_format"] = None
    seeded["store"].save_artifact(
        artifact_type="project_config",
        entity_id="project",
        data=project_config_payload,
        metadata=project_config_artifact.metadata.model_copy(update={"ref": None}),
    )

    intent_mood_path = seeded["project_dir"] / "artifacts" / "intent_mood" / "project" / "v1.json"
    if intent_mood_path.exists():
        intent_mood_path.unlink()
    look_and_feel_dir = seeded["project_dir"] / "artifacts" / "look_and_feel"
    if look_and_feel_dir.exists():
        for artifact_path in look_and_feel_dir.rglob("*.json"):
            artifact_path.unlink()
    character_bible_dir = seeded["project_dir"] / "artifacts" / "character_bible"
    if character_bible_dir.exists():
        for artifact_path in character_bible_dir.rglob("*.json"):
            artifact_path.unlink()
    location_bible_dir = seeded["project_dir"] / "artifacts" / "location_bible"
    if location_bible_dir.exists():
        for artifact_path in location_bible_dir.rglob("*.json"):
            artifact_path.unlink()
    bibles_dir = seeded["project_dir"] / "artifacts" / "bibles"
    if bibles_dir.exists():
        shutil.rmtree(bibles_dir)

    def _fake_call_llm(**kwargs):
        schema = kwargs["response_schema"]
        return (
            schema.model_validate(
                {
                    "prompt_text": (
                        "Render the confrontation as a controlled push that keeps the room "
                        "pressure "
                        "and Mara's decision legible without inventing absent style docs."
                    ),
                    "sections": [
                        {
                            "section_id": "shot_definition",
                            "title": "Shot Definition",
                            "body": "Preserve the planned slow push and room geometry.",
                            "source_artifact_types": ["shot_plan"],
                        },
                        {
                            "section_id": "character_and_performance",
                            "title": "Character & Performance",
                            "body": "Keep Mara compressed and deliberate while the frame tightens.",
                            "source_artifact_types": ["character_and_performance", "shot_plan"],
                        },
                    ],
                    "covered_categories": [
                        "shot_definition",
                        "character_and_performance",
                    ],
                    "missing_inputs": [
                        "creative_brief",
                        "look_and_feel",
                        "sound_and_music",
                        "rhythm_and_flow",
                        "character_bible_state",
                        "location_bible_state",
                        "keyframes",
                        "injected_assets",
                    ],
                    "operator_notes": [
                        "Optional upstream direction is absent, so the adapter stayed shot-plan "
                        "grounded."
                    ],
                }
            ),
            {
                "model": kwargs["model"],
                "input_tokens": 170,
                "output_tokens": 135,
                "estimated_cost_usd": 0.009,
                "latency_seconds": 0.6,
                "request_id": "compile-warning-001",
            },
        )

    monkeypatch.setattr(
        "cine_forge.modules.generation.render_adapter_v1.prompting.call_llm",
        _fake_call_llm,
    )
    monkeypatch.setattr(
        "cine_forge.ai.video.generate_video",
        lambda *, request, engine_pack: VideoGenerationResult(
            video_bytes=clip_bytes,
            media_type="video/mp4",
            model_used=engine_pack.target_model,
            request_id="video-warning-001",
            provider_job_id="job-warning-001",
        ),
    )

    run_state = engine.run(
        recipe_path=workspace_root / "configs" / "recipes" / "recipe-render-generation.yaml",
        run_id="integration-render-warning-gaps",
        force=True,
        start_from="render",
        runtime_params={
            "engine_pack_id": "openai_sora2",
            "compiler_model": "gpt-5.4-mini",
            "duration_seconds": 8,
        },
    )

    assert run_state["stages"]["render"]["status"] == "done"
    render_refs = [
        ArtifactRef.model_validate(item) for item in run_state["stages"]["render"]["artifact_refs"]
    ]
    render_prompt_ref = next(ref for ref in render_refs if ref.artifact_type == "render_prompt")
    render_prompt = engine.store.load_artifact(render_prompt_ref).data

    assert render_prompt["completeness"]["blocking_missing_categories"] == []
    assert render_prompt["completeness"]["advisory_missing_categories"] == [
        "character_bible_state",
        "creative_brief",
        "injected_assets",
        "keyframes",
        "location_bible_state",
        "look_and_feel",
        "rhythm_and_flow",
        "sound_and_music",
    ]


@pytest.mark.integration
def test_render_recipe_persists_reference_conditioned_truth_for_google_pack(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_root = Path(__file__).resolve().parents[2]
    seeded = seed_render_project(
        tmp_path,
        include_keyframe=True,
        include_scene_image=True,
        include_project_taste_refs=True,
    )
    engine = DriverEngine(workspace_root=workspace_root, project_dir=seeded["project_dir"])
    clip_bytes = (
        workspace_root
        / "benchmarks"
        / "video_understanding"
        / "dialogue_confession_push_in"
        / "clip.mp4"
    ).read_bytes()
    monkeypatch.setattr(
        "cine_forge.ai.video.generate_video",
        lambda *, request, engine_pack: VideoGenerationResult(
            video_bytes=clip_bytes,
            media_type="video/mp4",
            model_used=engine_pack.target_model,
            request_id="video-reference-conditioned-001",
            provider_job_id="job-reference-conditioned-001",
        ),
    )

    run_state = engine.run(
        recipe_path=workspace_root / "configs" / "recipes" / "recipe-render-generation.yaml",
        run_id="integration-render-reference-conditioned",
        force=True,
        start_from="render",
        runtime_params={
            "engine_pack_id": "google_veo31",
            "compiler_model": "mock",
            "duration_seconds": 8,
        },
    )

    assert run_state["stages"]["render"]["status"] == "done"

    refs = [
        ArtifactRef.model_validate(item) for item in run_state["stages"]["render"]["artifact_refs"]
    ]
    render_prompt_ref = next(ref for ref in refs if ref.artifact_type == "render_prompt")
    generated_video_ref = next(ref for ref in refs if ref.artifact_type == "generated_video")

    render_prompt = engine.store.load_artifact(render_prompt_ref).data
    generated_video = GeneratedVideoArtifact.model_validate(
        engine.store.load_artifact(generated_video_ref).data
    )
    resolved = {item["label"]: item["used_as"] for item in render_prompt["resolved_inputs"]}

    assert render_prompt["creative_brief_preview"] is not None
    assert {
        (reference["filename"], reference["purpose"])
        for reference in render_prompt["creative_brief_preview"]["active_project_references"]
    } == {
        ("mood_board.jpg", "mood_board"),
        ("style_reference.jpg", "style_reference"),
    }
    assert resolved["Character visual reference: mara"] == "reference_image"
    assert resolved["Location visual reference: LAB"] == "reference_image"
    assert generated_video.prompt_ref.path == render_prompt_ref.path
