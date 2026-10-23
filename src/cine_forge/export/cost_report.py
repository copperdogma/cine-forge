"""Deterministic CSV renderers retaining unresolved provider charge evidence."""

from __future__ import annotations

import csv
import io
from collections.abc import Iterable, Iterator
from typing import Any

from cine_forge.schemas import ProjectCostSummary, RunCostSummary
from cine_forge.schemas.cost_tracking import CostCompleteness
from cine_forge.schemas.media_cost import CostReceipt

_COMPLETENESS_FIELDS = [
    "cost_is_complete",
    "cost_status",
    "uncertain_cost_count",
    "component",
    "provider",
    "provider_job_id",
    "scene_id",
    "entity_id",
]


def render_run_cost_csv(summary: RunCostSummary) -> str:
    """Render run known subtotals and separate unresolved-charge rows as CSV."""
    fields = [
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
        *_COMPLETENESS_FIELDS,
    ]
    return _render_csv(fields, _run_rows(summary))


def _run_rows(summary: RunCostSummary) -> Iterator[dict[str, Any]]:
    yield {
        "section": "overview",
        "id": summary.run_id,
        "status": summary.status,
        "estimated_cost_usd": summary.total_cost_usd,
        "notes": f"recipe_id={summary.recipe_id}; {_subtotal_note(summary)}",
        **_completeness(summary),
    }
    for stage in summary.stages:
        yield {
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
            "notes": "; ".join(filter(None, [stage.pause_reason, _subtotal_note(stage)])),
            **_completeness(stage),
        }
    for model in summary.by_model:
        yield {
            "section": "model",
            "id": model.model,
            "model": model.model,
            "call_count": model.call_count,
            "input_tokens": model.input_tokens,
            "output_tokens": model.output_tokens,
            "estimated_cost_usd": model.estimated_cost_usd,
            "notes": _subtotal_note(model),
            **_completeness(model),
        }
    yield from _role_and_scene_rows(summary)
    for budget in summary.budget_statuses if summary.cost_is_complete else []:
        yield {
            "section": "budget",
            "id": budget.scope.value,
            "scope": budget.scope.value,
            "status": budget.health.value,
            "limit_usd": budget.limit_usd,
            "consumed_usd": budget.consumed_usd,
            "remaining_usd": budget.remaining_usd,
            "notes": "; ".join(filter(None, [budget.message, _subtotal_note(summary)])),
            **_completeness(summary),
        }
    yield from _uncertain_rows(summary.uncertain_cost_receipts)


def _role_and_scene_rows(summary: RunCostSummary) -> Iterator[dict[str, Any]]:
    for role in summary.by_role:
        yield {
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
                f"stages={','.join(role.stage_ids)}; scenes={','.join(role.scene_ids)};"
                f" entities={','.join(role.entity_ids)}"
            ),
        }
    for scene in summary.by_scene:
        yield {
            "section": "scene",
            "id": scene.scene_id,
            "call_count": scene.call_count,
            "input_tokens": scene.input_tokens,
            "output_tokens": scene.output_tokens,
            "estimated_cost_usd": scene.estimated_cost_usd,
            "attribution_kind": scene.attribution.kind,
            "attribution_basis": scene.attribution.basis,
            "notes": f"stages={','.join(scene.stage_ids)}; {_subtotal_note(scene)}",
            **_completeness(scene),
        }


def render_project_cost_csv(summary: ProjectCostSummary) -> str:
    """Render a project's known subtotal without presenting unknown charges as zero."""
    fields = [
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
        "model",
        *_COMPLETENESS_FIELDS,
    ]
    return _render_csv(fields, _project_rows(summary))


def _project_rows(summary: ProjectCostSummary) -> Iterator[dict[str, Any]]:
    yield {
        "section": "overview",
        "id": summary.project_id,
        "total_cost_usd": summary.total_cost_usd,
        "notes": f"run_count={summary.run_count}; {_subtotal_note(summary)}",
        **_completeness(summary),
    }
    yield {
        "section": "trend",
        "id": summary.project_id,
        "direction": summary.trend.direction,
        "recent_average_usd": summary.trend.recent_average_usd,
        "previous_average_usd": summary.trend.previous_average_usd,
        "delta_usd": summary.trend.delta_usd,
        "notes": _subtotal_note(summary.trend),
        **_completeness(summary.trend),
    }
    for run in summary.runs:
        yield {
            "section": "run",
            "id": run.run_id,
            "status": run.status,
            "started_at": run.started_at,
            "finished_at": run.finished_at,
            "total_cost_usd": run.total_cost_usd,
            "duration_seconds": run.duration_seconds,
            "notes": f"recipe_id={run.recipe_id}; {_subtotal_note(run)}",
            **_completeness(run),
        }
    config = summary.budget_config
    for scope, limit in [
        ("project", config.project_budget_limit_usd),
        ("run", config.default_run_budget_limit_usd),
    ]:
        if limit is not None:
            yield {
                "section": "budget",
                "id": scope,
                "limit_usd": limit,
                "warning_threshold_ratio": config.budget_warning_threshold_ratio,
            }
    yield from _uncertain_rows(summary.uncertain_cost_receipts)


def _completeness(summary: CostCompleteness) -> dict[str, Any]:
    return {
        "cost_is_complete": summary.cost_is_complete,
        "cost_status": "estimated" if summary.cost_is_complete else "known_subtotal",
        "uncertain_cost_count": len(summary.uncertain_cost_receipts),
    }


def _subtotal_note(summary: CostCompleteness) -> str:
    return (
        "" if summary.cost_is_complete else "Known subtotal; unresolved provider charges excluded."
    )


def _uncertain_rows(receipts: list[CostReceipt]) -> Iterator[dict[str, Any]]:
    for receipt in receipts:
        yield {
            "section": "uncertain_cost",
            "id": receipt.receipt_id,
            "status": receipt.status,
            "cost_status": "uncertain",
            "cost_is_complete": False,
            "model": receipt.model,
            "component": receipt.component,
            "provider": receipt.provider,
            "provider_job_id": receipt.provider_job_id,
            "scene_id": receipt.scene_id,
            "entity_id": receipt.entity_id,
            "notes": receipt.reason,
        }


def _render_csv(fields: list[str], rows: Iterable[dict[str, Any]]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()
