"""Deterministic CSV renderers for run/project cost summaries."""

from __future__ import annotations

import csv
import io

from cine_forge.schemas import ProjectCostSummary, RunCostSummary


def render_run_cost_csv(summary: RunCostSummary) -> str:
    """Render a detailed run cost summary as CSV."""
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=[
            "section",
            "id",
            "status",
            "model",
            "scope",
            "call_count",
            "input_tokens",
            "output_tokens",
            "estimated_cost_usd",
            "module_cost_usd",
            "role_cost_usd",
            "duration_seconds",
            "limit_usd",
            "consumed_usd",
            "remaining_usd",
            "attribution_kind",
            "attribution_basis",
            "notes",
        ],
    )
    writer.writeheader()
    writer.writerow(
        {
            "section": "overview",
            "id": summary.run_id,
            "status": summary.status,
            "estimated_cost_usd": summary.total_cost_usd,
            "notes": f"recipe_id={summary.recipe_id}",
        }
    )
    for stage in summary.stages:
        writer.writerow(
            {
                "section": "stage",
                "id": stage.stage_id,
                "status": stage.status,
                "model": stage.model_used,
                "call_count": stage.call_count,
                "input_tokens": stage.input_tokens,
                "output_tokens": stage.output_tokens,
                "estimated_cost_usd": stage.estimated_cost_usd,
                "module_cost_usd": stage.module_cost_usd,
                "role_cost_usd": stage.role_cost_usd,
                "duration_seconds": stage.duration_seconds,
                "notes": stage.pause_reason or "",
            }
        )
    for model in summary.by_model:
        writer.writerow(
            {
                "section": "model",
                "id": model.model,
                "model": model.model,
                "call_count": model.call_count,
                "input_tokens": model.input_tokens,
                "output_tokens": model.output_tokens,
                "estimated_cost_usd": model.estimated_cost_usd,
            }
        )
    for role in summary.by_role:
        writer.writerow(
            {
                "section": "role",
                "id": role.role_id,
                "model": ",".join(role.models),
                "call_count": role.call_count,
                "input_tokens": role.input_tokens,
                "output_tokens": role.output_tokens,
                "estimated_cost_usd": role.estimated_cost_usd,
                "attribution_kind": role.attribution.kind,
                "attribution_basis": role.attribution.basis,
                "notes": (
                    f"stages={','.join(role.stage_ids)};"
                    f" scenes={','.join(role.scene_ids)};"
                    f" entities={','.join(role.entity_ids)}"
                ),
            }
        )
    for scene in summary.by_scene:
        writer.writerow(
            {
                "section": "scene",
                "id": scene.scene_id,
                "call_count": scene.call_count,
                "input_tokens": scene.input_tokens,
                "output_tokens": scene.output_tokens,
                "estimated_cost_usd": scene.estimated_cost_usd,
                "attribution_kind": scene.attribution.kind,
                "attribution_basis": scene.attribution.basis,
                "notes": f"stages={','.join(scene.stage_ids)}",
            }
        )
    for budget in summary.budget_statuses:
        writer.writerow(
            {
                "section": "budget",
                "id": budget.scope.value,
                "scope": budget.scope.value,
                "status": budget.health.value,
                "limit_usd": budget.limit_usd,
                "consumed_usd": budget.consumed_usd,
                "remaining_usd": budget.remaining_usd,
                "notes": budget.message or "",
            }
        )
    return buffer.getvalue()


def render_project_cost_csv(summary: ProjectCostSummary) -> str:
    """Render a project cost summary as CSV."""
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=[
            "section",
            "id",
            "status",
            "started_at",
            "finished_at",
            "total_cost_usd",
            "duration_seconds",
            "direction",
            "recent_average_usd",
            "previous_average_usd",
            "delta_usd",
            "limit_usd",
            "warning_threshold_ratio",
            "notes",
        ],
    )
    writer.writeheader()
    writer.writerow(
        {
            "section": "overview",
            "id": summary.project_id,
            "total_cost_usd": summary.total_cost_usd,
            "notes": f"run_count={summary.run_count}",
        }
    )
    writer.writerow(
        {
            "section": "trend",
            "id": summary.project_id,
            "direction": summary.trend.direction,
            "recent_average_usd": summary.trend.recent_average_usd,
            "previous_average_usd": summary.trend.previous_average_usd,
            "delta_usd": summary.trend.delta_usd,
        }
    )
    for run in summary.runs:
        writer.writerow(
            {
                "section": "run",
                "id": run.run_id,
                "status": run.status,
                "started_at": run.started_at,
                "finished_at": run.finished_at,
                "total_cost_usd": run.total_cost_usd,
                "duration_seconds": run.duration_seconds,
                "notes": f"recipe_id={run.recipe_id}",
            }
        )
    if summary.budget_config.project_budget_limit_usd is not None:
        writer.writerow(
            {
                "section": "budget",
                "id": "project",
                "limit_usd": summary.budget_config.project_budget_limit_usd,
                "warning_threshold_ratio": summary.budget_config.budget_warning_threshold_ratio,
            }
        )
    if summary.budget_config.default_run_budget_limit_usd is not None:
        writer.writerow(
            {
                "section": "budget",
                "id": "run",
                "limit_usd": summary.budget_config.default_run_budget_limit_usd,
                "warning_threshold_ratio": summary.budget_config.budget_warning_threshold_ratio,
            }
        )
    return buffer.getvalue()
