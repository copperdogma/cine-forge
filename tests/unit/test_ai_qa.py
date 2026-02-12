from __future__ import annotations

from typing import Any

import pytest

from cine_forge.ai import qa


@pytest.mark.unit
def test_qa_check_returns_structured_result(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def fake_call_llm(**kwargs: Any):
        captured.update(kwargs)
        return (
            qa.QAResult(
                passed=True,
                confidence=0.88,
                issues=[],
                summary="Looks good.",
            ),
            {
                "model": "gpt-4o-mini",
                "input_tokens": 0,
                "output_tokens": 0,
                "estimated_cost_usd": 0.0,
            },
        )

    monkeypatch.setattr("cine_forge.ai.qa.call_llm", fake_call_llm)

    result, metadata = qa.qa_check(
        original_input="original text",
        prompt_used="prompt text",
        output_produced="output text",
        model="gpt-4o-mini",
    )

    assert result.passed is True
    assert metadata["model"] == "gpt-4o-mini"
    assert "intent preservation" in captured["prompt"]
    assert captured["response_schema"] is qa.QAResult


@pytest.mark.unit
def test_qa_check_with_repairs_returns_edit_plan(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_call_llm(**_: Any):
        return (
            qa.QARepairPlan(
                qa_result=qa.QAResult(
                    passed=False,
                    confidence=0.7,
                    issues=[
                        {
                            "severity": "error",
                            "description": "Heading malformed",
                            "location": "Scene 1",
                        }
                    ],
                    summary="Repair needed",
                ),
                edits=[
                    {
                        "search": "int. room - night",
                        "replace": "INT. ROOM - NIGHT",
                        "rationale": "Fix heading casing",
                    }
                ],
            ),
            {
                "model": "gpt-4o-mini",
                "input_tokens": 0,
                "output_tokens": 0,
                "estimated_cost_usd": 0.0,
            },
        )

    monkeypatch.setattr("cine_forge.ai.qa.call_llm", fake_call_llm)
    plan, _ = qa.qa_check_with_repairs(
        original_input="x",
        prompt_used="y",
        output_produced="z",
        model="gpt-4o-mini",
    )
    assert plan.qa_result.passed is False
    assert plan.edits[0].search == "int. room - night"
