"""Focused xAI Responses contract tests for the exact-runtime script-bible lane."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_provider():
    path = REPO_ROOT / "benchmarks/providers/script_bible_runtime_provider.py"
    spec = importlib.util.spec_from_file_location(
        "xai_script_bible_provider_contract", path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def provider():
    return _load_provider()


def _bible(provider):
    return provider.ScriptBible(
        title="Open Frequency",
        logline="A radio team helps its town.",
        synopsis="The team stays on air and helps reunite a missing dog.",
        act_structure=[
            {
                "act_number": 1,
                "title": "Broadcast",
                "start_scene": "INT. COMMUNITY RADIO STUDIO - NIGHT",
                "end_scene": "INT. COMMUNITY RADIO STUDIO - MORNING",
                "summary": "The team keeps broadcasting.",
                "turning_points": ["Comet returns."],
            }
        ],
        themes=[
            {
                "theme": "Service",
                "description": "The station serves its community.",
                "evidence": ["Maya's plea.", "Comet returns."],
            }
        ],
        narrative_arc="A worried plea resolves in communal relief.",
        genre="Drama",
        tone="Hopeful",
        protagonist_journey="The ensemble recommits to service.",
        central_conflict="Keeping the community connected.",
        setting_overview="A community radio station.",
        confidence=0.9,
    )


def test_grok46_responses_enforces_schema_storage_identity_and_usage(
    provider,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bible = _bible(provider)
    seen = {}

    def fake_request(payload: dict, *, timeout_seconds: float):
        seen.update(payload=payload, timeout_seconds=timeout_seconds)
        return (
            {
                "id": "resp-grok46",
                "model": "grok-4.6",
                "status": "completed",
                "incomplete_details": None,
                "output": [
                    {
                        "type": "message",
                        "content": [
                            {"type": "output_text", "text": bible.model_dump_json()}
                        ],
                    }
                ],
                "usage": {
                    "input_tokens": 100,
                    "output_tokens": 60,
                    "total_tokens": 160,
                    "cost_in_usd_ticks": 5600000,
                    "output_tokens_details": {"reasoning_tokens": 40},
                },
            },
            "false",
        )

    monkeypatch.setattr(provider, "_request_xai_responses_json", fake_request)
    result = provider.call_api(
        "marker",
        {
            "config": {
                "model": "grok-4.6",
                "max_tokens": 8192,
                "request_timeout_seconds": 12,
                "reasoning_effort": "low",
            }
        },
        {"vars": {"screenplay": "INT. STUDIO - NIGHT\nARIA broadcasts."}},
    )

    payload = seen["payload"]
    assert payload["model"] == "grok-4.6"
    assert payload["reasoning"] == {"effort": "low"}
    assert payload["store"] is False
    assert payload["max_output_tokens"] == 8192
    assert payload["text"]["format"]["type"] == "json_schema"
    assert payload["text"]["format"]["strict"] is True
    assert "temperature" not in payload
    assert result["output"] == bible.model_dump_json()
    assert result["tokenUsage"] == {
        "total": 160,
        "prompt": 100,
        "completion": 20,
        "completionDetails": {"reasoning": 40},
    }
    assert result["cost"] == 0.00056
    assert result["metadata"]["provider"] == "xai"
    assert result["metadata"]["returned_model"] == "grok-4.6"
    assert result["metadata"]["store"] is False
    assert result["metadata"]["x_zero_data_retention"] == "false"
    assert result["metadata"]["zdr"] is False
    assert result["raw"]["usage"]["output_tokens_details"] == {
        "reasoning_tokens": 40
    }


def test_grok46_responses_rejects_unreconciled_usage(
    provider,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bible = _bible(provider)
    monkeypatch.setattr(
        provider,
        "_request_xai_responses_json",
        lambda *_args, **_kwargs: (
            {
                "id": "resp-grok46",
                "model": "grok-4.6",
                "status": "completed",
                "incomplete_details": None,
                "output": [
                    {
                        "content": [
                            {"type": "output_text", "text": bible.model_dump_json()}
                        ]
                    }
                ],
                "usage": {
                    "input_tokens": 100,
                    "output_tokens": 60,
                    "total_tokens": 999,
                    "cost_in_usd_ticks": 5600000,
                    "output_tokens_details": {"reasoning_tokens": 40},
                },
            },
            "false",
        ),
    )

    result = provider.call_api(
        "marker",
        {"config": {"model": "grok-4.6"}},
        {"vars": {"screenplay": "synthetic"}},
    )

    assert result["output"] == ""
    assert "total_tokens does not reconcile" in result["error"]
