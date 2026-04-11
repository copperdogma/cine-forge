from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median
from typing import Literal

from pydantic import BaseModel, Field

TEXT_EXTENSIONS = {
    ".csv",
    ".fountain",
    ".json",
    ".md",
    ".py",
    ".txt",
    ".yaml",
    ".yml",
}


class ThroughputRecipeSpec(BaseModel):
    recipe_id: str = Field(min_length=1)
    recipe_path: str = Field(min_length=1)
    ui_label: str | None = None
    notes: str | None = None


class ThroughputEvalCase(BaseModel):
    case_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    input_fixture: str = Field(min_length=1)
    notes: str | None = None


class ThroughputEvalManifest(BaseModel):
    boundary_id: str = Field(min_length=1)
    boundary_label: str = Field(min_length=1)
    honest_scope: str = Field(min_length=1)
    recipes: list[ThroughputRecipeSpec] = Field(min_length=1)
    cases: list[ThroughputEvalCase] = Field(min_length=1)


class OutputVolumeEvidence(BaseModel):
    artifact_count: int = Field(ge=0, default=0)
    total_bytes: int = Field(ge=0, default=0)
    text_characters: int = Field(ge=0, default=0)
    text_lines: int = Field(ge=0, default=0)
    by_artifact_type: dict[str, int] = Field(default_factory=dict)


class StageThroughputSummary(BaseModel):
    stage_id: str
    status: str
    model_used: str | None = None
    call_count: int = Field(ge=0, default=0)
    attempt_count: int = Field(ge=0, default=0)
    duration_ms: int = Field(ge=0, default=0)
    cost_usd: float = Field(ge=0.0, default=0.0)
    input_tokens: int = Field(ge=0, default=0)
    output_tokens: int = Field(ge=0, default=0)
    output_volume: OutputVolumeEvidence = Field(default_factory=OutputVolumeEvidence)


class RecipeRunSummary(BaseModel):
    run_id: str
    recipe_id: str
    recipe_path: str
    ui_label: str | None = None
    elapsed_ms: int = Field(ge=0, default=0)
    success: bool
    error: str | None = None
    stage_summaries: list[StageThroughputSummary] = Field(default_factory=list)
    total_duration_ms: int = Field(ge=0, default=0)
    total_cost_usd: float = Field(ge=0.0, default=0.0)
    total_input_tokens: int = Field(ge=0, default=0)
    total_output_tokens: int = Field(ge=0, default=0)
    output_volume: OutputVolumeEvidence = Field(default_factory=OutputVolumeEvidence)


class CaseBoundaryResult(BaseModel):
    case_id: str
    label: str
    input_fixture: str
    input_word_count: int = Field(ge=0)
    input_line_count: int = Field(ge=0)
    input_bytes: int = Field(ge=0)
    notes: str | None = None
    project_dir: str
    success: bool
    error: str | None = None
    total_elapsed_ms: int = Field(ge=0, default=0)
    total_duration_ms: int = Field(ge=0, default=0)
    total_cost_usd: float = Field(ge=0.0, default=0.0)
    total_input_tokens: int = Field(ge=0, default=0)
    total_output_tokens: int = Field(ge=0, default=0)
    output_volume: OutputVolumeEvidence = Field(default_factory=OutputVolumeEvidence)
    recipe_runs: list[RecipeRunSummary] = Field(default_factory=list)


class BudgetMeasurement(BaseModel):
    current_label: str = "current_observed"
    climb_label: str = "climb_target"
    current_duration_ms_per_1k_words: float | None = Field(default=None, ge=0.0)
    climb_target_duration_ms_per_1k_words: float | None = Field(default=None, ge=0.0)
    current_cost_usd_per_1k_words: float | None = Field(default=None, ge=0.0)
    climb_target_cost_usd_per_1k_words: float | None = Field(default=None, ge=0.0)
    current_output_tokens_per_1k_words: float | None = Field(default=None, ge=0.0)
    climb_target_output_tokens_per_1k_words: float | None = Field(default=None, ge=0.0)
    current_output_bytes_per_1k_words: float | None = Field(default=None, ge=0.0)
    climb_target_output_bytes_per_1k_words: float | None = Field(default=None, ge=0.0)


