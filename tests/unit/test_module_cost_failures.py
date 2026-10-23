"""A fallback model must not replay accepted media jobs after a stage failure."""

from __future__ import annotations

import threading
from types import SimpleNamespace

import pytest

from cine_forge.driver.module_execution import run_module_with_retry
from cine_forge.driver.recipe import RecipeStage
from cine_forge.driver.retry_policy import RetryConfig, StageRetryPolicy
from cine_forge.execution_errors import ModuleCostError
from cine_forge.schemas.media_cost import CostReceipt

pytestmark = pytest.mark.unit


def test_cost_bearing_error_is_not_replayed_by_driver_fallback(tmp_path, monkeypatch) -> None:
    calls = []
    receipt = CostReceipt(
        receipt_id="accepted:job1", component="video", model="grok-imagine-video",
        status="uncertain", provider_job_id="job1", reason="HTTP 503 polling accepted job",
    )

    def module_runner(**kwargs):
        calls.append(kwargs)
        raise ModuleCostError("HTTP 503", cost_receipts=[receipt])

    stage = {"call_count": 0, "cost_usd": 0, "input_tokens": 0, "output_tokens": 0,
             "attempt_count": 0, "attempts": []}
    run = {"stages": {"generate": stage}, "total_cost_usd": 0}
    saved = []
    monkeypatch.setattr(StageRetryPolicy, "is_retryable_stage_error", lambda _: True)
    with pytest.raises(ModuleCostError):
        run_module_with_retry(
            module_runner=module_runner, module_inputs={},
            stage=RecipeStage(id="generate", module="fixture", params={}, needs=[]),
            stage_id="generate", run_id="fixture", resolved_runtime_params={},
            persister=SimpleNamespace(announce=lambda _: None),
            model_attempt_plan=["gpt-5.4-mini", "claude-sonnet-4-6"],
            retry_config=RetryConfig(None, 0, 0, 3, None), stage_state=stage,
            state_lock=threading.Lock(), emitter=SimpleNamespace(emit=lambda _: None),
            run_state=run, project_dir=tmp_path, retry_policy=StageRetryPolicy(),
            write_run_state=lambda: saved.append(True),
        )
    assert len(calls) == 1
    assert stage["call_count"] == 1
    assert stage["attempts"][0]["transient"] is False
    assert run["cost_is_complete"] is False
    assert saved
