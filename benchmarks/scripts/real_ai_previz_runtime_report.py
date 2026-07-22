"""Markdown reporting for the real AI previz runtime benchmark."""

from __future__ import annotations


def render_runtime_markdown(payload: dict[str, object]) -> str:
    summary = payload["summary"]
    cases = payload["cases"]
    focus_mode = summary.get("focus_prerequisite_mode") or "selected"
    lines = [
        "# Real AI Previz Runtime Eval",
        "",
        f"- Measured at: {payload['measured_at']}",
        f"- Fixture manifest: `{payload['fixture_manifest']}`",
        f"- Comparison method: `{payload['comparison_method']}`",
        f"- Repeat count: {payload['repeat_count']}",
        f"- Decision grade: {'yes' if summary.get('decision_grade') else 'no'}",
        f"- Timing evidence basis: `{summary.get('timing_evidence_basis')}`",
        f"- Fully successful cases: {summary['fully_successful_cases']} / {summary['total_cases']}",
        f"- Partial-success cases: {summary.get('partial_success_cases', 0)}",
        f"- Focus prerequisite mode: `{focus_mode}`",
        f"- Fastest focus case: `{summary['fastest_focus_case_id']}`",
        f"- Fastest focus time to first playable: {summary['fastest_focus_ms']} ms",
        f"- Fastest isolated AI-previz median: {summary['fastest_focus_isolated_ai_previz_ms']} ms",
        f"- Fastest total case: `{summary['fastest_total_case_id']}`",
        f"- Fast target: <= {summary['target_fast_previz_ms']} ms",
        "",
        "## Cases",
        "",
        (
            "| Case | Attempts | Substrate | Engine Pack | AI Previz ms | "
            "First playable ms | Total ms | Fully successful | Notes |"
        ),
        "| --- | ---: | --- | --- | ---: | ---: | ---: | --- | --- |",
    ]
    for case in cases:
        substrate = (
            "existing clip"
            if case.get("existing_clip_state")
            else "imported project"
            if case.get("existing_project_state")
            else "raw input"
        )
        lines.append(
            "| "
            f"{case['case_id']} | "
            f"{case['successful_attempts']}/{case['repeat_count']} | "
            f"{substrate} | "
            f"{case['engine_pack_id']} / {case['duration_seconds']}s {case['resolution']} | "
            f"{case['ai_previz_elapsed_ms']} | "
            f"{case['time_to_first_playable_ms']} | "
            f"{case['total_elapsed_ms']} | "
            f"{'yes' if case['success'] else 'no'} | "
            f"{case.get('notes') or ''} |"
        )
    return "\n".join(lines) + "\n"
