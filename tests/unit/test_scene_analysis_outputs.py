from __future__ import annotations

import pytest

from cine_forge.modules.ingest.scene_analysis_v1.execution import _SceneEnrichment
from cine_forge.modules.ingest.scene_analysis_v1.outputs import (
    _build_enriched_scene,
    _build_scene_index_artifact,
    _build_scene_outputs,
)
from cine_forge.schemas import NarrativeBeat, SceneIndexEntry


def _entry(
    *,
    scene_id: str = "scene_001",
    location: str = "UNKNOWN",
    time_of_day: str = "NIGHT",
    characters_present: list[str] | None = None,
) -> SceneIndexEntry:
    return SceneIndexEntry.model_validate(
        {
            "scene_id": scene_id,
            "scene_number": 1,
            "heading": "INT. ROOM - NIGHT",
            "location": location,
            "time_of_day": time_of_day,
            "characters_present": characters_present or [],
            "source_span": {"start_line": 1, "end_line": 10},
            "tone_mood": "neutral",
        }
    )


@pytest.mark.unit
def test_build_enriched_scene_applies_gap_fills() -> None:
    entry = _entry(characters_present=["MARA"])
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
    entry = _entry(location="Office", time_of_day="DAY")
    enrichment = _SceneEnrichment(
        scene_id="scene_001",
        tone_mood="professional",
        location="Conference Room",
    )

    result = _build_enriched_scene(entry, enrichment)

    assert result["location"] == "Office"


@pytest.mark.unit
def test_build_scene_outputs_marks_failed_analysis_for_review() -> None:
    entry = _entry(time_of_day="UNSPECIFIED")
    enrichment = _SceneEnrichment(
        scene_id="scene_001",
        tone_mood="_analysis_failed",
        characters_present=["MARA"],
    )

    scene_artifacts, updated_entries = _build_scene_outputs(
        entries=[entry],
        scene_texts={"scene_001": "INT. ROOM - NIGHT\n\nMARA\nSomething happens."},
        enrichments={"scene_001": enrichment},
        total_qa_needs_review=0,
    )

    assert scene_artifacts[0]["metadata"]["health"] == "needs_review"
    assert scene_artifacts[0]["data"]["tone_mood"] == "neutral"
    assert updated_entries[0].tone_mood == "neutral"


@pytest.mark.unit
def test_build_scene_index_artifact_preserves_batch_metadata() -> None:
    artifact = _build_scene_index_artifact(
        scene_count=1,
        estimated_runtime_minutes=1.0,
        updated_entries=[_entry(location="Control Room", characters_present=["MARA"])],
        total_qa_needs_review=1,
        batch_stats={
            "adaptive_batching": True,
            "configured_batch_size": 5,
            "configured_max_batch_size": 10,
            "configured_max_batch_words": 2500,
            "largest_batch_size": 10,
            "largest_batch_words": 900,
            "total_batches": 2,
        },
    )

    assert artifact["metadata"]["health"] == "needs_review"
    assert artifact["data"]["scenes_need_review"] == 1
    assert artifact["metadata"]["annotations"]["adaptive_batching"] is True
    assert artifact["metadata"]["annotations"]["total_batches"] == 2
