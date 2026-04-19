from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from statistics import median
from typing import Literal

from pydantic import BaseModel, Field


class AiPrevizStageOverride(BaseModel):
    engine_pack_id: str = Field(min_length=1)
    duration_seconds: int = Field(ge=1)
    resolution: str = Field(min_length=1)
    consistency_strategy: str = Field(default="prompt_only", min_length=1)
    prompt_profile: str = Field(default="standard", min_length=1)


class RuntimeEvalCase(BaseModel):
    case_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    input_fixture: str = Field(min_length=1)
    scene_id: str = Field(default="scene_001", min_length=1)
    prerequisite_mode: Literal["mvp_ingest_only", "scene_ready"] = "scene_ready"
    prerequisite_strategy: str | None = None
    recipe_mode: Literal["shipped", "patched"] = "shipped"
    ai_previz: AiPrevizStageOverride | None = None
    notes: str | None = None


class RuntimeEvalManifest(BaseModel):
    cases: list[RuntimeEvalCase] = Field(min_length=1)


class RecipeRunSummary(BaseModel):
    run_id: str
    recipe_id: str
    elapsed_ms: int = Field(ge=0)
    success: bool
    error: str | None = None
    total_cost_usd: float = Field(ge=0.0)
    stage_statuses: dict[str, str] = Field(default_factory=dict)
    stage_durations_ms: dict[str, int] = Field(default_factory=dict)
    artifact_counts: dict[str, int] = Field(default_factory=dict)
    artifact_paths: dict[str, str] = Field(default_factory=dict)


class RuntimeCaseResult(BaseModel):
    case_id: str
    label: str
    prerequisite_mode: str
    prerequisite_strategy: str | None = None
    recipe_mode: str
    engine_pack_id: str
    prompt_profile: str = Field(default="standard", min_length=1)
    duration_seconds: int
    resolution: str
    scene_id: str
    input_fixture: str
    attempt_index: int = Field(ge=1, default=1)
    notes: str | None = None
    project_dir: str
    success: bool
    error: str | None = None
    prerequisite_elapsed_ms: int = Field(ge=0)
    ai_previz_elapsed_ms: int = Field(ge=0)
    time_to_first_playable_ms: int = Field(ge=0)
    post_playable_overhead_ms: int = Field(ge=0)
    total_elapsed_ms: int = Field(ge=0)
    prerequisite_runs: list[RecipeRunSummary] = Field(default_factory=list)
    ai_previz_run: RecipeRunSummary | None = None
    ai_previz_artifact_path: str | None = None
    media_validation_path: str | None = None


class RuntimeCaseAggregate(BaseModel):
    case_id: str
    label: str
    prerequisite_mode: str
    prerequisite_strategy: str | None = None
    recipe_mode: str
    engine_pack_id: str
    prompt_profile: str = Field(default="standard", min_length=1)
    duration_seconds: int
    resolution: str
    scene_id: str
    input_fixture: str
    notes: str | None = None
    repeat_count: int = Field(ge=1)
    successful_attempts: int = Field(ge=0)
    success: bool
    prerequisite_elapsed_ms: int = Field(ge=0)
    ai_previz_elapsed_ms: int = Field(ge=0)
    time_to_first_playable_ms: int = Field(ge=0)
    post_playable_overhead_ms: int = Field(ge=0)
    total_elapsed_ms: int = Field(ge=0)
    min_time_to_first_playable_ms: int = Field(ge=0)
    max_time_to_first_playable_ms: int = Field(ge=0)
    min_total_elapsed_ms: int = Field(ge=0)
    max_total_elapsed_ms: int = Field(ge=0)
    min_ai_previz_elapsed_ms: int = Field(ge=0)
    max_ai_previz_elapsed_ms: int = Field(ge=0)


def display_repo_relative_path(path: Path, repo_root: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(repo_root))
    except ValueError:
        return str(resolved)


