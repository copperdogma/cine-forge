from __future__ import annotations

from typing import Any

import pytest

from cine_forge.modules.ingest.scene_analysis_v1.main import (
    _build_enriched_scene,
    _create_batches,
    _extract_scene_texts,
    _mock_enrichments,
    _resolve_inputs,
    _SceneEnrichment,
    run_module,
)
from cine_forge.schemas import NarrativeBeat, SceneIndexEntry

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _scene_index_data(num_scenes: int = 3) -> dict[str, Any]:
    entries = []
    for i in range(1, num_scenes + 1):
        entries.append(
            {
                "scene_id": f"scene_{i:03d}",
                "scene_number": i,
                "heading": f"INT. ROOM {i} - NIGHT",
                "location": "UNKNOWN" if i == 2 else f"Room {i}",
                "time_of_day": "UNSPECIFIED" if i == 3 else "NIGHT",
                "characters_present": ["MARA"] if i == 1 else [],
                "source_span": {"start_line": (i - 1) * 5 + 1, "end_line": i * 5},
                "tone_mood": "neutral",
            }
        )
    return {
        "total_scenes": num_scenes,
        "unique_locations": ["Room 1", "Room 3"],
        "unique_characters": ["MARA"],
        "estimated_runtime_minutes": float(num_scenes),
        "scenes_passed_qa": num_scenes,
        "scenes_need_review": 0,
        "entries": entries,
    }


def _canonical_data() -> dict[str, Any]:
    lines = []
    for i in range(1, 4):
        lines.extend([
            f"INT. ROOM {i} - NIGHT",
            "",
            "MARA" if i == 1 else "JACK",
            "Some dialogue here.",
            "",
        ])
    return {"script_text": "\n".join(lines)}


def _module_inputs() -> dict[str, Any]:
    return {
        "scene_index": _scene_index_data(),
        "canonical_script": _canonical_data(),
    }


# ---------------------------------------------------------------------------
# Input resolution
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_resolve_inputs_identifies_scene_index_and_canonical() -> None:
    inputs = _module_inputs()
    scene_idx, canonical = _resolve_inputs(inputs)
    assert "entries" in scene_idx
    assert "script_text" in canonical


@pytest.mark.unit
def test_resolve_inputs_raises_on_missing_scene_index() -> None:
    with pytest.raises(ValueError, match="requires scene_index"):
        _resolve_inputs({"canonical_script": _canonical_data()})


@pytest.mark.unit
def test_resolve_inputs_raises_on_missing_canonical() -> None:
    with pytest.raises(ValueError, match="requires canonical_script"):
        _resolve_inputs({"scene_index": _scene_index_data()})


# ---------------------------------------------------------------------------
# Scene text extraction
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_extract_scene_texts_pulls_correct_spans() -> None:
    script_text = "\n".join(
        [f"Line {i}" for i in range(1, 16)]
    )
    entries = [
        SceneIndexEntry.model_validate(
            {
                "scene_id": "scene_001",
                "scene_number": 1,
                "heading": "INT. ROOM - NIGHT",
                "location": "Room",
                "time_of_day": "NIGHT",
                "characters_present": [],
                "source_span": {"start_line": 1, "end_line": 5},
                "tone_mood": "neutral",
            }
        ),
        SceneIndexEntry.model_validate(
            {
                "scene_id": "scene_002",
                "scene_number": 2,
                "heading": "EXT. GARDEN - DAY",
                "location": "Garden",
                "time_of_day": "DAY",
                "characters_present": [],
                "source_span": {"start_line": 6, "end_line": 10},
                "tone_mood": "neutral",
            }
        ),
    ]
    result = _extract_scene_texts(script_text, entries)
    assert "Line 1" in result["scene_001"]
    assert "Line 5" in result["scene_001"]
    assert "Line 6" in result["scene_002"]
    assert "Line 10" in result["scene_002"]


# ---------------------------------------------------------------------------
# Batching
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_create_batches_splits_evenly() -> None:
    entries = [
        SceneIndexEntry.model_validate(
            {
                "scene_id": f"scene_{i:03d}",
                "scene_number": i,
                "heading": f"SCENE {i}",
                "location": "LOC",
                "time_of_day": "NIGHT",
                "characters_present": [],
                "source_span": {"start_line": 1, "end_line": 5},
                "tone_mood": "neutral",
            }
        )
        for i in range(1, 11)
    ]
    batches = _create_batches(entries, batch_size=3)
    assert len(batches) == 4  # 3, 3, 3, 1
    assert len(batches[0]) == 3
    assert len(batches[-1]) == 1


