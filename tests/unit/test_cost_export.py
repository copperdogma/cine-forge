from __future__ import annotations

import pytest

from cine_forge.export.cost_report import render_project_cost_csv, render_run_cost_csv
from cine_forge.schemas import (
    BudgetConfig,
    BudgetHealth,
    BudgetScope,
    BudgetStatus,
    CostAttribution,
    CostAttributionKind,
    ModelCostSummary,
    ProjectCostSummary,
    ProjectCostTrend,
    RoleCostSummary,
    RunCostOverview,
    RunCostSummary,
    SceneCostSummary,
    StageCostSummary,
)


@pytest.mark.unit
def test_run_cost_csv_includes_stage_role_scene_and_budget_sections() -> None:
    summary = RunCostSummary(
        run_id="run-cost-001",
        project_id="cost-project",
        recipe_id="mvp_ingest",
        status="paused",
        total_cost_usd=1.5,
        stages=[
            StageCostSummary(
                stage_id="analyze",
                status="done",
                model_used="claude-sonnet-4-6",
                call_count=2,
                attempt_count=1,
                input_tokens=200,
                output_tokens=80,
                estimated_cost_usd=1.2,
                module_cost_usd=0.6,
                role_cost_usd=0.6,
                duration_seconds=12.0,
                artifact_count=2,
            )
        ],
        by_model=[
            ModelCostSummary(
                model="claude-sonnet-4-6",
                call_count=2,
                input_tokens=200,
                output_tokens=80,
                estimated_cost_usd=0.6,
            )
        ],
        by_role=[
            RoleCostSummary(
                role_id="script_qa",
                models=["gpt-4.1-mini"],
                call_count=1,
                input_tokens=100,
                output_tokens=50,
                estimated_cost_usd=0.4,
                stage_ids=["analyze"],
                scene_ids=["scene_001"],
                entity_ids=["scene_001"],
            )
        ],
        by_scene=[
            SceneCostSummary(
                scene_id="scene_001",
                call_count=1,
                input_tokens=100,
                output_tokens=50,
                estimated_cost_usd=0.7,
                stage_ids=["analyze"],
                attribution=CostAttribution(
                    kind=CostAttributionKind.ALLOCATED,
                    basis="Equal allocation from stage output.",
                ),
            )
        ],
        budget_config=BudgetConfig(default_run_budget_limit_usd=1.5),
        budget_statuses=[
            BudgetStatus(
                scope=BudgetScope.RUN,
                limit_usd=1.5,
                consumed_usd=1.5,
                remaining_usd=0.0,
                warning_threshold_ratio=0.8,
                warning_threshold_usd=1.2,
                health=BudgetHealth.LIMIT_REACHED,
                message="Run budget cap reached.",
            )
        ],
    )

    csv_content = render_run_cost_csv(summary)

    assert "section,id,status,model,scope" in csv_content
    assert "overview,run-cost-001,paused" in csv_content
    assert "stage,analyze,done,claude-sonnet-4-6" in csv_content
    assert "role,script_qa" in csv_content
    assert "scene,scene_001" in csv_content
    assert "budget,run,limit_reached" in csv_content


@pytest.mark.unit
def test_project_cost_csv_includes_overview_trend_and_run_rows() -> None:
    summary = ProjectCostSummary(
        project_id="cost-project",
        total_cost_usd=6.0,
        run_count=2,
        runs=[
            RunCostOverview(
                run_id="run-002",
                recipe_id="mvp_ingest",
                status="done",
                started_at=20.0,
                finished_at=25.0,
                total_cost_usd=4.0,
                duration_seconds=5.0,
            ),
            RunCostOverview(
                run_id="run-001",
                recipe_id="mvp_ingest",
                status="done",
                started_at=10.0,
                finished_at=15.0,
                total_cost_usd=2.0,
                duration_seconds=5.0,
            ),
        ],
        trend=ProjectCostTrend(
            direction="up",
            recent_average_usd=4.0,
            previous_average_usd=2.0,
            delta_usd=2.0,
        ),
        budget_config=BudgetConfig(project_budget_limit_usd=12.0),
    )

    csv_content = render_project_cost_csv(summary)

    assert "overview,cost-project" in csv_content
    assert "trend,cost-project" in csv_content
    assert "run,run-002,done" in csv_content
    assert "budget,project" in csv_content
