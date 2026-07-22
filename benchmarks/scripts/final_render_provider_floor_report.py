#!/usr/bin/env python3
"""Join Story 169 runtime and promptfoo quality results into one decision summary."""

from __future__ import annotations

import argparse
import importlib
import json
import math
import sys
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
DATASET_ROOT = REPO_ROOT / "benchmarks" / "final_render_provider_floor"
TASK_PATH = REPO_ROOT / "benchmarks" / "tasks" / "final-render-provider-floor.yaml"
REGISTRY_PATH = REPO_ROOT / "docs" / "evals" / "registry.yaml"
SCORER_ROOT = REPO_ROOT / "benchmarks" / "scorers"
if str(SCORER_ROOT) not in sys.path:
    sys.path.insert(0, str(SCORER_ROOT))

from final_render_provider_floor_report_contract import validated_evidence  # noqa: E402

_scorer = importlib.import_module("video_understanding_scorer")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-result", type=Path, required=True)
    parser.add_argument("--promptfoo-result", type=Path, required=True)
    parser.add_argument("--output-prefix", type=Path, required=True)
    parser.add_argument("--dataset-root", type=Path, default=DATASET_ROOT)
    args = parser.parse_args()

    runtime_payload = json.loads(args.runtime_result.resolve().read_text(encoding="utf-8"))
    promptfoo_payload = json.loads(args.promptfoo_result.resolve().read_text(encoding="utf-8"))
    summary = build_summary(
        runtime_payload=runtime_payload,
        promptfoo_payload=promptfoo_payload,
        dataset_root=args.dataset_root.resolve(),
    )

    output_prefix = args.output_prefix.resolve()
    json_path = output_prefix.with_suffix(".json")
    md_path = output_prefix.with_suffix(".md")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(summary), encoding="utf-8")
    print(json_path)
    print(md_path)


def build_summary(
    *,
    runtime_payload: dict[str, Any],
    promptfoo_payload: dict[str, Any],
    dataset_root: Path,
    task_path: Path = TASK_PATH,
) -> dict[str, Any]:
    entries = promptfoo_payload.get("results", {}).get("results", [])
    evidence = (
        validated_evidence(
            promptfoo_entries=entries,
            runtime_payload=runtime_payload,
            dataset_root=dataset_root,
            task_path=task_path,
            scorer=_scorer,
        )
        if isinstance(entries, list)
        else None
    )
    rows: list[dict[str, Any]] = []
    if evidence is not None:
        for variant in evidence["variants"]:
            runtime = evidence["runtime_rows"][variant]
            quality = evidence["quality_rows"][variant]
            rows.append(_candidate_row(runtime=runtime, quality=quality))

    rows.sort(
        key=lambda row: (
            -(row["quality_overall"] or 0.0),
            row["mean_total_elapsed_ms"] or float("inf"),
        )
    )
    evidence_status = (
        "decision-grade" if evidence is not None else "contaminated-non-decision-grade"
    )
    policy = _registry_policy()
    previous_default = policy.get("default_model") if policy else None
    recommendation = (
        _recommend(rows, policy=policy)
        if evidence_status == "decision-grade"
        else {
            "decision": "hold_current_default_repaired_rerun_required",
            "rationale": (
                "The supplied evidence did not satisfy the maintained v2 task matrix, current "
                "scorer replay, and runtime reconciliation contract. Run a complete repaired-v2 "
                "evaluation before reconsidering the provider default."
            ),
        }
    )
    return {
        "eval_id": "final-render-provider-floor",
        "evidence_status": evidence_status,
        "runtime_fixture_manifest": str(runtime_payload.get("fixture_manifest", "")),
        "runtime_result": evidence["runtime_result"] if evidence is not None else None,
        "candidates": rows,
        "recommendation": recommendation,
        "previous_default": previous_default,
    }