class BudgetRow(BaseModel):
    scope_type: Literal["boundary", "recipe", "stage"]
    scope_id: str
    scope_label: str
    case_count: int = Field(ge=0, default=0)
    measurement: BudgetMeasurement
    median_duration_share: float | None = Field(default=None, ge=0.0, le=1.0)
    median_output_share: float | None = Field(default=None, ge=0.0, le=1.0)
    note: str | None = None


def display_repo_relative_path(path: Path, repo_root: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(repo_root))
    except ValueError:
        return str(resolved)


def measure_fixture_input(path: Path) -> dict[str, int]:
    raw_bytes = path.read_bytes()
    text = raw_bytes.decode("utf-8", errors="ignore")
    return {
        "input_bytes": len(raw_bytes),
        "input_line_count": len(text.splitlines()),
        "input_word_count": count_words(text),
    }


def count_words(text: str) -> int:
    matches = re.findall(r"[A-Za-z0-9']+", text)
    return len(matches)


def build_output_volume_evidence(
    artifact_refs: list[dict],
    *,
    project_dir: Path,
    repo_root: Path,
) -> OutputVolumeEvidence:
    counts: Counter[str] = Counter()
    total_bytes = 0
    text_characters = 0
    text_lines = 0

    for ref in artifact_refs:
        if not isinstance(ref, dict):
            continue
        artifact_type = str(ref.get("artifact_type", "unknown"))
        counts[artifact_type] += 1
        artifact_path = resolve_artifact_path(
            ref.get("path"),
            project_dir=project_dir,
            repo_root=repo_root,
        )
        if artifact_path is None or not artifact_path.exists() or not artifact_path.is_file():
            continue
        raw_bytes = artifact_path.read_bytes()
        total_bytes += len(raw_bytes)
        text = decode_text_payload(raw_bytes, artifact_path)
        if text is None:
            continue
        text_characters += len(text)
        text_lines += len(text.splitlines())

    return OutputVolumeEvidence(
        artifact_count=sum(counts.values()),
        total_bytes=total_bytes,
        text_characters=text_characters,
        text_lines=text_lines,
        by_artifact_type=dict(counts),
    )


def resolve_artifact_path(
    raw_path: object,
    *,
    project_dir: Path,
    repo_root: Path,
) -> Path | None:
    if not isinstance(raw_path, str) or not raw_path.strip():
        return None
    candidate = Path(raw_path)
    if candidate.is_absolute():
        return candidate
    project_candidate = project_dir / candidate
    if project_candidate.exists():
        return project_candidate
    repo_candidate = repo_root / candidate
    if repo_candidate.exists():
        return repo_candidate
    return project_candidate


def decode_text_payload(raw_bytes: bytes, artifact_path: Path) -> str | None:
    if artifact_path.suffix.lower() in TEXT_EXTENSIONS:
        return raw_bytes.decode("utf-8", errors="ignore")
    if b"\x00" in raw_bytes:
        return None
    try:
        return raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return None


def merge_output_volumes(volumes: list[OutputVolumeEvidence]) -> OutputVolumeEvidence:
    counts: Counter[str] = Counter()
    total_bytes = 0
    text_characters = 0
    text_lines = 0
    artifact_count = 0

    for volume in volumes:
        counts.update(volume.by_artifact_type)
        total_bytes += volume.total_bytes
        text_characters += volume.text_characters
        text_lines += volume.text_lines
        artifact_count += volume.artifact_count

    return OutputVolumeEvidence(
        artifact_count=artifact_count,
        total_bytes=total_bytes,
        text_characters=text_characters,
        text_lines=text_lines,
        by_artifact_type=dict(counts),
    )


