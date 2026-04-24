#!/usr/bin/env python3
"""Join storyboard runtime and promptfoo results into one decision summary."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from statistics import mean
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
DATASET_ROOT = REPO_ROOT / "benchmarks" / "storyboard_generation_quality"
REGISTRY_PATH = REPO_ROOT / "docs" / "evals" / "registry.yaml"
BASELINE_VARIANT = "gpt_image_2_storyboards"
SCORER_ROOT = REPO_ROOT / "benchmarks" / "scorers"
if str(SCORER_ROOT) not in sys.path:
    sys.path.insert(0, str(SCORER_ROOT))

storyboard_scorer = importlib.import_module("storyboard_understanding_scorer")


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
            storyboard_id=str(variant_entries[0].get("vars", {}).get("storyboard_id", "")),
        )
        dimension_scores = _mean_dimension_scores(variant_entries)
        quality_rows[variant] = {
            "candidate_variant": variant,
            "candidate_label": meta.get("candidate_label") or variant,
            "python_overall": _mean_component(variant_entries, "python"),
            "rubric_overall": _mean_component(variant_entries, "llm-rubric"),
            "overall": _mean_component(variant_entries, None),
            "dimension_scores": dimension_scores,
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
                "image_model": runtime.get("image_model"),
                "success_ratio": runtime.get("success_ratio"),
                "quality_overall": quality.get("overall"),
                "quality_python": quality.get("python_overall"),
                "quality_rubric": quality.get("rubric_overall"),
                "dimension_scores": quality.get("dimension_scores") or {},
                "mean_total_elapsed_ms": runtime.get("mean_total_elapsed_ms"),
                "mean_storyboard_stage_elapsed_ms": runtime.get("mean_storyboard_stage_elapsed_ms"),
                "mean_total_cost_usd": runtime.get("mean_total_cost_usd"),
                "mean_total_frames": runtime.get("mean_total_frames"),
                "mean_available_reference_image_count": runtime.get(
                    "mean_available_reference_image_count"
                ),
                "mean_prompt_reference_frame_count": runtime.get(
                    "mean_prompt_reference_frame_count"
                ),
                "mean_direct_reference_input_count": runtime.get(
                    "mean_direct_reference_input_count"
                ),
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
        "eval_id": "storyboard-generation-quality",
        "candidates": rows,
        "recommendation": recommendation,
        "previous_default": _registry_default(),
    }


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Storyboard Generation Quality Decision",
        "",
        f"Recommendation: **{summary['recommendation']['decision']}**",
        "",
        summary["recommendation"]["rationale"],
        "",
        (
            "| Candidate | Quality | Story | Style | Identity | Reference | Text | "
            "Python | Rubric | Mean Total ms | Storyboard Stage ms | Mean Cost | "
            "Frames | Available Refs | "
            "Prompt Ref Frames | Direct Refs | Success |"
        ),
        (
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | "
            "---: | ---: | ---: | ---: | ---: | ---: |"
        ),
    ]
    for row in summary["candidates"]:
        dimensions = row.get("dimension_scores") or {}
        lines.append(
            f"| {row['candidate_label']} | "
            f"{_fmt(row['quality_overall'])} | "
            f"{_fmt(dimensions.get('story_specificity'))} | "
            f"{_fmt(dimensions.get('style_consistency'))} | "
            f"{_fmt(dimensions.get('identity_consistency'))} | "
            f"{_fmt(dimensions.get('reference_fidelity'))} | "
            f"{_fmt(dimensions.get('text_cleanliness'))} | "
            f"{_fmt(row['quality_python'])} | "
            f"{_fmt(row['quality_rubric'])} | "
            f"{_fmt(row['mean_total_elapsed_ms'])} | "
            f"{_fmt(row['mean_storyboard_stage_elapsed_ms'])} | "
            f"{_fmt_cost(row['mean_total_cost_usd'])} | "
            f"{_fmt(row['mean_total_frames'])} | "
            f"{_fmt(row['mean_available_reference_image_count'])} | "
            f"{_fmt(row['mean_prompt_reference_frame_count'])} | "
            f"{_fmt(row['mean_direct_reference_input_count'])} | "
            f"{_fmt(row['success_ratio'])} |"
        )
    return "\n".join(lines).rstrip() + "\n"


def _recommend(rows: list[dict[str, Any]]) -> dict[str, str]:
    if not rows:
        return {
            "decision": "keep_current_default",
            "rationale": "No storyboard-quality results were available.",
        }
    baseline = next((row for row in rows if row["candidate_variant"] == BASELINE_VARIANT), None)
    if baseline is None:
        return {
            "decision": "keep_current_default",
            "rationale": "Current default storyboard candidate is missing from the result set.",
        }

    available_refs = float(baseline.get("mean_available_reference_image_count") or 0.0)
    prompt_refs = float(baseline.get("mean_prompt_reference_frame_count") or 0.0)
    direct_refs = float(baseline.get("mean_direct_reference_input_count") or 0.0)
    quality = float(baseline.get("quality_overall") or 0.0)

    if available_refs > 0.0 and (prompt_refs <= 0.0 or direct_refs <= 0.0):
        return {
            "decision": "lane_drops_references_before_generation",
            "rationale": (
                "The default storyboard lane had reference images available on the project "
                "state, but the measured prompt-reference and direct-reference counts stayed at "
                "zero. That is a structural failure before any subjective image judging."
            ),
        }
    if quality < 0.75:
        return {
            "decision": "quality_below_initial_floor",
            "rationale": (
                f"The current default storyboard lane scored {quality:.3f}, below the initial "
                "0.75 usefulness floor. The eval is doing its job by making that failure "
                "repeatable instead of anecdotal."
            ),
        }
    return {
        "decision": "lane_clears_initial_floor",
        "rationale": (
            "The current default storyboard lane cleared the initial quality floor and did not "
            "show an obvious structural reference-flow failure on the measured cases."
        ),
    }


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
        value = entry.get("cost") if key == "cost" else entry.get(key)
        if value is not None:
            values.append(float(value))
    if not values:
        return None
    return round(mean(values), 6)


def _mean_dimension_scores(entries: list[dict[str, Any]]) -> dict[str, float]:
    values_by_dimension: dict[str, list[float]] = {}
    for entry in entries:
        output = _entry_output(entry)
        target_path = str(entry.get("vars", {}).get("target_path") or "").strip()
        if not output or not target_path:
            continue
        try:
            score = storyboard_scorer.score_output_against_target(
                output=output,
                target_path=storyboard_scorer._resolve_relative(target_path),
                model_label="promptfoo-provider",
                prompt_version="storyboard-understanding-v2",
            )
        except Exception:
            continue
        for dimension in score.dimensions:
            values_by_dimension.setdefault(dimension.dimension, []).append(float(dimension.score))
    return {
        dimension: round(mean(values), 4)
        for dimension, values in sorted(values_by_dimension.items())
        if values
    }


def _entry_output(entry: dict[str, Any]) -> str | dict[str, Any] | None:
    response = entry.get("response")
    if isinstance(response, dict):
        output = response.get("output")
        if output:
            return output
    if isinstance(response, str) and response.strip():
        return response
    return None


def _load_candidate_meta(
    *,
    dataset_root: Path,
    candidate_variant: str,
    storyboard_id: str,
) -> dict[str, Any]:
    meta_path = dataset_root / candidate_variant / storyboard_id / "meta.json"
    if not meta_path.exists():
        return {}
    payload = json.loads(meta_path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _registry_default() -> str | None:
    if not REGISTRY_PATH.exists():
        return BASELINE_VARIANT
    data = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    for entry in data.get("evals", []):
        if entry.get("id") == "storyboard-generation-quality":
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
