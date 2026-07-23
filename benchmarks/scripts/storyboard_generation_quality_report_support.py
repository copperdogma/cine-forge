"""Coverage, regrading, and runtime-contract helpers for storyboard reports."""

from __future__ import annotations

import importlib
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

from cine_forge.evals.retained_media import (
    sha256_file,
    validate_retained_media_manifest,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SCORER_ROOT = REPO_ROOT / "benchmarks" / "scorers"
if str(SCORER_ROOT) not in sys.path:
    sys.path.insert(0, str(SCORER_ROOT))

storyboard_scorer = importlib.import_module("storyboard_understanding_scorer")


def expected_case_ids(dataset_root: Path) -> list[str]:
    path = dataset_root / "manifest.json"
    payload = validate_retained_media_manifest(path)
    case_ids = [str(item) for item in payload.get("expected_cases", [])]
    if not case_ids or len(case_ids) != len(set(case_ids)):
        raise ValueError("dataset manifest must declare unique expected_cases")
    return case_ids


def validated_result_matrix(
    *,
    runtime_payload: dict[str, Any],
    promptfoo_payload: dict[str, Any],
    expected_cases: list[str],
    dataset_root: Path,
) -> tuple[list[str], dict[str, list[dict[str, Any]]]]:
    variants = [str(item) for item in runtime_payload.get("candidate_variants", [])]
    if not variants or len(variants) != len(set(variants)):
        raise ValueError("runtime result must declare unique candidate_variants")
    expected = {(variant, case_id) for variant in variants for case_id in expected_cases}
    _require_dataset_matrix(dataset_root=dataset_root, expected=expected)
    dataset_manifest_sha256 = sha256_file(dataset_root / "manifest.json")

    runtime_keys: list[tuple[str, str]] = []
    for run in runtime_payload.get("runs", []):
        if not run.get("success"):
            raise ValueError(
                f"runtime case failed: {run.get('candidate_variant')}/{run.get('case_id')}"
            )
        runtime_keys.append((str(run.get("candidate_variant", "")), str(run.get("case_id", ""))))
    _require_exact_keys("runtime", runtime_keys, expected)

    by_variant: dict[str, list[dict[str, Any]]] = defaultdict(list)
    promptfoo_keys: list[tuple[str, str]] = []
    entries = promptfoo_payload.get("results", {}).get("results", [])
    for entry in entries:
        response = entry.get("response")
        if not isinstance(response, dict) or not response.get("output"):
            raise ValueError("promptfoo entry is missing provider output")
        metadata = response.get("metadata") or {}
        variant = str(metadata.get("candidate_variant") or "")
        case_id = str(entry.get("vars", {}).get("storyboard_id") or "")
        if metadata.get("prompt_version") != storyboard_scorer.PROMPT_VERSION:
            raise ValueError(
                f"stale storyboard prompt contract for {variant}/{case_id}: "
                f"{metadata.get('prompt_version')!r}"
            )
        if metadata.get("dataset_manifest_sha256") != dataset_manifest_sha256:
            raise ValueError(
                f"storyboard result used the wrong retained dataset for {variant}/{case_id}"
            )
        expected_asset_sha256 = sha256_file(
            dataset_root / variant / case_id / "assets.sha256.json"
        )
        if metadata.get("asset_manifest_sha256") != expected_asset_sha256:
            raise ValueError(
                f"storyboard result used the wrong asset packet for {variant}/{case_id}"
            )
        promptfoo_keys.append((variant, case_id))
        by_variant[variant].append(entry)
    _require_exact_keys("promptfoo", promptfoo_keys, expected)
    return variants, dict(by_variant)


def _require_dataset_matrix(
    *,
    dataset_root: Path,
    expected: set[tuple[str, str]],
) -> None:
    payload = validate_retained_media_manifest(dataset_root / "manifest.json")
    rows = payload.get("sequences")
    if not isinstance(rows, list):
        raise ValueError("dataset manifest sequences must be a list")
    observed = [
        (str(row.get("candidate_variant", "")), str(row.get("storyboard_id", "")))
        for row in rows
        if isinstance(row, dict)
    ]
    _require_exact_keys("dataset", observed, expected)


def regrade_variant(
    *,
    entries: list[dict[str, Any]],
) -> dict[str, Any]:
    scores = []
    python_values: list[float] = []
    python_passes: list[bool] = []
    recorded_python_passes: list[bool] = []
    dimensions: dict[str, list[float]] = defaultdict(list)
    rubric_values: list[float] = []
    rubric_passes: list[bool] = []
    for entry in entries:
        target_path = storyboard_scorer._resolve_relative(
            str(entry.get("vars", {}).get("target_path") or "")
        )
        score = storyboard_scorer.score_output_against_target(
            output=_entry_output(entry),
            target_path=target_path,
            model_label="promptfoo-provider",
            prompt_version=storyboard_scorer.PROMPT_VERSION,
        )
        scores.append(score)
        finalized = storyboard_scorer.finalize_score(
            score.overall_score,
            pass_threshold=storyboard_scorer.PASS_THRESHOLD,
            hard_gates=score.hard_constraints_passed,
            reason=storyboard_scorer.format_score_reason(score),
        )
        python_values.append(float(finalized["score"]))
        python_passes.append(bool(finalized["pass"]))
        for dimension in score.dimensions:
            dimensions[dimension.dimension].append(float(dimension.score))
        _stored_python_score, stored_python_passed = _required_component_result(
            entry, "python"
        )
        recorded_python_passes.append(stored_python_passed)
        rubric_score, rubric_passed = _required_component_result(entry, "llm-rubric")
        rubric_values.append(rubric_score)
        rubric_passes.append(rubric_passed)
    python_overall = mean(python_values)
    rubric_overall = mean(rubric_values)
    hard_constraints_passed = all(score.hard_constraints_passed for score in scores)
    quality_gates_passed = (
        all(python_passes)
        and all(recorded_python_passes)
        and all(rubric_passes)
    )
    return {
        "python_overall": round(python_overall, 4),
        "rubric_overall": round(rubric_overall, 4),
        "overall": (
            round((python_overall + rubric_overall) / 2, 4)
            if quality_gates_passed
            else None
        ),
        "hard_constraints_passed": hard_constraints_passed,
        "quality_gates_passed": quality_gates_passed,
        "dimension_scores": {
            name: round(mean(values), 4) for name, values in sorted(dimensions.items())
        },
        "analysis_latency_ms": _mean_entry_value(entries, "latencyMs"),
        "analysis_cost_usd": _mean_entry_value(entries, "cost"),
        "calls": len(entries),
    }


def runtime_contract_by_variant(
    *,
    runtime_payload: dict[str, Any],
    dataset_root: Path,
) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for run in runtime_payload.get("runs", []):
        variant = str(run["candidate_variant"])
        case_id = str(run["case_id"])
        target = json.loads(
            (dataset_root / "targets" / case_id / "target.json").read_text(encoding="utf-8")
        )
        failures = _runtime_failures(run=run, target=target)
        grouped[variant].extend(f"{case_id}: {failure}" for failure in failures)
    return {
        variant: {"passed": not failures, "failures": failures}
        for variant, failures in grouped.items()
    }


def _runtime_failures(*, run: dict[str, Any], target: dict[str, Any]) -> list[str]:
    expected_reference_count = len(target.get("reference_expectations", []))
    available_reference_count = int(run.get("available_reference_image_count", 0))
    prompt_reference_count = int(run.get("prompt_reference_frame_count", 0))
    direct_reference_count = int(run.get("direct_reference_input_count", 0))
    checks = [
        (
            int(run.get("total_frames", 0)) >= int(target["expected_frame_min"])
            and int(run.get("total_frames", 0)) <= int(target["expected_frame_max"]),
            "frame count outside source-target range",
        ),
        (
            available_reference_count == expected_reference_count,
            "available reference count does not match the source fixture",
        ),
        (
            prompt_reference_count
            >= int(target["expected_prompt_reference_min"]),
            "prompt reference count below minimum",
        ),
        (
            direct_reference_count
            >= int(target["expected_direct_reference_min"]),
            "direct reference count below minimum",
        ),
        (
            bool(run.get("reference_transport_supported"))
            == bool(expected_reference_count),
            "reference-support flag contradicts the source fixture",
        ),
        (
            bool(expected_reference_count)
            or (prompt_reference_count == 0 and direct_reference_count == 0),
            "prompt-only case reports unexpected reference use",
        ),
    ]
    return [message for passed, message in checks if not passed]


def _require_exact_keys(
    label: str,
    observed_keys: list[tuple[str, str]],
    expected: set[tuple[str, str]],
) -> None:
    observed = set(observed_keys)
    duplicates = sorted(key for key in observed if observed_keys.count(key) > 1)
    missing = sorted(expected - observed)
    extra = sorted(observed - expected)
    if duplicates or missing or extra:
        raise ValueError(
            f"{label} matrix mismatch; duplicates={duplicates}; missing={missing}; extra={extra}"
        )


def _entry_output(entry: dict[str, Any]) -> str | dict[str, Any]:
    response = entry.get("response")
    output = response.get("output") if isinstance(response, dict) else None
    if not isinstance(output, (str, dict)) or not output:
        raise ValueError("promptfoo entry has no regradable output")
    return output


def _required_component_result(
    entry: dict[str, Any], assertion_type: str
) -> tuple[float, bool]:
    values: list[tuple[float, bool]] = []
    for component in entry.get("gradingResult", {}).get("componentResults", []):
        if component.get("assertion", {}).get("type") != assertion_type:
            continue
        raw_score = component.get("score")
        if raw_score is None or isinstance(raw_score, bool):
            raise ValueError(f"{assertion_type} score must be numeric")
        value = float(raw_score)
        if not math.isfinite(value) or not 0.0 <= value <= 1.0:
            raise ValueError(f"{assertion_type} score must be finite and within [0, 1]")
        passed = component.get("pass")
        if not isinstance(passed, bool):
            raise ValueError(f"{assertion_type} pass must be boolean")
        values.append((value, passed))
    if len(values) != 1:
        raise ValueError(f"expected exactly one {assertion_type} result; found {len(values)}")
    return values[0]


def _mean_entry_value(entries: list[dict[str, Any]], key: str) -> float | None:
    values: list[float] = []
    for entry in entries:
        raw_value = entry.get(key)
        if raw_value is None or isinstance(raw_value, bool):
            raise ValueError(f"every promptfoo entry must record numeric {key}")
        value = float(raw_value)
        if not math.isfinite(value) or value < 0:
            raise ValueError(f"promptfoo {key} must be finite and non-negative")
        values.append(value)
    return round(mean(values), 6)
