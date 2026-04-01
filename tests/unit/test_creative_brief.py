from __future__ import annotations

import pytest

from cine_forge.schemas import InjectedAssetManifest
from cine_forge.services.creative_brief import (
    build_visual_creative_brief,
    creative_brief_source_artifact_types,
)


def _project_manifest() -> InjectedAssetManifest:
    return InjectedAssetManifest.model_validate(
        {
            "target_kind": "project",
            "target_id": "project",
            "display_name": "Project",
            "version": 1,
            "assets": [
                {
                    "asset_id": "asset-1",
                    "filename": "storm_palette_board.jpg",
                    "asset_type": "image",
                    "purpose": "mood_board",
                    "entity_type": None,
                    "entity_id": None,
                    "lock_status": "soft_locked",
                    "file_path": "artifacts/injected/project/storm_palette_board.jpg",
                    "file_size_bytes": 120,
                    "content_type": "image/jpeg",
                    "thumbnail_path": None,
                    "waveform_path": None,
                    "duration_seconds": None,
                    "width": None,
                    "height": None,
                    "tags": [],
                    "extra_metadata": {},
                },
                {
                    "asset_id": "asset-2",
                    "filename": "temp_score.wav",
                    "asset_type": "audio",
                    "purpose": "temp_score",
                    "entity_type": None,
                    "entity_id": None,
                    "lock_status": "hard_locked",
                    "file_path": "artifacts/injected/project/temp_score.wav",
                    "file_size_bytes": 120,
                    "content_type": "audio/wav",
                    "thumbnail_path": None,
                    "waveform_path": None,
                    "duration_seconds": 1.0,
                    "width": None,
                    "height": None,
                    "tags": [],
                    "extra_metadata": {},
                },
            ],
        }
    )


@pytest.mark.unit
def test_build_visual_creative_brief_returns_none_without_inputs() -> None:
    assert (
        build_visual_creative_brief(
            project_config_data=None,
            intent_mood_data=None,
            project_manifest=None,
        )
        is None
    )


@pytest.mark.unit
def test_build_visual_creative_brief_compiles_taste_inputs_and_project_references() -> None:
    brief = build_visual_creative_brief(
        project_config_data={"production_format": "animation_3d"},
        intent_mood_data={
            "scope": "project",
            "mood_descriptors": ["lonely", "ominous"],
            "reference_films": ["The Lighthouse"],
            "filmmaker_anchors": ["Robert Eggers"],
            "style_preset_id": "gothic-horror",
            "natural_language_intent": "Make the world feel ancient and judging.",
            "look_notes": "Salt-crusted textures and cold cyan drift.",
        },
        project_manifest=_project_manifest(),
    )

    assert brief is not None
    assert brief.visual_medium == "animation_3d"
    assert brief.filmmaker_anchors == ["Robert Eggers"]
    assert brief.sources_used == ["project_config", "intent_mood", "project_references"]
    assert len(brief.active_project_references) == 1
    assert brief.active_project_references[0].filename == "storm_palette_board.jpg"
    assert "Project reference cue:" in brief.summary_lines[-1]
    assert creative_brief_source_artifact_types(brief) == [
        "project_config",
        "intent_mood",
        "injected_asset_manifest",
    ]
