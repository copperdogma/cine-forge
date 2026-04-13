from __future__ import annotations

import pytest

from cine_forge.schemas import (
    ArtifactRef,
    FinalOutputArtifact,
    FinalOutputIncludedScene,
    FinalOutputOmittedScene,
    MediaFile,
)


def _ref(artifact_type: str, entity_id: str, version: int) -> ArtifactRef:
    return ArtifactRef(
        artifact_type=artifact_type,
        entity_id=entity_id,
        version=version,
        path=f"artifacts/{artifact_type}/{entity_id}/v{version}.json",
    )


@pytest.mark.unit
def test_complete_final_output_rejects_omitted_scenes() -> None:
    with pytest.raises(ValueError, match="complete coverage cannot include omitted scenes"):
        FinalOutputArtifact(
            timeline_ref=_ref("timeline", "project", 1),
            track_manifest_ref=_ref("track_manifest", "project", 2),
            video=MediaFile(
                relative_path="artifacts/final_output_media/project/v1/final_output.mp4",
                media_type="video/mp4",
            ),
            coverage_state="complete",
            total_scene_count=2,
            included_scene_ids=["scene_001"],
            omitted_scene_ids=["scene_002"],
            included_scenes=[
                FinalOutputIncludedScene(
                    scene_id="scene_001",
                    scene_number=1,
                    scene_heading="INT. LAB - NIGHT",
                    generated_video_ref=_ref("generated_video", "scene_001", 1),
                    clip_relative_path="artifacts/generated_video_media/scene_001/v1/scene_render.mp4",
                    duration_seconds=4.0,
                    output_start_seconds=0.0,
                    output_end_seconds=4.0,
                )
            ],
            omitted_scenes=[
                FinalOutputOmittedScene(
                    scene_id="scene_002",
                    scene_number=2,
                    scene_heading="EXT. ROOF - DAWN",
                    reason="missing_generated_video_track",
                )
            ],
        )


@pytest.mark.unit
def test_partial_final_output_requires_omission_list() -> None:
    with pytest.raises(
        ValueError, match="partial coverage must include at least one omitted scene"
    ):
        FinalOutputArtifact(
            timeline_ref=_ref("timeline", "project", 1),
            track_manifest_ref=_ref("track_manifest", "project", 2),
            video=MediaFile(
                relative_path="artifacts/final_output_media/project/v1/final_output.mp4",
                media_type="video/mp4",
            ),
            coverage_state="partial",
            total_scene_count=1,
            included_scene_ids=["scene_001"],
            omitted_scene_ids=[],
            included_scenes=[
                FinalOutputIncludedScene(
                    scene_id="scene_001",
                    scene_number=1,
                    scene_heading="INT. LAB - NIGHT",
                    generated_video_ref=_ref("generated_video", "scene_001", 1),
                    clip_relative_path="artifacts/generated_video_media/scene_001/v1/scene_render.mp4",
                    duration_seconds=4.0,
                    output_start_seconds=0.0,
                    output_end_seconds=4.0,
                )
            ],
            omitted_scenes=[],
        )


@pytest.mark.unit
def test_scene_id_lists_must_match_embedded_scene_order() -> None:
    with pytest.raises(ValueError, match="included_scene_ids must match included_scenes ordering"):
        FinalOutputArtifact(
            timeline_ref=_ref("timeline", "project", 1),
            track_manifest_ref=_ref("track_manifest", "project", 2),
            video=MediaFile(
                relative_path="artifacts/final_output_media/project/v1/final_output.mp4",
                media_type="video/mp4",
            ),
            coverage_state="complete",
            total_scene_count=1,
            included_scene_ids=["scene_999"],
            omitted_scene_ids=[],
            included_scenes=[
                FinalOutputIncludedScene(
                    scene_id="scene_001",
                    scene_number=1,
                    scene_heading="INT. LAB - NIGHT",
                    generated_video_ref=_ref("generated_video", "scene_001", 1),
                    clip_relative_path="artifacts/generated_video_media/scene_001/v1/scene_render.mp4",
                    duration_seconds=4.0,
                    output_start_seconds=0.0,
                    output_end_seconds=4.0,
                )
            ],
            omitted_scenes=[],
        )
