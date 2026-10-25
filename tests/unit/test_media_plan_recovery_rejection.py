"""Consumed media approval cannot enqueue resume or failed-stage replay."""

from __future__ import annotations

import json

import pytest

from cine_forge.api.exceptions import ServiceError
from cine_forge.api.service import OperatorConsoleService

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("action", ["budget_resume", "retry"])
def test_approved_media_recovery_requires_fresh_inspection_before_bootstrap(
    tmp_path,
    monkeypatch,
    action,
):
    service = OperatorConsoleService(tmp_path)
    run_id = "run-approved"
    run_dir = tmp_path / "output/runs" / run_id
    run_dir.mkdir(parents=True)
    ref = {
        "artifact_type": "media_execution_plan",
        "entity_id": "plan-accepted",
        "version": 1,
        "path": "artifacts/media_execution_plan/plan-accepted/v1.json",
    }
    state = {
        "run_id": run_id,
        "recipe_id": "ai_previz_generation",
        "cost_is_complete": True,
        "runtime_params": {
            "media_execution_plan_ref": ref,
            "input_file": "script.fountain",
            "default_model": "fixture",
            "run_budget_limit_usd": 0.2,
        },
        "stages": {
            "ai_previz": {
                "status": "done" if action == "budget_resume" else "failed",
                "cost_is_complete": True,
                "artifact_refs": [],
            },
            "validate_media": {
                "status": "paused" if action == "budget_resume" else "pending",
                "pause_reason": "budget_limit",
            },
        },
    }
    state_path = run_dir / "run_state.json"
    state_path.write_text(json.dumps(state))
    original_bytes = state_path.read_bytes()
    before = set(run_dir.parent.iterdir())
    monkeypatch.setattr(
        service._orchestrator,
        "_bootstrap_run_dir",
        lambda **kw: pytest.fail("Recovery must not bootstrap a new run"),
    )
    monkeypatch.setattr(
        "cine_forge.api.run_orchestrator.threading.Thread",
        lambda **kw: pytest.fail("Recovery must not construct a worker"),
    )
    with pytest.raises(ServiceError) as error:
        if action == "budget_resume":
            # Neither increasing budget nor stripping the ref in overrides can reuse authority.
            service.resume_run(
                run_id,
                overrides={
                    "run_budget_limit_usd": 20,
                    "media_execution_plan_ref": None,
                },
            )
        else:
            service.retry_failed_stage(run_id)
    assert error.value.status_code == 409
    assert error.value.code == "media_execution_plan_requires_inspection"
    assert "inspect" in error.value.hint.lower()
    assert "unknown charges" in error.value.hint
    assert set(run_dir.parent.iterdir()) == before
    assert not service._orchestrator._run_threads
    assert state_path.read_bytes() == original_bytes


def test_unresolved_cost_guard_remains_authoritative_for_approved_recovery(tmp_path):
    service = OperatorConsoleService(tmp_path)
    run_dir = tmp_path / "output/runs/run-uncertain-approved"
    run_dir.mkdir(parents=True)
    (run_dir / "run_state.json").write_text(
        json.dumps(
            {
                "run_id": "run-uncertain-approved",
                "recipe_id": "ai_previz_generation",
                "runtime_params": {"media_execution_plan_ref": {"fixture": "consumed"}},
                "cost_is_complete": False,
                "stages": {"ai_previz": {"status": "failed", "cost_is_complete": False}},
            }
        )
    )
    with pytest.raises(ServiceError) as error:
        service.retry_failed_stage("run-uncertain-approved")
    assert error.value.code == "unresolved_media_cost"
    assert error.value.status_code == 409
