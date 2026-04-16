#!/usr/bin/env python3
"""Join Story 169 runtime and promptfoo quality results into one decision summary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
DATASET_ROOT = REPO_ROOT / "benchmarks" / "final_render_provider_floor"
REGISTRY_PATH = REPO_ROOT / "docs" / "evals" / "registry.yaml"
BASELINE_VARIANT = "openai_sora2"


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
) -> dict[str, Any]:
    runtime_rows: dict[str, dict[str, Any]] = {}
    for row in runtime_payload.get("summary", {}).get("candidates", []):
        runtime_rows[str(row["candidate_variant"])] = dict(row)

    quality_rows: dict[str, dict[str, Any]] = {}
    entries = promptfoo_payload.get("results", {}).get("results", [])
    by_variant: dict[str, list[dict[str, Any]]] = {}
    for entry in entries:
        metadata = entry.get("response", {}).get("metadata", {})
        variant = str(metadata.get("candidate_variant") or "")
        if not variant:
            continue
        by_variant.setdefault(variant, []).append(entry)

    for variant, variant_entries in by_variant.items():
        meta = _load_candidate_meta(
            dataset_root=dataset_root,
            candidate_variant=variant,
            clip_id=str(variant_entries[0].get("vars", {}).get("clip_id", "")),
        )
        quality_rows[variant] = {
            "candidate_variant": variant,
            "candidate_label": meta.get("candidate_label") or variant,
            "python_overall": _mean_component(variant_entries, "python"),
            "rubric_overall": _mean_component(variant_entries, "llm-rubric"),
            "overall": _mean_component(variant_entries, None),
            "analysis_latency_ms": _mean_value(variant_entries, "latencyMs"),
            "analysis_cost_usd": _mean_value(variant_entries, "cost"),
            "calls": len(variant_entries),
        }

    variants = sorted(set(runtime_rows) | set(quality_rows))
    rows: list[dict[str, Any]] = []
    for variant in variants:
        runtime = runtime_rows.get(variant, {})
        quality = quality_rows.get(variant, {})
        rows.append(
            {
                "candidate_variant": variant,
                "candidate_label": quality.get("candidate_label")
                or runtime.get("candidate_label")
                or variant,
                "engine_pack_id": runtime.get("engine_pack_id") or variant,
                "target_model": runtime.get("target_model"),
                "success_ratio": runtime.get("success_ratio"),
                "quality_overall": quality.get("overall"),
                "quality_python": quality.get("python_overall"),
                "quality_rubric": quality.get("rubric_overall"),
                "mean_total_elapsed_ms": runtime.get("mean_total_elapsed_ms"),
                "mean_render_stage_elapsed_ms": runtime.get("mean_render_stage_elapsed_ms"),
                "mean_total_cost_usd": runtime.get("mean_total_cost_usd"),
                "mean_reference_usage_counts": runtime.get("mean_reference_usage_counts", {}),
                "mean_active_input_count": runtime.get("mean_active_input_count"),
                "mean_prompt_context_count": runtime.get("mean_prompt_context_count"),
                "mean_unsupported_count": runtime.get("mean_unsupported_count"),
                "calls": quality.get("calls", 0),
            }
        )

    rows.sort(
        key=lambda row: (
            -(row["quality_overall"] or 0.0),
            row["mean_total_elapsed_ms"] or float("inf"),
        )
    )
    recommendation = _recommend(rows)
    return {
        "eval_id": "final-render-provider-floor",
        "runtime_result_file": str(runtime_payload.get("fixture_manifest", "")),
        "candidates": rows,
        "recommendation": recommendation,
        "previous_default": _registry_default(),
    }


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Final Render Provider Floor Decision",
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


def _recommend(rows: list[dict[str, Any]]) -> dict[str, str]:
    if not rows:
        return {
            "decision": "keep_current_default",
            "rationale": "No provider-floor results were available.",
        }
    baseline = next((row for row in rows if row["candidate_variant"] == BASELINE_VARIANT), None)
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

    best = max(
        eligible,
        key=lambda row: (
            row["quality_overall"] or 0.0,
            -float(row.get("mean_total_elapsed_ms") or 10**12),
            float((row.get("mean_reference_usage_counts") or {}).get("reference_image", 0.0))
            + float((row.get("mean_reference_usage_counts") or {}).get("input_reference", 0.0)),
        ),
    )
    if best["candidate_variant"] == BASELINE_VARIANT:
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

    if quality_margin >= 0.03 and runtime_ratio <= 1.15 and best_direct > baseline_direct:
        return {
            "decision": f"switch_default_to_{best['engine_pack_id']}",
            "rationale": (
                f"{best['candidate_label']} beat the current default by {quality_margin:.3f} "
                f"quality points, stayed within {runtime_ratio:.2f}x of the current total runtime, "
                "and preserved more direct image conditioning on average. That is a defensible "
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


def _direct_inputs(row: dict[str, Any]) -> float:
    usage = row.get("mean_reference_usage_counts") or {}
    return float(usage.get("input_reference", 0.0)) + float(usage.get("reference_image", 0.0))


def _mean_component(entries: list[dict[str, Any]], assertion_type: str | None) -> float | None:
    values: list[float] = []
    for entry in entries:
        if assertion_type is None:
            score = entry.get("score")
            if score is not None:
                values.append(float(score))
            continue
        for component in entry.get("gradingResult", {}).get("componentResults", []):
            assertion = component.get("assertion", {})
            if assertion.get("type") == assertion_type and component.get("score") is not None:
                values.append(float(component["score"]))
    if not values:
        return None
    return round(mean(values), 4)


def _mean_value(entries: list[dict[str, Any]], key: str) -> float | None:
    values: list[float] = []
    for entry in entries:
        value = entry.get(key)
        if key == "cost":
            value = entry.get("cost")
        if value is not None:
            values.append(float(value))
    if not values:
        return None
    return round(mean(values), 6)


def _load_candidate_meta(
    *,
    dataset_root: Path,
    candidate_variant: str,
    clip_id: str,
) -> dict[str, Any]:
    meta_path = dataset_root / candidate_variant / clip_id / "meta.json"
    if not meta_path.exists():
        return {}
    payload = json.loads(meta_path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _registry_default() -> str | None:
    if not REGISTRY_PATH.exists():
        return BASELINE_VARIANT
    data = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    for entry in data.get("evals", []):
        if entry.get("id") == "final-render-provider-floor":
            return entry.get("default_model") or BASELINE_VARIANT
    return BASELINE_VARIANT


def _fmt(value: float | None) -> str:
    if value is None:
        return "n/a"
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.3f}"


def _fmt_cost(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"${value:.4f}"


if __name__ == "__main__":
    main()
