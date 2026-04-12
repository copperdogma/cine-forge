from __future__ import annotations

from typing import Any

import pytest

from cine_forge.modules.ingest.scene_analysis_v1.batching import (
    batch_word_count,
    create_adaptive_batches,
)
from cine_forge.modules.ingest.scene_analysis_v1.main import run_module
from cine_forge.schemas import SceneIndexEntry


def _entry(index: int) -> SceneIndexEntry:
    return SceneIndexEntry.model_validate(
        {
            "scene_id": f"scene_{index:03d}",
            "scene_number": index,
            "heading": f"INT. ROOM {index} - DAY",
            "location": f"Room {index}",
            "time_of_day": "DAY",
            "characters_present": [],
            "source_span": {
                "start_line": (index - 1) * 4 + 1,
                "end_line": index * 4,
            },
            "tone_mood": "neutral",
        }
    )

def _scene_texts(
    entries: list[SceneIndexEntry], word_counts: list[int]
) -> dict[str, str]:
    return {
        entry.scene_id: " ".join(["word"] * word_count)
        for entry, word_count in zip(entries, word_counts, strict=True)
    }


def _module_inputs(num_scenes: int, words_per_scene: int = 20) -> dict[str, Any]:
    entries = [_entry(index) for index in range(1, num_scenes + 1)]
    lines: list[str] = []
    for index in range(1, num_scenes + 1):
        lines.extend(
            [
                f"INT. ROOM {index} - DAY",
                "",
                " ".join(["word"] * words_per_scene),
                "",
            ]
        )

    return {
        "scene_index": {
            "total_scenes": num_scenes,
            "unique_locations": [
                f"Room {index}" for index in range(1, num_scenes + 1)
            ],
            "unique_characters": [],
            "estimated_runtime_minutes": float(num_scenes),
            "scenes_passed_qa": num_scenes,
            "scenes_need_review": 0,
            "entries": [entry.model_dump(mode="json") for entry in entries],
        },
        "canonical_script": {"script_text": "\n".join(lines)},
    }


@pytest.mark.unit
def test_create_adaptive_batches_expands_when_word_budget_allows() -> None:
    entries = [_entry(index) for index in range(1, 13)]
    scene_texts = _scene_texts(entries, [20] * len(entries))

    batches = create_adaptive_batches(
        entries=entries,
        scene_texts=scene_texts,
        batch_size=5,
        max_batch_size=10,
        max_batch_words=2500,
    )

    assert [len(batch) for batch in batches] == [10, 2]


@pytest.mark.unit
def test_create_adaptive_batches_respects_word_budget_after_minimum_size() -> None:
    entries = [_entry(index) for index in range(1, 9)]
    scene_texts = _scene_texts(
        entries, [400, 400, 400, 400, 400, 900, 100, 100]
    )

    batches = create_adaptive_batches(
        entries=entries,
        scene_texts=scene_texts,
        batch_size=5,
        max_batch_size=10,
        max_batch_words=2200,
    )

    assert [len(batch) for batch in batches] == [5, 3]
    assert batch_word_count(batches[0], scene_texts) == 2000


@pytest.mark.unit
def test_run_module_records_adaptive_batch_metadata() -> None:
    result = run_module(
        inputs=_module_inputs(num_scenes=12, words_per_scene=20),
        params={
            "work_model": "mock",
            "qa_model": "mock",
            "batch_size": 5,
            "max_batch_size": 10,
            "max_batch_words": 2500,
        },
        context={},
    )

    scene_index = next(
        artifact
        for artifact in result["artifacts"]
        if artifact["artifact_type"] == "scene_index"
    )
    annotations = scene_index["metadata"]["annotations"]

    assert annotations["adaptive_batching"] is True
    assert annotations["configured_batch_size"] == 5
    assert annotations["configured_max_batch_size"] == 10
    assert annotations["configured_max_batch_words"] == 2500
    assert annotations["largest_batch_size"] == 10
    assert annotations["total_batches"] == 2
