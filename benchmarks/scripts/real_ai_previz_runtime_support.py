from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from statistics import median

from real_ai_previz_runtime_contract import (
    AiPrevizStageOverride,
    RecipeRunSummary,
    RuntimeCaseAggregate,
    RuntimeCaseResult,
    RuntimeEvalCase,
    RuntimeEvalManifest,
    ShotPlanningStageOverride,
)
from real_ai_previz_runtime_report import render_runtime_markdown

__all__ = [
    "AiPrevizStageOverride",
    "RecipeRunSummary",
    "RuntimeCaseAggregate",
    "RuntimeCaseResult",
    "RuntimeEvalCase",
    "RuntimeEvalManifest",
    "ShotPlanningStageOverride",
    "aggregate_attempts",
    "display_repo_relative_path",
    "render_runtime_markdown",
    "summarize_results",
]


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
                existing_project_state=template.existing_project_state,
                existing_clip_state=template.existing_clip_state,
                requested_start_from=template.requested_start_from,
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
    fully_successful = [result for result in results if result.success]
    partial_success = [
        result
        for result in results
        if not result.success and result.successful_attempts > 0
    ]
    successful = fully_successful or partial_success
    timing_evidence_basis = (
        "fully_successful_cases" if fully_successful else "partial_success_diagnostic"
    )
    decision_grade = bool(results) and len(fully_successful) == len(results)
    focus_mode = _focus_prerequisite_mode(successful)
    focus_results = [
        result for result in successful if result.prerequisite_mode == focus_mode
    ] if focus_mode is not None else successful
    imported_project_focus = [
        result
        for result in focus_results
        if result.existing_project_state and not result.existing_clip_state
    ]
    if imported_project_focus:
        focus_results = imported_project_focus
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
    raw_input_first_pass = [
        result
        for result in successful
        if not result.existing_project_state and not result.existing_clip_state
    ]
    fastest_raw_input_first_pass = min(
        raw_input_first_pass,
        key=lambda result: result.time_to_first_playable_ms,
        default=None,
    )
    imported_project_first_pass = [
        result
        for result in successful
        if result.existing_project_state and not result.existing_clip_state
    ]
    fastest_imported_project_first_pass = min(
        imported_project_first_pass,
        key=lambda result: result.time_to_first_playable_ms,
        default=None,
    )
    regenerate_cases = [result for result in successful if result.existing_clip_state]
    regenerate_reuse = [
        result
        for result in regenerate_cases
        if result.requested_start_from == "ai_previz"
    ]
    regenerate_full = [
        result
        for result in regenerate_cases
        if result.requested_start_from in {None, ""}
    ]
    fastest_regenerate_reuse = min(
        regenerate_reuse,
        key=lambda result: result.time_to_first_playable_ms,
        default=None,
    )
    fastest_regenerate_full = min(
        regenerate_full,
        key=lambda result: result.time_to_first_playable_ms,
        default=None,
    )
    overall = 0.0
    if fastest_focus is not None and decision_grade:
        overall = (
            1.0
            if fastest_focus.time_to_first_playable_ms <= fast_previz_target_ms
            else 0.5
        )

    return {
        "overall": overall,
        "successful_cases": len(fully_successful),
        "total_cases": len(results),
        "successful_case_ratio": round(len(fully_successful) / len(results), 4),
        "fully_successful_cases": len(fully_successful),
        "partial_success_cases": len(partial_success),
        "timing_case_count": len(successful),
        "timing_evidence_basis": timing_evidence_basis,
        "decision_grade": decision_grade,
        "focus_prerequisite_mode": focus_mode,
        "focus_route_kind": _focus_route_kind(fastest_focus),
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
        "fastest_raw_input_first_pass_case_id": (
            fastest_raw_input_first_pass.case_id if fastest_raw_input_first_pass else None
        ),
        "fastest_raw_input_first_pass_ms": (
            fastest_raw_input_first_pass.time_to_first_playable_ms
            if fastest_raw_input_first_pass
            else None
        ),
        "fastest_raw_input_first_pass_prerequisite_ms": (
            fastest_raw_input_first_pass.prerequisite_elapsed_ms
            if fastest_raw_input_first_pass
            else None
        ),
        "fastest_imported_project_first_pass_case_id": (
            fastest_imported_project_first_pass.case_id
            if fastest_imported_project_first_pass
            else None
        ),
        "fastest_imported_project_first_pass_ms": (
            fastest_imported_project_first_pass.time_to_first_playable_ms
            if fastest_imported_project_first_pass
            else None
        ),
        "fastest_imported_project_first_pass_prerequisite_ms": (
            fastest_imported_project_first_pass.prerequisite_elapsed_ms
            if fastest_imported_project_first_pass
            else None
        ),
        "fastest_imported_project_first_pass_ai_previz_ms": (
            fastest_imported_project_first_pass.ai_previz_elapsed_ms
            if fastest_imported_project_first_pass
            else None
        ),
        "fastest_imported_project_first_pass_full_completion_ms": (
            fastest_imported_project_first_pass.total_elapsed_ms
            if fastest_imported_project_first_pass
            else None
        ),
        "fastest_regenerate_reuse_case_id": (
            fastest_regenerate_reuse.case_id if fastest_regenerate_reuse else None
        ),
        "fastest_regenerate_reuse_ms": (
            fastest_regenerate_reuse.time_to_first_playable_ms
            if fastest_regenerate_reuse
            else None
        ),
        "fastest_regenerate_reuse_ai_previz_ms": (
            fastest_regenerate_reuse.ai_previz_elapsed_ms
            if fastest_regenerate_reuse
            else None
        ),
        "fastest_regenerate_reuse_full_completion_ms": (
            fastest_regenerate_reuse.total_elapsed_ms
            if fastest_regenerate_reuse
            else None
        ),
        "fastest_regenerate_reuse_post_playable_overhead_ms": (
            fastest_regenerate_reuse.post_playable_overhead_ms
            if fastest_regenerate_reuse
            else None
        ),
        "fastest_regenerate_full_case_id": (
            fastest_regenerate_full.case_id if fastest_regenerate_full else None
        ),
        "fastest_regenerate_full_ms": (
            fastest_regenerate_full.time_to_first_playable_ms
            if fastest_regenerate_full
            else None
        ),
        "fastest_regenerate_full_ai_previz_ms": (
            fastest_regenerate_full.ai_previz_elapsed_ms
            if fastest_regenerate_full
            else None
        ),
        "fastest_regenerate_full_completion_ms": (
            fastest_regenerate_full.total_elapsed_ms
            if fastest_regenerate_full
            else None
        ),
        "fastest_regenerate_full_post_playable_overhead_ms": (
            fastest_regenerate_full.post_playable_overhead_ms
            if fastest_regenerate_full
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


def _focus_route_kind(result: RuntimeCaseAggregate | None) -> str | None:
    if result is None:
        return None
    if result.existing_clip_state:
        return "existing_clip"
    if result.existing_project_state:
        return "imported_project_first_pass"
    return "raw_input_first_pass"
