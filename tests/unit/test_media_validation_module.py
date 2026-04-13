from __future__ import annotations

import copy
import shutil
from pathlib import Path

import pytest

from cine_forge.modules.qa.media_validation_v1.main import _generated_videos, run_module
from cine_forge.schemas import (
    ArtifactHealth,
    ArtifactMetadata,
    ArtifactRef,
    MediaValidationArtifact,
    SemanticMediaReview,
)
from tests.render_fixtures import seed_final_output_project, seed_generated_video_project


@pytest.mark.unit
def test_run_module_validates_generated_video_with_real_clip(tmp_path: Path) -> None:
    seeded = seed_generated_video_project(tmp_path)

    result = run_module(
        inputs={"generated_video": [seeded["generated_video"].model_dump(mode="json")]},
        params={"sample_count": 3},
        context={"project_dir": str(seeded["project_dir"])},
    )

    payload = result["artifacts"][0]["data"]
    artifact = MediaValidationArtifact.model_validate(payload)

    assert artifact.target_ref.artifact_type == "generated_video"
    assert artifact.target.scope_kind == "scene"
    assert artifact.target.scene_id == seeded["scene_id"]
    assert artifact.deterministic_probe.decode_succeeded is True
    assert artifact.deterministic_probe.video_stream_present is True
    assert artifact.deterministic_probe.sample_count_extracted == 3
    assert len(artifact.deterministic_probe.sample_frames) == 3
    assert artifact.semantic_review.status == "skipped"
    assert artifact.recommended_health == ArtifactHealth.NEEDS_REVIEW


@pytest.mark.unit
def test_run_module_can_mark_clean_clip_valid_when_semantic_review_passes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seeded = seed_generated_video_project(tmp_path)

    monkeypatch.setattr(
        "cine_forge.modules.qa.media_validation_v1.main.review_sampled_frames",
        lambda **_: SemanticMediaReview(
            status="pass",
            mode="sampled_frames",
            model="gpt-5.4",
            summary="Sampled frames are coherent and production-usable.",
            confidence=0.92,
            findings=[],
        ),
    )

    result = run_module(
        inputs={"generated_video": [seeded["generated_video"].model_dump(mode="json")]},
        params={"sample_count": 2, "semantic_review_model": "gpt-5.4"},
        context={"project_dir": str(seeded["project_dir"])},
    )

    artifact = MediaValidationArtifact.model_validate(result["artifacts"][0]["data"])
    assert artifact.semantic_review.status == "pass"
    assert artifact.recommended_health == ArtifactHealth.VALID


@pytest.mark.unit
def test_run_module_can_target_ai_previz_video_refs(tmp_path: Path) -> None:
    seeded = seed_generated_video_project(tmp_path)
    store = seeded["store"]
    ai_previz_ref = store.save_artifact(
        artifact_type="ai_previz_video",
        entity_id=seeded["scene_id"],
        data=seeded["generated_video"].model_dump(mode="json"),
        metadata=ArtifactMetadata(
            lineage=[seeded["generated_video_ref"], seeded["prompt_ref"]],
            intent="seed ai previz video",
            rationale="target override coverage",
            confidence=1.0,
            source="code",
            producing_module="tests.unit",
        ),
    )

    result = run_module(
        inputs={"generated_video": [seeded["generated_video"].model_dump(mode="json")]},
        params={"sample_count": 2, "target_artifact_type": "ai_previz_video"},
        context={"project_dir": str(seeded["project_dir"])},
    )

    artifact = MediaValidationArtifact.model_validate(result["artifacts"][0]["data"])
    assert artifact.target_ref.artifact_type == "ai_previz_video"
    assert artifact.target_ref.version == ai_previz_ref.version
    assert artifact.target.scope_kind == "scene"


@pytest.mark.unit
def test_generated_video_selection_respects_scene_scope(tmp_path: Path) -> None:
    seeded = seed_generated_video_project(tmp_path)
    scene_one = seeded["generated_video"].model_dump(mode="json")
    scene_two = copy.deepcopy(scene_one)
    scene_two["scene_id"] = "scene_002"
    scene_two["scene_number"] = 2
    scene_two["scene_heading"] = "EXT. ROOF - DAWN"

    artifacts = _generated_videos(
        {"generated_video": [scene_one, scene_two]},
        runtime_params={"scene_scope": {"mode": "current_scene", "scene_ids": ["scene_002"]}},
    )

    assert [artifact.scene_id for artifact in artifacts] == ["scene_002"]


@pytest.mark.unit
def test_run_module_marks_missing_media_as_needing_revision(tmp_path: Path) -> None:
    seeded = seed_generated_video_project(tmp_path)
    media_path = seeded["project_dir"] / seeded["generated_video"].video.relative_path
    media_path.unlink()

    result = run_module(
        inputs={"generated_video": [seeded["generated_video"].model_dump(mode="json")]},
        params={"sample_count": 2},
        context={"project_dir": str(seeded["project_dir"])},
    )

    artifact = MediaValidationArtifact.model_validate(result["artifacts"][0]["data"])
    assert artifact.recommended_health == ArtifactHealth.NEEDS_REVISION
    assert artifact.deterministic_probe.findings[0].code == "missing_file"