def _candidate_row(
    *, runtime: dict[str, Any], quality: dict[str, Any]
) -> dict[str, Any]:
    return {
        "candidate_variant": runtime["candidate_variant"],
        "candidate_label": runtime["candidate_label"],
        "engine_pack_id": runtime["engine_pack_id"],
        "target_model": runtime["target_model"],
        "success_ratio": runtime["success_ratio"],
        "quality_overall": quality["overall"],
        "quality_python": quality["python_overall"],
        "quality_rubric": quality["rubric_overall"],
        "mean_total_elapsed_ms": runtime["mean_total_elapsed_ms"],
        "mean_render_stage_elapsed_ms": runtime["mean_render_stage_elapsed_ms"],
        "mean_total_cost_usd": runtime["mean_total_cost_usd"],
        "mean_reference_usage_counts": runtime["mean_reference_usage_counts"],
        "mean_active_input_count": runtime["mean_active_input_count"],
        "mean_prompt_context_count": runtime["mean_prompt_context_count"],
        "mean_unsupported_count": runtime["mean_unsupported_count"],
        "analysis_latency_ms": quality["analysis_latency_ms"],
        "analysis_cost_usd": quality["analysis_cost_usd"],
        "calls": quality["calls"],
    }


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Final Render Provider Floor Decision",
        "",
        f"Evidence status: **{summary['evidence_status']}**",
        "",
        f"Recommendation: **{summary['recommendation']['decision']}**",
        "",
        summary["recommendation"]["rationale"],
        "",
        (
            "| Candidate | Quality | Python | Rubric | Mean Total ms | "
            "Mean Render ms | Mean Cost | Direct Inputs | Prompt Context | "
            "Success |"
        ),
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in summary["candidates"]:
        usage = row.get("mean_reference_usage_counts") or {}
        direct_inputs = float(usage.get("input_reference", 0.0)) + float(
            usage.get("reference_image", 0.0)
        )
        lines.append(
            f"| {row['candidate_label']} | "
            f"{_fmt(row['quality_overall'])} | "
            f"{_fmt(row['quality_python'])} | "
            f"{_fmt(row['quality_rubric'])} | "
            f"{_fmt(row['mean_total_elapsed_ms'])} | "
            f"{_fmt(row['mean_render_stage_elapsed_ms'])} | "
            f"{_fmt_cost(row['mean_total_cost_usd'])} | "
            f"{_fmt(direct_inputs)} | "
            f"{_fmt(row['mean_prompt_context_count'])} | "
            f"{_fmt(row['success_ratio'])} |"
        )
    return "\n".join(lines).rstrip() + "\n"