def build_recipe_run_summary(
    *,
    state: dict | None,
    recipe_path: Path,
    ui_label: str | None,
    project_dir: Path,
    repo_root: Path,
    run_id: str,
    elapsed_ms: int,
    error: str | None,
) -> RecipeRunSummary:
    if state is None:
        return RecipeRunSummary(
            run_id=run_id,
            recipe_id=recipe_path.stem,
            recipe_path=display_repo_relative_path(recipe_path, repo_root),
            ui_label=ui_label,
            elapsed_ms=elapsed_ms,
            success=False,
            error=error or "run state unavailable",
        )

    stage_order = list(state.get("stage_order") or state.get("stages", {}).keys())
    stage_summaries: list[StageThroughputSummary] = []
    for stage_id in stage_order:
        stage_data = state.get("stages", {}).get(stage_id, {}) or {}
        output_volume = build_output_volume_evidence(
            stage_data.get("artifact_refs", []),
            project_dir=project_dir,
            repo_root=repo_root,
        )
        stage_summaries.append(
            StageThroughputSummary(
                stage_id=stage_id,
                status=str(stage_data.get("status", "unknown")),
                model_used=(
                    str(stage_data.get("model_used"))
                    if stage_data.get("model_used") is not None
                    else None
                ),
                call_count=int(stage_data.get("call_count", 0) or 0),
                attempt_count=int(stage_data.get("attempt_count", 0) or 0),
                duration_ms=round(float(stage_data.get("duration_seconds", 0.0) or 0.0) * 1000),
                cost_usd=float(stage_data.get("cost_usd", 0.0) or 0.0),
                input_tokens=int(stage_data.get("input_tokens", 0) or 0),
                output_tokens=int(stage_data.get("output_tokens", 0) or 0),
                output_volume=output_volume,
            )
        )

    recipe_volume = merge_output_volumes([stage.output_volume for stage in stage_summaries])
    success = state_succeeded(state) and error is None
    return RecipeRunSummary(
        run_id=run_id,
        recipe_id=str(state.get("recipe_id", recipe_path.stem)),
        recipe_path=display_repo_relative_path(recipe_path, repo_root),
        ui_label=ui_label,
        elapsed_ms=elapsed_ms,
        success=success,
        error=None if success else error,
        stage_summaries=stage_summaries,
        total_duration_ms=sum(stage.duration_ms for stage in stage_summaries),
        total_cost_usd=float(state.get("total_cost_usd", 0.0) or 0.0),
        total_input_tokens=sum(stage.input_tokens for stage in stage_summaries),
        total_output_tokens=sum(stage.output_tokens for stage in stage_summaries),
        output_volume=recipe_volume,
    )


def build_case_result(
    *,
    case: ThroughputEvalCase,
    input_metrics: dict[str, int],
    project_dir: Path,
    repo_root: Path,
    recipe_runs: list[RecipeRunSummary],
) -> CaseBoundaryResult:
    success = all(recipe.success for recipe in recipe_runs)
    error = next((recipe.error for recipe in recipe_runs if recipe.error), None)
    output_volume = merge_output_volumes([recipe.output_volume for recipe in recipe_runs])
    return CaseBoundaryResult(
        case_id=case.case_id,
        label=case.label,
        input_fixture=case.input_fixture,
        input_word_count=int(input_metrics["input_word_count"]),
        input_line_count=int(input_metrics["input_line_count"]),
        input_bytes=int(input_metrics["input_bytes"]),
        notes=case.notes,
        project_dir=display_repo_relative_path(project_dir, repo_root),
        success=success,
        error=error,
        total_elapsed_ms=sum(recipe.elapsed_ms for recipe in recipe_runs),
        total_duration_ms=sum(recipe.total_duration_ms for recipe in recipe_runs),
        total_cost_usd=round(sum(recipe.total_cost_usd for recipe in recipe_runs), 8),
        total_input_tokens=sum(recipe.total_input_tokens for recipe in recipe_runs),
        total_output_tokens=sum(recipe.total_output_tokens for recipe in recipe_runs),
        output_volume=output_volume,
        recipe_runs=recipe_runs,
    )


def state_succeeded(state: dict | None) -> bool:
    if not state:
        return False
    stage_ids = list(state.get("stage_order") or state.get("stages", {}).keys())
    if not stage_ids:
        return False
    statuses = {
        str(state.get("stages", {}).get(stage_id, {}).get("status", "unknown"))
        for stage_id in stage_ids
    }
    if "failed" in statuses:
        return False
    return all(status in {"done", "skipped_reused"} for status in statuses)


