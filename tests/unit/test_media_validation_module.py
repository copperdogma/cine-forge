from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from cine_forge.modules.qa.media_validation_v1.main import run_module
from cine_forge.schemas import ArtifactHealth, MediaValidationArtifact, SemanticMediaReview
from tests.render_fixtures import seed_generated_video_project


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
                "confidence": 0.81,
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
    assert [finding.severity for finding in artifact.semantic_review.findings] == [
        "error",
        "warning",
    ]
