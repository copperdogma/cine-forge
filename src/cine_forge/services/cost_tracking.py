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
    CostAttribution,
    CostAttributionKind,
    CostReport,
    ModelCostSummary,
    ProjectCostSummary,
    ProjectCostTrend,
    ProjectCostTrendPoint,
    RoleCostSummary,
    RunCostOverview,
    RunCostSummary,
    SceneCostSummary,
    StageCostSummary,
)


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
            float(project_limit)
            if project_limit is not None
            else base.project_budget_limit_usd
        ),
        default_run_budget_limit_usd=(
            float(run_limit)
            if run_limit is not None
            else base.default_run_budget_limit_usd
        ),
        budget_warning_threshold_ratio=(
            float(threshold)
            if threshold is not None
            else base.budget_warning_threshold_ratio
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
        stage_ids = [
            str(stage_id)
            for stage_id in raw_stage_order
            if str(stage_id) in stage_map
        ]
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
        role_records_by_stage = self._group_role_records_by_stage(role_records)
        stage_order = list(state.get("stage_order") or state.get("stages", {}).keys())

        stage_summaries: list[StageCostSummary] = []
        by_model_mut = defaultdict(lambda: {
            "call_count": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": 0.0,
        })
        scene_mut: dict[str, dict[str, Any]] = {}

        for stage_id in stage_order:
            stage = state.get("stages", {}).get(stage_id, {}) or {}
            stage_role_records = role_records_by_stage.get(stage_id, [])

            role_call_count = len(stage_role_records)
            role_input_tokens = sum(record.input_tokens for record in stage_role_records)
            role_output_tokens = sum(record.output_tokens for record in stage_role_records)
            role_cost_usd = round(
                sum(record.estimated_cost_usd for record in stage_role_records),
                8,
            )

            total_call_count = int(stage.get("call_count", 0) or 0)
            total_input_tokens = int(stage.get("input_tokens", 0) or 0)
            total_output_tokens = int(stage.get("output_tokens", 0) or 0)
            total_cost_usd = float(stage.get("cost_usd", 0.0) or 0.0)

            module_call_count = max(total_call_count - role_call_count, 0)
            module_input_tokens = max(total_input_tokens - role_input_tokens, 0)
            module_output_tokens = max(total_output_tokens - role_output_tokens, 0)
            module_cost_usd = round(max(total_cost_usd - role_cost_usd, 0.0), 8)

            stage_summary = StageCostSummary(
                stage_id=stage_id,
                status=str(stage.get("status", "pending")),
                model_used=(
                    str(stage.get("model_used"))
                    if stage.get("model_used") is not None
                    else None
                ),
                call_count=total_call_count,
                attempt_count=int(stage.get("attempt_count", 0) or 0),
                input_tokens=total_input_tokens,
                output_tokens=total_output_tokens,
                estimated_cost_usd=round(total_cost_usd, 8),
                module_cost_usd=module_cost_usd,
                role_cost_usd=role_cost_usd,
                duration_seconds=float(stage.get("duration_seconds", 0.0) or 0.0),
                artifact_count=(
                    len(stage.get("artifact_refs", []))
                    if isinstance(stage.get("artifact_refs"), list)
                    else 0
                ),
                pause_reason=stage.get("pause_reason"),
            )
            stage_summaries.append(stage_summary)

            model_name = stage_summary.model_used or "code"
            if module_cost_usd > 0.0 or module_call_count > 0:
                bucket = by_model_mut[model_name]
                bucket["call_count"] += module_call_count
                bucket["input_tokens"] += module_input_tokens
                bucket["output_tokens"] += module_output_tokens
                bucket["estimated_cost_usd"] += module_cost_usd

            scene_ids = _scene_ids_for_stage(stage)
            if scene_ids:
                split_costs = _split_float(module_cost_usd, len(scene_ids))
                split_calls = _split_int(module_call_count, len(scene_ids))
                split_inputs = _split_int(module_input_tokens, len(scene_ids))
                split_outputs = _split_int(module_output_tokens, len(scene_ids))
                for idx, scene_id in enumerate(scene_ids):
                    entry = scene_mut.setdefault(
                        scene_id,
                        {
                            "call_count": 0,
                            "input_tokens": 0,
                            "output_tokens": 0,
                            "estimated_cost_usd": 0.0,
                            "stage_ids": set(),
                            "notes": [],
                            "has_allocated": False,
                            "has_exact": False,
                        },
                    )
                    entry["call_count"] += split_calls[idx]
                    entry["input_tokens"] += split_inputs[idx]
                    entry["output_tokens"] += split_outputs[idx]
                    entry["estimated_cost_usd"] += split_costs[idx]
                    entry["stage_ids"].add(stage_id)
                    entry["has_allocated"] = True
                    entry["notes"].append(
                        "Equal allocation from stage "
                        f"'{stage_id}' across {len(scene_ids)} scene outputs."
                    )

        for record in role_records:
            bucket = by_model_mut[record.model]
            bucket["call_count"] += 1
            bucket["input_tokens"] += record.input_tokens
            bucket["output_tokens"] += record.output_tokens
            bucket["estimated_cost_usd"] += record.estimated_cost_usd

            if record.scene_id:
                entry = scene_mut.setdefault(
                    record.scene_id,
                    {
                        "call_count": 0,
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "estimated_cost_usd": 0.0,
                        "stage_ids": set(),
                        "notes": [],
                        "has_allocated": False,
                        "has_exact": False,
                    },
                )
                entry["call_count"] += 1
                entry["input_tokens"] += record.input_tokens
                entry["output_tokens"] += record.output_tokens
                entry["estimated_cost_usd"] += record.estimated_cost_usd
                if record.stage_id:
                    entry["stage_ids"].add(record.stage_id)
                entry["has_exact"] = True
                entry["notes"].append(
                    f"Exact role invocation cost from '{record.role_id}'."
                )

        by_model = [
            ModelCostSummary(
                model=model,
                call_count=values["call_count"],
                input_tokens=values["input_tokens"],
                output_tokens=values["output_tokens"],
                estimated_cost_usd=round(values["estimated_cost_usd"], 8),
            )
            for model, values in sorted(
                by_model_mut.items(),
                key=lambda item: (-item[1]["estimated_cost_usd"], item[0]),
            )
            if values["call_count"] > 0 or values["estimated_cost_usd"] > 0.0
        ]

        by_role = self._build_role_summaries(role_records)
        by_scene = [
            SceneCostSummary(
                scene_id=scene_id,
                call_count=entry["call_count"],
                input_tokens=entry["input_tokens"],
                output_tokens=entry["output_tokens"],
                estimated_cost_usd=round(entry["estimated_cost_usd"], 8),
                stage_ids=sorted(entry["stage_ids"]),
                attribution=CostAttribution(
                    kind=(
                        CostAttributionKind.ALLOCATED
                        if entry["has_allocated"]
                        else CostAttributionKind.EXACT
                    ),
                    basis=" ".join(dict.fromkeys(entry["notes"])),
                ),
            )
            for scene_id, entry in sorted(scene_mut.items())
            if entry["estimated_cost_usd"] > 0.0 or entry["call_count"] > 0
        ]

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
        budget_statuses = calculate_budget_statuses(
            total_cost_usd=float(state.get("total_cost_usd", 0.0) or 0.0),
            project_cost_baseline_usd=project_cost_baseline_usd,
            budget_config=budget_config,
        )

        return RunCostSummary(
            run_id=run_id,
            project_id=project_id,
            recipe_id=str(state.get("recipe_id", "unknown")),
            status=run_status_from_state(state),
            started_at=state.get("started_at"),
            finished_at=state.get("finished_at"),
            total_cost_usd=round(float(state.get("total_cost_usd", 0.0) or 0.0), 8),
            stages=stage_summaries,
            by_model=by_model,
            by_role=by_role,
            by_scene=by_scene,
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
            )
            for item in chronological
        ]

        recent = chronological[-3:]
        previous = chronological[-6:-3]
        recent_average = _average([item.total_cost_usd for item in recent])
        previous_average = _average([item.total_cost_usd for item in previous])
        if not previous:
            direction = "insufficient_data"
        elif recent_average > previous_average + 1e-9:
            direction = "up"
        elif recent_average + 1e-9 < previous_average:
            direction = "down"
        else:
            direction = "flat"

        return ProjectCostSummary(
            project_id=project_id,
            total_cost_usd=total_cost_usd,
            run_count=len(run_overviews),
            runs=run_overviews,
            trend_points=trend_points,
            trend=ProjectCostTrend(
                direction=direction,
                recent_average_usd=recent_average,
                previous_average_usd=previous_average,
                delta_usd=round(recent_average - previous_average, 8),
            ),
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
                )
            )
        return records

    @staticmethod
    def _group_role_records_by_stage(
        records: list[RoleInvocationCostRecord],
    ) -> dict[str, list[RoleInvocationCostRecord]]:
        grouped: dict[str, list[RoleInvocationCostRecord]] = defaultdict(list)
        for record in records:
            if record.stage_id is not None:
                grouped[record.stage_id].append(record)
        return grouped

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


