#!/usr/bin/env python3
"""Aggregate shared-substrate AI previz runtime runs into one decision summary."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from statistics import median

from pydantic import BaseModel, Field


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
    cases = {
        case["case_id"]: DecisionCase.model_validate(case)
        for case in payload["cases"]
    }

    for result_file in args.result_file:
        _append_result_file(cases=cases, result_path=result_file.resolve())

    ordered_cases = sorted(cases.values(), key=lambda case: _median(case.all_total_elapsed_ms))
    runtime_winner = ordered_cases[0]
    isolated_winner = min(ordered_cases, key=lambda case: _median(case.all_ai_previz_elapsed_ms))
    usefulness_cases = [case for case in ordered_cases if case.usefulness_overall is not None]
    usefulness_leader = max(
        usefulness_cases,
        key=lambda case: float(case.usefulness_overall),
        default=None,
    )
    current_shipped = cases.get(payload["summary"]["recommended_shipped_case_id"])

    summary = {
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
        "base_summary_file": str(base_path),
        "source_result_files": [str(result_file.resolve()) for result_file in args.result_file],
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
    for case in payload["cases"]:
        entry = cases.get(case["case_id"])
        if entry is None:
            raise KeyError(f"Unknown case_id in result file {result_path}: {case['case_id']}")
        entry.all_ai_previz_elapsed_ms.append(int(case["ai_previz_elapsed_ms"]))
        entry.all_total_elapsed_ms.append(int(case["total_elapsed_ms"]))


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
