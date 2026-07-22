"""Returned model and call identity in final-render analysis evidence."""

from __future__ import annotations

import importlib
import sys
from copy import deepcopy
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = REPO_ROOT / "benchmarks" / "scripts"
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

metrics = importlib.import_module("final_render_provider_floor_quality_metrics")

pytestmark = pytest.mark.unit


def _evidence() -> tuple[dict, dict]:
    response = {
        "tokenUsage": {"prompt": 100, "completion": 20, "total": 120},
        "latencyMs": 100,
        "cost": 0.00055,
        "metadata": {
            "provider": "openai",
            "model": "gpt-5.4",
            "requested_model": "gpt-5.4",
            "returned_model": "gpt-5.4-2026-03-05",
            "request_id": "analysis-response-1",
        },
        "raw": {
            "id": "analysis-response-1",
            "model": "gpt-5.4-2026-03-05",
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 20,
                "total_tokens": 120,
            },
        },
    }
    return {"latencyMs": 100, "cost": 0.00055}, response


def test_final_render_metrics_accept_compatible_dated_snapshot() -> None:
    entry, response = _evidence()

    assert metrics.validated_response_metrics(
        entry=entry,
        response=response,
        max_completion_tokens=1400,
    ) == (100.0, 0.00055)


@pytest.mark.parametrize("mutation", ["missing_id", "substitution", "id_mismatch"])
def test_final_render_metrics_reject_identity_contradictions(mutation: str) -> None:
    entry, response = _evidence()
    if mutation == "missing_id":
        response["raw"].pop("id")
    elif mutation == "substitution":
        response["raw"]["model"] = "gpt-4o-mini"
    else:
        response["metadata"]["request_id"] = "contradictory-request"

    assert metrics.validated_response_metrics(
        entry=deepcopy(entry),
        response=response,
        max_completion_tokens=1400,
    ) is None


def test_final_render_metrics_reject_raw_reasoning_breakdown_contradiction() -> None:
    entry, response = _evidence()
    response["tokenUsage"]["completionDetails"] = {"reasoning": 8}
    response["raw"]["usage"]["output_tokens_details"] = {
        "reasoning_tokens": 7,
    }

    assert metrics.validated_response_metrics(
        entry=entry,
        response=response,
        max_completion_tokens=1400,
    ) is None
