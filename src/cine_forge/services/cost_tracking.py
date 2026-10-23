"""Cost summary, budget-status, and report-generation helpers."""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cine_forge.artifacts import ArtifactStore
from cine_forge.schemas import (
    ArtifactMetadata,
    BudgetConfig,
    BudgetHealth,
    BudgetScope,
    BudgetStatus,
    CostReport,
    ProjectCostSummary,
    ProjectCostTrend,
    ProjectCostTrendPoint,
    RoleCostSummary,
    RunCostOverview,
    RunCostSummary,
)
from cine_forge.schemas.media_cost import CostReceipt
from cine_forge.services.cost_summary_stages import summarize_stages


@dataclass(frozen=True)
class RoleInvocationCostRecord:
    """Exact cost record for one role invocation."""

    run_id: str | None
    stage_id: str | None
    scene_id: str | None
    entity_id: str | None
    role_id: str
    model: str
    estimated_cost_usd: float
    input_tokens: int
    output_tokens: int
    request_id: str | None = None


@dataclass(frozen=True)
class ProjectRunData:
    """Loaded run metadata plus state."""

    project_id: str
    project_path: Path
    run_dir: Path
    run_id: str
    state: dict[str, Any]


def load_project_budget_config(project_path: Path) -> BudgetConfig:
    """Read project budget settings from project.json."""
    project_json = project_path / "project.json"
    if not project_json.exists():
        return BudgetConfig()
    try:
        payload = json.loads(project_json.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return BudgetConfig()
    return BudgetConfig(
        project_budget_limit_usd=payload.get("project_budget_limit_usd"),
        default_run_budget_limit_usd=payload.get("default_run_budget_limit_usd"),
        budget_warning_threshold_ratio=payload.get("budget_warning_threshold_ratio", 0.8),
    )


def build_effective_budget_config(
    *,
    project_path: Path,
    runtime_params: dict[str, Any] | None = None,
) -> BudgetConfig:
    """Resolve the effective budget config for a run."""
    runtime_params = runtime_params or {}
    base = load_project_budget_config(project_path)

    project_limit = runtime_params.get("project_budget_limit_usd")
    run_limit = runtime_params.get("run_budget_limit_usd")
    threshold = runtime_params.get("budget_warning_threshold_ratio")

    return BudgetConfig(
        project_budget_limit_usd=(
            float(project_limit) if project_limit is not None else base.project_budget_limit_usd
        ),
        default_run_budget_limit_usd=(
            float(run_limit) if run_limit is not None else base.default_run_budget_limit_usd
        ),
        budget_warning_threshold_ratio=(
            float(threshold) if threshold is not None else base.budget_warning_threshold_ratio
        ),
        stage_budget_limits_usd=dict(base.stage_budget_limits_usd),
    )


def calculate_budget_statuses(
    *,
    total_cost_usd: float,
    project_cost_baseline_usd: float,
    budget_config: BudgetConfig,
) -> list[BudgetStatus]:
    """Compute current budget status for all configured scopes."""
    statuses: list[BudgetStatus] = []
    if budget_config.project_budget_limit_usd is not None:
        statuses.append(
            _build_budget_status(
                scope=BudgetScope.PROJECT,
                limit_usd=budget_config.project_budget_limit_usd,
                consumed_usd=project_cost_baseline_usd + total_cost_usd,
                warning_threshold_ratio=budget_config.budget_warning_threshold_ratio,
            )
        )
    if budget_config.default_run_budget_limit_usd is not None:
        statuses.append(
            _build_budget_status(
                scope=BudgetScope.RUN,
                limit_usd=budget_config.default_run_budget_limit_usd,
                consumed_usd=total_cost_usd,
                warning_threshold_ratio=budget_config.budget_warning_threshold_ratio,
            )
        )
    return statuses


def run_status_from_state(state: dict[str, Any]) -> str:
    """Derive the same run status label used by the API layer."""
    stage_map = state.get("stages", {})
    if not isinstance(stage_map, dict):
        return "pending"

    raw_stage_order = state.get("stage_order")
    if isinstance(raw_stage_order, list) and raw_stage_order:
        stage_ids = [str(stage_id) for stage_id in raw_stage_order if str(stage_id) in stage_map]
    else:
        stage_ids = list(stage_map.keys())

    statuses = {
        str(stage_map[stage_id].get("status", "pending"))
        for stage_id in stage_ids
        if isinstance(stage_map.get(stage_id), dict)
    }
    if "failed" in statuses:
        return "failed"
    if "running" in statuses:
        return "running"
    if "paused" in statuses:
        return "paused"
    if statuses and statuses <= {"done", "skipped_reused"}:
        return "done"
    return "pending"


class CostTrackingService:
    """Build typed run/project cost summaries from run state and role logs."""

    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root

    def load_run_data(self, run_id: str) -> ProjectRunData:
        """Load run state plus owning project metadata for one run id."""
        run_dir = self.workspace_root / "output" / "runs" / run_id
        state_path = run_dir / "run_state.json"
        if not state_path.exists():
            raise FileNotFoundError(f"Run state not found for run_id='{run_id}'.")
        state = json.loads(state_path.read_text(encoding="utf-8"))

        run_meta_path = run_dir / "run_meta.json"
        if not run_meta_path.exists():
            run_meta_path = run_dir / "operator_console_run_meta.json"
        if not run_meta_path.exists():
            raise FileNotFoundError(f"Run metadata not found for run_id='{run_id}'.")
        meta = json.loads(run_meta_path.read_text(encoding="utf-8"))
        project_id = str(meta.get("project_id") or "")
        project_path = Path(str(meta.get("project_path") or ""))
        if not project_id or not project_path:
            raise ValueError(f"Run metadata incomplete for run_id='{run_id}'.")
        return ProjectRunData(
            project_id=project_id,
            project_path=project_path,
            run_dir=run_dir,
            run_id=run_id,
            state=state,
        )

    def iter_project_runs(self, project_path: Path) -> list[ProjectRunData]:
        """Return all run-state payloads for a project, newest first."""
        runs_dir = self.workspace_root / "output" / "runs"
        if not runs_dir.exists():
            return []

        project_runs: list[ProjectRunData] = []
        for run_dir in sorted(
            runs_dir.iterdir(),
            key=lambda item: item.stat().st_mtime,
            reverse=True,
        ):
            if not run_dir.is_dir():
                continue
            run_meta_path = run_dir / "run_meta.json"
            if not run_meta_path.exists():
                run_meta_path = run_dir / "operator_console_run_meta.json"
            state_path = run_dir / "run_state.json"
            if not run_meta_path.exists() or not state_path.exists():
                continue
            try:
                meta = json.loads(run_meta_path.read_text(encoding="utf-8"))
                if meta.get("project_path") != str(project_path):
                    continue
                state = json.loads(state_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            project_runs.append(
                ProjectRunData(
                    project_id=str(meta.get("project_id") or project_path.name),
                    project_path=project_path,
                    run_dir=run_dir,
                    run_id=str(state.get("run_id") or run_dir.name),
                    state=state,
                )
            )
        return project_runs

    def historical_project_total_cost(
        self,
        *,
        project_path: Path,
        exclude_run_id: str | None = None,
    ) -> float:
        """Sum total historical run cost for a project."""
        total = 0.0
        for run_data in self.iter_project_runs(project_path):
            if exclude_run_id is not None and run_data.run_id == exclude_run_id:
                continue
            total += float(run_data.state.get("total_cost_usd", 0.0) or 0.0)
        return round(total, 8)

    def historical_project_cost_is_complete(
        self, *, project_path: Path, exclude_run_id: str | None = None,
    ) -> bool:
        """Check historical estimate coverage without recursively building summaries."""
        for run_data in self.iter_project_runs(project_path):
            if run_data.run_id == exclude_run_id:
                continue
            if not summarize_stages(
                run_data.state, [], run_id=run_data.run_id,
            ).cost_is_complete:
                return False
        return True

    def build_run_summary(
        self,
        *,
        run_id: str,
        project_id: str | None = None,
        project_path: Path | None = None,
    ) -> RunCostSummary:
        """Build a detailed typed cost summary for one run."""
        run_data = self.load_run_data(run_id)
        project_id = project_id or run_data.project_id
        project_path = project_path or run_data.project_path
        state = run_data.state
        role_records = self._load_role_records(project_path=project_path, run_id=run_id)
        details = summarize_stages(state, role_records, run_id=run_id)

        budget_config = build_effective_budget_config(
            project_path=project_path,
            runtime_params=state.get("runtime_params", {}),
        )
        project_cost_baseline_usd = float(
            state.get(
                "project_cost_baseline_usd",
                self.historical_project_total_cost(
                    project_path=project_path,
                    exclude_run_id=run_id,
                ),
            )
            or 0.0
        )
        budget_statuses = (
            calculate_budget_statuses(
                total_cost_usd=float(state.get("total_cost_usd", 0.0) or 0.0),
                project_cost_baseline_usd=project_cost_baseline_usd,
                budget_config=budget_config,
            )
            if details.cost_is_complete
            else []
        )
        if any(row.scope == BudgetScope.PROJECT for row in budget_statuses) and not (
            self.historical_project_cost_is_complete(
                project_path=project_path, exclude_run_id=run_id,
            )
        ):
            budget_statuses = [row for row in budget_statuses if row.scope != BudgetScope.PROJECT]

        return RunCostSummary(
            run_id=run_id,
            project_id=project_id,
            recipe_id=str(state.get("recipe_id", "unknown")),
            status=run_status_from_state(state),
            started_at=state.get("started_at"),
            finished_at=state.get("finished_at"),
            total_cost_usd=round(float(state.get("total_cost_usd", 0.0) or 0.0), 8),
            stages=details.summaries,
            by_model=details.dimensions.model_summaries(),
            by_role=self._build_role_summaries(role_records),
            by_scene=details.dimensions.scene_summaries(),
            cost_is_complete=details.cost_is_complete,
            uncertain_cost_receipts=details.uncertain,
            budget_config=budget_config,
            budget_statuses=budget_statuses,
        )

    def build_project_summary(
        self,
        *,
        project_id: str,
        project_path: Path,
    ) -> ProjectCostSummary:
        """Build a project-level historical cost summary."""
        runs = self.iter_project_runs(project_path)
        run_summaries = [
            self.build_run_summary(
                run_id=run_data.run_id,
                project_id=project_id,
                project_path=project_path,
            )
            for run_data in runs
        ]

        run_overviews = [
            RunCostOverview(
                run_id=summary.run_id,
                recipe_id=summary.recipe_id,
                status=summary.status,
                started_at=summary.started_at,
                finished_at=summary.finished_at,
                total_cost_usd=summary.total_cost_usd,
                duration_seconds=_duration_seconds(summary.started_at, summary.finished_at),
                cost_is_complete=summary.cost_is_complete,
                uncertain_cost_receipts=summary.uncertain_cost_receipts,
            )
            for summary in run_summaries
        ]
        total_cost_usd = round(
            sum(item.total_cost_usd for item in run_overviews),
            8,
        )
        chronological = sorted(
            run_overviews,
            key=lambda item: item.started_at or 0.0,
        )
        trend_points = [
            ProjectCostTrendPoint(
                run_id=item.run_id,
                started_at=item.started_at,
                total_cost_usd=item.total_cost_usd,
                cost_is_complete=item.cost_is_complete,
                uncertain_cost_receipts=item.uncertain_cost_receipts,
            )
            for item in chronological
        ]

        return ProjectCostSummary(
            project_id=project_id,
            total_cost_usd=total_cost_usd,
            run_count=len(run_overviews),
            runs=run_overviews,
            trend_points=trend_points,
            trend=_build_project_trend(chronological),
            cost_is_complete=all(run.cost_is_complete for run in run_overviews),
            uncertain_cost_receipts=_uncertain_receipts(run_overviews),
            budget_config=load_project_budget_config(project_path),
        )

    def persist_run_cost_report(
        self,
        *,
        project_id: str,
        project_path: Path,
        run_id: str,
    ):
        """Persist an immutable cost-report artifact for a run if missing."""
        store = ArtifactStore(project_dir=project_path)
        existing = store.list_versions("cost_report", run_id)
        if existing:
            return existing[-1]

        summary = self.build_run_summary(
            run_id=run_id,
            project_id=project_id,
            project_path=project_path,
        )
        report = CostReport(
            run_id=run_id,
            project_id=project_id,
            summary=summary,
        )
        metadata = ArtifactMetadata(
            intent="Capture immutable cost report for a pipeline run.",
            rationale="Generated deterministically from run state and role invocation logs.",
            confidence=1.0,
            source="code",
            producing_module="cost_tracking_v1",
            annotations={
                "run_id": run_id,
                "recipe_id": summary.recipe_id,
            },
        )
        return store.save_artifact(
            artifact_type="cost_report",
            entity_id=run_id,
            data=report.model_dump(mode="json"),
            metadata=metadata,
        )

    def _load_role_records(
        self,
        *,
        project_path: Path,
        run_id: str | None = None,
    ) -> list[RoleInvocationCostRecord]:
        """Read role invocation cost records for a project, optionally scoped to a run."""
        log_path = project_path / "role_invocations.jsonl"
        if not log_path.exists():
            return []

        records: list[RoleInvocationCostRecord] = []
        for line in log_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            payload_run_id = payload.get("run_id")
            if run_id is not None and payload_run_id != run_id:
                continue
            response_payload = payload.get("response", {})
            if not isinstance(response_payload, dict):
                response_payload = {}
            cost_data = response_payload.get("cost_data", {})
            if not isinstance(cost_data, dict):
                cost_data = {}
            records.append(
                RoleInvocationCostRecord(
                    run_id=payload_run_id if isinstance(payload_run_id, str) else None,
                    stage_id=(
                        payload.get("stage_id")
                        if isinstance(payload.get("stage_id"), str)
                        else None
                    ),
                    scene_id=(
                        payload.get("scene_id")
                        if isinstance(payload.get("scene_id"), str)
                        else None
                    ),
                    entity_id=(
                        payload.get("entity_id")
                        if isinstance(payload.get("entity_id"), str)
                        else None
                    ),
                    role_id=str(payload.get("role_id") or "unknown"),
                    model=str(payload.get("model") or "unknown"),
                    estimated_cost_usd=float(
                        cost_data.get(
                            "estimated_cost_usd",
                            payload.get("cost_usd", 0.0),
                        )
                        or 0.0
                    ),
                    input_tokens=int(cost_data.get("input_tokens", 0) or 0),
                    output_tokens=int(cost_data.get("output_tokens", 0) or 0),
                    request_id=cost_data.get("request_id"),
                )
            )
        return records

    @staticmethod
    def _build_role_summaries(
        records: list[RoleInvocationCostRecord],
    ) -> list[RoleCostSummary]:
        buckets: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "models": set(),
                "call_count": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "estimated_cost_usd": 0.0,
                "stage_ids": set(),
                "scene_ids": set(),
                "entity_ids": set(),
            }
        )
        for record in records:
            bucket = buckets[record.role_id]
            bucket["models"].add(record.model)
            bucket["call_count"] += 1
            bucket["input_tokens"] += record.input_tokens
            bucket["output_tokens"] += record.output_tokens
            bucket["estimated_cost_usd"] += record.estimated_cost_usd
            if record.stage_id:
                bucket["stage_ids"].add(record.stage_id)
            if record.scene_id:
                bucket["scene_ids"].add(record.scene_id)
            if record.entity_id:
                bucket["entity_ids"].add(record.entity_id)

        return [
            RoleCostSummary(
                role_id=role_id,
                models=sorted(bucket["models"]),
                call_count=bucket["call_count"],
                input_tokens=bucket["input_tokens"],
                output_tokens=bucket["output_tokens"],
                estimated_cost_usd=round(bucket["estimated_cost_usd"], 8),
                stage_ids=sorted(bucket["stage_ids"]),
                scene_ids=sorted(bucket["scene_ids"]),
                entity_ids=sorted(bucket["entity_ids"]),
            )
            for role_id, bucket in sorted(
                buckets.items(),
                key=lambda item: (-item[1]["estimated_cost_usd"], item[0]),
            )
        ]