def derive_budget_rows(results: list[CaseBoundaryResult]) -> list[BudgetRow]:
    source_results = [result for result in results if result.success] or list(results)
    rows: list[BudgetRow] = []
    if not source_results:
        return rows

    rows.append(
        BudgetRow(
            scope_type="boundary",
            scope_id="story_lane_workspace_ready",
            scope_label="Story-lane workspace-ready boundary",
            case_count=len(source_results),
            measurement=_build_budget_measurement(
                rates=[
                    {
                        "duration": per_1k_words(result.total_elapsed_ms, result.input_word_count),
                        "cost": per_1k_words(result.total_cost_usd, result.input_word_count),
                        "output_tokens": per_1k_words(
                            result.total_output_tokens,
                            result.input_word_count,
                        ),
                        "output_bytes": per_1k_words(
                            result.output_volume.total_bytes,
                            result.input_word_count,
                        ),
                    }
                    for result in source_results
                ]
            ),
            note=(
                "Median is the current budget; best observed normalized rate is the next "
                "climb target."
            ),
        )
    )

    recipe_rates: dict[str, list[dict[str, float]]] = defaultdict(list)
    recipe_labels: dict[str, str] = {}
    stage_rates: dict[tuple[str, str], list[dict[str, float]]] = defaultdict(list)

    for result in source_results:
        total_elapsed = max(result.total_elapsed_ms, 1)
        total_output_tokens = max(result.total_output_tokens, 1)
        for recipe in result.recipe_runs:
            recipe_label = recipe.ui_label or recipe.recipe_id
            recipe_labels[recipe.recipe_id] = recipe_label
            recipe_rates[recipe.recipe_id].append(
                {
                    "duration": per_1k_words(recipe.elapsed_ms, result.input_word_count),
                    "cost": per_1k_words(recipe.total_cost_usd, result.input_word_count),
                    "output_tokens": per_1k_words(
                        recipe.total_output_tokens,
                        result.input_word_count,
                    ),
                    "output_bytes": per_1k_words(
                        recipe.output_volume.total_bytes,
                        result.input_word_count,
                    ),
                    "duration_share": round(recipe.elapsed_ms / total_elapsed, 4),
                    "output_share": round(recipe.total_output_tokens / total_output_tokens, 4),
                }
            )
            for stage in recipe.stage_summaries:
                stage_rates[(recipe.recipe_id, stage.stage_id)].append(
                    {
                        "duration": per_1k_words(stage.duration_ms, result.input_word_count),
                        "cost": per_1k_words(stage.cost_usd, result.input_word_count),
                        "output_tokens": per_1k_words(
                            stage.output_tokens,
                            result.input_word_count,
                        ),
                        "output_bytes": per_1k_words(
                            stage.output_volume.total_bytes,
                            result.input_word_count,
                        ),
                        "duration_share": round(stage.duration_ms / total_elapsed, 4),
                        "output_share": round(stage.output_tokens / total_output_tokens, 4),
                    }
                )

    for recipe_id, rates in recipe_rates.items():
        rows.append(
            BudgetRow(
                scope_type="recipe",
                scope_id=recipe_id,
                scope_label=recipe_labels[recipe_id],
                case_count=len(rates),
                measurement=_build_budget_measurement(rates=rates),
                median_duration_share=round(median(rate["duration_share"] for rate in rates), 4),
                median_output_share=round(median(rate["output_share"] for rate in rates), 4),
                note=_build_hotspot_note(
                    median(rate["duration_share"] for rate in rates),
                    median(rate["output_share"] for rate in rates),
                ),
            )
        )

    for (recipe_id, stage_id), rates in stage_rates.items():
        rows.append(
            BudgetRow(
                scope_type="stage",
                scope_id=f"{recipe_id}.{stage_id}",
                scope_label=f"{recipe_id}:{stage_id}",
                case_count=len(rates),
                measurement=_build_budget_measurement(rates=rates),
                median_duration_share=round(median(rate["duration_share"] for rate in rates), 4),
                median_output_share=round(median(rate["output_share"] for rate in rates), 4),
                note=_build_hotspot_note(
                    median(rate["duration_share"] for rate in rates),
                    median(rate["output_share"] for rate in rates),
                ),
            )
        )

    boundary_rows = [row for row in rows if row.scope_type == "boundary"]
    recipe_rows = sorted(
        (row for row in rows if row.scope_type == "recipe"),
        key=lambda row: row.measurement.current_duration_ms_per_1k_words or 0.0,
        reverse=True,
    )
    stage_rows = sorted(
        (row for row in rows if row.scope_type == "stage"),
        key=lambda row: row.measurement.current_duration_ms_per_1k_words or 0.0,
        reverse=True,
    )
    return boundary_rows + recipe_rows + stage_rows


