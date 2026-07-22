"""Unit tests for the script_bible_v1 module."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

import cine_forge.modules.ingest.script_bible_v1.main as script_bible_main
from cine_forge.modules.ingest.script_bible_v1.main import run_module
from cine_forge.schemas import ScriptBible

MODULE_MANIFEST = Path(script_bible_main.__file__).with_name("module.yaml")


def _canonical_script(text: str) -> dict[str, Any]:
    return {
        "title": "Test Script",
        "script_text": text,
        "line_count": text.count("\n") + 1,
        "scene_count": 1,
        "normalization": {
            "source_format": "screenplay",
            "strategy": "passthrough_cleanup",
            "inventions": [],
            "assumptions": [],
            "overall_confidence": 0.9,
            "rationale": "fixture",
        },
    }


SAMPLE_SCRIPT = """\
Title: The Test
    A test about testing.

FADE IN:

INT. LABORATORY - NIGHT

A scientist works alone. Equipment hums.

SCIENTIST
We need to test everything.

EXT. STREET - DAY

The scientist steps outside. Sunlight blinds.

SCIENTIST
The test is complete.

FADE OUT.
"""


@pytest.mark.unit
def test_mock_produces_valid_script_bible() -> None:
    """Mock model returns a structurally valid ScriptBible artifact."""
    result = run_module(
        inputs={"normalize": _canonical_script(SAMPLE_SCRIPT)},
        params={"work_model": "mock"},
        context={"run_id": "unit", "stage_id": "script_bible", "runtime_params": {}},
    )
    assert "artifacts" in result
    assert len(result["artifacts"]) == 1

    artifact = result["artifacts"][0]
    assert artifact["artifact_type"] == "script_bible"
    assert artifact["entity_id"] == "project"

    # Validate data against schema
    bible = ScriptBible.model_validate(artifact["data"])
    assert bible.title
    assert bible.logline
    assert bible.synopsis
    assert len(bible.act_structure) >= 1
    assert len(bible.themes) >= 1
    assert 0.0 <= bible.confidence <= 1.0


@pytest.mark.unit
def test_mock_metadata_fields() -> None:
    """Artifact metadata includes expected fields."""
    result = run_module(
        inputs={"normalize": _canonical_script(SAMPLE_SCRIPT)},
        params={"work_model": "mock"},
        context={"run_id": "unit", "stage_id": "script_bible", "runtime_params": {}},
    )
    meta = result["artifacts"][0]["metadata"]
    assert meta["source"] == "ai"
    assert meta["health"] == "valid"
    assert "intent" in meta
    assert "rationale" in meta


@pytest.mark.unit
def test_cost_returned() -> None:
    """Module returns a cost dict."""
    result = run_module(
        inputs={"normalize": _canonical_script(SAMPLE_SCRIPT)},
        params={"work_model": "mock"},
        context={"run_id": "unit", "stage_id": "script_bible", "runtime_params": {}},
    )
    assert "cost" in result
    assert result["cost"]["model"] == "mock"
    assert result["cost"]["estimated_cost_usd"] == 0.0


@pytest.mark.unit
def test_announce_artifact_called() -> None:
    """announce_artifact callback is invoked with the bible artifact."""
    announced: list[dict[str, Any]] = []
    run_module(
        inputs={"normalize": _canonical_script(SAMPLE_SCRIPT)},
        params={"work_model": "mock"},
        context={
            "run_id": "unit",
            "stage_id": "script_bible",
            "runtime_params": {},
            "announce_artifact": lambda a: announced.append(a),
        },
    )
    assert len(announced) == 1
    assert announced[0]["artifact_type"] == "script_bible"


@pytest.mark.unit
def test_empty_script_raises() -> None:
    """Empty script text should raise ValueError."""
    with pytest.raises(ValueError, match="non-empty"):
        run_module(
            inputs={"normalize": {"script_text": ""}},
            params={"work_model": "mock"},
            context={"run_id": "unit", "stage_id": "script_bible", "runtime_params": {}},
        )


@pytest.mark.unit
def test_missing_input_raises() -> None:
    """Missing input should raise ValueError."""
    with pytest.raises(ValueError, match="requires upstream"):
        run_module(
            inputs={},
            params={"work_model": "mock"},
            context={"run_id": "unit", "stage_id": "script_bible", "runtime_params": {}},
        )


@pytest.mark.unit
def test_schema_validation_round_trip() -> None:
    """ScriptBible schema validates and round-trips correctly."""
    data = {
        "title": "Test Film",
        "logline": "A test about testing things.",
        "synopsis": "Two paragraphs of synopsis.\n\nSecond paragraph.",
        "act_structure": [
            {
                "act_number": 1,
                "title": "Setup",
                "start_scene": "INT. ROOM - DAY",
                "end_scene": "EXT. PARK - NIGHT",
                "summary": "The story begins.",
                "turning_points": ["Discovery", "Commitment"],
            },
            {
                "act_number": 2,
                "title": "Confrontation",
                "start_scene": "INT. OFFICE - DAY",
                "end_scene": "EXT. ROOFTOP - NIGHT",
                "summary": "Conflict escalates.",
                "turning_points": ["Midpoint reversal"],
            },
        ],
        "themes": [
            {
                "theme": "Identity",
                "description": "Characters struggle with who they are.",
                "evidence": ["Scene 1: mirror scene", "Scene 5: confession"],
            },
        ],
        "narrative_arc": "Classic three-act structure with false victory at midpoint.",
        "genre": "Drama",
        "tone": "Contemplative and tense",
        "protagonist_journey": "From denial to acceptance.",
        "central_conflict": "Man vs. self — confronting past mistakes.",
        "setting_overview": "Contemporary urban setting, 2020s.",
        "confidence": 0.88,
    }
    bible = ScriptBible.model_validate(data)
    dumped = bible.model_dump(mode="json")
    assert dumped["title"] == "Test Film"
    assert len(dumped["act_structure"]) == 2
    assert dumped["confidence"] == 0.88


@pytest.mark.unit
def test_runtime_work_model_overrides_module_default(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def _fake_call_llm(**kwargs: Any):
        captured["model"] = kwargs["model"]
        return ScriptBible(
            title="Runtime Override",
            logline="A runtime override test.",
            synopsis="The runtime work model should win.",
            act_structure=[
                {
                    "act_number": 1,
                    "title": "Setup",
                    "start_scene": "INT. LAB - NIGHT",
                    "end_scene": "INT. LAB - NIGHT",
                    "summary": "The override is exercised.",
                    "turning_points": ["Runtime params win."],
                }
            ],
            themes=[
                {
                    "theme": "Configuration",
                    "description": "Runtime params override stale module defaults.",
                    "evidence": ["Test fixture."],
                }
            ],
            narrative_arc="Short.",
            genre="Drama",
            tone="Neutral",
            protagonist_journey="Learns the override path.",
            central_conflict="Configured model versus stale default.",
            setting_overview="A test harness.",
            confidence=0.9,
        ), {"model": kwargs["model"], "estimated_cost_usd": 0.0}

    monkeypatch.setattr(script_bible_main, "call_llm", _fake_call_llm)

    result = run_module(
        inputs={"normalize": _canonical_script(SAMPLE_SCRIPT)},
        params={},
        context={"runtime_params": {"work_model": "claude-sonnet-4-6"}},
    )

    assert captured["model"] == "claude-sonnet-4-6"
    assert result["cost"]["model"] == "claude-sonnet-4-6"


@pytest.mark.unit
def test_default_work_model_matches_module_manifest(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def _fake_call_llm(**kwargs: Any):
        captured["model"] = kwargs["model"]
        return ScriptBible(
            title="Default Model",
            logline="A default model alignment test.",
            synopsis="The runtime fallback and module manifest stay aligned.",
            act_structure=[
                {
                    "act_number": 1,
                    "title": "Setup",
                    "start_scene": "INT. LAB - NIGHT",
                    "end_scene": "INT. LAB - NIGHT",
                    "summary": "The default is exercised.",
                    "turning_points": ["The selected model is captured."],
                }
            ],
            themes=[
                {
                    "theme": "Alignment",
                    "description": "Declared and runtime defaults agree.",
                    "evidence": ["Test fixture."],
                }
            ],
            narrative_arc="Short.",
            genre="Drama",
            tone="Neutral",
            protagonist_journey="Learns the default path.",
            central_conflict="Manifest versus runtime drift.",
            setting_overview="A test harness.",
            confidence=0.9,
        ), {"model": kwargs["model"], "estimated_cost_usd": 0.0}

    monkeypatch.setattr(script_bible_main, "call_llm", _fake_call_llm)

    result = run_module(
        inputs={"normalize": _canonical_script(SAMPLE_SCRIPT)},
        params={},
        context={"runtime_params": {}},
    )
    manifest = yaml.safe_load(MODULE_MANIFEST.read_text())
    declared_default = manifest["parameters"]["work_model"]["default"]

    assert script_bible_main.DEFAULT_WORK_MODEL == "gemini-3.5-flash-lite"
    assert declared_default == script_bible_main.DEFAULT_WORK_MODEL
    assert captured["model"] == script_bible_main.DEFAULT_WORK_MODEL
    assert result["cost"]["model"] == script_bible_main.DEFAULT_WORK_MODEL


@pytest.mark.unit
def test_runtime_default_model_used_when_work_model_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def _fake_call_llm(**kwargs: Any):
        captured["model"] = kwargs["model"]
        return ScriptBible(
            title="Default Model Fallback",
            logline="A default model fallback test.",
            synopsis="The runtime default model should be used when work_model is absent.",
            act_structure=[
                {
                    "act_number": 1,
                    "title": "Setup",
                    "start_scene": "INT. LAB - NIGHT",
                    "end_scene": "INT. LAB - NIGHT",
                    "summary": "The default model fallback is exercised.",
                    "turning_points": ["Default model wins."],
                }
            ],
            themes=[
                {
                    "theme": "Fallbacks",
                    "description": "Default model should be honored before the hardcoded default.",
                    "evidence": ["Test fixture."],
                }
            ],
            narrative_arc="Short.",
            genre="Drama",
            tone="Neutral",
            protagonist_journey="Learns the fallback path.",
            central_conflict="Runtime default versus hardcoded fallback.",
            setting_overview="A test harness.",
            confidence=0.9,
        ), {"model": kwargs["model"], "estimated_cost_usd": 0.0}

    monkeypatch.setattr(script_bible_main, "call_llm", _fake_call_llm)

    result = run_module(
        inputs={"normalize": _canonical_script(SAMPLE_SCRIPT)},
        params={},
        context={"runtime_params": {"default_model": "claude-sonnet-4-6"}},
    )

    assert captured["model"] == "claude-sonnet-4-6"
    assert result["cost"]["model"] == "claude-sonnet-4-6"
