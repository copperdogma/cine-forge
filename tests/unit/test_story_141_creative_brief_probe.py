"""Regression tests for the deterministic Story 141 probe contract."""

from __future__ import annotations

import sys

import pytest
from scripts import story_141_creative_brief_probe
from scripts.story_141_creative_brief_probe_support import (
    deterministic_lane_verdict,
    project_fixture,
)

pytestmark = pytest.mark.unit


def test_story_141_probe_defaults_to_no_paid_judge(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["story_141_creative_brief_probe.py"])

    args = story_141_creative_brief_probe._parse_args()

    assert args.run_judge is False


def test_story_141_probe_requires_explicit_paid_judge_opt_in(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["story_141_creative_brief_probe.py", "--run-judge"],
    )

    args = story_141_creative_brief_probe._parse_args()

    assert args.run_judge is True


def test_story_141_signal_contract_discriminates_legacy_from_complete_prompt() -> None:
    new_prompt = " ".join(
        [
            "Animation 3D",
            "Lonely and ominous",
            "The Lighthouse",
            "Robert Eggers",
            "Salt-crusted wardrobe with a cold cyan palette",
            "storm_palette_board.jpg",
            "filename/purpose only",
            "hard monitor highlights in steel blue",
        ]
    )

    verdict = deterministic_lane_verdict("Animation 3D", new_prompt)

    assert verdict["pass"] is True
    assert verdict["missing_new_signals"] == []
    assert "filmmaker_anchor" in verdict["improvements_over_legacy"]


def test_story_141_signal_contract_rejects_missing_new_signal() -> None:
    verdict = deterministic_lane_verdict(
        "Animation 3D",
        "Animation 3D The Lighthouse Robert Eggers storm_palette_board.jpg",
    )

    assert verdict["pass"] is False
    assert "mood_descriptors" in verdict["missing_new_signals"]
    assert "look_notes" in verdict["missing_new_signals"]
    assert "reference_transparency" in verdict["missing_new_signals"]


def test_story_141_fixture_keeps_taste_sources_explicit() -> None:
    project_config, intent_mood = project_fixture()

    assert project_config["production_format"] == "animation_3d"
    assert intent_mood["reference_films"] == ["The Lighthouse"]
    assert intent_mood["filmmaker_anchors"] == ["Robert Eggers"]
    assert "Salt-crusted" in intent_mood["look_notes"]