@pytest.mark.unit
def test_run_module_keeps_decodable_clip_reviewable_when_ffprobe_is_unavailable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seeded = seed_generated_video_project(tmp_path)
    ffmpeg_path = shutil.which("ffmpeg")
    assert ffmpeg_path is not None

    def fake_which(name: str) -> str | None:
        if name == "ffprobe":
            return None
        if name == "ffmpeg":
            return ffmpeg_path
        return shutil.which(name)

    monkeypatch.setattr(
        "cine_forge.modules.qa.media_validation_v1.probe.shutil.which",
        fake_which,
    )

    result = run_module(
        inputs={"generated_video": [seeded["generated_video"].model_dump(mode="json")]},
        params={"sample_count": 3},
        context={"project_dir": str(seeded["project_dir"])},
    )

    artifact = MediaValidationArtifact.model_validate(result["artifacts"][0]["data"])
    finding_codes = {finding.code for finding in artifact.deterministic_probe.findings}

    assert artifact.recommended_health == ArtifactHealth.NEEDS_REVIEW
    assert artifact.deterministic_probe.decode_succeeded is True
    assert artifact.deterministic_probe.video_stream_present is True
    assert artifact.deterministic_probe.sample_count_extracted == 3
    assert "ffprobe_unavailable" in finding_codes
    assert "missing_video_stream" not in finding_codes


@pytest.mark.unit
def test_run_module_normalizes_semantic_review_severity_synonyms(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seeded = seed_generated_video_project(tmp_path)

    monkeypatch.setattr(
        "cine_forge.modules.qa.media_validation_v1.semantic_review._call_multimodal_reviewer",
        lambda **_: (
            {
                "verdict": "needs_review",
                "summary": "The clip has a visible continuity concern.",
                "confidence": "medium",
                "findings": [
                    {
                        "code": "continuity_break",
                        "severity": "blocking",
                        "message": "The folder changes color across the cut.",
                        "frame_index": 1,
                    },
                    {
                        "code": "staging_softness",
                        "severity": "minor",
                        "message": "The staging reads slightly ambiguous.",
                        "frame_index": 2,
                    },
                ],
            },
            {
                "model": "gpt-5.4",
                "input_tokens": 100,
                "output_tokens": 50,
                "estimated_cost_usd": 0.001,
            },
        ),
    )

    result = run_module(
        inputs={"generated_video": [seeded["generated_video"].model_dump(mode="json")]},
        params={"sample_count": 3, "semantic_review_model": "gpt-5.4"},
        context={"project_dir": str(seeded["project_dir"])},
    )

    artifact = MediaValidationArtifact.model_validate(result["artifacts"][0]["data"])

    assert artifact.semantic_review.status == "needs_review"
    assert artifact.semantic_review.confidence == pytest.approx(0.65)
    assert [finding.severity for finding in artifact.semantic_review.findings] == [
        "error",
        "warning",
    ]


@pytest.mark.unit
def test_run_module_can_validate_final_output_project_cut(tmp_path: Path) -> None:
    workspace_root = Path(__file__).resolve().parents[2]
    seeded = seed_final_output_project(tmp_path, rendered_scene_ids=["scene_001", "scene_002"])
    from cine_forge.driver.engine import DriverEngine

    engine = DriverEngine(workspace_root=workspace_root, project_dir=seeded["project_dir"])
    run_state = engine.run(
        recipe_path=workspace_root / "configs" / "recipes" / "recipe-final-output.yaml",
        run_id="unit-final-output-seed",
        end_at="final_output",
        force=True,
    )
    final_output_ref = ArtifactRef.model_validate(
        run_state["stages"]["final_output"]["artifact_refs"][0]
    )
    final_output_artifact = engine.store.load_artifact(final_output_ref).data

    result = run_module(
        inputs={"final_output": final_output_artifact},
        params={"sample_count": 2, "target_artifact_type": "final_output"},
        context={"project_dir": str(seeded["project_dir"])},
    )

    artifact = MediaValidationArtifact.model_validate(result["artifacts"][0]["data"])

    assert artifact.target.scope_kind == "project"
    assert artifact.target.label == "Project final output"
    assert artifact.target.coverage_state == "complete"
    assert artifact.target.included_scene_count == 2
    assert artifact.target.omitted_scene_count == 0
    assert artifact.target_ref.artifact_type == "final_output"
    assert artifact.target_ref.entity_id == "project"
    assert artifact.validated_media.relative_path.endswith("final_output.mp4")
    assert artifact.deterministic_probe.decode_succeeded is True
    assert artifact.semantic_review.status == "skipped"


@pytest.mark.unit
def test_run_module_records_partial_final_output_coverage_in_project_scope(
    tmp_path: Path,
) -> None:
    workspace_root = Path(__file__).resolve().parents[2]
    seeded = seed_final_output_project(tmp_path, rendered_scene_ids=["scene_001"])
    from cine_forge.driver.engine import DriverEngine

    engine = DriverEngine(workspace_root=workspace_root, project_dir=seeded["project_dir"])
    run_state = engine.run(
        recipe_path=workspace_root / "configs" / "recipes" / "recipe-final-output.yaml",
        run_id="unit-final-output-partial-seed",
        end_at="final_output",
        force=True,
    )
    final_output_ref = ArtifactRef.model_validate(
        run_state["stages"]["final_output"]["artifact_refs"][0]
    )
    final_output_artifact = engine.store.load_artifact(final_output_ref).data

    result = run_module(
        inputs={"final_output": final_output_artifact},
        params={"sample_count": 2, "target_artifact_type": "final_output"},
        context={"project_dir": str(seeded["project_dir"])},
    )

    artifact = MediaValidationArtifact.model_validate(result["artifacts"][0]["data"])

    assert artifact.target.scope_kind == "project"
    assert artifact.target.coverage_state == "partial"
    assert artifact.target.included_scene_count == 1
    assert artifact.target.omitted_scene_count == 1