def summarize_results(
    results: list[CaseBoundaryResult],
    budget_rows: list[BudgetRow],
) -> dict[str, object]:
    successful = [result for result in results if result.success] or list(results)
    if not successful:
        return {
            "overall": 0.0,
            "successful_cases": 0,
            "total_cases": len(results),
            "successful_case_ratio": 0.0,
            "median_total_elapsed_ms": None,
            "median_total_cost_usd": None,
            "fastest_case_id": None,
            "fastest_total_ms": None,
            "slowest_case_id": None,
            "slowest_total_ms": None,
            "boundary_current_budget_duration_ms_per_1k_words": None,
            "boundary_climb_target_duration_ms_per_1k_words": None,
            "top_runtime_hotspot_id": None,
            "top_output_hotspot_id": None,
            "follow_up_candidates": [],
        }

    boundary_row = next((row for row in budget_rows if row.scope_type == "boundary"), None)
    stage_rows = [row for row in budget_rows if row.scope_type == "stage"]
    runtime_hotspot = max(
        stage_rows,
        key=lambda row: row.measurement.current_duration_ms_per_1k_words or 0.0,
        default=None,
    )
    output_hotspot = max(
        stage_rows,
        key=lambda row: row.measurement.current_output_tokens_per_1k_words or 0.0,
        default=None,
    )
    fastest = min(successful, key=lambda result: result.total_elapsed_ms)
    slowest = max(successful, key=lambda result: result.total_elapsed_ms)
    follow_up_candidates = build_follow_up_candidates(stage_rows)
    return {
        "overall": round(len(successful) / len(results), 4),
        "successful_cases": len(successful),
        "total_cases": len(results),
        "successful_case_ratio": round(len(successful) / len(results), 4),
        "median_total_elapsed_ms": round(median(result.total_elapsed_ms for result in successful)),
        "median_total_cost_usd": round(median(result.total_cost_usd for result in successful), 6),
        "fastest_case_id": fastest.case_id,
        "fastest_total_ms": fastest.total_elapsed_ms,
        "slowest_case_id": slowest.case_id,
        "slowest_total_ms": slowest.total_elapsed_ms,
        "boundary_current_budget_duration_ms_per_1k_words": (
            boundary_row.measurement.current_duration_ms_per_1k_words if boundary_row else None
        ),
        "boundary_climb_target_duration_ms_per_1k_words": (
            boundary_row.measurement.climb_target_duration_ms_per_1k_words
            if boundary_row
            else None
        ),
        "top_runtime_hotspot_id": runtime_hotspot.scope_id if runtime_hotspot else None,
        "top_runtime_hotspot_current_duration_ms_per_1k_words": (
            runtime_hotspot.measurement.current_duration_ms_per_1k_words
            if runtime_hotspot
            else None
        ),
        "top_output_hotspot_id": output_hotspot.scope_id if output_hotspot else None,
        "top_output_hotspot_current_output_tokens_per_1k_words": (
            output_hotspot.measurement.current_output_tokens_per_1k_words
            if output_hotspot
            else None
        ),
        "follow_up_candidates": follow_up_candidates,
    }


def build_follow_up_candidates(stage_rows: list[BudgetRow]) -> list[dict[str, object]]:
    duration_sorted = sorted(
        stage_rows,
        key=lambda row: row.measurement.current_duration_ms_per_1k_words or 0.0,
        reverse=True,
    )
    output_sorted = sorted(
        stage_rows,
        key=lambda row: row.measurement.current_output_tokens_per_1k_words or 0.0,
        reverse=True,
    )
    selected: list[BudgetRow] = []
    seen: set[str] = set()
    for row in duration_sorted[:2] + output_sorted[:2]:
        if row.scope_id in seen:
            continue
        seen.add(row.scope_id)
        selected.append(row)

    candidates: list[dict[str, object]] = []
    for row in selected:
        candidates.append(
            {
                "scope_id": row.scope_id,
                "scope_label": row.scope_label,
                "runtime_ms_per_1k_words": row.measurement.current_duration_ms_per_1k_words,
                "output_tokens_per_1k_words": row.measurement.current_output_tokens_per_1k_words,
                "median_duration_share": row.median_duration_share,
                "median_output_share": row.median_output_share,
                "note": row.note
                or "Measured hotspot: promote into a stage-specific throughput follow-up.",
            }
        )
    return candidates


