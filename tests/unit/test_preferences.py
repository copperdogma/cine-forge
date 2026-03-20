"""Unit tests for transparent preference-learning aggregation."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from cine_forge.services.preferences import PreferenceService


def _project_dir(tmp_path: Path) -> Path:
    project_dir = tmp_path / "project"
    project_dir.mkdir(parents=True, exist_ok=True)
    return project_dir


@pytest.mark.unit
def test_preference_profile_reduces_to_latest_active_signal_per_image(tmp_path: Path) -> None:
    project_dir = _project_dir(tmp_path)
    service = PreferenceService(project_dir)

    service.record_design_study_signal(
        entity_id="character_mariner",
        entity_type="character",
        round_number=1,
        image_filename="img1.jpg",
        decision="favorite",
        guidance=None,
        round_guidance="older, storm-beaten face",
        prompt_used="test prompt",
        prompt_sources_used=["entity_bible"],
        model="mock",
    )
    service.record_design_study_signal(
        entity_id="character_mariner",
        entity_type="character",
        round_number=1,
        image_filename="img1.jpg",
        decision="pending",
        guidance=None,
        round_guidance="older, storm-beaten face",
        prompt_used="test prompt",
        prompt_sources_used=["entity_bible"],
        model="mock",
    )
    service.record_design_study_signal(
        entity_id="character_mariner",
        entity_type="character",
        round_number=1,
        image_filename="img2.jpg",
        decision="rejected",
        guidance="too polished",
        round_guidance=None,
        prompt_used="test prompt",
        prompt_sources_used=["entity_bible"],
        model="mock",
    )
    service.record_design_study_signal(
        entity_id="character_mariner",
        entity_type="character",
        round_number=1,
        image_filename="img3.jpg",
        decision="seed_for_variants",
        guidance="more weathered, darker costume",
        round_guidance=None,
        prompt_used="test prompt",
        prompt_sources_used=["entity_bible"],
        model="mock",
    )

    profile = service.build_profile()

    assert profile.active_signal_count == 2
    assert [signal.decision for signal in profile.recent_signals] == [
        "seed_for_variants",
        "rejected",
    ]
    assert profile.preferred_cues == []
    assert profile.avoid_cues[0].text == "too polished"
    assert profile.variation_cues[0].text == "more weathered, darker costume"


@pytest.mark.unit
def test_preference_profile_respects_project_clear_timestamp(tmp_path: Path) -> None:
    project_dir = _project_dir(tmp_path)
    service = PreferenceService(project_dir)

    service.record_design_study_signal(
        entity_id="character_mariner",
        entity_type="character",
        round_number=1,
        image_filename="img1.jpg",
        decision="selected_final",
        guidance=None,
        round_guidance="older, storm-beaten face",
        prompt_used="test prompt",
        prompt_sources_used=["entity_bible"],
        model="mock",
    )

    (project_dir / "project.json").write_text(
        json.dumps(
            {"preference_learning_cleared_at": datetime.now(UTC).isoformat()},
            indent=2,
        ),
        encoding="utf-8",
    )

    profile = service.build_profile()
    assert profile.active_signal_count == 0
    assert profile.summary_lines == ["No active learned preferences yet."]


@pytest.mark.unit
def test_preference_prompt_context_uses_positive_negative_and_variation_signals(
    tmp_path: Path,
) -> None:
    project_dir = _project_dir(tmp_path)
    service = PreferenceService(project_dir)

    service.record_design_study_signal(
        entity_id="character_mariner",
        entity_type="character",
        round_number=1,
        image_filename="img1.jpg",
        decision="selected_final",
        guidance=None,
        round_guidance="older, storm-beaten face",
        prompt_used="test prompt",
        prompt_sources_used=["entity_bible"],
        model="mock",
    )
    service.record_design_study_signal(
        entity_id="character_mariner",
        entity_type="character",
        round_number=1,
        image_filename="img2.jpg",
        decision="rejected",
        guidance="too polished",
        round_guidance=None,
        prompt_used="test prompt",
        prompt_sources_used=["entity_bible"],
        model="mock",
    )
    service.record_design_study_signal(
        entity_id="character_mariner",
        entity_type="character",
        round_number=1,
        image_filename="img3.jpg",
        decision="seed_for_variants",
        guidance="more weathered, darker costume",
        round_guidance=None,
        prompt_used="test prompt",
        prompt_sources_used=["entity_bible"],
        model="mock",
    )

    lines = service.build_prompt_context_for_entity(
        entity_id="character_mariner",
        entity_type="character",
    )

    assert any("older, storm-beaten face" in line for line in lines)
    assert any("more weathered, darker costume" in line for line in lines)
    assert any("too polished" in line for line in lines)
