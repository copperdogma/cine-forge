"""Budget warning and pause decisions for pipeline runs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cine_forge.schemas import BudgetHealth, BudgetStatus
from cine_forge.services.cost_tracking import (
    CostTrackingService,
    build_effective_budget_config,
    calculate_budget_statuses,
)


@dataclass(frozen=True)
class BudgetDecision:
    """Budget evaluation result after a completed stage or wave."""

    warnings: list[BudgetStatus]
    pause_status: BudgetStatus | None


class BudgetGuard:
    """Evaluate project/run budgets using persisted historical spend plus live run totals."""

    def __init__(
        self,
        *,
        workspace_root: Path,
        project_path: Path,
        run_id: str,
        runtime_params: dict[str, Any] | None = None,
    ) -> None:
        self._cost_tracking = CostTrackingService(workspace_root=workspace_root)
        self._budget_config = build_effective_budget_config(
            project_path=project_path,
            runtime_params=runtime_params,
        )
        self._project_cost_baseline_usd = self._cost_tracking.historical_project_total_cost(
            project_path=project_path,
            exclude_run_id=run_id,
        )

    @property
    def project_cost_baseline_usd(self) -> float:
        """Historical project spend snapshot captured when the run starts."""
        return self._project_cost_baseline_usd

    def evaluate(self, run_state: dict[str, Any], *, next_stage_id: str | None) -> BudgetDecision:
        """Evaluate live totals and decide whether to warn or pause before the next stage."""
        statuses = calculate_budget_statuses(
            total_cost_usd=float(run_state.get("total_cost_usd", 0.0) or 0.0),
            project_cost_baseline_usd=float(
                run_state.get("project_cost_baseline_usd", self._project_cost_baseline_usd) or 0.0
            ),
            budget_config=self._budget_config,
        )

        warning_scopes = set(run_state.get("budget_warning_scopes", []))
        warnings: list[BudgetStatus] = []
        pause_status: BudgetStatus | None = None
        for status in statuses:
            scope_key = status.scope.value
            if status.health == BudgetHealth.WARNING and scope_key not in warning_scopes:
                warnings.append(status)
                warning_scopes.add(scope_key)
            if (
                status.health == BudgetHealth.LIMIT_REACHED
                and next_stage_id is not None
                and pause_status is None
            ):
                pause_status = status
        run_state["budget_warning_scopes"] = sorted(warning_scopes)
        return BudgetDecision(warnings=warnings, pause_status=pause_status)