def render_throughput_markdown(payload: dict[str, object]) -> str:
    summary = payload["summary"]
    boundary = payload["boundary"]
    cases = payload["cases"]
    budgets = payload["budgets"]
    follow_ups = summary["follow_up_candidates"]

    lines = [
        "# Full Script Throughput Eval",
        "",
        f"- Measured at: {payload['measured_at']}",
        f"- Fixture manifest: `{payload['fixture_manifest']}`",
        f"- Honest boundary: `{boundary['boundary_label']}`",
        f"- Scope truth: {boundary['honest_scope']}",
        f"- Recipe chain: `{', '.join(recipe['recipe_id'] for recipe in boundary['recipes'])}`",
        f"- Successful cases: {summary['successful_cases']} / {summary['total_cases']}",
        f"- Median total runtime: {summary['median_total_elapsed_ms']} ms",
        f"- Median total cost: ${summary['median_total_cost_usd']:.4f}",
        (
            "- Boundary current budget: "
            f"{summary['boundary_current_budget_duration_ms_per_1k_words']} ms / 1k input words"
        ),
        (
            "- Boundary climb target: "
            f"{summary['boundary_climb_target_duration_ms_per_1k_words']} ms / 1k input words"
        ),
        (
            "- Top runtime hotspot: "
            f"`{summary['top_runtime_hotspot_id']}` "
            f"({summary['top_runtime_hotspot_current_duration_ms_per_1k_words']} ms / 1k words)"
        ),
        (
            "- Top output hotspot: "
            f"`{summary['top_output_hotspot_id']}` "
            "("
            f"{summary['top_output_hotspot_current_output_tokens_per_1k_words']} "
            "tokens / 1k words)"
        ),
        "",
        "## Budget Basis",
        "",
        "- `current_observed`: median normalized rate across successful cases.",
        "- `climb_target`: best observed normalized rate across successful cases.",
        "- These are climb aids for detector-backed optimization, not stop-ship thresholds.",
        "",
        "## Cases",
        "",
        (
            "| Case | Words | Total ms | Cost USD | Input tok | Output tok | "
            "Output bytes | Success | Notes |"
        ),
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for case in cases:
        lines.append(
            "| "
            f"{case['case_id']} | "
            f"{case['input_word_count']} | "
            f"{case['total_elapsed_ms']} | "
            f"{case['total_cost_usd']:.6f} | "
            f"{case['total_input_tokens']} | "
            f"{case['total_output_tokens']} | "
            f"{case['output_volume']['total_bytes']} | "
            f"{'yes' if case['success'] else 'no'} | "
            f"{case.get('notes') or ''} |"
        )

    lines.extend(
        [
            "",
            "## Stage Efficiency Budgets",
            "",
            (
                "| Scope | Current ms / 1k | Climb ms / 1k | Current out tok / 1k | "
                "Climb out tok / 1k | Current out bytes / 1k | Median dur share | "
                "Median out share | Note |"
            ),
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in budgets:
        lines.append(
            "| "
            f"{row['scope_id']} | "
            f"{_fmt_metric(row['measurement']['current_duration_ms_per_1k_words'])} | "
            f"{_fmt_metric(row['measurement']['climb_target_duration_ms_per_1k_words'])} | "
            f"{_fmt_metric(row['measurement']['current_output_tokens_per_1k_words'])} | "
            f"{_fmt_metric(row['measurement']['climb_target_output_tokens_per_1k_words'])} | "
            f"{_fmt_metric(row['measurement']['current_output_bytes_per_1k_words'])} | "
            f"{_fmt_share(row.get('median_duration_share'))} | "
            f"{_fmt_share(row.get('median_output_share'))} | "
            f"{row.get('note') or ''} |"
        )

    if follow_ups:
        lines.extend(["", "## Follow-Up Candidates", ""])
        for candidate in follow_ups:
            lines.append(
                "- "
                f"`{candidate['scope_id']}` — {candidate['note']} "
                f"(runtime {candidate['runtime_ms_per_1k_words']} ms / 1k, "
                f"output {candidate['output_tokens_per_1k_words']} tok / 1k)."
            )

    lines.extend(["", "## Per-Case Recipe Detail", ""])
    for case in cases:
        lines.extend(
            [
                f"### {case['case_id']}",
                "",
                (
                    f"- Runtime: {case['total_elapsed_ms']} ms total, "
                    f"${case['total_cost_usd']:.6f}, "
                    f"{case['total_output_tokens']} output tokens, "
                    f"{case['output_volume']['total_bytes']} output bytes."
                ),
                "",
                (
                    "| Recipe | Elapsed ms | Cost USD | Input tok | Output tok | "
                    "Output bytes | Success |"
                ),
                "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
            ]
        )
        for recipe in case["recipe_runs"]:
            lines.append(
                "| "
                f"{recipe['recipe_id']} | "
                f"{recipe['elapsed_ms']} | "
                f"{recipe['total_cost_usd']:.6f} | "
                f"{recipe['total_input_tokens']} | "
                f"{recipe['total_output_tokens']} | "
                f"{recipe['output_volume']['total_bytes']} | "
                f"{'yes' if recipe['success'] else 'no'} |"
            )
        lines.extend(
            [
                "",
                (
                    "| Stage | Status | Duration ms | Cost USD | Input tok | Output tok | "
                    "Artifacts | Output bytes | Output lines | Model |"
                ),
                "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
            ]
        )
        for recipe in case["recipe_runs"]:
            for stage in recipe["stage_summaries"]:
                lines.append(
                    "| "
                    f"{recipe['recipe_id']}.{stage['stage_id']} | "
                    f"{stage['status']} | "
                    f"{stage['duration_ms']} | "
                    f"{stage['cost_usd']:.6f} | "
                    f"{stage['input_tokens']} | "
                    f"{stage['output_tokens']} | "
                    f"{stage['output_volume']['artifact_count']} | "
                    f"{stage['output_volume']['total_bytes']} | "
                    f"{stage['output_volume']['text_lines']} | "
                    f"{stage.get('model_used') or 'code'} |"
                )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def per_1k_words(value: float | int, word_count: int) -> float:
    if word_count <= 0:
        return 0.0
    return round((float(value) * 1000.0) / word_count, 3)


def _build_budget_measurement(rates: list[dict[str, float]]) -> BudgetMeasurement:
    return BudgetMeasurement(
        current_duration_ms_per_1k_words=round(median(rate["duration"] for rate in rates), 3),
        climb_target_duration_ms_per_1k_words=round(min(rate["duration"] for rate in rates), 3),
        current_cost_usd_per_1k_words=round(median(rate["cost"] for rate in rates), 6),
        climb_target_cost_usd_per_1k_words=round(min(rate["cost"] for rate in rates), 6),
        current_output_tokens_per_1k_words=round(
            median(rate["output_tokens"] for rate in rates),
            3,
        ),
        climb_target_output_tokens_per_1k_words=round(
            min(rate["output_tokens"] for rate in rates),
            3,
        ),
        current_output_bytes_per_1k_words=round(
            median(rate["output_bytes"] for rate in rates),
            3,
        ),
        climb_target_output_bytes_per_1k_words=round(
            min(rate["output_bytes"] for rate in rates),
            3,
        ),
    )


def _build_hotspot_note(duration_share: float, output_share: float) -> str | None:
    if duration_share >= 0.35 and output_share >= 0.35:
        return "Dominant runtime and output-volume hotspot in the current boundary."
    if duration_share >= 0.35:
        return "Dominant runtime hotspot in the current boundary."
    if output_share >= 0.35:
        return "Dominant output-volume hotspot in the current boundary."
    return None


def _fmt_metric(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.3f}"


def _fmt_share(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value * 100:.1f}%"