def aggregate_attempts(attempts: list[RuntimeCaseResult]) -> list[RuntimeCaseAggregate]:
    grouped: dict[str, list[RuntimeCaseResult]] = defaultdict(list)
    for attempt in attempts:
        grouped[attempt.case_id].append(attempt)

    aggregates: list[RuntimeCaseAggregate] = []
    for case_id, case_attempts in grouped.items():
        ordered_attempts = sorted(case_attempts, key=lambda attempt: attempt.attempt_index)
        template = ordered_attempts[0]
        successful_attempts = [attempt for attempt in ordered_attempts if attempt.success]
        prerequisite_values = [attempt.prerequisite_elapsed_ms for attempt in successful_attempts]
        ai_values = [attempt.ai_previz_elapsed_ms for attempt in successful_attempts]
        first_playable_values = [
            attempt.time_to_first_playable_ms for attempt in successful_attempts
        ]
        overhead_values = [attempt.post_playable_overhead_ms for attempt in successful_attempts]
        total_values = [attempt.total_elapsed_ms for attempt in successful_attempts]
        if not total_values:
            prerequisite_values = [attempt.prerequisite_elapsed_ms for attempt in ordered_attempts]
            ai_values = [attempt.ai_previz_elapsed_ms for attempt in ordered_attempts]
            first_playable_values = [
                attempt.time_to_first_playable_ms for attempt in ordered_attempts
            ]
            overhead_values = [attempt.post_playable_overhead_ms for attempt in ordered_attempts]
            total_values = [attempt.total_elapsed_ms for attempt in ordered_attempts]
        aggregates.append(
            RuntimeCaseAggregate(
                case_id=case_id,
                label=template.label,
                prerequisite_mode=template.prerequisite_mode,
                prerequisite_strategy=template.prerequisite_strategy,
                recipe_mode=template.recipe_mode,
                engine_pack_id=template.engine_pack_id,
                prompt_profile=template.prompt_profile,
                duration_seconds=template.duration_seconds,
                resolution=template.resolution,
                scene_id=template.scene_id,
                input_fixture=template.input_fixture,
                notes=template.notes,
                repeat_count=len(ordered_attempts),
                successful_attempts=len(successful_attempts),
                success=len(successful_attempts) == len(ordered_attempts),
                prerequisite_elapsed_ms=round(median(prerequisite_values)),
                ai_previz_elapsed_ms=round(median(ai_values)),
                time_to_first_playable_ms=round(median(first_playable_values)),
                post_playable_overhead_ms=round(median(overhead_values)),
                total_elapsed_ms=round(median(total_values)),
                min_time_to_first_playable_ms=min(first_playable_values),
                max_time_to_first_playable_ms=max(first_playable_values),
                min_total_elapsed_ms=min(total_values),
                max_total_elapsed_ms=max(total_values),
                min_ai_previz_elapsed_ms=min(ai_values),
                max_ai_previz_elapsed_ms=max(ai_values),
            )
        )
    return sorted(aggregates, key=lambda aggregate: aggregate.case_id)


def summarize_results(
    results: list[RuntimeCaseAggregate],
    *,
    fast_previz_target_ms: int,
) -> dict[str, object]:
    successful = [result for result in results if result.success]
    if not successful:
        successful = [result for result in results if result.successful_attempts > 0]
    focus_mode = _focus_prerequisite_mode(successful)
    focus_results = [
        result for result in successful if result.prerequisite_mode == focus_mode
    ] if focus_mode is not None else successful
    fastest_focus = min(
        focus_results,
        key=lambda result: result.time_to_first_playable_ms,
        default=None,
    )
    fastest_focus_ai_previz = min(
        focus_results,
        key=lambda result: result.ai_previz_elapsed_ms,
        default=None,
    )
    scene_ready = [
        result
        for result in successful
        if result.prerequisite_mode == "scene_ready"
    ]
    fastest_scene_ready = min(
        scene_ready,
        key=lambda result: result.time_to_first_playable_ms,
        default=None,
    )
    fastest_total = min(
        successful,
        key=lambda result: result.total_elapsed_ms,
        default=None,
    )
    fastest_scene_ready_ai_previz = min(
        scene_ready,
        key=lambda result: result.ai_previz_elapsed_ms,
        default=None,
    )
    overall = 0.0
    if fastest_focus is not None:
        overall = (
            1.0
            if fastest_focus.time_to_first_playable_ms <= fast_previz_target_ms
            else 0.5
        )

    return {
        "overall": overall,
        "successful_cases": len(successful),
        "total_cases": len(results),
        "successful_case_ratio": round(len(successful) / len(results), 4),
        "fully_successful_cases": len([result for result in results if result.success]),
        "focus_prerequisite_mode": focus_mode,
        "fastest_focus_case_id": fastest_focus.case_id if fastest_focus else None,
        "fastest_focus_ms": (
            fastest_focus.time_to_first_playable_ms if fastest_focus else None
        ),
        "fastest_focus_prerequisite_ms": (
            fastest_focus.prerequisite_elapsed_ms if fastest_focus else None
        ),
        "fastest_focus_ai_previz_ms": (
            fastest_focus.ai_previz_elapsed_ms if fastest_focus else None
        ),
        "fastest_focus_full_completion_ms": (
            fastest_focus.total_elapsed_ms if fastest_focus else None
        ),
        "fastest_focus_post_playable_overhead_ms": (
            fastest_focus.post_playable_overhead_ms if fastest_focus else None
        ),
        "fastest_focus_ai_previz_case_id": (
            fastest_focus_ai_previz.case_id if fastest_focus_ai_previz else None
        ),
        "fastest_focus_isolated_ai_previz_ms": (
            fastest_focus_ai_previz.ai_previz_elapsed_ms if fastest_focus_ai_previz else None
        ),
        "fastest_scene_ready_case_id": fastest_scene_ready.case_id if fastest_scene_ready else None,
        "fastest_scene_ready_ms": (
            fastest_scene_ready.time_to_first_playable_ms if fastest_scene_ready else None
        ),
        "fastest_scene_ready_prerequisite_ms": (
            fastest_scene_ready.prerequisite_elapsed_ms if fastest_scene_ready else None
        ),
        "fastest_scene_ready_ai_previz_ms": (
            fastest_scene_ready.ai_previz_elapsed_ms if fastest_scene_ready else None
        ),
        "fastest_scene_ready_full_completion_ms": (
            fastest_scene_ready.total_elapsed_ms if fastest_scene_ready else None
        ),
        "fastest_scene_ready_post_playable_overhead_ms": (
            fastest_scene_ready.post_playable_overhead_ms if fastest_scene_ready else None
        ),
        "fastest_scene_ready_ai_previz_case_id": (
            fastest_scene_ready_ai_previz.case_id if fastest_scene_ready_ai_previz else None
        ),
        "fastest_isolated_ai_previz_ms": (
            fastest_scene_ready_ai_previz.ai_previz_elapsed_ms
            if fastest_scene_ready_ai_previz
            else None
        ),
        "fastest_total_case_id": fastest_total.case_id if fastest_total else None,
        "fastest_total_ms": fastest_total.total_elapsed_ms if fastest_total else None,
        "target_fast_previz_ms": fast_previz_target_ms,
    }


