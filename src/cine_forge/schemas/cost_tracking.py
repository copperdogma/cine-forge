"""Schemas for cost summaries, budgets, and immutable cost reports."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class BudgetScope(StrEnum):
    """Scopes where budget limits may apply."""

    PROJECT = "project"
    RUN = "run"
    STAGE = "stage"


class BudgetHealth(StrEnum):
    """Computed budget state for a scope."""

    OK = "ok"
    WARNING = "warning"
    LIMIT_REACHED = "limit_reached"


class CostAttributionKind(StrEnum):
    """How exact a cost breakdown is for a downstream dimension."""

    EXACT = "exact"
    ALLOCATED = "allocated"
    UNATTRIBUTED = "unattributed"


class BudgetConfig(BaseModel):
    """Project- and run-level budget settings."""

    project_budget_limit_usd: float | None = Field(default=None, ge=0.0)
    default_run_budget_limit_usd: float | None = Field(default=None, ge=0.0)
    budget_warning_threshold_ratio: float = Field(default=0.8, ge=0.0, le=1.0)
    stage_budget_limits_usd: dict[str, float] = Field(default_factory=dict)


class BudgetStatus(BaseModel):
    """Current budget consumption for one scope."""

    scope: BudgetScope
    limit_usd: float = Field(ge=0.0)
    consumed_usd: float = Field(ge=0.0)
    remaining_usd: float
    warning_threshold_ratio: float = Field(ge=0.0, le=1.0)
    warning_threshold_usd: float = Field(ge=0.0)
    health: BudgetHealth
    message: str | None = None


class CostAttribution(BaseModel):
    """Explain whether a cost figure is exact or allocated."""

    kind: CostAttributionKind
    basis: str = Field(min_length=1)


class StageCostSummary(BaseModel):
    """Cost summary for one pipeline stage."""

    stage_id: str
    status: str
    model_used: str | None = None
    call_count: int = Field(ge=0)
    attempt_count: int = Field(ge=0)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    estimated_cost_usd: float = Field(ge=0.0)
    module_cost_usd: float = Field(ge=0.0)
    role_cost_usd: float = Field(ge=0.0)
    duration_seconds: float = Field(ge=0.0)
    artifact_count: int = Field(ge=0)
    pause_reason: str | None = None


class ModelCostSummary(BaseModel):
    """Aggregate cost totals for one model."""

    model: str
    call_count: int = Field(ge=0)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    estimated_cost_usd: float = Field(ge=0.0)


class RoleCostSummary(BaseModel):
    """Aggregate cost totals for one role within a run."""

    role_id: str
    models: list[str] = Field(default_factory=list)
    call_count: int = Field(ge=0)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    estimated_cost_usd: float = Field(ge=0.0)
    stage_ids: list[str] = Field(default_factory=list)
    scene_ids: list[str] = Field(default_factory=list)
    entity_ids: list[str] = Field(default_factory=list)
    attribution: CostAttribution = Field(
        default_factory=lambda: CostAttribution(
            kind=CostAttributionKind.EXACT,
            basis="Derived from exact role invocation cost logs.",
        )
    )


class SceneCostSummary(BaseModel):
    """Aggregate cost totals for one scene within a run."""

    scene_id: str
    call_count: int = Field(ge=0)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    estimated_cost_usd: float = Field(ge=0.0)
    stage_ids: list[str] = Field(default_factory=list)
    attribution: CostAttribution


class RunCostOverview(BaseModel):
    """Thin project-history entry for one run."""

    run_id: str
    recipe_id: str
    status: str
    started_at: float | None = None
    finished_at: float | None = None
    total_cost_usd: float = Field(ge=0.0)
    duration_seconds: float = Field(ge=0.0)


class ProjectCostTrendPoint(BaseModel):
    """One point in the project cost trend series."""

    run_id: str
    started_at: float | None = None
    total_cost_usd: float = Field(ge=0.0)


class ProjectCostTrend(BaseModel):
    """Simple recent-vs-previous trend signal for project run costs."""

    direction: Literal["up", "down", "flat", "insufficient_data"] = "insufficient_data"
    recent_average_usd: float = Field(ge=0.0, default=0.0)
    previous_average_usd: float = Field(ge=0.0, default=0.0)
    delta_usd: float = 0.0


class RunCostSummary(BaseModel):
    """Detailed cost summary for one run."""

    run_id: str
    project_id: str
    recipe_id: str
    status: str
    started_at: float | None = None
    finished_at: float | None = None
    total_cost_usd: float = Field(ge=0.0)
    stages: list[StageCostSummary] = Field(default_factory=list)
    by_model: list[ModelCostSummary] = Field(default_factory=list)
    by_role: list[RoleCostSummary] = Field(default_factory=list)
    by_scene: list[SceneCostSummary] = Field(default_factory=list)
    budget_config: BudgetConfig = Field(default_factory=BudgetConfig)
    budget_statuses: list[BudgetStatus] = Field(default_factory=list)


class ProjectCostSummary(BaseModel):
    """Aggregate cost view across all runs in a project."""

    project_id: str
    total_cost_usd: float = Field(ge=0.0)
    run_count: int = Field(ge=0)
    runs: list[RunCostOverview] = Field(default_factory=list)
    trend_points: list[ProjectCostTrendPoint] = Field(default_factory=list)
    trend: ProjectCostTrend = Field(default_factory=ProjectCostTrend)
    budget_config: BudgetConfig = Field(default_factory=BudgetConfig)


class CostReport(BaseModel):
    """Immutable artifact containing a run's cost summary."""

    run_id: str
    project_id: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    summary: RunCostSummary
