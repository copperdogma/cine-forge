from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

from cine_forge.ai.video import VideoGenerationResult
from cine_forge.modules.generation.render_adapter_v1.main import (
    _ensure_dialogue_prompt_contract,
    run_module,
)
from cine_forge.modules.generation.render_adapter_v1.support import load_engine_pack
from cine_forge.modules.timeline.track_system_v1.main import best_for_scene
from cine_forge.schemas import (
    CompiledRenderPrompt,
    GeneratedVideoArtifact,
    RenderClipPlan,
    ShotPlan,
    TrackManifest,
)
from cine_forge.services import InjectedAssetService
from tests.render_fixtures import seed_render_project
from tests.storyboard_fixtures import reference_raster_bytes


@pytest.mark.unit
def test_load_engine_pack_supports_story_143_previz_candidate_packs() -> None:
    sora = load_engine_pack("openai_sora2")
    veo = load_engine_pack("google_veo31")
    veo_fast = load_engine_pack("google_veo31_fast")
    veo_lite = load_engine_pack("google_veo31_lite")
    grok = load_engine_pack("xai_grok_imagine_video")

    assert sora.provider == "openai"
    assert sora.target_model == "sora-2"
    assert veo.provider == "google"
    assert "1080p" in veo.limits.supported_resolutions
    assert veo_fast.target_model == "veo-3.1-fast-generate-preview"
    assert veo_fast.request_defaults["benchmark_cost_per_second_usd"] == 0.10
    assert veo_lite.target_model == "veo-3.1-lite-generate-preview"
    assert veo_lite.limits.max_reference_images == 0
    assert grok.provider == "xai"
    assert grok.target_model == "grok-imagine-video"
    assert grok.request_defaults["default_resolution"] == "480p"


@pytest.mark.unit
def test_render_module_metadata_defaults_final_render_to_google_veo31() -> None:
    module_yaml = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "cine_forge"
        / "modules"
        / "generation"
        / "render_adapter_v1"
        / "module.yaml"
    )
    payload = yaml.safe_load(module_yaml.read_text(encoding="utf-8"))

    assert payload["parameters"]["engine_pack_id"]["default"] == "google_veo31"


