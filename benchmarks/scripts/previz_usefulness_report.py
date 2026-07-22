#!/usr/bin/env python3
"""Summarize repaired-contract previz-usefulness promptfoo results."""

from __future__ import annotations

import argparse
import importlib
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SCORERS_ROOT = REPO_ROOT / "benchmarks" / "scorers"
DATASET_ROOT = REPO_ROOT / "benchmarks" / "previz_usefulness"
if str(SCORERS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCORERS_ROOT))

_scorer = importlib.import_module("video_understanding_scorer")
_contract = importlib.import_module("previz_usefulness_report_contract")
_rows = importlib.import_module("previz_usefulness_report_rows")
_report_support = importlib.import_module("previz_usefulness_report_support")

REGISTRY_PATH = REPO_ROOT / "docs" / "evals" / "registry.yaml"
_DIMENSION_NAMES = (
    "summary",
    "tone",
    "emotion",
    "color",
    "camera",
    "motion",
    "continuity",
    "audio",
    "evidence",
    "hard_constraints",
)
_RUBRIC_PASS_THRESHOLD = 0.8


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result-file", action="append", required=True, type=Path)
    parser.add_argument("--output-prefix", type=Path)
    parser.add_argument("--dataset-root", type=Path, default=DATASET_ROOT)
    args = parser.parse_args()

    result_files = [path.resolve() for path in args.result_file]
    output_prefix = (
        args.output_prefix.resolve() if args.output_prefix else result_files[0].with_suffix("")
    )
    results: list[dict[str, Any]] = []
    for result_file in result_files:
        payload = json.loads(result_file.read_text(encoding="utf-8"))
        results.extend(payload.get("results", {}).get("results", []))
    summary = build_summary(results, dataset_root=args.dataset_root.resolve())

    json_path = output_prefix.with_name(output_prefix.name + "-report.json")
    md_path = output_prefix.with_name(output_prefix.name + "-report.md")
    json_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(summary), encoding="utf-8")
    print(json_path)
    print(md_path)


def build_summary(
    results: list[dict[str, Any]],
    dataset_root: Path | None = None,
) -> dict[str, Any]:
    """Regrade raw outputs and require the exact candidate x case matrix."""
    dataset_root = dataset_root or DATASET_ROOT
    case_contract = _contract.load_case_contract(dataset_root)
    expected_cases = case_contract["expected_cases"]
    expected_variants = set(case_contract["expected_variants"])
    previous_scores = _contract.load_previous_scores(REGISTRY_PATH)
    providers: dict[str, dict[str, Any]] = defaultdict(_rows.new_bucket)
    observations: list[tuple[str, str]] = []

    for entry in results:
        observations.append(
            _process_entry(
                entry,
                dataset_root=dataset_root,
                case_contract=case_contract,
                providers=providers,
            )
        )

    rows = [
        _rows.build_row(
            variant=variant,
            bucket=bucket,
            expected_cases=set(expected_cases),
            expected_variants=expected_variants,
            previous_scores=previous_scores,
        )
        for variant, bucket in providers.items()
    ]
    rows.sort(
        key=lambda row: (
            not row["failed_cases"],
            row["overall"] if row["overall"] is not None else -1.0,
        ),
        reverse=True,
    )
    complete_variants = {row["candidate_variant"] for row in rows if row["data_complete"]}
    evidence_contract = _contract.matrix_status(
        observations=observations,
        contract=case_contract,
        complete_variants=complete_variants,
    )
    return {
        "eval_id": "previz-usefulness",
        "expected_prompt_version": case_contract["expected_prompt_version"],
        "expected_variants": case_contract["expected_variants"],
        "expected_cases": sorted(expected_cases),
        "evidence_contract": evidence_contract,
        "candidates": rows,
        "recommendation": _report_support.recommend(rows, evidence_contract),
    }


