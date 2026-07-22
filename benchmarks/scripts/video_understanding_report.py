#!/usr/bin/env python3
"""Summarize Story 030 video-understanding promptfoo results into a report."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCORERS_ROOT = REPO_ROOT / "benchmarks" / "scorers"
if str(SCORERS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCORERS_ROOT))

_scorer = importlib.import_module("video_understanding_scorer")
score_output_against_target = _scorer.score_output_against_target
_support = importlib.import_module("video_understanding_report_support")
_case_id = _support.case_id
_exact_component_score = _support.exact_component_score
_finalize_rows = _support.finalize_rows
_finite_number = _support.finite_number
_lineage_errors = _support.lineage_errors
_load_expected_contracts = _support.load_expected_contracts
_load_previous_scores = _support.load_previous_scores
_new_bucket = _support.new_bucket
_recommend = _support.recommend
_resolve_target_path = _support.resolve_target_path
render_markdown = _support.render_markdown


REGISTRY_PATH = REPO_ROOT / "docs" / "evals" / "registry.yaml"
TASK_PATH = REPO_ROOT / "benchmarks" / "tasks" / "video-understanding.yaml"
BENCHMARK_ROOT = REPO_ROOT / "benchmarks"
_DIMENSION_NAMES = _support.DIMENSION_NAMES
_RUBRIC_PASS_THRESHOLD = 0.8


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result-file", action="append", required=True, type=Path)
    parser.add_argument("--output-prefix", type=Path)
    args = parser.parse_args()

    result_files = [path.resolve() for path in args.result_file]
    output_prefix = (
        args.output_prefix.resolve()
        if args.output_prefix
        else result_files[0].with_suffix("")
    )

    results = []
    for result_file in result_files:
        data = json.loads(result_file.read_text())
        results.extend(data.get("results", {}).get("results", []))
    summary = build_summary(results)

    json_path = output_prefix.with_name(output_prefix.name + "-report.json")
    md_path = output_prefix.with_name(output_prefix.name + "-report.md")
    json_path.write_text(json.dumps(summary, indent=2) + "\n")
    md_path.write_text(render_markdown(summary))
    print(json_path)
    print(md_path)


def build_summary(
    results: list[dict],
    *,
    expected_cases: set[str] | None = None,
    expected_contracts: dict[str, dict] | None = None,
) -> dict:
    if expected_cases is None:
        expected_contracts = expected_contracts or _load_expected_contracts(
            TASK_PATH, BENCHMARK_ROOT
        )
        expected_cases = set(expected_contracts)
    providers: dict[str, dict] = defaultdict(_new_bucket)
    for entry in results:
        _record_entry(
            entry,
            providers=providers,
            expected_contracts=expected_contracts,
        )
    rows = _finalize_rows(
        providers,
        expected_cases=expected_cases,
        previous_scores=_load_previous_scores(REGISTRY_PATH),
    )
    return {
        "eval_id": "video-understanding",
        "prompt_version": _support.CURRENT_PROMPT_VERSION,
        "expected_cases": sorted(expected_cases),
        "models": rows,
        "recommendation": _recommend(rows),
    }


def _record_entry(
    entry: dict,
    *,
    providers: dict[str, dict],
    expected_contracts: dict[str, dict] | None,
) -> None:
    provider = entry.get("provider", {})
    label = provider.get("label") or provider.get("id") or "unknown"
    vars_data = entry.get("vars", {})
    current_case = _case_id(vars_data)
    bucket = providers[label]
    if current_case in bucket["case_ids"]:
        bucket["duplicate_case_ids"].add(current_case)
    bucket["case_ids"].add(current_case)
    bucket["calls"] += 1

    contract = expected_contracts.get(current_case) if expected_contracts else None
    for error in _lineage_errors(
        entry,
        case_contract=contract,
        benchmark_root=BENCHMARK_ROOT,
    ):
        bucket["contract_errors"].append(f"{current_case}: {error}")

    stored_python, stored_python_pass, python_error = _exact_component_score(
        entry, "python"
    )
    rubric_score, rubric_pass, rubric_error = _exact_component_score(
        entry, "llm-rubric"
    )
    del stored_python  # The current scorer, not the retained component, is authoritative.
    for error in (python_error, rubric_error):
        if error:
            bucket["contract_errors"].append(f"{current_case}: {error}")

    python_score = None
    current_hard_constraints_passed = False
    dimension_scores = dict.fromkeys(_DIMENSION_NAMES, 0.0)
    try:
        evaluation_id = str(vars_data.get("evaluation_id", "")).strip()
        score = score_output_against_target(
            output=entry.get("response", {}).get("output", ""),
            target_path=_resolve_target_path(
                str(vars_data.get("target_path", "")), BENCHMARK_ROOT
            ),
            model_label=label,
            prompt_version=entry.get("response", {}).get("metadata", {}).get(
                "prompt_version"
            ),
            expected_clip_id=evaluation_id or None,
        )
        raw_python_score = float(score.overall_score)
        finalized = _scorer.finalize_score(
            raw_python_score,
            pass_threshold=_scorer.PASS_THRESHOLD,
            hard_gates=bool(
                getattr(
                    score,
                    "hard_constraints_passed",
                    raw_python_score >= _scorer.PASS_THRESHOLD,
                )
            ),
            reason=f"current_regrade={raw_python_score:.4f}",
        )
        python_score = float(finalized["score"])
        current_hard_constraints_passed = bool(finalized["pass"])
        dimension_scores = {
            dimension.dimension: dimension.score for dimension in score.dimensions
        }
    except ValueError:
        python_score = 0.0
    except Exception as exc:
        bucket["regrade_errors"].append(
            f"{current_case}: {type(exc).__name__}: {exc}"
        )

    component_contract_ok = python_error is None and rubric_error is None
    if python_score is not None:
        bucket["python_scores"].append(python_score)
    if rubric_score is not None:
        bucket["rubric_scores"].append(rubric_score)
    if python_score is not None and rubric_score is not None and component_contract_ok:
        bucket["combined_scores"].append((python_score + rubric_score) / 2)
        if (
            stored_python_pass is not True
            or not current_hard_constraints_passed
            or python_score < _scorer.PASS_THRESHOLD
            or rubric_pass is not True
            or rubric_score < _RUBRIC_PASS_THRESHOLD
        ):
            bucket["failed_case_ids"].add(current_case)
    else:
        bucket["incomplete_case_ids"].add(current_case)

    latency = _finite_number(entry.get("latencyMs"), minimum=0.0)
    cost = _finite_number(entry.get("cost"), minimum=0.0)
    if latency is None:
        bucket["contract_errors"].append(
            f"{current_case}: latencyMs must be finite and non-negative"
        )
    else:
        bucket["latencies"].append(latency)
    if cost is None or cost == 0.0:
        bucket["contract_errors"].append(f"{current_case}: cost must be finite and positive")
    else:
        bucket["costs"].append(cost)
    for name, value in dimension_scores.items():
        bucket["dimension_scores"][name].append(value)


if __name__ == "__main__":
    main()
