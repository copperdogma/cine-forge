from __future__ import annotations

from pathlib import Path

import pytest

from cine_forge.ai.video import VideoGenerationResult
from cine_forge.modules.generation.render_adapter_v1.main import run_module
from cine_forge.modules.generation.render_adapter_v1.support import load_engine_pack
from cine_forge.modules.timeline.track_system_v1.main import best_for_scene
from cine_forge.schemas import (
    ArtifactMetadata,
    CompiledRenderPrompt,
    GeneratedVideoArtifact,
    TrackManifest,
)
from tests.render_fixtures import seed_render_project


@pytest.mark.unit
def test_load_engine_pack_supports_story_143_previz_candidate_packs() -> None:
    sora = load_engine_pack("openai_sora2")
    veo = load_engine_pack("google_veo31")
    veo_fast = load_engine_pack("google_veo31_fast")
    veo_lite = load_engine_pack("google_veo31_lite")

    assert sora.provider == "openai"
    assert sora.target_model == "sora-2"
    assert veo.provider == "google"
    assert "1080p" in veo.limits.supported_resolutions
    assert veo_fast.target_model == "veo-3.1-fast-generate-preview"
    assert veo_fast.request_defaults["benchmark_cost_per_second_usd"] == 0.10
    assert veo_lite.target_model == "veo-3.1-lite-generate-preview"
    assert veo_lite.limits.max_reference_images == 0


