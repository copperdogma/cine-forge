#!/usr/bin/env python3
"""Aggregate shared-substrate AI previz runtime runs into one decision summary."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from statistics import median

from pydantic import BaseModel, Field

REPO_ROOT = Path(__file__).resolve().parents[2]


class DecisionCase(BaseModel):
    case_id: str
    label: str
    engine_pack_id: str
    duration_seconds: int = Field(ge=1)
    resolution: str
    usefulness_overall: float | None = None
    usefulness_note: str | None = None
    all_ai_previz_elapsed_ms: list[int] = Field(default_factory=list)
    all_total_elapsed_ms: list[int] = Field(default_factory=list)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--summary-file",
        type=Path,
        required=True,
        help="Existing shared-scene-ready summary JSON with usefulness annotations.",
    )
    parser.add_argument(
        "--result-file",
        action="append",
        type=Path,
        default=[],
        help="Additional raw runtime result JSON files to append into the summary.",
    )
    parser.add_argument(
        "--output-prefix",
        type=Path,
        required=True,
        help="Write <prefix>.json and <prefix>.md.",
    )
    args = parser.parse_args()

    base_path = args.summary_file.resolve()
    payload = json.loads(base_path.read_text(encoding="utf-8"))
    _require_decision_grade_summary(payload, base_path)
    cases = {
        case["case_id"]: DecisionCase.model_validate(case)
        for case in payload["cases"]
    }
    _validate_balanced_samples(cases, source_path=base_path)

    recommended_case_id = payload["summary"].get("recommended_shipped_case_id")
    if not isinstance(recommended_case_id, str) or recommended_case_id not in cases:
        raise ValueError(
            f"Base runtime summary has an unknown recommended_shipped_case_id: {base_path}"
        )

    for result_file in args.result_file:
        _append_result_file(cases=cases, result_path=result_file.resolve())

    _validate_balanced_samples(cases, source_path=base_path)

    ordered_cases = sorted(cases.values(), key=lambda case: _median(case.all_total_elapsed_ms))
    runtime_winner = ordered_cases[0]
    isolated_winner = min(ordered_cases, key=lambda case: _median(case.all_ai_previz_elapsed_ms))
    usefulness_cases = [case for case in ordered_cases if case.usefulness_overall is not None]
    usefulness_leader = max(
        usefulness_cases,
        key=lambda case: float(case.usefulness_overall),
        default=None,
    )
    current_shipped = cases[recommended_case_id]

    summary = {
        "decision_grade": True,
        "current_shipped_case_id": current_shipped.case_id if current_shipped else None,
        "runtime_winner_case_id": runtime_winner.case_id,
        "runtime_winner_total_ms": _median(runtime_winner.all_total_elapsed_ms),
        "isolated_runtime_winner_case_id": isolated_winner.case_id,
        "isolated_runtime_winner_ai_previz_ms": _median(isolated_winner.all_ai_previz_elapsed_ms),
        "usefulness_leader_case_id": usefulness_leader.case_id if usefulness_leader else None,
        "usefulness_leader_overall": (
            usefulness_leader.usefulness_overall if usefulness_leader else None
        ),
        "leaders_diverge": (
            usefulness_leader is not None and usefulness_leader.case_id != runtime_winner.case_id
        ),
        "note": _decision_note(
            current_shipped=current_shipped,
            runtime_winner=runtime_winner,
            usefulness_leader=usefulness_leader,
        ),
    }

    output_payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "base_summary_file": _display_path(base_path),
        "source_result_files": [_display_path(result_file) for result_file in args.result_file],
        "summary": summary,
        "cases": [_case_payload(case, runtime_winner=runtime_winner) for case in ordered_cases],
    }

    output_prefix = args.output_prefix.resolve()
    json_path = output_prefix.with_suffix(".json")
    md_path = output_prefix.with_suffix(".md")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(output_payload, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(_render_markdown(output_payload), encoding="utf-8")
    print(json_path)
    print(md_path)


def _append_result_file(*, cases: dict[str, DecisionCase], result_path: Path) -> None:
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    _require_decision_grade_summary(payload, result_path)
    result_cases = payload["cases"]
    observed_ids = [case["case_id"] for case in result_cases]
    expected_ids = set(cases)
    observed_set = set(observed_ids)
    if len(observed_ids) != len(observed_set):
        raise ValueError(f"Result file contains duplicate case IDs: {result_path}")
    if observed_set != expected_ids:
        missing = sorted(expected_ids - observed_set)
        extra = sorted(observed_set - expected_ids)
        raise ValueError(
            f"Result file does not contain the exact case matrix: {result_path}; "
            f"missing={missing}, extra={extra}"
        )

    additions: list[tuple[DecisionCase, int, int]] = []
    for case in result_cases:
        ai_elapsed = _runtime_ms(case.get("ai_previz_elapsed_ms"), result_path=result_path)
        total_elapsed = _runtime_ms(case.get("total_elapsed_ms"), result_path=result_path)
        additions.append((cases[case["case_id"]], ai_elapsed, total_elapsed))

    for entry, ai_elapsed, total_elapsed in additions:
        entry.all_ai_previz_elapsed_ms.append(ai_elapsed)
        entry.all_total_elapsed_ms.append(total_elapsed)

    _validate_balanced_samples(cases, source_path=result_path)


def _require_decision_grade_summary(payload: dict, source_path: Path) -> None:
    summary = payload.get("summary")
    if not isinstance(summary, dict) or summary.get("decision_grade") is not True:
        raise ValueError(
            f"Base runtime summary is not decision-grade: {source_path}. "
            "Every selected repeat must succeed before runtime can drive a decision."
        )
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError(f"Base runtime summary has no cases: {source_path}")
    case_ids: list[str] = []
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError(f"Runtime summary has a non-object case: {source_path}")
        case_id = case.get("case_id")
        if not isinstance(case_id, str) or not case_id.strip():
            raise ValueError(f"Runtime summary has an invalid case_id: {source_path}")
        case_ids.append(case_id)
    if len(case_ids) != len(set(case_ids)):
        raise ValueError(f"Runtime summary contains duplicate case IDs: {source_path}")


def _runtime_ms(value: object, *, result_path: Path) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(
            f"Runtime result has an invalid nonnegative integer latency in {result_path}: {value!r}"
        )
    return value


def _validate_balanced_samples(
    cases: dict[str, DecisionCase], *, source_path: Path
) -> None:
    if not cases:
        raise ValueError(f"Runtime decision has no cases: {source_path}")

    sample_counts: set[int] = set()
    for case in cases.values():
        ai_values = case.all_ai_previz_elapsed_ms
        total_values = case.all_total_elapsed_ms
        if not ai_values or not total_values:
            raise ValueError(
                f"Runtime decision case {case.case_id!r} has no retained samples: {source_path}"
            )
        if len(ai_values) != len(total_values):
            raise ValueError(
                f"Runtime decision case {case.case_id!r} has unbalanced AI/total samples: "
                f"{source_path}"
            )
        for value in [*ai_values, *total_values]:
            _runtime_ms(value, result_path=source_path)
        sample_counts.add(len(total_values))

    if len(sample_counts) != 1:
        raise ValueError(
            f"Runtime decision cases have unequal sample counts {sorted(sample_counts)}: "
            f"{source_path}"
        )


def _case_payload(case: DecisionCase, *, runtime_winner: DecisionCase) -> dict[str, object]:
    median_total = _median(case.all_total_elapsed_ms)
    median_ai_previz = _median(case.all_ai_previz_elapsed_ms)
    winner_total = _median(runtime_winner.all_total_elapsed_ms)
    winner_ai_previz = _median(runtime_winner.all_ai_previz_elapsed_ms)
    return {
        "case_id": case.case_id,
        "label": case.label,
        "engine_pack_id": case.engine_pack_id,
        "duration_seconds": case.duration_seconds,
        "resolution": case.resolution,
        "usefulness_overall": case.usefulness_overall,
        "usefulness_note": case.usefulness_note,
        "sample_count": len(case.all_total_elapsed_ms),
        "median_total_elapsed_ms": median_total,
        "median_ai_previz_elapsed_ms": median_ai_previz,
        "delta_vs_runtime_winner_total_ms": median_total - winner_total,
        "delta_vs_runtime_winner_ai_previz_ms": median_ai_previz - winner_ai_previz,
        "min_total_elapsed_ms": min(case.all_total_elapsed_ms),
        "max_total_elapsed_ms": max(case.all_total_elapsed_ms),
        "min_ai_previz_elapsed_ms": min(case.all_ai_previz_elapsed_ms),
        "max_ai_previz_elapsed_ms": max(case.all_ai_previz_elapsed_ms),
        "all_total_elapsed_ms": case.all_total_elapsed_ms,
        "all_ai_previz_elapsed_ms": case.all_ai_previz_elapsed_ms,
    }


def _decision_note(
    *,
    current_shipped: DecisionCase | None,
    runtime_winner: DecisionCase,
    usefulness_leader: DecisionCase | None,
) -> str:
    if usefulness_leader is None:
        return (
            f"Runtime winner is {runtime_winner.case_id}. No usefulness leader is available, "
            "so the result remains runtime-only."
        )
    if usefulness_leader.case_id == runtime_winner.case_id:
        return (
            f"{runtime_winner.case_id} leads both runtime and usefulness across the "
            "combined shared-substrate evidence."
        )
    shipped_text = (
        f" Current shipped case is {current_shipped.case_id}."
        if current_shipped is not None
        else ""
    )
    return (
        f"Runtime leader ({runtime_winner.case_id}) and usefulness leader "
        f"({usefulness_leader.case_id}) diverge.{shipped_text} No dominant winner is proven "
        "by the combined evidence alone."
    )


def _median(values: list[int]) -> int:
    return round(median(values))


def _display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(REPO_ROOT))
    except ValueError:
        return str(resolved)


def _render_markdown(payload: dict[str, object]) -> str:
    summary = payload["summary"]
    lines = [
        "# Real AI Previz Runtime Decision Summary",
        "",
        f"- Generated at: {payload['generated_at']}",
        f"- Base summary: `{payload['base_summary_file']}`",
        f"- Additional result files: {len(payload['source_result_files'])}",
        f"- Current shipped case: `{summary['current_shipped_case_id']}`",
        (
            f"- Runtime winner: `{summary['runtime_winner_case_id']}` "
            f"({summary['runtime_winner_total_ms']} ms)"
        ),
        (
            "- Isolated AI-previz runtime winner: "
            f"`{summary['isolated_runtime_winner_case_id']}` "
            f"({summary['isolated_runtime_winner_ai_previz_ms']} ms)"
        ),
        (
            "- Usefulness leader: "
            f"`{summary['usefulness_leader_case_id']}` "
            f"({summary['usefulness_leader_overall']})"
        ),
        f"- Leaders diverge: {'yes' if summary['leaders_diverge'] else 'no'}",
        f"- Note: {summary['note']}",
        "",
        "## Cases",
        "",
        (
            "| Case | Samples | Engine Pack | Usefulness | Median AI Previz ms | "
            "Median Total ms | Delta vs Runtime Winner | Notes |"
        ),
        "| --- | ---: | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for case in payload["cases"]:
        lines.append(
            "| "
            f"{case['case_id']} | "
            f"{case['sample_count']} | "
            f"{case['engine_pack_id']} / {case['duration_seconds']}s {case['resolution']} | "
            f"{case['usefulness_overall'] if case['usefulness_overall'] is not None else 'n/a'} | "
            f"{case['median_ai_previz_elapsed_ms']} | "
            f"{case['median_total_elapsed_ms']} | "
            f"+{case['delta_vs_runtime_winner_total_ms']} ms total / "
            f"+{case['delta_vs_runtime_winner_ai_previz_ms']} ms ai | "
            f"{case.get('usefulness_note') or ''} |"
        )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