def _focus_prerequisite_mode(results: list[RuntimeCaseAggregate]) -> str | None:
    modes = {result.prerequisite_mode for result in results}
    if not modes:
        return None
    if len(modes) == 1:
        return next(iter(modes))
    if "scene_ready" in modes:
        return "scene_ready"
    return sorted(modes)[0]


def render_runtime_markdown(payload: dict[str, object]) -> str:
    summary = payload["summary"]
    cases = payload["cases"]
    focus_mode = summary.get("focus_prerequisite_mode") or "selected"
    focus_label = str(focus_mode).replace("_", " ")
    lines = [
        "# Real AI Previz Runtime Eval",
        "",
        f"- Measured at: {payload['measured_at']}",
        f"- Fixture manifest: `{payload['fixture_manifest']}`",
        f"- Comparison method: `{payload['comparison_method']}`",
        f"- Repeat count: {payload['repeat_count']}",
        f"- Successful cases: {summary['successful_cases']} / {summary['total_cases']}",
        f"- Fully successful cases: {summary['fully_successful_cases']} / {summary['total_cases']}",
        f"- Focus prerequisite mode: `{focus_mode}`",
        f"- Fastest {focus_label} case: `{summary['fastest_focus_case_id']}`",
        f"- Fastest {focus_label} time to first playable: {summary['fastest_focus_ms']} ms",
        f"- Fastest {focus_label} prerequisites: {summary['fastest_focus_prerequisite_ms']} ms",
        f"- Fastest {focus_label} AI-previz recipe: {summary['fastest_focus_ai_previz_ms']} ms",
        (
            f"- Fastest {focus_label} full completion: "
            f"{summary['fastest_focus_full_completion_ms']} ms"
        ),
        (
            f"- Fastest {focus_label} post-playable overhead: "
            f"{summary['fastest_focus_post_playable_overhead_ms']} ms"
        ),
        (
            f"- Fastest isolated {focus_label} AI-previz case: "
            f"`{summary['fastest_focus_ai_previz_case_id']}`"
        ),
        (
            f"- Fastest isolated {focus_label} AI-previz median: "
            f"{summary['fastest_focus_isolated_ai_previz_ms']} ms"
        ),
        f"- Fastest total case: `{summary['fastest_total_case_id']}`",
        f"- Fastest total elapsed: {summary['fastest_total_ms']} ms",
        (
            f"- Fast target: <= {summary['target_fast_previz_ms']} ms "
            f"to first real {focus_label} `ai_previz_video`"
        ),
        "",
        "## Cases",
        "",
        (
            "| Case | Attempts | Mode | Strategy | Engine Pack | Prompt | Prereqs | "
            "AI Previz ms | First playable ms | Full completion ms | "
            "Post-playable overhead | Success | Notes |"
        ),
        "| --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for case in cases:
        lines.append(
            "| "
            f"{case['case_id']} | "
            f"{case['successful_attempts']}/{case['repeat_count']} | "
            f"{case['recipe_mode']} | "
            f"{case.get('prerequisite_strategy') or case['prerequisite_mode']} | "
            f"{case['engine_pack_id']} / {case['duration_seconds']}s {case['resolution']} | "
            f"{case['prompt_profile']} | "
            f"{case['prerequisite_mode']} ({case['prerequisite_elapsed_ms']} ms) | "
            f"{case['ai_previz_elapsed_ms']} | "
            f"{case['time_to_first_playable_ms']} | "
            f"{case['total_elapsed_ms']} | "
            f"{case['post_playable_overhead_ms']} | "
            f"{'yes' if case['success'] else 'no'} | "
            f"{case.get('notes') or ''} |"
        )
    return "\n".join(lines) + "\n"
