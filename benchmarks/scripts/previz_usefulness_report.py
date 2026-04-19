#!/usr/bin/env python3
"""Summarize Story 143 previz-usefulness promptfoo results into a report."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SCORERS_ROOT = REPO_ROOT / "benchmarks" / "scorers"
DATASET_ROOT = REPO_ROOT / "benchmarks" / "previz_usefulness"
FAST_PREVIZ_BUDGET_MS = 6_000
if str(SCORERS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCORERS_ROOT))

score_output_against_target = importlib.import_module(
    "video_understanding_scorer"
).score_output_against_target

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
_AI_VARIANTS = {
    "openai_sora2_previz",
    "google_veo31_previz",
    "google_veo31_fast_previz",
    "google_veo31_lite_previz",
    "google_veo31_lite_compact_previz",
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result-file", action="append", required=True, type=Path)
    parser.add_argument("--output-prefix", type=Path)
    parser.add_argument("--dataset-root", type=Path, default=DATASET_ROOT)
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
    summary = build_summary(results, dataset_root=args.dataset_root.resolve())

    json_path = output_prefix.with_name(output_prefix.name + "-report.json")
    md_path = output_prefix.with_name(output_prefix.name + "-report.md")
    json_path.write_text(json.dumps(summary, indent=2) + "\n")
    md_path.write_text(render_markdown(summary))
    print(json_path)
    print(md_path)


def build_summary(results: list[dict], dataset_root: Path | None = None) -> dict:
    dataset_root = dataset_root or DATASET_ROOT
    providers: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "python_scores": [],
            "rubric_scores": [],
            "combined_scores": [],
            "analysis_latencies": [],
            "analysis_costs": [],
            "generation_latencies": [],
            "generation_costs": [],
            "dimension_scores": defaultdict(list),
            "calls": 0,
            "variants": set(),
            "operator_lanes": set(),
            "latency_budgets": set(),
            "engine_pack_ids": set(),
            "target_models": set(),
            "resolutions": set(),
            "durations": set(),
            "consistency_strategies": set(),
            "prompt_profiles": set(),
            "style_profile_ids": set(),
            "style_profile_titles": set(),
        }
    )
    previous_scores = _load_previous_scores()

    for entry in results:
        provider = entry.get("provider", {})
        label = provider.get("label", provider.get("id", "unknown"))
        response_metadata = entry.get("response", {}).get("metadata", {})
        clip_id = str(
            response_metadata.get("clip_id") or entry.get("vars", {}).get("clip_id") or ""
        )
        candidate_variant = str(response_metadata.get("candidate_variant") or "")
        candidate_meta = _load_candidate_meta(
            candidate_variant=candidate_variant,
            clip_id=clip_id,
            dataset_root=dataset_root,
        )
        target_path = _resolve_target_path(entry.get("vars", {}).get("target_path", ""))

        python_score = _component_score(entry, "python")
        dimension_scores = dict.fromkeys(_DIMENSION_NAMES, 0.0)
        try:
            score = score_output_against_target(
                output=entry.get("response", {}).get("output", ""),
                target_path=target_path,
                model_label=label,
                prompt_version=response_metadata.get("prompt_version"),
            )
            if python_score is None:
                python_score = score.overall_score
            dimension_scores = {
                dimension.dimension: dimension.score for dimension in score.dimensions
            }
        except Exception:
            if python_score is None:
                python_score = 0.0

        rubric_score = _component_score(entry, "llm-rubric")
        combined_score = mean(
            [value for value in [python_score, rubric_score] if value is not None]
        )

        bucket = providers[label]
        bucket["python_scores"].append(python_score)
        if rubric_score is not None:
            bucket["rubric_scores"].append(rubric_score)
        bucket["combined_scores"].append(combined_score)
        if entry.get("latencyMs") is not None:
            bucket["analysis_latencies"].append(entry["latencyMs"])
        if entry.get("cost") is not None:
            bucket["analysis_costs"].append(entry["cost"])
        if candidate_meta.get("generation_latency_ms") is not None:
            bucket["generation_latencies"].append(candidate_meta["generation_latency_ms"])
        if candidate_meta.get("estimated_generation_cost_usd") is not None:
            bucket["generation_costs"].append(candidate_meta["estimated_generation_cost_usd"])
        if candidate_variant:
            bucket["variants"].add(candidate_variant)
        _maybe_add(bucket["operator_lanes"], candidate_meta.get("operator_lane"))
        _maybe_add(bucket["latency_budgets"], candidate_meta.get("latency_budget_ms"))
        _maybe_add(bucket["engine_pack_ids"], candidate_meta.get("engine_pack_id"))
        _maybe_add(bucket["target_models"], candidate_meta.get("target_model"))
        _maybe_add(bucket["resolutions"], candidate_meta.get("resolution"))
        _maybe_add(bucket["durations"], candidate_meta.get("duration_seconds"))
        _maybe_add(bucket["consistency_strategies"], candidate_meta.get("consistency_strategy"))
        _maybe_add(bucket["prompt_profiles"], candidate_meta.get("prompt_profile"))
        _maybe_add(bucket["style_profile_ids"], candidate_meta.get("style_profile_id"))
        _maybe_add(bucket["style_profile_titles"], candidate_meta.get("style_profile_title"))
        bucket["calls"] += 1
        for name, value in dimension_scores.items():
            bucket["dimension_scores"][name].append(value)

    rows = []
    for label, bucket in providers.items():
        overall = round(mean(bucket["combined_scores"]), 4)
        candidate_variant = _single_or_none(bucket["variants"])
        operator_lane = _single_or_none(bucket["operator_lanes"])
        latency_budget_ms = _single_or_none(bucket["latency_budgets"])
        generation_latency_ms = (
            round(mean(bucket["generation_latencies"])) if bucket["generation_latencies"] else None
        )
        rows.append(
            {
                "candidate": label,
                "candidate_variant": candidate_variant,
                "candidate_class": _candidate_class(candidate_variant, operator_lane),
                "operator_lane": operator_lane,
                "python_overall": round(mean(bucket["python_scores"]), 4),
                "rubric_overall": round(mean(bucket["rubric_scores"]), 4)
                if bucket["rubric_scores"]
                else None,
                "overall": overall,
                "analysis_latency_ms": round(mean(bucket["analysis_latencies"]))
                if bucket["analysis_latencies"]
                else None,
                "analysis_cost_usd": round(mean(bucket["analysis_costs"]), 6)
                if bucket["analysis_costs"]
                else None,
                "generation_latency_ms": generation_latency_ms,
                "generation_cost_usd": round(mean(bucket["generation_costs"]), 4)
                if bucket["generation_costs"]
                else None,
                "latency_budget_ms": latency_budget_ms,
                "latency_budget_pass": (
                    generation_latency_ms <= latency_budget_ms
                    if generation_latency_ms is not None and latency_budget_ms is not None
                    else None
                ),
                "resolution": _single_or_join(bucket["resolutions"]),
                "duration_seconds": _single_or_join(bucket["durations"]),
                "engine_pack_id": _single_or_join(bucket["engine_pack_ids"]),
                "target_model": _single_or_join(bucket["target_models"]),
                "consistency_strategy": _single_or_join(bucket["consistency_strategies"]),
                "prompt_profile": _single_or_join(bucket["prompt_profiles"]),
                "style_profile_id": _single_or_join(bucket["style_profile_ids"]),
                "style_profile_title": _single_or_join(bucket["style_profile_titles"]),
                "dimension_scores": {
                    name: round(mean(values), 4)
                    for name, values in sorted(bucket["dimension_scores"].items())
                },
                "calls": bucket["calls"],
                "previous_overall": previous_scores.get(label),
            }
        )

    rows.sort(key=lambda item: item["overall"], reverse=True)
    return {
        "eval_id": "previz-usefulness",
        "candidates": rows,
        "recommendation": _recommend(rows),
    }


def render_markdown(summary: dict) -> str:
    lines = [
        "# Previz Usefulness Report v2",
        "",
        f"Recommendation: **{summary['recommendation']['decision']}**",
        "",
        summary["recommendation"]["rationale"],
        "",
        (
            "| Candidate | Lane | Overall | Gen Latency | Budget | Gen Cost | "
            "Resolution | Consistency | Prompt | "
            "Analysis Latency | Analysis Cost |"
        ),
        "|---|---|---:|---:|---:|---:|---|---|---|---:|---:|",
    ]
    for row in summary["candidates"]:
        generation_latency = (
            f"{row['generation_latency_ms']} ms"
            if row["generation_latency_ms"] is not None
            else "n/a"
        )
        latency_budget = (
            f"{row['latency_budget_ms']} ms"
            if row["latency_budget_ms"] is not None
            else "n/a"
        )
        generation_cost = (
            f"${row['generation_cost_usd']:.4f}"
            if row["generation_cost_usd"] is not None
            else "n/a"
        )
        analysis_latency = (
            f"{row['analysis_latency_ms']} ms" if row["analysis_latency_ms"] is not None else "n/a"
        )
        analysis_cost = (
            f"${row['analysis_cost_usd']:.5f}" if row["analysis_cost_usd"] is not None else "n/a"
        )
        lines.append(
            f"| {row['candidate']} | {row['operator_lane'] or row['candidate_class']} | "
            f"{row['overall']:.3f} | {generation_latency} | {latency_budget} | "
            f"{generation_cost} | {row['resolution'] or 'n/a'} | "
            f"{row['consistency_strategy'] or 'n/a'} | {row['prompt_profile'] or 'n/a'} | "
            f"{analysis_latency} | {analysis_cost} |"
        )

    lines.extend(["", "## Candidate Notes", ""])
    for row in summary["candidates"]:
        lines.append(f"### {row['candidate']}")
        lines.append(f"- lane: {row['operator_lane'] or row['candidate_class']}")
        lines.append(f"- variant: {row['candidate_variant'] or 'n/a'}")
        lines.append(f"- latency budget: {row['latency_budget_ms'] or 'n/a'}")
        lines.append(f"- engine pack: {row['engine_pack_id'] or 'n/a'}")
        lines.append(f"- target model: {row['target_model'] or 'n/a'}")
        lines.append(f"- prompt profile: {row['prompt_profile'] or 'n/a'}")
        lines.append(
            f"- style profile: {row['style_profile_title'] or row['style_profile_id'] or 'n/a'}"
        )
        for name, value in row["dimension_scores"].items():
            lines.append(f"- {name}: {value:.3f}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _recommend(rows: list[dict[str, Any]]) -> dict[str, str | None]:
    if not rows:
        return {
            "decision": "retest",
            "primary_lane": None,
            "fallback_lane": None,
            "rationale": "No results were available.",
        }

    annotated = next(
        (
            row
            for row in rows
            if row.get("candidate_variant") == "annotated_symbolic"
            or row.get("candidate_class") == "deterministic_baseline"
        ),
        None,
    )
    ai_rows = [row for row in rows if row.get("candidate_class") == "ai_previz"]
    if annotated is None:
        return {
            "decision": "retest",
            "primary_lane": None,
            "fallback_lane": None,
            "rationale": (
                "The deterministic baseline is missing from the dataset, so the fallback/control "
                "policy cannot "
                "be verified."
            ),
        }
    if annotated["generation_latency_ms"] is None:
        return {
            "decision": "retest",
            "primary_lane": None,
            "fallback_lane": annotated["candidate"],
            "rationale": (
                "The deterministic baseline is missing a measured generation latency. Re-run the "
                "deterministic dataset first."
            ),
        }
    if annotated["generation_latency_ms"] > FAST_PREVIZ_BUDGET_MS:
        return {
            "decision": "block",
            "primary_lane": None,
            "fallback_lane": annotated["candidate"],
            "rationale": (
                f"Deterministic baseline measured {annotated['generation_latency_ms']} ms, above "
                f"the {FAST_PREVIZ_BUDGET_MS} ms control-arm budget. Fix the fallback path before "
                "using it as the non-AI comparator."
            ),
        }
    if not ai_rows:
        return {
            "decision": "missing_ai_primary",
            "primary_lane": None,
            "fallback_lane": annotated["candidate"],
            "rationale": (
                f"Deterministic baseline measured {annotated['generation_latency_ms']} ms and "
                f"stays inside the {FAST_PREVIZ_BUDGET_MS} ms control bar, but no AI previz "
                "candidate was present. The product previz requirement remains unmet."
            ),
        }

    best_ai = max(ai_rows, key=lambda item: item["overall"])
    if best_ai["calls"] < 3:
        return {
            "decision": "retest",
            "primary_lane": best_ai["candidate"],
            "fallback_lane": annotated["candidate"],
            "rationale": (
                "AI candidate coverage is incomplete. Run all selected scene packets "
                "before making a primary-lane recommendation."
            ),
        }
    if best_ai["overall"] < 0.75:
        return {
            "decision": "hold_ai_primary_blocked",
            "primary_lane": None,
            "fallback_lane": annotated["candidate"],
            "rationale": (
                f"Deterministic baseline measured {annotated['generation_latency_ms']} ms and "
                f"stays inside the {FAST_PREVIZ_BUDGET_MS} ms control bar. {best_ai['candidate']} "
                f"is the best AI lane at {best_ai['overall']:.3f}, but it still misses the first "
                "usefulness floor for camera/blocking readability, so the product previz lane "
                "remains blocked."
            ),
        }
    if (
        best_ai["generation_cost_usd"] is not None
        and best_ai["generation_latency_ms"] is not None
        and best_ai["generation_latency_ms"] <= FAST_PREVIZ_BUDGET_MS
    ):
        return {
            "decision": "promote_ai_primary",
            "primary_lane": best_ai["candidate"],
            "fallback_lane": annotated["candidate"],
            "rationale": (
                f"{best_ai['candidate']} measured {best_ai['generation_latency_ms']} ms, inside "
                f"the {FAST_PREVIZ_BUDGET_MS} ms fast-previz target, while clearing the quality "
                "bar. It can serve as the honest AI-primary previz lane, with deterministic "
                "baseline retained only as fallback/control."
            ),
        }
    if best_ai["generation_latency_ms"] is not None and best_ai["generation_latency_ms"] > 180000:
        return {
            "decision": "hold_ai_primary_blocked",
            "primary_lane": best_ai["candidate"],
            "fallback_lane": annotated["candidate"],
            "rationale": (
                f"Deterministic baseline measured {annotated['generation_latency_ms']} ms and "
                f"stays inside the {FAST_PREVIZ_BUDGET_MS} ms control bar. {best_ai['candidate']} "
                f"clears the quality bar but averages {best_ai['generation_latency_ms']} ms "
                "generation latency, which is outside even the optional AI-previz envelope."
            ),
        }
    return {
        "decision": "hold_ai_primary_blocked",
        "primary_lane": best_ai["candidate"],
        "fallback_lane": annotated["candidate"],
        "rationale": (
            f"Deterministic baseline measured {annotated['generation_latency_ms']} ms and stays "
            f"inside the {FAST_PREVIZ_BUDGET_MS} ms control bar, but it does not satisfy the "
            "product previz requirement. "
            f"{best_ai['candidate']} is the strongest current AI lane at {best_ai['overall']:.3f} "
            f"overall and {best_ai['generation_latency_ms']} ms generation latency, so AI previz "
            "remains the intended primary lane while runtime work stays blocked."
        ),
    }


def _load_candidate_meta(
    *,
    candidate_variant: str,
    clip_id: str,
    dataset_root: Path,
) -> dict[str, Any]:
    if not candidate_variant or not clip_id:
        return {}
    meta_path = dataset_root / candidate_variant / clip_id / "meta.json"
    if not meta_path.exists():
        return {}
    try:
        payload = json.loads(meta_path.read_text())
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _candidate_class(candidate_variant: str | None, operator_lane: str | None) -> str:
    if operator_lane in {"fast_previz", "deterministic_baseline"}:
        return "deterministic_baseline"
    if candidate_variant in _AI_VARIANTS:
        return "ai_previz"
    return "baseline"


def _component_score(entry: dict[str, Any], assertion_type: str) -> float | None:
    component_results = entry.get("gradingResult", {}).get("componentResults", [])
    scores = []
    for component in component_results:
        assertion = component.get("assertion", {})
        if assertion.get("type") == assertion_type and component.get("score") is not None:
            scores.append(component["score"])
    return round(mean(scores), 4) if scores else None


def _load_previous_scores() -> dict[str, float]:
    if not REGISTRY_PATH.exists():
        return {}
    data = yaml.safe_load(REGISTRY_PATH.read_text())
    for entry in data.get("evals", []):
        if entry.get("id") != "previz-usefulness":
            continue
        return {
            score["model"]: score.get("metrics", {}).get("overall")
            for score in entry.get("scores", [])
            if score.get("metrics", {}).get("overall") is not None
        }
    return {}


def _resolve_target_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return (REPO_ROOT / "benchmarks" / value).resolve()


def _maybe_add(values: set[Any], value: Any) -> None:
    if value not in (None, "", []):
        values.add(value)


def _single_or_none(values: set[Any]) -> Any | None:
    if not values:
        return None
    if len(values) == 1:
        return next(iter(values))
    return ", ".join(str(item) for item in sorted(values, key=str))


def _single_or_join(values: set[Any]) -> str | None:
    value = _single_or_none(values)
    if value is None:
        return None
    return str(value)


if __name__ == "__main__":
    main()