def _build_budget_status(
    *,
    scope: BudgetScope,
    limit_usd: float,
    consumed_usd: float,
    warning_threshold_ratio: float,
) -> BudgetStatus:
    remaining_usd = round(limit_usd - consumed_usd, 8)
    warning_threshold_usd = round(limit_usd * warning_threshold_ratio, 8)
    if consumed_usd >= limit_usd:
        health = BudgetHealth.LIMIT_REACHED
        message = (
            f"{scope.value.capitalize()} budget cap reached: "
            f"${consumed_usd:.4f} used against ${limit_usd:.4f}."
        )
    elif consumed_usd >= warning_threshold_usd:
        health = BudgetHealth.WARNING
        message = (
            f"{scope.value.capitalize()} budget warning: "
            f"${consumed_usd:.4f} used against ${limit_usd:.4f}."
        )
    else:
        health = BudgetHealth.OK
        message = None
    return BudgetStatus(
        scope=scope,
        limit_usd=round(limit_usd, 8),
        consumed_usd=round(consumed_usd, 8),
        remaining_usd=remaining_usd,
        warning_threshold_ratio=warning_threshold_ratio,
        warning_threshold_usd=warning_threshold_usd,
        health=health,
        message=message,
    )


def _duration_seconds(started_at: float | None, finished_at: float | None) -> float:
    if started_at is None or finished_at is None:
        return 0.0
    return round(max(finished_at - started_at, 0.0), 4)


def _average(values: list[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 8)


def _uncertain_receipts(runs: list[RunCostOverview]) -> list[CostReceipt]:
    return list(
        {
            receipt.receipt_id: receipt for run in runs for receipt in run.uncertain_cost_receipts
        }.values()
    )


def _build_project_trend(chronological: list[RunCostOverview]) -> ProjectCostTrend:
    recent = chronological[-3:]
    previous = chronological[-6:-3]
    recent_average = _average([item.total_cost_usd for item in recent])
    previous_average = _average([item.total_cost_usd for item in previous])
    compared = previous + recent
    complete = all(item.cost_is_complete for item in compared)
    if not previous or not complete:
        direction = "insufficient_data"
    elif recent_average > previous_average + 1e-9:
        direction = "up"
    elif recent_average + 1e-9 < previous_average:
        direction = "down"
    else:
        direction = "flat"
    return ProjectCostTrend(
        direction=direction,
        cost_is_complete=complete,
        uncertain_cost_receipts=_uncertain_receipts(compared),
        recent_average_usd=recent_average,
        previous_average_usd=previous_average,
        delta_usd=round(recent_average - previous_average, 8),
    )
