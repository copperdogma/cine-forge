from __future__ import annotations

from pathlib import Path

import pytest

from cine_forge.modules.ingest.scene_breakdown_v1.main import (
    _empty_cost,
    _sum_costs,
    run_module,
)

pytestmark = pytest.mark.unit


def test_sum_costs_preserves_totals_and_single_model_label() -> None:
    result = _sum_costs(
        [
            {
                "model": "fixture",
                "input_tokens": 17,
                "output_tokens": 5,
                "estimated_cost_usd": 0.00125,
            },
            {
                "model": "fixture",
                "input_tokens": 23,
                "output_tokens": 7,
                "estimated_cost_usd": 0.0025,
            },
        ]
    )

    assert result == {
        "model": "fixture",
        "input_tokens": 40,
        "output_tokens": 12,
        "estimated_cost_usd": 0.00375,
        "call_count": 2,
    }


def test_sum_costs_uses_mixed_label_only_for_distinct_models() -> None:
    result = _sum_costs(
        [
            {
                "model": "fixture",
                "input_tokens": 10,
                "output_tokens": 4,
                "estimated_cost_usd": 0.1,
                "call_count": 2,
            },
            {
                "model": "gpt-4.1-mini",
                "input_tokens": 20,
                "output_tokens": 6,
                "estimated_cost_usd": 0.2,
            },
        ]
    )

    assert result["model"] == "mixed:fixture+gpt-4.1-mini"
    assert result["call_count"] == 3
    assert result["input_tokens"] == 30
    assert result["output_tokens"] == 10
    assert result["estimated_cost_usd"] == 0.3


def test_sum_costs_does_not_count_no_call_sentinels() -> None:
    result = _sum_costs([_empty_cost("mock"), _empty_cost("mock")])

    assert result["model"] == "mock"
    assert result["call_count"] == 0
    assert result["estimated_cost_usd"] == 0.0


def test_sample_screenplay_reports_one_fixture_call_per_scene(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_root = Path(__file__).resolve().parents[2]
    fixture_root = workspace_root / "tests" / "fixtures" / "mvp_mock_responses"
    screenplay_path = workspace_root / "tests" / "fixtures" / "sample_screenplay.fountain"
    monkeypatch.setenv("CINE_FORGE_MOCK_FIXTURE_DIR", str(fixture_root))

    result = run_module(
        inputs={"canonical": {"script_text": screenplay_path.read_text(encoding="utf-8")}},
        params={"work_model": "fixture", "max_workers": 4},
        context={},
    )

    scenes = [
        artifact
        for artifact in result["artifacts"]
        if artifact["artifact_type"] == "scene"
    ]
    assert len(scenes) == 8
    assert result["cost"]["model"] == "fixture"
    assert result["cost"]["call_count"] == len(scenes)
    assert result["cost"]["input_tokens"] == 0
    assert result["cost"]["output_tokens"] == 0
    assert result["cost"]["estimated_cost_usd"] == 0.0