def _process_entry(
    entry: dict[str, Any],
    *,
    dataset_root: Path,
    case_contract: dict[str, Any],
    providers: dict[str, dict[str, Any]],
) -> tuple[str, str]:
    vars_data = _mapping(entry.get("vars"))
    response = _mapping(entry.get("response"))
    response_metadata = _mapping(response.get("metadata"))
    provider = _mapping(entry.get("provider"))
    label = str(provider.get("label") or provider.get("id") or "unknown")
    variant = str(response_metadata.get("candidate_variant") or "<missing-variant>")
    case_id = str(vars_data.get("evaluation_id") or "<missing-case-id>")
    bucket = providers[variant]
    bucket["calls"] += 1
    bucket["labels"].add(label)
    if case_id in bucket["case_ids"]:
        bucket["duplicate_case_ids"].add(case_id)
    bucket["case_ids"].add(case_id)

    target_path = _resolve_target_path(str(vars_data.get("target_path") or ""))
    candidate_meta = _load_candidate_meta(
        candidate_variant=variant,
        clip_id=str(response_metadata.get("clip_id") or ""),
        dataset_root=dataset_root,
    )
    bucket["contract_errors"].extend(
        _entry_contract_errors(
            variant=variant,
            case_id=case_id,
            vars_data=vars_data,
            response=response,
            response_metadata=response_metadata,
            candidate_meta=candidate_meta,
            expected_case=case_contract["expected_cases"].get(case_id),
            expected_variants=set(case_contract["expected_variants"]),
            expected_prompt_version=case_contract["expected_prompt_version"],
            target_path=target_path,
        )
    )
    _rows.collect_candidate_metadata(bucket, candidate_meta, response_metadata)

    python_component = _single_component_result(_components(entry, "python"))
    if python_component is None:
        bucket["contract_errors"].append(
            f"{case_id}: expected one numeric Python assertion with boolean pass"
        )
    recorded_python_passed = python_component[1] if python_component else False
    rubric_component = _single_component_result(_components(entry, "llm-rubric"))
    if rubric_component is None:
        bucket["contract_errors"].append(
            f"{case_id}: expected one numeric LLM-rubric assertion with boolean pass"
        )
    rubric_score, recorded_rubric_passed = rubric_component or (None, False)
    rubric_passed = (
        recorded_rubric_passed
        and rubric_score is not None
        and rubric_score >= _RUBRIC_PASS_THRESHOLD
    )

    python_score, python_passed, dimensions, regrade_error = _current_python_score(
        output=response.get("output", ""),
        target_path=target_path,
        model_label=label,
        prompt_version=response_metadata.get("prompt_version"),
        expected_clip_id=case_id,
    )
    if regrade_error:
        bucket["regrade_errors"].append(f"{case_id}: {regrade_error}")
    combined = (
        mean([python_score, rubric_score])
        if python_score is not None and rubric_score is not None
        else None
    )
    _rows.collect_scores(bucket, python_score, rubric_score, combined, dimensions)
    if combined is None:
        bucket["incomplete_case_ids"].add(case_id)
    elif not recorded_python_passed or not python_passed or not rubric_passed:
        bucket["failed_case_ids"].add(case_id)
    _rows.collect_number(bucket["analysis_latencies"], entry.get("latencyMs"))
    _rows.collect_number(bucket["analysis_costs"], entry.get("cost"))
    return variant, case_id