def _scene_ids_for_stage(stage: dict[str, Any]) -> list[str]:
    refs = stage.get("artifact_refs", [])
    if not isinstance(refs, list):
        return []
    scene_ids: set[str] = set()
    for ref in refs:
        if not isinstance(ref, dict):
            continue
        entity_id = ref.get("entity_id")
        if _is_exact_scene_id(entity_id):
            scene_ids.add(str(entity_id))
    return sorted(scene_ids)


def _is_exact_scene_id(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    parts = value.split("_")
    return len(parts) == 2 and parts[0] == "scene" and parts[1].isdigit()


def _split_int(total: int, parts: int) -> list[int]:
    if parts <= 0:
        return []
    base, remainder = divmod(int(total), parts)
    return [base + (1 if idx < remainder else 0) for idx in range(parts)]


def _split_float(total: float, parts: int) -> list[float]:
    if parts <= 0:
        return []
    if parts == 1:
        return [round(total, 8)]
    base = round(total / parts, 8)
    values = [base for _ in range(parts - 1)]
    tail = round(total - sum(values), 8)
    values.append(tail)
    return values


def _duration_seconds(started_at: float | None, finished_at: float | None) -> float:
    if started_at is None or finished_at is None:
        return 0.0
    return round(max(finished_at - started_at, 0.0), 4)


def _average(values: list[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 8)