def _recommend(
    rows: list[dict[str, Any]], *, policy: dict[str, Any] | None
) -> dict[str, str]:
    if not rows:
        return {
            "decision": "keep_current_default",
            "rationale": "No provider-floor results were available.",
        }
    if not policy:
        return {
            "decision": "keep_current_default",
            "rationale": "The configured default and target gates could not be resolved.",
        }
    baseline_variant = policy["default_model"]
    baseline = next(
        (row for row in rows if row["candidate_variant"] == baseline_variant),
        None,
    )
    if baseline is None:
        return {
            "decision": "keep_current_default",
            "rationale": "Current default candidate is missing from the result set.",
        }

    eligible = [
        row
        for row in rows
        if (row.get("success_ratio") or 0.0) >= 1.0 and row.get("quality_overall") is not None
    ]
    if not eligible:
        return {
            "decision": "keep_current_default",
            "rationale": "No candidate completed the full matrix with usable quality scores.",
        }

    challengers = [
        row for row in eligible if row["candidate_variant"] != baseline_variant
    ]
    target_qualified = [
        row for row in challengers if not _target_failures(row, policy)
    ]
    if not target_qualified:
        strongest = max(
            challengers,
            key=_candidate_rank,
            default=None,
        )
        failures = _target_failures(strongest, policy) if strongest else []
        if failures:
            return {
                "decision": "keep_current_default_target_missed",
                "rationale": (
                    f"{strongest['candidate_label']} cannot replace the current default because "
                    f"it missed maintained target gates: {', '.join(failures)}."
                ),
            }

    best = max(
        [baseline, *target_qualified],
        key=_candidate_rank,
    )
    if best["candidate_variant"] == baseline_variant:
        return {
            "decision": "keep_current_default",
            "rationale": (
                f"{baseline['candidate_label']} remains the strongest measured option. "
                "No other wired pack cleared both the quality and runtime bars strongly "
                "enough to justify a default change."
            ),
        }

    quality_margin = float(best["quality_overall"] or 0.0) - float(
        baseline.get("quality_overall") or 0.0
    )
    baseline_runtime = float(baseline.get("mean_total_elapsed_ms") or 0.0)
    best_runtime = float(best.get("mean_total_elapsed_ms") or 0.0)
    runtime_ratio = (best_runtime / baseline_runtime) if baseline_runtime else 999.0
    baseline_direct = _direct_inputs(baseline)
    best_direct = _direct_inputs(best)

    if quality_margin >= 0.03 and runtime_ratio <= 1.15 and best_direct >= baseline_direct:
        return {
            "decision": f"switch_default_to_{best['engine_pack_id']}",
            "rationale": (
                f"{best['candidate_label']} beat the current default by {quality_margin:.3f} "
                f"quality points, stayed within {runtime_ratio:.2f}x of the current total runtime, "
                "and preserved at least as much direct image conditioning on average. That is a "
                "provider-floor improvement instead of noisy churn."
            ),
        }

    return {
        "decision": "keep_current_default_no_clear_winner",
        "rationale": (
            f"{best['candidate_label']} looked strongest on at least one axis, but the measured "
            "margin was not strong enough to justify a default flip. Keep the current default and "
            "treat the result as evidence, not as a decisive pack change."
        ),
    }


def _candidate_rank(row: dict[str, Any]) -> tuple[float, float, float]:
    return (
        row["quality_overall"] or 0.0,
        -float(row.get("mean_total_elapsed_ms") or 10**12),
        _direct_inputs(row),
    )


def _target_failures(row: dict[str, Any], policy: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if float(row["quality_overall"]) < policy["quality_min"]:
        failures.append(f"quality < {policy['quality_min']}")
    if float(row["mean_total_elapsed_ms"]) > policy["latency_max"]:
        failures.append(f"latency > {policy['latency_max']} ms")
    if float(row["mean_total_cost_usd"]) > policy["cost_max"]:
        failures.append(f"cost > ${policy['cost_max']}")
    return failures


def _direct_inputs(row: dict[str, Any]) -> float:
    usage = row.get("mean_reference_usage_counts") or {}
    return float(usage.get("input_reference", 0.0)) + float(usage.get("reference_image", 0.0))


def _registry_default() -> str | None:
    policy = _registry_policy()
    return policy.get("default_model") if policy else None


def _registry_policy() -> dict[str, Any] | None:
    if not REGISTRY_PATH.exists():
        return None
    data = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    for entry in data.get("evals", []):
        if entry.get("id") == "final-render-provider-floor":
            default_model = entry.get("default_model")
            target = entry.get("target")
            values = (
                target.get("value"),
                target.get("latency_ms_max"),
                target.get("cost_usd_max"),
            ) if isinstance(target, dict) else ()
            if not isinstance(default_model, str) or len(values) != 3:
                return None
            if any(
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(float(value))
                or float(value) <= 0
                for value in values
            ):
                return None
            return {
                "default_model": default_model,
                "quality_min": float(values[0]),
                "latency_max": float(values[1]),
                "cost_max": float(values[2]),
            }
    return None


def _fmt(value: float | None) -> str:
    if value is None:
        return "n/a"
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.3f}"


def _fmt_cost(value: float | None) -> str:
    return "n/a" if value is None else f"${value:.4f}"


if __name__ == "__main__":
    main()