@pytest.mark.unit
def test_run_module_generates_prompt_video_and_track_entries(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seeded = seed_render_project(tmp_path, include_keyframe=True, include_scene_image=True)
    captured: dict[str, object] = {}

    def _fake_call_llm(**kwargs):
        captured["compiler_prompt"] = kwargs["prompt"]
        schema = kwargs["response_schema"]
        return (
            schema.model_validate(
                {
                    "prompt_text": (
                        "Render the confrontation as a controlled opening push through cold "
                        "monitor light, keeping Mara pinned against the console and the room's "
                        "machine hum present in the atmosphere."
                    ),
                    "sections": [
                        {
                            "section_id": "creative_brief",
                            "title": "Creative Brief",
                            "body": (
                                "Live-action pressure cooker with wind-scoured tension "
                                "and named project taste cues."
                            ),
                            "source_artifact_types": [],
                        },
                        {
                            "section_id": "shot_definition",
                            "title": "Shot Definition",
                            "body": "Use the planned slow push and preserve the hero coverage.",
                            "source_artifact_types": ["shot_plan"],
                        },
                        {
                            "section_id": "look_and_feel",
                            "title": "Look & Feel",
                            "body": (
                                "Cold practical spill, hard monitor highlights, "
                                "divided frames."
                            ),
                            "source_artifact_types": ["look_and_feel"],
                        },
                        {
                            "section_id": "sound_and_music",
                            "title": "Sound & Music",
                            "body": "Keep machinery hum and restrained pressure in the audio cues.",
                            "source_artifact_types": ["sound_and_music"],
                        },
                        {
                            "section_id": "character_and_performance",
                            "title": "Character & Performance",
                            "body": (
                                "Keep Mara's posture taut and Owen rigid within the "
                                "frame geometry."
                            ),
                            "source_artifact_types": ["character_and_performance", "shot_plan"],
                        },
                        {
                            "section_id": "character_bible_state",
                            "title": "Character State",
                            "body": "Mara is exhausted but resolute in the approved silhouette.",
                            "source_artifact_types": ["character_bible", "bible_manifest"],
                        },
                        {
                            "section_id": "location_bible_state",
                            "title": "Location State",
                            "body": "The lab is steel-blue, wet, and crowded with monitor banks.",
                            "source_artifact_types": ["location_bible", "bible_manifest"],
                        },
                        {
                            "section_id": "keyframes",
                            "title": "Keyframe Constraints",
                            "body": (
                                "Match the locked opening frame exactly before "
                                "introducing motion."
                            ),
                            "source_artifact_types": ["keyframe"],
                        },
                        {
                            "section_id": "injected_assets",
                            "title": "Injected Assets",
                            "body": "Use the scene reference image only as a secondary look cue.",
                            "source_artifact_types": ["injected_asset_manifest"],
                        },
                    ],
                    "covered_categories": [
                        "creative_brief",
                        "shot_definition",
                        "look_and_feel",
                        "sound_and_music",
                        "character_and_performance",
                        "character_bible_state",
                        "location_bible_state",
                        "keyframes",
                        "injected_assets",
                    ],
                    "missing_inputs": [],
                    "operator_notes": ["All required upstream context was represented."],
                }
            ),
            {
                "model": kwargs["model"],
                "input_tokens": 280,
                "output_tokens": 180,
                "estimated_cost_usd": 0.012,
                "latency_seconds": 0.9,
                "request_id": "compile-001",
            },
        )

    def _fake_generate_video(*, request, engine_pack):
        captured["video_request"] = request
        return VideoGenerationResult(
            video_bytes=b"fake-mp4",
            media_type="video/mp4",
            model_used=engine_pack.target_model,
            request_id="video-001",
            provider_job_id="job-001",
        )

    monkeypatch.setattr(
        "cine_forge.modules.generation.render_adapter_v1.prompting.call_llm",
        _fake_call_llm,
    )
    monkeypatch.setattr(
        "cine_forge.modules.generation.render_adapter_v1.main.generate_video",
        _fake_generate_video,
    )

    result = run_module(
        inputs=seeded["inputs"],
        params={
            "engine_pack_id": "openai_sora2",
            "compiler_model": "gpt-5.4-mini",
            "duration_seconds": 8,
        },
        context={"project_dir": str(seeded["project_dir"])},
    )

    prompt_output = next(
        artifact for artifact in result["artifacts"] if artifact["artifact_type"] == "render_prompt"
    )
    video_output = next(
        artifact
        for artifact in result["artifacts"]
        if artifact["artifact_type"] == "generated_video"
    )
    prompt_payload = next(
        artifact["data"]
        for artifact in result["artifacts"]
        if artifact["artifact_type"] == "render_prompt"
    )
    video_payload = next(
        artifact["data"]
        for artifact in result["artifacts"]
        if artifact["artifact_type"] == "generated_video"
    )
    manifest_payload = next(
        artifact["data"]
        for artifact in result["artifacts"]
        if artifact["artifact_type"] == "track_manifest"
    )

    prompt_artifact = CompiledRenderPrompt.model_validate(prompt_payload)
    generated_video = GeneratedVideoArtifact.model_validate(video_payload)
    manifest = TrackManifest.model_validate(manifest_payload)

    assert "Coverage approach" in str(captured["compiler_prompt"])
    assert "CREATIVE BRIEF:" in str(captured["compiler_prompt"])
    assert prompt_output["exclude_upstream_lineage_types"] == ["track_manifest"]
    assert prompt_artifact.target_provider == "openai"
    assert prompt_artifact.completeness.missing_categories == []
    assert prompt_artifact.creative_brief_preview is not None
    assert video_output["exclude_upstream_lineage_types"] == ["track_manifest"]
    assert any(item.used_as == "input_reference" for item in prompt_artifact.resolved_inputs)
    assert generated_video.prompt_ref.artifact_type == "render_prompt"
    assert (seeded["project_dir"] / generated_video.video.relative_path).exists()
    assert (
        best_for_scene(manifest, scene_id=seeded["scene_id"])["selected_track_type"]
        == "generated_video"
    )


@pytest.mark.unit
def test_run_module_generates_ai_previz_artifacts_and_track_entries(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seeded = seed_render_project(tmp_path, include_keyframe=True, include_scene_image=True)
    store = seeded["store"]
    scene_id = seeded["scene_id"]

    scene_ref = store.list_versions("scene", scene_id)[-1]
    shot_plan_ref = store.list_versions("shot_plan", scene_id)[-1]
    keyframe_ref = store.list_versions("keyframe", scene_id)[-1]
    metadata = ArtifactMetadata(
        lineage=[scene_ref, shot_plan_ref, keyframe_ref],
        intent="seed previz references",
        rationale="unit test seed",
        confidence=1.0,
        source="code",
    )
    store.save_artifact(
        artifact_type="animatic",
        entity_id=scene_id,
        data={"scene_id": scene_id, "segments": [], "duration_seconds": 0.0},
        metadata=metadata,
    )
    store.save_artifact(
        artifact_type="previz_reel",
        entity_id="project",
        data={"scenes": [], "total_duration_seconds": 0.0},
        metadata=metadata,
    )

    monkeypatch.setattr(
        "cine_forge.modules.generation.render_adapter_v1.main.compile_render_prompt",
        lambda *args, **kwargs: pytest.fail(
            "render prompt compilation should not run for ai_previz mode"
        ),
    )
    monkeypatch.setattr(
        "cine_forge.modules.generation.render_adapter_v1.main.generate_video",
        lambda *, request, engine_pack: VideoGenerationResult(
            video_bytes=b"fake-mp4",
            media_type="video/mp4",
            model_used=engine_pack.target_model,
            request_id="previz-video-001",
            provider_job_id="previz-job-001",
        ),
    )

    result = run_module(
        inputs=seeded["inputs"],
        params={
            "prompt_mode": "ai_previz",
            "engine_pack_id": "google_veo31_lite",
            "duration_seconds": 8,
            "resolution": "1280x720",
            "consistency_strategy": "prompt_only",
        },
        context={"project_dir": str(seeded["project_dir"])},
    )

    prompt_payload = next(
        artifact["data"]
        for artifact in result["artifacts"]
        if artifact["artifact_type"] == "ai_previz_prompt"
    )
    video_payload = next(
        artifact["data"]
        for artifact in result["artifacts"]
        if artifact["artifact_type"] == "ai_previz_video"
    )
    manifest_payload = next(
        artifact["data"]
        for artifact in result["artifacts"]
        if artifact["artifact_type"] == "track_manifest"
    )

    prompt_artifact = CompiledRenderPrompt.model_validate(prompt_payload)
    generated_video = GeneratedVideoArtifact.model_validate(video_payload)
    manifest = TrackManifest.model_validate(manifest_payload)

    assert prompt_artifact.compiler_model == "code"
    assert prompt_artifact.preview_provenance.mode == "ai_previz"
    assert prompt_artifact.preview_provenance.consistency_strategy == "prompt_only"
    assert "This is previs, not a final render." in prompt_artifact.prompt_text
    assert generated_video.prompt_ref.artifact_type == "ai_previz_prompt"
    assert generated_video.previz_baseline_ref is not None
    assert generated_video.previz_baseline_ref.artifact_type == "animatic"
    assert generated_video.previz_reel_ref is not None
    assert generated_video.previz_reel_ref.artifact_type == "previz_reel"
    assert generated_video.preview_provenance.mode == "ai_previz"
    assert (seeded["project_dir"] / generated_video.video.relative_path).exists()
    assert (
        best_for_scene(manifest, scene_id=seeded["scene_id"])["selected_track_type"]
        == "ai_previz_video"
    )


@pytest.mark.unit
def test_run_module_rejects_hard_locked_audio_for_non_upload_pack(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seeded = seed_render_project(
        tmp_path,
        include_keyframe=True,
        include_scene_image=False,
        include_scene_audio=True,
    )

    monkeypatch.setattr(
        "cine_forge.modules.generation.render_adapter_v1.prompting.call_llm",
        lambda **_: pytest.fail(
            "prompt compilation should not start when audio upload is unsupported"
        ),
    )
    monkeypatch.setattr(
        "cine_forge.modules.generation.render_adapter_v1.main.generate_video",
        lambda **_: pytest.fail("video generation should not start when capability checks fail"),
    )

    with pytest.raises(ValueError, match="does not support required audio uploads"):
        run_module(
            inputs=seeded["inputs"],
            params={"engine_pack_id": "openai_sora2", "duration_seconds": 8},
            context={"project_dir": str(seeded["project_dir"])},
        )