def _entry_contract_errors(
    *,
    variant: str,
    case_id: str,
    vars_data: dict[str, Any],
    response: dict[str, Any],
    response_metadata: dict[str, Any],
    candidate_meta: dict[str, Any],
    expected_case: dict[str, str] | None,
    expected_variants: set[str],
    expected_prompt_version: str,
    target_path: Path,
) -> list[str]:
    errors: list[str] = []
    if variant not in expected_variants:
        errors.append(f"{case_id}: unexpected candidate variant {variant}")
    if expected_case is None:
        errors.append(f"{case_id}: unexpected evaluation case")
        return errors
    expected_clip = expected_case["clip_id"]
    if vars_data.get("clip_id") != expected_clip:
        errors.append(f"{case_id}: vars clip_id does not match case contract")
    if response_metadata.get("clip_id") != expected_clip:
        errors.append(f"{case_id}: response clip_id does not match case contract")
    if response_metadata.get("evaluation_id") != case_id:
        errors.append(f"{case_id}: response evaluation_id is missing or inconsistent")
    if response_metadata.get("prompt_version") != expected_prompt_version:
        errors.append(f"{case_id}: prompt version is not {expected_prompt_version}")
    if response.get("error"):
        errors.append(f"{case_id}: provider response contains an error")
    expected_target = _resolve_contract_target(expected_case["target_path"])
    if target_path != expected_target:
        errors.append(f"{case_id}: target_path does not match case contract")
    required_meta = {
        "clip_id": expected_clip,
        "candidate_variant": variant,
        "decision_role": "decision_candidate",
        "decision_eligible": True,
        "artifact_status": "retained_candidate_regrade_ready",
    }
    for field, expected in required_meta.items():
        if candidate_meta.get(field) != expected:
            errors.append(f"{case_id}: candidate meta {field} is not {expected!r}")
    return errors


def _current_python_score(
    *,
    output: object,
    target_path: Path,
    model_label: str,
    prompt_version: object,
    expected_clip_id: str,
) -> tuple[float | None, bool, dict[str, float], str | None]:
    dimensions = dict.fromkeys(_DIMENSION_NAMES, 0.0)
    try:
        target_payload = json.loads(target_path.read_text(encoding="utf-8"))
        target = _scorer.VideoAnalysisTarget.model_validate(target_payload)
    except Exception as exc:
        return None, False, dimensions, f"target {type(exc).__name__}: {exc}"
    try:
        prediction = _scorer.parse_prediction(output)
    except ValueError:
        return 0.0, False, dimensions, None
    except Exception as exc:
        return None, False, dimensions, f"prediction {type(exc).__name__}: {exc}"
    try:
        score = _scorer.score_prediction_against_target(
            prediction=prediction,
            target=target,
            model_label=model_label,
            prompt_version=str(prompt_version) if prompt_version is not None else None,
            expected_clip_id=expected_clip_id,
        )
    except Exception as exc:
        return None, False, dimensions, f"scoring {type(exc).__name__}: {exc}"
    finalized = _scorer.finalize_score(
        score.overall_score,
        pass_threshold=_scorer.PASS_THRESHOLD,
        hard_gates=score.hard_constraints_passed,
        reason=_scorer.format_score_reason(score),
    )
    return (
        float(finalized["score"]),
        bool(finalized["pass"]),
        {dimension.dimension: dimension.score for dimension in score.dimensions},
        None,
    )


def _components(entry: dict[str, Any], assertion_type: str) -> list[dict[str, Any]]:
    grading = _mapping(entry.get("gradingResult"))
    components = grading.get("componentResults")
    if not isinstance(components, list):
        return []
    return [
        component
        for component in components
        if isinstance(component, dict)
        and _mapping(component.get("assertion")).get("type") == assertion_type
    ]


def _single_component_result(
    components: list[dict[str, Any]],
) -> tuple[float, bool] | None:
    if len(components) != 1:
        return None
    score = components[0].get("score")
    if isinstance(score, bool) or not isinstance(score, (int, float)):
        return None
    value = float(score)
    passed = components[0].get("pass")
    if not math.isfinite(value) or not 0.0 <= value <= 1.0 or not isinstance(passed, bool):
        return None
    return value, passed


def render_markdown(summary: dict[str, Any]) -> str:
    return _report_support.render_markdown(summary)


def _load_candidate_meta(
    *, candidate_variant: str, clip_id: str, dataset_root: Path
) -> dict[str, Any]:
    if not candidate_variant or not clip_id:
        return {}
    path = dataset_root / candidate_variant / clip_id / "meta.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _resolve_target_path(value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (REPO_ROOT / "benchmarks" / path).resolve()


def _resolve_contract_target(value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (REPO_ROOT / path).resolve()


def _mapping(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


if __name__ == "__main__":
    main()
