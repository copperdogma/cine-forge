from __future__ import annotations

from typing import Any

import pytest

import cine_forge.modules.ingest.scene_analysis_v1.execution as execution_module
from cine_forge.schemas import SceneIndexEntry
from cine_forge.schemas.qa import QAIssue, QAResult


def _entry(index: int) -> SceneIndexEntry:
    return SceneIndexEntry.model_validate(
        {
            "scene_id": f"scene_{index:03d}",
            "scene_number": index,
            "heading": f"INT. ROOM {index} - NIGHT",
            "location": f"Room {index}",
            "time_of_day": "NIGHT",
            "characters_present": [],
            "source_span": {"start_line": 1, "end_line": 5},
            "tone_mood": "neutral",
        }
    )


def _scene_texts(entries: list[SceneIndexEntry]) -> dict[str, str]:
    return {
        entry.scene_id: f"{entry.heading}\n\nSome dialogue for {entry.scene_id}."
        for entry in entries
    }


@pytest.mark.unit
def test_mock_enrichments_produces_neutral_defaults() -> None:
    entries = [_entry(index) for index in range(1, 4)]
    enrichments = execution_module._mock_enrichments(entries)

    assert len(enrichments) == 3
    for enrichment in enrichments:
        assert enrichment.tone_mood == "neutral"
        assert enrichment.narrative_beats == []


@pytest.mark.unit
def test_analyze_batch_returns_failed_mock_enrichments_after_retry_exhaustion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts: list[str] = []

    def _raise_call_llm(**kwargs: Any) -> tuple[Any, dict[str, Any]]:
        attempts.append(kwargs["model"])
        raise RuntimeError("boom")

    monkeypatch.setattr(execution_module, "call_llm", _raise_call_llm)
    entries = [_entry(1), _entry(2)]

    enrichments, cost = execution_module._analyze_batch(
        entries=entries,
        scene_texts=_scene_texts(entries),
        work_model="claude-sonnet-4-6",
        escalate_model="claude-opus-4-6",
        max_retries=1,
    )

    assert attempts == ["claude-sonnet-4-6", "claude-opus-4-6"]
    assert [enrichment.tone_mood for enrichment in enrichments] == [
        "_analysis_failed",
        "_analysis_failed",
    ]
    assert cost["model"] == "claude-sonnet-4-6"


@pytest.mark.unit
def test_run_batch_analysis_accumulates_failed_qa_batch_sizes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entries = [_entry(index) for index in range(1, 4)]
    batches = [entries[:2], entries[2:]]
    qa_results = [
        (
            QAResult(
                passed=False,
                confidence=0.2,
                issues=[
                    QAIssue(
                        severity="warning",
                        description="Possible hallucination",
                        location="scene_001",
                    )
                ],
                summary="Needs review",
            ),
            {"model": "mock", "estimated_cost_usd": 0.0},
        ),
        (
            QAResult(passed=True, confidence=0.95, issues=[], summary="Passed"),
            {"model": "mock", "estimated_cost_usd": 0.0},
        ),
    ]

    def _fake_qa_batch(*args: Any, **kwargs: Any) -> tuple[QAResult, dict[str, Any]]:
        del args, kwargs
        return qa_results.pop(0)

    monkeypatch.setattr(execution_module, "_qa_batch", _fake_qa_batch)
    enrichments, costs, total_qa_needs_review, duration = (
        execution_module._run_batch_analysis(
            batches=batches,
            scene_texts=_scene_texts(entries),
            work_model="mock",
            escalate_model="mock",
            max_retries=0,
            skip_qa=False,
            qa_model="mock",
        )
    )

    assert sorted(enrichments) == ["scene_001", "scene_002", "scene_003"]
    assert total_qa_needs_review == 2
    assert len(costs) == 4
    assert duration >= 0.0


@pytest.mark.unit
def test_build_macro_analysis_prompt_requests_explicit_tonal_juxtaposition() -> None:
    entry = _entry(1)

    prompt = execution_module._build_macro_analysis_prompt(
        entries=[entry],
        scene_texts={
            entry.scene_id: (
                f"{entry.heading}\n\n"
                "UB40 muzak plays while Rose and Mariner stagger into the elevator."
            )
        },
    )

    assert "soundtrack, ambient audio, and other sensory cues" in prompt
    assert "tonal contradiction explicitly" in prompt
    assert "generic phrases like 'action to dark comedy'" in prompt
    assert "flashback, memory, or formative past moment" in prompt
