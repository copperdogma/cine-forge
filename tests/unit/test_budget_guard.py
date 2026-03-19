from __future__ import annotations

import json
from pathlib import Path

import pytest

from cine_forge.driver.budget_guard import BudgetGuard


def _write_project_json(
    project_path: Path,
    *,
    project_limit: float | None = None,
    run_limit: float | None = None,
    threshold: float = 0.8,
) -> None:
    project_path.mkdir(parents=True, exist_ok=True)
    (project_path / "artifacts").mkdir(exist_ok=True)
    (project_path / "graph").mkdir(exist_ok=True)
    (project_path / "project.json").write_text(
        json.dumps(
            {
                "slug": project_path.name,
                "display_name": project_path.name,
                "project_budget_limit_usd": project_limit,
                "default_run_budget_limit_usd": run_limit,
                "budget_warning_threshold_ratio": threshold,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def _write_historical_run(
    workspace_root: Path,
    *,
    project_id: str,
    project_path: Path,
    run_id: str,
    total_cost_usd: float,
) -> None:
    run_dir = workspace_root / "output" / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "run_state.json").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "recipe_id": "mvp_ingest",
                "runtime_params": {},
                "total_cost_usd": total_cost_usd,
                "stages": {
                    "only": {
                        "status": "done",
                        "artifact_refs": [],
                        "duration_seconds": 1.0,
                        "cost_usd": total_cost_usd,
                    }
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (run_dir / "run_meta.json").write_text(
        json.dumps(
            {
                "project_id": project_id,
                "project_path": str(project_path),
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


@pytest.mark.unit
def test_budget_guard_warns_once_then_pauses_at_limit(tmp_path: Path) -> None:
    workspace_root = tmp_path
    project_path = workspace_root / "output" / "budget-project"
    _write_project_json(project_path, run_limit=1.0, threshold=0.8)

    guard = BudgetGuard(
        workspace_root=workspace_root,
        project_path=project_path,
        run_id="run-current",
        runtime_params={"run_budget_limit_usd": 1.0, "budget_warning_threshold_ratio": 0.8},
    )
    run_state = {
        "total_cost_usd": 0.85,
        "project_cost_baseline_usd": 0.0,
        "budget_warning_scopes": [],
    }

    warning = guard.evaluate(run_state, next_stage_id="next-stage")
    assert len(warning.warnings) == 1
    assert warning.warnings[0].scope.value == "run"
    assert warning.pause_status is None
    assert run_state["budget_warning_scopes"] == ["run"]

    deduped = guard.evaluate(run_state, next_stage_id="next-stage")
    assert deduped.warnings == []

    run_state["total_cost_usd"] = 1.0
    paused = guard.evaluate(run_state, next_stage_id="next-stage")
    assert paused.pause_status is not None
    assert paused.pause_status.scope.value == "run"
    assert paused.pause_status.health.value == "limit_reached"

    no_next_stage = guard.evaluate(run_state, next_stage_id=None)
    assert no_next_stage.pause_status is None


@pytest.mark.unit
def test_budget_guard_uses_historical_project_baseline(tmp_path: Path) -> None:
    workspace_root = tmp_path
    project_path = workspace_root / "output" / "budget-project"
    _write_project_json(project_path, project_limit=5.0, threshold=0.8)
    _write_historical_run(
        workspace_root,
        project_id="budget-project",
        project_path=project_path,
        run_id="run-previous",
        total_cost_usd=4.5,
    )

    guard = BudgetGuard(
        workspace_root=workspace_root,
        project_path=project_path,
        run_id="run-current",
        runtime_params={"project_budget_limit_usd": 5.0, "budget_warning_threshold_ratio": 0.8},
    )

    assert guard.project_cost_baseline_usd == pytest.approx(4.5)

    decision = guard.evaluate(
        {
            "total_cost_usd": 0.7,
            "budget_warning_scopes": [],
        },
        next_stage_id="next-stage",
    )
    assert decision.pause_status is not None
    assert decision.pause_status.scope.value == "project"
    assert decision.pause_status.consumed_usd == pytest.approx(5.2)