@pytest.mark.unit
def test_run_module_defaults_final_render_to_google_veo31(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seeded = seed_render_project(
        tmp_path,
        include_keyframe=False,
        include_scene_image=True,
        include_project_taste_refs=True,
    )
    captured: dict[str, str] = {}

    monkeypatch.setattr(
        "cine_forge.modules.generation.render_adapter_v1.main.generate_video",
        lambda *, request, engine_pack: (
            captured.setdefault("engine_pack_id", engine_pack.pack_id),
            VideoGenerationResult(
                video_bytes=b"fake-mp4",
                media_type="video/mp4",
                model_used=engine_pack.target_model,
                request_id="video-default-001",
                provider_job_id="job-default-001",
            ),
        )[1],
    )

    result = run_module(
        inputs=seeded["inputs"],
        params={"compiler_model": "mock", "duration_seconds": 8},
        context={"project_dir": str(seeded["project_dir"])},
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

    prompt_artifact = CompiledRenderPrompt.model_validate(prompt_payload)
    generated_video = GeneratedVideoArtifact.model_validate(video_payload)

    assert captured["engine_pack_id"] == "google_veo31"
    assert prompt_artifact.engine_pack_id == "google_veo31"
    assert generated_video.engine_pack_id == "google_veo31"


@pytest.mark.unit
def test_run_module_generates_prompt_video_and_track_entries(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seeded = seed_render_project(
        tmp_path,
        include_keyframe=True,
        include_scene_image=True,
        include_project_taste_refs=True,
    )
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
    assert "Dialogue timing / exact lines:" in str(captured["compiler_prompt"])
    assert "We can still stop this." in str(captured["compiler_prompt"])
    assert "CREATIVE BRIEF:" in str(captured["compiler_prompt"])
    assert prompt_output["exclude_upstream_lineage_types"] == ["track_manifest"]
    assert prompt_artifact.target_provider == "openai"
    assert "Dialogue timing / exact lines:" in prompt_artifact.prompt_text
    assert "- We can still stop this." in prompt_artifact.prompt_text
    assert "Dialogue cadence:" in prompt_artifact.prompt_text
    assert "Dialogue timing / exact lines:" in captured["video_request"].prompt
    assert "- We can still stop this." in captured["video_request"].prompt
    assert any(
        note.startswith("Adapter appended a dialogue timing contract from the shot plan")
        for note in prompt_artifact.completeness.notes
    )
    assert any(
        note.startswith("Adapter added dialogue cadence guidance")
        for note in prompt_artifact.completeness.notes
    )
    assert prompt_artifact.completeness.missing_categories == []
    assert prompt_artifact.creative_brief_preview is not None
    assert {
        (reference.filename, reference.purpose)
        for reference in prompt_artifact.creative_brief_preview.active_project_references
    } == {
        ("mood_board.jpg", "mood_board"),
        ("style_reference.jpg", "style_reference"),
    }
    assert {
        item.label
        for item in prompt_artifact.resolved_inputs
        if item.kind == "character_injected_image"
    } == {"Character visual reference: mara"}
    assert {
        item.label
        for item in prompt_artifact.resolved_inputs
        if item.kind == "location_injected_image"
    } == {"Location visual reference: LAB"}
    assert video_output["exclude_upstream_lineage_types"] == ["track_manifest"]
    assert any(item.used_as == "input_reference" for item in prompt_artifact.resolved_inputs)
    assert generated_video.prompt_ref.artifact_type == "render_prompt"
    assert (seeded["project_dir"] / generated_video.video.relative_path).exists()
    assert (
        best_for_scene(manifest, scene_id=seeded["scene_id"])["selected_track_type"]
        == "generated_video"
    )


@pytest.mark.unit
def test_run_module_builds_clip_local_render_prompts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seeded = seed_render_project(
        tmp_path,
        include_keyframe=False,
        include_scene_image=True,
    )
    scene_id = seeded["scene_id"]
    base_plan = ShotPlan.model_validate(seeded["inputs"]["shot_plan"][0])
    first_shot = base_plan.shots[0].model_copy(
        update={
            "shot_id": "SCENE_001_A",
            "action_description": "FIRST ACTION ONLY: Steel enters with the beers.",
            "dialogue_lines": ["STEEL: FIRST ONLY."],
            "duration_estimate_seconds": 8.0,
        }
    )
    second_shot = base_plan.shots[0].model_copy(
        update={
            "shot_id": "SCENE_001_B",
            "action_description": "SECOND ACTION ONLY: The retirement silence lands.",
            "dialogue_lines": ["BRICK: SECOND ONLY."],
            "duration_estimate_seconds": 8.0,
        }
    )
    third_shot = base_plan.shots[0].model_copy(
        update={
            "shot_id": "SCENE_001_C",
            "action_description": "THIRD ACTION ONLY: Steel breaks the silence.",
            "dialogue_lines": ["STEEL: THIRD ONLY."],
            "duration_estimate_seconds": 8.0,
        }
    )
    fourth_shot = base_plan.shots[0].model_copy(
        update={
            "shot_id": "SCENE_001_D",
            "action_description": "FOURTH ACTION ONLY: Brick agrees and the cut lands.",
            "dialogue_lines": ["BRICK: FOURTH ONLY."],
            "duration_estimate_seconds": 8.0,
        }
    )
    seeded["inputs"]["shot_plan"] = [
        base_plan.model_copy(
            update={
                "shots": [first_shot, second_shot, third_shot, fourth_shot],
                "total_estimated_duration_seconds": 32.0,
            }
        ).model_dump(mode="json")
    ]
    shot_plan_ref = seeded["store"].list_versions("shot_plan", scene_id)[-1]
    render_clip_plan = RenderClipPlan.model_validate(
        {
            "scene_id": scene_id,
            "scene_number": base_plan.scene_number,
            "scene_heading": base_plan.scene_heading,
            "scene_ref": base_plan.scene_ref.model_dump(mode="json"),
            "shot_plan_ref": shot_plan_ref.model_dump(mode="json"),
            "selected_engine_pack_id": "openai_sora2",
            "engine_max_clip_duration_seconds": 8.0,
            "target_dramatic_duration_seconds": 32.0,
            "duration_rationale": "Four dialogue beats need separate render units.",
            "confidence": 0.84,
            "source": "ai",
            "provenance_mode": "shot_plan_ai",
            "planner_model": "gpt-5.4-mini",
            "missing_upstream_categories": [],
            "deterministic_lower_bound_seconds": 28.0,
            "clips": [
                {
                    "clip_id": f"{scene_id}_clip_001",
                    "scene_id": scene_id,
                    "source_shot_ids": ["SCENE_001_A"],
                    "start_time_seconds": 0.0,
                    "end_time_seconds": 8.0,
                    "target_duration_seconds": 8.0,
                    "dialogue_lines": ["STEEL: FIRST ONLY."],
                    "action_beats": ["FIRST ACTION ONLY: Steel enters with the beers."],
                    "continuity_end_notes": ["Steel sits with the beer bottles settled."],
                    "derivation": "shot_plan",
                    "rationale": "Opening movement and first line.",
                    "confidence": 0.9,
                },
                {
                    "clip_id": f"{scene_id}_clip_002",
                    "scene_id": scene_id,
                    "source_shot_ids": ["SCENE_001_B"],
                    "start_time_seconds": 8.0,
                    "end_time_seconds": 16.0,
                    "target_duration_seconds": 8.0,
                    "dialogue_lines": ["BRICK: SECOND ONLY."],
                    "action_beats": ["SECOND ACTION ONLY: The retirement silence lands."],
                    "continuity_start_notes": ["Steel is already seated with both beers settled."],
                    "derivation": "shot_plan",
                    "rationale": "Second beat and reaction silence.",
                    "confidence": 0.88,
                },
                {
                    "clip_id": f"{scene_id}_clip_003",
                    "scene_id": scene_id,
                    "source_shot_ids": ["SCENE_001_C"],
                    "start_time_seconds": 16.0,
                    "end_time_seconds": 24.0,
                    "target_duration_seconds": 8.0,
                    "dialogue_lines": ["STEEL: THIRD ONLY."],
                    "action_beats": ["THIRD ACTION ONLY: Steel breaks the silence."],
                    "continuity_start_notes": ["Both partners are still seated."],
                    "continuity_end_notes": ["Steel has committed to the line."],
                    "derivation": "shot_plan",
                    "rationale": "Third beat and decision turn.",
                    "confidence": 0.87,
                },
                {
                    "clip_id": f"{scene_id}_clip_004",
                    "scene_id": scene_id,
                    "source_shot_ids": ["SCENE_001_D"],
                    "start_time_seconds": 24.0,
                    "end_time_seconds": 32.0,
                    "target_duration_seconds": 8.0,
                    "dialogue_lines": ["BRICK: FOURTH ONLY."],
                    "action_beats": ["FOURTH ACTION ONLY: Brick agrees and the cut lands."],
                    "continuity_start_notes": ["Steel's line hangs in the air."],
                    "derivation": "shot_plan",
                    "rationale": "Fourth beat and smash-cut setup.",
                    "confidence": 0.86,
                },
            ],
        }
    )
    seeded["inputs"]["render_clip_plan"] = [render_clip_plan.model_dump(mode="json")]
    compiler_prompts: list[str] = []

    def _fake_call_llm(**kwargs):
        compiler_prompts.append(str(kwargs["prompt"]))
        schema = kwargs["response_schema"]
        return (
            schema.model_validate(
                {
                    "prompt_text": "Render this isolated planned clip with restrained pacing.",
                    "sections": [
                        {
                            "section_id": "shot_definition",
                            "title": "Shot Definition",
                            "body": "Use only the selected shot coverage for this clip.",
                            "source_artifact_types": ["shot_plan"],
                        }
                    ],
                    "covered_categories": ["shot_definition"],
                    "missing_inputs": [],
                    "operator_notes": ["Compiler received one render-clip prompt."],
                }
            ),
            {
                "model": kwargs["model"],
                "input_tokens": 120,
                "output_tokens": 80,
                "estimated_cost_usd": 0.004,
                "latency_seconds": 0.4,
                "request_id": f"compile-{len(compiler_prompts):03d}",
            },
        )

    monkeypatch.setattr(
        "cine_forge.modules.generation.render_adapter_v1.prompting.call_llm",
        _fake_call_llm,
    )
    video_request_count = 0

    def _fake_generate_video(*, request, engine_pack):
        nonlocal video_request_count
        video_request_count += 1
        return VideoGenerationResult(
            video_bytes=b"fake-mp4",
            media_type="video/mp4",
            model_used=engine_pack.target_model,
            request_id=f"video-{video_request_count:03d}",
            provider_job_id=f"job-{video_request_count:03d}",
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

    prompt_artifacts = [
        CompiledRenderPrompt.model_validate(artifact["data"])
        for artifact in result["artifacts"]
        if artifact["artifact_type"] == "render_prompt"
    ]

    assert len(compiler_prompts) == 4
    assert len(prompt_artifacts) == 4
    assert "FIRST ACTION ONLY" in compiler_prompts[0]
    assert "STEEL: FIRST ONLY." in compiler_prompts[0]
    assert "SECOND ACTION ONLY" not in compiler_prompts[0]
    assert "BRICK: SECOND ONLY." not in compiler_prompts[0]
    assert "THIRD ACTION ONLY" not in compiler_prompts[0]
    assert "FOURTH ACTION ONLY" not in compiler_prompts[0]
    assert "SECOND ACTION ONLY" in compiler_prompts[1]
    assert "BRICK: SECOND ONLY." in compiler_prompts[1]
    assert "FIRST ACTION ONLY" not in compiler_prompts[1]
    assert "STEEL: FIRST ONLY." not in compiler_prompts[1]
    assert "THIRD ACTION ONLY" in compiler_prompts[2]
    assert "STEEL: THIRD ONLY." in compiler_prompts[2]
    assert "FOURTH ACTION ONLY" not in compiler_prompts[2]
    assert "BRICK: FOURTH ONLY." not in compiler_prompts[2]
    assert "FOURTH ACTION ONLY" in compiler_prompts[3]
    assert "BRICK: FOURTH ONLY." in compiler_prompts[3]
    assert "THIRD ACTION ONLY" not in compiler_prompts[3]
    assert "STEEL: THIRD ONLY." not in compiler_prompts[3]
    assert [
        (artifact.render_unit, artifact.render_clip_id)
        for artifact in prompt_artifacts
    ] == [
        ("render_clip", f"{scene_id}_clip_001"),
        ("render_clip", f"{scene_id}_clip_002"),
        ("render_clip", f"{scene_id}_clip_003"),
        ("render_clip", f"{scene_id}_clip_004"),
    ]
    assert "STEEL: FIRST ONLY." in prompt_artifacts[0].prompt_text
    assert "BRICK: SECOND ONLY." not in prompt_artifacts[0].prompt_text
    assert "BRICK: SECOND ONLY." in prompt_artifacts[1].prompt_text
    assert "STEEL: FIRST ONLY." not in prompt_artifacts[1].prompt_text
    assert "STEEL: THIRD ONLY." in prompt_artifacts[2].prompt_text
    assert "BRICK: FOURTH ONLY." not in prompt_artifacts[2].prompt_text
    assert "BRICK: FOURTH ONLY." in prompt_artifacts[3].prompt_text
    assert "STEEL: THIRD ONLY." not in prompt_artifacts[3].prompt_text

    compiler_prompts.clear()
    selected_result = run_module(
        inputs=seeded["inputs"],
        params={
            "engine_pack_id": "openai_sora2",
            "compiler_model": "gpt-5.4-mini",
            "duration_seconds": 8,
        },
        context={
            "project_dir": str(seeded["project_dir"]),
            "runtime_params": {"render_clip_ids": [f"{scene_id}_clip_003"]},
        },
    )
    selected_prompt_artifacts = [
        CompiledRenderPrompt.model_validate(artifact["data"])
        for artifact in selected_result["artifacts"]
        if artifact["artifact_type"] == "render_prompt"
    ]
    selected_video_artifacts = [
        GeneratedVideoArtifact.model_validate(artifact["data"])
        for artifact in selected_result["artifacts"]
        if artifact["artifact_type"] == "generated_video"
    ]

    assert len(compiler_prompts) == 1
    assert "THIRD ACTION ONLY" in compiler_prompts[0]
    assert "FOURTH ACTION ONLY" not in compiler_prompts[0]
    assert [
        (artifact.render_unit, artifact.render_clip_id)
        for artifact in selected_prompt_artifacts
    ] == [("render_clip", f"{scene_id}_clip_003")]
    assert [
        (artifact.render_unit, artifact.render_clip_id)
        for artifact in selected_video_artifacts
    ] == [("render_clip", f"{scene_id}_clip_003")]


@pytest.mark.unit
def test_dialogue_prompt_contract_does_not_duplicate_quoted_speaker_lines(
    tmp_path: Path,
) -> None:
    seeded = seed_render_project(tmp_path)
    base_plan = ShotPlan.model_validate(seeded["inputs"]["shot_plan"][0])
    dialogue_lines = [
        "STEEL: Beer's ready!",
        "BRICK: Are they cold?",
        "STEEL: Does a bear crap in the woods?",
        "STEEL: To retirement.",
        "BRICK: To retirement.",
        "STEEL: Screw retirement.",
        "BRICK: Screw retirement.",
    ]
    shots = [
        base_plan.shots[0].model_copy(
            update={
                "shot_id": "scene_001_dialogue",
                "shot_size": "Two-shot",
                "dialogue_lines": dialogue_lines,
                "duration_estimate_seconds": 8.0,
            }
        )
    ]
    plan = base_plan.model_copy(
        update={"shots": shots, "total_estimated_duration_seconds": 8.0}
    )
    prompt_text = (
        'Live-action 8-second patio scene. Exact dialogue, spoken verbatim: '
        'STEEL: "Beer\'s ready!" BRICK: "Are they cold?" '
        'STEEL: "Does a bear crap in the woods?" STEEL: "To retirement." '
        'BRICK: "To retirement." STEEL: "Screw retirement." '
        'BRICK: "Screw retirement." Hold the silence after the toast.'
    )

    updated_prompt, notes = _ensure_dialogue_prompt_contract(
        prompt_text,
        plan,
        duration_seconds=8.0,
    )

    assert "Dialogue timing / exact lines:" not in updated_prompt
    assert updated_prompt.count("Beer's ready!") == 1
    assert updated_prompt.count("Screw retirement.") == 2
    assert "Dialogue cadence: This is dialogue-dense" in updated_prompt
    assert not any("compiler omitted" in note for note in notes)
    assert any("dense for the requested 8s render" in note for note in notes)


@pytest.mark.unit
def test_run_module_allows_advisory_missing_prompt_inputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seeded = seed_render_project(tmp_path, include_keyframe=False, include_scene_image=False)
    seeded["inputs"]["intent_mood"] = None
    seeded["inputs"]["look_and_feel"] = []
    seeded["inputs"]["character_bible"] = []
    seeded["inputs"]["location_bible"] = []
    bibles_dir = seeded["project_dir"] / "artifacts" / "bibles"
    if bibles_dir.exists():
        shutil.rmtree(bibles_dir)
    project_config = dict(seeded["inputs"]["project_config"])
    project_config["production_format"] = None
    seeded["inputs"]["project_config"] = project_config

    def _fake_call_llm(**kwargs):
        schema = kwargs["response_schema"]
        return (
            schema.model_validate(
                {
                    "prompt_text": (
                        "Render the lab confrontation as a measured push that stays anchored "
                        "to Mara's decision and the room's machine pressure."
                    ),
                    "sections": [
                        {
                            "section_id": "shot_definition",
                            "title": "Shot Definition",
                            "body": (
                                "Use the planned slow push and preserve the confrontation "
                                "geometry."
                            ),
                            "source_artifact_types": ["shot_plan"],
                        },
                        {
                            "section_id": "character_and_performance",
                            "title": "Character & Performance",
                            "body": "Keep Mara taut and Owen rigid as the room closes in.",
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
                        "Optional upstream render context is missing, so the prompt stays "
                        "tightly grounded in the shot plan."
                    ],
                }
            ),
            {
                "model": kwargs["model"],
                "input_tokens": 180,
                "output_tokens": 140,
                "estimated_cost_usd": 0.008,
                "latency_seconds": 0.7,
                "request_id": "compile-optional-001",
            },
        )

    monkeypatch.setattr(
        "cine_forge.modules.generation.render_adapter_v1.prompting.call_llm",
        _fake_call_llm,
    )
    monkeypatch.setattr(
        "cine_forge.modules.generation.render_adapter_v1.main.generate_video",
        lambda *, request, engine_pack: VideoGenerationResult(
            video_bytes=b"fake-mp4",
            media_type="video/mp4",
            model_used=engine_pack.target_model,
            request_id="video-optional-001",
            provider_job_id="job-optional-001",
        ),
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

    prompt_payload = next(
        artifact["data"]
        for artifact in result["artifacts"]
        if artifact["artifact_type"] == "render_prompt"
    )
    prompt_artifact = CompiledRenderPrompt.model_validate(prompt_payload)

    assert prompt_artifact.completeness.blocking_missing_categories == []
    assert prompt_artifact.completeness.advisory_missing_categories == [
        "character_bible_state",
        "creative_brief",
        "injected_assets",
        "keyframes",
        "location_bible_state",
        "look_and_feel",
        "rhythm_and_flow",
        "sound_and_music",
    ]
    assert prompt_artifact.completeness.missing_categories == (
        prompt_artifact.completeness.advisory_missing_categories
    )


@pytest.mark.unit
def test_run_module_synthesizes_required_character_state_when_compiler_omits_it(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seeded = seed_render_project(tmp_path, include_keyframe=False, include_scene_image=True)

    def _fake_call_llm(**kwargs):
        schema = kwargs["response_schema"]
        return (
            schema.model_validate(
                {
                    "prompt_text": (
                        "Render the lab confrontation as a measured push anchored to the shot "
                        "plan and the approved reference stack."
                    ),
                    "sections": [
                        {
                            "section_id": "shot_definition",
                            "title": "Shot Definition",
                            "body": "Preserve the planned slow push and room geometry.",
                            "source_artifact_types": ["shot_plan"],
                        },
                        {
                            "section_id": "location_bible_state",
                            "title": "Location State",
                            "body": "The lab is steel-blue, wet, and crowded with monitor banks.",
                            "source_artifact_types": ["location_bible", "bible_manifest"],
                        },
                        {
                            "section_id": "injected_assets",
                            "title": "Injected Assets",
                            "body": "Use the scene reference image as a secondary cue.",
                            "source_artifact_types": ["injected_asset_manifest"],
                        },
                    ],
                    "covered_categories": [
                        "shot_definition",
                        "location_bible_state",
                        "injected_assets",
                    ],
                    "missing_inputs": ["character_bible_state"],
                    "operator_notes": [
                        "Compiler omitted one required world-state section."
                    ],
                }
            ),
            {
                "model": kwargs["model"],
                "input_tokens": 160,
                "output_tokens": 110,
                "estimated_cost_usd": 0.007,
                "latency_seconds": 0.5,
                "request_id": "compile-fallback-001",
            },
        )

    monkeypatch.setattr(
        "cine_forge.modules.generation.render_adapter_v1.prompting.call_llm",
        _fake_call_llm,
    )
    monkeypatch.setattr(
        "cine_forge.modules.generation.render_adapter_v1.main.generate_video",
        lambda *, request, engine_pack: VideoGenerationResult(
            video_bytes=b"fake-mp4",
            media_type="video/mp4",
            model_used=engine_pack.target_model,
            request_id="video-fallback-001",
            provider_job_id="job-fallback-001",
        ),
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

    prompt_payload = next(
        artifact["data"]
        for artifact in result["artifacts"]
        if artifact["artifact_type"] == "render_prompt"
    )
    prompt_artifact = CompiledRenderPrompt.model_validate(prompt_payload)

    assert prompt_artifact.completeness.blocking_missing_categories == []
    assert "character_bible_state" in prompt_artifact.completeness.included_categories
    assert "character_bible_state" not in prompt_artifact.completeness.missing_categories
    assert any(
        note.startswith("Adapter synthesized fallback sections for:")
        for note in prompt_artifact.completeness.notes
    )
    synthesized_section = next(
        section
        for section in prompt_artifact.sections
        if section.section_id == "character_bible_state"
    )
    assert "MARA:" in synthesized_section.body


@pytest.mark.unit
def test_run_module_rejects_blocking_prompt_gaps(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seeded = seed_render_project(tmp_path, include_keyframe=False, include_scene_image=False)

    def _fake_call_llm(**kwargs):
        schema = kwargs["response_schema"]
        return (
            schema.model_validate(
                {
                    "prompt_text": "Render the scene from the shot plan only.",
                    "sections": [
                        {
                            "section_id": "shot_definition",
                            "title": "Shot Definition",
                            "body": "Use the planned hero shot.",
                            "source_artifact_types": ["shot_plan"],
                        }
                    ],
                    "covered_categories": ["shot_definition"],
                    "missing_inputs": ["provider_contract"],
                    "operator_notes": [],
                }
            ),
            {
                "model": kwargs["model"],
                "input_tokens": 120,
                "output_tokens": 80,
                "estimated_cost_usd": 0.004,
                "latency_seconds": 0.4,
                "request_id": "compile-blocking-001",
            },
        )

    monkeypatch.setattr(
        "cine_forge.modules.generation.render_adapter_v1.prompting.call_llm",
        _fake_call_llm,
    )
    monkeypatch.setattr(
        "cine_forge.modules.generation.render_adapter_v1.main.generate_video",
        lambda **_: pytest.fail("video generation should not start when blocking gaps remain"),
    )

    with pytest.raises(ValueError, match="provider_contract"):
        run_module(
            inputs=seeded["inputs"],
            params={
                "engine_pack_id": "openai_sora2",
                "compiler_model": "gpt-5.4-mini",
                "duration_seconds": 8,
            },
            context={"project_dir": str(seeded["project_dir"])},
        )


@pytest.mark.unit
def test_run_module_generates_ai_previz_artifacts_and_track_entries(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seeded = seed_render_project(tmp_path, include_keyframe=True, include_scene_image=True)

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
        context={
            "project_dir": str(seeded["project_dir"]),
            "runtime_params": {
                "scene_action_preflight": {
                    "recipe_id": "ai_previz_generation",
                    "recipe_name": "AI Previz",
                    "scene_scope": {
                        "mode": "current_scene",
                        "scene_ids": [seeded["scene_id"]],
                    },
                    "status": "warn",
                    "summary": "AI Previz can run for the current scene with warnings.",
                    "prerequisite_strategy": "one_pass_previz_prep",
                    "reused_artifact_types": ["track_manifest"],
                    "auto_build_artifact_types": ["timeline", "shot_plan"],
                    "missing_optional_artifact_types": ["look_and_feel", "sound_and_music"],
                    "items": [],
                }
            },
        },
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
    assert prompt_artifact.preview_provenance.prompt_profile == "standard"
    assert prompt_artifact.preview_provenance.prerequisite_strategy == "one_pass_previz_prep"
    assert prompt_artifact.preview_provenance.reused_artifact_types == ["track_manifest"]
    assert prompt_artifact.preview_provenance.auto_build_artifact_types == [
        "timeline",
        "shot_plan",
    ]
    assert prompt_artifact.preview_provenance.missing_optional_artifact_types == [
        "look_and_feel",
        "sound_and_music",
    ]
    assert "This is previs, not a final render." in prompt_artifact.prompt_text
    assert generated_video.prompt_ref.artifact_type == "ai_previz_prompt"
    assert generated_video.preview_provenance.mode == "ai_previz"
    assert generated_video.preview_provenance.prerequisite_strategy == "one_pass_previz_prep"
    assert (seeded["project_dir"] / generated_video.video.relative_path).exists()
    assert (
        best_for_scene(manifest, scene_id=seeded["scene_id"])["selected_track_type"]
        == "ai_previz_video"
    )


@pytest.mark.unit
def test_run_module_generates_clip_local_ai_previz_outputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seeded = seed_render_project(tmp_path, include_keyframe=False, include_scene_image=True)
    scene_id = seeded["scene_id"]
    base_plan = ShotPlan.model_validate(seeded["inputs"]["shot_plan"][0])
    first_shot = base_plan.shots[0].model_copy(
        update={
            "shot_id": "SCENE_001_A",
            "action_description": "FIRST PREVIZ ONLY: Steel enters with the beers.",
            "dialogue_lines": ["STEEL: FIRST PREVIZ ONLY."],
            "duration_estimate_seconds": 8.0,
        }
    )
    second_shot = base_plan.shots[0].model_copy(
        update={
            "shot_id": "SCENE_001_B",
            "action_description": "SECOND PREVIZ ONLY: Brick answers after the beat.",
            "dialogue_lines": ["BRICK: SECOND PREVIZ ONLY."],
            "duration_estimate_seconds": 8.0,
        }
    )
    seeded["inputs"]["shot_plan"] = [
        base_plan.model_copy(
            update={
                "shots": [first_shot, second_shot],
                "total_estimated_duration_seconds": 16.0,
            }
        ).model_dump(mode="json")
    ]
    shot_plan_ref = seeded["store"].list_versions("shot_plan", scene_id)[-1]
    render_clip_plan = RenderClipPlan.model_validate(
        {
            "scene_id": scene_id,
            "scene_number": base_plan.scene_number,
            "scene_heading": base_plan.scene_heading,
            "scene_ref": base_plan.scene_ref.model_dump(mode="json"),
            "shot_plan_ref": shot_plan_ref.model_dump(mode="json"),
            "selected_engine_pack_id": "google_veo31",
            "engine_max_clip_duration_seconds": 8.0,
            "target_dramatic_duration_seconds": 16.0,
            "duration_rationale": "Two beats need separate previz units.",
            "confidence": 0.84,
            "source": "ai",
            "provenance_mode": "shot_plan_ai",
            "planner_model": "gpt-5.4-mini",
            "missing_upstream_categories": [],
            "deterministic_lower_bound_seconds": 14.0,
            "clips": [
                {
                    "clip_id": f"{scene_id}_clip_001",
                    "scene_id": scene_id,
                    "source_shot_ids": ["SCENE_001_A"],
                    "start_time_seconds": 0.0,
                    "end_time_seconds": 8.0,
                    "target_duration_seconds": 8.0,
                    "dialogue_lines": ["STEEL: FIRST PREVIZ ONLY."],
                    "action_beats": ["FIRST PREVIZ ONLY: Steel enters with the beers."],
                    "continuity_end_notes": ["Steel has crossed to the chairs."],
                    "derivation": "shot_plan",
                    "rationale": "Opening movement and first line.",
                    "confidence": 0.9,
                },
                {
                    "clip_id": f"{scene_id}_clip_002",
                    "scene_id": scene_id,
                    "source_shot_ids": ["SCENE_001_B"],
                    "start_time_seconds": 8.0,
                    "end_time_seconds": 16.0,
                    "target_duration_seconds": 8.0,
                    "dialogue_lines": ["BRICK: SECOND PREVIZ ONLY."],
                    "action_beats": ["SECOND PREVIZ ONLY: Brick answers after the beat."],
                    "continuity_start_notes": ["Steel is already settled beside Brick."],
                    "derivation": "shot_plan",
                    "rationale": "Second beat and response.",
                    "confidence": 0.88,
                },
            ],
        }
    )
    seeded["inputs"]["render_clip_plan"] = [render_clip_plan.model_dump(mode="json")]
    video_prompts: list[str] = []

    monkeypatch.setattr(
        "cine_forge.modules.generation.render_adapter_v1.main.compile_render_prompt",
        lambda *args, **kwargs: pytest.fail(
            "render prompt compilation should not run for ai_previz mode"
        ),
    )

    def _fake_generate_video(*, request, engine_pack):
        video_prompts.append(request.prompt)
        return VideoGenerationResult(
            video_bytes=b"fake-mp4",
            media_type="video/mp4",
            model_used=engine_pack.target_model,
            request_id=f"previz-video-{len(video_prompts):03d}",
            provider_job_id=f"previz-job-{len(video_prompts):03d}",
        )

    monkeypatch.setattr(
        "cine_forge.modules.generation.render_adapter_v1.main.generate_video",
        _fake_generate_video,
    )

    result = run_module(
        inputs=seeded["inputs"],
        params={
            "prompt_mode": "ai_previz",
            "engine_pack_id": "xai_grok_imagine_video",
            "duration_seconds": 4,
            "resolution": "480p",
            "consistency_strategy": "prompt_only",
        },
        context={"project_dir": str(seeded["project_dir"])},
    )

    prompt_outputs = [
        artifact for artifact in result["artifacts"]
        if artifact["artifact_type"] == "ai_previz_prompt"
    ]
    video_outputs = [
        artifact for artifact in result["artifacts"]
        if artifact["artifact_type"] == "ai_previz_video"
    ]
    prompt_artifacts = [
        CompiledRenderPrompt.model_validate(artifact["data"])
        for artifact in prompt_outputs
    ]
    generated_videos = [
        GeneratedVideoArtifact.model_validate(artifact["data"])
        for artifact in video_outputs
    ]

    assert [artifact["entity_id"] for artifact in prompt_outputs] == [
        f"{scene_id}_clip_001",
        f"{scene_id}_clip_002",
    ]
    assert [artifact["entity_id"] for artifact in video_outputs] == [
        f"{scene_id}_clip_001",
        f"{scene_id}_clip_002",
    ]
    assert len(video_prompts) == 2
    assert "FIRST PREVIZ ONLY" in video_prompts[0]
    assert "SECOND PREVIZ ONLY" not in video_prompts[0]
    assert "SECOND PREVIZ ONLY" in video_prompts[1]
    assert "FIRST PREVIZ ONLY" not in video_prompts[1]
    assert [
        (artifact.render_unit, artifact.render_clip_id, artifact.source_shot_ids)
        for artifact in prompt_artifacts
    ] == [
        ("render_clip", f"{scene_id}_clip_001", ["SCENE_001_A"]),
        ("render_clip", f"{scene_id}_clip_002", ["SCENE_001_B"]),
    ]
    assert [
        (video.render_unit, video.render_clip_id, video.duration_seconds)
        for video in generated_videos
    ] == [
        ("render_clip", f"{scene_id}_clip_001", 8.0),
        ("render_clip", f"{scene_id}_clip_002", 8.0),
    ]

    video_prompts.clear()
    selected_result = run_module(
        inputs=seeded["inputs"],
        params={
            "prompt_mode": "ai_previz",
            "engine_pack_id": "xai_grok_imagine_video",
            "duration_seconds": 4,
            "resolution": "480p",
            "consistency_strategy": "prompt_only",
        },
        context={
            "project_dir": str(seeded["project_dir"]),
            "runtime_params": {"render_clip_ids": [f"{scene_id}_clip_002"]},
        },
    )
    selected_prompt_outputs = [
        artifact for artifact in selected_result["artifacts"]
        if artifact["artifact_type"] == "ai_previz_prompt"
    ]
    selected_video_outputs = [
        artifact for artifact in selected_result["artifacts"]
        if artifact["artifact_type"] == "ai_previz_video"
    ]

    assert [artifact["entity_id"] for artifact in selected_prompt_outputs] == [
        f"{scene_id}_clip_002"
    ]
    assert [artifact["entity_id"] for artifact in selected_video_outputs] == [
        f"{scene_id}_clip_002"
    ]
    assert len(video_prompts) == 1
    assert "SECOND PREVIZ ONLY" in video_prompts[0]
    assert "FIRST PREVIZ ONLY" not in video_prompts[0]


@pytest.mark.unit
def test_run_module_defaults_ai_previz_to_shipped_xai_lane(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seeded = seed_render_project(tmp_path, include_keyframe=True, include_scene_image=True)
    captured: dict[str, str] = {}

    monkeypatch.setattr(
        "cine_forge.modules.generation.render_adapter_v1.main.compile_render_prompt",
        lambda *args, **kwargs: pytest.fail(
            "render prompt compilation should not run for ai_previz mode"
        ),
    )
    monkeypatch.setattr(
        "cine_forge.modules.generation.render_adapter_v1.main.generate_video",
        lambda *, request, engine_pack: (
            captured.setdefault("engine_pack_id", engine_pack.pack_id),
            VideoGenerationResult(
                video_bytes=b"fake-mp4",
                media_type="video/mp4",
                model_used=engine_pack.target_model,
                request_id="previz-video-default-001",
                provider_job_id="previz-job-default-001",
            ),
        )[1],
    )

    result = run_module(
        inputs=seeded["inputs"],
        params={"prompt_mode": "ai_previz"},
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

    prompt_artifact = CompiledRenderPrompt.model_validate(prompt_payload)
    generated_video = GeneratedVideoArtifact.model_validate(video_payload)

    assert captured["engine_pack_id"] == "xai_grok_imagine_video"
    assert prompt_artifact.engine_pack_id == "xai_grok_imagine_video"
    assert generated_video.engine_pack_id == "xai_grok_imagine_video"


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


@pytest.mark.unit
def test_run_module_prefers_soft_locked_project_reference_for_openai_input_reference(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seeded = seed_render_project(tmp_path, include_keyframe=False, include_scene_image=False)
    bibles_dir = seeded["project_dir"] / "artifacts" / "bibles"
    if bibles_dir.exists():
        shutil.rmtree(bibles_dir)
    seeded["inputs"]["character_bible"] = []
    seeded["inputs"]["location_bible"] = []

    service = InjectedAssetService(seeded["project_dir"])
    service.inject_asset(
        target_kind="project",
        target_id="project",
        purpose="reference_image",
        filename="aaa_unlocked.jpg",
        content=reference_raster_bytes("Unlocked", accent=(148, 163, 184)),
        lock_status="unlocked",
        content_type="image/jpeg",
    )
    service.inject_asset(
        target_kind="project",
        target_id="project",
        purpose="mood_board",
        filename="zzz_soft_locked.jpg",
        content=reference_raster_bytes("Soft Locked", accent=(244, 114, 182)),
        lock_status="soft_locked",
        content_type="image/jpeg",
    )
    manifest, _ = service.load_manifest(target_kind="project", target_id="project")
    assert manifest is not None
    seeded["inputs"]["injected_asset_manifest"] = [manifest.model_dump(mode="json")]
    monkeypatch.setattr(
        "cine_forge.modules.generation.render_adapter_v1.main.generate_video",
        lambda *, request, engine_pack: VideoGenerationResult(
            video_bytes=b"fake-mp4",
            media_type="video/mp4",
            model_used=engine_pack.target_model,
            request_id="video-priority-001",
            provider_job_id="job-priority-001",
        ),
    )

    result = run_module(
        inputs=seeded["inputs"],
        params={"engine_pack_id": "openai_sora2", "compiler_model": "mock", "duration_seconds": 8},
        context={"project_dir": str(seeded["project_dir"])},
    )

    prompt_payload = next(
        artifact["data"]
        for artifact in result["artifacts"]
        if artifact["artifact_type"] == "render_prompt"
    )
    prompt_artifact = CompiledRenderPrompt.model_validate(prompt_payload)
    input_reference = next(
        item for item in prompt_artifact.resolved_inputs if item.used_as == "input_reference"
    )
    demoted = {
        item.label: item.used_as
        for item in prompt_artifact.resolved_inputs
        if item.label in {"Project: aaa_unlocked.jpg", "Project: zzz_soft_locked.jpg"}
    }

    assert input_reference.label == "Project: zzz_soft_locked.jpg"
    assert demoted["Project: aaa_unlocked.jpg"] == "prompt_context"


@pytest.mark.unit
def test_run_module_rejects_hard_locked_image_when_pack_cannot_honor_it(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seeded = seed_render_project(tmp_path, include_keyframe=True, include_scene_image=False)
    service = InjectedAssetService(seeded["project_dir"])
    service.inject_asset(
        target_kind="project",
        target_id="project",
        purpose="style_reference",
        filename="locked_style.jpg",
        content=reference_raster_bytes("Locked Style", accent=(250, 204, 21)),
        lock_status="hard_locked",
        content_type="image/jpeg",
    )
    manifest, _ = service.load_manifest(target_kind="project", target_id="project")
    assert manifest is not None
    seeded["inputs"]["injected_asset_manifest"] = [manifest.model_dump(mode="json")]

    monkeypatch.setattr(
        "cine_forge.modules.generation.render_adapter_v1.prompting.call_llm",
        lambda **_: pytest.fail(
            "prompt compilation should not start when hard-locked images cannot fit"
        ),
    )
    monkeypatch.setattr(
        "cine_forge.modules.generation.render_adapter_v1.main.generate_video",
        lambda **_: pytest.fail("video generation should not start when image constraints fail"),
    )

    with pytest.raises(ValueError, match="cannot satisfy required image constraints"):
        run_module(
            inputs=seeded["inputs"],
            params={"engine_pack_id": "openai_sora2", "duration_seconds": 8},
            context={"project_dir": str(seeded["project_dir"])},
        )


@pytest.mark.unit
def test_run_module_uses_reference_images_for_google_pack_without_keyframe_guidance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seeded = seed_render_project(
        tmp_path,
        include_keyframe=False,
        include_scene_image=True,
        include_project_taste_refs=True,
    )
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        "cine_forge.modules.generation.render_adapter_v1.main.generate_video",
        lambda *, request, engine_pack: (
            captured.setdefault("video_request", request),
            VideoGenerationResult(
                video_bytes=b"fake-mp4",
                media_type="video/mp4",
                model_used=engine_pack.target_model,
                request_id="video-google-001",
                provider_job_id="job-google-001",
            ),
        )[1],
    )

    result = run_module(
        inputs=seeded["inputs"],
        params={"engine_pack_id": "google_veo31", "compiler_model": "mock", "duration_seconds": 8},
        context={"project_dir": str(seeded["project_dir"])},
    )

    prompt_payload = next(
        artifact["data"]
        for artifact in result["artifacts"]
        if artifact["artifact_type"] == "render_prompt"
    )
    prompt_artifact = CompiledRenderPrompt.model_validate(prompt_payload)
    resolved = {item.label: item.used_as for item in prompt_artifact.resolved_inputs}

    assert prompt_artifact.creative_brief_preview is not None
    assert {
        (reference.filename, reference.purpose)
        for reference in prompt_artifact.creative_brief_preview.active_project_references
    } == {
        ("mood_board.jpg", "mood_board"),
        ("style_reference.jpg", "style_reference"),
    }
    request = captured["video_request"]
    assert request.first_frame is None
    assert request.last_frame is None
    assert len(request.reference_images) == 3
    assert request.reference_images[0].usage == "reference_image"
    assert resolved["Character visual reference: mara"] == "reference_image"
    assert resolved["Location visual reference: LAB"] == "reference_image"


@pytest.mark.unit
def test_run_module_keeps_google_reference_images_prompt_only_when_keyframe_guidance_exists(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seeded = seed_render_project(
        tmp_path,
        include_keyframe=True,
        include_scene_image=True,
        include_project_taste_refs=True,
    )
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        "cine_forge.modules.generation.render_adapter_v1.main.generate_video",
        lambda *, request, engine_pack: (
            captured.setdefault("video_request", request),
            VideoGenerationResult(
                video_bytes=b"fake-mp4",
                media_type="video/mp4",
                model_used=engine_pack.target_model,
                request_id="video-google-002",
                provider_job_id="job-google-002",
            ),
        )[1],
    )

    result = run_module(
        inputs=seeded["inputs"],
        params={"engine_pack_id": "google_veo31", "compiler_model": "mock", "duration_seconds": 8},
        context={"project_dir": str(seeded["project_dir"])},
    )

    prompt_payload = next(
        artifact["data"]
        for artifact in result["artifacts"]
        if artifact["artifact_type"] == "render_prompt"
    )
    prompt_artifact = CompiledRenderPrompt.model_validate(prompt_payload)
    resolved = {item.label: item.used_as for item in prompt_artifact.resolved_inputs}

    request = captured["video_request"]
    assert request.first_frame is not None
    assert request.reference_images == []
    assert resolved["Character visual reference: mara"] == "prompt_context"
    assert resolved["Location visual reference: LAB"] == "prompt_context"
    assert any(
        "mixing frame guidance with extra reference images" in note
        for note in prompt_artifact.completeness.notes
    )
