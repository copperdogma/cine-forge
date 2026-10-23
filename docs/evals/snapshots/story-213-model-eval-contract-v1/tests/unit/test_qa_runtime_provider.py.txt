"""Focused tests for the production-parity QA benchmark provider."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_provider():
    path = REPO_ROOT / "benchmarks/providers/qa_runtime_provider.py"
    spec = importlib.util.spec_from_file_location("qa_runtime_provider_contract", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_provider_uses_production_prompt_schema_and_current_gemini_controls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = _load_provider()
    seen = {}

    def fake_call_llm(**kwargs):
        seen.update(kwargs)
        return (
            provider.QAResult(
                passed=True,
                confidence=0.95,
                issues=[],
                summary="The extraction is accurate and materially complete.",
            ),
            {
                "provider": "google",
                "requested_model": "gemini-3.7-flash",
                "returned_model": "gemini-3.7-flash",
                "request_id": "gemini-qa-1",
                "finish_reason": "stop",
                "input_tokens": 100,
                "output_tokens": 30,
                "reasoning_output_tokens": 20,
                "visible_output_tokens": 10,
                "estimated_cost_usd": 0.0002,
                "latency_seconds": 1.25,
            },
        )

    monkeypatch.setattr(provider, "call_llm", fake_call_llm)
    response = provider.call_api(
        "ignored marker",
        {"config": {"model": "gemini-3.7-flash"}},
        {"vars": {"scene_text": "INT. ROOM", "extracted_data": "{}"}},
    )

    assert seen["response_schema"] is provider.QAResult
    assert seen["max_tokens"] == 1200
    assert seen["max_retries"] == 2
    assert "thinking_level" not in seen
    assert seen["prompt"] == provider._build_qa_prompt(
        original_input="INT. ROOM",
        prompt_used=provider.PRODUCING_PROMPT,
        output_produced="{}",
        criteria=provider.QA_CRITERIA,
    )
    assert response["tokenUsage"] == {
        "total": 130,
        "prompt": 100,
        "completion": 10,
        "completionDetails": {"reasoning": 20},
    }
    assert response["metadata"]["runtime_prompt"].endswith("._build_qa_prompt")
    assert response["metadata"]["returned_model"] == "gemini-3.7-flash"
    assert response["cost"] == pytest.approx(0.0001875)


def test_provider_rejects_served_model_substitution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = _load_provider()
    monkeypatch.setattr(
        provider,
        "call_llm",
        lambda **_kwargs: (
            provider.QAResult(
                passed=True,
                confidence=0.9,
                issues=[],
                summary="The extraction is accurate and complete.",
            ),
            {
                "provider": "openai",
                "returned_model": "gpt-4.1",
                "request_id": "chatcmpl-substitution",
                "finish_reason": "stop",
            },
        ),
    )

    response = provider.call_api(
        "ignored",
        {"config": {"model": "gpt-4.1-mini"}},
        {"vars": {"scene_text": "INT. ROOM", "extracted_data": "{}"}},
    )

    assert response["output"] == ""
    assert "does not match" in response["error"]
