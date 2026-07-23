#!/usr/bin/env python3
"""Join complete storyboard runtime and current-contract quality evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml
from storyboard_generation_quality_report_support import (
    expected_case_ids,
    regrade_variant,
    runtime_contract_by_variant,
    validated_result_matrix,
)

from cine_forge.evals.retained_media import (
    sha256_file,
    validate_retained_media_manifest,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DATASET_ROOT = REPO_ROOT / "benchmarks" / "storyboard_generation_quality"
REGISTRY_PATH = REPO_ROOT / "docs" / "evals" / "registry.yaml"
BASELINE_VARIANT = "gpt_image_2_template_grid_storyboards"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-result", type=Path, required=True)
    parser.add_argument("--promptfoo-result", type=Path, required=True)
    parser.add_argument("--output-prefix", type=Path, required=True)
    parser.add_argument("--dataset-root", type=Path, default=DATASET_ROOT)
    args = parser.parse_args()

    runtime_path = args.runtime_result.resolve()
    promptfoo_path = args.promptfoo_result.resolve()
    runtime_payload = json.loads(runtime_path.read_text(encoding="utf-8"))
    promptfoo_payload = json.loads(promptfoo_path.read_text(encoding="utf-8"))
    dataset_root = args.dataset_root.resolve()
    summary = build_summary(
        runtime_payload=runtime_payload,
        promptfoo_payload=promptfoo_payload,
        dataset_root=dataset_root,
    )
    retained = summary["retained_media"]
    if retained["runtime_result_sha256"] != sha256_file(runtime_path):
        raise ValueError("dataset manifest does not bind the supplied runtime result")
    retained.update(
        {
            "runtime_result": _repo_display(runtime_path),
            "promptfoo_result": _repo_display(promptfoo_path),
            "promptfoo_result_sha256": sha256_file(promptfoo_path),
        }
    )
    output_prefix = args.output_prefix.resolve()
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    output_prefix.with_suffix(".json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    output_prefix.with_suffix(".md").write_text(render_markdown(summary), encoding="utf-8")


def build_summary(
    *,
    runtime_payload: dict[str, Any],
    promptfoo_payload: dict[str, Any],
    dataset_root: Path,
    baseline_variant: str | None = None,
) -> dict[str, Any]:
    cases = expected_case_ids(dataset_root)
    variants, entries_by_variant = validated_result_matrix(
        runtime_payload=runtime_payload,
        promptfoo_payload=promptfoo_payload,
        expected_cases=cases,
        dataset_root=dataset_root,
    )
    runtime_rows = {
        str(row["candidate_variant"]): dict(row)
        for row in runtime_payload.get("summary", {}).get("candidates", [])
    }
    if set(runtime_rows) != set(variants):
        raise ValueError("runtime candidate summary does not match exact result matrix")
    runtime_contracts = runtime_contract_by_variant(
        runtime_payload=runtime_payload,
        dataset_root=dataset_root,
    )

    rows = [
        _build_candidate_row(
            variant=variant,
            runtime=runtime_rows[variant],
            quality=regrade_variant(entries=entries_by_variant[variant]),
            runtime_contract=runtime_contracts[variant],
        )
        for variant in variants
    ]
    rows.sort(
        key=lambda row: (
            -(row["quality_overall"] or 0.0),
            row["mean_total_elapsed_ms"] or float("inf"),
        )
    )
    previous_default = baseline_variant or _registry_default()
    dataset_manifest_path = dataset_root / "manifest.json"
    dataset_manifest = validate_retained_media_manifest(dataset_manifest_path)
    return {
        "eval_id": "storyboard-generation-quality",
        "evidence_status": "current-contract-complete",
        "expected_cases": cases,
        "retained_media": {
            "manifest": _repo_display(dataset_manifest_path),
            "manifest_sha256": sha256_file(dataset_manifest_path),
            "runtime_result": dataset_manifest.get("runtime_result"),
            "runtime_result_sha256": dataset_manifest.get("runtime_result_sha256"),
        },
        "candidates": rows,
        "recommendation": _recommend(rows, baseline_variant=previous_default),
        "previous_default": previous_default,
    }


def _build_candidate_row(
    *,
    variant: str,
    runtime: dict[str, Any],
    quality: dict[str, Any],
    runtime_contract: dict[str, Any],
) -> dict[str, Any]:
    return {
        "candidate_variant": variant,
        "candidate_label": runtime.get("candidate_label") or variant,
        "image_model": runtime.get("image_model"),
        "success_ratio": runtime.get("success_ratio"),
        "quality_overall": quality["overall"],
        "quality_python_regraded": quality["python_overall"],
        "quality_rubric_recorded": quality["rubric_overall"],
        "hard_constraints_passed": quality["hard_constraints_passed"],
        "quality_gates_passed": quality["quality_gates_passed"],
        "dimension_scores": quality["dimension_scores"],
        "runtime_contract_passed": runtime_contract["passed"],
        "runtime_contract_failures": runtime_contract["failures"],
        "mean_total_elapsed_ms": runtime.get("mean_total_elapsed_ms"),
        "mean_storyboard_stage_elapsed_ms": runtime.get("mean_storyboard_stage_elapsed_ms"),
        "mean_total_cost_usd": runtime.get("mean_total_cost_usd"),
        "mean_total_frames": runtime.get("mean_total_frames"),
        "mean_available_reference_image_count": runtime.get("mean_available_reference_image_count"),
        "mean_prompt_reference_frame_count": runtime.get("mean_prompt_reference_frame_count"),
        "mean_direct_reference_input_count": runtime.get("mean_direct_reference_input_count"),
        "analysis_latency_ms": quality["analysis_latency_ms"],
        "analysis_cost_usd": quality["analysis_cost_usd"],
        "calls": quality["calls"],
    }


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Storyboard Generation Quality Decision",
        "",
        f"- Evidence status: `{summary['evidence_status']}`",
        f"- Retained media manifest: `{summary['retained_media']['manifest']}`",
        f"- Retained media SHA-256: `{summary['retained_media']['manifest_sha256']}`",
        f"- Exact cases: {', '.join(summary['expected_cases'])}",
        f"- Recommendation: **{summary['recommendation']['decision']}**",
        "",
        summary["recommendation"]["rationale"],
        "",
        (
            "| Candidate | Quality | Current Python | Recorded Rubric | Hard | Runtime | "
            "Story | Style | Identity | Text | Mean Total ms | Mean Cost |"
        ),
        "| --- | ---: | ---: | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in summary["candidates"]:
        dimensions = row["dimension_scores"]
        lines.append(
            f"| {row['candidate_label']} | {_fmt(row['quality_overall'])} | "
            f"{_fmt(row['quality_python_regraded'])} | "
            f"{_fmt(row['quality_rubric_recorded'])} | "
            f"{'pass' if row['hard_constraints_passed'] else 'fail'} | "
            f"{'pass' if row['runtime_contract_passed'] else 'fail'} | "
            f"{_fmt(dimensions.get('story_specificity'))} | "
            f"{_fmt(dimensions.get('style_consistency'))} | "
            f"{_fmt(dimensions.get('identity_consistency'))} | "
            f"{_fmt(dimensions.get('text_cleanliness'))} | "
            f"{_fmt(row['mean_total_elapsed_ms'])} | "
            f"{_fmt_cost(row['mean_total_cost_usd'])} |"
        )
    return "\n".join(lines).rstrip() + "\n"


def _recommend(
    rows: list[dict[str, Any]],
    *,
    baseline_variant: str | None,
) -> dict[str, str]:
    active_baseline = baseline_variant or BASELINE_VARIANT
    baseline = next((row for row in rows if row["candidate_variant"] == active_baseline), None)
    if baseline is None:
        return {
            "decision": "evidence_incomplete",
            "rationale": "The configured default is absent from the exact result matrix.",
        }
    if not baseline["runtime_contract_passed"]:
        return {
            "decision": "runtime_contract_failed",
            "rationale": "; ".join(baseline["runtime_contract_failures"]),
        }
    if not baseline["hard_constraints_passed"]:
        return {
            "decision": "analysis_contract_failed",
            "rationale": (
                "At least one default-case analysis failed packet/evidence hard "
                "constraints."
            ),
        }
    if not baseline["quality_gates_passed"]:
        return {
            "decision": "analysis_contract_failed",
            "rationale": (
                "At least one default-case Python or rubric quality gate failed."
            ),
        }
    quality = float(baseline["quality_overall"] or 0.0)
    if quality < 0.75:
        return {
            "decision": "quality_below_initial_floor",
            "rationale": f"The current default scored {quality:.3f}, below the 0.75 floor.",
        }
    return {
        "decision": "lane_clears_initial_floor",
        "rationale": "The current default cleared exact runtime, evidence, and quality gates.",
    }


def _registry_default() -> str:
    data = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    for entry in data.get("evals", []):
        if entry.get("id") == "storyboard-generation-quality":
            return str(entry.get("default_model") or BASELINE_VARIANT)
    return BASELINE_VARIANT


def _fmt(value: float | None) -> str:
    if value is None:
        return "n/a"
    return str(int(value)) if float(value).is_integer() else f"{value:.3f}"


def _fmt_cost(value: float | None) -> str:
    return "n/a" if value is None else f"${value:.4f}"


def _repo_display(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path.resolve())


if __name__ == "__main__":
    main()
