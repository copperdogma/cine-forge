from __future__ import annotations

import json
from pathlib import Path

import pytest

from cine_forge.services.cost_tracking import CostTrackingService, run_status_from_state


def _write_project_settings(project_path: Path) -> None:
    project_path.mkdir(parents=True, exist_ok=True)
    (project_path / "artifacts").mkdir(exist_ok=True)
    (project_path / "graph").mkdir(exist_ok=True)
    (project_path / "project.json").write_text(
        json.dumps(
            {
                "slug": "cost-project",
                "display_name": "Cost Project",
                "project_budget_limit_usd": 10.0,
                "default_run_budget_limit_usd": 1.5,
                "budget_warning_threshold_ratio": 0.8,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def _write_run_state(
    *,
    workspace_root: Path,
    project_id: str,
    project_path: Path,
    run_id: str,
    state: dict[str, object],
) -> None:
    run_dir = workspace_root / "output" / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "run_state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
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


def _append_role_record(project_path: Path, payload: dict[str, object]) -> None:
    log_path = project_path / "role_invocations.jsonl"
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")


@pytest.mark.unit
def test_build_run_summary_aggregates_stage_model_role_and_scene_costs(tmp_path: Path) -> None:
    workspace_root = tmp_path
    project_path = workspace_root / "output" / "cost-project"
    _write_project_settings(project_path)

    _write_run_state(
        workspace_root=workspace_root,
        project_id="cost-project",
        project_path=project_path,
        run_id="run-cost-001",
        state={
            "run_id": "run-cost-001",
            "recipe_id": "mvp_ingest",
            "started_at": 10.0,
            "finished_at": 20.0,
            "project_cost_baseline_usd": 5.0,
            "runtime_params": {
                "run_budget_limit_usd": 1.5,
                "project_budget_limit_usd": 10.0,
                "budget_warning_threshold_ratio": 0.8,
            },
            "stage_order": ["analyze", "review"],
            "total_cost_usd": 1.5,
            "stages": {
                "analyze": {
                    "status": "done",
                    "model_used": "claude-sonnet-4-6",
                    "call_count": 4,
                    "attempt_count": 1,
                    "input_tokens": 400,
                    "output_tokens": 160,
                    "cost_usd": 1.2,
                    "duration_seconds": 12.0,
                    "artifact_refs": [
                        {"artifact_type": "scene", "entity_id": "scene_001", "version": 1},
                        {"artifact_type": "scene", "entity_id": "scene_002", "version": 1},
                    ],
                },
                "review": {
                    "status": "paused",
                    "model_used": "claude-haiku-4-5-20251001",
                    "call_count": 1,
                    "attempt_count": 1,
                    "input_tokens": 120,
                    "output_tokens": 30,
                    "cost_usd": 0.3,
                    "duration_seconds": 2.0,
                    "pause_reason": (
                        "Run budget cap reached. "
                        "Increase the budget and resume to continue."
                    ),
                    "artifact_refs": [],
                },
            },
        },
    )

    _append_role_record(
        project_path,
        {
            "run_id": "run-cost-001",
            "stage_id": "analyze",
            "scene_id": "scene_001",
            "entity_id": "scene_001",
            "role_id": "script_qa",
            "model": "gpt-4.1-mini",
            "response": {
                "cost_data": {
                    "estimated_cost_usd": 0.4,
                    "input_tokens": 100,
                    "output_tokens": 50,
                }
            },
        },
    )
    _append_role_record(
        project_path,
        {
            "run_id": "run-cost-001",
            "stage_id": "analyze",
            "scene_id": "scene_002",
            "entity_id": "scene_002",
            "role_id": "continuity_guard",
            "model": "gpt-4.1-mini",
            "response": {
                "cost_data": {
                    "estimated_cost_usd": 0.2,
                    "input_tokens": 60,
                    "output_tokens": 20,
                }
            },
        },
    )

    summary = CostTrackingService(workspace_root).build_run_summary(run_id="run-cost-001")

    assert summary.project_id == "cost-project"
    assert summary.status == "paused"
    assert summary.total_cost_usd == pytest.approx(1.5)
    assert [stage.stage_id for stage in summary.stages] == ["analyze", "review"]
    assert summary.stages[0].module_cost_usd == pytest.approx(0.6)
    assert summary.stages[0].role_cost_usd == pytest.approx(0.6)
    assert summary.stages[1].pause_reason is not None

    by_model = {item.model: item for item in summary.by_model}
    assert by_model["claude-sonnet-4-6"].estimated_cost_usd == pytest.approx(0.6)
    assert by_model["claude-sonnet-4-6"].call_count == 2
    assert by_model["gpt-4.1-mini"].estimated_cost_usd == pytest.approx(0.6)
    assert by_model["gpt-4.1-mini"].call_count == 2
    assert by_model["claude-haiku-4-5-20251001"].estimated_cost_usd == pytest.approx(0.3)

    by_role = {item.role_id: item for item in summary.by_role}
    assert by_role["script_qa"].scene_ids == ["scene_001"]
    assert by_role["script_qa"].estimated_cost_usd == pytest.approx(0.4)
    assert by_role["continuity_guard"].stage_ids == ["analyze"]

    by_scene = {item.scene_id: item for item in summary.by_scene}
    assert by_scene["scene_001"].estimated_cost_usd == pytest.approx(0.7)
    assert by_scene["scene_001"].attribution.kind.value == "allocated"
    assert by_scene["scene_002"].estimated_cost_usd == pytest.approx(0.5)

    budget_by_scope = {item.scope.value: item for item in summary.budget_statuses}
    assert budget_by_scope["run"].health.value == "limit_reached"
    assert budget_by_scope["project"].consumed_usd == pytest.approx(6.5)


@pytest.mark.unit
def test_build_project_summary_tracks_history_and_trend(tmp_path: Path) -> None:
    workspace_root = tmp_path
    project_path = workspace_root / "output" / "cost-project"
    _write_project_settings(project_path)

    costs = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
    for index, total_cost in enumerate(costs, start=1):
        _write_run_state(
            workspace_root=workspace_root,
            project_id="cost-project",
            project_path=project_path,
            run_id=f"run-{index:03d}",
            state={
                "run_id": f"run-{index:03d}",
                "recipe_id": "mvp_ingest",
                "started_at": float(index * 10),
                "finished_at": float(index * 10 + 5),
                "runtime_params": {},
                "total_cost_usd": total_cost,
                "stages": {
                    "only": {
                        "status": "done",
                        "artifact_refs": [],
                        "duration_seconds": 5.0,
                        "cost_usd": total_cost,
                    }
                },
            },
        )

    summary = CostTrackingService(workspace_root).build_project_summary(
        project_id="cost-project",
        project_path=project_path,
    )

    assert summary.project_id == "cost-project"
    assert summary.run_count == 6
    assert summary.total_cost_usd == pytest.approx(21.0)
    assert [point.run_id for point in summary.trend_points] == [
        "run-001",
        "run-002",
        "run-003",
        "run-004",
        "run-005",
        "run-006",
    ]
    assert summary.trend.direction == "up"
    assert summary.trend.recent_average_usd == pytest.approx(5.0)
    assert summary.trend.previous_average_usd == pytest.approx(2.0)
    assert summary.trend.delta_usd == pytest.approx(3.0)


@pytest.mark.unit
def test_run_status_from_state_uses_stage_order_for_sliced_runs() -> None:
    state = {
        "stage_order": ["look_and_feel"],
        "stages": {
            "intent_mood": {"status": "pending"},
            "look_and_feel": {"status": "done"},
            "sound_and_music": {"status": "pending"},
        },
    }

    assert run_status_from_state(state) == "done"