@pytest.mark.unit
def test_create_batches_single_batch() -> None:
    entries = [
        SceneIndexEntry.model_validate(
            {
                "scene_id": "scene_001",
                "scene_number": 1,
                "heading": "SCENE 1",
                "location": "LOC",
                "time_of_day": "NIGHT",
                "characters_present": [],
                "source_span": {"start_line": 1, "end_line": 5},
                "tone_mood": "neutral",
            }
        )
    ]
    batches = _create_batches(entries, batch_size=5)
    assert len(batches) == 1


# ---------------------------------------------------------------------------
# Mock enrichments
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_mock_enrichments_produces_neutral_defaults() -> None:
    entries = [
        SceneIndexEntry.model_validate(
            {
                "scene_id": f"scene_{i:03d}",
                "scene_number": i,
                "heading": f"SCENE {i}",
                "location": "LOC",
                "time_of_day": "NIGHT",
                "characters_present": [],
                "source_span": {"start_line": 1, "end_line": 5},
                "tone_mood": "neutral",
            }
        )
        for i in range(1, 4)
    ]
    enrichments = _mock_enrichments(entries)
    assert len(enrichments) == 3
    for e in enrichments:
        assert e.tone_mood == "neutral"
        assert e.narrative_beats == []


# ---------------------------------------------------------------------------
# Scene enrichment merge
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_build_enriched_scene_applies_gap_fills() -> None:
    entry = SceneIndexEntry.model_validate(
        {
            "scene_id": "scene_001",
            "scene_number": 1,
            "heading": "INT. ??? - NIGHT",
            "location": "UNKNOWN",
            "time_of_day": "NIGHT",
            "characters_present": ["MARA"],
            "source_span": {"start_line": 1, "end_line": 10},
            "tone_mood": "neutral",
        }
    )
    enrichment = _SceneEnrichment(
        scene_id="scene_001",
        narrative_beats=[
            NarrativeBeat(
                beat_type="conflict",
                description="Rising tension",
                approximate_location="middle",
                confidence=0.85,
            )
        ],
        tone_mood="tense",
        tone_shifts=["calm to tense"],
        location="Control Room",
        characters_present=["MARA", "JACK"],
    )
    result = _build_enriched_scene(entry, enrichment)
    assert result["location"] == "Control Room"
    assert result["tone_mood"] == "tense"
    assert len(result["narrative_beats"]) == 1
    assert "JACK" in result["characters_present"]
    assert "MARA" in result["characters_present"]


@pytest.mark.unit
def test_build_enriched_scene_preserves_known_location() -> None:
    entry = SceneIndexEntry.model_validate(
        {
            "scene_id": "scene_001",
            "scene_number": 1,
            "heading": "INT. OFFICE - DAY",
            "location": "Office",
            "time_of_day": "DAY",
            "characters_present": [],
            "source_span": {"start_line": 1, "end_line": 5},
            "tone_mood": "neutral",
        }
    )
    enrichment = _SceneEnrichment(
        scene_id="scene_001",
        tone_mood="professional",
        location="Conference Room",  # Should NOT override known location
    )
    result = _build_enriched_scene(entry, enrichment)
    assert result["location"] == "Office"  # Preserved, not overwritten


# ---------------------------------------------------------------------------
# run_module (mock model)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_run_module_mock_produces_enriched_scenes() -> None:
    result = run_module(
        inputs=_module_inputs(),
        params={"work_model": "mock", "qa_model": "mock"},
        context={},
    )
    artifacts = result["artifacts"]
    scenes = [a for a in artifacts if a["artifact_type"] == "scene"]
    indexes = [a for a in artifacts if a["artifact_type"] == "scene_index"]

    assert len(scenes) == 3
    assert len(indexes) == 1

    for scene in scenes:
        assert scene["metadata"]["annotations"]["discovery_tier"] == "llm_enriched"

    assert indexes[0]["metadata"]["annotations"]["discovery_tier"] == "llm_enriched"


@pytest.mark.unit
def test_run_module_mock_cost_is_present() -> None:
    result = run_module(
        inputs=_module_inputs(),
        params={"work_model": "mock", "qa_model": "mock"},
        context={},
    )
    assert "cost" in result
    assert "estimated_cost_usd" in result["cost"]


@pytest.mark.unit
def test_run_module_rejects_missing_inputs() -> None:
    with pytest.raises(ValueError, match="requires"):
        run_module(inputs={}, params={"work_model": "mock"}, context={})


@pytest.mark.unit
def test_run_module_respects_batch_size() -> None:
    # 3 scenes with batch_size=2 should produce 2 batches
    result = run_module(
        inputs=_module_inputs(),
        params={"work_model": "mock", "qa_model": "mock", "batch_size": 2},
        context={},
    )
    # Should still produce all scenes
    scenes = [a for a in result["artifacts"] if a["artifact_type"] == "scene"]
    assert len(scenes) == 3
